import pygame
import numpy as np
import random
import math
from collections import defaultdict, deque

# ----------------------------
# Constants
# ----------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
BROWN = (139, 69, 19)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)

# Map rooms: name, rect, color, task icon position
ROOMS = [
    {"name": "Cafeteria", "rect": pygame.Rect(
        100, 80, 220, 160), "color": (255, 255, 200)},
    {"name": "Weapons", "rect": pygame.Rect(
        380, 80, 180, 140), "color": (200, 200, 255)},
    {"name": "Electrical", "rect": pygame.Rect(
        620, 80, 180, 140), "color": (255, 200, 200)},
    {"name": "O2", "rect": pygame.Rect(
        860, 80, 180, 140), "color": (200, 255, 200)},
    {"name": "Navigation", "rect": pygame.Rect(
        200, 280, 200, 160), "color": (255, 255, 150)},
    {"name": "Shields", "rect": pygame.Rect(
        460, 280, 200, 160), "color": (200, 255, 255)},
    {"name": "Communications", "rect": pygame.Rect(
        720, 280, 180, 140), "color": (255, 200, 255)},
    {"name": "Storage", "rect": pygame.Rect(
        320, 480, 240, 160), "color": (210, 180, 140)}
]

# Build lookup
ROOM_BY_NAME = {r["name"]: r for r in ROOMS}
ROOM_NAMES = [r["name"] for r in ROOMS]

# Adjacency list (graph)
ADJACENT = {
    "Cafeteria": ["Weapons", "Navigation", "Storage"],
    "Weapons": ["Cafeteria", "Electrical", "Shields"],
    "Electrical": ["Weapons", "O2", "Communications"],
    "O2": ["Electrical", "Communications", "Storage"],
    "Navigation": ["Cafeteria", "Shields", "Storage"],
    "Shields": ["Weapons", "Navigation", "Communications"],
    "Communications": ["Electrical", "O2", "Shields"],
    "Storage": ["Cafeteria", "O2", "Navigation"]
}

NUM_PLAYERS = 8
NUM_IMPOSTORS = 2
MAX_TASKS = 4  # tasks per crewmate

# Neural network
INPUT_SIZE = 20
HIDDEN_SIZE = 12
OUTPUT_SIZE = 5  # move, task, kill, report, call meeting

# Event log
MAX_LOG_ENTRIES = 8

# ----------------------------
# Neural Network
# ----------------------------


class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size):
        self.W1 = np.random.randn(input_size, hidden_size) * 0.2
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * 0.2
        self.b2 = np.zeros((1, output_size))

    def forward(self, x):
        x = np.array(x).reshape(1, -1)
        z = np.dot(x, self.W1) + self.b1
        a = np.tanh(z)
        out = np.dot(a, self.W2) + self.b2
        return np.tanh(out).flatten()

# ----------------------------
# Player
# ----------------------------


class Player:
    def __init__(self, pid, role, network):
        self.id = pid
        self.role = role
        self.alive = True
        self.room = random.choice(ROOM_NAMES)
        self.tasks_done = 0
        self.suspicion = 0
        self.network = network
        self.vote = None
        self.color = BLUE if role == 'crewmate' else RED
        # For smooth movement
        self.target_pos = self.get_room_center()
        self.pos = list(self.target_pos)
        self.speed = 5.0

    def get_room_center(self):
        rect = ROOM_BY_NAME[self.room]["rect"]
        return (rect.centerx, rect.centery)

    def update_position(self):
        # Move toward target room center
        dx = self.target_pos[0] - self.pos[0]
        dy = self.target_pos[1] - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < self.speed:
            self.pos = list(self.target_pos)
        else:
            self.pos[0] += dx / dist * self.speed
            self.pos[1] += dy / dist * self.speed

    def move_to(self, new_room):
        if new_room in ADJACENT[self.room]:
            self.room = new_room
            self.target_pos = self.get_room_center()
            return True
        return False

# ----------------------------
# Game
# ----------------------------


