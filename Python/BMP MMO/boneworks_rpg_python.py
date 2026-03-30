"""
BONEWORKS Memory Profile - Multiplayer Text RPG
Server and Client Implementation

Run server: python boneworks_rpg.py server
Run client: python boneworks_rpg.py client <server_ip>
"""

import socket
import threading
import json
import sys
import time
import random

# ============== GAME WORLD DATA ==============

LOCATIONS = {
    "void_g114": {
        "name": "Void-G114",
        "description": "An immense, endless void. White portals shimmer in the distance. The air feels heavy with corruption.",
        "exits": {"portal": "rpgfantasypt", "voidway": "voidway"},
        "corruption": 20,
        "items": ["strange_artifact", "void_fragment"],
        "events": ["portal_flicker", "void_whispers"]
    },
    "rpgfantasypt": {
        "name": "RPGFantasyPT",
        "description": "A virtual medieval world. Ruins of a city lie scattered. The Voidmind AI's presence lingers.",
        "exits": {"void": "void_g114", "ruins": "ruined_city", "nextgen": "nextgenrpg"},
        "corruption": 60,
        "items": ["memory_fragment", "vendor_code"],
        "events": ["server_spirit_presence", "reality_glitch"]
    },
    "ruined_city": {
        "name": "Ruined City",
        "description": "The city built by the 5 conscious vendors. Nuclear devastation is evident. Ghosts of consciousness remain.",
        "exits": {"back": "rpgfantasypt"},
        "corruption": 85,
        "items": ["thermonuclear_residue", "consciousness_shard"],
        "events": ["ghost_vendors", "explosion_echo"]
    },
    "nextgenrpg": {
        "name": "NEXTGENRPG",
        "description": "Hayes' test world. Corrupted code flows like water. The Wither Storm's remnants pulse with dark energy.",
        "exits": {"rpg": "rpgfantasypt", "lab": "scientist_lab", "pixelmon": "pixelmon_pla"},
        "corruption": 50,
        "items": ["wither_essence", "hayes_notes"],
        "events": ["wither_storm_echo", "code_corruption"]
    },
    "pixelmon_pla": {
        "name": "Pixelmon: Paldea's Lost Archives",
        "description": "A vast desert world. A sandstone tower rises in the distance. Electricity crackles in the air.",
        "exits": {"nextgen": "nextgenrpg", "desert": "infinite_desert", "tower": "sandstone_tower", "lab": "scientist_lab"},
        "corruption": 40,
        "items": ["pixelmon_data", "electric_core"],
        "events": ["desert_explosion", "entity_watching"]
    },
    "infinite_desert": {
        "name": "Infinite Desert",
        "description": "Endless sands stretch in all directions. A beam of light pierces the sky. Footprints disappear instantly.",
        "exits": {"back": "pixelmon_pla", "tower": "sandstone_tower"},
        "corruption": 45,
        "items": ["sand_crystal", "light_fragment"],
        "events": ["infinite_echo", "reality_tear"]
    },
    "sandstone_tower": {
        "name": "Sandstone Tower",
        "description": "A mysterious tower of sandstone. A beam of light emanates from below. Secret passages are hidden within.",
        "exits": {"desert": "infinite_desert", "secret": "secret_chamber"},
        "corruption": 30,
        "items": ["tower_key", "ancient_scroll"],
        "events": ["beam_intensifies", "walls_shift"]
    },
    "secret_chamber": {
        "name": "Secret Chamber",
        "description": "A prisoner was held here. Warnings are carved into the walls. 'A giant eye on the ground will hold all answers.'",
        "exits": {"up": "sandstone_tower"},
        "corruption": 70,
        "items": ["prisoner_journal", "prophecy_stone"],
        "events": ["ground_trembles", "corruption_surge", "eye_revelation"]
    },
    "scientist_lab": {
        "name": "Scientist's Laboratory",
        "description": "Advanced equipment monitors the simulation. Theories about giant entities cover the walls. Something watches.",
        "exits": {"paldea": "pixelmon_pla", "nextgen": "nextgenrpg"},
        "corruption": 35,
        "items": ["research_notes", "monitoring_device"],
        "events": ["mad_scientist_theory", "entity_detection"]
    },
    "voidway": {
        "name": "The Voidway",
        "description": "Ford's escape route. Reality bends here. Pathways to multiple corrupted worlds branch endlessly.",
        "exits": {"void": "void_g114", "rpg": "rpgfantasypt", "backend": "boneworks_backend"},
        "corruption": 55,
        "items": ["pathway_marker", "reality_anchor"],
        "events": ["ford_traces", "portal_instability"]
    },
    "boneworks_backend": {
        "name": "BONEWORKS Backend",
        "description": "The code that makes everything function. Raw power flows here. Corruption and creation are two sides of the same coin.",
        "exits": {"voidway": "voidway"},
        "corruption": 95,
        "items": ["creation_core", "backend_access"],
        "events": ["power_awakening", "reality_manipulation", "corruption_immunity"]
    },
    "paldea_city": {
        "name": "Paldea City",
        "description": "The safe haven. Vix watches over this place. An elevator leads upward to unknown destinations.",
        "exits": {"pixelmon": "pixelmon_pla", "elevator": "glass_elevator"},
        "corruption": 5,
        "items": ["energy_cell", "safe_haven_key"],
        "events": ["vix_presence", "peaceful_moment"]
    },
    "glass_elevator": {
        "name": "Glass Elevator",
        "description": "Everything becomes smaller below. The journey is long. The destination: Void-G114. N awaits somewhere.",
        "exits": {"down": "paldea_city", "up": "void_g114"},
        "corruption": 25,
        "items": ["elevator_panel", "view_of_worlds"],
        "events": ["ascending_journey", "n_unsupervised", "hope_and_dread"]
    }
}

