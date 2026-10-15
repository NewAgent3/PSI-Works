"""
Brawl Clone - 3D Client
=======================
Ursina client with an in-game lobby, brawler picker, local hosting, and a
networked arena view driven by the authoritative server.
"""
import argparse
import asyncio
import importlib.util
import json
import math
import os
import shutil
import socket
import sys
import threading
import time
from pathlib import Path

try:
    from ursina import (
        AmbientLight,
        Button,
        DirectionalLight,
        Entity,
        InputField,
        Sky,
        Text,
        Ursina,
        Vec3,
        application,
        camera,
        color,
        destroy,
        held_keys,
        load_model,
        load_texture,
        mouse,
        scene,
        time as utime,
        window,
    )
    from ursina.models.procedural.cylinder import Cylinder
except ImportError:
    print("Ursina is not installed. Run install.bat or: python -m pip install -r requirements.txt")
    sys.exit(1)


ROOT_DIR = Path(__file__).resolve().parent.parent
SERVER_FILE = ROOT_DIR / "server" / "server.py"
ASSETS_DIR = ROOT_DIR / "assets"
GLB_DIR = ASSETS_DIR / "glb"
TEX_DIR = ASSETS_DIR / "textures"

BRAWLER_ORDER = ["spike", "edgar", "buzz", "damian", "lumi", "sirius", "alli", "kaze", "kit"]
MODEL_TEXTURE_ALIASES = {
    "alli": ["alli_tex.png", "alli_tex_highres.png"],
    "buzz": ["buzz_tex.png", "buzz_tex_highres.png"],
    "damian": ["damian_tex.png", "damian_tex_highres.png"],
    "edgar": ["edgar_tex.png", "edgar_tex_highres.png"],
    "kaze": ["kaze_tex.png", "kaze_tex_highres.png", "kaze_geisha_tex_highres.png"],
    "kit": ["kit_tex.png", "kit_tex_highres.png"],
    "lumi": ["lumi_tex.png", "lumi_tex_highres.png"],
    "sirius": ["sirius_tex.png", "sirius_tex_highres.png"],
    "spike": ["spike_tex.png", "spike_tex_highres.png"],
}
FALLBACK_BRAWLERS = {
    "spike": {"hp": 700, "speed": 6.2, "dmg": 70, "fire_rate": 0.55, "range": 18, "proj_speed": 22, "spread": 0.0, "shots": 1, "color": [0, 1, 0]},
    "edgar": {"hp": 1100, "speed": 8.0, "dmg": 110, "fire_rate": 0.40, "range": 6, "proj_speed": 30, "spread": 0.0, "shots": 1, "color": [1, 0, 0.4]},
    "buzz": {"hp": 1000, "speed": 6.6, "dmg": 90, "fire_rate": 0.50, "range": 7, "proj_speed": 28, "spread": 0.0, "shots": 1, "color": [1, 0.8, 0]},
    "damian": {"hp": 900, "speed": 6.0, "dmg": 80, "fire_rate": 0.60, "range": 14, "proj_speed": 22, "spread": 0.0, "shots": 1, "color": [0.6, 0, 1]},
    "lumi": {"hp": 650, "speed": 6.4, "dmg": 95, "fire_rate": 0.70, "range": 22, "proj_speed": 26, "spread": 0.0, "shots": 1, "color": [1, 0.9, 0.4]},
    "sirius": {"hp": 750, "speed": 6.2, "dmg": 85, "fire_rate": 0.65, "range": 20, "proj_speed": 24, "spread": 0.0, "shots": 1, "color": [0.2, 0.4, 1]},
    "alli": {"hp": 800, "speed": 6.3, "dmg": 75, "fire_rate": 0.55, "range": 16, "proj_speed": 22, "spread": 0.0, "shots": 1, "color": [0, 0.8, 1]},
    "kaze": {"hp": 700, "speed": 6.8, "dmg": 60, "fire_rate": 0.35, "range": 12, "proj_speed": 26, "spread": 0.0, "shots": 1, "color": [1, 0.3, 0.6]},
    "kit": {"hp": 850, "speed": 6.5, "dmg": 70, "fire_rate": 0.50, "range": 13, "proj_speed": 24, "spread": 0.15, "shots": 3, "color": [1, 0.6, 0.3]},
}

ACTIVE_APP = None
_SERVER_MODULE = None
HOST_BOT_COUNT = 3
KILL_FEED_LINES = 5
KILL_FEED_TTL = 4.0

# Screen-space UI palette (opaque — alpha panels vanish on some GPUs/drivers).
UI_WINDOW_BG = color.rgb(16, 22, 34)
UI_PANEL = color.rgb(24, 34, 52)
UI_PANEL_ALT = color.rgb(20, 28, 42)
UI_FIELD = color.rgb(40, 54, 78)
UI_FIELD_ACTIVE = color.rgb(58, 144, 218)
UI_LABEL = color.rgb(175, 190, 215)
UI_TEXT = color.white
UI_ACCENT = color.rgb(255, 210, 80)


