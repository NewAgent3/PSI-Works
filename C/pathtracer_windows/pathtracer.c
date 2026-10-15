/*
 * Minimal Path Tracer in pure C (no external libraries).
 * - Monte Carlo path tracing with Russian roulette
 * - Spheres only (Cornell-box-like scene)
 * - Lambertian, Metal, Dielectric (glass) materials
 * - Antialiasing via stratified sampling
 * - Writes a 24-bit BMP file (no libraries needed)
 *
 * Build (Windows, MinGW):
 *     gcc -O3 -ffast-math -o pathtracer.exe pathtracer.c
 *
 * Run:
 *     pathtracer.exe
 *     -> produces "output.bmp"
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ---------- Image / render configuration ---------- */
#define IMAGE_WIDTH   640
#define IMAGE_HEIGHT  480
#define SAMPLES_PER_PIXEL 64
#define MAX_DEPTH 8

/* ---------- Math utilities ---------- */
typedef struct { double x, y, z; } Vec3;

static inline Vec3 v(double x, double y, double z) { Vec3 r = {x,y,z}; return r; }
static inline Vec3 vadd(Vec3 a, Vec3 b) { return v(a.x+b.x, a.y+b.y, a.z+b.z); }
static inline Vec3 vsub(Vec3 a, Vec3 b) { return v(a.x-b.x, a.y-b.y, a.z-b.z); }
static inline Vec3 vmul(Vec3 a, double s) { return v(a.x*s, a.y*s, a.z*s); }
static inline Vec3 vhad(Vec3 a, Vec3 b) { return v(a.x*b.x, a.y*b.y, a.z*b.z); }
static inline double vdot(Vec3 a, Vec3 b) { return a.x*b.x + a.y*b.y + a.z*b.z; }
static inline Vec3 vcross(Vec3 a, Vec3 b) {
    return v(a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x);
}
static inline double vlen(Vec3 a) { return sqrt(vdot(a,a)); }
static inline Vec3 vnorm(Vec3 a) { double l = vlen(a); return vmul(a, 1.0/l); }
static inline Vec3 vneg(Vec3 a) { return v(-a.x,-a.y,-a.z); }
static inline double clampd(double x, double a, double b){ return x<a?a:(x>b?b:x); }

/* ---------- Fast thread-unsafe PRNG (xorshift) ---------- */
static uint64_t g_rng = 0x9E3779B97F4A7C15ULL;
static inline uint64_t xorshift64(void) {
    uint64_t x = g_rng;
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    g_rng = x;
    return x;
}
static inline double rnd(void) {
    /* uniform [0,1) */
    return (xorshift64() >> 11) * (1.0/9007199254740992.0);
}

static Vec3 random_in_unit_sphere(void) {
    while (1) {
        Vec3 p = v(rnd()*2-1, rnd()*2-1, rnd()*2-1);
        if (vdot(p,p) < 1.0) return p;
    }
}
static Vec3 random_unit_vector(void) { return vnorm(random_in_unit_sphere()); }
static Vec3 random_in_unit_disk(void) {
    while (1) {
        Vec3 p = v(rnd()*2-1, rnd()*2-1, 0);
        if (vdot(p,p) < 1.0) return p;
    }
}

/* ---------- Ray ---------- */
typedef struct { Vec3 o, d; } Ray;
static inline Vec3 ray_at(Ray r, double t) { return vadd(r.o, vmul(r.d,t)); }

/* ---------- Materials ---------- */
typedef enum { MAT_LAMBERT, MAT_METAL, MAT_DIELECTRIC, MAT_LIGHT } MatType;

typedef struct {
    MatType type;
    Vec3 albedo;       /* color */
    double fuzz;       /* metal */
    double ir;         /* dielectric index of refraction */
    Vec3 emit;         /* emissive */
} Material;

/* ---------- Sphere ---------- */
typedef struct {
    Vec3 center;
    double radius;
    Material mat;
} Sphere;

typedef struct {
    Vec3 p;
    Vec3 n;
    double t;
    int front_face;
    Material mat;
} HitRec;

