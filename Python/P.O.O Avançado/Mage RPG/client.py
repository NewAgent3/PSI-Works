import pygame
import socket
import threading
import json
import time
import random
import math
import os

# Use existing magic files
from livro_magia import LivroDeMagia
from truque_elemento import TruqueElemento
from truque_mental import TruqueMental

# Config
SCREEN_W, SCREEN_H = 800, 600
GAME_PORT = 5555
DISCOVERY_PORT = 5556

# Network State
players = {}
mobs = {}
npcs = {}                # {id: {x, y, name, type, dialogue}}
world_seed = 0
my_id = None
chat_messages = []       # list of (sender, text)
ground_items = {}        # {id: {x, y, name, item_id, owner?}}
inventory = []           # local inventory (synced)
spells_known = []        # list of spell names
cooldowns = {}           # spell name -> remaining time (client approx)
player_stats = {}        # stats from server

# =====================
# NETWORKING
# =====================
sock = socket.socket()


def discover_and_connect():
    print("Looking for servers...")
    disc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    disc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    disc_sock.settimeout(2)

    try:
        disc_sock.sendto(b"DISCOVER_MMO_SERVER",
                         ("<broadcast>", DISCOVERY_PORT))
        data, addr = disc_sock.recvfrom(1024)
        if data == b"MMO_SERVER_HERE":
            print(f"Found server at {addr[0]}")
            return addr[0]
    except:
        return "127.0.0.1"  # Fallback


server_ip = discover_and_connect()
sock.connect((server_ip, GAME_PORT))


def network_thread():
    global players, mobs, npcs, world_seed, chat_messages, ground_items, inventory, spells_known, cooldowns, player_stats
    buffer = ""
    while True:
        try:
            chunk = sock.recv(4096).decode()
            if not chunk:
                break
            buffer += chunk

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line:
                    continue

                data = json.loads(line)
                # Game state broadcast
                if "players" in data:
                    players = data.get("players", {})
                    mobs = data.get("mobs", {})
                    npcs = data.get("npcs", {})
                    world_seed = data.get("seed", 0)
                    ground_items = data.get("items", {})
                # Chat message
                elif data.get("type") == "CHAT":
                    chat_messages.append((data["sender"], data["text"]))
                    if len(chat_messages) > 50:
                        chat_messages.pop(0)
                # Sync personal data (inventory, spells, stats)
                elif data.get("type") == "SYNC":
                    inventory = data.get("inventory", [])
                    spells_known = data.get("spells", [])
                    player_stats = data.get("stats", {})
                # Cooldown update
                elif data.get("type") == "COOLDOWN":
                    spell = data["spell"]
                    cd = data["cooldown"]
                    cooldowns[spell] = cd
        except:
            break


threading.Thread(target=network_thread, daemon=True).start()

# =====================
# PROCEDURAL WORLD (improved noise)
# =====================


def get_terrain_at(x, y, seed):
    """Simple pseudo‑noise for biomes"""
    random.seed(seed + int(x * 0.1) + int(y * 0.1) * 1000)
    val = random.random()
    if val < 0.15:
        return "WATER"
    elif val < 0.3:
        return "SAND"
    elif val < 0.7:
        return "GRASS"
    elif val < 0.9:
        return "FOREST"
    else:
        return "MOUNTAIN"

# =====================
# LOCAL PLAYER (with magic)
# =====================


