"""
Global Fan-Strike — 3D FPS client (Ursina / Panda3D).
Fan homage to bomb-defusal shooters. Not affiliated with Valve Corporation.
"""
import argparse
import importlib.util
import json
import math
import os
import random
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
        camera,
        color,
        destroy,
        held_keys,
        mouse,
        scene,
        window,
    )
except ImportError:
    print("Install dependencies: install.bat")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SERVER_FILE = ROOT / "server" / "server.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.game_config import (  # noqa: E402
    DEFAULT_PORT,
    TEAM_CT,
    TEAM_T,
    VALVE_KILL_PHRASES,
    VALVE_LOADING_TIPS,
    WEAPONS,
)
from shared.dust2_map import (  # noqa: E402
    BOMBSITE_A,
    BOMBSITE_B,
    FLOOR_SIZE,
    SAND_COLOR,
    WALL_COLOR,
    CRATE_COLOR,
    SKY_TINT,
    wall_dicts,
    prop_dicts,
)

ACTIVE_APP = None
HOST_BOTS = 5

# Valve Orange Box palette
VALVE_ORANGE = color.rgb(244, 120, 33)
UI_BG = color.rgb(18, 20, 24)
UI_PANEL = color.rgb(28, 32, 40)
UI_FIELD = color.rgb(45, 52, 64)
UI_TEXT = color.white
UI_MUTED = color.rgb(160, 170, 185)
TEAM_T_COLOR = color.rgb(180, 140, 60)
TEAM_CT_COLOR = color.rgb(90, 140, 200)


def load_server_module():
    spec = importlib.util.spec_from_file_location("fanstrike_server", SERVER_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rgb(c):
    return color.rgb(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))


def apply_window_theme():
    """Force a dark clear color — window.color alone stays white on some drivers."""
    window.color = UI_BG
    try:
        camera.clear_color = UI_BG
    except Exception:
        pass


def ui_add(owner, entity):
    owner._ui_widgets.append(entity)
    return entity


def destroy_widgets(widgets):
    for w in list(widgets):
        try:
            destroy(w)
        except Exception:
            pass
    widgets.clear()


class NetClient:
    def __init__(self, host, port, name, team, bots=0):
        self.host = host
        self.port = int(port)
        self.name = (name or "Player")[:16]
        self.team = team if team in (TEAM_T, TEAM_CT) else TEAM_T
        self.bots = int(bots)
        self.sock = None
        self.file = None
        self.send_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.state = {}
        self.welcome = None
        self.my_pid = -1
        self.connected = False
        self.error = None

    def connect(self):
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=6)
            self.file = self.sock.makefile("rwb")
            join = {"t": "join", "name": self.name, "team": self.team, "bots": self.bots}
            self._send(join)
            line = self.file.readline()
            if not line:
                self.error = "Connection closed (Valve Time?)"
                return False
            msg = json.loads(line.decode())
            if msg.get("t") != "welcome":
                self.error = "Bad welcome packet"
                return False
            self.welcome = msg
            self.my_pid = int(msg["pid"])
            self.team = msg.get("team", self.team)
            self.connected = True
            threading.Thread(target=self._reader, daemon=True).start()
            return True
        except Exception as exc:
            self.error = str(exc)
            self.close()
            return False

    def _send(self, obj):
        if not self.sock:
            return False
        try:
            data = (json.dumps(obj, separators=(",", ":")) + "\n").encode()
            with self.send_lock:
                self.sock.sendall(data)
            return True
        except Exception as exc:
            self.error = str(exc)
            self.connected = False
            return False

    def _reader(self):
        try:
            while self.connected:
                line = self.file.readline()
                if not line:
                    self.error = "Disconnected"
                    self.connected = False
                    return
                msg = json.loads(line.decode())
                if msg.get("t") == "state":
                    with self.state_lock:
                        self.state = msg
        except Exception as exc:
            self.error = str(exc)
            self.connected = False

    def snapshot(self):
        with self.state_lock:
            return dict(self.state)

    def send_input(self, dx, dz, dt, yaw, pitch, crouch):
        self._send({"t": "input", "dx": dx, "dz": dz, "dt": dt, "yaw": yaw, "pitch": pitch, "crouch": crouch})

    def send_shoot(self, yaw, pitch):
        self._send({"t": "shoot", "yaw": yaw, "pitch": pitch})

    def send_reload(self):
        self._send({"t": "reload"})

    def send_plant(self, on):
        self._send({"t": "plant", "on": on})

    def send_defuse(self, on):
        self._send({"t": "defuse", "on": on})

    def send_buy(self, weapon):
        self._send({"t": "buy", "weapon": weapon})

    def close(self):
        self.connected = False
        for o in (self.file, self.sock):
            if o:
                try:
                    o.close()
                except Exception:
                    pass
        self.sock = None
        self.file = None


