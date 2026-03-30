"""
Socos Na Cristina - All-in-One LAN Edition
Features in this single file:
- Local split/full screen co-op
- 2-player LAN (host + client) with host discovery (UDP beacons)
- Host prompt: server name + port (default 50007)
- Persistent username and friends saved to player_config.json
- Friend list showing "username - IP - ping"
- Chat (press T) showing last 8 messages (white text)
- Shooting and death sound effects (shoot.wav, death.wav) if present
- Optimized simple game loop, capped particles

Run: python socos_na_cristina_lan.py
Place optional shoot.wav and death.wav in same folder.
"""

import os
import sys
import json
import time
import math
import random
import socket
import threading
from collections import deque

import pygame
from pygame.locals import *

# ------------------ Config / Persistence ------------------
CONFIG_FILE = 'player_config.json'
DEFAULT_PORT = 50007
MAX_CHAT = 8
BEACON_INTERVAL = 1.0  # seconds
DISCOVERY_TIMEOUT = 5.0  # seconds
NETWORK_TICK = 0.06

WORLD_W, WORLD_H = 2000, 1200
SCREEN_W, SCREEN_H = 1200, 700
FPS = 60

PLAYER_SPEED = 300
BULLET_SPEED = 900
BULLET_LIFETIME = 1.5
ZOMBIE_SPEED = 90
ZOMBIE_SPAWN = 2.5

# ------------------ Helper Utilities ------------------


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'username': None,
        'friends': [],
        'last_port': DEFAULT_PORT
    }


def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf8') as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print('Failed to save config:', e)


def clamp(v, a, b):
    return max(a, min(b, v))


