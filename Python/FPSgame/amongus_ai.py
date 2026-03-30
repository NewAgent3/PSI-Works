import pygame
import random
import math
import json
import os
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict, Set
from collections import deque, defaultdict
import time

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Enhanced Colors
SPACE_BLACK = (10, 10, 20)
DEEP_SPACE = (15, 15, 30)
NEON_CYAN = (0, 255, 255)
NEON_PINK = (255, 20, 147)
NEON_GREEN = (57, 255, 20)
WARNING_RED = (255, 50, 50)
ELECTRIC_BLUE = (100, 150, 255)
GOLD = (255, 215, 0)

PLAYER_COLORS = [
    (197, 17, 17), (19, 46, 210), (17, 128, 45), (238, 84, 187),
    (240, 125, 13), (245, 245, 87), (107, 47, 188), (113, 73, 30),
    (56, 255, 221), (80, 240, 57),
]

PLAYER_NAMES = ["Red", "Blue", "Green", "Pink", "Orange",
                "Yellow", "Purple", "Brown", "Cyan", "Lime"]

# Learning data file
LEARNING_FILE = "ai_learning_data.json"


class GameState(Enum):
    INTRO = 0
    PLAYING = 1
    MEETING = 2
    VOTING = 3
    RESULTS = 4
    GAME_OVER = 5


@dataclass
class MatchHistory:
    """Store complete match data for learning"""
    winner: str  # "crewmate" or "imposter"
    imposter_name: str
    rounds_lasted: int
    kills_made: int
    correct_votes: int
    wrong_votes: int
    tasks_completed: int
    player_performances: Dict[str, Dict]
    successful_strategies: List[str]
    failed_strategies: List[str]
    timestamp: float


class AILearningSystem:
    """Advanced learning system that persists across matches"""

    def __init__(self):
        self.match_history: List[MatchHistory] = []
        self.strategy_success_rates = defaultdict(
            lambda: {"success": 0, "failure": 0})
        self.player_behavior_patterns = defaultdict(lambda: {
            "avg_task_time": 0,
            "preferred_rooms": [],
            "voting_accuracy": 0,
            "survival_rate": 0,
            "detection_rate": 0
        })
        self.meta_strategies = {
            "early_aggression": 0.5,
            "late_game_patience": 0.5,
            "evidence_weight": 0.6,
            "group_vs_solo": 0.5,
            "accusation_timing": 0.5
        }
        self.load_learning_data()

    def load_learning_data(self):
        """Load persistent learning data"""
        if os.path.exists(LEARNING_FILE):
            try:
                with open(LEARNING_FILE, 'r') as f:
                    data = json.load(f)
                    self.strategy_success_rates = defaultdict(lambda: {"success": 0, "failure": 0},
                                                              data.get("strategies", {}))
                    self.player_behavior_patterns = defaultdict(lambda: {
                        "avg_task_time": 0, "preferred_rooms": [],
                        "voting_accuracy": 0, "survival_rate": 0, "detection_rate": 0
                    }, data.get("behaviors", {}))
                    self.meta_strategies = data.get(
                        "meta_strategies", self.meta_strategies)

                    # Load match history
                    # Keep last 50 matches
                    for match_data in data.get("matches", [])[-50:]:
                        self.match_history.append(MatchHistory(**match_data))

                    print(
                        f"✓ Loaded learning data from {len(self.match_history)} previous matches")
            except Exception as e:
                print(f"⚠ Error loading learning data: {e}")

    def save_learning_data(self):
        """Save learning data to disk"""
        try:
            data = {
                "strategies": dict(self.strategy_success_rates),
                "behaviors": dict(self.player_behavior_patterns),
                "meta_strategies": self.meta_strategies,
                # Keep last 50
                "matches": [asdict(m) for m in self.match_history[-50:]]
            }
            with open(LEARNING_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(
                f"✓ Saved learning data from {len(self.match_history)} matches")
        except Exception as e:
            print(f"⚠ Error saving learning data: {e}")

    def record_match(self, match: MatchHistory):
        """Record match results and update strategies"""
        self.match_history.append(match)

        # Update strategy success rates
        for strategy in match.successful_strategies:
            self.strategy_success_rates[strategy]["success"] += 1
        for strategy in match.failed_strategies:
            self.strategy_success_rates[strategy]["failure"] += 1

        # Update meta-strategies based on outcomes
        if match.winner == "imposter":
            if match.kills_made > 3:
                self.meta_strategies["early_aggression"] += 0.02
            else:
                self.meta_strategies["late_game_patience"] += 0.02
        else:  # Crewmate win
            if match.correct_votes > match.wrong_votes:
                self.meta_strategies["evidence_weight"] += 0.02
            self.meta_strategies["early_aggression"] -= 0.01

        # Normalize meta-strategies
        for key in self.meta_strategies:
            self.meta_strategies[key] = max(
                0.1, min(0.9, self.meta_strategies[key]))

        self.save_learning_data()

    def get_strategy_confidence(self, strategy: str) -> float:
        """Get confidence score for a strategy (0-1)"""
        stats = self.strategy_success_rates[strategy]
        total = stats["success"] + stats["failure"]
        if total == 0:
            return 0.5  # Unknown strategy
        return stats["success"] / total

    def get_learned_behavior(self, player_name: str) -> Dict:
        """Get learned behavior patterns for a player"""
        return self.player_behavior_patterns[player_name]

    def should_use_aggressive_strategy(self) -> bool:
        """Determine if aggressive play is favored based on learning"""
        recent_wins = [m for m in self.match_history[-10:]
                       if m.winner == "imposter"]
        if len(recent_wins) > 5:
            avg_kills = sum(m.kills_made for m in recent_wins) / \
                len(recent_wins)
            return avg_kills > 2.5
        return self.meta_strategies["early_aggression"] > 0.6


class Particle:
    def __init__(self, x, y, color, vel_x=None, vel_y=None, life=60, size=None):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = vel_x if vel_x is not None else random.uniform(-2, 2)
        self.vel_y = vel_y if vel_y is not None else random.uniform(-2, 2)
        self.life = life
        self.max_life = life
        self.size = size if size is not None else random.randint(2, 5)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.life -= 1
        self.vel_y += 0.1

    def draw(self, screen):
        alpha = int(255 * (self.life / self.max_life))
        size = int(self.size * (self.life / self.max_life))
        if size > 0:
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (size, size), size)
            screen.blit(s, (int(self.x - size), int(self.y - size)))


@dataclass
class Room:
    name: str
    rect: pygame.Rect
    color: Tuple[int, int, int]
    has_task: bool = False
    has_vent: bool = False
    is_critical: bool = False
    traffic_count: int = 0


@dataclass
class Task:
    room: str
    name: str
    completed: bool = False
    progress: float = 0.0


@dataclass
class Evidence:
    type: str
    location: str
    suspect: str
    witness: str
    timestamp: int
    reliability: float
    context: str = ""


@dataclass
class SocialRelationship:
    """Track relationships between players"""
    player_a: str
    player_b: str
    trust: float = 0.5  # 0 = distrust, 1 = full trust
    interactions: int = 0
    seen_together: int = 0
    voted_same: int = 0
    voted_opposite: int = 0


