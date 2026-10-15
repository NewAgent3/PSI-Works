"""Headless checks for bots, stealth, and match state."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

from server import BRAWLERS, Bush, GameServer, Player  # noqa: E402


def test_bots_and_stealth():
    srv = GameServer("127.0.0.1", 5555)
    srv.spawn_bots(2)
    assert len(srv.players) == 2
    assert all(p.is_bot for p in srv.players.values())

    human = Player(pid=99, name="You", brawler="spike", x=0, z=0, hp=700, max_hp=700, speed=6.2)
    bot = next(iter(srv.players.values()))
    now = time.time()
    bot.x, bot.z = 4, 0
    human.x, human.z = 0, 0
    bot.revealed_until = now - 1
    srv.bushes = [Bush(0, 0, r=3.0)]
    bot.x, bot.z = 0, 0
    assert srv._inside_bush(bot)
    assert srv._is_stealthed(bot, now)
    assert not srv._visible_to(human, bot, now)

    state = srv._build_state_for(human, now)
    hidden_entry = next(p for p in state["players"] if p["pid"] == bot.pid)
    assert hidden_entry["hidden"] is True
    assert "time_left" in state
    print("ok: bots, stealth, and state payload")


if __name__ == "__main__":
    test_bots_and_stealth()