# ------------------ Networking: Discovery & Game Sync ------------------
class DiscoveryListener(threading.Thread):
    """Listens for UDP beacon broadcasts and keeps a list of discovered hosts."""

    def __init__(self, listen_port=DEFAULT_PORT):
        super().__init__(daemon=True)
        self.listen_port = listen_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.bind(('', listen_port))
        except Exception:
            # bind to random port if failed
            self.sock.bind(('', 0))
        self.sock.settimeout(0.5)
        self.running = True
        # key: (ip,port) -> {name, host, port, last_seen, ping_ms}
        self.discovered = {}

    def run(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except Exception:
                break
            try:
                payload = json.loads(data.decode('utf8', 'ignore'))
            except Exception:
                continue
            if payload.get('type') != 'beacon':
                continue
            now = time.time()
            ip = addr[0]
            port = payload.get('port', self.listen_port)
            key = (ip, port)
            # compute ping approx using timestamp in beacon if provided
            ts = payload.get('t')
            ping = None
            if ts:
                ping = max(0, int((now - ts) * 1000))
            self.discovered[key] = {
                'server': payload.get('name', 'Unnamed'),
                'host': payload.get('host', 'Unknown'),
                'ip': ip,
                'port': port,
                'last_seen': now,
                'ping': ping
            }
            # prune old
            to_del = []
            for k, v in list(self.discovered.items()):
                if now - v['last_seen'] > DISCOVERY_TIMEOUT:
                    to_del.append(k)
            for k in to_del:
                del self.discovered[k]

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass


class BeaconBroadcaster(threading.Thread):
    """Broadcasts beacon messages periodically (host)."""

    def __init__(self, server_name, host_name, port=DEFAULT_PORT, interval=BEACON_INTERVAL):
        super().__init__(daemon=True)
        self.server_name = server_name
        self.host_name = host_name
        self.port = port
        self.interval = interval
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def run(self):
        while self.running:
            payload = json.dumps({
                'type': 'beacon',
                'name': self.server_name,
                'host': self.host_name,
                'port': self.port,
                't': time.time()
            }).encode('utf8')
            try:
                self.sock.sendto(payload, ('<broadcast>', self.port))
            except Exception:
                pass
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass


class GameNet(threading.Thread):
    """Handles UDP messages for game state and chat between host and single client."""

    def __init__(self, is_host, local_player_id, host_ip=None, port=DEFAULT_PORT):
        super().__init__(daemon=True)
        self.is_host = is_host
        self.port = port
        self.host_ip = host_ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.05)
        if is_host:
            try:
                self.sock.bind(('', port))
            except Exception:
                self.sock.bind(('', 0))
        else:
            # client binds ephemeral
            try:
                self.sock.bind(('', 0))
            except Exception:
                pass
        self.peer = None
        self.running = True
        self.incoming = deque()  # (msg_dict, addr)

    def send(self, data):
        b = json.dumps(data).encode('utf8')
        try:
            if self.is_host:
                if self.peer:
                    self.sock.sendto(b, self.peer)
            else:
                if self.host_ip:
                    self.sock.sendto(b, (self.host_ip, self.port))
        except Exception:
            pass

    def run(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(8192)
            except socket.timeout:
                continue
            except Exception:
                break
            try:
                msg = json.loads(data.decode('utf8', 'ignore'))
            except Exception:
                continue
            # if host, set peer
            if self.is_host and not self.peer:
                self.peer = addr
            # queue incoming
            self.incoming.append((msg, addr))

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass


# ------------------ Game Entities ------------------
class Bullet:
    def __init__(self, pos, vel, owner):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.owner = owner
        self.spawn = time.time()

    def update(self, dt):
        self.pos += self.vel * dt
        if time.time() - self.spawn > BULLET_LIFETIME:
            return False
        if not (0 <= self.pos.x <= WORLD_W and 0 <= self.pos.y <= WORLD_H):
            return False
        return True


class Player:
    def __init__(self, x, y, color, uname, pid):
        self.pos = pygame.Vector2(x, y)
        self.color = color
        self.uname = uname
        self.pid = pid
        self.health = 5
        self.alive = True
        self.last_dir = pygame.Vector2(0, -1)
        self.score = 0

    def take_damage(self, d=1):
        if not self.alive:
            return False
        self.health -= d
        if self.health <= 0:
            self.health = 0
            self.alive = False
            return True
        return False


class Zombie:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.health = 2

    def update(self, dt, players):
        alive = [p for p in players if p.alive]
        if not alive:
            return
        nearest = min(alive, key=lambda p: (p.pos - self.pos).length_squared())
        dir = (nearest.pos - self.pos)
        if dir.length_squared() > 0.01:
            self.pos += dir.normalize() * ZOMBIE_SPEED * dt


# ------------------ Main Game ------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption('Socos Na Cristina - LAN Edition')
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 24)
    big = pygame.font.Font(None, 48)

    # load config
    cfg = load_config()
    if not cfg.get('username'):
        cfg['username'] = prompt_username(screen, font)
        save_config(cfg)
    username = cfg['username']

    # load sounds
    shoot_sfx = load_sound('shoot.wav')
    death_sfx = load_sound('death.wav')

    # discovery listener
    discovery = DiscoveryListener(
        listen_port=cfg.get('last_port', DEFAULT_PORT))
    discovery.start()

    # game state
    STATE_MENU = 0
    STATE_PLAY = 1
    STATE_PAUSED = 2
    STATE_GAMEOVER = 3

    state = STATE_MENU
    menu_idx = 0
    menu_items = ['Local Co-op', 'LAN Host', 'LAN Join', 'Friend List', 'Quit']

    # players & world
    p1 = Player(WORLD_W * 0.3, WORLD_H * 0.5, (80, 180, 240), username, 1)
    p2_name = 'Player2'
    p2 = Player(WORLD_W * 0.7, WORLD_H * 0.5, (240, 200, 80), p2_name, 2)

    bullets = []
    zombies = []
    last_zombie = time.time()

    # networking
    net = None
    beacon = None
    is_host = False
    network_mode = None  # None, 'host', 'client'
    host_ip_connected = None

    # chat
    chat_mode = False
    chat_input = ''
    chat_messages = deque(maxlen=MAX_CHAT)
    chat_timers = deque(maxlen=MAX_CHAT)

    # friend list
    friends = cfg.get('friends', [])

    # UI helper
    def draw_centered_text(txt, y, surf=screen, fnt=font):
        r = fnt.render(txt, True, (230, 230, 230))
        surf.blit(r, (SCREEN_W // 2 - r.get_width() // 2, y))

    last_net_send = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        now = time.time()

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            if state == STATE_MENU:
                if event.type == KEYDOWN:
                    if event.key == K_DOWN:
                        menu_idx = (menu_idx + 1) % len(menu_items)
                    elif event.key == K_UP:
                        menu_idx = (menu_idx - 1) % len(menu_items)
                    elif event.key == K_RETURN:
                        sel = menu_items[menu_idx]
                        if sel == 'Local Co-op':
                            # reset world
                            p1.pos = pygame.Vector2(
                                WORLD_W * 0.3, WORLD_H * 0.5)
                            p2.pos = pygame.Vector2(
                                WORLD_W * 0.7, WORLD_H * 0.5)
                            p1.alive = p2.alive = True
                            p1.health = p2.health = 5
                            bullets.clear()
                            zombies.clear()
                            last_zombie = now
                            state = STATE_PLAY
                            network_mode = None
                            if net:
                                net.stop()
                                net = None
                            if beacon:
                                beacon.stop()
                                beacon = None
                        elif sel == 'LAN Host':
                            # prompt server name + port
                            server_name, port = prompt_host_info(
                                screen, font, username, cfg.get('last_port', DEFAULT_PORT))
                            cfg['last_port'] = port
                            save_config(cfg)
                            # start beacon
                            beacon = BeaconBroadcaster(
                                server_name, username, port=port)
                            beacon.start()
                            # start game net as host
                            net = GameNet(
                                is_host=True, local_player_id=1, host_ip=None, port=port)
                            net.start()
                            is_host = True
                            network_mode = 'host'
                            state = STATE_PLAY
                            # reset
                            p1.pos = pygame.Vector2(
                                WORLD_W * 0.3, WORLD_H * 0.5)
                            p2.pos = pygame.Vector2(
                                WORLD_W * 0.7, WORLD_H * 0.5)
                            p1.uname = username
                            p2.uname = 'Waiting...'
                            p1.alive = p2.alive = True
                            bullets.clear()
                            zombies.clear()
                            last_zombie = now
                        elif sel == 'LAN Join':
                            # show discovered hosts list and manual entry
                            choice = prompt_join_menu(screen, font, discovery)
                            if choice:
                                host_ip, port = choice
                                cfg['last_port'] = port
                                save_config(cfg)
                                net = GameNet(
                                    is_host=False, local_player_id=2, host_ip=host_ip, port=port)
                                net.start()
                                is_host = False
                                network_mode = 'client'
                                host_ip_connected = host_ip
                                state = STATE_PLAY
                                # reset
                                p1.pos = pygame.Vector2(
                                    WORLD_W * 0.3, WORLD_H * 0.5)
                                p2.pos = pygame.Vector2(
                                    WORLD_W * 0.7, WORLD_H * 0.5)
                                p1.uname = 'Host'
                                p2.uname = username
                                p1.alive = p2.alive = True
                                bullets.clear()
                                zombies.clear()
                                last_zombie = now
                        elif sel == 'Friend List':
                            friends = prompt_friend_list(
                                screen, font, friends, discovery)
                            cfg['friends'] = friends
                            save_config(cfg)
                        elif sel == 'Quit':
                            running = False
                    elif event.key == K_q:
                        running = False

            elif state == STATE_PLAY:
                if event.type == KEYDOWN:
                    if chat_mode:
                        if event.key == K_RETURN:
                            if chat_input.strip():
                                send_chat(net, username, chat_input.strip())
                                push_chat(chat_messages, chat_timers,
                                          username + ': ' + chat_input.strip())
                                chat_input = ''
                            chat_mode = False
                        elif event.key == K_ESCAPE:
                            chat_mode = False
                        elif event.key == K_BACKSPACE:
                            chat_input = chat_input[:-1]
                        else:
                            if len(chat_input) < 128 and event.unicode:
                                chat_input += event.unicode
                    else:
                        if event.key == K_t:
                            chat_mode = True
                            chat_input = ''
                        elif event.key == K_ESCAPE:
                            state = STATE_PAUSED
                        elif event.key == K_q:
                            running = False
                        # shooting on E for local player
                        elif event.key == K_e:
                            if network_mode is None:
                                # local, allow both players to shoot depending on proximity? Keep simple: both can shoot
                                b = player_shoot_local(p1)
                                if b:
                                    bullets.append(b)
                                    play_sound(shoot_sfx)
                                b2 = player_shoot_local(p2)
                                if b2:
                                    bullets.append(b2)
                                    play_sound(shoot_sfx)
                            else:
                                # networked: local controls only one player depending on role
                                if network_mode == 'host':
                                    b = player_shoot_local(p1)
                                    if b:
                                        bullets.append(b)
                                        play_sound(shoot_sfx)
                                        # notify client about bullet via net
                                        if net:
                                            net.send(
                                                {'type': 'bullet', 'x': b.pos.x, 'y': b.pos.y, 'vx': b.vel.x, 'vy': b.vel.y})
                                else:
                                    b = player_shoot_local(p2)
                                    if b:
                                        bullets.append(b)
                                        play_sound(shoot_sfx)
                                        if net:
                                            net.send(
                                                {'type': 'bullet', 'x': b.pos.x, 'y': b.pos.y, 'vx': b.vel.x, 'vy': b.vel.y})
                elif event.type == QUIT:
                    running = False

        # Update networking incoming messages
        if net:
            while net.incoming:
                msg, addr = net.incoming.popleft()
                handle_net_message(msg, addr, net, p1, p2,
                                   bullets, chat_messages, chat_timers)

        # Periodic network sync
        if net and time.time() - last_net_send > NETWORK_TICK:
            last_net_send = time.time()
            if network_mode == 'host':
                # send host state (p1) to client
                net.send({'type': 'state', 'pid': 1, 'x': p1.pos.x, 'y': p1.pos.y,
                         'hp': p1.health, 'alive': p1.alive, 'uname': username})
            elif network_mode == 'client':
                net.send({'type': 'state', 'pid': 2, 'x': p2.pos.x, 'y': p2.pos.y,
                         'hp': p2.health, 'alive': p2.alive, 'uname': username})

        # Game logic
        if state == STATE_PLAY:
            keys = pygame.key.get_pressed()
            if network_mode is None:
                # local mode: both players controlled locally by different keys
                handle_local_controls(keys, p1, p2, dt)
            else:
                # networked: both sides use WASD+E schematic but only local player moves
                if network_mode == 'host':
                    handle_single_controls(keys, p1, dt)
                else:
                    handle_single_controls(keys, p2, dt)

            # update bullets
            alive_bullets = []
            for b in bullets:
                if b.update(dt):
                    alive_bullets.append(b)
            bullets = alive_bullets

            # spawn zombies
            if time.time() - last_zombie > ZOMBIE_SPAWN:
                last_zombie = time.time()
                zombies.append(Zombie(random.randint(
                    0, WORLD_W), random.randint(0, WORLD_H)))

            # update zombies
            for z in zombies:
                z.update(dt, [p1, p2])

            # simple collisions: bullets vs zombies
            for b in list(bullets):
                for z in list(zombies):
                    if (b.pos - z.pos).length_squared() < 30*30:
                        bullets.remove(b)
                        z.health -= 1
                        if z.health <= 0:
                            try:
                                zombies.remove(z)
                            except ValueError:
                                pass
                        break

            # zombies hitting players
            for z in list(zombies):
                if p1.alive and (p1.pos - z.pos).length_squared() < 30*30:
                    died = p1.take_damage(1)
                    try:
                        zombies.remove(z)
                    except ValueError:
                        pass
                    if died:
                        play_sound(death_sfx)
                        if network_mode and net:
                            net.send({'type': 'death', 'pid': p1.pid})
                if p2.alive and (p2.pos - z.pos).length_squared() < 30*30:
                    died = p2.take_damage(1)
                    try:
                        zombies.remove(z)
                    except ValueError:
                        pass
                    if died:
                        play_sound(death_sfx)
                        if network_mode and net:
                            net.send({'type': 'death', 'pid': p2.pid})

            # Both dead -> game over
            if not p1.alive and not p2.alive:
                state = STATE_GAMEOVER

        # Rendering
        screen.fill((12, 14, 18))
        if state == STATE_MENU:
            draw_centered_text(
                'SOCOS NA CRISTINA - LAN EDITION', 80, screen, big)
            for i, item in enumerate(menu_items):
                color = (255, 255, 255) if i == menu_idx else (180, 180, 180)
                txt = font.render(item, True, color)
                screen.blit(
                    txt, (SCREEN_W//2 - txt.get_width()//2, 220 + i*36))
            draw_centered_text(f'User: {username}', 420, screen)
            draw_centered_text(
                'Use arrow keys + Enter. Q to quit.', 460, screen)

            # show discovered hosts briefly
            y = 520
            draw_centered_text('Discovered on LAN:', y-20)
            for k, v in discovery.discovered.items():
                line = f"{v['host']} - {v['ip']} - {v['ping']} ms" if v['ping'] is not None else f"{v['host']} - {v['ip']} - ?"
                r = font.render(line, True, (180, 180, 180))
                screen.blit(r, (SCREEN_W//2 - r.get_width()//2, y))
                y += 22

        elif state == STATE_PLAY or state == STATE_PAUSED:
            # simple world render: players, bullets, zombies
            # center camera on local player for network mode, otherwise center between players
            cam = pygame.Rect(0, 0, SCREEN_W, SCREEN_H)
            if network_mode == 'host':
                cx = int(p1.pos.x - SCREEN_W/2)
                cy = int(p1.pos.y - SCREEN_H/2)
            elif network_mode == 'client':
                cx = int(p2.pos.x - SCREEN_W/2)
                cy = int(p2.pos.y - SCREEN_H/2)
            else:
                mid = (p1.pos + p2.pos) * 0.5
                cx = int(mid.x - SCREEN_W/2)
                cy = int(mid.y - SCREEN_H/2)
            cx = clamp(cx, 0, WORLD_W - SCREEN_W)
            cy = clamp(cy, 0, WORLD_H - SCREEN_H)
            cam.topleft = (cx, cy)

            # draw background grid
            for gx in range(0, WORLD_W, 160):
                x = gx - cam.x
                pygame.draw.line(screen, (18, 18, 20), (x, 0), (x, SCREEN_H))
            for gy in range(0, WORLD_H, 160):
                y = gy - cam.y
                pygame.draw.line(screen, (18, 18, 20), (0, y), (SCREEN_W, y))

            # draw zombies
            for z in zombies:
                pos = (int(z.pos.x - cam.x), int(z.pos.y - cam.y))
                pygame.draw.circle(screen, (100, 200, 120), pos, 16)

            # bullets
            for b in bullets:
                pos = (int(b.pos.x - cam.x), int(b.pos.y - cam.y))
                pygame.draw.circle(screen, (255, 255, 255), pos, 4)

            # players
            p1s = (int(p1.pos.x - cam.x), int(p1.pos.y - cam.y))
            p2s = (int(p2.pos.x - cam.x), int(p2.pos.y - cam.y))
            pygame.draw.polygon(screen, p1.color, [
                                (p1s[0], p1s[1]-12), (p1s[0]+10, p1s[1]+12), (p1s[0]-10, p1s[1]+12)])
            pygame.draw.polygon(screen, p2.color, [
                                (p2s[0], p2s[1]-12), (p2s[0]+10, p2s[1]+12), (p2s[0]-10, p2s[1]+12)])

            # HUD: names and health
            hud1 = font.render(
                f"{p1.uname} - HP: {p1.health}", True, (230, 230, 230))
            hud2 = font.render(
                f"{p2.uname} - HP: {p2.health}", True, (230, 230, 230))
            screen.blit(hud1, (12, 12))
            screen.blit(hud2, (12, 36))

            # chat box
            draw_chat(screen, font, chat_messages, chat_timers)
            if chat_mode:
                inp = font.render('> ' + chat_input, True, (240, 240, 240))
                screen.blit(inp, (12, SCREEN_H - 28))

            if state == STATE_PAUSED:
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                screen.blit(overlay, (0, 0))
                draw_centered_text('PAUSED - Esc to resume', SCREEN_H//2 - 12)

        elif state == STATE_GAMEOVER:
            draw_centered_text('GAME OVER', SCREEN_H//2 - 40, screen, big)
            draw_centered_text(
                'Press Enter to return to menu', SCREEN_H//2 + 8)
            keys = pygame.key.get_pressed()
            if keys[K_RETURN]:
                state = STATE_MENU

        pygame.display.flip()

    # cleanup
    if discovery:
        discovery.stop()
    if beacon:
        beacon.stop()
    if net:
        net.stop()
    pygame.quit()
    sys.exit()


# ------------------ Helper / UI / Network Handlers ------------------

def load_sound(filename):
    if not os.path.exists(filename):
        return None
    try:
        snd = pygame.mixer.Sound(filename)
        return snd
    except Exception:
        return None


def play_sound(snd):
    if snd:
        try:
            snd.play()
        except Exception:
            pass


def prompt_username(screen, font):
    # simple blocking prompt
    username = ''
    clock = pygame.time.Clock()
    asking = True
    while asking:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == KEYDOWN:
                if ev.key == K_RETURN:
                    if username.strip():
                        asking = False
                elif ev.key == K_BACKSPACE:
                    username = username[:-1]
                elif ev.unicode and len(username) < 16:
                    username += ev.unicode
        screen.fill((8, 8, 10))
        txt = font.render('Enter username (will be saved):',
                          True, (230, 230, 230))
        screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, 220))
        inp = font.render(username or 'Player', True, (240, 240, 240))
        screen.blit(inp, (SCREEN_W//2 - inp.get_width()//2, 260))
        small = font.render('Press Enter to confirm', True, (180, 180, 180))
        screen.blit(small, (SCREEN_W//2 - small.get_width()//2, 320))
        pygame.display.flip()
        clock.tick(30)
    return username


def prompt_host_info(screen, font, username, default_port):
    server_name = ''
    port_text = str(default_port)
    field = 'name'  # or 'port'
    clock = pygame.time.Clock()
    while True:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == KEYDOWN:
                if ev.key == K_TAB:
                    field = 'port' if field == 'name' else 'name'
                elif ev.key == K_RETURN:
                    try:
                        port = int(port_text)
                    except Exception:
                        port = default_port
                    if not server_name.strip():
                        server_name = f"{username}'s Server"
                    return server_name, port
                elif ev.key == K_BACKSPACE:
                    if field == 'name':
                        server_name = server_name[:-1]
                    else:
                        port_text = port_text[:-1]
                elif ev.unicode:
                    if field == 'name' and len(server_name) < 24:
                        server_name += ev.unicode
                    elif field == 'port' and ev.unicode.isdigit() and len(port_text) < 6:
                        port_text += ev.unicode
        screen.fill((8, 8, 10))
        draw_text_center(
            screen, font, 'Host Game - Enter Server Name and Port', 120)
        nlabel = font.render('Server name:', True, (220, 220, 220))
        screen.blit(nlabel, (120, 220))
        nval = font.render(
            server_name or f"{username}'s Server", True, (240, 240, 240))
        screen.blit(nval, (120, 252))
        plabel = font.render('Port:', True, (220, 220, 220))
        screen.blit(plabel, (120, 300))
        pval = font.render(port_text, True, (240, 240, 240))
        screen.blit(pval, (120, 332))
        hint = font.render(
            'Press Enter to start hosting. Tab to switch field.', True, (160, 160, 160))
        screen.blit(hint, (120, 380))
        pygame.display.flip()
        clock.tick(30)


def prompt_join_menu(screen, font, discovery):
    # show discovered hosts in list; user can select with arrows, or press M to manual enter
    sel = 0
    clock = pygame.time.Clock()
    manual = False
    manual_ip = ''
    manual_port = str(discovery.listen_port if hasattr(
        discovery, 'listen_port') else DEFAULT_PORT)
    while True:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == KEYDOWN:
                if manual:
                    if ev.key == K_RETURN:
                        try:
                            return (manual_ip.strip(), int(manual_port))
                        except Exception:
                            pass
                    elif ev.key == K_ESCAPE:
                        manual = False
                    elif ev.key == K_BACKSPACE:
                        manual_ip = manual_ip[:-1]
                    elif ev.unicode:
                        manual_ip += ev.unicode
                else:
                    if ev.key == K_DOWN:
                        sel += 1
                    elif ev.key == K_UP:
                        sel -= 1
                    elif ev.key == K_RETURN:
                        items = list(discovery.discovered.items())
                        if items:
                            (ipport, info) = items[sel % len(items)]
                            return info['ip'], info['port']
                    elif ev.key == K_m:
                        manual = True
                    elif ev.key == K_ESCAPE:
                        return None
        screen.fill((8, 8, 10))
        draw_text_center(
            screen, font, 'Join LAN - Select Host (Enter) or M for manual IP', 80)
        items = list(discovery.discovered.items())
        if not items:
            draw_text_center(
                screen, font, 'Searching for hosts on LAN...', 160)
        else:
            y = 140
            for i, (k, v) in enumerate(items):
                ping_text = f"{v['ping']} ms" if v['ping'] is not None else '?'
                line = f"{v['host']} - {v['ip']} - {ping_text}"
                color = (255, 255, 255) if i == (sel %
                                                 len(items)) else (200, 200, 200)
                r = font.render(line, True, color)
                screen.blit(r, (120, y))
                y += 28
        small = font.render('Press Esc to cancel', True, (160, 160, 160))
        screen.blit(small, (120, SCREEN_H - 40))
        if manual:
            mlabel = font.render(
                'Manual IP (type then Enter): ' + manual_ip, True, (240, 240, 240))
            screen.blit(mlabel, (120, SCREEN_H - 80))
        pygame.display.flip()
        clock.tick(30)


def prompt_friend_list(screen, font, friends, discovery):
    sel = 0
    clock = pygame.time.Clock()
    while True:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == KEYDOWN:
                if ev.key == K_DOWN:
                    sel = (sel + 1) % max(1, len(friends)+1)
                elif ev.key == K_UP:
                    sel = (sel - 1) % max(1, len(friends)+1)
                elif ev.key == K_a:
                    new = prompt_add_friend(screen, font)
                    if new and new not in friends:
                        friends.append(new)
                elif ev.key == K_DELETE:
                    if friends:
                        friends.pop(sel % len(friends))
                elif ev.key == K_ESCAPE:
                    return friends
        screen.fill((8, 8, 10))
        draw_text_center(
            screen, font, 'Friend List - Press A to add, Delete to remove, Esc to back', 60)
        y = 120
        for i, f in enumerate(friends):
            # see if friend is online by matching discovery entries
            online = False
            ip = '?'
            ping = '?'
            for k, v in discovery.discovered.items():
                if v['host'] == f:
                    online = True
                    ip = v['ip']
                    ping = f"{v['ping']} ms" if v['ping'] is not None else '?'
            color = (255, 255, 255) if i == sel else (200, 200, 200)
            status = f"{f} - {ip} - {ping}"
            r = font.render(status, True, color)
            screen.blit(r, (80, y))
            y += 28
        # also show discovered hosts not in friend list
        y += 8
        draw_text_center(screen, font, 'Discovered (not friends):', y)
        y += 28
        for k, v in discovery.discovered.items():
            if v['host'] not in friends:
                line = f"{v['host']} - {v['ip']} - {v['ping']} ms" if v['ping'] is not None else f"{v['host']} - {v['ip']} - ?"
                r = font.render(line, True, (170, 170, 170))
                screen.blit(r, (80, y))
                y += 22
        pygame.display.flip()
        clock.tick(30)


def prompt_add_friend(screen, font):
    name = ''
    clock = pygame.time.Clock()
    while True:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == KEYDOWN:
                if ev.key == K_RETURN:
                    return name.strip() if name.strip() else None
                elif ev.key == K_ESCAPE:
                    return None
                elif ev.key == K_BACKSPACE:
                    name = name[:-1]
                elif ev.unicode and len(name) < 20:
                    name += ev.unicode
        screen.fill((8, 8, 10))
        draw_text_center(screen, font, 'Add Friend - Enter username:', 220)
        inp = font.render(name or 'Name', True, (240, 240, 240))
        screen.blit(inp, (SCREEN_W//2 - inp.get_width()//2, 260))
        pygame.display.flip()
        clock.tick(30)


def draw_text_center(screen, font, text, y):
    r = font.render(text, True, (230, 230, 230))
    screen.blit(r, (SCREEN_W//2 - r.get_width()//2, y))


def push_chat(chat_messages, chat_timers, msg):
    chat_messages.append(msg)
    chat_timers.append(time.time())


def draw_chat(screen, font, chat_messages, chat_timers):
    # draw last messages at bottom-left
    x = 12
    y = SCREEN_H - 36 - (len(chat_messages) * 18)
    now = time.time()
    for i, msg in enumerate(chat_messages):
        # fade based on age
        age = now - chat_timers[i]
        alpha = 255
        if age > 7.0:
            alpha = max(0, int(255 - (age - 7.0) * 40))
        color = (255, 255, 255)
        surf = font.render(msg, True, color)
        screen.blit(surf, (x, y))
        y += 18


def player_shoot_local(player):
    if not player.alive:
        return None
    dir = player.last_dir if player.last_dir.length_squared() > 0 else pygame.Vector2(0, -1)
    vel = dir.normalize() * BULLET_SPEED
    b = Bullet(player.pos + dir*12, vel, player.pid)
    return b


def handle_local_controls(keys, p1, p2, dt):
    # P1 - WASD, P2 - arrows
    mv1 = pygame.Vector2(0, 0)
    if keys[K_w]:
        mv1.y -= 1
    if keys[K_s]:
        mv1.y += 1
    if keys[K_a]:
        mv1.x -= 1
    if keys[K_d]:
        mv1.x += 1
    if mv1.length_squared() > 0:
        mv1 = mv1.normalize()
        p1.pos += mv1 * PLAYER_SPEED * dt
        p1.last_dir = mv1
    mv2 = pygame.Vector2(0, 0)
    if keys[K_UP]:
        mv2.y -= 1
    if keys[K_DOWN]:
        mv2.y += 1
    if keys[K_LEFT]:
        mv2.x -= 1
    if keys[K_RIGHT]:
        mv2.x += 1
    if mv2.length_squared() > 0:
        mv2 = mv2.normalize()
        p2.pos += mv2 * PLAYER_SPEED * dt
        p2.last_dir = mv2


def handle_single_controls(keys, p, dt):
    mv = pygame.Vector2(0, 0)
    if keys[K_w]:
        mv.y -= 1
    if keys[K_s]:
        mv.y += 1
    if keys[K_a]:
        mv.x -= 1
    if keys[K_d]:
        mv.x += 1
    if mv.length_squared() > 0:
        mv = mv.normalize()
        p.pos += mv * PLAYER_SPEED * dt
        p.last_dir = mv


def handle_net_message(msg, addr, net, p1, p2, bullets, chat_messages, chat_timers):
    t = msg.get('type')
    if t == 'state':
        pid = msg.get('pid')
        if pid == 1:
            # host state
            p1.pos.x += (msg.get('x', p1.pos.x) - p1.pos.x) * 0.4
            p1.pos.y += (msg.get('y', p1.pos.y) - p1.pos.y) * 0.4
            p1.health = msg.get('hp', p1.health)
            p1.alive = msg.get('alive', p1.alive)
            p1.uname = msg.get('uname', p1.uname)
        else:
            p2.pos.x += (msg.get('x', p2.pos.x) - p2.pos.x) * 0.4
            p2.pos.y += (msg.get('y', p2.pos.y) - p2.pos.y) * 0.4
            p2.health = msg.get('hp', p2.health)
            p2.alive = msg.get('alive', p2.alive)
            p2.uname = msg.get('uname', p2.uname)
    elif t == 'bullet':
        bx = msg.get('x')
        by = msg.get('y')
        vx = msg.get('vx')
        vy = msg.get('vy')
        if None not in (bx, by, vx, vy):
            b = Bullet(pygame.Vector2(bx, by), pygame.Vector2(
                vx, vy), msg.get('owner', 0))
            bullets.append(b)
    elif t == 'chat':
        user = msg.get('user', '??')
        text = msg.get('text', '')
        push_chat(chat_messages, chat_timers, f"{user}: {text}")
    elif t == 'death':
        pid = msg.get('pid')
        if pid == 1:
            p1.alive = False
        elif pid == 2:
            p2.alive = False


def send_chat(net, user, text):
    if net:
        net.send({'type': 'chat', 'user': user, 'text': text})


# ------------------ Entry ------------------
if __name__ == '__main__':
    main()
