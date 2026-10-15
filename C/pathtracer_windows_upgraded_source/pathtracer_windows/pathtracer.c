/*
 * PathTracer++ (single-file, no external libraries)
 * -------------------------------------------------
 * Upgraded self-contained path tracer for Windows.
 *
 * Highlights:
 *   - Pure C, single source file, no external dependencies
 *   - Windows multithreaded tiled renderer (single-thread fallback elsewhere)
 *   - Lambertian / metal / dielectric / emissive materials
 *   - Multiple built-in scenes
 *   - Deterministic seed option
 *   - Configurable CLI: resolution, spp, depth, output, threads, scene, lens settings
 *   - ACES-style tone mapping + gamma correction
 *   - BMP and PPM output writers
 *   - Backward compatible with: pathtracer.exe 128
 *
 * Build (MinGW-w64, Windows):
 *   gcc -O3 -std=c99 -ffast-math -static -s -o pathtracer.exe pathtracer.c -lm
 *
 * Build (MSVC, Developer Command Prompt):
 *   cl /O2 /MT pathtracer.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define MAX_SPHERES 512
#define TILE_SIZE 16
#define EPSILON 1e-4

typedef struct { double x, y, z; } Vec3;
typedef struct { Vec3 o, d; } Ray;
typedef enum { MAT_LAMBERT, MAT_METAL, MAT_DIELECTRIC, MAT_LIGHT } MatType;
typedef enum { SCENE_SHOWCASE, SCENE_CORNELL_SPHERES, SCENE_RANDOM_BALLS, SCENE_GLASSES } ScenePreset;
typedef enum { SKY_BLUE, SKY_STUDIO, SKY_BLACK, SKY_SUNSET } SkyMode;

typedef struct {
    MatType type;
    Vec3 albedo;
    Vec3 emit;
    double fuzz;
    double ir;
} Material;

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

typedef struct {
    Vec3 origin, lower_left, horizontal, vertical, u, v, w;
    double lens_radius;
} Camera;

typedef struct {
    uint64_t state;
} RNG;

typedef struct {
    int width;
    int height;
    int spp;
    int max_depth;
    int threads;
    int tile_size;
    int scene;
    int quiet;
    double vfov;
    double aperture;
    double focus_dist;
    uint64_t seed;
    int seed_explicit;
    char output[260];
} RenderConfig;

typedef struct {
    RenderConfig cfg;
    Camera cam;
    unsigned char *img;
    int tiles_x;
    int tiles_y;
    int total_tiles;
    volatile int next_tile;
    volatile int tiles_done;
    clock_t start_clock;
} RenderContext;

static Sphere g_scene[MAX_SPHERES];
static int g_scene_n = 0;

/* --------------------------- Vec utilities --------------------------- */
static inline Vec3 v3(double x, double y, double z) { Vec3 r = {x,y,z}; return r; }
static inline Vec3 vadd(Vec3 a, Vec3 b) { return v3(a.x+b.x, a.y+b.y, a.z+b.z); }
static inline Vec3 vsub(Vec3 a, Vec3 b) { return v3(a.x-b.x, a.y-b.y, a.z-b.z); }
static inline Vec3 vmul(Vec3 a, double s) { return v3(a.x*s, a.y*s, a.z*s); }
static inline Vec3 vdiv(Vec3 a, double s) { return v3(a.x/s, a.y/s, a.z/s); }
static inline Vec3 vhad(Vec3 a, Vec3 b) { return v3(a.x*b.x, a.y*b.y, a.z*b.z); }
static inline Vec3 vneg(Vec3 a) { return v3(-a.x, -a.y, -a.z); }
static inline double vdot(Vec3 a, Vec3 b) { return a.x*b.x + a.y*b.y + a.z*b.z; }
static inline Vec3 vcross(Vec3 a, Vec3 b) { return v3(a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x); }
static inline double vlen2(Vec3 a) { return vdot(a,a); }
static inline double vlen(Vec3 a) { return sqrt(vlen2(a)); }
static inline Vec3 vnorm(Vec3 a) { double l = vlen(a); return (l > 0.0) ? vdiv(a, l) : v3(0,0,0); }
static inline double clampd(double x, double a, double b) { return x < a ? a : (x > b ? b : x); }
static inline double max3(double a, double b, double c) { double m = a > b ? a : b; return m > c ? m : c; }