class LocalPlayer:
    def __init__(self):
        self.x = 500
        self.y = 500
        self.speed = 5
        self.grimoire = LivroDeMagia()
        # Start with one spell (will be synced from server later)
        self.grimoire.adicionar(TruqueElemento("Fireball", 1, "Fire"))
        self.selected_spell_index = 0
        self.mana = 100
        self.max_mana = 100
        self.last_cast_time = 0
        # seconds between casts (client-side cooldown, server has own)
        self.cast_cooldown = 0.5

        # Chat input
        self.chat_input = ""
        self.chat_active = False

        # UI toggles
        self.show_inventory = False
        self.show_spellbook = False
        self.show_stats = False
        self.show_minimap = True

        # Particle effects
        self.effects = []  # list of (x,y,type,start_time)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        # Movement (only if chat not active)
        if not self.chat_active:
            dx, dy = 0, 0
            if keys[pygame.K_w]:
                dy -= self.speed
            if keys[pygame.K_s]:
                dy += self.speed
            if keys[pygame.K_a]:
                dx -= self.speed
            if keys[pygame.K_d]:
                dx += self.speed
            if dx != 0 or dy != 0:
                self.x += dx
                self.y += dy
                # Send move packet
                send_json({"type": "MOVE", "x": self.x, "y": self.y})

        # Chat toggle
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.chat_active = not self.chat_active
                    if not self.chat_active and self.chat_input:
                        # Send chat message
                        send_json({"type": "CHAT", "text": self.chat_input})
                        self.chat_input = ""
                elif event.key == pygame.K_BACKSPACE and self.chat_active:
                    self.chat_input = self.chat_input[:-1]
                elif event.key == pygame.K_i:
                    self.show_inventory = not self.show_inventory
                elif event.key == pygame.K_s:
                    self.show_spellbook = not self.show_spellbook
                elif event.key == pygame.K_c:
                    self.show_stats = not self.show_stats
                elif event.key == pygame.K_m:
                    self.show_minimap = not self.show_minimap
                elif event.key == pygame.K_1:
                    self.selected_spell_index = 0
                elif event.key == pygame.K_2:
                    self.selected_spell_index = min(
                        1, len(self.grimoire.truques)-1)
                elif event.key == pygame.K_3:
                    self.selected_spell_index = min(
                        2, len(self.grimoire.truques)-1)
                elif event.key == pygame.K_4:
                    self.selected_spell_index = min(
                        3, len(self.grimoire.truques)-1)
                elif event.key == pygame.K_5:
                    self.selected_spell_index = min(
                        4, len(self.grimoire.truques)-1)
                elif event.key == pygame.K_6:
                    self.selected_spell_index = min(
                        5, len(self.grimoire.truques)-1)
                elif self.chat_active and event.unicode:
                    self.chat_input += event.unicode

        # Mouse interaction
        mouse_buttons = pygame.mouse.get_pressed()
        if not self.chat_active:
            mx, my = pygame.mouse.get_pos()
            wx = mx + camera.x
            wy = my + camera.y

            # Left click – attack / pick up item
            if mouse_buttons[0]:
                # First check if we clicked on a ground item (pickup)
                picked = False
                for iid, item in ground_items.items():
                    d = math.hypot(wx - item["x"], wy - item["y"])
                    if d < 30:
                        send_json({"type": "PICKUP", "item_id": iid})
                        picked = True
                        break
                if not picked:
                    # Find closest target (mob or player)
                    target_id = None
                    min_dist = 60
                    for mid, m in mobs.items():
                        d = math.hypot(wx - m["x"], wy - m["y"])
                        if d < min_dist:
                            target_id = mid
                            min_dist = d
                    for pid, p in players.items():
                        if pid != my_id:
                            d = math.hypot(wx - p["x"], wy - p["y"])
                            if d < min_dist:
                                target_id = pid
                                min_dist = d
                    if target_id:
                        send_json(
                            {"type": "ATTACK", "target_id": target_id, "damage": 10})

            # Right click – cast selected spell
            if mouse_buttons[2]:
                if time.time() - self.last_cast_time > 0.3:  # throttle
                    # Find target under mouse
                    target_id = None
                    min_dist = 60
                    for mid, m in mobs.items():
                        d = math.hypot(wx - m["x"], wy - m["y"])
                        if d < min_dist:
                            target_id = mid
                            min_dist = d
                    for pid, p in players.items():
                        if pid != my_id:
                            d = math.hypot(wx - p["x"], wy - p["y"])
                            if d < min_dist:
                                target_id = pid
                                min_dist = d

                    spell_name = self.grimoire.truques[self.selected_spell_index].nome if self.grimoire.truques else None
                    if spell_name:
                        send_json({
                            "type": "CAST_SPELL",
                            "spell": spell_name,
                            "target_id": target_id,
                            "x": wx, "y": wy
                        })
                        # Add visual effect
                        self.effects.append((wx, wy, spell_name, time.time()))
                        self.last_cast_time = time.time()

        return True


def send_json(data):
    try:
        sock.send((json.dumps(data) + "\n").encode())
    except:
        pass

