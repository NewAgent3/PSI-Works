"""
Brawl Clone - Authoritative Multiplayer Server
================================================
Pure Python stdlib WebSocket-like server using asyncio + simple JSON-line protocol
over TCP. Handles up to N players, projectiles, damage, respawn, scoreboard.

Run:  python server.py [--host 0.0.0.0] [--port 5555]
"""
import asyncio
import json
import math
import random
import time
import argparse
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple

TICK_RATE = 30          # server ticks per second
ARENA_RADIUS = 28.0     # circular arena
RESPAWN_TIME = 4.0
PROJECTILE_LIFETIME = 1.5
WALL_COUNT = 14         # cover boxes
BUSH_COUNT = 10         # stealth bushes
PLAYER_RADIUS = 0.6
MAX_NAME_LEN = 16
REVEAL_AFTER_SHOOT = 0.75
MAX_PLAYERS = 8
MATCH_DURATION = 180.0  # seconds; 0 = no time limit
BOT_NAMES = ("Rex", "Nova", "Blitz", "Viper", "Tank", "Zap", "Ghost", "Ace")
BOT_REACTION_MIN = 0.12
BOT_REACTION_MAX = 0.38


# ---------- Character archetypes (Brawl-Stars style stats) ----------
BRAWLERS = {
    "spike":  {"hp": 700,  "speed": 6.2, "dmg": 70,  "fire_rate": 0.55, "range": 18, "proj_speed": 22, "spread": 0.0,  "shots": 1, "color": [0, 1, 0]},
    "edgar":  {"hp": 1100, "speed": 8.0, "dmg": 110, "fire_rate": 0.40, "range": 6,  "proj_speed": 30, "spread": 0.0,  "shots": 1, "color": [1, 0, 0.4]},
    "buzz":   {"hp": 1000, "speed": 6.6, "dmg": 90,  "fire_rate": 0.50, "range": 7,  "proj_speed": 28, "spread": 0.0,  "shots": 1, "color": [1, 0.8, 0]},
    "damian": {"hp": 900,  "speed": 6.0, "dmg": 80,  "fire_rate": 0.60, "range": 14, "proj_speed": 22, "spread": 0.0,  "shots": 1, "color": [0.6, 0, 1]},
    "lumi":   {"hp": 650,  "speed": 6.4, "dmg": 95,  "fire_rate": 0.70, "range": 22, "proj_speed": 26, "spread": 0.0,  "shots": 1, "color": [1, 0.9, 0.4]},
    "sirius": {"hp": 750,  "speed": 6.2, "dmg": 85,  "fire_rate": 0.65, "range": 20, "proj_speed": 24, "spread": 0.0,  "shots": 1, "color": [0.2, 0.4, 1]},
    "alli":   {"hp": 800,  "speed": 6.3, "dmg": 75,  "fire_rate": 0.55, "range": 16, "proj_speed": 22, "spread": 0.0,  "shots": 1, "color": [0, 0.8, 1]},
    "kaze":   {"hp": 700,  "speed": 6.8, "dmg": 60,  "fire_rate": 0.35, "range": 12, "proj_speed": 26, "spread": 0.0,  "shots": 1, "color": [1, 0.3, 0.6]},
    "kit":    {"hp": 850,  "speed": 6.5, "dmg": 70,  "fire_rate": 0.50, "range": 13, "proj_speed": 24, "spread": 0.15, "shots": 3, "color": [1, 0.6, 0.3]},
}


@dataclass
class Player:
    pid: int
    name: str
    brawler: str
    x: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    hp: float = 1000
    max_hp: float = 1000
    speed: float = 6.0
    alive: bool = True
    respawn_at: float = 0.0
    kills: int = 0
    deaths: int = 0
    last_shot: float = 0.0
    writer: object = None
    in_bush: bool = False
    moving: bool = False
    revealed_until: float = 0.0
    is_bot: bool = False
    bot_target_pid: int = -1
    bot_wander_x: float = 0.0
    bot_wander_z: float = 0.0
    bot_next_think: float = 0.0
    bot_strafe: float = 1.0


@dataclass
class Projectile:
    oid: int
    owner: int
    x: float
    z: float
    vx: float
    vz: float
    dmg: float
    born: float
    lifetime: float
    color: list


@dataclass
class Wall:
    x: float
    z: float
    w: float = 2.0
    h: float = 2.0


@dataclass
class Bush:
    x: float
    z: float
    r: float = 2.0


class GameServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.players: Dict[int, Player] = {}
        self.projectiles: List[Projectile] = []
        self.walls: List[Wall] = []
        self.bushes: List[Bush] = []
        self.next_pid = 1
        self.next_oid = 1
        self.start_time = time.time()
        self.match_ends_at = 0.0
        self.match_started = False
        self.winner_pid = -1
        self.pending_bots = 0
        self._gen_map()

    def _gen_map(self):
        rng = random.Random(42)
        # Symmetrical-ish wall layout
        positions = []
        for _ in range(WALL_COUNT):
            for _ in range(40):
                x = rng.uniform(-ARENA_RADIUS + 4, ARENA_RADIUS - 4)
                z = rng.uniform(-ARENA_RADIUS + 4, ARENA_RADIUS - 4)
                if math.hypot(x, z) < 5:  # leave center open
                    continue
                if all(math.hypot(x - px, z - pz) > 4 for px, pz in positions):
                    positions.append((x, z))
                    self.walls.append(Wall(x, z))
                    break
        for _ in range(BUSH_COUNT):
            for _ in range(40):
                x = rng.uniform(-ARENA_RADIUS + 3, ARENA_RADIUS - 3)
                z = rng.uniform(-ARENA_RADIUS + 3, ARENA_RADIUS - 3)
                if all(math.hypot(x - w.x, z - w.z) > 3 for w in self.walls) and \
                   all(math.hypot(x - b.x, z - b.z) > 4 for b in self.bushes):
                    self.bushes.append(Bush(x, z))
                    break

    def spawn_point(self) -> Tuple[float, float]:
        for _ in range(80):
            angle = random.uniform(0, math.tau)
            r = random.uniform(ARENA_RADIUS * 0.35, ARENA_RADIUS - 3)
            x = math.cos(angle) * r
            z = math.sin(angle) * r
            if not self._in_wall(x, z, PLAYER_RADIUS):
                return x, z
        return 0.0, 0.0

    def _in_wall(self, x: float, z: float, radius=PLAYER_RADIUS) -> bool:
        for w in self.walls:
            if abs(x - w.x) < w.w / 2 + radius and abs(z - w.z) < w.h / 2 + radius:
                return True
        return False

    def _in_arena(self, x: float, z: float, radius=PLAYER_RADIUS) -> bool:
        return math.hypot(x, z) <= ARENA_RADIUS - radius

    def _inside_bush(self, p: Player) -> bool:
        return any(math.hypot(p.x - b.x, p.z - b.z) < b.r for b in self.bushes)

    def _is_stealthed(self, p: Player, now: float) -> bool:
        return p.alive and self._inside_bush(p) and now >= p.revealed_until

    def _visible_to(self, viewer: Player, target: Player, now: float) -> bool:
        if viewer.pid == target.pid:
            return True
        if not target.alive:
            return True
        return not self._is_stealthed(target, now)

    def _human_count(self) -> int:
        return sum(1 for p in self.players.values() if not p.is_bot)

    def _ensure_match_clock(self):
        if self.match_started or self._human_count() == 0:
            return
        self.match_started = True
        if MATCH_DURATION > 0:
            self.match_ends_at = time.time() + MATCH_DURATION

    def _pick_winner(self) -> int:
        alive = [p for p in self.players.values() if p.alive]
        if alive:
            best = max(alive, key=lambda p: (p.kills, -p.deaths, p.hp))
            return best.pid
        ranked = sorted(
            self.players.values(),
            key=lambda p: (-p.kills, p.deaths, -p.hp),
        )
        return ranked[0].pid if ranked else -1

    def spawn_bot(self, brawler: str = None) -> Player | None:
        if len(self.players) >= MAX_PLAYERS:
            return None
        pid = self.next_pid
        self.next_pid += 1
        if brawler not in BRAWLERS:
            brawler = random.choice(list(BRAWLERS.keys()))
        stats = BRAWLERS[brawler]
        sx, sz = self.spawn_point()
        used = {p.name for p in self.players.values()}
        name = next((n for n in BOT_NAMES if n not in used), f"Bot{pid}")
        p = Player(
            pid=pid,
            name=name,
            brawler=brawler,
            x=sx,
            z=sz,
            hp=stats["hp"],
            max_hp=stats["hp"],
            speed=stats["speed"],
            writer=None,
            is_bot=True,
        )
        p.bot_wander_x, p.bot_wander_z = sx, sz
        p.bot_next_think = time.time() + random.uniform(0.2, 0.8)
        self.players[pid] = p
        return p

    def spawn_bots(self, count: int):
        count = max(0, min(int(count), MAX_PLAYERS - len(self.players)))
        brawlers = list(BRAWLERS.keys())
        random.shuffle(brawlers)
        for i in range(count):
            pick = brawlers[i % len(brawlers)]
            self.spawn_bot(pick)

    def _move_player(self, p: Player, dx: float, dz: float, dt: float, now: float):
        ln = math.hypot(dx, dz)
        if ln > 1e-4:
            dx /= ln
            dz /= ln
            p.moving = True
        else:
            dx = 0.0
            dz = 0.0
            p.moving = False
        step = p.speed * dt
        nx = p.x + dx * step
        nz = p.z + dz * step
        if self._in_arena(nx, p.z) and not self._in_wall(nx, p.z):
            p.x = nx
        if self._in_arena(p.x, nz) and not self._in_wall(p.x, nz):
            p.z = nz
        if not self._in_arena(p.x, p.z):
            dist = max(0.001, math.hypot(p.x, p.z))
            limit = ARENA_RADIUS - PLAYER_RADIUS
            p.x = p.x / dist * limit
            p.z = p.z / dist * limit
        p.in_bush = self._inside_bush(p) and now >= p.revealed_until

    def _shoot_player(self, p: Player, yaw: float, now: float) -> bool:
        if not p.alive:
            return False
        stats = BRAWLERS[p.brawler]
        if now - p.last_shot < stats["fire_rate"]:
            return False
        p.last_shot = now
        p.yaw = yaw
        p.revealed_until = now + REVEAL_AFTER_SHOOT
        p.in_bush = False
        shots = stats["shots"]
        spread = stats["spread"]
        for i in range(shots):
            if shots == 1:
                a = yaw
            else:
                a = yaw + (i - (shots - 1) / 2) * spread
            vx = math.sin(a) * stats["proj_speed"]
            vz = math.cos(a) * stats["proj_speed"]
            self.projectiles.append(
                Projectile(
                    oid=self.next_oid,
                    owner=p.pid,
                    x=p.x + math.sin(a) * 0.9,
                    z=p.z + math.cos(a) * 0.9,
                    vx=vx,
                    vz=vz,
                    dmg=stats["dmg"],
                    born=now,
                    lifetime=min(PROJECTILE_LIFETIME, stats["range"] / stats["proj_speed"]),
                    color=stats["color"],
                )
            )
            self.next_oid += 1
        return True

    def _bot_enemies(self, bot: Player):
        for other in self.players.values():
            if other.pid == bot.pid or not other.alive:
                continue
            yield other

    def _bot_pick_target(self, bot: Player, now: float):
        best = None
        best_score = 1e9
        stats = BRAWLERS[bot.brawler]
        for enemy in self._bot_enemies(bot):
            if self._is_stealthed(enemy, now):
                continue
            dist = math.hypot(enemy.x - bot.x, enemy.z - bot.z)
            if dist > stats["range"] * 1.15:
                continue
            if self._line_blocked(bot.x, bot.z, enemy.x, enemy.z):
                continue
            score = dist + (0 if enemy.pid == bot.bot_target_pid else 2.5)
            if score < best_score:
                best_score = score
                best = enemy
        return best

    def _line_blocked(self, x0, z0, x1, z1) -> bool:
        steps = 8
        for i in range(1, steps):
            t = i / steps
            x = x0 + (x1 - x0) * t
            z = z0 + (z1 - z0) * t
            if self._in_wall(x, z, radius=0.25):
                return True
        return False

    def _bot_think(self, bot: Player, dt: float, now: float):
        if now < bot.bot_next_think:
            return
        bot.bot_next_think = now + random.uniform(BOT_REACTION_MIN, BOT_REACTION_MAX)
        if self.winner_pid >= 0:
            return

        target = self._bot_pick_target(bot, now)
        if target:
            bot.bot_target_pid = target.pid
            dx = target.x - bot.x
            dz = target.z - bot.z
            dist = max(0.001, math.hypot(dx, dz))
            stats = BRAWLERS[bot.brawler]
            aim = math.atan2(dx, dz)
            bot.yaw = aim
            if dist > stats["range"] * 0.55:
                self._move_player(bot, dx / dist, dz / dist, dt, now)
            else:
                strafe_x = -dz / dist * bot.bot_strafe
                strafe_z = dx / dist * bot.bot_strafe
                self._move_player(bot, strafe_x, strafe_z, dt, now)
                if random.random() < 0.08:
                    bot.bot_strafe *= -1
            if dist <= stats["range"] and not self._line_blocked(bot.x, bot.z, target.x, target.z):
                self._shoot_player(bot, aim, now)
            return

        bot.bot_target_pid = -1
        if math.hypot(bot.x - bot.bot_wander_x, bot.z - bot.bot_wander_z) < 2.0:
            bot.bot_wander_x = random.uniform(-ARENA_RADIUS + 5, ARENA_RADIUS - 5)
            bot.bot_wander_z = random.uniform(-ARENA_RADIUS + 5, ARENA_RADIUS - 5)
        wx = bot.bot_wander_x - bot.x
        wz = bot.bot_wander_z - bot.z
        wl = max(0.001, math.hypot(wx, wz))
        self._move_player(bot, wx / wl, wz / wl, dt, now)

    def _safe_float(self, value, default=0.0, lo=None, hi=None) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return default
        if not math.isfinite(result):
            return default
        if lo is not None:
            result = max(lo, result)
        if hi is not None:
            result = min(hi, result)
        return result

    def _clean_name(self, value, fallback: str) -> str:
        name = str(value or "").strip()
        if not name:
            name = fallback
        return name[:MAX_NAME_LEN]

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if len(self.players) >= MAX_PLAYERS:
            try:
                writer.write(b'{"t":"error","msg":"Server full"}\n')
                await writer.drain()
            except Exception:
                pass
            writer.close()
            return

        pid = self.next_pid
        self.next_pid += 1
        addr = writer.get_extra_info("peername")
        print(f"[+] Connection from {addr} -> pid={pid}")

        # First message must be JOIN
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=10)
            if not line:
                writer.close()
                return
            msg = json.loads(line.decode().strip())
            if not isinstance(msg, dict):
                writer.close()
                return
            if msg.get("t") != "join":
                writer.close()
                return
            name = self._clean_name(msg.get("name"), f"Player{pid}")
            brawler = msg.get("brawler", "spike")
            if brawler not in BRAWLERS:
                brawler = "spike"
            bot_count = max(0, min(int(msg.get("bots", 0)), MAX_PLAYERS - 1))
        except Exception as e:
            print(f"[!] Join failed: {e}")
            writer.close()
            return

        stats = BRAWLERS[brawler]
        sx, sz = self.spawn_point()
        p = Player(
            pid=pid, name=name, brawler=brawler,
            x=sx, z=sz, yaw=0.0,
            hp=stats["hp"], max_hp=stats["hp"], speed=stats["speed"],
            writer=writer,
        )
        self.players[pid] = p
        self._ensure_match_clock()
        if self._human_count() == 1:
            spawn_count = max(bot_count, self.pending_bots)
            if spawn_count:
                self.spawn_bots(spawn_count)
                print(f"[server] spawned {spawn_count} bot(s)")
            self.pending_bots = 0

        # Send welcome with map + own pid
        await self._send(writer, {
            "t": "welcome",
            "pid": pid,
            "walls": [asdict(w) for w in self.walls],
            "bushes": [asdict(b) for b in self.bushes],
            "arena": ARENA_RADIUS,
            "brawlers": BRAWLERS,
            "match_duration": MATCH_DURATION,
        })

        try:
            async for raw in reader:
                if not raw:
                    break
                try:
                    msg = json.loads(raw.decode().strip())
                except Exception:
                    continue
                await self.handle_msg(p, msg)
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            print(f"[-] pid={pid} ({p.name}) disconnected")
            self.players.pop(pid, None)
            try:
                writer.close()
            except Exception:
                pass

    async def _send(self, writer, obj):
        try:
            writer.write((json.dumps(obj) + "\n").encode())
            await writer.drain()
        except Exception:
            pass

    async def handle_msg(self, p: Player, msg: dict):
        if p.is_bot or self.winner_pid >= 0:
            return
        t = msg.get("t")
        now = time.time()
        if t == "input":
            if not p.alive:
                return
            dx = self._safe_float(msg.get("dx", 0))
            dz = self._safe_float(msg.get("dz", 0))
            dt = self._safe_float(msg.get("dt", 1 / TICK_RATE), 1 / TICK_RATE, 0.001, 0.1)
            self._move_player(p, dx, dz, dt, now)
            p.yaw = self._safe_float(msg.get("yaw", p.yaw), p.yaw, -math.tau * 2, math.tau * 2)

        elif t == "shoot":
            if not p.alive:
                return
            yaw = self._safe_float(msg.get("yaw", p.yaw), p.yaw, -math.tau * 2, math.tau * 2)
            self._shoot_player(p, yaw, now)

    def _build_state_for(self, viewer: Player, now: float) -> dict:
        players = []
        for pl in self.players.values():
            hidden = not self._visible_to(viewer, pl, now)
            entry = {
                "pid": pl.pid,
                "name": pl.name,
                "brawler": pl.brawler,
                "x": round(pl.x, 3),
                "z": round(pl.z, 3),
                "yaw": round(pl.yaw, 3),
                "hp": round(pl.hp, 1),
                "max_hp": pl.max_hp,
                "alive": pl.alive,
                "kills": pl.kills,
                "deaths": pl.deaths,
                "in_bush": pl.in_bush,
                "hidden": hidden,
                "is_bot": pl.is_bot,
                "moving": pl.moving,
                "respawn_in": max(0.0, round(pl.respawn_at - now, 2)) if not pl.alive else 0,
            }
            players.append(entry)

        time_left = 0.0
        if self.match_ends_at > 0:
            time_left = max(0.0, self.match_ends_at - now)

        return {
            "t": "state",
            "ts": now,
            "players": players,
            "projectiles": [
                {"oid": pr.oid, "x": round(pr.x, 2), "z": round(pr.z, 2), "color": pr.color}
                for pr in self.projectiles
            ],
            "time_left": round(time_left, 1),
            "winner_pid": self.winner_pid,
        }

    async def tick(self):
        dt = 1.0 / TICK_RATE
        now = time.time()

        if self.match_started and self.winner_pid < 0 and self.match_ends_at > 0 and now >= self.match_ends_at:
            self.winner_pid = self._pick_winner()

        for p in self.players.values():
            if p.alive:
                p.in_bush = self._inside_bush(p) and now >= p.revealed_until

        for p in self.players.values():
            if p.is_bot and p.alive and self.winner_pid < 0:
                self._bot_think(p, dt, now)

        # Projectiles
        alive_projs = []
        for pr in self.projectiles:
            if now - pr.born > pr.lifetime:
                continue
            pr.x += pr.vx * dt
            pr.z += pr.vz * dt
            # wall collision
            if self._in_wall(pr.x, pr.z, radius=0.1):
                continue
            if math.hypot(pr.x, pr.z) > ARENA_RADIUS:
                continue
            # player hits
            hit = False
            for tgt in self.players.values():
                if tgt.pid == pr.owner or not tgt.alive:
                    continue
                if math.hypot(tgt.x - pr.x, tgt.z - pr.z) < 0.8:
                    tgt.hp -= pr.dmg
                    hit = True
                    if tgt.hp <= 0:
                        tgt.alive = False
                        tgt.deaths += 1
                        tgt.respawn_at = now + RESPAWN_TIME
                        if pr.owner in self.players:
                            self.players[pr.owner].kills += 1
                    break
            if not hit:
                alive_projs.append(pr)
        self.projectiles = alive_projs

        # Respawn
        for p in self.players.values():
            if not p.alive and now >= p.respawn_at:
                p.alive = True
                stats = BRAWLERS[p.brawler]
                p.hp = stats["hp"]
                p.x, p.z = self.spawn_point()
                p.in_bush = False
                p.revealed_until = now + 0.5

        # Broadcast personalized state
        dead = []
        for pid, pl in self.players.items():
            if pl.is_bot or pl.writer is None:
                continue
            try:
                payload = self._build_state_for(pl, now)
                pl.writer.write((json.dumps(payload) + "\n").encode())
                await pl.writer.drain()
            except Exception:
                dead.append(pid)
        for pid in dead:
            removed = self.players.pop(pid, None)
            if removed:
                print(f"[-] pid={pid} ({removed.name}) disconnected")

    async def run(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        sockets = server.sockets or []
        for s in sockets:
            print(f"[server] listening on {s.getsockname()}")
        print(f"[server] tick rate = {TICK_RATE} Hz, arena radius = {ARENA_RADIUS}")
        async def ticker():
            interval = 1.0 / TICK_RATE
            next_t = time.time()
            while True:
                await self.tick()
                next_t += interval
                sleep = next_t - time.time()
                if sleep > 0:
                    await asyncio.sleep(sleep)
                else:
                    next_t = time.time()
        async with server:
            await asyncio.gather(server.serve_forever(), ticker())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--bots", type=int, default=0, help="Spawn AI bots when the first player joins.")
    args = ap.parse_args()
    srv = GameServer(args.host, args.port)
    srv.pending_bots = max(0, min(args.bots, MAX_PLAYERS - 1))
    try:
        asyncio.run(srv.run())
    except KeyboardInterrupt:
        print("\n[server] shutting down")


if __name__ == "__main__":
    main()
