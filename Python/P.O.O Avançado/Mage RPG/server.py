import socket
import threading
import json
import traceback
import time
import random
import math
import os
from pathlib import Path

GAME_PORT = 5555
DISCOVERY_PORT = 5556
SEED = random.randint(1, 999999)

# Save to user's home directory to avoid permission issues
SAVE_DIR = Path.home() / "mmo_saves"
SAVE_DIR.mkdir(exist_ok=True)
SAVE_FILE = SAVE_DIR / "players.json"

# =====================
# GAME STATE
# =====================
# pid -> {x,y,hp,max_hp,mp,max_mp,xp,lvl,str,int,agi,color,name,quests,inventory,spells}
players = {}
mobs = {}             # mid -> {x,y,hp,max_hp,type,level,aggro_target}
npcs = {}             # nid -> {x,y,name,type,dialogue,quest_giver}
connections = {}      # pid -> socket
ground_items = {}     # iid -> {x,y,name,item_id}
next_item_id = 0

# Mob definitions
MOB_TYPES = {
    "Slime":   {"base_hp": 30, "color": (200, 0, 200), "xp": 50,
                "drops": [("health_potion", 0.3), ("gold", 0.5)],
                "damage": 5, "aggro_range": 150},
    "Goblin":  {"base_hp": 60, "color": (0, 200, 0), "xp": 80,
                "drops": [("health_potion", 0.2), ("mana_potion", 0.2), ("gold", 0.7)],
                "damage": 8, "aggro_range": 200},
    "Dragon":  {"base_hp": 200, "color": (200, 100, 0), "xp": 300,
                "drops": [("fireball_tome", 0.1), ("dragon_scale", 0.5), ("gold", 1.0)],
                "damage": 20, "aggro_range": 300},
}

# NPC definitions
NPCS = [
    {"name": "Elder Quinn", "x": 400, "y": 400,
        "type": "quest", "dialogue": "Slay 20 slimes for me!"},
    {"name": "Merlin", "x": 1200, "y": 800, "type": "trainer",
        "dialogue": "I can teach you spells."},
]

# Spell definitions
SPELLS = {
    "Fireball":   {"mana_cost": 20, "base_damage": 25, "cooldown": 2.0, "type": "damage"},
    "Heal":       {"mana_cost": 30, "base_heal": 40, "cooldown": 3.0, "type": "heal"},
    "Lightning":  {"mana_cost": 40, "base_damage": 50, "cooldown": 4.0, "type": "damage"},
}

# Track spell cooldowns per player
player_cooldowns = {}  # pid -> {spell_name: expiry_time}


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# =====================
# DISCOVERY
# =====================


def discovery_service():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data.decode() == "DISCOVER_MMO_SERVER":
                sock.sendto(b"MMO_SERVER_HERE", addr)
        except:
            pass

# =====================
# SAVE/LOAD PLAYERS
# =====================


def load_players():
    global players
    if SAVE_FILE.exists():
        with open(SAVE_FILE, "r") as f:
            players = json.load(f)
    # ensure all players have required fields
    for pid, p in players.items():
        p.setdefault("inventory", [])
        p.setdefault("spells", ["Fireball"])
        p.setdefault("mana", 100)
        p.setdefault("max_mana", 100)
        p.setdefault("quest_slime", 0)
        p.setdefault("quest_goblin", 0)
        p.setdefault("gold", 0)
        p.setdefault("str", 5)
        p.setdefault("int", 5)
        p.setdefault("agi", 5)
        p.setdefault("xp", 0)
        p.setdefault("lvl", 1)