# =====================
# CAMERA (with smoothing)
# =====================


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.smooth_speed = 0.1

    def update(self, target):
        target_x = target.x - SCREEN_W // 2
        target_y = target.y - SCREEN_H // 2
        self.x += (target_x - self.x) * self.smooth_speed
        self.y += (target_y - self.y) * self.smooth_speed

# =====================
# UI RENDERING
# =====================


def draw_ui(screen, me, my_stats):
    # Chat box (bottom left)
    chat_surf = pygame.Surface((400, 120))
    chat_surf.set_alpha(180)
    chat_surf.fill((0, 0, 0))
    screen.blit(chat_surf, (10, SCREEN_H-130))

    y_offset = SCREEN_H-125
    for sender, text in chat_messages[-5:]:
        msg = f"{sender}: {text}"
        txt = font.render(msg, True, (255, 255, 255))
        screen.blit(txt, (15, y_offset))
        y_offset += 18

    if me.chat_active:
        prompt = "> " + me.chat_input + "_"
        txt = font.render(prompt, True, (255, 255, 255))
        screen.blit(txt, (15, SCREEN_H-25))

    # Mana bar (top right)
    if my_stats:
        mana_pct = my_stats.get("mana", 0) / my_stats.get("max_mana", 1)
        pygame.draw.rect(screen, (0, 0, 150), (SCREEN_W-210, 10, 200, 20))
        pygame.draw.rect(screen, (0, 100, 255),
                         (SCREEN_W-210, 10, 200 * mana_pct, 20))
        mana_text = font.render(
            f"Mana: {my_stats['mana']}/{my_stats['max_mana']}", True, (255, 255, 255))
        screen.blit(mana_text, (SCREEN_W-200, 12))

    # Hotbar (bottom center)
    hotbar_y = SCREEN_H - 70
    for i in range(6):
        rect = (SCREEN_W//2 - 180 + i*60, hotbar_y, 50, 50)
        color = (100, 100, 100)
        if i < len(me.grimoire.truques):
            spell = me.grimoire.truques[i].nome
            # color by element (just for fun)
            if "Fire" in spell:
                color = (200, 50, 50)
            elif "Heal" in spell:
                color = (50, 200, 50)
            elif "Lightning" in spell:
                color = (255, 255, 0)
            else:
                color = (150, 150, 150)
            # Cooldown overlay
            if spell in cooldowns and cooldowns[spell] > 0:
                overlay = pygame.Surface((50, 50))
                overlay.set_alpha(128)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, rect)
                cd_text = font.render(
                    str(int(cooldowns[spell])), True, (255, 255, 255))
                screen.blit(cd_text, (rect[0]+15, rect[1]+15))
        if i == me.selected_spell_index:
            pygame.draw.rect(screen, (255, 255, 0), rect, 3)  # highlight
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 1)
        # number key
        num = font.render(str(i+1), True, (255, 255, 255))
        screen.blit(num, (rect[0]+2, rect[1]+2))

    # Inventory panel (toggle I)
    if me.show_inventory:
        inv_surf = pygame.Surface((250, 350))
        inv_surf.set_alpha(200)
        inv_surf.fill((50, 50, 50))
        screen.blit(inv_surf, (SCREEN_W-270, 100))
        title = font_big.render("Inventory", True, (255, 215, 0))
        screen.blit(title, (SCREEN_W-260, 105))
        y = 140
        for item in inventory[:15]:
            txt = font.render(item, True, (255, 255, 255))
            screen.blit(txt, (SCREEN_W-260, y))
            y += 20

    # Spellbook panel (toggle S)
    if me.show_spellbook:
        spell_surf = pygame.Surface((200, 200))
        spell_surf.set_alpha(200)
        spell_surf.fill((70, 0, 70))
        screen.blit(spell_surf, (SCREEN_W-220, 420))
        title = font_big.render("Spellbook", True, (200, 200, 0))
        screen.blit(title, (SCREEN_W-210, 425))
        y = 455
        for i, spell in enumerate(me.grimoire.truques):
            color = (0, 255, 0) if i == me.selected_spell_index else (
                255, 255, 255)
            txt = font.render(f"{i+1}. {spell.nome}", True, color)
            screen.blit(txt, (SCREEN_W-210, y))
            y += 20

    # Stats panel (toggle C)
    if me.show_stats and my_stats:
        stat_surf = pygame.Surface((200, 150))
        stat_surf.set_alpha(200)
        stat_surf.fill((20, 20, 80))
        screen.blit(stat_surf, (10, 140))
        title = font_big.render("Stats", True, (255, 255, 0))
        screen.blit(title, (15, 145))
        y = 170
        for key in ["str", "int", "agi"]:
            val = my_stats.get(key, 0)
            txt = font.render(f"{key.upper()}: {val}", True, (200, 200, 255))
            screen.blit(txt, (15, y))
            y += 20

    # Minimap (toggle M)
    if me.show_minimap:
        map_size = 150
        mm_surf = pygame.Surface((map_size, map_size))
        mm_surf.set_alpha(180)
        mm_surf.fill((30, 30, 30))
        # Draw dots for players, mobs, npcs
        scale = map_size / 2000.0  # world size 2000
        # self
        px = int(me.x * scale)
        py = int(me.y * scale)
        pygame.draw.circle(mm_surf, (0, 255, 0), (px, py), 3)
        # other players
        for pid, p in players.items():
            if pid != my_id:
                px = int(p["x"] * scale)
                py = int(p["y"] * scale)
                pygame.draw.circle(mm_surf, (255, 255, 255), (px, py), 2)
        # mobs
        for m in mobs.values():
            px = int(m["x"] * scale)
            py = int(m["y"] * scale)
            pygame.draw.circle(mm_surf, (255, 0, 0), (px, py), 2)
        # npcs
        for n in npcs.values():
            px = int(n["x"] * scale)
            py = int(n["y"] * scale)
            pygame.draw.circle(mm_surf, (0, 255, 255), (px, py), 3)
        screen.blit(mm_surf, (SCREEN_W - map_size - 10, 10))

    # Quest log (left top)
    quest_surf = pygame.Surface((250, 120))
    quest_surf.set_alpha(200)
    quest_surf.fill((20, 20, 20))
    screen.blit(quest_surf, (10, 10))
    q_title = font_big.render("Quests", True, (255, 215, 0))
    screen.blit(q_title, (15, 15))
    if my_stats:
        kills = my_stats.get("quest_slime", 0)
        q1 = font.render(f"Slime Hunt: {kills}/20", True, (200, 200, 200))
        screen.blit(q1, (15, 45))
        kills2 = my_stats.get("quest_goblin", 0)
        q2 = font.render(f"Goblin Slayer: {kills2}/10", True, (200, 200, 200))
        screen.blit(q2, (15, 65))
        xp_text = font.render(
            f"XP: {my_stats.get('xp', 0)}/100", True, (100, 255, 100))
        screen.blit(xp_text, (15, 90))