class EmbeddedServer:
    def __init__(self, port):
        self.port = port
        self.thread = None

    def start(self):
        mod = load_server_module()
        srv = mod.GameServer("127.0.0.1", self.port)

        def run():
            import asyncio
            asyncio.run(srv.run())

        self.thread = threading.Thread(target=run, daemon=True, name="embedded-fanstrike")
        self.thread.start()
        time.sleep(0.35)


def build_map(walls_data, props_data):
    entities = []
    floor = Entity(
        model="plane",
        scale=(FLOOR_SIZE, 1, FLOOR_SIZE),
        color=rgb(SAND_COLOR),
        texture="white_cube",
        collider="box",
        y=0,
    )
    entities.append(floor)
    for w in walls_data:
        kind = w.get("kind", "wall")
        col = rgb(CRATE_COLOR if kind == "crate" else WALL_COLOR)
        e = Entity(
            model="cube",
            color=col,
            position=(w["x"], w["h"] / 2, w["z"]),
            scale=(w["hw"] * 2, w["h"], w["hd"] * 2),
            collider="box",
            texture="white_cube",
        )
        entities.append(e)
    # Bombsite markers
    for site, data in (("A", BOMBSITE_A), ("B", BOMBSITE_B)):
        cx, cz, r = data
        ring_col = color.rgba(200, 60, 40, 120) if site == "A" else color.rgba(40, 90, 200, 120)
        ring = Entity(
            model="quad",
            color=ring_col,
            position=(cx, 0.06, cz),
            scale=(r * 2, r * 2, 1),
            rotation_x=90,
        )
        label = Text(
            text=f"Bombsite {site}",
            position=(cx, 2.5, cz),
            scale=8,
            billboard=True,
            color=UI_TEXT,
            origin=(0, 0),
        )
        entities.extend([ring, label])
    for p in props_data:
        pk = p.get("kind")
        if pk == "chicken":
            body = Entity(model="sphere", color=color.yellow, scale=0.5, position=(p["x"], p["y"], p["z"]))
            Text(text="CHICKEN", parent=body, y=1.2, scale=6, billboard=True, color=color.orange)
            entities.append(body)
        elif pk == "cube":
            body = Entity(
                model="cube",
                color=color.rgb(180, 180, 200),
                scale=0.6,
                position=(p["x"], p["y"], p["z"]),
            )
            Text(text="Companion", parent=body, y=1.5, scale=5, billboard=True)
            entities.append(body)
        elif pk == "lambda":
            Text(text="λ", position=(p["x"], p["y"], p["z"]), scale=20, color=color.rgb(255, 180, 0), billboard=True)
    return entities


class MenuScene3D:
    """Dust Valley preview behind the lobby (3D world, not UI)."""

    def __init__(self):
        self.entities = []
        self.sky = Sky(color=rgb(SKY_TINT))
        self.entities.append(self.sky)
        self.entities.extend(build_map(wall_dicts(), prop_dicts()))
        self.entities.append(DirectionalLight(direction=(1, -1, 0.4), shadows=False))
        self.entities.append(AmbientLight(color=color.rgba(140, 130, 115, 0.55)))
        camera.position = Vec3(8, 78, -58)
        camera.rotation_x = 38
        camera.rotation_y = -10
        camera.fov = 55
        mouse.visible = True
        mouse.locked = False

    def destroy(self):
        for ent in self.entities:
            try:
                destroy(ent)
            except Exception:
                pass
        self.entities.clear()
        self.sky = None