def save_players():
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(players, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save players: {e}")

# =====================
# GAME LOOP
# =====================


def game_loop():
    last_save = time.time()
    while True:
        time.sleep(0.1)  # 10 Hz

        # Mob AI
        for m_id, mob in list(mobs.items()):
            # Aggro: chase nearest player if in range
            if "aggro_target" in mob and mob["aggro_target"] in players:
                target = players[mob["aggro_target"]]
                dx = target["x"] - mob["x"]
                dy = target["y"] - mob["y"]
                dist = math.hypot(dx, dy)
                if dist > 10:
                    # move toward target
                    move = min(5, dist/5)
                    mob["x"] += (dx / dist) * move
                    mob["y"] += (dy / dist) * move
                # attack if close enough
                if dist < 50:
                    # damage player
                    dmg = MOB_TYPES[mob["type"]]["damage"] * \
                        mob.get("level", 1)
                    target["hp"] -= dmg
                    if target["hp"] <= 0:
                        target["hp"] = target["max_hp"]
                        target["x"] = random.randint(100, 500)
                        target["y"] = random.randint(100, 500)
            else:
                # Wander if no target
                if random.random() < 0.1:
                    mob["x"] += random.choice([-8, 8, 0])
                    mob["y"] += random.choice([-8, 8, 0])
                    mob["x"] = max(50, min(1950, mob["x"]))
                    mob["y"] = max(50, min(1950, mob["y"]))

            # Check for new aggro (player nearby)
            if "aggro_target" not in mob or mob["aggro_target"] not in players:
                for pid, p in players.items():
                    dist = math.hypot(p["x"] - mob["x"], p["y"] - mob["y"])
                    if dist < MOB_TYPES[mob["type"]]["aggro_range"]:
                        mob["aggro_target"] = pid
                        break

        # Mana regen for players
        for pid, p in players.items():
            if p["mana"] < p["max_mana"]:
                p["mana"] = min(p["max_mana"], p["mana"] + 1)

        # Broadcast state
        broadcast_state()

        # Auto‑save every 60 seconds
        if time.time() - last_save > 60:
            save_players()
            last_save = time.time()


def broadcast_state():
    """Sends world state to all clients."""
    state = {
        "players": players,
        "mobs": mobs,
        "npcs": {str(i): npc for i, npc in enumerate(NPCS)},  # send NPCs
        "seed": SEED,
        "items": ground_items
    }
    msg = (json.dumps(state) + "\n").encode()
    for conn in list(connections.values()):
        try:
            conn.send(msg)
        except:
            pass


def send_chat(sender, text):
    """Broadcast a chat message to all."""
    msg = json.dumps({"type": "CHAT", "sender": sender, "text": text}) + "\n"
    for conn in connections.values():
        try:
            conn.send(msg.encode())
        except:
            pass


def send_sync(conn, pid):
    """Send personal data (inventory, spells, stats) to a specific player."""
    p = players[pid]
    sync = {
        "type": "SYNC",
        "inventory": p.get("inventory", []),
        "spells": p.get("spells", []),
        "stats": {k: p.get(k, 0) for k in ["str", "int", "agi", "xp", "lvl", "gold", "quest_slime", "quest_goblin"]}
    }
    try:
        conn.send((json.dumps(sync) + "\n").encode())
    except:
        pass


def send_cooldown(conn, pid, spell_name, remaining):
    """Send cooldown update to player."""
    msg = json.dumps({"type": "COOLDOWN", "spell": spell_name,
                     "cooldown": remaining}) + "\n"
    try:
        conn.send(msg.encode())
    except:
        pass

# =====================
# COMBAT & SPELLS
# =====================


def handle_attack(attacker_id, target_id, damage):
    if target_id in mobs:
        mob = mobs[target_id]
        dist = math.hypot(players[attacker_id]["x"] - mob["x"],
                          players[attacker_id]["y"] - mob["y"])
        if dist < 80:
            # scale damage with strength
            dmg = damage + players[attacker_id].get("str", 0) // 2
            mob["hp"] -= dmg
            # set aggro to attacker
            mob["aggro_target"] = attacker_id
            if mob["hp"] <= 0:
                # Reward player
                p = players[attacker_id]
                xp_gain = MOB_TYPES[mob["type"]]["xp"] * mob.get("level", 1)
                p["xp"] += xp_gain
                # Level up
                while p["xp"] >= 100:
                    p["lvl"] += 1
                    p["xp"] -= 100
                    p["max_hp"] += 20
                    p["hp"] = p["max_hp"]
                    p["max_mana"] += 10
                    p["mana"] = p["max_mana"]
                    p["str"] += 2
                    p["int"] += 2
                    p["agi"] += 2
                # Quest progress
                if mob["type"] == "Slime":
                    p["quest_slime"] = p.get("quest_slime", 0)+1
                elif mob["type"] == "Goblin":
                    p["quest_goblin"] = p.get("quest_goblin", 0)+1
                # Drop items on ground
                for item_name, chance in mob["drops"]:
                    if random.random() < chance:
                        drop_item(
                            item_name, mob["x"] + random.randint(-20, 20), mob["y"] + random.randint(-20, 20))
                # Remove mob
                del mobs[target_id]
                # Respawn a new mob elsewhere after a delay? For now, respawn immediately
                new_type = random.choice(list(MOB_TYPES.keys()))
                base = MOB_TYPES[new_type]
                new_id = f"{new_type}_{random.randint(1000, 9999)}"
                mobs[new_id] = {
                    "x": random.randint(100, 1900),
                    "y": random.randint(100, 1900),
                    "hp": base["base_hp"] * (1 + random.randint(0, 2)),
                    "max_hp": base["base_hp"] * (1 + random.randint(0, 2)),
                    "type": new_type,
                    "level": random.randint(1, 5),
                    "drops": base["drops"]
                }
    elif target_id in players:
        target = players[target_id]
        dist = math.hypot(players[attacker_id]["x"] - target["x"],
                          players[attacker_id]["y"] - target["y"])
        if dist < 80:
            dmg = damage + players[attacker_id].get("str", 0) // 2
            target["hp"] -= dmg
            if target["hp"] <= 0:
                target["hp"] = target["max_hp"]
                target["x"] = random.randint(100, 500)
                target["y"] = random.randint(100, 500)


def handle_spell(attacker_id, spell_name, target_id, tx, ty):
    if spell_name not in SPELLS:
        return
    spell = SPELLS[spell_name]
    p = players[attacker_id]
    now = time.time()

    # Check cooldown
    if attacker_id in player_cooldowns and spell_name in player_cooldowns[attacker_id]:
        if player_cooldowns[attacker_id][spell_name] > now:
            remaining = player_cooldowns[attacker_id][spell_name] - now
            send_cooldown(connections.get(attacker_id),
                          attacker_id, spell_name, remaining)
            return

    # Check mana
    if p["mana"] < spell["mana_cost"]:
        return
    p["mana"] -= spell["mana_cost"]

    # Apply cooldown
    if attacker_id not in player_cooldowns:
        player_cooldowns[attacker_id] = {}
    player_cooldowns[attacker_id][spell_name] = now + spell["cooldown"]
    send_cooldown(connections.get(attacker_id), attacker_id,
                  spell_name, spell["cooldown"])

    # Spell effects scaled by intelligence
    int_stat = p.get("int", 5)
    if spell["type"] == "damage" and target_id:
        if target_id in mobs:
            mob = mobs[target_id]
            dist = math.hypot(p["x"] - mob["x"], p["y"] - mob["y"])
            if dist < 150:
                dmg = spell["base_damage"] + int_stat * 2
                mob["hp"] -= dmg
                mob["aggro_target"] = attacker_id
                if mob["hp"] <= 0:
                    # similar rewards as attack (simplified)
                    p["xp"] += 50  # etc.
                    del mobs[target_id]
                    # drop items...
        elif target_id in players:
            target = players[target_id]
            dist = math.hypot(p["x"] - target["x"], p["y"] - target["y"])
            if dist < 150:
                dmg = spell["base_damage"] + int_stat * 2
                target["hp"] -= dmg
    elif spell["type"] == "heal" and target_id and target_id in players:
        target = players[target_id]
        heal = spell["base_heal"] + int_stat * 3
        target["hp"] = min(target["max_hp"], target["hp"] + heal)


def drop_item(name, x, y):
    global next_item_id
    iid = f"item_{next_item_id}"
    next_item_id += 1
    ground_items[iid] = {"x": x, "y": y, "name": name, "item_id": name}


def handle_pickup(player_id, item_id):
    if item_id in ground_items:
        item = ground_items.pop(item_id)
        players[player_id]["inventory"].append(item["name"])
        send_chat(
            "Server", f"{players[player_id].get('name', player_id)} picked up {item['name']}")

# =====================
# CLIENT HANDLER
# =====================


def handle_client(conn, addr):
    player_id = f"{addr[0]}:{addr[1]}"
    print(f"Connected: {player_id}")

    # Default name
    player_name = f"Hero{random.randint(100, 999)}"

    # Load or create player
    if player_id in players:
        p = players[player_id]
    else:
        p = {
            "x": 500, "y": 500,
            "hp": 100, "max_hp": 100,
            "mana": 100, "max_mana": 100,
            "xp": 0, "lvl": 1,
            "str": 5, "int": 5, "agi": 5,
            "quest_slime": 0,
            "quest_goblin": 0,
            "inventory": [],
            "spells": ["Fireball"],
            "gold": 0,
            "color": (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)),
            "name": player_name
        }
    players[player_id] = p
    connections[player_id] = conn

    # Send initial sync
    send_sync(conn, player_id)

    buffer = ""
    while True:
        try:
            chunk = conn.recv(4096).decode()
            if not chunk:
                break

            buffer += chunk
            while "\n" in buffer:
                msg, buffer = buffer.split("\n", 1)
                if not msg:
                    continue

                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "MOVE":
                    if player_id in players:
                        players[player_id]["x"] = data["x"]
                        players[player_id]["y"] = data["y"]

                elif msg_type == "ATTACK":
                    handle_attack(
                        player_id, data["target_id"], data.get("damage", 10))

                elif msg_type == "CAST_SPELL":
                    handle_spell(player_id,
                                 data["spell"],
                                 data.get("target_id"),
                                 data.get("x", 0),
                                 data.get("y", 0))

                elif msg_type == "CHAT":
                    text = data.get("text", "")
                    # Handle commands
                    if text.startswith("/stats"):
                        s = players[player_id]
                        reply = f"Lvl {s['lvl']} | Str {s['str']} Int {s['int']} Agi {s['agi']} | HP {s['hp']}/{s['max_hp']} Mana {s['mana']}/{s['max_mana']}"
                        send_chat("Server", reply)
                    elif text.startswith("/quests"):
                        s = players[player_id]
                        reply = f"Slimes: {s.get('quest_slime', 0)}/20, Goblins: {s.get('quest_goblin', 0)}/10"
                        send_chat("Server", reply)
                    elif text.startswith("/inventory"):
                        inv = players[player_id].get("inventory", [])
                        reply = "Inventory: " + \
                            ", ".join(inv) if inv else "Empty"
                        send_chat("Server", reply)
                    else:
                        send_chat(players[player_id].get(
                            "name", player_id), text)

                elif msg_type == "LOGIN":
                    if "name" in data:
                        players[player_id]["name"] = data["name"]

                elif msg_type == "PICKUP":
                    handle_pickup(player_id, data["item_id"])

        except Exception as e:
            print(f"Error with {player_id}: {e}")
            break

    print(f"Disconnected: {player_id}")
    if player_id in players:
        del players[player_id]
    if player_id in connections:
        del connections[player_id]
    if player_id in player_cooldowns:
        del player_cooldowns[player_id]
    conn.close()
    save_players()

# =====================
# MAIN
# =====================


def main():
    load_players()
    ip = get_local_ip()
    print(f"MMO SERVER STARTED ON {ip}:{GAME_PORT} (seed {SEED})")
    print(f"Saving players to {SAVE_FILE}")

    threading.Thread(target=discovery_service, daemon=True).start()
    threading.Thread(target=game_loop, daemon=True).start()

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", GAME_PORT))
    server.listen()

    while True:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(
                conn, addr), daemon=True).start()
        except:
            pass


if __name__ == "__main__":
    main()
