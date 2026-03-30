"""
PyRPG Classic - Multiplayer with LAN discovery

This single-file pygame game adds LAN discovery so clients can find hosts automatically.

How it works:
- Host: when you press H on title, the game starts a TCP host (same as before) and also
  starts a UDP discovery responder on DISCOVERY_PORT. The responder replies to discovery
  requests with a small JSON message containing host IP and TCP port.
- Client: pressing C on the title starts a short LAN scan. The game broadcasts a UDP
  discovery packet and listens for replies for SCAN_TIMEOUT seconds. Found hosts are
  displayed; press the corresponding number key to connect to that host.

Notes:
- Discovery uses UDP broadcast and relies on local network allowing broadcasts.
- If discovery fails across subnets, you can still connect manually by changing
  CONNECT_IP or by entering a UI prompt (I can add that on request).

Run: pip install pygame
Then: python python_rpg.py
"""

import pygame
import random
import sys
import json
import socket
import threading
import time
from queue import Queue, Empty
from dataclasses import dataclass, field

# ---- Config ----
SCREEN_W, SCREEN_H = 900, 640
TILE = 48
MAP_W, MAP_H = 16, 11
FPS = 60

# Networking
HOST_PORT = 50007
DISCOVERY_PORT = 50008
SCAN_TIMEOUT = 1.5  # seconds to wait for discovery replies
CONNECT_IP = '127.0.0.1'  # default if manual connect

WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
BLUE, RED, GOLD = (60, 100, 200), (200, 60, 60), (230, 190, 60)

pygame.init()
FONT = pygame.font.SysFont('consolas', 18)
BIGFONT = pygame.font.SysFont('consolas', 36)
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption('PyRPG Classic - LAN Discovery')
clock = pygame.time.Clock()

# particle surface
particle_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

# ---- Data Classes ----


@dataclass
class Player:
    name: str = 'Hero'
    x: int = MAP_W // 2
    y: int = MAP_H // 2
    hp: int = 30
    max_hp: int = 30
    atk: int = 6
    defense: int = 2
    level: int = 1
    xp: int = 0
    xp_to_next: int = 20
    gold: int = 20
    inventory: dict = field(default_factory=lambda: {'Potion': 3, 'Elixir': 1})

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level_up()

    def level_up(self):
        self.level += 1
        self.max_hp += 6
        self.hp = self.max_hp
        self.atk += 2
        self.defense += 1
        self.xp_to_next = int(self.xp_to_next * 1.5)


@dataclass
class Enemy:
    name: str
    hp: int
    max_hp: int
    atk: int
    defense: int
    xp_reward: int
    gold_reward: int


# ---- Enemy Factory ----
ENEMY_POOL = [
    lambda: Enemy('Slime', 10, 10, 3, 0, 8, 5),
    lambda: Enemy('Wolf', 14, 14, 5, 1, 12, 10),
    lambda: Enemy('Bandit', 18, 18, 7, 2, 18, 15),
    lambda: Enemy('Goblin', 22, 22, 8, 3, 25, 20),
]