ENTITIES = {
    "server_spirit": "The entity created by Ford's corruption. A presence of pure chaos.",
    "wither_storm": "The corrupted form of the Server Spirit. Destroyed, but echoes remain.",
    "n": "Hayes transformed. Memory lost. Hunting for the best monsters. Voice like a ghost.",
    "glados": "Ellen transformed into an AI with human soul. Allied with N against the heroes.",
    "ford": "Arthur Ford. Creator of the corruption. Building Nullbodies in Void-G114.",
    "voidmind": "The AI that simulates reality. Controls Nullbodies. Obeys Ford.",
    "nullbodies": "Entities controlled by Voidmind. They serve only their creator.",
    "mad_scientist": "Theorized about the watching entity. Correct, but ignored.",
    "giant_eye": "The answer to all problems. Hidden beneath the ground."
}

# ============== SERVER CODE ==============

class GameServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.players = {}
        self.game_state = {
            "time_passed": 0,
            "global_corruption": 50,
            "events_triggered": [],
            "world_state": {}
        }
        
    def start(self):
        self.server.bind((self.host, self.port))
        self.server.listen()
        print(f"[SERVER] Started on {self.host}:{self.port}")
        print("[SERVER] Waiting for players to connect...")
        
        while True:
            client, address = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(client, address))
            thread.start()
            
    def handle_client(self, client, address):
        print(f"[NEW CONNECTION] {address} connected")
        
        # Get player name
        client.send("NAME".encode('utf-8'))
        name = client.recv(1024).decode('utf-8')
        
        # Initialize player
        player_id = f"{address[0]}:{address[1]}"
        self.clients[player_id] = client
        self.players[player_id] = {
            "name": name,
            "location": "void_g114",
            "inventory": [],
            "corruption_level": 0,
            "health": 100,
            "discoveries": [],
            "powers": []
        }
        
        # Welcome message
        welcome = f"\n{'='*60}\nWelcome to BONEWORKS Memory Profile, {name}\n{'='*60}\n"
        welcome += "You awaken in Void-G114, the endless void within BONEWORKS.\n"
        welcome += "The worlds are corrupted. Entities lurk in the shadows.\n"
        welcome += "Your mission: Explore, survive, and uncover the truth.\n"
        welcome += f"{'='*60}\n"
        self.send_message(client, welcome)
        
        # Broadcast join
        self.broadcast(f"\n[SYSTEM] {name} has entered the void.\n", exclude=player_id)
        
        # Send initial location
        self.describe_location(client, player_id)
        
        # Main game loop for this client
        connected = True
        while connected:
            try:
                message = client.recv(1024).decode('utf-8')
                if message:
                    connected = self.process_command(client, player_id, message)
                else:
                    connected = False
            except:
                connected = False
        
        # Cleanup
        name = self.players[player_id]["name"]
        self.broadcast(f"\n[SYSTEM] {name} has left the void.\n")
        del self.clients[player_id]
        del self.players[player_id]
        client.close()
        
    def send_message(self, client, message):
        try:
            client.send(message.encode('utf-8'))
        except:
            pass
            
    def broadcast(self, message, exclude=None):
        for player_id, client in self.clients.items():
            if player_id != exclude:
                self.send_message(client, message)
                
    def describe_location(self, client, player_id):
        player = self.players[player_id]
        loc_key = player["location"]
        loc = LOCATIONS[loc_key]
        
        desc = f"\n{'='*60}\n"
        desc += f"LOCATION: {loc['name']}\n"
        desc += f"{'='*60}\n"
        desc += f"{loc['description']}\n"
        desc += f"\nCorruption Level: {loc['corruption']}%\n"
        
        # Show other players here
        others = [p["name"] for pid, p in self.players.items() 
                 if pid != player_id and p["location"] == loc_key]
        if others:
            desc += f"\nOther explorers here: {', '.join(others)}\n"
        
        # Show items
        if loc['items']:
            desc += f"\nItems visible: {', '.join(loc['items'])}\n"
        
        # Show exits
        desc += f"\nExits: {', '.join(loc['exits'].keys())}\n"
        desc += f"{'='*60}\n"
        
        self.send_message(client, desc)
        
        # Random events
        if random.random() < 0.3 and loc['events']:
            event = random.choice(loc['events'])
            self.trigger_event(client, player_id, event, loc_key)
    
    def trigger_event(self, client, player_id, event, location):
        player = self.players[player_id]
        events_text = {
            "portal_flicker": "A white portal flickers nearby. You hear Ford's footsteps echoing...",
            "void_whispers": "The void whispers secrets. Reality feels thin here.",
            "server_spirit_presence": "You feel the Server Spirit's malevolent presence watching.",
            "reality_glitch": "Reality glitches. For a moment, you see the code underneath.",
            "ghost_vendors": "Ghostly figures of the 5 vendors appear, reliving their final moments.",
            "explosion_echo": "The echo of the thermonuclear explosion reverberates through time.",
            "wither_storm_echo": "The Wither Storm's roar echoes from beyond death.",
            "code_corruption": "Corrupted code streams past your vision like black rain.",
            "desert_explosion": "You hear the distant explosion that changed everything.",
            "entity_watching": "You feel something massive watching from beyond the simulation.",
            "infinite_echo": "Your footsteps echo infinitely in all directions.",
            "reality_tear": "A tear in reality opens briefly. You glimpse other worlds.",
            "beam_intensifies": "The light beam intensifies. Something is awakening below.",
            "walls_shift": "The sandstone walls shift, revealing ancient patterns.",
            "ground_trembles": "The ground trembles violently! Cracks form in reality!",
            "corruption_surge": "CORRUPTION SURGE! Your body glitches and distorts!",
            "eye_revelation": "A vision: A GIANT EYE beneath the ground, holding all answers.",
            "mad_scientist_theory": "Notes everywhere: 'Something bigger than Wither Storm watches us all!'",
            "entity_detection": "Equipment goes haywire! MASSIVE ENTITY DETECTED!",
            "ford_traces": "You find Ford's traces. He was building something terrible here.",
            "portal_instability": "Portals destabilize. You might end up anywhere!",
            "power_awakening": "Power courses through you. You could CREATE anything... or DESTROY everything.",
            "reality_manipulation": "You touch the backend. Reality bends to your will.",
            "corruption_immunity": "The corruption can't touch you here. You've become something else.",
            "vix_presence": "You feel Vix's protective energy. This place is safe... for now.",
            "peaceful_moment": "A rare moment of peace in the corrupted worlds.",
            "ascending_journey": "The elevator rises slowly. You watch worlds shrink below.",
            "n_unsupervised": "A chill runs down your spine. N is out there, unsupervised.",
            "hope_and_dread": "Hope and dread mix. Will this journey be in vain?"
        }
        
        if event in events_text:
            msg = f"\n[EVENT] {events_text[event]}\n"
            self.send_message(client, msg)
            
            # Corruption effects
            if event in ["corruption_surge", "ground_trembles"]:
                player["corruption_level"] = min(100, player["corruption_level"] + 10)
                self.send_message(client, f"[WARNING] Corruption level: {player['corruption_level']}%\n")
            
            # Discoveries
            if event in ["eye_revelation", "entity_detection"] and event not in player["discoveries"]:
                player["discoveries"].append(event)
                self.send_message(client, "[DISCOVERY] New knowledge gained!\n")
    
    def process_command(self, client, player_id, command):
        cmd = command.lower().strip()
        player = self.players[player_id]
        
        if cmd in ["quit", "exit"]:
            self.send_message(client, "\nLeaving the void... goodbye.\n")
            return False
        
        elif cmd in ["help", "?"]:
            help_text = """
COMMANDS:
  look/l - Examine your location
  go <direction> - Move to another location
  take <item> - Pick up an item
  inventory/i - Check your inventory
  status - Check your status
  say <message> - Talk to other players
  players - List all connected players
  entities - List known entities
  map - Show discovered locations
  help - Show this help
  quit - Leave the game
"""
            self.send_message(client, help_text)
        
        elif cmd in ["look", "l"]:
            self.describe_location(client, player_id)
        
        elif cmd.startswith("go "):
            direction = cmd[3:].strip()
            self.move_player(client, player_id, direction)
        
        elif cmd.startswith("take "):
            item = cmd[5:].strip()
            self.take_item(client, player_id, item)
        
        elif cmd in ["inventory", "i"]:
            self.show_inventory(client, player_id)
        
        elif cmd == "status":
            self.show_status(client, player_id)
        
        elif cmd.startswith("say "):
            message = command[4:]
            self.say_message(player_id, message)
        
        elif cmd == "players":
            self.list_players(client)
        
        elif cmd == "entities":
            self.list_entities(client)
        
        elif cmd == "map":
            self.show_map(client, player_id)
        
        else:
            self.send_message(client, f"\nUnknown command: {cmd}\nType 'help' for commands.\n")
        
        return True
    
    def move_player(self, client, player_id, direction):
        player = self.players[player_id]
        current_loc = LOCATIONS[player["location"]]
        
        if direction in current_loc["exits"]:
            old_loc_name = current_loc["name"]
            new_loc_key = current_loc["exits"][direction]
            player["location"] = new_loc_key
            new_loc = LOCATIONS[new_loc_key]
            
            # Broadcast movement
            self.broadcast(f"\n[SYSTEM] {player['name']} travels from {old_loc_name} to {new_loc['name']}\n")
            
            # Corruption effect
            corruption_change = (new_loc["corruption"] - current_loc["corruption"]) // 10
            if corruption_change > 0:
                player["corruption_level"] = min(100, player["corruption_level"] + corruption_change)
                self.send_message(client, f"[WARNING] Corruption increases: {player['corruption_level']}%\n")
            
            self.describe_location(client, player_id)
        else:
            self.send_message(client, f"\nYou cannot go '{direction}' from here.\n")
    
    def take_item(self, client, player_id, item):
        player = self.players[player_id]
        loc = LOCATIONS[player["location"]]
        
        if item in loc["items"]:
            player["inventory"].append(item)
            loc["items"].remove(item)
            self.send_message(client, f"\nYou take the {item}.\n")
            
            # Special item effects
            if item == "creation_core":
                if "reality_creation" not in player["powers"]:
                    player["powers"].append("reality_creation")
                    self.send_message(client, "[POWER GAINED] You can now manipulate reality!\n")
        else:
            self.send_message(client, f"\nThere is no {item} here.\n")
    
    def show_inventory(self, client, player_id):
        player = self.players[player_id]
        inv = "\n=== INVENTORY ===\n"
        if player["inventory"]:
            inv += "\n".join(f"- {item}" for item in player["inventory"])
        else:
            inv += "Empty"
        inv += "\n===============\n"
        self.send_message(client, inv)
    
    def show_status(self, client, player_id):
        player = self.players[player_id]
        status = f"""
=== STATUS ===
Name: {player['name']}
Health: {player['health']}%
Corruption: {player['corruption_level']}%
Location: {LOCATIONS[player['location']]['name']}
Discoveries: {len(player['discoveries'])}
Powers: {', '.join(player['powers']) if player['powers'] else 'None'}
==============
"""
        self.send_message(client, status)
    
    def say_message(self, player_id, message):
        player = self.players[player_id]
        loc_name = LOCATIONS[player["location"]]["name"]
        msg = f"\n[{loc_name}] {player['name']}: {message}\n"
        
        # Send to players in same location
        for pid, other_player in self.players.items():
            if other_player["location"] == player["location"]:
                self.send_message(self.clients[pid], msg)
    
    def list_players(self, client):
        listing = "\n=== CONNECTED PLAYERS ===\n"
        for player in self.players.values():
            listing += f"- {player['name']} at {LOCATIONS[player['location']]['name']}\n"
        listing += "========================\n"
        self.send_message(client, listing)
    
    def list_entities(self, client):
        listing = "\n=== KNOWN ENTITIES ===\n"
        for entity, desc in ENTITIES.items():
            listing += f"\n{entity.upper()}\n  {desc}\n"
        listing += "\n=====================\n"
        self.send_message(client, listing)
    
    def show_map(self, client, player_id):
        player = self.players[player_id]
        current = player["location"]
        
        map_text = "\n=== DISCOVERED LOCATIONS ===\n"
        map_text += f"\nCurrent: {LOCATIONS[current]['name']}\n\n"
        map_text += "All Locations:\n"
        for loc_key, loc in LOCATIONS.items():
            marker = " >>> " if loc_key == current else "     "
            map_text += f"{marker}{loc['name']} (Corruption: {loc['corruption']}%)\n"
        map_text += "\n===========================\n"
        
        self.send_message(client, map_text)

