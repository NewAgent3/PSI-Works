"""
Global Fan-Strike — authoritative bomb-defusal server (Dust Valley).
"""
import argparse
import asyncio
import json
import math
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.dust2_map import (  # noqa: E402
    BOMBSITE_A,
    BOMBSITE_B,
    build_walls,
    in_bombsite,
    nearest_site,
    prop_dicts,
    wall_dicts,
)
from shared.game_config import (  # noqa: E402
    BUY_MENU_ORDER,
    DEFAULT_PORT,
    DEFUSE_REWARD,
    FREEZE_TIME,
    KILL_REWARD,
    LOSS_BONUS,
    LOSS_STREAK_BONUS,
    MAX_MONEY,
    MAX_PLAYERS,
    PLANT_REWARD,
    PLAYER_RADIUS,
    ROUNDS_TO_WIN,
    ROUND_TIME,
    START_MONEY,
    TEAM_CT,
    TEAM_T,
    TICK_RATE,
    WALK_SPEED,
    CROUCH_SPEED,
    WEAPONS,
    WIN_BONUS,
)

BOT_NAMES = ("Smurf", "Headshot", "EcoWarrior", "RushB", "Lambda", "Gaben", "Chicken", "Cube")


@dataclass
class Wall:
    x: float
    z: float
    hw: float
    hd: float
    h: float = 4.0
    kind: str = "wall"


@dataclass
class Player:
    pid: int
    name: str
    team: str
    x: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0
    hp: int = 100
    armor: int = 0
    alive: bool = True
    money: int = START_MONEY
    weapon: str = "glock"
    mag: int = 20
    reserve: int = 120
    kills: int = 0
    deaths: int = 0
    last_shot: float = 0.0
    has_bomb: bool = False
    planting: bool = False
    defusing: bool = False
    plant_progress: float = 0.0
    defuse_progress: float = 0.0
    writer: object = None
    is_bot: bool = False
    loss_streak: int = 0
    bot_goal: str = "mid"
    bot_next_think: float = 0.0
    crouching: bool = False


