import socket
import threading
import pickle
import pygame
import sys
import random

# --- CONFIGURATION ---
PORT = 5555
HEADER_SIZE = 4096  # Buffer size for network data
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# --- COLORS ---
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRID_COLOR = (40, 40, 40)
TEXT_COLOR = (255, 255, 255)

# --- UTILS ---


def get_local_ip():
    """Try to determine the local machine's IP address on the network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable, just triggers OS to find correct interface
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# --- PLAYER CLASS (Game Object) ---


class Player:
    def __init__(self, x, y, width, height, color, name="Unknown"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = (x, y, width, height)
        self.vel = 3
        self.name = name
        self.is_attacking = False
        self.attack_timer = 0
        self.hp = 100

    def draw(self, win):
        # Draw Player Body
        pygame.draw.rect(win, self.color, self.rect)

        # Draw Attack Visual (White flash border)
        if self.is_attacking:
            pygame.draw.rect(win, WHITE, self.rect, 3)

        # Draw Name
        font = pygame.font.SysFont("Arial", 16)
        text = font.render(self.name, 1, TEXT_COLOR)
        win.blit(text, (self.x - 10, self.y - 20))

        # Draw HP Bar
        pygame.draw.rect(win, (255, 0, 0), (self.x, self.y - 8, self.width, 5))
        pygame.draw.rect(win, (0, 255, 0), (self.x, self.y -
                         8, self.width * (self.hp/100), 5))

    def move(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.vel
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.vel
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.vel
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.vel

        # Attack logic
        if keys[pygame.K_SPACE]:
            self.is_attacking = True
            self.attack_timer = 10

        if self.attack_timer > 0:
            self.attack_timer -= 1
        else:
            self.is_attacking = False

        self.update()

    def update(self):
        # Keep inside screen bounds
        if self.x < 0:
            self.x = 0
        if self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
        if self.y < 0:
            self.y = 0
        if self.y > SCREEN_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - self.height

        self.rect = (self.x, self.y, self.width, self.height)

# --- NETWORK CLASS (Client Side Helper) ---


class Network:
    def __init__(self, server_ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip
        self.port = PORT
        self.addr = (self.server, self.port)
        self.p_data = self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            # Receive initial player object confirmation
            return pickle.loads(self.client.recv(HEADER_SIZE))
        except Exception as e:
            print(f"Network Connection Error: {e}")
            pass

    def send(self, data):
        try:
            # Send our player data to server
            self.client.send(pickle.dumps(data))
            # Receive the entire world state (dict of all players)
            return pickle.loads(self.client.recv(HEADER_SIZE))
        except socket.error as e:
            print(e)

# --- SERVER CODE ---


def start_server():
    server_ip = get_local_ip()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Bind to '' (INADDR_ANY) to listen on all interfaces (localhost AND LAN)
        server.bind(('', PORT))
    except socket.error as e:
        print(str(e))
        print("Error: Could not bind server. Port might be in use.")
        return

    server.listen(4)  # Allow up to 4 connections queued
    print("="*40)
    print(f" SERVER STARTED")
    print(f" Local IP for friends: {server_ip}")
    print("="*40)
    print("Waiting for connections...")

    # Dictionary to hold all players: { conn_id: PlayerObject }
    players = {}

    # Simple ID generator
    current_id = 0

    def threaded_client(conn, player_id):
        # Generate a random color and start pos for new player
        start_x = random.randint(50, SCREEN_WIDTH-50)
        start_y = random.randint(50, SCREEN_HEIGHT-50)
        color = (random.randint(50, 255), random.randint(
            50, 255), random.randint(50, 255))

        # Create the new player object and store it
        players[player_id] = Player(
            start_x, start_y, 50, 50, color, f"Player {player_id}")

        # Send the initial player object to the client so they know who they are
        conn.send(pickle.dumps(players[player_id]))

        reply = ""
        while True:
            try:
                # Receive data from client
                data = pickle.loads(conn.recv(HEADER_SIZE))
                # Update the server's version of this player
                players[player_id] = data

                if not data:
                    print("Disconnected")
                    break

                # Send back the dictionary of ALL players
                reply = players
                conn.sendall(pickle.dumps(reply))
            except:
                break

        print(f"Player {player_id} Lost Connection")
        del players[player_id]
        conn.close()

    while True:
        conn, addr = server.accept()
        print(f"Connected to: {addr}")

        current_id += 1
        # Start a new thread for this specific player
        import threading
        t = threading.Thread(target=threaded_client, args=(conn, current_id))
        t.start()

# --- CLIENT CODE ---


def start_client():
    print("="*40)
    print(" CLIENT MODE")
    print("="*40)
    server_ip = input("Enter Server IP (e.g. 192.168.1.X or localhost): ")
    if not server_ip:
        server_ip = "127.0.0.1"

    name = input("Enter your Character Name: ")

    pygame.init()
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("LAN RPG Adventure")

    clock = pygame.time.Clock()

    # Initialize networking
    print(f"Connecting to {server_ip}...")
    try:
        n = Network(server_ip)
        p = n.p_data  # Get our initial player object
        if not p:
            print("Could not connect to server. Ensure Server is running.")
            return
        p.name = name  # Update name locally
    except:
        print("Connection Failed. Check IP or if Server is running.")
        return

    run = True
    while run:
        clock.tick(FPS)

        # 1. Check Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        # 2. Move Local Player
        p.move()

        # 3. Network Sync
        # Send our updated player 'p' to server, receive 'others' (all players) back
        try:
            others = n.send(p)
        except:
            print("Lost connection to server.")
            run = False
            break

        # 4. Draw Everything
        win.fill(BLACK)

        # Draw a simple grid floor
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(win, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(win, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

        # Draw all players in the server list
        if others:
            for p_id, player_obj in others.items():
                player_obj.draw(win)

        pygame.display.update()

    pygame.quit()


# --- MAIN MENU ---
if __name__ == "__main__":
    print("   SIMPLE PYTHON LAN RPG   ")
    print("---------------------------")
    print("[1] Host Server")
    print("[2] Join Server")

    choice = input("Select option: ")

    if choice == "1":
        start_server()
    elif choice == "2":
        start_client()
    else:
        print("Invalid choice.")

# --- CONFIGURATION ---
PORT = 5555
HEADER_SIZE = 8192  # Increased buffer for more data
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# --- COLORS ---
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRID_COLOR = (40, 40, 40)
TEXT_COLOR = (255, 255, 255)
COIN_COLOR = (255, 215, 0)  # Gold
UI_BG = (50, 50, 50)

# --- UTILS ---


def get_local_ip():
    """Try to determine the local machine's IP address on the network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# --- GAME CLASSES ---