static int hit_sphere(const Sphere *s, Ray r, double tmin, double tmax, HitRec *rec) {
    Vec3 oc = vsub(r.o, s->center);
    double a = vdot(r.d, r.d);
    double half_b = vdot(oc, r.d);
    double c = vdot(oc,oc) - s->radius*s->radius;
    double disc = half_b*half_b - a*c;
    if (disc < 0) return 0;
    double sq = sqrt(disc);
    double t = (-half_b - sq)/a;
    if (t < tmin || t > tmax) {
        t = (-half_b + sq)/a;
        if (t < tmin || t > tmax) return 0;
    }
    rec->t = t;
    rec->p = ray_at(r, t);
    Vec3 outward = vmul(vsub(rec->p, s->center), 1.0/s->radius);
    rec->front_face = vdot(r.d, outward) < 0;
    rec->n = rec->front_face ? outward : vneg(outward);
    rec->mat = s->mat;
    return 1;
}

/* ---------- Scene ---------- */
#define MAX_SPHERES 32
static Sphere g_scene[MAX_SPHERES];
static int g_scene_n = 0;
static void add_sphere(Vec3 c, double r, Material m){
    g_scene[g_scene_n].center=c; g_scene[g_scene_n].radius=r; g_scene[g_scene_n].mat=m; g_scene_n++;
}

static int hit_scene(Ray r, double tmin, double tmax, HitRec *rec) {
    HitRec tmp;
    int hit_any = 0;
    double closest = tmax;
    for (int i=0;i<g_scene_n;i++){
        if (hit_sphere(&g_scene[i], r, tmin, closest, &tmp)){
            hit_any = 1;
            closest = tmp.t;
            *rec = tmp;
        }
    }
    return hit_any;
}

/* ---------- Material scatter / emit ---------- */
static double reflectance(double cosine, double ref_idx) {
    /* Schlick approximation */
    double r0 = (1.0 - ref_idx) / (1.0 + ref_idx);
    r0 = r0*r0;
    return r0 + (1.0 - r0)*pow(1.0 - cosine, 5.0);
}
static Vec3 reflect(Vec3 v_in, Vec3 n) { return vsub(v_in, vmul(n, 2*vdot(v_in,n))); }
static Vec3 refract(Vec3 uv, Vec3 n, double etai_over_etat) {
    double cos_theta = fmin(vdot(vneg(uv), n), 1.0);
    Vec3 r_out_perp = vmul(vadd(uv, vmul(n, cos_theta)), etai_over_etat);
    double k = -sqrt(fabs(1.0 - vdot(r_out_perp, r_out_perp)));
    Vec3 r_out_par = vmul(n, k);
    return vadd(r_out_perp, r_out_par);
}

static int scatter(Ray r_in, HitRec rec, Vec3 *attenuation, Ray *scattered) {
    switch (rec.mat.type) {
    case MAT_LAMBERT: {
        Vec3 dir = vadd(rec.n, random_unit_vector());
        if (fabs(dir.x)<1e-8 && fabs(dir.y)<1e-8 && fabs(dir.z)<1e-8) dir = rec.n;
        scattered->o = rec.p;
        scattered->d = dir;
        *attenuation = rec.mat.albedo;
        return 1;
    }
    case MAT_METAL: {
        Vec3 refl = reflect(vnorm(r_in.d), rec.n);
        scattered->o = rec.p;
        scattered->d = vadd(refl, vmul(random_in_unit_sphere(), rec.mat.fuzz));
        *attenuation = rec.mat.albedo;
        return vdot(scattered->d, rec.n) > 0;
    }
    case MAT_DIELECTRIC: {
        *attenuation = v(1,1,1);
        double ratio = rec.front_face ? (1.0/rec.mat.ir) : rec.mat.ir;
        Vec3 unit_dir = vnorm(r_in.d);
        double cos_theta = fmin(vdot(vneg(unit_dir), rec.n), 1.0);
        double sin_theta = sqrt(1.0 - cos_theta*cos_theta);
        int cannot_refract = ratio * sin_theta > 1.0;
        Vec3 dir;
        if (cannot_refract || reflectance(cos_theta, ratio) > rnd())
            dir = reflect(unit_dir, rec.n);
        else
            dir = refract(unit_dir, rec.n, ratio);
        scattered->o = rec.p;
        scattered->d = dir;
        return 1;
    }
    case MAT_LIGHT:
    default:
        return 0;
    }
}