class MatchView:
    def __init__(self, app, net: NetClient):
        self.app = app
        self.net = net
        self.map_entities = []
        self.player_models = {}
        self.yaw = 0.0
        self.pitch = 0.0
        self.mouse_sens = 55
        self.shoot_cooldown = 0.0
        self.plant_key = False
        self.defuse_key = False
        self.buy_open = False
        self.console_open = False
        self.console_field = None
        self.kill_feed = []
        self._ui_widgets = []
        self.last_hp = {}
        self.tip_index = random.randint(0, len(VALVE_LOADING_TIPS) - 1)
        self._build_world()
        self._build_hud()
        mouse.locked = True
        mouse.visible = False

    def _build_world(self):
        w = self.net.welcome or {}
        Sky(color=rgb(SKY_TINT))
        DirectionalLight(direction=(1, -1, 0.5), shadows=False)
        AmbientLight(color=color.rgba(120, 110, 100, 0.4))
        self.map_entities = build_map(w.get("map", []), w.get("props", []))

    def _build_hud(self):
        ui = camera.ui
        add = lambda e: ui_add(self, e)

        self.crosshair = add(Text(parent=ui, text="+", origin=(0, 0), scale=2, color=VALVE_ORANGE, z=-2))
        self.top_bar = add(
            Text(
                parent=ui,
                text="",
                origin=(-0.5, 0.5),
                position=(-0.86, 0.46),
                scale=1.2,
                color=UI_TEXT,
                z=-2,
            )
        )
        self.bottom_bar = add(
            Text(
                parent=ui,
                text="",
                origin=(-0.5, -0.5),
                position=(-0.86, -0.46),
                scale=1,
                color=UI_MUTED,
                z=-2,
            )
        )
        self.center_msg = add(Text(parent=ui, text="", origin=(0, 0), y=0.15, scale=1.5, color=VALVE_ORANGE, z=-2))
        self.buy_panel = add(Text(parent=ui, text="", enabled=False, origin=(0, 0), scale=1.1, color=UI_TEXT, z=-2))
        self.kill_feed_text = add(
            Text(
                parent=ui,
                text="",
                origin=(0.5, 0.5),
                position=(0.86, 0.35),
                scale=0.85,
                color=UI_MUTED,
                z=-2,
            )
        )
        self.tip_text = add(
            Text(
                parent=ui,
                text=VALVE_LOADING_TIPS[self.tip_index],
                origin=(0, -0.5),
                y=-0.42,
                scale=0.9,
                color=UI_MUTED,
                z=-2,
            )
        )

    def destroy(self):
        destroy_widgets(self._ui_widgets)
        for ent in self.map_entities:
            try:
                destroy(ent)
            except Exception:
                pass
        self.map_entities.clear()
        for m in self.player_models.values():
            try:
                destroy(m)
            except Exception:
                pass
        self.player_models.clear()

    def _me(self, state):
        for p in state.get("players", []):
            if p["pid"] == self.net.my_pid:
                return p
        return None

    def update(self):
        if not self.net.connected:
            self.center_msg.text = self.net.error or "Disconnected"
            return
        state = self.net.snapshot()
        me = self._me(state)
        if not me:
            return

        dt = time.dt
        phase = state.get("phase", "live")
        if phase == "live" and not self.buy_open:
            self._fps_input(dt, me, state)
        elif phase == "freeze":
            mouse.locked = False
        else:
            mouse.locked = True

        self._sync_camera(me, state)
        self._sync_players(state)
        self._hud(state, me)
        self._kill_feed_logic(state)

    def _fps_input(self, dt, me, state):
        mouse.locked = True
        self.yaw += mouse.velocity[0] * self.mouse_sens * dt
        self.pitch -= mouse.velocity[1] * self.mouse_sens * dt
        self.pitch = max(-1.2, min(1.2, self.pitch))
        dx = (held_keys["d"] - held_keys["a"]) + (held_keys["right arrow"] - held_keys["left arrow"])
        dz = (held_keys["w"] - held_keys["s"]) + (held_keys["up arrow"] - held_keys["down arrow"])
        crouch = held_keys["control"] or held_keys["c"]
        self.net.send_input(dx, dz, dt, self.yaw, self.pitch, crouch)
        if held_keys["left mouse"] or held_keys["space"]:
            if time.time() > self.shoot_cooldown:
                self.net.send_shoot(self.yaw, self.pitch)
                self.shoot_cooldown = time.time() + 0.05
        if held_keys["r"]:
            self.net.send_reload()
        site_near = self._near_site(me)
        if me.get("has_bomb") and site_near and (held_keys["e"]):
            self.net.send_plant(True)
            self.plant_key = True
        else:
            if self.plant_key:
                self.net.send_plant(False)
            self.plant_key = False
        if state.get("bomb_planted") and me["team"] == TEAM_CT and held_keys["e"]:
            self.net.send_defuse(True)
            self.defuse_key = True
        else:
            if self.defuse_key:
                self.net.send_defuse(False)
            self.defuse_key = False

    def _near_site(self, me):
        x, z = me["x"], me["z"]
        for cx, cz, r in (BOMBSITE_A, BOMBSITE_B):
            if (x - cx) ** 2 + (z - cz) ** 2 <= (r + 1) ** 2:
                return True
        return False

    def _sync_camera(self, me, state):
        eye_y = 1.65 if not me.get("crouch") else 1.1
        camera.position = Vec3(me["x"], eye_y, me["z"])
        camera.rotation_x = self.pitch * 57.3
        camera.rotation_y = self.yaw * 57.3

    def _sync_players(self, state):
        seen = set()
        for p in state.get("players", []):
            pid = p["pid"]
            seen.add(pid)
            if pid == self.net.my_pid:
                continue
            if pid not in self.player_models:
                col = TEAM_T_COLOR if p["team"] == TEAM_T else TEAM_CT_COLOR
                body = Entity(model="capsule", color=col, scale=(0.9, 1.8, 0.9), collider=None)
                self.player_models[pid] = body
            m = self.player_models[pid]
            if not p["alive"]:
                m.enabled = False
                continue
            m.enabled = True
            m.position = Vec3(p["x"], 0.9, p["z"])
            m.rotation_y = p["yaw"] * 57.3
        for pid in list(self.player_models):
            if pid not in seen:
                destroy(self.player_models[pid])
                del self.player_models[pid]

    def _hud(self, state, me):
        wpn = WEAPONS.get(me["weapon"], {})
        wname = wpn.get("name", me["weapon"])
        self.top_bar.text = (
            f"  T {state.get('score_t', 0)}  :  {state.get('score_ct', 0)} CT  |  "
            f"Round {state.get('round', 0)}  |  {state.get('phase', '').upper()}  |  "
            f"${me['money']}  |  HP {me['hp']}  ARM {me['armor']}"
        )
        ammo = f"{me['mag']} / {me['reserve']}" if wpn.get("mag") else "—"
        bomb = " [BOMB]" if me.get("has_bomb") else ""
        planted = ""
        if state.get("bomb_planted"):
            planted = f"  PLANTED {state.get('bomb_site')} ({state.get('bomb_explodes_in')}s)"
        self.bottom_bar.text = (
            f"{wname}  {ammo}{bomb}{planted}  |  "
            f"E plant/defuse  |  B buy  |  ` console  |  Tab scoreboard"
        )
        phase = state.get("phase")
        if phase == "freeze":
            self.center_msg.text = f"Freeze — {state.get('freeze_left', 0):.0f}s"
        elif state.get("round_reason") and phase == "over":
            self.center_msg.text = state["round_reason"]
        elif state.get("match_over"):
            w = "Terrorists" if state.get("match_winner") == TEAM_T else "Counter-Terrorists"
            self.center_msg.text = f"Match over — {w} win! Accept our fiscal apology."
        else:
            self.center_msg.text = ""
        if self.buy_open:
            lines = ["=== BUY MENU (Steam Wallet) ===", "Insufficient funds? Eco round.", ""]
            for i, wid in enumerate(["ak47", "m4a1", "awp", "kevlar"], 1):
                item = WEAPONS[wid]
                lines.append(f"  [{i}] {item['name']} — ${item['price']}")
            lines.append("  [Esc] close")
            self.buy_panel.text = "\n".join(lines)
            self.buy_panel.enabled = True
        else:
            self.buy_panel.enabled = False
        if self.kill_feed:
            self.kill_feed_text.text = "\n".join(self.kill_feed[-4:])
        else:
            self.kill_feed_text.text = ""

    def _kill_feed_logic(self, state):
        for p in state.get("players", []):
            pid = p["pid"]
            prev = self.last_hp.get(pid, 100)
            if prev > 0 and p["hp"] <= 0 and pid != self.net.my_pid:
                phrase = random.choice(VALVE_KILL_PHRASES)
                self.kill_feed.append(f"{p['name']} eliminated — {phrase}")
                if len(self.kill_feed) > 4:
                    self.kill_feed.pop(0)
            self.last_hp[pid] = p["hp"]

    def input_key(self, key):
        if key == "b":
            self.buy_open = not self.buy_open
            mouse.locked = not self.buy_open
        if self.buy_open:
            for i, wid in enumerate(["ak47", "m4a1", "awp", "kevlar"], 1):
                if key == str(i):
                    self.net.send_buy(wid)
                    if self._me(self.net.snapshot()) and self._me(self.net.snapshot())["money"] < WEAPONS[wid]["price"]:
                        self.center_msg.text = "Steam Wallet: insufficient funds."
            if key == "escape":
                self.buy_open = False
                mouse.locked = True
        if key == "`" or key == "grave":
            self.console_open = not self.console_open
            if self.console_open:
                self.center_msg.text = "Developer console — try: sv_cheats 1"
        if key == "escape" and not self.buy_open:
            self.app.return_to_menu()