class AdvancedMemory:
    """Sophisticated memory system for AI"""

    def __init__(self):
        self.short_term = deque(maxlen=15)  # Last 15 observations
        self.long_term: List[str] = []  # Important events
        self.spatial_memory: Dict[str, List[Tuple[str, int]]] = defaultdict(
            list)  # Who was where
        # Player relationships
        self.social_graph: Dict[str, SocialRelationship] = {}
        self.pattern_recognition: Dict[str, int] = defaultdict(
            int)  # Behavioral patterns
        self.confidence_levels: Dict[str, float] = defaultdict(lambda: 0.5)

    def observe(self, observation: str, importance: float = 0.5):
        """Add observation with importance weighting"""
        self.short_term.append(
            (observation, importance, pygame.time.get_ticks()))
        if importance > 0.7:
            self.long_term.append(observation)

    def remember_location(self, player: str, location: str, timestamp: int):
        """Remember who was where"""
        self.spatial_memory[location].append((player, timestamp))

    def get_alibi(self, player: str, time_range: Tuple[int, int]) -> Optional[str]:
        """Check if player has alibi for time range"""
        for location, entries in self.spatial_memory.items():
            for p, timestamp in entries:
                if p == player and time_range[0] <= timestamp <= time_range[1]:
                    return location
        return None

    def analyze_patterns(self) -> Dict[str, any]:
        """Analyze memory for patterns"""
        patterns = {
            "suspicious_players": [],
            "trusted_players": [],
            "suspicious_locations": [],
            "common_pairs": []
        }

        # Analyze suspicion patterns
        for player, confidence in self.confidence_levels.items():
            if confidence < 0.3:
                patterns["suspicious_players"].append(player)
            elif confidence > 0.7:
                patterns["trusted_players"].append(player)

        return patterns