# =====================
# PARTICLE EFFECTS
# =====================


def draw_effects(screen, me, camera):
    now = time.time()
    for fx in me.effects[:]:
        x, y, typ, t0 = fx
        if now - t0 > 1.0:
            me.effects.remove(fx)
            continue
        sx = x - camera.x
        sy = y - camera.y
        alpha = int(255 * (1 - (now - t0)))
        if typ == "Fireball":
            color = (255, 100, 0, alpha)
        elif typ == "Heal":
            color = (0, 255, 100, alpha)
        else:
            color = (255, 255, 0, alpha)
        # Draw expanding circle
        radius = int(20 * (now - t0) * 3)
        surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color[:3] +
                           (alpha,), (radius, radius), radius, 2)
        screen.blit(surf, (sx-radius, sy-radius))


# =====================
# MAIN LOOP
# =====================
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Ultimate Magic MMORPG")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)
font_big = pygame.font.SysFont("Arial", 20, bold=True)

me = LocalPlayer()
camera = Camera()

# Request initial sync
send_json({"type": "LOGIN", "name": f"Hero{random.randint(100, 999)}"})

running = True
while running:
    clock.tick(60)
    running = me.handle_input()
    camera.update(me)

    # Draw world
    screen.fill((100, 150, 100))

    # Determine visible tile range
    start_col = int(camera.x // 50) - 2
    end_col = int((camera.x + SCREEN_W) // 50) + 2
    start_row = int(camera.y // 50) - 2
    end_row = int((camera.y + SCREEN_H) // 50) + 2

    if world_seed != 0:
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                terrain = get_terrain_at(c, r, world_seed)
                rect = (c * 50 - camera.x, r * 50 - camera.y, 50, 50)

                if terrain == "WATER":
                    pygame.draw.rect(screen, (0, 100, 200), rect)
                elif terrain == "SAND":
                    pygame.draw.rect(screen, (240, 230, 140), rect)
                elif terrain == "GRASS":
                    pygame.draw.rect(screen, (34, 139, 34), rect)
                elif terrain == "FOREST":
                    pygame.draw.rect(screen, (0, 80, 0), rect)
                    pygame.draw.circle(screen, (0, 60, 0),
                                       (rect[0]+25, rect[1]+25), 15)
                elif terrain == "MOUNTAIN":
                    pygame.draw.rect(screen, (128, 128, 128), rect)
                    pygame.draw.polygon(screen, (80, 80, 80), [
                                        (rect[0], rect[1]+50), (rect[0]+25, rect[1]), (rect[0]+50, rect[1]+50)])

    # Draw ground items
    for iid, item in ground_items.items():
        sx = item["x"] - camera.x
        sy = item["y"] - camera.y
        if -20 < sx < SCREEN_W and -20 < sy < SCREEN_H:
            # gold or item
            if "gold" in item["name"].lower():
                color = (255, 215, 0)
            else:
                color = (200, 100, 255)
            pygame.draw.circle(screen, color, (sx, sy), 8)
            name = item["name"][:1].upper()
            txt = font.render(name, True, (0, 0, 0))
            screen.blit(txt, (sx-3, sy-6))

    # Draw mobs
    for mid, m in mobs.items():
        sx = m["x"] - camera.x
        sy = m["y"] - camera.y
        if -50 < sx < SCREEN_W and -50 < sy < SCREEN_H:
            if m.get("type") == "Slime":
                color = (200, 0, 200)
            elif m.get("type") == "Goblin":
                color = (0, 200, 0)
            elif m.get("type") == "Dragon":
                color = (200, 100, 0)
            else:
                color = (150, 150, 150)
            pygame.draw.circle(screen, color, (sx, sy), 15)
            # HP bar
            hp_ratio = m["hp"] / m.get("max_hp", 30)
            pygame.draw.rect(screen, (255, 0, 0), (sx-15, sy-25, 30, 5))
            pygame.draw.rect(screen, (0, 255, 0),
                             (sx-15, sy-25, 30 * hp_ratio, 5))
            # level
            lvl = m.get("level", 1)
            lvl_txt = font.render(str(lvl), True, (255, 255, 255))
            screen.blit(lvl_txt, (sx-5, sy-35))

    # Draw NPCs
    for nid, npc in npcs.items():
        sx = npc["x"] - camera.x
        sy = npc["y"] - camera.y
        if -50 < sx < SCREEN_W and -50 < sy < SCREEN_H:
            pygame.draw.circle(screen, (0, 255, 255), (sx, sy), 20)
            name = font.render(npc.get("name", "NPC"), True, (255, 255, 255))
            screen.blit(name, (sx-20, sy-30))
            # speech bubble if nearby? maybe later

    # Draw players
    my_stats = None
    for pid, p in players.items():
        is_me = abs(p["x"] - me.x) < 2 and abs(p["y"] - me.y) < 2
        if is_me:
            my_stats = p
            my_id = pid

        sx = p["x"] - camera.x
        sy = p["y"] - camera.y

        base_color = p.get("color", (255, 255, 255))
        pygame.draw.rect(screen, base_color, (sx-20, sy-20, 40, 40))
        name = p.get("name", "Unknown")
        name_lbl = font.render(name, True, (255, 255, 255))
        screen.blit(name_lbl, (sx-20, sy-45))
        # HP bar
        hp_pct = p["hp"] / p["max_hp"]
        pygame.draw.rect(screen, (255, 0, 0), (sx-20, sy+25, 40, 5))
        pygame.draw.rect(screen, (0, 255, 0), (sx-20, sy+25, 40 * hp_pct, 5))

    # Draw particle effects
    draw_effects(screen, me, camera)

    # UI
    draw_ui(screen, me, my_stats)

    pygame.display.flip()

pygame.quit()