class Player:
    def __init__(self, id, x, y, p_class, name="Unknown"):
        self.id = id
        self.x = x
        self.y = y
        self.name = name
        self.p_class = p_class
        self.score = 0

        # Class Stats
        if p_class == "Scout":
            self.width = 30
            self.height = 30
            self.color = (0, 255, 255)  # Cyan
            self.vel = 5
        elif p_class == "Tank":
            self.width = 60
            self.height = 60
            self.color = (0, 255, 0)  # Green
            self.vel = 3
        else:  # Default
            self.width = 40
            self.height = 40
            self.color = (255, 0, 0)
            self.vel = 4

        self.rect = (self.x, self.y, self.width, self.height)

    def draw(self, win):
        # Draw Player Body
        pygame.draw.rect(win, self.color, self.rect)

        # Draw Outline
        pygame.draw.rect(win, WHITE, self.rect, 2)

        # Draw Name
        font = pygame.font.SysFont("Arial", 14, bold=True)
        text = font.render(f"{self.name} [{self.score}]", 1, TEXT_COLOR)
        # Center text above player
        text_rect = text.get_rect(center=(self.x + self.width//2, self.y - 15))
        win.blit(text, text_rect)

    def move(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.vel
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.vel
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.vel
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.vel

        self.update()

    def update(self):
        # Keep inside screen bounds
        if self.x < 0:
            self.x = 0
        if self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
        if self.y < 0:
            self.y = 0
        if self.y > SCREEN_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - self.height

        self.rect = (self.x, self.y, self.width, self.height)


class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 15
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def draw(self, win):
        pygame.draw.ellipse(win, COIN_COLOR, self.rect)
        # Shine effect
        pygame.draw.ellipse(win, WHITE, (self.x + 4, self.y + 4, 5, 5))

# --- NETWORK CLASS ---


class Network:
    def __init__(self, server_ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip
        self.port = PORT
        self.addr = (self.server, self.port)
        self.initial_data = self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            # Receive initial setup (ID, StartPos)
            return pickle.loads(self.client.recv(HEADER_SIZE))
        except Exception as e:
            print(f"Network Connection Error: {e}")
            pass

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            # Receive tuple: (players_dict, coins_list)
            return pickle.loads(self.client.recv(HEADER_SIZE))
        except socket.error as e:
            print(e)

# --- SERVER CODE ---


def start_server():
    server_ip = get_local_ip()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind(('', PORT))
    except socket.error as e:
        print(str(e))
        return

    server.listen(4)
    print("="*40)
    print(f" SERVER STARTED - TREASURE HUNT MODE")
    print(f" Local IP: {server_ip}")
    print("="*40)

    # Game State
    players = {}
    coins = []

    # Spawn initial coins
    for _ in range(10):
        coins.append(Coin(random.randint(50, SCREEN_WIDTH-50),
                     random.randint(50, SCREEN_HEIGHT-50)))

    # Thread to handle a single client
    def threaded_client(conn, player_id):
        # 1. Receive 'Handshake': Player Name and Class
        try:
            handshake = pickle.loads(conn.recv(HEADER_SIZE))
            name = handshake['name']
            p_class = handshake['class']
        except:
            conn.close()
            return

        # 2. Create Player Object
        start_x = random.randint(50, SCREEN_WIDTH-50)
        start_y = random.randint(50, SCREEN_HEIGHT-50)
        new_player = Player(player_id, start_x, start_y, p_class, name)
        players[player_id] = new_player

        # 3. Send Initial Player Object back to client
        conn.send(pickle.dumps(new_player))

        while True:
            try:
                # Receive updated player object from client
                data = pickle.loads(conn.recv(HEADER_SIZE))

                # Update server state (Movement)
                players[player_id].x = data.x
                players[player_id].y = data.y
                players[player_id].update()

                # --- SERVER AUTHORITATIVE LOGIC (Collision) ---
                # Check if this player hit any coins
                p_rect = pygame.Rect(players[player_id].rect)
                for coin in coins[:]:  # Copy list to remove safely
                    if p_rect.colliderect(coin.rect):
                        coins.remove(coin)
                        players[player_id].score += 1
                        # Respawn coin elsewhere
                        coins.append(Coin(random.randint(
                            20, SCREEN_WIDTH-20), random.randint(20, SCREEN_HEIGHT-20)))

                if not data:
                    break

                # Send World State: (All Players, All Coins)
                reply = (players, coins)
                conn.sendall(pickle.dumps(reply))
            except Exception as e:
                break

        print(f"Player {player_id} Disconnected")
        if player_id in players:
            del players[player_id]
        conn.close()

    current_id = 0
    while True:
        conn, addr = server.accept()
        print(f"Connected to: {addr}")
        current_id += 1
        t = threading.Thread(target=threaded_client, args=(conn, current_id))
        t.start()

# --- CLIENT CODE ---


def start_client():
    print("="*40)
    print(" CLIENT MODE")
    print("="*40)
    server_ip = input("Enter Server IP (leave empty for localhost): ")
    if not server_ip:
        server_ip = "127.0.0.1"

    name = input("Enter Character Name: ")
    print("\nChoose Class:")
    print("[1] Scout (Fast, Small)")
    print("[2] Tank (Slow, Big)")
    class_choice = input("Choice: ")

    p_class = "Scout" if class_choice == "1" else "Tank"

    # Init Pygame
    pygame.init()
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"LAN RPG - {name} ({p_class})")
    clock = pygame.time.Clock()

    # Network Setup
    print(f"Connecting to {server_ip}...")
    try:
        n = Network(server_ip)

        # Send Handshake (Name/Class)
        n.client.send(pickle.dumps({'name': name, 'class': p_class}))

        # Receive our actual Player Object
        p = pickle.loads(n.client.recv(HEADER_SIZE))

    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    run = True
    server_coins = []  # Store coins locally for drawing

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        # Move
        p.move()

        # Network Sync
        try:
            # Send 'p', receive '(players_dict, coins_list)'
            response = n.send(p)
            if response:
                others, server_coins = response

                # Sync Score from Server Authority
                if p.id in others:
                    p.score = others[p.id].score
            else:
                others = {}
        except:
            print("Server Disconnected")
            run = False
            break

        # Draw
        win.fill(BLACK)

        # Grid
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(win, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(win, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

        # Draw Coins
        for coin in server_coins:
            coin.draw(win)

        # Draw Players
        for p_id, player_obj in others.items():
            player_obj.draw(win)

        # Draw UI (Scoreboard)
        pygame.draw.rect(win, UI_BG, (0, 0, 200, 100))
        pygame.draw.rect(win, WHITE, (0, 0, 200, 100), 2)
        font = pygame.font.SysFont("Arial", 16)
        title = font.render("LEADERBOARD", 1, WHITE)
        win.blit(title, (10, 5))

        # Sort players by score
        sorted_players = sorted(
            others.values(), key=lambda x: x.score, reverse=True)
        y_offset = 25
        for sp in sorted_players[:4]:  # Show top 4
            score_text = font.render(f"{sp.name}: {sp.score}", 1, sp.color)
            win.blit(score_text, (10, y_offset))
            y_offset += 18

        pygame.display.update()

    pygame.quit()


# --- MAIN MENU ---
if __name__ == "__main__":
    print("   PYTHON LAN TREASURE HUNT   ")
    print("------------------------------")
    print("[1] Host Server")
    print("[2] Join Server")

    choice = input("Select option: ")

    if choice == "1":
        start_server()
    elif choice == "2":
        start_client()