class Game:
    def __init__(self, screen, players_networks):
        self.screen = screen
        self.players = []
        impostor_ids = random.sample(range(NUM_PLAYERS), NUM_IMPOSTORS)
        for i in range(NUM_PLAYERS):
            role = 'impostor' if i in impostor_ids else 'crewmate'
            self.players.append(Player(i, role, players_networks[i]))
        self.meeting = False
        self.meeting_timer = 0
        self.dead_bodies = []  # list of player ids dead but not reported
        self.sabotage = None
        self.tasks_remaining = sum(
            MAX_TASKS for p in self.players if p.role == 'crewmate')
        self.game_over = False
        self.winner = None
        self.step_count = 0
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.big_font = pygame.font.Font(None, 48)
        self.event_log = deque(maxlen=MAX_LOG_ENTRIES)
        self.log("Game started.")

    def log(self, message):
        self.event_log.append(message)

    def get_state(self, player):
        state = []
        state.append(1 if player.role == 'impostor' else 0)
        state.append(self.step_count / 200)  # normalized time
        nearby = sum(1 for p in self.players if p.id !=
                     player.id and p.alive and p.room == player.room)
        state.append(nearby / (NUM_PLAYERS-1))
        bodies_nearby = sum(
            1 for b in self.dead_bodies if self.players[b].room == player.room)
        state.append(bodies_nearby / NUM_PLAYERS)
        state.append(self.tasks_remaining /
                     (MAX_TASKS * (NUM_PLAYERS - NUM_IMPOSTORS)))
        state.append(1 if self.sabotage else 0)
        state.append(1 if self.meeting else 0)
        state.append(player.suspicion / NUM_PLAYERS)
        while len(state) < INPUT_SIZE:
            state.append(0)
        return state[:INPUT_SIZE]

    def step(self):
        if self.game_over:
            return
        self.step_count += 1
        if self.meeting:
            self.meeting_step()
        else:
            self.game_step()
        # Update player positions for smooth animation
        for p in self.players:
            p.update_position()

    def game_step(self):
        for player in self.players:
            if not player.alive:
                continue
            state = self.get_state(player)
            output = player.network.forward(state)
            action = np.argmax(output)
            if action == 0:  # move
                if ADJACENT[player.room]:
                    new_room = random.choice(ADJACENT[player.room])
                    player.move_to(new_room)
            elif action == 1:  # task
                if player.role == 'crewmate' and player.tasks_done < MAX_TASKS:
                    player.tasks_done += 1
                    self.tasks_remaining -= 1
                    self.log(
                        f"Crewmate {player.id} did a task in {player.room}.")
            elif action == 2:  # kill
                if player.role == 'impostor':
                    targets = [p for p in self.players if p.id !=
                               player.id and p.alive and p.room == player.room]
                    if targets:
                        target = random.choice(targets)
                        target.alive = False
                        self.dead_bodies.append(target.id)
                        self.log(
                            f"Impostor {player.id} killed {target.id} in {player.room}!")
            elif action == 3:  # report
                if self.dead_bodies and any(self.players[b].room == player.room for b in self.dead_bodies):
                    self.meeting = True
                    self.meeting_timer = 5
                    self.dead_bodies = []
                    self.log(
                        f"Player {player.id} reported a body! Meeting called.")
            elif action == 4:  # call meeting
                if player.room == "Cafeteria":
                    self.meeting = True
                    self.meeting_timer = 5
                    self.log(
                        f"Player {player.id} called an emergency meeting!")

        # Win conditions
        alive_crew = sum(
            1 for p in self.players if p.alive and p.role == 'crewmate')
        alive_imp = sum(
            1 for p in self.players if p.alive and p.role == 'impostor')
        if self.tasks_remaining <= 0:
            self.game_over = True
            self.winner = 'crew'
            self.log("All tasks done! Crew wins.")
        elif alive_imp == 0:
            self.game_over = True
            self.winner = 'crew'
            self.log("All impostors eliminated! Crew wins.")
        elif alive_imp >= alive_crew:
            self.game_over = True
            self.winner = 'impostor'
            self.log("Impostors outnumber crew! Impostors win.")

    def meeting_step(self):
        if self.meeting_timer > 0:
            self.meeting_timer -= 1
            if self.meeting_timer == 0:
                # Simple voting: each alive player votes randomly among alive players or skip
                votes = defaultdict(int)
                for p in self.players:
                    if p.alive:
                        candidates = [i for i in range(
                            NUM_PLAYERS) if self.players[i].alive] + [-1]
                        vote = random.choice(candidates)
                        if vote != -1:
                            votes[vote] += 1
                if votes:
                    max_votes = max(votes.values())
                    top = [p for p, v in votes.items() if v == max_votes]
                    ejected = random.choice(top)
                    self.players[ejected].alive = False
                    self.log(f"Player {ejected} was ejected.")
                self.meeting = False
                self.dead_bodies = []
        else:
            self.meeting = False

    def draw(self, show_roles=True, show_minimap=True):
        self.screen.fill((30, 30, 30))  # dark background

        # Draw rooms
        for room in ROOMS:
            rect = room["rect"]
            color = room["color"]
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 3)  # border
            # Room name
            text = self.font.render(room["name"], True, BLACK)
            self.screen.blit(text, (rect.x+10, rect.y+10))
            # Task indicator if tasks remain in this room? Not tracked per room, but we can show a generic icon.

        # Draw dead bodies
        for body_id in self.dead_bodies:
            player = self.players[body_id]
            center = player.get_room_center()
            pygame.draw.circle(self.screen, GRAY, center, 12)
            pygame.draw.line(
                self.screen, BLACK, (center[0]-8, center[1]-8), (center[0]+8, center[1]+8), 3)
            pygame.draw.line(
                self.screen, BLACK, (center[0]+8, center[1]-8), (center[0]-8, center[1]+8), 3)

        # Draw players
        for player in self.players:
            if not player.alive:
                continue
            color = player.color if show_roles else GRAY
            pygame.draw.circle(self.screen, color, (int(
                player.pos[0]), int(player.pos[1])), 14)
            pygame.draw.circle(self.screen, BLACK, (int(
                player.pos[0]), int(player.pos[1])), 14, 2)
            # Name tag
            role_text = "C" if player.role == 'crewmate' else "I"
            name_tag = f"{player.id}{role_text}" if show_roles else str(
                player.id)
            text = self.small_font.render(name_tag, True, BLACK)
            self.screen.blit(text, (player.pos[0]-10, player.pos[1]-25))

        # Mini-map
        if show_minimap:
            self.draw_minimap()

        # Status panel (top left)
        self.draw_status_panel()

        # Event log (bottom left)
        self.draw_event_log()

        # Meeting overlay
        if self.meeting:
            meeting_surf = self.big_font.render(
                "MEETING IN PROGRESS", True, RED)
            self.screen.blit(meeting_surf, (SCREEN_WIDTH//2 - 200, 50))

        # Game over overlay
        if self.game_over:
            overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            winner_text = self.big_font.render(
                f"{self.winner.upper()} WIN!", True, GREEN)
            self.screen.blit(winner_text, (SCREEN_WIDTH //
                             2 - 150, SCREEN_HEIGHT//2 - 30))

        pygame.display.flip()

    def draw_minimap(self):
        # Simple minimap in top-right corner
        mini_width, mini_height = 200, 150
        mini_x = SCREEN_WIDTH - mini_width - 20
        mini_y = 20
        pygame.draw.rect(self.screen, (50, 50, 50),
                         (mini_x, mini_y, mini_width, mini_height))
        pygame.draw.rect(self.screen, WHITE,
                         (mini_x, mini_y, mini_width, mini_height), 2)

        # Scale factor
        scale_x = mini_width / SCREEN_WIDTH
        scale_y = mini_height / SCREEN_HEIGHT
        for player in self.players:
            if player.alive:
                # even crewmates are blue on minimap? Or use role colors.
                color = player.color if player.role == 'impostor' else BLUE
                # Actually use actual colors if show_roles, else gray
                if not hasattr(self, 'show_roles_minimap') or self.show_roles_minimap:
                    color = player.color
                else:
                    color = GRAY
                x = mini_x + player.pos[0] * scale_x
                y = mini_y + player.pos[1] * scale_y
                pygame.draw.circle(self.screen, color, (int(x), int(y)), 4)

    def draw_status_panel(self):
        panel_x, panel_y = 20, 20
        panel_width = 200
        panel_height = 120
        pygame.draw.rect(self.screen, (50, 50, 50),
                         (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, WHITE,
                         (panel_x, panel_y, panel_width, panel_height), 2)

        lines = [
            f"Step: {self.step_count}",
            f"Tasks left: {self.tasks_remaining}",
            f"Alive: {sum(p.alive for p in self.players)}/{NUM_PLAYERS}",
            f"Crew: {sum(p.alive and p.role == 'crewmate' for p in self.players)}",
            f"Imp: {sum(p.alive and p.role == 'impostor' for p in self.players)}"
        ]
        y = panel_y + 10
        for line in lines:
            text = self.small_font.render(line, True, WHITE)
            self.screen.blit(text, (panel_x + 10, y))
            y += 20

    def draw_event_log(self):
        log_x, log_y = 20, SCREEN_HEIGHT - 200
        log_width = 400
        log_height = 180
        pygame.draw.rect(self.screen, (20, 20, 20),
                         (log_x, log_y, log_width, log_height))
        pygame.draw.rect(self.screen, WHITE,
                         (log_x, log_y, log_width, log_height), 2)

        y = log_y + 10
        for entry in list(self.event_log)[-MAX_LOG_ENTRIES:]:
            text = self.small_font.render(entry, True, WHITE)
            self.screen.blit(text, (log_x + 10, y))
            y += 20

# ----------------------------
# Main
# ----------------------------


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Among Us AI Spectator")
    clock = pygame.time.Clock()

    # Generate random networks for each player
    def create_random_networks():
        return [NeuralNetwork(INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE) for _ in range(NUM_PLAYERS)]

    networks = create_random_networks()
    game = Game(screen, networks)

    running = True
    paused = False
    step_mode = False
    show_roles = True
    show_minimap = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    if paused:
                        game.step()
                elif event.key == pygame.K_r:
                    # Restart with new random networks
                    networks = create_random_networks()
                    game = Game(screen, networks)
                elif event.key == pygame.K_s:
                    step_mode = not step_mode
                elif event.key == pygame.K_h:
                    show_roles = not show_roles
                elif event.key == pygame.K_m:
                    show_minimap = not show_minimap
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # Speed up (increase FPS target)
                    global FPS
                    FPS = min(120, FPS + 10)
                elif event.key == pygame.K_MINUS:
                    FPS = max(10, FPS - 10)

        if not paused:
            game.step()
            if step_mode:
                paused = True

        game.draw(show_roles, show_minimap)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