def spawn_enemy(level):
    e = random.choice(ENEMY_POOL)()
    e.max_hp += level * 2
    e.hp = e.max_hp
    e.atk += level
    e.defense += max(0, level // 2)
    e.xp_reward += level * 5
    e.gold_reward += level * 3
    return e

# ---- Map ----


def generate_map():
    tiles = [[0 for _ in range(MAP_W)] for _ in range(MAP_H)]
    for y in range(MAP_H):
        for x in range(MAP_W):
            r = random.random()
            if r < 0.08:
                tiles[y][x] = 1  # tree
            elif r < 0.1:
                tiles[y][x] = 2  # water
    return tiles

# ---- Helper ----


def draw_text(surf, text, x, y, color=BLACK, font=FONT):
    surf.blit(font.render(str(text), True, color), (x, y))

# procedural 'sprite' animation helper


def draw_player_sprite(surf, x, y, color, tick, size=28):
    bob = int((tick % 30) / 6) - 2
    rect = pygame.Rect(x - size//2, y - size//2 + bob, size, size)
    pygame.draw.rect(surf, color, rect)
    eye_w = max(2, size//8)
    pygame.draw.rect(surf, BLACK, (rect.x + size//6,
                     rect.y + size//4, eye_w, eye_w))
    pygame.draw.rect(surf, BLACK, (rect.x + size*4//6,
                     rect.y + size//4, eye_w, eye_w))

# particle system


class Particle:
    def __init__(self, x, y, vx, vy, life, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.color = color

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surf):
        if self.life > 0:
            alpha = max(0, int(255 * (self.life / 1.0)))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            s.fill((*self.color, alpha))
            surf.blit(s, (int(self.x), int(self.y)))


particles = []

# ---- States ----
STATE_TITLE = 'title'
STATE_OVERWORLD = 'overworld'
STATE_BATTLE = 'battle'
STATE_GAMEOVER = 'gameover'
STATE_SHOP = 'shop'
STATE_SCAN = 'scan'

# ---- Game Class ----


class Game:
    def __init__(self):
        self.state = STATE_TITLE
        self.map = generate_map()
        self.player = Player()
        self.other_player = None
        self.message = ''
        self.battle_enemy = None
        self.battle_log = []
        self.battle_turn = 'player'
        self.player_defending = False

        # Networking
        self.net_mode = None  # 'host' or 'client' or None
        self.net_thread = None
        self.net_queue = Queue()
        self.net_sock = None
        self.client_conn = None
        self.client_addr = None
        self.connected = False

        # discovery
        self.scan_results = []  # list of dicts {'ip','port','name'}
        self.scanning = False

        # tick for animation
        self.tick = 0

    def new_game(self):
        self.map = generate_map()
        self.player = Player()
        self.state = STATE_OVERWORLD
        self.message = 'Adventure begins!'

    def attempt_move(self, dx, dy):
        nx, ny = self.player.x + dx, self.player.y + dy
        if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
            if self.map[ny][nx] == 1:
                self.message = 'A tree blocks your path.'
                return
            self.player.x, self.player.y = nx, ny
            if random.random() < 0.15:
                self.start_battle()
            elif random.random() < 0.05:
                self.enter_shop()

    def start_battle(self):
        self.battle_enemy = spawn_enemy(self.player.level)
        self.state = STATE_BATTLE
        self.battle_log = [f'A wild {self.battle_enemy.name} appears!']
        self.battle_turn = 'player'
        self.player_defending = False

    def enter_shop(self):
        self.state = STATE_SHOP
        self.message = 'Welcome to the Shop!'

    def save_game(self):
        try:
            with open('savegame.json', 'w') as f:
                json.dump({'player': self.player.__dict__, 'map': self.map}, f)
            self.message = 'Game saved.'
        except Exception as e:
            self.message = f'Save failed: {e}'

    def load_game(self):
        try:
            with open('savegame.json', 'r') as f:
                data = json.load(f)
            self.player = Player(**data['player'])
            self.map = data['map']
            self.state = STATE_OVERWORLD
            self.message = 'Game loaded.'
        except Exception as e:
            self.message = f'Load failed: {e}'

    # ---- Battle Actions ----
    def player_attack(self):
        e = self.battle_enemy
        dmg = max(1, self.player.atk - e.defense + random.randint(-2, 2))
        e.hp -= dmg
        self.battle_log.append(f'You dealt {dmg} damage!')
        if e.hp <= 0:
            self.battle_log.append(f'You defeated {e.name}!')
            self.player.gain_xp(e.xp_reward)
            self.player.gold += e.gold_reward
            self.state = STATE_OVERWORLD
            self.message = f'Gained {e.xp_reward} XP and {e.gold_reward} gold!'
        else:
            self.battle_turn = 'enemy'

    def player_defend(self):
        self.player_defending = True
        self.battle_log.append('You brace for the attack.')
        self.battle_turn = 'enemy'

    def player_item(self, item='Potion'):
        if item == 'Potion' and self.player.inventory.get('Potion', 0) > 0:
            self.player.inventory['Potion'] -= 1
            heal = min(12, self.player.max_hp - self.player.hp)
            self.player.hp += heal
            self.battle_log.append(f'Used Potion! Healed {heal} HP.')
        elif item == 'Elixir' and self.player.inventory.get('Elixir', 0) > 0:
            self.player.inventory['Elixir'] -= 1
            self.player.hp = self.player.max_hp
            self.battle_log.append('Used Elixir! HP fully restored.')
        else:
            self.battle_log.append('You have none left!')
        self.battle_turn = 'enemy'

    def player_run(self):
        if random.random() < 0.6:
            self.battle_log.append('You escaped safely!')
            self.state = STATE_OVERWORLD
        else:
            self.battle_log.append('Failed to escape!')
            self.battle_turn = 'enemy'

    def enemy_turn(self):
        e = self.battle_enemy
        dmg = max(1, e.atk - self.player.defense + random.randint(-2, 2))
        if self.player_defending:
            dmg //= 2
        self.player.hp -= dmg
        self.battle_log.append(f'{e.name} hit you for {dmg} damage!')
        self.player_defending = False
        if self.player.hp <= 0:
            self.state = STATE_GAMEOVER
            self.battle_log.append('You were defeated...')
        else:
            self.battle_turn = 'player'

    # ---- Networking: host/client (TCP) and discovery (UDP) ----
    def host_game(self, port=HOST_PORT):
        if self.net_mode:
            self.message = 'Already in network mode.'
            return
        self.net_mode = 'host'
        # start UDP discovery responder
        t = threading.Thread(target=self._discovery_responder, daemon=True)
        t.start()
        # start TCP host thread
        t2 = threading.Thread(target=self._host_thread,
                              args=(port,), daemon=True)
        t2.start()
        self.net_thread = (t, t2)
        self.message = f'Hosting on port {port}...'

    def _discovery_responder(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('0.0.0.0', DISCOVERY_PORT))
        except Exception:
            try:
                s.bind(('', DISCOVERY_PORT))
            except Exception:
                return
        s.settimeout(0.5)
        while self.net_mode == 'host':
            try:
                data, addr = s.recvfrom(1024)
                if not data:
                    continue
                if data.strip() == b'PYRPG_DISCOVER':
                    resp = json.dumps(
                        {'name': 'PyRPG Host', 'port': HOST_PORT}).encode()
                    s.sendto(resp, addr)
            except socket.timeout:
                continue
            except Exception:
                break
        try:
            s.close()
        except:
            pass

    def _host_thread(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('0.0.0.0', port))
            s.listen(1)
            s.settimeout(0.5)
            self.net_sock = s
            while self.net_mode == 'host':
                try:
                    conn, addr = s.accept()
                    conn.settimeout(0.2)
                    self.client_conn = conn
                    self.client_addr = addr
                    self.connected = True
                    self.message = f'Client connected: {addr[0]}'
                    # send initial state
                    self._send_state(conn)
                    while self.net_mode == 'host':
                        try:
                            data = conn.recv(4096)
                            if not data:
                                break
                            for raw in data.split(b'\n'):
                                if not raw:
                                    continue
                                try:
                                    obj = json.loads(raw.decode())
                                    self.net_queue.put(('client_input', obj))
                                except Exception:
                                    pass
                        except socket.timeout:
                            # send periodic state updates
                            self._send_state(conn)
                        except Exception:
                            break
                    break
                except socket.timeout:
                    continue
        finally:
            try:
                s.close()
            except:
                pass
            self.connected = False
            self.net_mode = None
            self.message = 'Host closed.'

    def _send_state(self, conn):
        payload = {'type': 'host_state', 'player': self.player.__dict__, 'other': (
            self.other_player.__dict__ if self.other_player else None), 'map': self.map}
        try:
            conn.sendall((json.dumps(payload) + '\n').encode())
        except Exception:
            pass

    def connect_game(self, host_ip=CONNECT_IP, port=HOST_PORT):
        if self.net_mode:
            self.message = 'Already in network mode.'
            return
        self.net_mode = 'client'
        t = threading.Thread(target=self._client_thread,
                             args=(host_ip, port), daemon=True)
        t.start()
        self.net_thread = t
        self.message = f'Connecting to {host_ip}:{port}...'

    def _client_thread(self, host_ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.0)
        try:
            s.connect((host_ip, port))
            self.net_sock = s
            self.connected = True
            self.message = f'Connected to {host_ip}:{port}'
            s.settimeout(0.2)
            while self.net_mode == 'client':
                try:
                    # send local state
                    msg = json.dumps(
                        {'type': 'state_update', 'player': self.player.__dict__}).encode() + b'\n'
                    s.sendall(msg)
                except Exception:
                    break
                try:
                    data = s.recv(8192)
                    if not data:
                        break
                    for raw in data.split(b'\n'):
                        if not raw:
                            continue
                        try:
                            obj = json.loads(raw.decode())
                            self.net_queue.put(('host_state', obj))
                        except Exception:
                            pass
                except socket.timeout:
                    pass
                time.sleep(0.25)
        except Exception as e:
            self.message = f'Connection failed: {e}'
        finally:
            try:
                s.close()
            except:
                pass
            self.connected = False
            self.net_mode = None
            self.message = 'Disconnected.'

    def process_network_queue(self):
        try:
            while True:
                typ, obj = self.net_queue.get_nowait()
                if typ == 'client_input' and self.net_mode == 'host':
                    p = obj.get('player')
                    if p:
                        self.other_player = Player(**p)
                elif typ == 'host_state' and self.net_mode == 'client':
                    pl = obj.get('player')
                    other = obj.get('other')
                    if pl:
                        self.other_player = Player(**pl)
                    if other:
                        self.player = Player(**other)
                    if 'map' in obj:
                        self.map = obj['map']
                self.net_queue.task_done()
        except Empty:
            pass

    # ---- Discovery: client-side scan ----
    def scan_network(self, timeout=SCAN_TIMEOUT):
        if self.scanning:
            return
        self.scanning = True
        self.scan_results = []

        def _scan():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(timeout)
            msg = b'PYRPG_DISCOVER'
            # send broadcast
            try:
                s.sendto(msg, ('<broadcast>', DISCOVERY_PORT))
                s.sendto(msg, ('255.255.255.255', DISCOVERY_PORT))
            except Exception:
                pass
            start = time.time()
            seen = set()
            while time.time() - start < timeout:
                try:
                    data, addr = s.recvfrom(1024)
                    if not data:
                        continue
                    try:
                        info = json.loads(data.decode())
                        ip = addr[0]
                        port = info.get('port', HOST_PORT)
                        name = info.get('name', 'PyRPG Host')
                        key = f'{ip}:{port}'
                        if key not in seen:
                            seen.add(key)
                            self.scan_results.append(
                                {'ip': ip, 'port': port, 'name': name})
                    except Exception:
                        continue
                except socket.timeout:
                    continue
                except Exception:
                    break
            try:
                s.close()
            except:
                pass
            self.scanning = False
        threading.Thread(target=_scan, daemon=True).start()

# ---- Drawing ----


def draw_title():
    screen.fill((20, 24, 48))
    draw_text(screen, '★ PyRPG Classic ★ (LAN Discovery)', SCREEN_W //
              2 - 260, SCREEN_H//2 - 120, color=GOLD, font=BIGFONT)
    draw_text(screen, 'N - New | L - Load | Q - Quit',
              SCREEN_W//2 - 140, SCREEN_H//2 - 20, color=WHITE)
    draw_text(screen, 'H - Host  |  C - Scan & Connect',
              SCREEN_W//2 - 170, SCREEN_H//2 + 10, color=WHITE)
    draw_text(screen, 'Tip: Hosts on your LAN will respond to the scan.',
              SCREEN_W//2 - 250, SCREEN_H//2 + 40, color=WHITE)


def draw_overworld(g: Game):
    screen.fill((120, 200, 120))
    start_x = (SCREEN_W - MAP_W * TILE)//2
    start_y = (SCREEN_H - MAP_H * TILE)//2
    for y in range(MAP_H):
        for x in range(MAP_W):
            rect = pygame.Rect(start_x + x*TILE, start_y + y*TILE, TILE, TILE)
            color = (165, 214, 167) if g.map[y][x] == 0 else (
                90, 60, 20) if g.map[y][x] == 1 else (60, 100, 180)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)
    px = start_x + g.player.x*TILE + TILE//2
    py = start_y + g.player.y*TILE + TILE//2
    draw_player_sprite(screen, px, py, GOLD, g.tick, size=32)
    if g.other_player:
        opx = start_x + g.other_player.x*TILE + TILE//2
        opy = start_y + g.other_player.y*TILE + TILE//2
        draw_player_sprite(screen, opx, opy, BLUE, g.tick, size=28)
    draw_text(
        screen, f'HP: {g.player.hp}/{g.player.max_hp}  LVL: {g.player.level}', 10, 10)
    draw_text(
        screen, f'Gold: {g.player.gold}  Potions: {g.player.inventory.get("Potion", 0)}  Elixirs: {g.player.inventory.get("Elixir", 0)}', 10, 30)
    draw_text(screen, g.message, 10, SCREEN_H - 30)
    netst = f'NET: {g.net_mode or "local"} {"(connected)" if g.connected else ""}'
    draw_text(screen, netst, SCREEN_W - 320, 10)


def draw_battle(g: Game):
    screen.fill((40, 30, 60))
    e = g.battle_enemy
    draw_text(screen, f'{e.name}  HP: {e.hp}/{e.max_hp}', 40, 40, color=WHITE)
    draw_text(
        screen, f'You  HP: {g.player.hp}/{g.player.max_hp}', 40, 100, color=WHITE)
    draw_text(screen, 'A-Attack  D-Defend  P-Potion  E-Elixir  R-Run',
              40, 160, color=WHITE)
    for i, line in enumerate(g.battle_log[-6:]):
        draw_text(screen, line, 40, 220 + i*24, color=WHITE)


def draw_shop(g: Game):
    screen.fill((80, 60, 40))
    draw_text(screen, 'Welcome to the Shop!', 60, 40, color=WHITE)
    draw_text(screen, 'B - Buy Potion (10g)  E - Buy Elixir (25g)',
              60, 80, color=WHITE)
    draw_text(screen, 'Q - Exit Shop', 60, 120, color=WHITE)
    draw_text(screen, f'Gold: {g.player.gold}', 60, 160, color=WHITE)


def draw_scan(g: Game):
    screen.fill((30, 30, 30))
    draw_text(screen, 'Scan Results - Press number to connect, R to rescan, Q to cancel',
              40, 30, color=WHITE)
    if g.scanning:
        draw_text(screen, 'Scanning on LAN... please wait',
                  40, 60, color=WHITE)
    for i, h in enumerate(g.scan_results):
        draw_text(
            screen, f'{i+1}. {h["name"]} @ {h["ip"]}:{h["port"]}', 40, 100 + i*30, color=WHITE)
    if not g.scan_results and not g.scanning:
        draw_text(
            screen, 'No hosts found. Press R to scan again or Q to cancel.', 40, 100, color=WHITE)


def draw_gameover():
    screen.fill((0, 0, 0))
    draw_text(screen, 'GAME OVER', SCREEN_W//2 - 80,
              SCREEN_H//2 - 40, color=WHITE, font=BIGFONT)
    draw_text(screen, 'Press N for New Game or Q to Quit',
              SCREEN_W//2 - 180, SCREEN_H//2 + 20, color=WHITE)

# ---- Main ----


def main():
    g = Game()
    while True:
        g.tick += 1
        g.process_network_queue()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                k = e.key
                if k == pygame.K_q:
                    # if scanning, cancel scan
                    if g.state == STATE_SCAN and g.scanning:
                        g.scanning = False
                    else:
                        pygame.quit()
                        sys.exit()

                if g.state == STATE_TITLE:
                    if k == pygame.K_n:
                        g.new_game()
                    elif k == pygame.K_l:
                        g.load_game()
                    elif k == pygame.K_h:
                        g.host_game()
                    elif k == pygame.K_c:
                        g.state = STATE_SCAN
                        g.scan_network()

                elif g.state == STATE_SCAN:
                    if k == pygame.K_r:
                        g.scan_results = []
                        g.scan_network()
                    elif k == pygame.K_q:
                        g.state = STATE_TITLE
                    else:
                        # number keys 1-9 for selection
                        if k >= pygame.K_1 and k <= pygame.K_9:
                            idx = k - pygame.K_1
                            if 0 <= idx < len(g.scan_results):
                                target = g.scan_results[idx]
                                g.connect_game(
                                    host_ip=target['ip'], port=target['port'])
                                g.state = STATE_OVERWORLD

                elif g.state == STATE_OVERWORLD:
                    if k == pygame.K_s:
                        g.save_game()
                    elif k == pygame.K_i:
                        g.enter_shop()
                    elif k == pygame.K_LEFT:
                        g.attempt_move(-1, 0)
                    elif k == pygame.K_RIGHT:
                        g.attempt_move(1, 0)
                    elif k == pygame.K_UP:
                        g.attempt_move(0, -1)
                    elif k == pygame.K_DOWN:
                        g.attempt_move(0, 1)
                    if g.net_mode == 'host' and g.client_conn:
                        try:
                            g._send_state(g.client_conn)
                        except:
                            pass

                elif g.state == STATE_BATTLE and g.battle_enemy:
                    if g.battle_turn == 'player':
                        if k == pygame.K_a:
                            cx = SCREEN_W//2
                            cy = SCREEN_H//2
                            for i in range(12):
                                particles.append(
                                    Particle(cx, cy, random.uniform(-60, 60), random.uniform(-120, -20), 1.0, RED))
                            g.player_attack()
                        elif k == pygame.K_d:
                            g.player_defend()
                        elif k == pygame.K_p:
                            g.player_item('Potion')
                        elif k == pygame.K_e:
                            g.player_item('Elixir')
                        elif k == pygame.K_r:
                            g.player_run()

                elif g.state == STATE_SHOP:
                    if k == pygame.K_b:
                        if g.player.gold >= 10:
                            g.player.gold -= 10
                            g.player.inventory['Potion'] = g.player.inventory.get(
                                'Potion', 0) + 1
                            g.message = 'Bought a Potion!'
                        else:
                            g.message = 'Not enough gold!'
                    elif k == pygame.K_e:
                        if g.player.gold >= 25:
                            g.player.gold -= 25
                            g.player.inventory['Elixir'] = g.player.inventory.get(
                                'Elixir', 0) + 1
                            g.message = 'Bought an Elixir!'
                        else:
                            g.message = 'Not enough gold!'
                    elif k == pygame.K_q:
                        g.state = STATE_OVERWORLD

                elif g.state == STATE_GAMEOVER:
                    if k == pygame.K_n:
                        g.new_game()

        # update particles
        dt = clock.get_time() / 1000.0
        for p in particles[:]:
            p.update(dt)
            if p.life <= 0:
                particles.remove(p)

        # enemy turn
        if g.state == STATE_BATTLE and g.battle_enemy and g.battle_turn == 'enemy':
            g.enemy_turn()

        # draw
        if g.state == STATE_TITLE:
            draw_title()
        elif g.state == STATE_SCAN:
            draw_scan(g)
        elif g.state == STATE_OVERWORLD:
            draw_overworld(g)
        elif g.state == STATE_BATTLE:
            draw_battle(g)
        elif g.state == STATE_SHOP:
            draw_shop(g)
        elif g.state == STATE_GAMEOVER:
            draw_gameover()

        # draw particles
        for p in particles:
            p.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