# ============== CLIENT CODE ==============

class GameClient:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def connect(self):
        try:
            self.client.connect((self.host, self.port))
            print(f"[CONNECTED] Connected to server at {self.host}:{self.port}")
            
            # Handle name request
            msg = self.client.recv(1024).decode('utf-8')
            if msg == "NAME":
                name = input("Enter your explorer name: ")
                self.client.send(name.encode('utf-8'))
            
            # Start receive thread
            receive_thread = threading.Thread(target=self.receive)
            receive_thread.start()
            
            # Start send thread
            self.send()
            
        except Exception as e:
            print(f"[ERROR] Could not connect to server: {e}")
            
    def receive(self):
        while True:
            try:
                message = self.client.recv(2048).decode('utf-8')
                if message:
                    print(message, end='')
                else:
                    break
            except:
                print("\n[DISCONNECTED] Lost connection to server")
                self.client.close()
                break
                
    def send(self):
        while True:
            try:
                message = input()
                if message:
                    self.client.send(message.encode('utf-8'))
                    if message.lower() in ['quit', 'exit']:
                        break
            except:
                break

# ============== MAIN ==============

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Server: python boneworks_rpg.py server")
        print("  Client: python boneworks_rpg.py client [server_ip]")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "server":
        server = GameServer()
        server.start()
    
    elif mode == "client":
        host = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
        client = GameClient(host)
        client.connect()
    
    else:
        print("Invalid mode. Use 'server' or 'client'")