class LobbyMenu:
    """Screen-space lobby — all widgets parented to camera.ui."""

    def __init__(self, app):
        self.app = app
        self._ui_widgets = []
        self.team = TEAM_T
        ui = camera.ui
        add = lambda e: ui_add(self, e)

        add(Entity(parent=ui, model="quad", color=color.rgba(8, 10, 14, 210), scale=(2, 1.25), z=1))
        add(Entity(parent=ui, model="quad", color=UI_PANEL, scale=(0.78, 0.88), z=0.95))

        add(Text(parent=ui, text="GLOBAL FAN-STRIKE", y=0.38, scale=2, color=VALVE_ORANGE, origin=(0, 0), z=-1))
        add(Text(parent=ui, text="de_dust_valley", y=0.30, scale=1.1, color=UI_TEXT, origin=(0, 0), z=-1))
        add(Text(parent=ui, text="(fan map — not Valve IP)", y=0.24, scale=0.75, color=UI_MUTED, origin=(0, 0), z=-1))

        def field_row(y, default, limit=24):
            add(Entity(parent=ui, model="quad", color=UI_FIELD, scale=(0.44, 0.06), position=(0, y), z=-0.98))
            f = InputField(
                parent=ui,
                default_value=default,
                position=(0, y),
                scale=(0.4, 0.05),
                character_limit=limit,
                color=UI_FIELD,
                text_color=UI_TEXT,
                z=-0.97,
            )
            add(f)
            return f

        add(Text(parent=ui, text="Name", y=0.16, scale=0.8, color=UI_MUTED, origin=(0, 0), z=-1))
        self.name_field = field_row(0.10, "Player", 16)
        add(Text(parent=ui, text="Server IP", y=0.02, scale=0.8, color=UI_MUTED, origin=(0, 0), z=-1))
        self.host_field = field_row(-0.04, "127.0.0.1")
        add(Text(parent=ui, text="Port", y=-0.10, scale=0.8, color=UI_MUTED, origin=(0, 0), z=-1))
        self.port_field = field_row(-0.16, str(DEFAULT_PORT), 6)

        add(Text(parent=ui, text="Pick team", y=-0.24, scale=0.85, color=UI_MUTED, origin=(0, 0), z=-1))
        add(
            Button(
                parent=ui,
                text="Terrorists",
                position=(-0.15, -0.30),
                scale=(0.22, 0.07),
                color=TEAM_T_COLOR,
                highlight_color=VALVE_ORANGE,
                pressed_color=color.rgb(140, 100, 40),
                text_color=UI_TEXT,
                z=-0.96,
                on_click=self.pick_t,
            )
        )
        add(
            Button(
                parent=ui,
                text="Counter-Terrorists",
                position=(0.15, -0.30),
                scale=(0.22, 0.07),
                color=TEAM_CT_COLOR,
                highlight_color=color.rgb(120, 180, 240),
                pressed_color=color.rgb(50, 90, 140),
                text_color=UI_TEXT,
                z=-0.96,
                on_click=self.pick_ct,
            )
        )
        add(
            Button(
                parent=ui,
                text="HOST LOCAL (+ BOTS)",
                position=(0, -0.40),
                scale=(0.42, 0.08),
                color=VALVE_ORANGE,
                highlight_color=color.rgb(255, 160, 80),
                pressed_color=color.rgb(200, 90, 20),
                text_color=color.black,
                z=-0.96,
                on_click=lambda: app.connect(host_local=True),
            )
        )
        add(
            Button(
                parent=ui,
                text="JOIN SERVER",
                position=(0, -0.50),
                scale=(0.42, 0.08),
                color=color.rgb(55, 95, 140),
                highlight_color=color.rgb(80, 130, 190),
                pressed_color=color.rgb(35, 60, 95),
                text_color=UI_TEXT,
                z=-0.96,
                on_click=lambda: app.connect(host_local=False),
            )
        )
        self.status = add(
            Text(
                parent=ui,
                text=random.choice(VALVE_LOADING_TIPS),
                y=-0.58,
                scale=0.7,
                color=UI_MUTED,
                origin=(0, 0),
                z=-1,
            )
        )

    def pick_t(self):
        self.team = TEAM_T
        self.status.text = "Team: Terrorists — rush B responsibly."

    def pick_ct(self):
        self.team = TEAM_CT
        self.status.text = "Team: Counter-Terrorists — hold the sites."

    def destroy(self):
        destroy_widgets(self._ui_widgets)