class Player:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], name: str,
                 is_imposter: bool = False, learning_system: AILearningSystem = None):
        self.x = x
        self.y = y
        self.color = color
        self.name = name
        self.is_imposter = is_imposter
        self.alive = True
        self.tasks: List[Task] = []
        self.speed = 2.5
        self.target_x = x
        self.target_y = y
        self.current_room = None
        self.previous_room = None
        self.time_in_room = 0
        self.suspicion_level = 0
        self.vote = None
        self.voted_for_history = []

        # Advanced AI attributes
        self.memory = AdvancedMemory()
        self.learning_system = learning_system
        self.personality_traits = self._generate_personality()
        # "aggressive", "defensive", "deceptive", "analytical"
        self.strategic_mode = "neutral"
        self.kill_count = 0
        self.correct_accusations = 0
        self.wrong_accusations = 0
        self.tasks_completed_count = 0

        # Behavioral learning
        self.preferred_kill_locations: List[str] = []
        self.safe_rooms: List[str] = []
        self.dangerous_rooms: List[str] = []
        self.trusted_players: Set[str] = set()
        self.suspected_players: Set[str] = set()

        # Social deduction
        self.social_network: Dict[str, SocialRelationship] = {}
        self.voting_confidence = 0.5

        # Performance tracking
        self.decision_history = []
        self.strategies_used = []

        # Visual
        self.animation_offset = 0
        self.glow_intensity = 0
        self.trail = deque(maxlen=15)
        self.thought_bubble = None
        self.thought_timer = 0

    def _generate_personality(self) -> Dict:
        """Generate unique personality with learned preferences"""
        base_personalities = {
            "aggression": random.uniform(0.2, 0.8),
            "caution": random.uniform(0.2, 0.8),
            "social": random.uniform(0.3, 0.9),
            "analytical": random.uniform(0.3, 0.9),
            "deception_skill": random.uniform(0.3, 0.9),
            "pattern_recognition": random.uniform(0.4, 0.9),
            "risk_tolerance": random.uniform(0.2, 0.8),
            "evidence_weighting": random.uniform(0.4, 0.9)
        }

        # Adjust based on learning if available
        if self.learning_system:
            learned = self.learning_system.get_learned_behavior(self.name)
            if learned.get("survival_rate", 0) > 0.7:
                base_personalities["caution"] += 0.1
            if learned.get("detection_rate", 0) > 0.6:
                base_personalities["deception_skill"] += 0.1

        return base_personalities

    def update_social_network(self, other_player: str, interaction_type: str):
        """Update social relationship with another player"""
        key = f"{self.name}_{other_player}"
        if key not in self.social_network:
            self.social_network[key] = SocialRelationship(
                self.name, other_player)

        rel = self.social_network[key]
        rel.interactions += 1

        if interaction_type == "seen_together":
            rel.seen_together += 1
            rel.trust += 0.05
        elif interaction_type == "voted_same":
            rel.voted_same += 1
            rel.trust += 0.1
        elif interaction_type == "voted_opposite":
            rel.voted_opposite += 1
            rel.trust -= 0.15
        elif interaction_type == "suspicious":
            rel.trust -= 0.2

        rel.trust = max(0, min(1, rel.trust))

    def get_trust_level(self, other_player: str) -> float:
        """Get trust level for another player"""
        key = f"{self.name}_{other_player}"
        if key in self.social_network:
            return self.social_network[key].trust
        return 0.5  # Neutral

    def analyze_game_state(self, all_players: List['Player'], dead_bodies: List) -> Dict:
        """Deep analysis of current game state"""
        alive_players = [p for p in all_players if p.alive and p != self]

        analysis = {
            "threat_level": 0.0,
            "safest_location": None,
            "most_suspicious": None,
            "should_call_meeting": False,
            "optimal_strategy": "neutral",
            "confidence": self.voting_confidence
        }

        # Threat assessment
        if len(alive_players) <= 4:
            analysis["threat_level"] = 0.8
        elif len(dead_bodies) > 3:
            analysis["threat_level"] = 0.6
        else:
            analysis["threat_level"] = 0.3

        # Find most suspicious player based on evidence and memory
        patterns = self.memory.analyze_patterns()
        if patterns["suspicious_players"]:
            analysis["most_suspicious"] = patterns["suspicious_players"][0]

        # Strategic mode selection
        if self.is_imposter:
            if len(alive_players) <= 3:
                analysis["optimal_strategy"] = "aggressive"
            elif self.kill_count == 0 and self.learning_system:
                if self.learning_system.should_use_aggressive_strategy():
                    analysis["optimal_strategy"] = "aggressive"
                else:
                    analysis["optimal_strategy"] = "deceptive"
            else:
                analysis["optimal_strategy"] = "deceptive"
        else:
            if len(self.memory.short_term) > 10:
                analysis["optimal_strategy"] = "analytical"
            else:
                analysis["optimal_strategy"] = "defensive"

        return analysis

    def assign_tasks(self, rooms: List[Room], num_tasks: int = 4):
        """Assign tasks with learning-based preferences"""
        task_rooms = [room for room in rooms if room.has_task]

        # Prefer rooms with lower traffic (safer)
        if self.personality_traits["caution"] > 0.6:
            task_rooms.sort(key=lambda r: r.traffic_count)

        selected_rooms = random.sample(
            task_rooms, min(num_tasks, len(task_rooms)))
        task_types = ["Wiring", "Download", "Scan", "Fuel",
                      "Charts", "Samples", "Diagnostics", "Align"]
        self.tasks = [Task(room.name, f"{random.choice(task_types)} in {room.name}")
                      for room in selected_rooms]

    def move_towards_target(self, rooms: List[Room]):
        """Enhanced movement with spatial awareness"""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance > 3:
            move_speed = min(self.speed, distance * 0.1)
            self.x += (dx / distance) * move_speed
            self.y += (dy / distance) * move_speed

            if len(self.trail) == 0 or (abs(self.trail[-1][0] - self.x) > 5 or abs(self.trail[-1][1] - self.y) > 5):
                self.trail.append((self.x, self.y))
        else:
            self.x = self.target_x
            self.y = self.target_y

        self.animation_offset = math.sin(pygame.time.get_ticks() * 0.005) * 2
        self.update_current_room(rooms)

    def update_current_room(self, rooms: List[Room]):
        """Update room tracking with memory"""
        self.previous_room = self.current_room
        self.current_room = None

        for room in rooms:
            if room.rect.collidepoint(int(self.x), int(self.y)):
                self.current_room = room.name
                room.traffic_count += 1

                if self.previous_room != self.current_room:
                    self.time_in_room = 0
                    self.memory.remember_location(
                        self.name, self.current_room, pygame.time.get_ticks())

                    # Learn room safety
                    if self.current_room not in self.safe_rooms and random.random() < 0.3:
                        self.safe_rooms.append(self.current_room)
                break

        if self.current_room:
            self.time_in_room += 1

    def draw(self, screen: pygame.Surface, particles: List[Particle], camera_shake=0):
        """Enhanced drawing with thought bubbles"""
        shake_x = random.randint(-camera_shake, camera_shake)
        shake_y = random.randint(-camera_shake, camera_shake)

        draw_x = int(self.x) + shake_x
        draw_y = int(self.y) + shake_y + self.animation_offset

        if self.alive:
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 * (i / len(self.trail)))
                s = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, alpha), (4, 4), 4)
                screen.blit(s, (int(tx) - 4 + shake_x, int(ty) - 4 + shake_y))

            # Glow
            if self.glow_intensity > 0:
                glow_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow_surface, (*self.color, int(self.glow_intensity)), (30, 30), 30)
                screen.blit(glow_surface, (draw_x - 30, draw_y - 30),
                            special_flags=pygame.BLEND_ADD)
                self.glow_intensity = max(0, self.glow_intensity - 5)

            # Shadow
            shadow_surf = pygame.Surface((40, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, 40, 20))
            screen.blit(shadow_surf, (draw_x - 20, draw_y + 15))

            # Body with gradient
            body_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            for i in range(18, 0, -1):
                alpha = int(255 * (i / 18))
                pygame.draw.circle(
                    body_surf, (*self.color, alpha), (20, 20), i)
            screen.blit(body_surf, (draw_x - 20, draw_y - 20))

            # Visor
            pygame.draw.ellipse(screen, ELECTRIC_BLUE,
                                (draw_x - 10, draw_y - 8, 15, 10))
            pygame.draw.ellipse(screen, (200, 230, 255),
                                (draw_x - 8, draw_y - 7, 6, 4))

            # Backpack
            pygame.draw.circle(screen, self.color, (draw_x + 10, draw_y), 10)
            pygame.draw.circle(screen, tuple(max(0, c - 40)
                               for c in self.color), (draw_x + 12, draw_y + 2), 8)

            # Suspicion indicator
            if self.suspicion_level > 60:
                pygame.draw.circle(screen, WARNING_RED,
                                   (draw_x, draw_y - 25), 6)
                pygame.draw.circle(screen, (255, 255, 100),
                                   (draw_x, draw_y - 25), 4)

            # Thought bubble
            if self.thought_bubble and self.thought_timer > 0:
                font = pygame.font.Font(None, 16)
                thought = font.render(
                    self.thought_bubble, True, (255, 255, 255))
                bubble_bg = pygame.Surface(
                    (thought.get_width() + 10, thought.get_height() + 6), pygame.SRCALPHA)
                pygame.draw.ellipse(bubble_bg, (50, 50, 80, 200), (0, 0, thought.get_width(
                ) + 10, thought.get_height() + 6))
                screen.blit(
                    bubble_bg, (draw_x - thought.get_width() // 2 - 5, draw_y - 45))
                screen.blit(
                    thought, (draw_x - thought.get_width() // 2, draw_y - 42))
                self.thought_timer -= 1

        else:
            # Dead body (enhanced)
            for _ in range(5):
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                pygame.draw.circle(
                    screen, (180, 0, 0), (draw_x + offset_x, draw_y + offset_y), random.randint(2, 6))

            pygame.draw.circle(screen, self.color, (draw_x, draw_y), 15)
            pygame.draw.circle(screen, self.color,
                               (draw_x + 12, draw_y - 8), 10)
            pygame.draw.polygon(screen, self.color, [
                (draw_x - 5, draw_y + 10), (draw_x -
                                            15, draw_y + 20), (draw_x, draw_y + 15)
            ])
            pygame.draw.line(screen, (240, 240, 240), (draw_x +
                             15, draw_y + 5), (draw_x + 25, draw_y + 15), 3)

        # Name tag
        font = pygame.font.Font(None, 20)
        name_text = font.render(self.name, True, (255, 255, 255))
        name_bg = pygame.Surface(
            (name_text.get_width() + 10, name_text.get_height() + 4), pygame.SRCALPHA)
        pygame.draw.rect(name_bg, (0, 0, 0, 180), (0, 0, name_text.get_width(
        ) + 10, name_text.get_height() + 4), border_radius=5)
        screen.blit(
            name_bg, (draw_x - name_text.get_width() // 2 - 5, draw_y - 40))
        screen.blit(
            name_text, (draw_x - name_text.get_width() // 2, draw_y - 38))


class SuperIntelligentAI:
    """Ultra-advanced AI with deep learning and meta-cognition"""

    def __init__(self, player: Player, learning_system: AILearningSystem):
        self.player = player
        self.learning_system = learning_system
        self.next_action_time = random.randint(40, 120)
        self.target_player = None
        self.current_strategy = "observe"
        self.strategy_confidence = 0.5
        self.kill_opportunities_missed = 0
        self.deception_attempts = 0
        self.rooms = []  # Will be updated during decide_action

    def think(self, all_players: List[Player], rooms: List[Room], dead_bodies: List) -> str:
        """Meta-cognitive thinking process"""
        # Analyze game state
        analysis = self.player.analyze_game_state(all_players, dead_bodies)

        # Update strategic mode based on analysis
        self.player.strategic_mode = analysis["optimal_strategy"]
        self.strategy_confidence = analysis["confidence"]

        # Generate thought
        if self.player.is_imposter:
            if analysis["threat_level"] > 0.7:
                return "Need to act fast..."
            elif self.kill_opportunities_missed > 2:
                return "Too cautious..."
            else:
                return "Blend in..."
        else:
            if analysis["most_suspicious"]:
                return f"Sus: {analysis['most_suspicious']}"
            return "Observe..."

    def observe_environment(self, other_players: List[Player], dead_bodies: List):
        """Advanced environmental observation with pattern recognition"""
        if not self.player.alive:
            return

        current_time = pygame.time.get_ticks()

        # Observe nearby players with context
        for other in other_players:
            if other.alive and other != self.player:
                distance = math.sqrt(
                    (self.player.x - other.x)**2 + (self.player.y - other.y)**2)

                if distance < 150:
                    # Record observation with importance
                    importance = 0.5
                    context = f"Saw {other.name} in {other.current_room}"

                    # Increase importance if suspicious
                    if other.current_room in ["Electrical", "Security"] and len(dead_bodies) > 0:
                        importance = 0.8
                        context += " (suspicious location)"

                    self.player.memory.observe(context, importance)
                    self.player.memory.remember_location(
                        other.name, other.current_room or "hallway", current_time)

                    # Update social network
                    self.player.update_social_network(
                        other.name, "seen_together")

                    # Pattern recognition
                    if other.is_imposter and not self.player.is_imposter:
                        # Crewmate detecting imposter behavior patterns
                        if hasattr(other, 'kill_count') and other.kill_count > 0:
                            if distance < 100:
                                self.player.memory.observe(
                                    f"{other.name} acting nervous", 0.7)
                                self.player.suspected_players.add(other.name)

        # Observe bodies
        for bx, by, color in dead_bodies:
            distance = math.sqrt((self.player.x - bx) **
                                 2 + (self.player.y - by)**2)
            if distance < 100:
                self.player.memory.observe(
                    f"Found body in {self.player.current_room}", 0.9)

                # Check for nearby suspicious players
                for other in other_players:
                    if other.alive and other != self.player:
                        other_dist = math.sqrt(
                            (other.x - bx)**2 + (other.y - by)**2)
                        if other_dist < 150:
                            evidence = Evidence(
                                type="saw_near_body",
                                location=self.player.current_room or "unknown",
                                suspect=other.name,
                                witness=self.player.name,
                                timestamp=current_time,
                                reliability=0.8,
                                context=f"Saw {other.name} near body"
                            )
                            # Store as memory
                            self.player.memory.observe(evidence.context, 0.9)
                            self.player.suspected_players.add(other.name)

    def decide_action(self, rooms: List[Room], other_players: List[Player], dead_bodies: List):
        """Advanced decision-making with learning integration"""
        if not self.player.alive:
            return

        self.observe_environment(other_players, dead_bodies)
        self.next_action_time -= 1

        # Update thought bubble
        self.player.thought_bubble = self.think(
            other_players, rooms, dead_bodies)
        self.player.thought_timer = 60

        # Store rooms for later use
        self.rooms = rooms

        if self.next_action_time <= 0:
            if self.player.is_imposter:
                self.imposter_meta_strategy(other_players, rooms, dead_bodies)
            else:
                self.crewmate_meta_strategy(rooms, other_players, dead_bodies)

            self.next_action_time = random.randint(60, 180)

    def crewmate_meta_strategy(self, rooms: List[Room], other_players: List[Player], dead_bodies: List):
        """Meta-strategic crewmate behavior"""
        incomplete_tasks = [
            task for task in self.player.tasks if not task.completed]

        # Analytical mode - prioritize evidence gathering
        if self.player.strategic_mode == "analytical":
            # Visit high-traffic areas to observe
            high_traffic_rooms = sorted(
                rooms, key=lambda r: r.traffic_count, reverse=True)[:3]
            target_room = random.choice(high_traffic_rooms)
            self.player.target_x = target_room.rect.centerx + \
                random.randint(-25, 25)
            self.player.target_y = target_room.rect.centery + \
                random.randint(-25, 25)
            self.player.strategies_used.append("evidence_gathering")
            return

        # Defensive mode - stick with groups
        if self.player.strategic_mode == "defensive":
            alive_others = [
                p for p in other_players if p.alive and p != self.player]
            if alive_others:
                # Find closest player
                closest = min(alive_others, key=lambda p: math.sqrt(
                    (self.player.x - p.x)**2 + (self.player.y - p.y)**2))
                self.player.target_x = closest.target_x + \
                    random.randint(-30, 30)
                self.player.target_y = closest.target_y + \
                    random.randint(-30, 30)
                self.player.strategies_used.append("group_safety")
                return

        # Default: Complete tasks
        if incomplete_tasks and random.random() < 0.7:
            task = random.choice(incomplete_tasks)
            task_room = next(
                (room for room in rooms if room.name == task.room), None)
            if task_room:
                self.player.target_x = task_room.rect.centerx + \
                    random.randint(-25, 25)
                self.player.target_y = task_room.rect.centery + \
                    random.randint(-25, 25)
                self.player.strategies_used.append("task_completion")
        else:
            # Explore safely
            safe_rooms = [r for r in rooms if r.traffic_count > 5] or rooms
            target = random.choice(safe_rooms)
            self.player.target_x = target.rect.centerx + \
                random.randint(-30, 30)
            self.player.target_y = target.rect.centery + \
                random.randint(-30, 30)

    def imposter_meta_strategy(self, other_players: List[Player], rooms: List[Room], dead_bodies: List):
        """Meta-strategic imposter behavior with learning"""
        alive_crewmates = [
            p for p in other_players if p.alive and not p.is_imposter]

        # Learn from past matches
        use_aggressive = self.learning_system.should_use_aggressive_strategy()

        # Aggressive mode - hunt aggressively
        if self.player.strategic_mode == "aggressive" or use_aggressive:
            if alive_crewmates:
                # Target isolated players
                isolated = []
                for crew in alive_crewmates:
                    nearby_count = sum(1 for p in other_players if p.alive and p != crew
                                       and math.sqrt((p.x - crew.x)**2 + (p.y - crew.y)**2) < 150)
                    if nearby_count == 0:
                        isolated.append(crew)

                if isolated:
                    target = random.choice(isolated)
                    self.player.target_x = target.x + random.randint(-40, 40)
                    self.player.target_y = target.y + random.randint(-40, 40)
                    self.target_player = target
                    self.player.strategies_used.append("aggressive_hunt")
                    return

        # Deceptive mode - blend in perfectly
        if self.player.strategic_mode == "deceptive":
            # Mimic crewmate behavior
            task_rooms = [r for r in rooms if r.has_task]
            if task_rooms:
                target = random.choice(task_rooms)
                self.player.target_x = target.rect.centerx + \
                    random.randint(-25, 25)
                self.player.target_y = target.rect.centery + \
                    random.randint(-25, 25)
                self.player.strategies_used.append("deceptive_blending")
                return

        # Default: Act natural
        target_room = random.choice(rooms)
        self.player.target_x = target_room.rect.centerx + \
            random.randint(-30, 30)
        self.player.target_y = target_room.rect.centery + \
            random.randint(-30, 30)

    def attempt_kill(self, other_players: List[Player], kill_cooldown: dict, particles: List[Particle], rooms: List[Room]) -> Optional[Player]:
        """Intelligent kill decision with risk assessment"""
        if not self.player.is_imposter or not self.player.alive:
            return None

        current_time = pygame.time.get_ticks()
        if current_time - kill_cooldown.get(self.player.name, 0) < 15000:
            return None

        best_target = None
        lowest_risk = float('inf')

        for other in other_players:
            if other.alive and not other.is_imposter:
                distance = math.sqrt(
                    (self.player.x - other.x)**2 + (self.player.y - other.y)**2)

                if distance < 45:
                    # Calculate risk
                    witnesses = [p for p in other_players if p.alive and p != other and p != self.player
                                 and math.sqrt((p.x - other.x)**2 + (p.y - other.y)**2) < 120]

                    witness_count = len(witnesses)
                    # Get room traffic safely
                    room_traffic = 10  # Default
                    if other.current_room:
                        matching_room = next(
                            (r for r in rooms if r.name == other.current_room), None)
                        if matching_room:
                            room_traffic = matching_room.traffic_count

                    # Risk calculation
                    risk = witness_count * 10 + (room_traffic / 5)

                    # Adjust risk based on personality
                    risk_threshold = self.player.personality_traits["risk_tolerance"] * 20

                    if risk < risk_threshold and risk < lowest_risk:
                        lowest_risk = risk
                        best_target = other

        if best_target:
            # Decide to kill based on learning
            kill_confidence = self.learning_system.get_strategy_confidence(
                "early_kill")

            if self.player.strategic_mode == "aggressive":
                kill_chance = 0.7
            elif self.player.strategic_mode == "deceptive" and lowest_risk < 5:
                kill_chance = 0.4
            else:
                kill_chance = 0.2

            # Factor in learned confidence
            kill_chance *= (0.5 + kill_confidence * 0.5)

            if random.random() < kill_chance:
                best_target.alive = False
                kill_cooldown[self.player.name] = current_time
                self.player.kill_count += 1
                self.player.strategies_used.append("calculated_kill")

                # Particles
                for _ in range(40):
                    particles.append(Particle(
                        best_target.x, best_target.y,
                        (255, 0, 0),
                        random.uniform(-4, 4),
                        random.uniform(-5, -1),
                        random.randint(40, 80)
                    ))

                # Update memory
                self.player.memory.observe(
                    f"Eliminated {best_target.name} in {self.player.current_room}", 0.9)

                return best_target
            else:
                self.kill_opportunities_missed += 1

        return None

    def vote_with_intelligence(self, all_players: List[Player]) -> str:
        """Advanced voting logic with evidence weighting"""
        alive_players = [p for p in all_players if p.alive]

        if self.player.is_imposter:
            return self._imposter_vote(alive_players)
        else:
            return self._crewmate_vote(alive_players)

    def _crewmate_vote(self, alive_players: List[Player]) -> str:
        """Evidence-based crewmate voting"""
        # Analyze all evidence
        suspicion_scores = defaultdict(float)

        # Check memory for suspicious behavior
        patterns = self.player.memory.analyze_patterns()
        for suspect in patterns["suspicious_players"]:
            suspicion_scores[suspect] += 30

        # Check suspected players set
        for suspect in self.player.suspected_players:
            suspicion_scores[suspect] += 25

        # Check social trust network
        for other in alive_players:
            if other != self.player:
                trust = self.player.get_trust_level(other.name)
                if trust < 0.3:
                    suspicion_scores[other.name] += 20
                elif trust > 0.7:
                    suspicion_scores[other.name] -= 15

        # Weight by personality
        evidence_weight = self.player.personality_traits["evidence_weighting"]
        for player_name in suspicion_scores:
            suspicion_scores[player_name] *= evidence_weight

        # Make decision
        if suspicion_scores:
            top_suspect = max(suspicion_scores, key=suspicion_scores.get)
            if suspicion_scores[top_suspect] > 25:
                self.player.voting_confidence = min(
                    0.9, suspicion_scores[top_suspect] / 100)
                self.player.strategies_used.append("evidence_based_vote")
                return top_suspect

        # Not enough evidence - use learning
        if self.player.personality_traits["analytical"] > 0.6:
            # Skip if uncertain
            self.player.strategies_used.append("analytical_skip")
            return "skip"
        else:
            # Random guess
            others = [p.name for p in alive_players if p != self.player]
            if others:
                self.player.strategies_used.append("uncertain_guess")
                return random.choice(others)

        return "skip"

    def _imposter_vote(self, alive_players: List[Player]) -> str:
        """Strategic imposter voting"""
        crewmates = [p for p in alive_players if not p.is_imposter]

        if not crewmates:
            return "skip"

        # Find most suspicious crewmate to blend votes
        target = max(crewmates, key=lambda p: p.suspicion_level)

        # Sometimes vote for someone with high trust to seem innocent
        if random.random() < 0.3 and self.player.personality_traits["deception_skill"] > 0.6:
            trusted = [
                p for p in crewmates if self.player.get_trust_level(p.name) > 0.6]
            if trusted:
                target = random.choice(trusted)
                self.player.strategies_used.append("deceptive_vote")
        else:
            self.player.strategies_used.append("strategic_vote")

        return target.name


class AmongUsGame:
    """Main game with advanced learning system"""

    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Among Us - ULTIMATE AI Learning Edition")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 42)
        self.font_huge = pygame.font.Font(None, 72)

        # Learning system
        self.learning_system = AILearningSystem()

        # Game state
        self.state = GameState.INTRO
        self.intro_timer = 0
        self.players: List[Player] = []
        self.ais: List[SuperIntelligentAI] = []
        self.rooms: List[Room] = []
        self.dead_bodies = []
        self.kill_cooldown = {}
        self.meeting_timer = 0
        self.meeting_messages = []
        self.votes = {}
        self.voting_timer = 0
        self.game_over_message = ""
        self.particles: List[Particle] = []
        self.camera_shake = 0
        self.background_stars = [(random.randint(0, WINDOW_WIDTH),
                                 random.randint(0, WINDOW_HEIGHT),
                                 random.randint(1, 3)) for _ in range(100)]

        # Match tracking
        self.match_start_time = time.time()
        self.rounds_played = 0
        self.kills_this_match = 0
        self.correct_votes_this_match = 0
        self.wrong_votes_this_match = 0

        self.setup_rooms()
        self.setup_players()
        self.imposter = next(p for p in self.players if p.is_imposter)

        # Ambient particles
        for _ in range(50):
            self.particles.append(Particle(
                random.randint(0, 700), random.randint(0, 720),
                (100, 100, 150),
                random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5),
                999999, random.randint(1, 3)
            ))

    def setup_rooms(self):
        """Create map scaled for 720p"""
        # Scaled down rooms (about 76% of original size)
        self.rooms = [
            Room("Cafeteria", pygame.Rect(40, 230, 165, 135),
                 (120, 120, 140), True, False, False),
            Room("Weapons", pygame.Rect(25, 40, 130, 135),
                 (160, 80, 80), True, True, False),
            Room("O2", pygame.Rect(190, 40, 135, 100),
                 (80, 130, 180), True, False, True),
            Room("Navigation", pygame.Rect(365, 25, 135, 115),
                 (130, 180, 80), True, True, False),
            Room("Shields", pygame.Rect(540, 30, 115, 135),
                 (180, 130, 70), True, False, True),
            Room("Communications", pygame.Rect(540, 210, 135, 90),
                 (80, 180, 130), True, True, True),
            Room("Storage", pygame.Rect(245, 230, 135, 135),
                 (170, 170, 80), True, False, False),
            Room("Electrical", pygame.Rect(420, 230, 120, 115),
                 (200, 140, 40), True, True, True),
            Room("Lower Engine", pygame.Rect(25, 400, 135, 115),
                 (130, 80, 180), True, True, False),
            Room("Upper Engine", pygame.Rect(540, 365, 135, 115),
                 (180, 80, 130), True, True, False),
            Room("Security", pygame.Rect(245, 400, 115, 100),
                 (80, 200, 130), True, False, True),
            Room("Medbay", pygame.Rect(395, 395, 120, 115),
                 (80, 180, 180), True, False, False),
            Room("Admin", pygame.Rect(420, 135, 105, 75),
                 (150, 150, 150), True, False, True),
        ]

    def setup_players(self):
        """Create players with learning system"""
        num_players = 10
        imposter_index = random.randint(0, num_players - 1)

        # Adjusted spawn for scaled map
        spawn_x, spawn_y = 115, 295
        spawn_radius = 30

        for i in range(num_players):
            angle = (i / num_players) * 2 * math.pi
            x = spawn_x + math.cos(angle) * spawn_radius
            y = spawn_y + math.sin(angle) * spawn_radius

            is_imposter = (i == imposter_index)
            player = Player(
                x, y, PLAYER_COLORS[i], PLAYER_NAMES[i], is_imposter, self.learning_system)

            if not is_imposter:
                player.assign_tasks(self.rooms, 4)

            self.players.append(player)
            self.ais.append(SuperIntelligentAI(player, self.learning_system))

    def update(self):
        """Main update"""
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()

        self.camera_shake = max(0, self.camera_shake - 1)

        if self.state == GameState.INTRO:
            self.update_intro()
        elif self.state == GameState.PLAYING:
            self.update_playing()
        elif self.state == GameState.MEETING:
            self.update_meeting()
        elif self.state == GameState.VOTING:
            self.update_voting()
        elif self.state == GameState.RESULTS:
            self.update_results()

    def update_intro(self):
        """Intro with learning stats"""
        self.intro_timer += 1
        if self.intro_timer > 300:  # 5 seconds to show learning stats
            self.state = GameState.PLAYING

    def update_playing(self):
        """Enhanced gameplay"""
        for i, player in enumerate(self.players):
            if player.alive:
                player.move_towards_target(self.rooms)
                self.ais[i].decide_action(
                    self.rooms, self.players, self.dead_bodies)

                # Complete tasks
                if player.current_room and not player.is_imposter:
                    for task in player.tasks:
                        if task.room == player.current_room and not task.completed:
                            task.progress += 0.016
                            if task.progress >= 1.0:
                                task.completed = True
                                player.tasks_completed_count += 1
                                player.glow_intensity = 100

                                for _ in range(15):
                                    self.particles.append(Particle(
                                        player.x, player.y, NEON_GREEN,
                                        random.uniform(-2,
                                                       2), random.uniform(-3, -1), 40, 4
                                    ))

        # Imposters try kills
        for i, player in enumerate(self.players):
            if player.is_imposter and player.alive:
                killed = self.ais[i].attempt_kill(
                    self.players, self.kill_cooldown, self.particles, self.rooms)
                if killed:
                    self.camera_shake = 10
                    self.kills_this_match += 1
                    self.dead_bodies.append((killed.x, killed.y, killed.color))

        # Random meetings (rare)
        if random.random() < 0.0002 and len([p for p in self.players if p.alive]) > 3:
            caller = random.choice([p for p in self.players if p.alive])
            self.start_meeting(
                f"{caller.name} called emergency meeting!", caller)

        # Body discovery
        for player in self.players:
            if player.alive:
                for bx, by, _ in self.dead_bodies:
                    distance = math.sqrt(
                        (player.x - bx)**2 + (player.y - by)**2)
                    if distance < 50 and random.random() < 0.008:
                        self.start_meeting(
                            f"{player.name} reported a body!", player)
                        return

        self.check_win_condition()

    def update_meeting(self):
        """Meeting phase"""
        self.meeting_timer += 1

        if self.meeting_timer == 30:
            self.generate_ai_discussion()

        if self.meeting_timer > 480:  # 8 seconds
            self.state = GameState.VOTING
            self.voting_timer = 0

    def update_voting(self):
        """Voting with AI intelligence"""
        self.voting_timer += 1

        if self.voting_timer == 60:
            self.ai_intelligent_vote()

        if self.voting_timer > 300:
            self.state = GameState.RESULTS
            self.meeting_timer = 0

    def update_results(self):
        """Results phase"""
        self.meeting_timer += 1

        if self.meeting_timer > 240:
            self.count_votes_and_learn()

    def start_meeting(self, reason: str, caller: Player = None):
        """Start meeting"""
        self.state = GameState.MEETING
        self.meeting_timer = 0
        self.meeting_messages = [f"🚨 {reason}"]
        self.votes = {}
        self.rounds_played += 1

        self.camera_shake = 15
        for _ in range(50):
            self.particles.append(Particle(400, 400, WARNING_RED,
                                           random.uniform(-5, 5), random.uniform(-5, 5), 60, 6))

        # Teleport to cafeteria
        cafeteria = next(
            (r for r in self.rooms if r.name == "Cafeteria"), None)
        for player in self.players:
            if player.alive:
                player.target_x = cafeteria.rect.centerx + \
                    random.randint(-50, 50)
                player.target_y = cafeteria.rect.centery + \
                    random.randint(-50, 50)
                player.x = player.target_x
                player.y = player.target_y

    def generate_ai_discussion(self):
        """AI generates intelligent discussion"""
        alive = [p for p in self.players if p.alive]

        speakers = random.sample(alive, min(6, len(alive)))

        for speaker in speakers:
            ai = next(ai for ai in self.ais if ai.player == speaker)

            if speaker.is_imposter:
                # Imposter uses deception
                strategies = [
                    self._imposter_deflect,
                    self._imposter_alibi,
                    self._imposter_accuse
                ]
                random.choice(strategies)(speaker, alive)
            else:
                # Crewmate shares analysis
                self._crewmate_analysis(speaker, alive)

    def _imposter_deflect(self, imp: Player, alive: List[Player]):
        innocents = [p for p in alive if not p.is_imposter]
        if innocents:
            target = random.choice(innocents)
            self.meeting_messages.append(
                f"{imp.name}: {target.name} was acting really sus! 🤨")

    def _imposter_alibi(self, imp: Player):
        fake_room = random.choice(self.rooms).name
        self.meeting_messages.append(
            f"{imp.name}: I was doing tasks in {fake_room} 💯")

    def _imposter_accuse(self, imp: Player, alive: List[Player]):
        innocents = [p for p in alive if not p.is_imposter]
        if innocents:
            target = max(innocents, key=lambda p: p.suspicion_level)
            self.meeting_messages.append(
                f"{imp.name}: Vote {target.name}, trust me! ⚠️")

    def _crewmate_analysis(self, crew: Player, alive: List[Player]):
        if crew.suspected_players:
            suspect = random.choice(list(crew.suspected_players))
            confidence = int(crew.voting_confidence * 100)
            self.meeting_messages.append(
                f"{crew.name}: {suspect} is sus ({confidence}% sure) 👀")
        elif crew.memory.short_term:
            memory = random.choice(list(crew.memory.short_term))
            self.meeting_messages.append(f"{crew.name}: {memory[0]}")
        else:
            self.meeting_messages.append(f"{crew.name}: Not sure yet... 🤔")

    def ai_intelligent_vote(self):
        """AI uses intelligence to vote"""
        alive = [p for p in self.players if p.alive]

        for i, player in enumerate(alive):
            vote = self.ais[i].vote_with_intelligence(self.players)
            player.vote = vote
            self.votes[player.name] = vote

    def count_votes_and_learn(self):
        """Count votes and update learning"""
        vote_counts = defaultdict(int)

        self.meeting_messages.append("--- VOTES ---")
        for voter, voted in self.votes.items():
            vote_counts[voted] += 1
            self.meeting_messages.append(f"{voter} → {voted}")

        ejected = None
        if vote_counts:
            max_votes = max(vote_counts.values())
            top = [name for name, count in vote_counts.items() if count ==
                   max_votes]

            if len(top) == 1 and top[0] != "skip":
                ejected_name = top[0]
                ejected = next(
                    (p for p in self.players if p.name == ejected_name), None)
                if ejected:
                    was_imposter = ejected.is_imposter
                    ejected.alive = False
                    role = "❌ IMPOSTER" if was_imposter else "✓ CREWMATE"

                    self.meeting_messages.append("")
                    self.meeting_messages.append(
                        f"💀 {ejected_name} was ejected.")
                    self.meeting_messages.append(f"{ejected_name} was {role}")

                    # Track voting accuracy
                    for voter_name, voted_name in self.votes.items():
                        if voted_name == ejected_name:
                            voter = next(
                                p for p in self.players if p.name == voter_name)
                            if was_imposter:
                                voter.correct_accusations += 1
                                self.correct_votes_this_match += 1
                            else:
                                voter.wrong_accusations += 1
                                self.wrong_votes_this_match += 1

                    # Ejection particles
                    for _ in range(100):
                        self.particles.append(Particle(
                            ejected.x, ejected.y, ejected.color,
                            random.uniform(-8, 8), random.uniform(-8, 8),
                            random.randint(60, 120), random.randint(4, 8)
                        ))
            else:
                self.meeting_messages.append("⏭️ No one ejected")

        self.state = GameState.PLAYING
        self.check_win_condition()

    def check_win_condition(self):
        """Check win and trigger learning"""
        alive = [p for p in self.players if p.alive]
        alive_imp = [p for p in alive if p.is_imposter]
        alive_crew = [p for p in alive if not p.is_imposter]

        winner = None

        if len(alive_imp) >= len(alive_crew) and len(alive_crew) > 0:
            winner = "imposter"
            self.game_over_message = "💀 IMPOSTERS WIN!"
        elif len(alive_imp) == 0:
            winner = "crewmate"
            self.game_over_message = "✓ CREWMATES WIN!"
        else:
            # Task win
            all_tasks = [
                t for p in self.players if not p.is_imposter for t in p.tasks]
            if all_tasks and all(t.completed for t in all_tasks):
                winner = "crewmate"
                self.game_over_message = "✓ TASKS COMPLETED!"

        if winner:
            self.state = GameState.GAME_OVER
            self.meeting_messages.append(
                f"{self.imposter.name} was the imposter!")
            self.record_match_for_learning(winner)

    def record_match_for_learning(self, winner: str):
        """Record match data for AI learning"""
        # Collect strategies
        successful_strat = []
        failed_strat = []

        for player in self.players:
            for strat in player.strategies_used:
                if (winner == "imposter" and player.is_imposter) or \
                   (winner == "crewmate" and not player.is_imposter):
                    successful_strat.append(strat)
                else:
                    failed_strat.append(strat)

        # Player performances
        performances = {}
        for player in self.players:
            performances[player.name] = {
                "kills": player.kill_count if player.is_imposter else 0,
                "tasks_completed": player.tasks_completed_count,
                "correct_votes": player.correct_accusations,
                "wrong_votes": player.wrong_accusations,
                "survived": player.alive,
                "was_imposter": player.is_imposter
            }

        match = MatchHistory(
            winner=winner,
            imposter_name=self.imposter.name,
            rounds_lasted=self.rounds_played,
            kills_made=self.kills_this_match,
            correct_votes=self.correct_votes_this_match,
            wrong_votes=self.wrong_votes_this_match,
            tasks_completed=sum(p.tasks_completed_count for p in self.players),
            player_performances=performances,
            successful_strategies=successful_strat,
            failed_strategies=failed_strat,
            timestamp=time.time()
        )

        self.learning_system.record_match(match)

        print(f"\n📊 MATCH RECORDED:")
        print(f"   Winner: {winner}")
        print(f"   Rounds: {self.rounds_played}")
        print(f"   Kills: {self.kills_this_match}")
        print(
            f"   Learning improved from {len(self.learning_system.match_history)} total matches")

    def draw(self):
        """Render everything"""
        self.screen.fill(SPACE_BLACK)

        # Stars
        for i, (x, y, size) in enumerate(self.background_stars):
            twinkle = abs(math.sin(pygame.time.get_ticks() * 0.001 + i))
            color_val = int(150 + 105 * twinkle)
            pygame.draw.circle(
                self.screen, (color_val, color_val, color_val), (x, y), size)

        if self.state == GameState.INTRO:
            self.draw_intro()
        else:
            self.draw_game()

        pygame.display.flip()

    def draw_intro(self):
        """Intro with learning stats"""
        alpha = min(255, self.intro_timer * 2)

        # Title
        title = self.font_huge.render("AMONG US", True, (255, 255, 255))
        for offset in range(10, 0, -2):
            glow = self.font_huge.render("AMONG US", True, (255, 50, 50))
            glow.set_alpha(30)
            self.screen.blit(
                glow, (WINDOW_WIDTH // 2 - title.get_width() // 2 - offset // 2, 200 - offset // 2))

        title_surf = pygame.Surface(
            (title.get_width(), title.get_height()), pygame.SRCALPHA)
        title_surf.blit(title, (0, 0))
        title_surf.set_alpha(alpha)
        self.screen.blit(title_surf, (WINDOW_WIDTH //
                         2 - title.get_width() // 2, 200))

        if self.intro_timer > 60:
            subtitle = self.font_large.render(
                "ULTIMATE AI LEARNING EDITION", True, NEON_CYAN)
            subtitle.set_alpha(min(255, (self.intro_timer - 60) * 4))
            self.screen.blit(subtitle, (WINDOW_WIDTH // 2 -
                             subtitle.get_width() // 2, 290))

        if self.intro_timer > 120:
            imp_text = self.font_medium.render(
                f"Imposter: {self.imposter.name}", True, WARNING_RED)
            imp_text.set_alpha(min(255, (self.intro_timer - 120) * 4))
            self.screen.blit(imp_text, (WINDOW_WIDTH // 2 -
                             imp_text.get_width() // 2, 370))

        # Learning stats
        if self.intro_timer > 180:
            matches = len(self.learning_system.match_history)
            stats_text = self.font_small.render(
                f"AI trained on {matches} previous matches", True, GOLD)
            stats_text.set_alpha(min(255, (self.intro_timer - 180) * 4))
            self.screen.blit(stats_text, (WINDOW_WIDTH // 2 -
                             stats_text.get_width() // 2, 440))

            if matches > 0:
                imp_wins = sum(
                    1 for m in self.learning_system.match_history if m.winner == "imposter")
                winrate = f"Imposter Win Rate: {int(imp_wins / matches * 100)}%"
                wr_text = self.font_small.render(
                    winrate, True, (200, 200, 200))
                wr_text.set_alpha(min(255, (self.intro_timer - 180) * 4))
                self.screen.blit(
                    wr_text, (WINDOW_WIDTH // 2 - wr_text.get_width() // 2, 470))

    def draw_game(self):
        """Draw main game (same as before but with learning indicators)"""
        # Map - make it smaller for 720p
        map_surf = pygame.Surface((700, WINDOW_HEIGHT))
        map_surf.fill(DEEP_SPACE)

        # Rooms
        for room in self.rooms:
            glow_rect = room.rect.inflate(10, 10)
            glow_surf = pygame.Surface(
                (glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*room.color, 30), (0, 0,
                             glow_rect.width, glow_rect.height), border_radius=8)
            map_surf.blit(glow_surf, (glow_rect.x, glow_rect.y))

            pygame.draw.rect(map_surf, room.color, room.rect, border_radius=5)
            highlight = tuple(min(255, c + 40) for c in room.color)
            pygame.draw.rect(map_surf, highlight, (room.rect.x, room.rect.y, room.rect.width, 20),
                             border_top_left_radius=5, border_top_right_radius=5)
            pygame.draw.rect(map_surf, (255, 255, 255),
                             room.rect, 2, border_radius=5)

            name = self.font_small.render(room.name, True, (255, 255, 255))
            map_surf.blit(name, (room.rect.x + 8, room.rect.y + 5))

            if room.is_critical:
                pygame.draw.circle(map_surf, WARNING_RED,
                                   (room.rect.right - 15, room.rect.y + 15), 5)

        # Hallways (scaled down)
        hallways = [((205, 190), (205, 230)), ((155, 175), (345, 175))]
        for start, end in hallways:
            pygame.draw.line(map_surf, (80, 80, 100), start, end, 26)
            pygame.draw.line(map_surf, (100, 100, 120), start, end, 23)

        # Particles
        for p in self.particles:
            if p.x < 700:  # Map width
                p.draw(map_surf)

        # Players
        for player in self.players:
            player.draw(map_surf, self.particles, self.camera_shake)

        self.screen.blit(map_surf, (0, 0))

        # UI Panel (adjusted for 720p)
        panel_x = 700
        panel_width = 580
        panel_surf = pygame.Surface(
            (panel_width, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (20, 20, 40, 230),
                         (0, 0, panel_width, WINDOW_HEIGHT))
        self.screen.blit(panel_surf, (panel_x, 0))
        pygame.draw.line(self.screen, NEON_CYAN, (panel_x, 0),
                         (panel_x, WINDOW_HEIGHT), 3)

        y = 20
        title = self.font_large.render("AMONG US", True, NEON_CYAN)
        self.screen.blit(title, (panel_x + 20, y))
        y += 50

        # Status
        status_map = {
            GameState.PLAYING: ("▶ PLAYING", NEON_GREEN),
            GameState.MEETING: ("🚨 MEETING", WARNING_RED),
            GameState.VOTING: ("🗳 VOTING", NEON_PINK),
            GameState.RESULTS: ("📊 RESULTS", (255, 255, 100)),
            GameState.GAME_OVER: ("💀 GAME OVER", WARNING_RED),
        }
        status_text, status_color = status_map.get(
            self.state, ("", (255, 255, 255)))
        status = self.font_medium.render(status_text, True, status_color)
        self.screen.blit(status, (panel_x + 20, y))
        y += 40

        # Learning indicator
        matches = len(self.learning_system.match_history)
        learn_text = self.font_small.render(
            f"🧠 Trained: {matches} matches", True, GOLD)
        self.screen.blit(learn_text, (panel_x + 20, y))
        y += 25

        # Stats
        alive = sum(1 for p in self.players if p.alive)
        stats = self.font_small.render(
            f"Alive: {alive}/{len(self.players)}", True, (255, 255, 255))
        self.screen.blit(stats, (panel_x + 20, y))
        y += 25

        # Task progress
        total = sum(len(p.tasks) for p in self.players if not p.is_imposter)
        completed = sum(
            1 for p in self.players if not p.is_imposter for t in p.tasks if t.completed)
        progress = completed / total if total > 0 else 0

        bar_width = 540
        pygame.draw.rect(self.screen, (50, 50, 70),
                         (panel_x + 20, y, bar_width, 25), border_radius=12)
        if progress > 0:
            pygame.draw.rect(self.screen, NEON_GREEN, (panel_x + 22, y + 2,
                             int((bar_width - 4) * progress), 21), border_radius=10)

        task_text = self.font_small.render(
            f"Tasks: {completed}/{total}", True, (255, 255, 255))
        self.screen.blit(task_text, (panel_x + 25, y + 5))
        y += 35

        # Player list
        pygame.draw.line(self.screen, (100, 100, 120),
                         (panel_x + 20, y), (panel_x + 560, y), 2)
        y += 15

        list_title = self.font_medium.render(
            "CREW STATUS", True, (200, 200, 255))
        self.screen.blit(list_title, (panel_x + 20, y))
        y += 35

        for player in self.players:
            bg_color = (80, 40, 40, 100) if player.suspicion_level > 60 else (
                40, 40, 60, 100)
            row = pygame.Surface((540, 30), pygame.SRCALPHA)
            pygame.draw.rect(row, bg_color, (0, 0, 540, 30), border_radius=5)
            self.screen.blit(row, (panel_x + 20, y))

            pygame.draw.circle(self.screen, player.color,
                               (panel_x + 40, y + 15), 12)
            if not player.alive:
                pygame.draw.line(self.screen, (255, 50, 50),
                                 (panel_x + 32, y + 7), (panel_x + 48, y + 23), 3)

            status_sym = "✓" if player.alive else "💀"
            color = player.color if player.alive else (150, 150, 150)
            name = self.font_small.render(
                f"{status_sym} {player.name}", True, color)
            self.screen.blit(name, (panel_x + 65, y + 8))

            # Show AI confidence
            confidence = int(player.voting_confidence * 100)
            conf_text = self.font_small.render(
                f"{confidence}%", True, (180, 180, 200))
            self.screen.blit(conf_text, (panel_x + 200, y + 8))

            # Suspicion
            if player.alive and not player.is_imposter:
                sus_w = int(2 * (player.suspicion_level / 100))
                if sus_w > 0:
                    pygame.draw.rect(
                        self.screen, WARNING_RED, (panel_x + 280, y + 10, sus_w, 10), border_radius=5)

            # Tasks
            if not player.is_imposter and player.alive:
                done = sum(1 for t in player.tasks if t.completed)
                task_info = self.font_small.render(
                    f"{done}/{len(player.tasks)}", True, NEON_CYAN)
                self.screen.blit(task_info, (panel_x + 420, y + 8))

            y += 35

        # Chat
        y += 10
        pygame.draw.line(self.screen, (100, 100, 120),
                         (panel_x + 20, y), (panel_x + 560, y), 2)
        y += 15

        chat_title = self.font_medium.render(
            "COMMUNICATIONS", True, (200, 200, 255))
        self.screen.blit(chat_title, (panel_x + 20, y))
        y += 35

        chat_rect = pygame.Rect(panel_x + 20, y, 540, 260)
        chat_surf = pygame.Surface((540, 260), pygame.SRCALPHA)
        pygame.draw.rect(chat_surf, (20, 20, 40, 200),
                         (0, 0, 540, 260), border_radius=10)
        self.screen.blit(chat_surf, (panel_x + 20, y))
        pygame.draw.rect(self.screen, NEON_CYAN,
                         chat_rect, 2, border_radius=10)

        msg_y = y + 10
        # Show 10 messages instead of 12 for smaller screen
        for msg in self.meeting_messages[-10:]:
            msg_text = self.font_small.render(msg, True, (255, 255, 255))
            self.screen.blit(msg_text, (panel_x + 30, msg_y))
            msg_y += 22

        # Game over
        if self.state == GameState.GAME_OVER:
            overlay = pygame.Surface(
                (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 200),
                             (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
            self.screen.blit(overlay, (0, 0))

            game_over = self.font_huge.render(
                self.game_over_message, True, WARNING_RED)
            for i in range(8, 0, -2):
                glow = self.font_huge.render(
                    self.game_over_message, True, (255, 100, 100))
                glow.set_alpha(40)
                self.screen.blit(
                    glow, (WINDOW_WIDTH // 2 - game_over.get_width() // 2 - i, WINDOW_HEIGHT // 2 - 50 - i))
            self.screen.blit(game_over, (WINDOW_WIDTH // 2 -
                             game_over.get_width() // 2, WINDOW_HEIGHT // 2 - 50))

            if self.meeting_messages:
                reveal = self.font_large.render(
                    self.meeting_messages[-1], True, NEON_CYAN)
                self.screen.blit(
                    reveal, (WINDOW_WIDTH // 2 - reveal.get_width() // 2, WINDOW_HEIGHT // 2 + 50))

            restart = self.font_medium.render(
                "Press R to restart  |  ESC to quit", True, (255, 255, 255))
            self.screen.blit(restart, (WINDOW_WIDTH // 2 -
                             restart.get_width() // 2, WINDOW_HEIGHT // 2 + 120))

            # Show learning improvement
            matches = len(self.learning_system.match_history)
            learn = self.font_small.render(
                f"AI has learned from {matches} total matches!", True, GOLD)
            self.screen.blit(learn, (WINDOW_WIDTH // 2 -
                             learn.get_width() // 2, WINDOW_HEIGHT // 2 + 170))

    def handle_events(self):
        """Input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                    self.__init__()
                if event.key == pygame.K_SPACE and self.state == GameState.PLAYING:
                    caller = random.choice(
                        [p for p in self.players if p.alive])
                    self.start_meeting(
                        f"{caller.name} pressed button!", caller)
        return True

    def run(self):
        """Main loop"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = AmongUsGame()
    game.run()