def load_server_module():
    global _SERVER_MODULE
    if _SERVER_MODULE is not None:
        return _SERVER_MODULE
    spec = importlib.util.spec_from_file_location("brawl_clone_server", SERVER_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load server module from {SERVER_FILE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _SERVER_MODULE = module
    return module


def load_brawler_stats():
    try:
        return dict(load_server_module().BRAWLERS)
    except Exception:
        return dict(FALLBACK_BRAWLERS)


BRAWLER_STATS = load_brawler_stats()


def update():
    if ACTIVE_APP is not None:
        ACTIVE_APP.update()


def input(key):
    if ACTIVE_APP is not None:
        ACTIVE_APP.input(key)


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def display_name(name):
    return str(name).strip().title()


def apply_window_theme():
    window.color = UI_WINDOW_BG
    try:
        camera.clear_color = UI_WINDOW_BG
    except Exception:
        pass


def ui_panel(parent, position, scale, panel_color=None):
    return Entity(
        parent=parent,
        model="quad",
        color=panel_color or UI_PANEL,
        scale=scale,
        position=position,
        z=-0.1,
    )


def make_input_field(parent, default_value, position, scale, character_limit=24):
    field_bg = Entity(parent=parent, model="quad", color=UI_FIELD, scale=scale, position=position, z=-0.05)
    # InputField passes highlight_color internally; do not pass it here.
    field = InputField(
        default_value=default_value,
        parent=parent,
        scale=scale,
        position=position,
        character_limit=character_limit,
        color=UI_FIELD,
        text_color=UI_TEXT,
    )
    try:
        field.text_field.text_entity.color = UI_TEXT
    except Exception:
        pass
    field.field_bg = field_bg
    return field


def stat_to_color(rgb, alpha=255):
    values = []
    for c in rgb:
        values.append(int(c * 255) if c <= 1 else int(c))
    values = [clamp(v, 0, 255) for v in values]
    return color.rgba(values[0], values[1], values[2], alpha)


def ensure_texture_alias(brawler):
    source = TEX_DIR / f"{brawler}.png"
    if not source.exists():
        return
    for alias_name in MODEL_TEXTURE_ALIASES.get(brawler, [f"{brawler}_tex.png"]):
        alias = GLB_DIR / alias_name
        if alias.exists():
            continue
        try:
            os.link(source, alias)
        except OSError:
            try:
                shutil.copy2(source, alias)
            except OSError:
                pass


def brawler_model(brawler):
    ensure_texture_alias(brawler)
    try:
        return load_model(brawler, folder=GLB_DIR, use_deepcopy=True)
    except Exception as exc:
        print(f"[client] Failed to load model for {brawler}: {exc}")
        return None


def brawler_texture(brawler):
    try:
        return load_texture(brawler, folder=TEX_DIR)
    except Exception:
        return None


def clean_player_name(value):
    name = str(value or "").strip()
    return (name[:16] or f"P{os.getpid() % 1000}")


def parse_port(value):
    try:
        port = int(str(value).strip())
    except ValueError:
        return None
    return port if 1 <= port <= 65535 else None


class NetClient:
    def __init__(self, host, port, name, brawler, bots=0):
        self.host = host
        self.port = int(port)
        self.name = clean_player_name(name)
        self.brawler = brawler if brawler in BRAWLER_ORDER else "spike"
        self.bots = max(0, int(bots))
        self.sock = None
        self.file = None
        self.send_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.state = {"players": [], "projectiles": []}
        self.welcome = None
        self.my_pid = -1
        self.connected = False
        self.error = None

    def connect(self):
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=5)
            self.file = self.sock.makefile("rwb")
            join_msg = {"t": "join", "name": self.name, "brawler": self.brawler}
            if self.bots > 0:
                join_msg["bots"] = self.bots
            if not self._send(join_msg):
                return False

            line = self.file.readline()
            if not line:
                self.error = "Server closed the connection."
                self.close()
                return False

            msg = json.loads(line.decode("utf-8").strip())
            if msg.get("t") != "welcome":
                self.error = "Server sent an unexpected welcome packet."
                self.close()
                return False

            self.welcome = msg
            self.my_pid = int(msg["pid"])
            self.sock.settimeout(None)
            self.connected = True
            threading.Thread(target=self._reader, name="brawl-net-reader", daemon=True).start()
            return True
        except Exception as exc:
            self.error = str(exc)
            self.close()
            return False

    def _send(self, obj):
        if not self.sock:
            self.error = "Not connected."
            return False
        try:
            data = (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")
            with self.send_lock:
                self.sock.sendall(data)
            return True
        except Exception as exc:
            self.error = str(exc)
            self.connected = False
            return False

    def send_input(self, dx, dz, dt, yaw):
        if self.connected:
            self._send({"t": "input", "dx": dx, "dz": dz, "dt": dt, "yaw": yaw})

    def send_shoot(self, yaw):
        if self.connected:
            self._send({"t": "shoot", "yaw": yaw})

    def _reader(self):
        try:
            while self.connected:
                line = self.file.readline()
                if not line:
                    self.error = "Disconnected from server."
                    self.connected = False
                    return
                try:
                    msg = json.loads(line.decode("utf-8").strip())
                except Exception:
                    continue
                if msg.get("t") == "state":
                    with self.state_lock:
                        self.state = msg
        except Exception as exc:
            if self.connected:
                self.error = str(exc)
            self.connected = False

    def snapshot(self):
        with self.state_lock:
            return dict(self.state)

    def close(self):
        self.connected = False
        for obj in (self.file, self.sock):
            if obj:
                try:
                    obj.close()
                except Exception:
                    pass
        self.file = None
        self.sock = None


class EmbeddedServer:
    def __init__(self, port):
        self.port = int(port)
        self.thread = None
        self.error = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        self.error = None

        def runner():
            try:
                module = load_server_module()
                asyncio.run(module.GameServer("127.0.0.1", self.port).run())
            except OSError as exc:
                self.error = f"Could not host on port {self.port}: {exc}"
            except Exception as exc:
                self.error = f"Local server stopped: {exc}"

        self.thread = threading.Thread(target=runner, name="brawl-local-server", daemon=True)
        self.thread.start()


class PlayerView:
    def __init__(self, pid, brawler, brawler_stats, is_local=False):
        self.pid = pid
        self.brawler = brawler
        self.is_local = is_local
        self.target_x = 0.0
        self.target_z = 0.0
        self.target_yaw = 0.0
        self.initialized = False
        self.alive = True
        self.hidden = False

        self.entity = self._make_model(brawler, brawler_stats)
        self.shadow = Entity(model="circle", color=color.rgba(0, 0, 0, 80), scale=1.15, rotation_x=90, y=0.035)
        self.name_text = Text(
            text="",
            parent=scene,
            billboard=True,
            origin=(0, 0),
            scale=1.0,
            color=color.white,
            background=True,
        )
        self.hp_bg = Entity(
            parent=scene,
            model="quad",
            billboard=True,
            color=color.rgba(20, 20, 28, 210),
            scale=(1.42, 0.14, 1),
        )
        self.hp_bar = Entity(
            parent=scene,
            model="quad",
            billboard=True,
            color=color.lime,
            origin=(-0.5, 0),
            scale=(1.36, 0.09, 1),
        )
        self._set_overlay_enabled(False)

    def _make_model(self, brawler, brawler_stats):
        model = brawler_model(brawler)
        if model:
            try:
                entity = Entity(model=model, scale=0.012, position=(0, 0, 0))
                texture = brawler_texture(brawler)
                if texture:
                    entity.texture = texture
                return entity
            except Exception as exc:
                print(f"[client] Failed to create {brawler} model: {exc}")
        return Entity(
            model="cube",
            color=stat_to_color(brawler_stats.get("color", [1, 1, 1])),
            scale=(0.8, 1.4, 0.8),
            position=(0, 0.7, 0),
        )

    def update_from(self, data):
        self.hidden = bool(data.get("hidden"))
        if self.hidden:
            self.entity.enabled = False
            self.shadow.enabled = False
            self._set_overlay_enabled(False)
            return

        self.target_x = float(data["x"])
        self.target_z = float(data["z"])
        self.target_yaw = float(data["yaw"])
        self.alive = bool(data["alive"])

        if not self.initialized:
            self.entity.x = self.target_x
            self.entity.z = self.target_z
            self.shadow.x = self.target_x
            self.shadow.z = self.target_z
            self.initialized = True

        hp_ratio = clamp(float(data["hp"]) / max(1.0, float(data["max_hp"])), 0.0, 1.0)
        self.hp_bar.scale_x = max(0.01, 1.36 * hp_ratio)
        self.hp_bar.color = color.lime if hp_ratio > 0.6 else color.yellow if hp_ratio > 0.3 else color.red

        tag = " [BOT]" if data.get("is_bot") else ""
        bush_tag = " (bush)" if data.get("in_bush") and self.is_local else ""
        self.name_text.text = f"{data['name']}{tag}{bush_tag}"
        self.name_text.color = color.azure if self.is_local else color.white

        alpha = 0.45 if data.get("in_bush") else 1.0
        self.entity.alpha = alpha
        for child in self.entity.children:
            if hasattr(child, "alpha"):
                child.alpha = alpha

        self.entity.enabled = self.alive
        self.shadow.enabled = self.alive
        self._set_overlay_enabled(self.alive)

    def lerp(self, dt):
        if not self.initialized:
            return
        k = min(1.0, dt * 14)
        self.entity.x += (self.target_x - self.entity.x) * k
        self.entity.z += (self.target_z - self.entity.z) * k
        self.shadow.x = self.entity.x
        self.shadow.z = self.entity.z

        target_deg = math.degrees(self.target_yaw)
        current = self.entity.rotation_y
        diff = (target_deg - current + 540) % 360 - 180
        self.entity.rotation_y = current + diff * k
        self._position_overlays()

    def _position_overlays(self):
        x = self.entity.x
        z = self.entity.z
        self.name_text.position = (x, 3.05, z)
        self.hp_bg.position = (x, 2.65, z)
        self.hp_bar.position = (x - 0.68, 2.65, z - 0.01)

    def _set_overlay_enabled(self, enabled):
        self.name_text.enabled = enabled
        self.hp_bg.enabled = enabled
        self.hp_bar.enabled = enabled

    def destroy(self):
        destroy(self.entity)
        destroy(self.shadow)
        destroy(self.name_text)
        destroy(self.hp_bg)
        destroy(self.hp_bar)


class ProjectileView:
    def __init__(self, oid, x, z, projectile_color):
        self.oid = oid
        body_color = stat_to_color(projectile_color)
        glow_color = stat_to_color(projectile_color, alpha=90)
        self.entity = Entity(model="sphere", color=body_color, scale=0.38, position=(x, 0.85, z))
        self.glow = Entity(parent=self.entity, model="sphere", color=glow_color, scale=2.1)
        self.shadow = Entity(model="circle", color=color.rgba(0, 0, 0, 55), scale=0.5, rotation_x=90, position=(x, 0.04, z))

    def update(self, x, z):
        self.entity.x = x
        self.entity.z = z
        self.shadow.x = x
        self.shadow.z = z

    def destroy(self):
        destroy(self.entity)
        destroy(self.shadow)


class MuzzleFlash:
    def __init__(self, x, z, yaw, flash_color):
        self.life = 0.12
        self.entity = Entity(
            model="sphere",
            color=stat_to_color(flash_color, alpha=200),
            scale=0.55,
            position=(x + math.sin(yaw) * 0.7, 1.0, z + math.cos(yaw) * 0.7),
        )
        Entity(parent=self.entity, model="sphere", color=color.rgba(255, 255, 255, 90), scale=1.8)

    def update(self, dt):
        self.life -= dt
        if self.entity:
            self.entity.scale *= max(0.0, 1 - dt * 9)
        return self.life > 0

    def destroy(self):
        destroy(self.entity)


class MatchScene:
    def __init__(self, shell, net):
        self.shell = shell
        self.net = net
        self.root = Entity(name="match-root")
        self.brawler_stats = net.welcome["brawlers"]
        self.arena_r = float(net.welcome["arena"])
        self.match_duration = float(net.welcome.get("match_duration", 0))
        self.player_views = {}
        self.proj_views = {}
        self.muzzle_flashes = []
        self.aim_world = Vec3(0, 0, 1)
        self.current_yaw = 0.0
        self.last_shot = 0.0
        self.last_input_send = 0.0
        self.me = None
        self.last_kills = {}
        self.last_deaths = {}
        self.kill_feed = []
        self.winner_pid = -1
        self.match_over = False

        self._build_world()
        self._build_hud()

        camera.orthographic = False
        camera.fov = 48
        self.cam_offset = Vec3(0, 23, -15)
        camera.position = self.cam_offset
        camera.rotation = (55, 0, 0)

    def _build_world(self):
        r = self.arena_r
        Sky(color=color.rgb(72, 148, 196))
        DirectionalLight(parent=self.root, y=20, rotation=(50, -30, 0), shadows=False)
        AmbientLight(parent=self.root, color=color.rgba(140, 150, 170, 255))
        Entity(parent=self.root, model=Cylinder(resolution=64), color=color.rgb(70, 58, 46), scale=(r * 2.08, 0.34, r * 2.08), position=(0, -0.2, 0))
        Entity(parent=self.root, model=Cylinder(resolution=64), color=color.rgb(94, 156, 88), scale=(r * 2.0, 0.22, r * 2.0), position=(0, -0.08, 0))
        Entity(parent=self.root, model="circle", color=color.rgba(255, 255, 255, 42), scale=r * 1.98, rotation_x=90, y=0.02)

        self.ground_pick = Entity(parent=self.root, model="plane", collider="box", visible=False, scale=(r * 2.2, 1, r * 2.2), y=0)

        for i in range(-int(r), int(r) + 1, 4):
            Entity(parent=self.root, model="cube", color=color.rgba(255, 255, 255, 16), scale=(r * 2, 0.01, 0.035), position=(0, 0.012, i))
            Entity(parent=self.root, model="cube", color=color.rgba(255, 255, 255, 16), scale=(0.035, 0.01, r * 2), position=(i, 0.012, 0))

        for wall in self.net.welcome["walls"]:
            Entity(
                parent=self.root,
                model="cube",
                color=color.rgb(171, 111, 66),
                scale=(wall["w"], 1.8, wall["h"]),
                position=(wall["x"], 0.9, wall["z"]),
                texture="white_cube",
            )
            Entity(
                parent=self.root,
                model="cube",
                color=color.rgb(99, 62, 39),
                scale=(wall["w"] * 1.05, 0.18, wall["h"] * 1.05),
                position=(wall["x"], 1.84, wall["z"]),
            )

        for bush in self.net.welcome["bushes"]:
            base = Entity(
                parent=self.root,
                model="sphere",
                color=color.rgb(37, 126, 64),
                scale=(bush["r"] * 2, 1.2, bush["r"] * 2),
                position=(bush["x"], 0.35, bush["z"]),
            )
            Entity(parent=base, model="sphere", color=color.rgb(73, 166, 78), scale=(0.62, 0.62, 0.62), position=(0.35, 0.25, 0.25))
            Entity(parent=base, model="sphere", color=color.rgb(59, 151, 70), scale=(0.52, 0.52, 0.52), position=(-0.35, 0.2, -0.25))

        self.reticle = Entity(parent=self.root, model="circle", color=color.rgba(255, 64, 64, 190), scale=1.35, rotation_x=90, y=0.06)
        self.reticle_dot = Entity(parent=self.reticle, model="sphere", color=color.rgba(255, 255, 255, 230), scale=0.08, y=0.02)

    def _build_hud(self):
        self.hud_root = Entity(parent=camera.ui)
        self.status_panel = Entity(parent=self.hud_root, model="quad", color=color.rgba(13, 18, 28, 190), scale=(0.46, 0.13), position=(-0.64, 0.41))
        self.hud_status = Text(text="", parent=self.hud_root, position=(-0.84, 0.445), scale=0.9, color=color.white)
        self.hp_bg = Entity(parent=self.hud_root, model="quad", color=color.rgba(0, 0, 0, 150), scale=(0.34, 0.025), position=(-0.67, 0.395), origin=(-0.5, 0))
        self.hp_fill = Entity(parent=self.hud_root, model="quad", color=color.lime, scale=(0.34, 0.025), position=(-0.67, 0.395), origin=(-0.5, 0))
        self.hud_center = Text(text="", parent=self.hud_root, origin=(0, 0), scale=2.2, color=color.red, position=(0, 0.04))
        self.hud_timer = Text(text="", parent=self.hud_root, origin=(0, 0), scale=1.35, color=color.white, position=(0, 0.44))
        self.hud_kill_feed = Text(
            text="",
            parent=self.hud_root,
            origin=(1, 0),
            scale=0.78,
            color=color.light_gray,
            position=(0.48, 0.32),
        )

        self.score_panel = Entity(parent=self.hud_root, model="quad", color=color.rgba(13, 18, 28, 220), scale=(0.58, 0.48), position=(0, 0.18), enabled=False)
        self.hud_scoreboard = Text(text="", parent=self.hud_root, position=(-0.25, 0.37), scale=0.82, color=color.white, enabled=False)

        self.end_panel = Entity(parent=self.hud_root, model="quad", color=color.rgba(8, 10, 18, 230), scale=(0.72, 0.42), position=(0, 0.02), enabled=False)
        self.hud_end_title = Text(text="", parent=self.hud_root, origin=(0, 0), scale=2.4, color=color.gold, position=(0, 0.12), enabled=False)
        self.hud_end_sub = Text(text="", parent=self.hud_root, origin=(0, 0), scale=1.0, color=color.white, position=(0, -0.02), enabled=False)
        self.hud_end_hint = Text(
            text="Press Esc to return to lobby",
            parent=self.hud_root,
            origin=(0, 0),
            scale=0.75,
            color=color.light_gray,
            position=(0, -0.14),
            enabled=False,
        )

    def update(self, dt):
        if not self.net.connected:
            self.hud_center.text = self.net.error or "Disconnected from server."
            return

        state = self.net.snapshot()
        self.me = self._find_me(state)

        self._handle_movement_and_aim()
        self._sync_players(state, dt)
        self._sync_projectiles(state)
        self._update_muzzle_flashes(dt)
        self._update_kill_feed(dt)
        self._track_kills(state)
        self._update_match_result(state)
        self._update_camera()
        self._update_hud(state)

    def input(self, key):
        if key == "escape":
            self.shell.return_to_menu("Left match.")
        elif key in ("left mouse down", "space"):
            self._try_shoot(time.time())

    def _find_me(self, state):
        for player in state.get("players", []):
            if player["pid"] == self.net.my_pid:
                return player
        return None

    def _handle_movement_and_aim(self):
        if self.match_over:
            return
        dx = (held_keys["d"] + held_keys["right arrow"]) - (held_keys["a"] + held_keys["left arrow"])
        dz = (held_keys["w"] + held_keys["up arrow"]) - (held_keys["s"] + held_keys["down arrow"])

        if mouse.world_point is not None:
            point = mouse.world_point
            if math.isfinite(point.x) and math.isfinite(point.z):
                self.aim_world = Vec3(point.x, 0, point.z)

        if self.me:
            yaw_dx = self.aim_world.x - self.me["x"]
            yaw_dz = self.aim_world.z - self.me["z"]
            if abs(yaw_dx) > 0.001 or abs(yaw_dz) > 0.001:
                self.current_yaw = math.atan2(yaw_dx, yaw_dz)

        now = time.time()
        if now - self.last_input_send >= 1 / 30:
            dt = 1 / 30 if self.last_input_send <= 0 else now - self.last_input_send
            self.net.send_input(dx, dz, dt, self.current_yaw)
            self.last_input_send = now

        try:
            shooting = bool(mouse.left or held_keys["space"])
        except Exception:
            shooting = bool(held_keys["space"])
        if shooting:
            self._try_shoot(now)

        self.reticle.position = (self.aim_world.x, 0.06, self.aim_world.z)

    def _try_shoot(self, now):
        if not self.me or not self.me["alive"] or self.match_over:
            return
        stats = self.brawler_stats[self.me["brawler"]]
        if now - self.last_shot >= float(stats["fire_rate"]):
            self.net.send_shoot(self.current_yaw)
            self.last_shot = now
            self._spawn_muzzle(self.me["x"], self.me["z"], self.current_yaw, stats.get("color", [1, 1, 1]))

    def _spawn_muzzle(self, x, z, yaw, rgb):
        self.muzzle_flashes.append(MuzzleFlash(x, z, yaw, rgb))

    def _update_muzzle_flashes(self, dt):
        alive = []
        for flash in self.muzzle_flashes:
            if flash.update(dt):
                alive.append(flash)
            else:
                flash.destroy()
        self.muzzle_flashes = alive

    def _track_kills(self, state):
        killers = []
        victims = []
        for player in state.get("players", []):
            pid = player["pid"]
            prev_k = self.last_kills.get(pid, 0)
            prev_d = self.last_deaths.get(pid, 0)
            if player["kills"] > prev_k:
                killers.append(player)
            if player["deaths"] > prev_d:
                victims.append(player)
            self.last_kills[pid] = player["kills"]
            self.last_deaths[pid] = player["deaths"]

        if killers and victims:
            killer = killers[0]
            victim = victims[0]
            line = f"{killer['name']} eliminated {victim['name']}"
            self.kill_feed.insert(0, (line, time.time()))
            self.kill_feed = self.kill_feed[:KILL_FEED_LINES]

    def _update_kill_feed(self, dt):
        now = time.time()
        self.kill_feed = [(line, born) for line, born in self.kill_feed if now - born < KILL_FEED_TTL]
        self.hud_kill_feed.text = "\n".join(line for line, _ in self.kill_feed)

    def _update_match_result(self, state):
        winner = int(state.get("winner_pid", -1))
        if winner < 0:
            return
        if self.winner_pid == winner:
            return
        self.winner_pid = winner
        self.match_over = True
        winner_name = "Nobody"
        for player in state.get("players", []):
            if player["pid"] == winner:
                winner_name = player["name"]
                break
        you_won = winner == self.net.my_pid
        self.end_panel.enabled = True
        self.hud_end_title.enabled = True
        self.hud_end_sub.enabled = True
        self.hud_end_hint.enabled = True
        self.hud_end_title.text = "VICTORY!" if you_won else "MATCH OVER"
        self.hud_end_title.color = color.gold if you_won else color.azure
        self.hud_end_sub.text = f"{winner_name} wins the match"

    def _sync_players(self, state, dt):
        seen = set()
        for player in state.get("players", []):
            pid = player["pid"]
            seen.add(pid)
            if pid not in self.player_views:
                stats = self.brawler_stats[player["brawler"]]
                self.player_views[pid] = PlayerView(pid, player["brawler"], stats, is_local=(pid == self.net.my_pid))
            self.player_views[pid].update_from(player)

        for pid in list(self.player_views):
            if pid not in seen:
                self.player_views[pid].destroy()
                del self.player_views[pid]

        for view in self.player_views.values():
            view.lerp(dt)

    def _sync_projectiles(self, state):
        seen = set()
        for projectile in state.get("projectiles", []):
            oid = projectile["oid"]
            seen.add(oid)
            if oid not in self.proj_views:
                self.proj_views[oid] = ProjectileView(oid, projectile["x"], projectile["z"], projectile["color"])
            else:
                self.proj_views[oid].update(projectile["x"], projectile["z"])

        for oid in list(self.proj_views):
            if oid not in seen:
                self.proj_views[oid].destroy()
                del self.proj_views[oid]

    def _update_camera(self):
        if not self.me:
            return
        target = Vec3(self.me["x"] + self.cam_offset.x, self.cam_offset.y, self.me["z"] + self.cam_offset.z)
        camera.position = camera.position + (target - camera.position) * min(1, utime.dt * 6)
        camera.look_at(Vec3(self.me["x"], 0, self.me["z"] + 2))

    def _format_time(self, seconds):
        seconds = max(0, int(seconds))
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:01d}:{secs:02d}"

    def _update_hud(self, state):
        players = state.get("players", [])
        time_left = float(state.get("time_left", 0))
        if self.match_duration > 0 and not self.match_over:
            self.hud_timer.text = self._format_time(time_left)
            self.hud_timer.color = color.red if time_left <= 30 else color.white
        else:
            self.hud_timer.text = ""

        if self.me:
            hp_ratio = clamp(float(self.me["hp"]) / max(1.0, float(self.me["max_hp"])), 0.0, 1.0)
            self.hp_fill.scale_x = max(0.001, 0.34 * hp_ratio)
            self.hp_fill.color = color.lime if hp_ratio > 0.6 else color.yellow if hp_ratio > 0.3 else color.red
            self.hud_status.text = (
                f"{self.me['brawler'].upper()}  HP {int(self.me['hp'])}/{int(self.me['max_hp'])}\n"
                f"K {self.me['kills']}  D {self.me['deaths']}  Online {len(players)}"
            )
            if self.me["alive"]:
                self.hud_center.text = ""
            else:
                self.hud_center.text = f"Respawn in {self.me['respawn_in']:.1f}s"

        show_scoreboard = bool(held_keys["tab"])
        self.score_panel.enabled = show_scoreboard
        self.hud_scoreboard.enabled = show_scoreboard
        if show_scoreboard:
            rows = sorted(players, key=lambda p: (-p["kills"], p["deaths"], p["name"].lower()))
            lines = ["SCOREBOARD", f"{'Name':<14} {'Brawler':<9} {'K':>2} {'D':>2}"]
            for player in rows:
                marker = ">" if player["pid"] == self.net.my_pid else " "
                lines.append(f"{marker}{player['name'][:13]:<13} {player['brawler'][:9]:<9} {player['kills']:>2} {player['deaths']:>2}")
            self.hud_scoreboard.text = "\n".join(lines)

    def destroy(self):
        self.net.close()
        for view in list(self.player_views.values()):
            view.destroy()
        for view in list(self.proj_views.values()):
            view.destroy()
        for flash in self.muzzle_flashes:
            flash.destroy()
        destroy(self.root)
        destroy(self.hud_root)


class MainMenu:
    def __init__(self, shell, args):
        self.shell = shell
        self.args = args
        self.selected_brawler = args.brawler or "spike"
        self.buttons_by_brawler = {}
        self.busy = False
        self.preview_entity = None
        self.preview_pivot = None

        apply_window_theme()
        self.ui_backdrop = Entity(
            parent=camera.ui,
            model="quad",
            color=UI_WINDOW_BG,
            scale=(2, 2),
            position=(0, 0),
            z=-90,
        )
        self.world_root = Entity(name="menu-world")
        self.root = Entity(parent=camera.ui, name="menu-ui", z=0)
        self.stat_fills = {}
        self._build_world()
        self._build_ui()
        self.select_brawler(self.selected_brawler)

    def _build_world(self):
        camera.orthographic = False
        camera.fov = 50
        camera.position = (0, 5.2, -10)
        camera.rotation = (22, 0, 0)
        Sky(color=color.rgb(28, 45, 64))
        DirectionalLight(parent=self.world_root, y=8, z=-5, rotation=(45, -25, 0), shadows=False)
        AmbientLight(parent=self.world_root, color=color.rgba(130, 140, 170, 255))
        Entity(parent=self.world_root, model=Cylinder(resolution=64), color=color.rgb(53, 121, 102), scale=(12, 0.22, 12), y=-0.18)
        Entity(parent=self.world_root, model=Cylinder(resolution=64), color=color.rgb(26, 38, 54), scale=(13.2, 0.2, 13.2), y=-0.32)
        self.preview_stage = Entity(parent=self.world_root, position=(0, 0, 1.2))
        Entity(
            parent=self.preview_stage,
            model=Cylinder(resolution=32),
            color=color.rgb(42, 58, 78),
            scale=(2.4, 0.12, 2.4),
            y=0.02,
        )
        self.preview_pivot = Entity(parent=self.preview_stage, position=(0, 0.6, 0))
        for x, z, sx, sz in [(-4, 1.8, 1.6, 2.4), (4, 0.9, 2.2, 1.4), (0, 3.6, 1.8, 1.8)]:
            Entity(parent=self.world_root, model="cube", color=color.rgb(169, 108, 65), scale=(sx, 1.2, sz), position=(x, 0.42, z))
        for x, z in [(-3.1, -2.2), (3.4, -2.5), (0.9, 2.1)]:
            Entity(parent=self.world_root, model="sphere", color=color.rgb(47, 149, 76), scale=(1.8, 0.8, 1.8), position=(x, 0.25, z))

    def _build_ui(self):
        Text("BRAWL CLONE", parent=self.root, position=(-0.83, 0.42), scale=2.1, color=UI_ACCENT)
        Text("ARENA LOBBY", parent=self.root, position=(-0.82, 0.35), scale=0.9, color=color.azure)

        ui_panel(self.root, (-0.61, 0.08), (0.47, 0.45))
        ui_panel(self.root, (0.25, -0.12), (0.74, 0.38))
        ui_panel(self.root, (0.63, 0.18), (0.34, 0.42), UI_PANEL_ALT)

        Text("Player name", parent=self.root, position=(-0.82, 0.25), scale=0.82, color=UI_LABEL)
        self.name_field = make_input_field(
            self.root,
            clean_player_name(self.args.name),
            (-0.62, 0.22),
            (0.34, 0.055),
            character_limit=16,
        )

        Text("Server IP", parent=self.root, position=(-0.82, 0.14), scale=0.82, color=UI_LABEL)
        self.host_field = make_input_field(
            self.root,
            str(self.args.host),
            (-0.62, 0.11),
            (0.34, 0.055),
            character_limit=40,
        )

        Text("Port", parent=self.root, position=(-0.82, 0.03), scale=0.82, color=UI_LABEL)
        self.port_field = make_input_field(
            self.root,
            str(self.args.port),
            (-0.70, 0.00),
            (0.18, 0.055),
            character_limit=5,
        )
        self.port_field.limit_content_to = "0123456789"
        self.name_field.next_field = self.host_field
        self.host_field.next_field = self.port_field
        self.port_field.next_field = self.name_field

        self.host_button = self._make_button("Host Local", (-0.72, -0.17), (0.22, 0.065), color.rgb(229, 151, 57), self.start_host)
        self.join_button = self._make_button("Join Server", (-0.49, -0.17), (0.22, 0.065), color.rgb(58, 144, 218), self.start_join)
        Text(
            f"Host Local adds {HOST_BOT_COUNT} bots for practice",
            parent=self.root,
            position=(-0.82, -0.24),
            scale=0.65,
            color=UI_LABEL,
        )
        self.quit_button = self._make_button("Quit", (-0.61, -0.27), (0.22, 0.055), color.rgb(115, 88, 132), application.quit)

        self.status_text = Text("", parent=self.root, position=(-0.82, -0.36), scale=0.75, color=color.yellow)

        Text("Choose brawler", parent=self.root, position=(-0.08, 0.035), scale=1.0, color=UI_TEXT)
        x0, y0 = -0.08, -0.05
        for index, name in enumerate(BRAWLER_ORDER):
            row = index // 3
            col = index % 3
            pos = (x0 + col * 0.20, y0 - row * 0.095)
            button = self._make_button(display_name(name), pos, (0.18, 0.07), color.rgb(45, 63, 82), lambda n=name: self.select_brawler(n))
            self.buttons_by_brawler[name] = button

        self.selected_title = Text("", parent=self.root, position=(0.49, 0.35), scale=1.2, color=UI_TEXT)
        self.selected_note = Text("", parent=self.root, position=(0.49, 0.29), scale=0.72, color=color.azure)
        self.stats_text = Text("", parent=self.root, position=(0.49, 0.21), scale=0.72, color=UI_LABEL)
        self._make_stat_rows()

    def _make_stat_rows(self):
        labels = ["HP", "Speed", "Damage", "Range", "Rate"]
        for i, label in enumerate(labels):
            y = 0.09 - i * 0.055
            Text(label, parent=self.root, position=(0.49, y + 0.008), scale=0.62, color=UI_LABEL)
            Entity(parent=self.root, model="quad", color=color.rgb(10, 12, 18), scale=(0.18, 0.018), position=(0.67, y), origin=(-0.5, 0))
            fill = Entity(parent=self.root, model="quad", color=color.azure, scale=(0.01, 0.018), position=(0.67, y), origin=(-0.5, 0))
            self.stat_fills[label] = fill

    def _make_button(self, text, position, scale, button_color, callback):
        return Button(
            text=text,
            parent=self.root,
            position=position,
            scale=scale,
            color=button_color,
            text_color=color.white,
            highlight_color=color.rgba(255, 255, 255, 230),
            pressed_color=color.rgb(35, 45, 60),
            on_click=callback,
        )

    def start_host(self):
        self.shell.connect_from_menu(host_local=True)

    def start_join(self):
        self.shell.connect_from_menu(host_local=False)

    def get_settings(self):
        return {
            "name": clean_player_name(self.name_field.text),
            "host": str(self.host_field.text or "127.0.0.1").strip() or "127.0.0.1",
            "port": parse_port(self.port_field.text),
            "brawler": self.selected_brawler,
        }

    def select_brawler(self, name):
        if name not in BRAWLER_ORDER:
            name = "spike"
        self.selected_brawler = name
        stats = BRAWLER_STATS.get(name, FALLBACK_BRAWLERS[name])
        accent = stat_to_color(stats.get("color", [1, 1, 1]))

        for brawler, button in self.buttons_by_brawler.items():
            button.color = accent if brawler == name else color.rgb(45, 63, 82)

        self.selected_title.text = display_name(name)
        self.selected_note.text = "3-shot spread" if stats.get("shots", 1) > 1 else "Single shot"
        self.stats_text.text = (
            f"HP {stats['hp']}\n"
            f"Damage {stats['dmg']}\n"
            f"Cooldown {stats['fire_rate']:.2f}s"
        )

        values = {
            "HP": stats["hp"] / 1100,
            "Speed": stats["speed"] / 8,
            "Damage": stats["dmg"] / 110,
            "Range": stats["range"] / 22,
            "Rate": (1 / stats["fire_rate"]) / (1 / 0.35),
        }
        for label, value in values.items():
            fill = self.stat_fills[label]
            fill.scale_x = max(0.01, 0.18 * clamp(value, 0.0, 1.0))
            fill.color = accent

        self._set_preview(name, accent)

    def _set_preview(self, name, accent):
        if self.preview_entity:
            destroy(self.preview_entity)
            self.preview_entity = None
        parent = self.preview_pivot or self.world_root
        model = brawler_model(name)
        if model:
            self.preview_entity = Entity(
                parent=parent,
                model=model,
                scale=0.024,
                rotation_y=200,
                rotation_x=-12,
                double_sided=True,
            )
            texture = brawler_texture(name)
            if texture:
                self.preview_entity.texture = texture
            bounds = getattr(self.preview_entity, "bounds", None)
            if bounds is not None:
                height = max(getattr(bounds, "height", 1), 0.01)
                target_height = 2.2
                self.preview_entity.scale *= target_height / height
        else:
            self.preview_entity = Entity(parent=parent, model="cube", scale=(1.1, 1.8, 1.1), color=accent)

    def set_status(self, text, status_color=None):
        self.status_text.text = text
        self.status_text.color = status_color or color.yellow

    def set_busy(self, busy):
        self.busy = busy
        for button in [self.host_button, self.join_button, self.quit_button, *self.buttons_by_brawler.values()]:
            button.disabled = busy
        if busy:
            self.host_button.color = color.rgb(87, 91, 102)
            self.join_button.color = color.rgb(87, 91, 102)
        else:
            self.host_button.color = color.rgb(229, 151, 57)
            self.join_button.color = color.rgb(58, 144, 218)
            self.select_brawler(self.selected_brawler)

    def show(self):
        apply_window_theme()
        self.ui_backdrop.enabled = True
        self.root.enabled = True
        self.world_root.enabled = True
        camera.orthographic = False
        camera.fov = 50
        camera.position = (0, 5.2, -10)
        camera.rotation = (22, 0, 0)

    def hide(self):
        self.ui_backdrop.enabled = False
        self.root.enabled = False
        self.world_root.enabled = False

    def update(self, dt):
        if self.preview_entity:
            self.preview_entity.rotation_y += dt * 35

    def input(self, key):
        if key == "escape":
            application.quit()
        if self.busy or self._typing_in_field():
            return
        if key == "enter":
            self.start_join()
        elif key == "left arrow":
            self._cycle_brawler(-1)
        elif key == "right arrow":
            self._cycle_brawler(1)

    def _cycle_brawler(self, step):
        idx = BRAWLER_ORDER.index(self.selected_brawler)
        self.select_brawler(BRAWLER_ORDER[(idx + step) % len(BRAWLER_ORDER)])

    def _typing_in_field(self):
        return any(field.active for field in (self.name_field, self.host_field, self.port_field))


class BrawlClientApp:
    def __init__(self, args):
        global ACTIVE_APP
        ACTIVE_APP = self
        self.args = args
        self.app = Ursina(title="Brawl Clone", borderless=False, fullscreen=False, development_mode=False, vsync=True)
        apply_window_theme()
        window.fullscreen = False
        try:
            window.fps_counter.enabled = False
            window.exit_button.visible = True
        except Exception:
            pass

        self.mode = "menu"
        self.menu = MainMenu(self, args)
        self.match = None
        self.local_server = None
        self.connection_lock = threading.Lock()
        self.connection_result = None
        self.connection_thread = None

        if args.no_menu:
            self.connect_direct(args)

    def connect_direct(self, args):
        if not args.brawler:
            args.brawler = "spike"
        self.menu.hide()
        self.connect_from_values(
            host="127.0.0.1" if args.host_local else args.host,
            port=args.port,
            name=args.name,
            brawler=args.brawler,
            host_local=args.host_local,
        )

    def connect_from_menu(self, host_local=False):
        values = self.menu.get_settings()
        if values["port"] is None:
            self.menu.set_status("Port must be between 1 and 65535.", color.red)
            return
        host = "127.0.0.1" if host_local else values["host"]
        self.connect_from_values(host, values["port"], values["name"], values["brawler"], host_local)

    def connect_from_values(self, host, port, name, brawler, host_local=False):
        self.mode = "connecting"
        self.menu.show()
        self.menu.set_busy(True)
        action = "Hosting local match" if host_local else f"Connecting to {host}:{port}"
        self.menu.set_status(f"{action}...")
        with self.connection_lock:
            self.connection_result = None

        if host_local:
            self.local_server = EmbeddedServer(port)
            self.local_server.start()

        self.connection_thread = threading.Thread(
            target=self._connect_worker,
            args=(host, port, name, brawler, host_local),
            name="brawl-connect-worker",
            daemon=True,
        )
        self.connection_thread.start()

    def _connect_worker(self, host, port, name, brawler, host_local):
        deadline = time.time() + (7 if host_local else 0)
        last_error = None
        bot_count = HOST_BOT_COUNT if host_local else 0
        while True:
            net = NetClient(host, port, name, brawler, bots=bot_count)
            if net.connect():
                with self.connection_lock:
                    self.connection_result = (net, None)
                return
            last_error = net.error or "Could not connect."
            net.close()
            if not host_local or time.time() >= deadline:
                break
            time.sleep(0.25)

        with self.connection_lock:
            self.connection_result = (None, last_error)

    def update(self):
        dt = utime.dt
        if self.mode in ("menu", "connecting"):
            self.menu.update(dt)
        if self.mode == "connecting":
            self._poll_connection()
        elif self.mode == "playing" and self.match:
            self.match.update(dt)

    def input(self, key):
        if self.mode in ("menu", "connecting"):
            self.menu.input(key)
        elif self.mode == "playing" and self.match:
            self.match.input(key)

    def _poll_connection(self):
        if self.local_server and self.local_server.error:
            self.menu.set_status(self.local_server.error, color.red)

        with self.connection_lock:
            result = self.connection_result
            self.connection_result = None

        if result is None:
            return

        net, error = result
        self.menu.set_busy(False)
        if net:
            self.start_match(net)
        else:
            self.mode = "menu"
            self.menu.set_status(f"Connection failed: {error}", color.red)

    def start_match(self, net):
        self.menu.hide()
        if self.match:
            self.match.destroy()
        self.match = MatchScene(self, net)
        self.mode = "playing"

    def return_to_menu(self, message=""):
        if self.match:
            self.match.destroy()
            self.match = None
        self.mode = "menu"
        self.menu.show()
        self.menu.set_busy(False)
        if message:
            self.menu.set_status(message, color.azure)

    def run(self):
        self.app.run()


def parse_args():
    parser = argparse.ArgumentParser(description="Brawl Clone client")
    parser.add_argument("--host", default="127.0.0.1", help="Server host for direct connect or menu default.")
    parser.add_argument("--port", type=int, default=5555, help="Server port.")
    parser.add_argument("--name", default=f"P{os.getpid() % 1000}", help="Player name.")
    parser.add_argument("--brawler", choices=BRAWLER_ORDER, default=None, help="Brawler for direct connect or menu default.")
    parser.add_argument("--no-menu", action="store_true", help="Skip the lobby and connect immediately.")
    parser.add_argument("--host-local", action="store_true", help="Start an embedded local server before connecting.")
    parser.add_argument("--no-prompt", action="store_true", help="Compatibility flag; prompts have been replaced by the lobby.")
    return parser.parse_args()


def main():
    args = parse_args()
    app = BrawlClientApp(args)
    app.run()


if __name__ == "__main__":
    main()