class GameServer:
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.walls: List[Wall] = [
            Wall(w.x, w.z, w.hw, w.hd, w.h, w.kind) for w in build_walls()
        ]
        self.players: Dict[int, Player] = {}
        self.next_pid = 1
        self.pending_bots = 0
        self.round = 0
        self.score_t = 0
        self.score_ct = 0
        self.phase = "warmup"  # warmup | freeze | live | over
        self.phase_ends = 0.0
        self.round_ends = 0.0
        self.bomb_planted = False
        self.bomb_site: Optional[str] = None
        self.bomb_x = 0.0
        self.bomb_z = 0.0
        self.bomb_explodes_at = 0.0
        self.bomb_carrier_pid = -1
        self.round_win_reason = ""
        self.match_over = False
        self.match_winner = ""
        self.start_time = time.time()
        self._assign_bomb_next_round = True

    def _spawn_for_team(self, team: str) -> Tuple[float, float]:
        from shared.dust2_map import CT_SPAWNS, T_SPAWNS

        points = T_SPAWNS if team == TEAM_T else CT_SPAWNS
        random.shuffle(points)
        for x, z in points:
            if not self._blocked(x, z):
                return x, z
        return points[0]

    def _blocked(self, x: float, z: float, r=PLAYER_RADIUS) -> bool:
        for w in self.walls:
            if abs(x - w.x) < w.hw + r and abs(z - w.z) < w.hd + r:
                return True
        return False

    def _move(self, p: Player, dx: float, dz: float, dt: float):
        if not p.alive or self.phase not in ("live", "warmup"):
            return
        ln = math.hypot(dx, dz)
        if ln < 1e-4:
            return
        dx /= ln
        dz /= ln
        speed = CROUCH_SPEED if p.crouching else WALK_SPEED
        step = speed * dt
        nx = p.x + dx * step
        nz = p.z + dz * step
        if not self._blocked(nx, p.z):
            p.x = nx
        if not self._blocked(p.x, nz):
            p.z = nz

    def _ray_hit_player(self, origin, direction, max_dist, shooter: Player) -> Optional[Player]:
        ox, oz = origin
        dx, dz = direction
        best = None
        best_t = max_dist + 1
        for tgt in self.players.values():
            if tgt.pid == shooter.pid or not tgt.alive or tgt.team == shooter.team:
                continue
            # circle intersection in xz
            fx, fz = tgt.x - ox, tgt.z - oz
            a = dx * dx + dz * dz
            if a < 1e-8:
                continue
            b = 2 * (fx * dx + fz * dz)
            c = fx * fx + fz * fz - (PLAYER_RADIUS + 0.15) ** 2
            disc = b * b - 4 * a * c
            if disc < 0:
                continue
            t = (-b - math.sqrt(disc)) / (2 * a)
            if 0.05 < t < best_t and t <= max_dist:
                hit_x = ox + dx * t
                hit_z = oz + dz * t
                if not self._ray_hits_wall(ox, oz, hit_x, hit_z):
                    best_t = t
                    best = tgt
        return best

    def _ray_hits_wall(self, x0, z0, x1, z1) -> bool:
        steps = int(max(8, math.hypot(x1 - x0, z1 - z0) * 4))
        for i in range(1, steps + 1):
            t = i / steps
            x = x0 + (x1 - x0) * t
            z = z0 + (z1 - z0) * t
            if self._blocked(x, z, r=0.1):
                return True
        return False

    def _shoot(self, p: Player, now: float) -> Optional[str]:
        if not p.alive or self.phase not in ("live", "warmup"):
            return None
        wid = p.weapon
        if wid not in WEAPONS:
            return None
        stats = WEAPONS[wid]
        if now - p.last_shot < stats["fire_rate"]:
            return None
        p.last_shot = now
        if wid == "knife":
            for tgt in self.players.values():
                if tgt.pid == p.pid or not tgt.alive or tgt.team == p.team:
                    continue
                if math.hypot(tgt.x - p.x, tgt.z - p.z) < stats["range"]:
                    self._damage(p, tgt, stats["dmg"], now)
                    return "knife"
            return None
        if p.mag <= 0:
            return None
        p.mag -= 1
        spread = stats["spread"] * (1.6 if p.crouching else 1.0)
        yaw = p.yaw + random.uniform(-spread, spread)
        pitch = p.pitch + random.uniform(-spread, spread)
        dx = math.sin(yaw) * math.cos(pitch)
        dz = math.cos(yaw) * math.cos(pitch)
        ln = math.hypot(dx, dz)
        if ln < 1e-6:
            return None
        dx /= ln
        dz /= ln
        tgt = self._ray_hit_player((p.x, p.z), (dx, dz), stats["range"], p)
        if tgt:
            dmg = stats["dmg"]
            if tgt.armor > 0 and wid != "awp":
                dmg = int(dmg * 0.72)
                tgt.armor = max(0, tgt.armor - 12)
            elif wid == "awp" and tgt.armor > 0:
                tgt.armor = 0
            self._damage(p, tgt, dmg, now)
            if stats["dmg"] >= 90:
                return "awp_pick"
        return None

    def _damage(self, src: Player, tgt: Player, dmg: int, now: float):
        tgt.hp -= dmg
        if tgt.hp <= 0:
            tgt.alive = False
            tgt.deaths += 1
            src.kills += 1
            src.money = min(MAX_MONEY, src.money + KILL_REWARD)
            if tgt.has_bomb:
                tgt.has_bomb = False
                self._drop_bomb_near(tgt.x, tgt.z)

    def _drop_bomb_near(self, x: float, z: float):
        for p in self.players.values():
            if p.alive and p.team == TEAM_T and not p.has_bomb:
                p.has_bomb = True
                self.bomb_carrier_pid = p.pid
                return
        self.bomb_carrier_pid = -1

    def _pick_team(self) -> str:
        tc = sum(1 for p in self.players.values() if p.team == TEAM_T and not p.is_bot)
        cc = sum(1 for p in self.players.values() if p.team == TEAM_CT and not p.is_bot)
        return TEAM_CT if tc > cc else TEAM_T

    def _reset_player_loadout(self, p: Player, knife_round: bool = False):
        p.hp = 100
        p.armor = 0
        p.alive = True
        p.planting = False
        p.defusing = False
        p.plant_progress = 0.0
        p.defuse_progress = 0.0
        if knife_round:
            p.weapon = "knife"
            p.mag = 1
            p.reserve = 0
            return
        if p.team == TEAM_T:
            p.weapon = "glock"
            stats = WEAPONS["glock"]
        else:
            p.weapon = "usp"
            stats = WEAPONS["usp"]
        p.mag = stats["mag"]
        p.reserve = stats["reserve"]

    def _start_round(self):
        self.round += 1
        self.bomb_planted = False
        self.bomb_site = None
        self.round_win_reason = ""
        knife = self.round == 1
        for p in self.players.values():
            self._reset_player_loadout(p, knife_round=knife)
            sx, sz = self._spawn_for_team(p.team)
            p.x, p.z = sx, sz
            p.has_bomb = False
        if carriers:
            bomber = random.choice([p for p in self.players.values() if p.team == TEAM_T])
            bomber.has_bomb = True
            self.bomb_carrier_pid = bomber.pid
        self.phase = "freeze"
        self.phase_ends = time.time() + FREEZE_TIME
        self.round_ends = self.phase_ends + ROUND_TIME

    def _living_count(self, team: str) -> int:
        return sum(1 for p in self.players.values() if p.alive and p.team == team)

    def _end_round(self, winner: str, reason: str):
        self.phase = "over"
        self.round_win_reason = reason
        if winner == TEAM_T:
            self.score_t += 1
        elif winner == TEAM_CT:
            self.score_ct += 1
        for p in self.players.values():
            if p.team == winner:
                p.money = min(MAX_MONEY, p.money + WIN_BONUS)
                p.loss_streak = 0
            else:
                p.loss_streak += 1
                bonus = LOSS_BONUS + min(3, p.loss_streak) * LOSS_STREAK_BONUS
                p.money = min(MAX_MONEY, p.money + bonus)
        if self.score_t >= ROUNDS_TO_WIN:
            self.match_over = True
            self.match_winner = TEAM_T
        elif self.score_ct >= ROUNDS_TO_WIN:
            self.match_over = True
            self.match_winner = TEAM_CT
        self.phase_ends = time.time() + 5.0

    def _update_bomb(self, dt: float, now: float):
        from shared.dust2_map import DEFUSE_TIME, PLANT_TIME, BOMB_TIMER

        if self.bomb_planted and now >= self.bomb_explodes_at:
            self._end_round(TEAM_T, "Target successfully detonated.")
            return

        for p in self.players.values():
            if not p.alive:
                p.planting = False
                p.defusing = False
                continue
            if p.planting:
                site = nearest_site(p.x, p.z)
                if site and p.has_bomb and p.team == TEAM_T and not self.bomb_planted:
                    p.plant_progress += dt
                    if p.plant_progress >= PLANT_TIME:
                        self.bomb_planted = True
                        self.bomb_site = site
                        self.bomb_x, self.bomb_z = p.x, p.z
                        p.has_bomb = False
                        self.bomb_carrier_pid = -1
                        p.planting = False
                        p.plant_progress = 0.0
                        self.bomb_explodes_at = now + BOMB_TIMER
                        p.money = min(MAX_MONEY, p.money + PLANT_REWARD)
                else:
                    p.planting = False
                    p.plant_progress = 0.0
            if p.defusing and self.bomb_planted and p.team == TEAM_CT:
                if math.hypot(p.x - self.bomb_x, p.z - self.bomb_z) < 4.0:
                    p.defuse_progress += dt
                    if p.defuse_progress >= DEFUSE_TIME:
                        self._end_round(TEAM_CT, "Bomb has been defused.")
                        p.money = min(MAX_MONEY, p.money + DEFUSE_REWARD)
                        return
                else:
                    p.defusing = False
                    p.defuse_progress = 0.0

    def _tick_round_logic(self, now: float):
        if self.match_over:
            return
        if self.phase == "warmup":
            if len(self.players) >= 1 and all(not p.is_bot for p in self.players.values()):
                if sum(1 for p in self.players.values() if not p.is_bot) >= 1:
                    self._start_round()
            return
        if self.phase == "freeze" and now >= self.phase_ends:
            self.phase = "live"
        if self.phase == "over" and now >= self.phase_ends:
            if not self.match_over:
                self._start_round()
            return
        if self.phase != "live":
            return
        if self.round_ends > 0 and now >= self.round_ends and not self.bomb_planted:
            self._end_round(TEAM_CT, "Round time expired — CT win.")
            return
        t_alive = self._living_count(TEAM_T)
        ct_alive = self._living_count(TEAM_CT)
        if t_alive == 0 and not self.bomb_planted:
            self._end_round(TEAM_CT, "Elimination — CT win.")
        elif ct_alive == 0 and not self.bomb_planted:
            self._end_round(TEAM_T, "Elimination — T win.")
        elif ct_alive == 0 and self.bomb_planted:
            pass  # wait for boom or defuse

    def _bot_think(self, p: Player, dt: float, now: float):
        if now < p.bot_next_think:
            return
        p.bot_next_think = now + random.uniform(0.15, 0.45)
        if p.team == TEAM_T and random.random() < 0.35:
            p.bot_goal = "B"
        elif random.random() < 0.4:
            p.bot_goal = "A"
        else:
            p.bot_goal = "mid"
        goals = {
            "A": (-32, 28),
            "B": (30, 22),
            "mid": (0, -4),
        }
        gx, gz = goals.get(p.bot_goal, (0, -4))
        dx, dz = gx - p.x, gz - p.z
        self._move(p, dx, dz, dt)
        p.yaw = math.atan2(dx, dz) if math.hypot(dx, dz) > 0.1 else p.yaw
        # shoot nearest enemy
        for tgt in self.players.values():
            if tgt.team != p.team and tgt.alive:
                if math.hypot(tgt.x - p.x, tgt.z - p.z) < 25:
                    p.pitch = 0.0
                    p.yaw = math.atan2(tgt.x - p.x, tgt.z - p.z)
                    self._shoot(p, now)
                    break
        if p.team == TEAM_T and p.has_bomb and nearest_site(p.x, p.z):
            p.planting = True

    def spawn_bot(self) -> Optional[Player]:
        if len(self.players) >= MAX_PLAYERS:
            return None
        pid = self.next_pid
        self.next_pid += 1
        team = self._pick_team()
        sx, sz = self._spawn_for_team(team)
        used = {pl.name for pl in self.players.values()}
        name = next((n for n in BOT_NAMES if n not in used), f"Bot{pid}")
        p = Player(pid=pid, name=name, team=team, x=sx, z=sz, is_bot=True)
        self._reset_player_loadout(p)
        self.players[pid] = p
        return p

    async def handle_client(self, reader, writer):
        if len(self.players) >= MAX_PLAYERS:
            await self._send(writer, {"t": "error", "msg": "Server full (Valve Time queue)."})
            writer.close()
            return
        try:
            line = await asyncio.wait_for(reader.readline(), 10)
            msg = json.loads(line.decode().strip())
            if msg.get("t") != "join":
                writer.close()
                return
            name = str(msg.get("name", "Player"))[:16] or "Player"
            team = msg.get("team")
            if team not in (TEAM_T, TEAM_CT):
                team = self._pick_team()
            bots = max(0, min(int(msg.get("bots", 0)), MAX_PLAYERS - 1))
        except Exception:
            writer.close()
            return

        pid = self.next_pid
        self.next_pid += 1
        sx, sz = self._spawn_for_team(team)
        p = Player(pid=pid, name=name, team=team, x=sx, z=sz, writer=writer)
        self._reset_player_loadout(p)
        self.players[pid] = p
        if self.phase == "warmup" and self.round == 0:
            spawn_bots = max(bots, self.pending_bots)
            if spawn_bots:
                for _ in range(spawn_bots):
                    self.spawn_bot()
                self.pending_bots = 0
            if len(self.players) >= 2:
                self._start_round()

        await self._send(writer, {
            "t": "welcome",
            "pid": pid,
            "team": team,
            "map": wall_dicts(),
            "props": prop_dicts(),
            "weapons": WEAPONS,
            "buy_order": BUY_MENU_ORDER,
            "bombsite_a": BOMBSITE_A,
            "bombsite_b": BOMBSITE_B,
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
        finally:
            self.players.pop(pid, None)
            writer.close()

    async def handle_msg(self, p: Player, msg: dict):
        if p.is_bot:
            return
        t = msg.get("t")
        now = time.time()
        if t == "input":
            dt = float(msg.get("dt", 1 / TICK_RATE))
            dt = max(0.001, min(0.05, dt))
            self._move(p, float(msg.get("dx", 0)), float(msg.get("dz", 0)), dt)
            p.yaw = float(msg.get("yaw", p.yaw))
            p.pitch = float(msg.get("pitch", p.pitch))
            p.crouching = bool(msg.get("crouch", False))
        elif t == "shoot":
            p.yaw = float(msg.get("yaw", p.yaw))
            p.pitch = float(msg.get("pitch", p.pitch))
            self._shoot(p, now)
        elif t == "reload":
            stats = WEAPONS.get(p.weapon, {})
            need = stats.get("mag", 0) - p.mag
            if need > 0 and p.reserve > 0:
                take = min(need, p.reserve)
                p.mag += take
                p.reserve -= take
        elif t == "plant":
            p.planting = bool(msg.get("on", False))
            if not p.planting:
                p.plant_progress = 0.0
        elif t == "defuse":
            p.defusing = bool(msg.get("on", False))
            if not p.defusing:
                p.defuse_progress = 0.0
        elif t == "buy":
            wid = msg.get("weapon")
            if self.phase not in ("freeze", "over", "warmup"):
                return
            if wid not in WEAPONS:
                return
            item = WEAPONS[wid]
            if item["team"] not in ("both", p.team):
                return
            if p.money < item["price"]:
                return
            if wid == "kevlar":
                p.armor = 100
                p.money -= item["price"]
                return
            p.money -= item["price"]
            p.weapon = wid
            p.mag = item["mag"]
            p.reserve = item["reserve"]

    def _build_state(self, viewer: Player, now: float) -> dict:
        players = []
        for pl in self.players.values():
            players.append({
                "pid": pl.pid,
                "name": pl.name,
                "team": pl.team,
                "x": round(pl.x, 3),
                "z": round(pl.z, 3),
                "yaw": round(pl.yaw, 3),
                "pitch": round(pl.pitch, 3),
                "hp": pl.hp,
                "armor": pl.armor,
                "alive": pl.alive,
                "weapon": pl.weapon,
                "mag": pl.mag,
                "reserve": pl.reserve,
                "money": pl.money,
                "has_bomb": pl.has_bomb,
                "planting": pl.planting,
                "defusing": pl.defusing,
                "plant_p": round(pl.plant_progress, 2),
                "defuse_p": round(pl.defuse_progress, 2),
                "kills": pl.kills,
                "deaths": pl.deaths,
                "is_bot": pl.is_bot,
            })
        time_left = max(0.0, self.round_ends - now) if self.phase == "live" else 0.0
        freeze_left = max(0.0, self.phase_ends - now) if self.phase == "freeze" else 0.0
        return {
            "t": "state",
            "ts": now,
            "players": players,
            "phase": self.phase,
            "round": self.round,
            "score_t": self.score_t,
            "score_ct": self.score_ct,
            "time_left": round(time_left, 1),
            "freeze_left": round(freeze_left, 1),
            "bomb_planted": self.bomb_planted,
            "bomb_site": self.bomb_site,
            "bomb_x": self.bomb_x,
            "bomb_z": self.bomb_z,
            "bomb_explodes_in": round(max(0, self.bomb_explodes_at - now), 1) if self.bomb_planted else 0,
            "round_reason": self.round_win_reason,
            "match_over": self.match_over,
            "match_winner": self.match_winner,
            "my_pid": viewer.pid,
        }

    async def tick(self):
        dt = 1.0 / TICK_RATE
        now = time.time()
        self._update_bomb(dt, now)
        self._tick_round_logic(now)
        for p in self.players.values():
            if p.is_bot and p.alive:
                self._bot_think(p, dt, now)
        dead = []
        for pl in self.players.values():
            if pl.is_bot or pl.writer is None:
                continue
            try:
                payload = self._build_state(pl, now)
                pl.writer.write((json.dumps(payload) + "\n").encode())
                await pl.writer.drain()
            except Exception:
                dead.append(pl.pid)
        for pid in dead:
            self.players.pop(pid, None)

    async def _send(self, writer, obj):
        writer.write((json.dumps(obj) + "\n").encode())
        await writer.drain()

    async def run(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"[fan-strike] de_dust_valley on port {self.port} @ {TICK_RATE} tick")

        async def ticker():
            interval = 1.0 / TICK_RATE
            nxt = time.time()
            while True:
                await self.tick()
                nxt += interval
                s = nxt - time.time()
                if s > 0:
                    await asyncio.sleep(s)
                else:
                    nxt = time.time()

        async with server:
            await asyncio.gather(server.serve_forever(), ticker())


def main():
    ap = argparse.ArgumentParser(description="Global Fan-Strike dedicated server")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--bots", type=int, default=0)
    args = ap.parse_args()
    srv = GameServer(args.host, args.port)
    srv.pending_bots = max(0, args.bots)
    try:
        asyncio.run(srv.run())
    except KeyboardInterrupt:
        print("\n[server] shutdown — see you in Valve Time.")


if __name__ == "__main__":
    main()