class FanStrikeApp:
    def __init__(self, args):
        global ACTIVE_APP
        ACTIVE_APP = self
        self.args = args
        self.app = Ursina(
            title="Global Fan-Strike: Dust Valley",
            borderless=False,
            fullscreen=False,
            development_mode=False,
            vsync=True,
        )
        apply_window_theme()
        camera.fov = 90
        try:
            window.fps_counter.enabled = False
        except Exception:
            pass

        self.mode = "menu"
        self.menu = None
        self.menu_scene = None
        self.match = None
        self.net = None
        self.embedded = None
        self.connect_thread = None
        self.connect_result = None
        self.connect_lock = threading.Lock()
        self.start_menu()

    def _clear_match(self):
        if self.match:
            self.match.destroy()
            self.match = None

    def _clear_menu(self):
        if self.menu:
            self.menu.destroy()
            self.menu = None
        if self.menu_scene:
            self.menu_scene.destroy()
            self.menu_scene = None

    def start_menu(self):
        self.mode = "menu"
        self._clear_match()
        self._clear_menu()
        apply_window_theme()
        self.menu_scene = MenuScene3D()
        self.menu = LobbyMenu(self)

    def connect(self, host_local=False):
        name = (self.menu.name_field.text or "Player").strip()[:16]
        host = (self.menu.host_field.text or "127.0.0.1").strip()
        try:
            port = int(self.menu.port_field.text.strip())
        except ValueError:
            self.menu.status.text = "Invalid port."
            return
        team = self.menu.team
        bots = HOST_BOTS if host_local else 0
        self.mode = "connecting"
        self.menu.status.text = "Connecting via Steam-ish protocol..."
        threading.Thread(
            target=self._connect_worker,
            args=(host, port, name, team, bots, host_local),
            daemon=True,
        ).start()

    def _connect_worker(self, host, port, name, team, bots, host_local):
        err = None
        net = None
        try:
            if host_local:
                emb = EmbeddedServer(port)
                emb.start()
            net = NetClient(host if not host_local else "127.0.0.1", port, name, team, bots=bots)
            if not net.connect():
                err = net.error or "Connect failed"
                net = None
        except Exception as exc:
            err = str(exc)
            net = None
        with self.connect_lock:
            self.connect_result = (net, err)

    def poll_connect(self):
        with self.connect_lock:
            res = self.connect_result
            self.connect_result = None
        if res is None:
            return
        net, err = res
        if err or not net:
            self.mode = "menu"
            self.menu.status.text = err or "Failed"
            return
        self._clear_menu()
        self.net = net
        apply_window_theme()
        camera.fov = 90
        self.match = MatchView(self, net)
        self.mode = "play"

    def return_to_menu(self):
        if self.net:
            self.net.close()
        self.net = None
        mouse.locked = False
        self.start_menu()

    def update(self):
        if self.mode == "connecting":
            self.poll_connect()
        elif self.mode == "play" and self.match:
            self.match.update()

    def input_key(self, key):
        if self.mode == "play" and self.match:
            self.match.input_key(key)

    def run(self):
        print("[fan-strike] Press Esc in-match to leave. Port default:", DEFAULT_PORT)
        self.app.run()


def update():
    if ACTIVE_APP:
        ACTIVE_APP.update()


def input(key):
    if ACTIVE_APP:
        ACTIVE_APP.input_key(key)


def main():
    os.chdir(ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-menu", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--name", default="Player")
    parser.add_argument("--team", choices=[TEAM_T, TEAM_CT], default=TEAM_T)
    parser.add_argument("--host-local", action="store_true")
    args = parser.parse_args()
    FanStrikeApp(args).run()


if __name__ == "__main__":
    main()