/* --------------------------- RNG --------------------------- */
static uint64_t splitmix64_next(uint64_t *x) {
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
static void rng_seed(RNG *rng, uint64_t seed) {
    rng->state = seed ? seed : 0xA5A5A5A5A5A5A5A5ULL;
    (void)splitmix64_next(&rng->state);
}
static uint64_t rng_u64(RNG *rng) {
    uint64_t x = rng->state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    rng->state = x;
    return x * 2685821657736338717ULL;
}
static double rng_next(RNG *rng) {
    return (rng_u64(rng) >> 11) * (1.0 / 9007199254740992.0);
}

static Vec3 random_in_unit_sphere(RNG *rng) {
    for (;;) {
        Vec3 p = v3(rng_next(rng)*2.0 - 1.0, rng_next(rng)*2.0 - 1.0, rng_next(rng)*2.0 - 1.0);
        if (vlen2(p) < 1.0) return p;
    }
}
static Vec3 random_in_unit_disk(RNG *rng) {
    for (;;) {
        Vec3 p = v3(rng_next(rng)*2.0 - 1.0, rng_next(rng)*2.0 - 1.0, 0.0);
        if (vlen2(p) < 1.0) return p;
    }
}
static void orthonormal_basis(Vec3 n, Vec3 *tangent, Vec3 *bitangent) {
    Vec3 a = fabs(n.z) < 0.999 ? v3(0,0,1) : v3(1,0,0);
    *tangent = vnorm(vcross(a, n));
    *bitangent = vcross(n, *tangent);
}
static Vec3 cosine_sample_hemisphere(Vec3 n, RNG *rng) {
    double r1 = rng_next(rng);
    double r2 = rng_next(rng);
    double phi = 2.0 * M_PI * r1;
    double r = sqrt(r2);
    double x = cos(phi) * r;
    double y = sin(phi) * r;
    double z = sqrt(1.0 - r2);
    Vec3 t, b;
    orthonormal_basis(n, &t, &b);
    return vnorm(vadd(vadd(vmul(t, x), vmul(b, y)), vmul(n, z)));
}

/* --------------------------- Ray / camera --------------------------- */
static inline Vec3 ray_at(Ray r, double t) { return vadd(r.o, vmul(r.d, t)); }

static Camera make_camera(Vec3 lookfrom, Vec3 lookat, Vec3 vup, double vfov_deg,
                          double aspect, double aperture, double focus_dist) {
    Camera c;
    double theta = vfov_deg * M_PI / 180.0;
    double h = tan(theta * 0.5);
    double viewport_h = 2.0 * h;
    double viewport_w = aspect * viewport_h;

    c.w = vnorm(vsub(lookfrom, lookat));
    c.u = vnorm(vcross(vup, c.w));
    c.v = vcross(c.w, c.u);

    c.origin = lookfrom;
    c.horizontal = vmul(c.u, viewport_w * focus_dist);
    c.vertical = vmul(c.v, viewport_h * focus_dist);
    c.lower_left = vsub(vsub(vsub(c.origin, vmul(c.horizontal, 0.5)), vmul(c.vertical, 0.5)), vmul(c.w, focus_dist));
    c.lens_radius = aperture * 0.5;
    return c;
}

static Ray cam_ray(const Camera *c, double s, double t, RNG *rng) {
    Vec3 rd = vmul(random_in_unit_disk(rng), c->lens_radius);
    Vec3 offset = vadd(vmul(c->u, rd.x), vmul(c->v, rd.y));
    Ray r;
    r.o = vadd(c->origin, offset);
    r.d = vsub(vsub(vadd(vadd(c->lower_left, vmul(c->horizontal, s)), vmul(c->vertical, t)), c->origin), offset);
    return r;
}

/* --------------------------- Materials / geometry --------------------------- */
static Material lambert(double r, double g, double b) {
    Material m; m.type = MAT_LAMBERT; m.albedo = v3(r,g,b); m.emit = v3(0,0,0); m.fuzz = 0.0; m.ir = 0.0; return m;
}
static Material metal(double r, double g, double b, double fuzz) {
    Material m; m.type = MAT_METAL; m.albedo = v3(r,g,b); m.emit = v3(0,0,0); m.fuzz = clampd(fuzz, 0.0, 1.0); m.ir = 0.0; return m;
}
static Material glass(double ir) {
    Material m; m.type = MAT_DIELECTRIC; m.albedo = v3(1,1,1); m.emit = v3(0,0,0); m.fuzz = 0.0; m.ir = ir; return m;
}
static Material lightm(double r, double g, double b) {
    Material m; m.type = MAT_LIGHT; m.albedo = v3(0,0,0); m.emit = v3(r,g,b); m.fuzz = 0.0; m.ir = 0.0; return m;
}

static void reset_scene(void) { g_scene_n = 0; }
static void add_sphere(Vec3 center, double radius, Material mat) {
    if (g_scene_n >= MAX_SPHERES) return;
    g_scene[g_scene_n].center = center;
    g_scene[g_scene_n].radius = radius;
    g_scene[g_scene_n].mat = mat;
    g_scene_n++;
}

static int hit_sphere(const Sphere *s, Ray r, double tmin, double tmax, HitRec *rec) {
    Vec3 oc = vsub(r.o, s->center);
    double a = vdot(r.d, r.d);
    double half_b = vdot(oc, r.d);
    double c = vdot(oc, oc) - s->radius * s->radius;
    double disc = half_b * half_b - a * c;
    if (disc < 0.0) return 0;
    double sq = sqrt(disc);
    double root = (-half_b - sq) / a;
    if (root < tmin || root > tmax) {
        root = (-half_b + sq) / a;
        if (root < tmin || root > tmax) return 0;
    }
    rec->t = root;
    rec->p = ray_at(r, root);
    {
        Vec3 outward = vmul(vsub(rec->p, s->center), 1.0 / s->radius);
        rec->front_face = vdot(r.d, outward) < 0.0;
        rec->n = rec->front_face ? outward : vneg(outward);
    }
    rec->mat = s->mat;
    return 1;
}

static int hit_scene(Ray r, double tmin, double tmax, HitRec *rec) {
    int hit_any = 0;
    double closest = tmax;
    HitRec tmp;
    int i;
    for (i = 0; i < g_scene_n; ++i) {
        if (hit_sphere(&g_scene[i], r, tmin, closest, &tmp)) {
            hit_any = 1;
            closest = tmp.t;
            *rec = tmp;
        }
    }
    return hit_any;
}

static Vec3 reflect(Vec3 vin, Vec3 n) {
    return vsub(vin, vmul(n, 2.0 * vdot(vin, n)));
}

static Vec3 refract(Vec3 uv, Vec3 n, double etai_over_etat) {
    double cos_theta = fmin(vdot(vneg(uv), n), 1.0);
    Vec3 r_out_perp = vmul(vadd(uv, vmul(n, cos_theta)), etai_over_etat);
    Vec3 r_out_parallel = vmul(n, -sqrt(fabs(1.0 - vlen2(r_out_perp))));
    return vadd(r_out_perp, r_out_parallel);
}

static double reflectance(double cosine, double ref_idx) {
    double r0 = (1.0 - ref_idx) / (1.0 + ref_idx);
    r0 = r0 * r0;
    return r0 + (1.0 - r0) * pow(1.0 - cosine, 5.0);
}

/* --------------------------- Sky / tone mapping --------------------------- */
static Vec3 sky_color(Vec3 dir, int scene) {
    Vec3 u = vnorm(dir);
    double t = 0.5 * (u.y + 1.0);
    switch ((SkyMode)scene) {
        case SKY_STUDIO:
            return vadd(vmul(v3(0.95, 0.97, 1.00), 1.0 - t), vmul(v3(0.55, 0.62, 0.75), t));
        case SKY_BLACK:
            return v3(0.0, 0.0, 0.0);
        case SKY_SUNSET:
            return vadd(vmul(v3(1.00, 0.72, 0.45), 1.0 - t), vmul(v3(0.25, 0.35, 0.70), t));
        case SKY_BLUE:
        default:
            return vadd(vmul(v3(1.0, 1.0, 1.0), 1.0 - t), vmul(v3(0.45, 0.65, 1.0), t));
    }
}

static Vec3 aces_tonemap(Vec3 c) {
    const double a = 2.51;
    const double b = 0.03;
    const double c1 = 2.43;
    const double d = 0.59;
    const double e = 0.14;
    Vec3 r;
    r.x = clampd((c.x * (a * c.x + b)) / (c.x * (c1 * c.x + d) + e), 0.0, 1.0);
    r.y = clampd((c.y * (a * c.y + b)) / (c.y * (c1 * c.y + d) + e), 0.0, 1.0);
    r.z = clampd((c.z * (a * c.z + b)) / (c.z * (c1 * c.z + d) + e), 0.0, 1.0);
    return r;
}

static Vec3 gamma_correct(Vec3 c) {
    return v3(pow(clampd(c.x, 0.0, 1.0), 1.0 / 2.2),
              pow(clampd(c.y, 0.0, 1.0), 1.0 / 2.2),
              pow(clampd(c.z, 0.0, 1.0), 1.0 / 2.2));
}

/* --------------------------- Rendering --------------------------- */
static Vec3 ray_color(Ray r, RNG *rng, int max_depth, int scene) {
    Vec3 throughput = v3(1.0, 1.0, 1.0);
    Vec3 radiance = v3(0.0, 0.0, 0.0);
    int depth;

    for (depth = 0; depth < max_depth; ++depth) {
        HitRec rec;
        if (!hit_scene(r, EPSILON, 1e30, &rec)) {
            radiance = vadd(radiance, vhad(throughput, sky_color(r.d, scene == SCENE_CORNELL_SPHERES ? SKY_BLACK : (scene == SCENE_GLASSES ? SKY_STUDIO : (scene == SCENE_RANDOM_BALLS ? SKY_SUNSET : SKY_BLUE)))));
            break;
        }

        if (rec.mat.type == MAT_LIGHT) {
            radiance = vadd(radiance, vhad(throughput, rec.mat.emit));
            break;
        }

        if (rec.mat.type == MAT_LAMBERT) {
            Vec3 dir = cosine_sample_hemisphere(rec.n, rng);
            r.o = rec.p;
            r.d = dir;
            throughput = vhad(throughput, rec.mat.albedo);
        } else if (rec.mat.type == MAT_METAL) {
            Vec3 refl = reflect(vnorm(r.d), rec.n);
            Vec3 dir = vadd(refl, vmul(random_in_unit_sphere(rng), rec.mat.fuzz));
            if (vdot(dir, rec.n) <= 0.0) break;
            r.o = rec.p;
            r.d = dir;
            throughput = vhad(throughput, rec.mat.albedo);
        } else if (rec.mat.type == MAT_DIELECTRIC) {
            double refraction_ratio = rec.front_face ? (1.0 / rec.mat.ir) : rec.mat.ir;
            Vec3 unit_dir = vnorm(r.d);
            double cos_theta = fmin(vdot(vneg(unit_dir), rec.n), 1.0);
            double sin_theta = sqrt(fmax(0.0, 1.0 - cos_theta * cos_theta));
            int cannot_refract = refraction_ratio * sin_theta > 1.0;
            Vec3 dir;
            if (cannot_refract || reflectance(cos_theta, refraction_ratio) > rng_next(rng)) {
                dir = reflect(unit_dir, rec.n);
            } else {
                dir = refract(unit_dir, rec.n, refraction_ratio);
            }
            r.o = rec.p;
            r.d = dir;
        }

        if (depth >= 3) {
            double p = clampd(max3(throughput.x, throughput.y, throughput.z), 0.05, 0.95);
            if (rng_next(rng) > p) break;
            throughput = vdiv(throughput, p);
        }
    }

    return radiance;
}

static void put_pixel(unsigned char *img, int w, int x, int y, Vec3 linear) {
    Vec3 mapped = aces_tonemap(linear);
    Vec3 out = gamma_correct(mapped);
    int idx = (y * w + x) * 3;
    img[idx + 0] = (unsigned char)(255.99 * clampd(out.x, 0.0, 1.0));
    img[idx + 1] = (unsigned char)(255.99 * clampd(out.y, 0.0, 1.0));
    img[idx + 2] = (unsigned char)(255.99 * clampd(out.z, 0.0, 1.0));
}

static uint64_t pixel_seed(uint64_t seed, int x, int y, int sample) {
    uint64_t s = seed;
    s ^= (uint64_t)(x + 1) * 0x9E3779B185EBCA87ULL;
    s ^= (uint64_t)(y + 1) * 0xC2B2AE3D27D4EB4FULL;
    s ^= (uint64_t)(sample + 1) * 0x165667B19E3779F9ULL;
    s ^= (s >> 29);
    s *= 0x94D049BB133111EBULL;
    s ^= (s >> 31);
    return s;
}

static void render_tile(RenderContext *ctx, int tile_index) {
    int tx = tile_index % ctx->tiles_x;
    int ty = tile_index / ctx->tiles_x;
    int x0 = tx * ctx->cfg.tile_size;
    int y0 = ty * ctx->cfg.tile_size;
    int x1 = x0 + ctx->cfg.tile_size;
    int y1 = y0 + ctx->cfg.tile_size;
    int x, y, s;
    if (x1 > ctx->cfg.width) x1 = ctx->cfg.width;
    if (y1 > ctx->cfg.height) y1 = ctx->cfg.height;

    for (y = y0; y < y1; ++y) {
        for (x = x0; x < x1; ++x) {
            Vec3 col = v3(0.0, 0.0, 0.0);
            for (s = 0; s < ctx->cfg.spp; ++s) {
                RNG rng;
                double u, v;
                Ray r;
                rng_seed(&rng, pixel_seed(ctx->cfg.seed, x, y, s));
                u = ((double)x + rng_next(&rng)) / (double)(ctx->cfg.width - 1);
                v = ((double)y + rng_next(&rng)) / (double)(ctx->cfg.height - 1);
                r = cam_ray(&ctx->cam, u, 1.0 - v, &rng);
                col = vadd(col, ray_color(r, &rng, ctx->cfg.max_depth, ctx->cfg.scene));
            }
            col = vdiv(col, (double)ctx->cfg.spp);
            put_pixel(ctx->img, ctx->cfg.width, x, y, col);
        }
    }
}

#ifdef _WIN32
static DWORD WINAPI worker_thread(LPVOID param) {
    RenderContext *ctx = (RenderContext*)param;
    for (;;) {
        int tile = (int)InterlockedIncrement((volatile LONG*)&ctx->next_tile) - 1;
        if (tile >= ctx->total_tiles) break;
        render_tile(ctx, tile);
        InterlockedIncrement((volatile LONG*)&ctx->tiles_done);
    }
    return 0;
}
#endif

static void render_image(RenderContext *ctx) {
#ifdef _WIN32
    if (ctx->cfg.threads > 1) {
        HANDLE *threads = (HANDLE*)malloc(sizeof(HANDLE) * (size_t)ctx->cfg.threads);
        int i;
        ctx->next_tile = 0;
        ctx->tiles_done = 0;
        for (i = 0; i < ctx->cfg.threads; ++i) {
            threads[i] = CreateThread(NULL, 0, worker_thread, ctx, 0, NULL);
        }

        for (;;) {
            double secs;
            int done = (int)ctx->tiles_done;
            if (!ctx->cfg.quiet) {
                secs = (double)(clock() - ctx->start_clock) / CLOCKS_PER_SEC;
                printf("\rTiles %d/%d (%.1f%%) | %.2fs", done, ctx->total_tiles,
                       100.0 * (double)done / (double)ctx->total_tiles, secs);
                fflush(stdout);
            }
            if (done >= ctx->total_tiles) break;
            Sleep(150);
        }
        WaitForMultipleObjects((DWORD)ctx->cfg.threads, threads, TRUE, INFINITE);
        for (i = 0; i < ctx->cfg.threads; ++i) CloseHandle(threads[i]);
        free(threads);
        if (!ctx->cfg.quiet) printf("\n");
        return;
    }
#endif
    ctx->next_tile = 0;
    ctx->tiles_done = 0;
    while (ctx->next_tile < ctx->total_tiles) {
        render_tile(ctx, ctx->next_tile++);
        ctx->tiles_done++;
        if (!ctx->cfg.quiet && ((ctx->tiles_done % 4) == 0 || ctx->tiles_done == ctx->total_tiles)) {
            double secs = (double)(clock() - ctx->start_clock) / CLOCKS_PER_SEC;
            printf("\rTiles %d/%d (%.1f%%) | %.2fs", ctx->tiles_done, ctx->total_tiles,
                   100.0 * (double)ctx->tiles_done / (double)ctx->total_tiles, secs);
            fflush(stdout);
        }
    }
    if (!ctx->cfg.quiet) printf("\n");
}

/* --------------------------- Writers --------------------------- */
static void write_bmp(const char *fname, int w, int h, const unsigned char *rgb) {
    int row_bytes = w * 3;
    int pad = (4 - (row_bytes % 4)) % 4;
    int img_size = (row_bytes + pad) * h;
    int file_size = 54 + img_size;
    unsigned char header[54] = {0};
    unsigned char zero[3] = {0,0,0};
    FILE *f;
    int y, x;

    header[0] = 'B'; header[1] = 'M';
    header[2] = (unsigned char)(file_size);
    header[3] = (unsigned char)(file_size >> 8);
    header[4] = (unsigned char)(file_size >> 16);
    header[5] = (unsigned char)(file_size >> 24);
    header[10] = 54;
    header[14] = 40;
    header[18] = (unsigned char)(w);
    header[19] = (unsigned char)(w >> 8);
    header[20] = (unsigned char)(w >> 16);
    header[21] = (unsigned char)(w >> 24);
    header[22] = (unsigned char)(h);
    header[23] = (unsigned char)(h >> 8);
    header[24] = (unsigned char)(h >> 16);
    header[25] = (unsigned char)(h >> 24);
    header[26] = 1;
    header[28] = 24;
    header[34] = (unsigned char)(img_size);
    header[35] = (unsigned char)(img_size >> 8);
    header[36] = (unsigned char)(img_size >> 16);
    header[37] = (unsigned char)(img_size >> 24);

    f = fopen(fname, "wb");
    if (!f) {
        fprintf(stderr, "Cannot write %s\n", fname);
        return;
    }
    fwrite(header, 1, 54, f);
    for (y = h - 1; y >= 0; --y) {
        for (x = 0; x < w; ++x) {
            const unsigned char *p = &rgb[(y * w + x) * 3];
            unsigned char bgr[3] = { p[2], p[1], p[0] };
            fwrite(bgr, 1, 3, f);
        }
        if (pad) fwrite(zero, 1, (size_t)pad, f);
    }
    fclose(f);
}

static void write_ppm(const char *fname, int w, int h, const unsigned char *rgb) {
    FILE *f = fopen(fname, "wb");
    if (!f) {
        fprintf(stderr, "Cannot write %s\n", fname);
        return;
    }
    fprintf(f, "P6\n%d %d\n255\n", w, h);
    fwrite(rgb, 1, (size_t)(w * h * 3), f);
    fclose(f);
}

/* --------------------------- Utility --------------------------- */
static int streqi(const char *a, const char *b) {
    while (*a && *b) {
        char ca = *a, cb = *b;
        if (ca >= 'A' && ca <= 'Z') ca = (char)(ca - 'A' + 'a');
        if (cb >= 'A' && cb <= 'Z') cb = (char)(cb - 'A' + 'a');
        if (ca != cb) return 0;
        ++a; ++b;
    }
    return *a == '\0' && *b == '\0';
}

static int is_number(const char *s) {
    if (!s || !*s) return 0;
    if (*s == '-' || *s == '+') ++s;
    if (!*s) return 0;
    while (*s) {
        if (*s < '0' || *s > '9') return 0;
        ++s;
    }
    return 1;
}

static int detect_threads(void) {
#ifdef _WIN32
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return si.dwNumberOfProcessors > 0 ? (int)si.dwNumberOfProcessors : 1;
#else
    return 1;
#endif
}

static void set_defaults(RenderConfig *cfg) {
    cfg->width = 960;
    cfg->height = 540;
    cfg->spp = 128;
    cfg->max_depth = 12;
    cfg->threads = detect_threads();
    cfg->tile_size = TILE_SIZE;
    cfg->scene = SCENE_SHOWCASE;
    cfg->quiet = 0;
    cfg->vfov = 32.0;
    cfg->aperture = 0.04;
    cfg->focus_dist = 0.0;
    cfg->seed = (uint64_t)time(NULL) ^ 0xD1B54A32D192ED03ULL;
    cfg->seed_explicit = 0;
    strcpy(cfg->output, "output.bmp");
}

static void print_help(void) {
    printf("PathTracer++ - self-contained Windows path tracer\n\n");
    printf("Usage:\n");
    printf("  pathtracer.exe\n");
    printf("  pathtracer.exe 256\n");
    printf("  pathtracer.exe --scene showcase --width 1280 --height 720 --spp 256 --output final.bmp\n\n");
    printf("Options:\n");
    printf("  --width N        image width (default 960)\n");
    printf("  --height N       image height (default 540)\n");
    printf("  --spp N          samples per pixel (default 128)\n");
    printf("  --depth N        max path depth (default 12)\n");
    printf("  --threads N      worker threads; 0 = auto\n");
    printf("  --scene NAME     showcase | cornell | random | glass\n");
    printf("  --vfov X         vertical field of view in degrees\n");
    printf("  --aperture X     thin lens aperture\n");
    printf("  --focus X        explicit focus distance\n");
    printf("  --seed N         deterministic seed\n");
    printf("  --output FILE    output .bmp or .ppm\n");
    printf("  --quiet          suppress progress output\n");
    printf("  --help           show this message\n\n");
    printf("Examples:\n");
    printf("  pathtracer.exe --scene cornell --width 1024 --height 1024 --spp 512 --output cornell.bmp\n");
    printf("  pathtracer.exe --scene random --spp 64 --threads 0 --output random.bmp\n");
}

static int parse_scene(const char *name) {
    if (streqi(name, "showcase")) return SCENE_SHOWCASE;
    if (streqi(name, "cornell") || streqi(name, "cornell_spheres")) return SCENE_CORNELL_SPHERES;
    if (streqi(name, "random") || streqi(name, "random_balls")) return SCENE_RANDOM_BALLS;
    if (streqi(name, "glass") || streqi(name, "glasses")) return SCENE_GLASSES;
    return -1;
}

static void parse_args(RenderConfig *cfg, int argc, char **argv) {
    int i;
    if (argc == 2 && is_number(argv[1])) {
        cfg->spp = atoi(argv[1]);
        return;
    }

    for (i = 1; i < argc; ++i) {
        const char *arg = argv[i];
        if (streqi(arg, "--help") || streqi(arg, "-h")) {
            print_help();
            exit(0);
        } else if (streqi(arg, "--width") && i + 1 < argc) {
            cfg->width = atoi(argv[++i]);
        } else if (streqi(arg, "--height") && i + 1 < argc) {
            cfg->height = atoi(argv[++i]);
        } else if (streqi(arg, "--spp") && i + 1 < argc) {
            cfg->spp = atoi(argv[++i]);
        } else if (streqi(arg, "--depth") && i + 1 < argc) {
            cfg->max_depth = atoi(argv[++i]);
        } else if (streqi(arg, "--threads") && i + 1 < argc) {
            cfg->threads = atoi(argv[++i]);
        } else if (streqi(arg, "--scene") && i + 1 < argc) {
            int s = parse_scene(argv[++i]);
            if (s >= 0) cfg->scene = s;
        } else if (streqi(arg, "--vfov") && i + 1 < argc) {
            cfg->vfov = atof(argv[++i]);
        } else if (streqi(arg, "--aperture") && i + 1 < argc) {
            cfg->aperture = atof(argv[++i]);
        } else if (streqi(arg, "--focus") && i + 1 < argc) {
            cfg->focus_dist = atof(argv[++i]);
        } else if (streqi(arg, "--seed") && i + 1 < argc) {
            cfg->seed = (uint64_t)strtoull(argv[++i], NULL, 10);
            cfg->seed_explicit = 1;
        } else if (streqi(arg, "--output") && i + 1 < argc) {
            strncpy(cfg->output, argv[++i], sizeof(cfg->output) - 1);
            cfg->output[sizeof(cfg->output) - 1] = '\0';
        } else if (streqi(arg, "--quiet")) {
            cfg->quiet = 1;
        } else if (is_number(arg)) {
            cfg->spp = atoi(arg);
        }
    }

    if (cfg->threads <= 0) cfg->threads = detect_threads();
    if (cfg->width < 16) cfg->width = 16;
    if (cfg->height < 16) cfg->height = 16;
    if (cfg->spp < 1) cfg->spp = 1;
    if (cfg->max_depth < 1) cfg->max_depth = 1;
    if (cfg->tile_size < 4) cfg->tile_size = 4;
    if (cfg->threads < 1) cfg->threads = 1;
}

/* --------------------------- Scene presets --------------------------- */
static Camera build_scene_and_camera(const RenderConfig *cfg) {
    reset_scene();

    if (cfg->scene == SCENE_SHOWCASE) {
        add_sphere(v3(0,-1000,0), 1000, lambert(0.55, 0.58, 0.62));
        add_sphere(v3(0.0, 1.1, 0.0), 1.1, lambert(0.75, 0.30, 0.25));
        add_sphere(v3(-2.3, 1.0, 0.2), 1.0, glass(1.5));
        add_sphere(v3(-2.3, 1.0, 0.2), -0.82, glass(1.5));
        add_sphere(v3(2.4, 1.0, -0.1), 1.0, metal(0.88, 0.72, 0.28, 0.03));
        add_sphere(v3(0.6, 0.35, 1.9), 0.35, lambert(0.10, 0.20, 0.85));
        add_sphere(v3(-0.95, 0.35, 1.7), 0.35, metal(0.20, 0.85, 0.45, 0.16));
        add_sphere(v3(3.8, 5.0, 2.2), 1.45, lightm(8.0, 7.6, 6.8));
        return make_camera(v3(6.7, 2.6, 6.8), v3(0, 1.0, 0.2), v3(0,1,0), cfg->vfov,
                           (double)cfg->width / (double)cfg->height, cfg->aperture,
                           cfg->focus_dist > 0.0 ? cfg->focus_dist : vlen(vsub(v3(6.7,2.6,6.8), v3(0,1.0,0.2))));
    }

    if (cfg->scene == SCENE_CORNELL_SPHERES) {
        add_sphere(v3(0,-10004,0), 10000, lambert(0.73, 0.73, 0.73));
        add_sphere(v3(-10007,0,0), 10000, lambert(0.75, 0.18, 0.18));
        add_sphere(v3(10007,0,0), 10000, lambert(0.18, 0.75, 0.22));
        add_sphere(v3(0,0,-10018), 10000, lambert(0.73, 0.73, 0.73));
        add_sphere(v3(0,10012,0), 10000, lambert(0.73, 0.73, 0.73));
        add_sphere(v3(0,11.4,0), 2.0, lightm(15.0, 14.0, 12.0));
        add_sphere(v3(-1.8, -2.6, -2.5), 2.2, glass(1.5));
        add_sphere(v3(-1.8, -2.6, -2.5), -1.8, glass(1.5));
        add_sphere(v3(2.2, -2.9, 1.0), 2.1, metal(0.86, 0.85, 0.82, 0.02));
        add_sphere(v3(0.0, -3.4, 3.1), 1.5, lambert(0.85, 0.75, 0.30));
        return make_camera(v3(0, 0.8, 13.5), v3(0, -1.2, 0), v3(0,1,0), cfg->vfov > 1.0 ? cfg->vfov : 35.0,
                           (double)cfg->width / (double)cfg->height, 0.0,
                           cfg->focus_dist > 0.0 ? cfg->focus_dist : 13.5);
    }

    if (cfg->scene == SCENE_RANDOM_BALLS) {
        int a, b;
        RNG rng;
        rng_seed(&rng, cfg->seed ^ 0xBADC0FFEE0DDF00DULL);
        add_sphere(v3(0,-1000,0), 1000, lambert(0.48, 0.50, 0.53));
        for (a = -8; a <= 8; ++a) {
            for (b = -8; b <= 8; ++b) {
                double choose = rng_next(&rng);
                Vec3 center = v3(a + 0.9 * rng_next(&rng), 0.2, b + 0.9 * rng_next(&rng));
                if (vlen(vsub(center, v3(4,0.2,0))) > 0.9) {
                    if (choose < 0.70) {
                        add_sphere(center, 0.2, lambert(rng_next(&rng)*rng_next(&rng), rng_next(&rng)*rng_next(&rng), rng_next(&rng)*rng_next(&rng)));
                    } else if (choose < 0.92) {
                        add_sphere(center, 0.2, metal(0.5*(1+rng_next(&rng)), 0.5*(1+rng_next(&rng)), 0.5*(1+rng_next(&rng)), 0.5*rng_next(&rng)));
                    } else {
                        add_sphere(center, 0.2, glass(1.5));
                    }
                }
            }
        }
        add_sphere(v3(0,1,0), 1.0, glass(1.5));
        add_sphere(v3(-4,1,0), 1.0, lambert(0.4, 0.2, 0.1));
        add_sphere(v3(4,1,0), 1.0, metal(0.7, 0.6, 0.5, 0.0));
        add_sphere(v3(0, 7, 0), 1.8, lightm(6.0, 5.7, 5.2));
        return make_camera(v3(13,2.2,3), v3(0,0.8,0), v3(0,1,0), cfg->vfov > 1.0 ? cfg->vfov : 20.0,
                           (double)cfg->width / (double)cfg->height, cfg->aperture > 0.0 ? cfg->aperture : 0.06,
                           cfg->focus_dist > 0.0 ? cfg->focus_dist : 10.0);
    }

    /* SCENE_GLASSES */
    add_sphere(v3(0,-1000,0), 1000, lambert(0.57, 0.57, 0.60));
    add_sphere(v3(-2.0, 1.0, 0.5), 1.0, glass(1.33));
    add_sphere(v3(-2.0, 1.0, 0.5), -0.82, glass(1.33));
    add_sphere(v3(0.0, 1.0, 0.0), 1.0, glass(1.5));
    add_sphere(v3(0.0, 1.0, 0.0), -0.82, glass(1.5));
    add_sphere(v3(2.1, 1.0, -0.5), 1.0, glass(1.8));
    add_sphere(v3(2.1, 1.0, -0.5), -0.82, glass(1.8));
    add_sphere(v3(-3.6, 0.45, 2.2), 0.45, metal(0.9, 0.85, 0.80, 0.0));
    add_sphere(v3(3.7, 5.2, 2.0), 1.4, lightm(7.5, 7.1, 6.7));
    return make_camera(v3(7.0, 2.2, 7.0), v3(0.0, 1.0, 0.0), v3(0,1,0), cfg->vfov,
                       (double)cfg->width / (double)cfg->height, cfg->aperture,
                       cfg->focus_dist > 0.0 ? cfg->focus_dist : vlen(vsub(v3(7.0,2.2,7.0), v3(0.0,1.0,0.0))));
}

/* --------------------------- Main --------------------------- */
int main(int argc, char **argv) {
    RenderConfig cfg;
    RenderContext ctx;
    double secs;
    size_t bytes;
    const char *ext;

    set_defaults(&cfg);
    parse_args(&cfg, argc, argv);

    bytes = (size_t)cfg.width * (size_t)cfg.height * 3u;
    ctx.cfg = cfg;
    ctx.cam = build_scene_and_camera(&cfg);
    ctx.img = (unsigned char*)malloc(bytes);
    if (!ctx.img) {
        fprintf(stderr, "Out of memory allocating %zu bytes\n", bytes);
        return 1;
    }

    ctx.tiles_x = (cfg.width + cfg.tile_size - 1) / cfg.tile_size;
    ctx.tiles_y = (cfg.height + cfg.tile_size - 1) / cfg.tile_size;
    ctx.total_tiles = ctx.tiles_x * ctx.tiles_y;
    ctx.start_clock = clock();

    if (!cfg.quiet) {
        printf("PathTracer++\n");
        printf("  scene   : %d\n", cfg.scene);
        printf("  image   : %dx%d\n", cfg.width, cfg.height);
        printf("  spp     : %d\n", cfg.spp);
        printf("  depth   : %d\n", cfg.max_depth);
        printf("  threads : %d\n", cfg.threads);
        printf("  output  : %s\n", cfg.output);
        printf("  seed    : %llu\n\n", (unsigned long long)cfg.seed);
    }

    render_image(&ctx);
    secs = (double)(clock() - ctx.start_clock) / CLOCKS_PER_SEC;

    ext = strrchr(cfg.output, '.');
    if (ext && streqi(ext, ".ppm")) {
        write_ppm(cfg.output, cfg.width, cfg.height, ctx.img);
    } else {
        write_bmp(cfg.output, cfg.width, cfg.height, ctx.img);
    }

    if (!cfg.quiet) {
        printf("Done in %.2f s\n", secs);
        printf("Saved %s\n", cfg.output);
    }

    free(ctx.img);
    return 0;
}