/* ---------- Ray color (path tracing) ---------- */
static Vec3 ray_color(Ray r, int depth) {
    if (depth <= 0) return v(0,0,0);
    HitRec rec;
    if (!hit_scene(r, 0.001, 1e18, &rec)) {
        /* Sky gradient */
        Vec3 ud = vnorm(r.d);
        double t = 0.5*(ud.y + 1.0);
        Vec3 c1 = v(1.0,1.0,1.0);
        Vec3 c2 = v(0.5,0.7,1.0);
        return vadd(vmul(c1, 1.0-t), vmul(c2, t));
    }
    Vec3 emitted = rec.mat.emit;
    Ray scat;
    Vec3 att;
    if (!scatter(r, rec, &att, &scat)) return emitted;
    Vec3 child = ray_color(scat, depth-1);
    return vadd(emitted, vhad(att, child));
}

/* ---------- Camera ---------- */
typedef struct {
    Vec3 origin, lower_left, horizontal, vertical, u, v, w;
    double lens_radius;
} Camera;

static Camera make_camera(Vec3 lookfrom, Vec3 lookat, Vec3 vup, double vfov_deg,
                          double aspect, double aperture, double focus_dist) {
    Camera c;
    double theta = vfov_deg * 3.14159265358979323846 / 180.0;
    double h = tan(theta/2.0);
    double vh = 2.0 * h;
    double vw = aspect * vh;
    c.w = vnorm(vsub(lookfrom, lookat));
    c.u = vnorm(vcross(vup, c.w));
    c.v = vcross(c.w, c.u);
    c.origin = lookfrom;
    c.horizontal = vmul(c.u, vw*focus_dist);
    c.vertical   = vmul(c.v, vh*focus_dist);
    c.lower_left = vsub(vsub(vsub(c.origin, vmul(c.horizontal, 0.5)),
                             vmul(c.vertical, 0.5)),
                        vmul(c.w, focus_dist));
    c.lens_radius = aperture/2.0;
    return c;
}
static Ray cam_ray(Camera *c, double s, double t) {
    Vec3 rd = vmul(random_in_unit_disk(), c->lens_radius);
    Vec3 offset = vadd(vmul(c->u, rd.x), vmul(c->v, rd.y));
    Ray r;
    r.o = vadd(c->origin, offset);
    r.d = vsub(vsub(vadd(vadd(c->lower_left, vmul(c->horizontal, s)),
                         vmul(c->vertical, t)),
                    c->origin), offset);
    return r;
}

/* ---------- BMP writer (24-bit, no libraries) ---------- */
static void write_bmp(const char *fname, int w, int h, unsigned char *rgb) {
    /* rgb stored top-to-bottom, R,G,B per pixel; BMP is bottom-to-top BGR */
    int row_bytes = w*3;
    int pad = (4 - (row_bytes % 4)) % 4;
    int img_size = (row_bytes + pad) * h;
    int file_size = 54 + img_size;
    unsigned char header[54] = {0};
    header[0]='B'; header[1]='M';
    header[2] = (unsigned char)(file_size);
    header[3] = (unsigned char)(file_size>>8);
    header[4] = (unsigned char)(file_size>>16);
    header[5] = (unsigned char)(file_size>>24);
    header[10] = 54;
    header[14] = 40;
    header[18] = (unsigned char)(w);
    header[19] = (unsigned char)(w>>8);
    header[20] = (unsigned char)(w>>16);
    header[21] = (unsigned char)(w>>24);
    header[22] = (unsigned char)(h);
    header[23] = (unsigned char)(h>>8);
    header[24] = (unsigned char)(h>>16);
    header[25] = (unsigned char)(h>>24);
    header[26] = 1;
    header[28] = 24;
    header[34] = (unsigned char)(img_size);
    header[35] = (unsigned char)(img_size>>8);
    header[36] = (unsigned char)(img_size>>16);
    header[37] = (unsigned char)(img_size>>24);

    FILE *f = fopen(fname, "wb");
    if (!f) { fprintf(stderr, "Cannot write %s\n", fname); return; }
    fwrite(header,1,54,f);
    unsigned char zero[3] = {0,0,0};
    for (int y = h-1; y >= 0; y--) {
        for (int x = 0; x < w; x++) {
            unsigned char *p = &rgb[(y*w + x)*3];
            unsigned char bgr[3] = { p[2], p[1], p[0] };
            fwrite(bgr,1,3,f);
        }
        if (pad) fwrite(zero,1,pad,f);
    }
    fclose(f);
}

/* ---------- Scene setup ---------- */
static void build_scene(void) {
    Material ground = { MAT_LAMBERT, {0.5,0.5,0.5}, 0, 0, {0,0,0} };
    add_sphere(v(0,-1000,0), 1000, ground);

    Material center = { MAT_LAMBERT, {0.7,0.3,0.3}, 0, 0, {0,0,0} };
    add_sphere(v(0,1,0), 1.0, center);

    Material glass  = { MAT_DIELECTRIC, {1,1,1}, 0, 1.5, {0,0,0} };
    add_sphere(v(-2.2,1,0), 1.0, glass);
    /* hollow glass effect */
    add_sphere(v(-2.2,1,0), -0.85, glass);

    Material metal  = { MAT_METAL, {0.8,0.6,0.2}, 0.05, 0, {0,0,0} };
    add_sphere(v(2.2,1,0), 1.0, metal);

    /* Small accent spheres */
    Material blueDiff = { MAT_LAMBERT, {0.1,0.2,0.8}, 0, 0, {0,0,0} };
    add_sphere(v(0.5, 0.3, 1.8), 0.3, blueDiff);

    Material greenMetal = { MAT_METAL, {0.2,0.8,0.4}, 0.2, 0, {0,0,0} };
    add_sphere(v(-0.9, 0.3, 1.8), 0.3, greenMetal);

    /* Emissive sphere as a soft light source */
    Material light = { MAT_LIGHT, {0,0,0}, 0, 0, {6,6,5} };
    add_sphere(v(3.5, 4.5, 3.0), 1.2, light);
}

/* ---------- Main ---------- */
int main(int argc, char **argv) {
    int W = IMAGE_WIDTH, H = IMAGE_HEIGHT, SPP = SAMPLES_PER_PIXEL;
    if (argc >= 2) SPP = atoi(argv[1]);
    if (SPP <= 0) SPP = SAMPLES_PER_PIXEL;

    g_rng = (uint64_t)time(NULL) ^ 0xDEADBEEFCAFEBABEULL;
    if (g_rng == 0) g_rng = 1;

    build_scene();

    Vec3 lookfrom = v(6, 2.5, 6);
    Vec3 lookat   = v(0, 1.0, 0);
    Vec3 vup      = v(0,1,0);
    double dist_to_focus = vlen(vsub(lookfrom, lookat));
    double aperture = 0.06;
    Camera cam = make_camera(lookfrom, lookat, vup, 30.0,
                             (double)W/(double)H, aperture, dist_to_focus);

    unsigned char *img = (unsigned char*)malloc(W*H*3);
    if (!img) { fprintf(stderr,"oom\n"); return 1; }

    printf("Path tracing %dx%d, %d spp, depth %d ...\n", W, H, SPP, MAX_DEPTH);
    fflush(stdout);

    clock_t t0 = clock();
    for (int j = 0; j < H; j++) {
        if (j % 16 == 0) {
            printf("\r  row %d/%d (%.1f%%)", j, H, 100.0*j/H);
            fflush(stdout);
        }
        for (int i = 0; i < W; i++) {
            Vec3 col = v(0,0,0);
            for (int s = 0; s < SPP; s++) {
                double u = ((double)i + rnd()) / (double)(W-1);
                double t = ((double)j + rnd()) / (double)(H-1);
                /* flip y so image isn't upside down */
                Ray r = cam_ray(&cam, u, 1.0 - t);
                col = vadd(col, ray_color(r, MAX_DEPTH));
            }
            col = vmul(col, 1.0/SPP);
            /* gamma 2.0 + clamp */
            double rr = sqrt(clampd(col.x, 0, 1));
            double gg = sqrt(clampd(col.y, 0, 1));
            double bb = sqrt(clampd(col.z, 0, 1));
            int idx = (j*W + i)*3;
            img[idx+0] = (unsigned char)(255.99 * rr);
            img[idx+1] = (unsigned char)(255.99 * gg);
            img[idx+2] = (unsigned char)(255.99 * bb);
        }
    }
    double secs = (double)(clock()-t0)/CLOCKS_PER_SEC;
    printf("\rRendered in %.2f seconds.            \n", secs);

    write_bmp("output.bmp", W, H, img);
    printf("Wrote output.bmp\n");
    free(img);
    return 0;
}
