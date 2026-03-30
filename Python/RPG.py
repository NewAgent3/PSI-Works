import tkinter as tk
from tkinter import simpledialog, messagebox
import random

# ------------------------------
# CONFIG / DATA
# ------------------------------
MAP_SIZE = 10
CELL_PIX = 40

# Tile types and colors (including dungeon entrance)
TILE_TYPES = ["grass", "forest", "town", "chest", "dungeon_entrance"]
TILE_COLORS = {"grass": "#7cfc00", "forest": "#228b22",
               "town": "#deb887", "chest": "#d2b48c", "dungeon_entrance": "#87cefa"}
# encounter rates per tile (will be used per region)
ENCOUNTER_RATES = {"grass": 0.15, "forest": 0.45,
                   "town": 0.02, "chest": 0.0, "dungeon_entrance": 0.0}

# Basic enemy templates (level-based will scale)
ENEMY_TEMPLATES = [
    {"name": "Goblin", "hp": 40, "atk": 8, "def": 2, "xp": 20, "gold": 10},
    {"name": "Wolf", "hp": 50, "atk": 10, "def": 3, "xp": 25, "gold": 12},
    {"name": "Bandit", "hp": 60, "atk": 12, "def": 4, "xp": 30, "gold": 15},
    # New enemies
    {"name": "Ice Wolf", "hp": 70, "atk": 14, "def": 5, "xp": 45, "gold": 25},
    {"name": "Frost Golem", "hp": 120, "atk": 18, "def": 8, "xp": 90, "gold": 60},
    {"name": "Necromancer", "hp": 90, "atk": 16, "def": 4, "xp": 80, "gold": 50},
]

# Shop items (added gear and elixir)
SHOP_ITEMS = [
    {"id": "potion", "name": "Potion", "type": "consumable", "heal": 30, "price": 20},
    {"id": "superpotion", "name": "Super Potion",
        "type": "consumable", "heal": 60, "price": 50},
    {"id": "elixir", "name": "Elixir",
        "type": "consumable", "heal": 120, "price": 200},
    {"id": "iron_sword", "name": "Iron Sword",
        "type": "weapon", "atk": 5, "price": 80},
    {"id": "steel_sword", "name": "Steel Sword",
        "type": "weapon", "atk": 10, "price": 160},
    {"id": "frost_blade", "name": "Frost Blade",
        "type": "weapon", "atk": 15, "price": 400},
    {"id": "leather_armor", "name": "Leather Armor",
        "type": "armor", "def": 2, "price": 60},
    {"id": "chain_armor", "name": "Chain Armor",
        "type": "armor", "def": 5, "price": 130},
    {"id": "crystal_armor", "name": "Crystal Armor",
        "type": "armor", "def": 8, "price": 420},
]

# ------------------------------
# CLASSES
# ------------------------------


class Player:
    def __init__(self):
        # start in 'Plains' region in center
        self.pos = [MAP_SIZE // 2, MAP_SIZE // 2]
        self.level = 1
        self.xp = 0
        self.xp_to_level = 100
        self.max_hp = 120
        self.hp = self.max_hp
        self.base_atk = 10
        self.base_def = 2
        self.gold = 100
        # equipment slots: weapon, armor
        self.equipment = {"weapon": None, "armor": None}
        # inventory: {item_id: count}
        self.inventory = {"potion": 2}
        # quest log: dict quest_id -> quest dict
        self.quests = {}
        # track kills for quest progress
        self.kill_counters = {}

    def atk_value(self):
        bonus = 0
        w = self.equipment.get("weapon")
        if w and "atk" in w:
            bonus += w["atk"]
        return self.base_atk + bonus

    def def_value(self):
        bonus = 0
        a = self.equipment.get("armor")
        if a and "def" in a:
            bonus += a["def"]
        return self.base_def + bonus

    def gain_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.level += 1
            self.xp_to_level = int(self.xp_to_level * 1.3)
            self.max_hp += 25
            self.base_atk += 3
            self.base_def += 1
            self.hp = self.max_hp
            leveled = True
        return leveled

    def add_item(self, item_id, amount=1):
        self.inventory[item_id] = self.inventory.get(item_id, 0) + amount

    def remove_item(self, item_id, amount=1):
        if self.inventory.get(item_id, 0) >= amount:
            self.inventory[item_id] -= amount
            if self.inventory[item_id] <= 0:
                del self.inventory[item_id]
            return True
        return False


class Quest:
    def __init__(self, qid, title, description, target_type, target, amount, reward):
        """
        target_type: "kill" or "collect" or "clear_dungeon"
        target: enemy name or item id (or dungeon id)
        amount: required count (or 1 for dungeon)
        reward: dict, e.g. {"xp":50, "gold":50, "item":"potion"}
        """
        self.qid = qid
        self.title = title
        self.description = description
        self.target_type = target_type
        self.target = target
        self.amount = amount
        self.progress = 0
        self.completed = False
        self.reward = reward

    def progress_by(self, n=1):
        if self.completed:
            return
        self.progress += n
        if self.progress >= self.amount:
            self.progress = self.amount
            self.completed = True


# ------------------------------
# MAIN GAME CLASS (Tkinter GUI)
# ------------------------------


class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter RPG — Towns, Gear, Quests (Expanded)")
        self.canvas = tk.Canvas(root, width=MAP_SIZE *
                                CELL_PIX, height=MAP_SIZE*CELL_PIX, bg="black")
        self.canvas.grid(row=0, column=0, rowspan=8, padx=8, pady=8)

        # UI side panel
        self.stats_label = tk.Label(
            root, text="", justify="left", font=("Consolas", 11))
        self.stats_label.grid(row=0, column=1, sticky="nw", padx=8)
        self.inv_label = tk.Label(
            root, text="", justify="left", font=("Consolas", 11))
        self.inv_label.grid(row=1, column=1, sticky="nw", padx=8)
        self.info_label = tk.Label(
            root, text="Use arrow keys to move. Move north from the Plains to reach the Frostlands.", font=("Helvetica", 11))
        self.info_label.grid(row=2, column=1, sticky="nw", padx=8, pady=6)

        # Buttons
        self.btn_use_item = tk.Button(
            root, text="Use Item", command=self.open_use_item)
        self.btn_use_item.grid(row=3, column=1, sticky="nw", padx=8, pady=4)
        self.btn_equip = tk.Button(
            root, text="Equip/Unequip", command=self.open_equip_window)
        self.btn_equip.grid(row=4, column=1, sticky="nw", padx=8, pady=4)
        self.btn_quests = tk.Button(
            root, text="Quests", command=self.open_quests_window)
        self.btn_quests.grid(row=5, column=1, sticky="nw", padx=8, pady=4)
        self.btn_inventory = tk.Button(
            root, text="Inventory Details", command=self.open_inventory_window)
        self.btn_inventory.grid(row=6, column=1, sticky="nw", padx=8, pady=4)

        # initialize game world
        self.player = Player()
        self.current_region = "Plains"  # two regions: Plains, Frostlands
        self.maps = {}  # region_name -> tile grid
        self.towns_by_region = {}
        self.chests_by_region = {}
        self.create_region_map("Plains")
        # prepare but player starts in Plains
        self.create_region_map("Frostlands")
        self.place_region_towns("Plains")
        self.place_region_towns("Frostlands")
        self.place_region_chests("Plains")
        self.place_region_chests("Frostlands")
        self.place_frost_dungeon_entrance()  # place entrance in Frostlands
        self.create_sample_quests()
        self.in_battle = False
        self.current_enemy = None
        self.battle_window = None

        # draw initial map and labels
        self.draw_map()
        self.update_ui()

        # key bindings
        root.bind("<Up>", lambda e: self.attempt_move(0, -1))
        root.bind("<Down>", lambda e: self.attempt_move(0, 1))
        root.bind("<Left>", lambda e: self.attempt_move(-1, 0))
        root.bind("<Right>", lambda e: self.attempt_move(1, 0))

    # ------------------------------
    # REGION / MAP CREATION
    # ------------------------------
    def create_region_map(self, region_name):
        # create a fresh tile grid for the region
        grid = [[random.choices(["grass", "forest"], weights=[0.7, 0.3])[0]
                 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        self.maps[region_name] = grid

    def place_region_towns(self, region_name):
        towns = {}
        grid = self.maps[region_name]
        # place 1-3 towns per region
        for _ in range(random.randint(1, 3)):
            tx = random.randrange(1, MAP_SIZE-1)
            ty = random.randrange(1, MAP_SIZE-1)
            grid[ty][tx] = "town"
            towns[(tx, ty)] = {
                "name": f"{region_name}_Town_{tx}_{ty}",
                "shop": SHOP_ITEMS.copy() if region_name == "Plains" else SHOP_ITEMS.copy(),
                "inn_cost": 10 if region_name == "Plains" else 20,
                "npcs": [
                    {"name": "Mayor", "dialogue": "Welcome to our town! We need help clearing wolves." if region_name ==
                        "Plains" else "The Frostlands grew cold after the dungeon awoke..."},
                    {"name": "Shopkeeper", "dialogue": "Buy something useful!"}
                ],
            }
        self.towns_by_region[region_name] = towns

    def place_region_chests(self, region_name):
        chests = {}
        grid = self.maps[region_name]
        for _ in range(random.randint(3, 6)):
            x = random.randrange(MAP_SIZE)
            y = random.randrange(MAP_SIZE)
            if grid[y][x] != "town":
                grid[y][x] = "chest"
                chests[(x, y)] = False
        self.chests_by_region[region_name] = chests

    def place_frost_dungeon_entrance(self):
        # pick a spot in Frostlands away from towns
        grid = self.maps["Frostlands"]
        placed = False
        for _ in range(200):
            x = random.randrange(MAP_SIZE)
            y = random.randrange(MAP_SIZE)
            if grid[y][x] not in ("town", "chest"):
                grid[y][x] = "dungeon_entrance"
                placed = True
                break
        if not placed:
            # fallback: place at 1,1
            grid[1][1] = "dungeon_entrance"

    # ------------------------------
    # DRAW MAP
    # ------------------------------
    def draw_map(self):
        self.canvas.delete("all")
        grid = self.maps[self.current_region]
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                tile = grid[y][x]
                color = TILE_COLORS.get(tile, "#7cfc00")
                self.canvas.create_rectangle(x*CELL_PIX, y*CELL_PIX,
                                             (x+1)*CELL_PIX, (y+1)*CELL_PIX,
                                             fill=color, outline="black")
        # draw chests
        chests = self.chests_by_region.get(self.current_region, {})
        for (cx, cy), opened in chests.items():
            if not opened:
                self.canvas.create_rectangle(cx*CELL_PIX+12, cy*CELL_PIX+12,
                                             cx*CELL_PIX+28, cy*CELL_PIX+28,
                                             fill="#b8860b")
        # draw player as oval
        px, py = self.player.pos
        self.canvas.create_oval(
            px*CELL_PIX+6, py*CELL_PIX+6, px*CELL_PIX+34, py*CELL_PIX+34, fill="blue")
        # draw towns as small houses
        for (tx, ty) in self.towns_by_region.get(self.current_region, {}).keys():
            self.canvas.create_rectangle(
                tx*CELL_PIX+5, ty*CELL_PIX+5, tx*CELL_PIX+35, ty*CELL_PIX+35, outline="sienna", width=2)

    # ------------------------------
    # MOVEMENT + REGION SWITCHING + ENCOUNTERS
    # ------------------------------
    def attempt_move(self, dx, dy):
        if self.in_battle:
            self.set_info("You're in battle — finish it first!")
            return
        new_x = self.player.pos[0] + dx
        new_y = self.player.pos[1] + dy

        # region boundary checks for switching regions
        # If at north edge of Plains and move north -> offer Frostlands
        if self.current_region == "Plains" and new_y < 0:
            ans = messagebox.askyesno(
                "Region Travel", "The air grows colder. Travel into the Frostlands to the north?")
            if ans:
                self.current_region = "Frostlands"
                # put player at bottom row of frostlands roughly same x
                self.player.pos = [
                    max(0, min(MAP_SIZE-1, self.player.pos[0])), MAP_SIZE-1]
                self.draw_map()
                self.set_info(
                    "You enter the Frostlands. Beware the cold and the dungeon...")
                self.update_ui()
            return
        # If at south edge of Frostlands and move south -> return to Plains
        if self.current_region == "Frostlands" and new_y >= MAP_SIZE:
            ans = messagebox.askyesno(
                "Region Travel", "Return to the warmer Plains to the south?")
            if ans:
                self.current_region = "Plains"
                self.player.pos = [
                    max(0, min(MAP_SIZE-1, self.player.pos[0])), 0]
                self.draw_map()
                self.set_info("You return to the Plains.")
                self.update_ui()
            return

        # normal bounds check within current_map
        if not (0 <= new_x < MAP_SIZE and 0 <= new_y < MAP_SIZE):
            self.set_info("You can't walk off the map.")
            return

        self.player.pos = [new_x, new_y]
        self.draw_map()
        tile = self.maps[self.current_region][new_y][new_x]
        self.set_info(
            f"You moved to a {tile} tile in the {self.current_region}.")
        # chest open?
        if tile == "chest" and not self.chests_by_region[self.current_region].get((new_x, new_y), True):
            self.open_chest(new_x, new_y)
            return
        # town interactions
        if tile == "town":
            self.enter_town(new_x, new_y)
            return
        # dungeon entrance
        if tile == "dungeon_entrance":
            self.enter_dungeon(new_x, new_y)
            return
        # random encounter
        # slightly different enemy pools by region
        encounter_chance = ENCOUNTER_RATES.get(tile, 0.15)
        if random.random() < encounter_chance:
            # scale by player level, but bias frost enemies in Frostlands
            self.start_battle(scale=self.player.level,
                              region=self.current_region)
        self.update_ui()

    # ------------------------------
    # CHESTS
    # ------------------------------
    def open_chest(self, x, y):
        self.chests_by_region[self.current_region][(x, y)] = True
        # random chest contents, region-sensitive
        if self.current_region == "Plains":
            items = ["potion", "gold", "superpotion"]
        else:
            items = ["potion", "gold", "superpotion", "elixir"]
        choice = random.choice(items)
        if choice == "gold":
            amt = random.randint(
                20, 80) if self.current_region == "Frostlands" else random.randint(20, 60)
            self.player.gold += amt
            self.set_info(f"You opened a chest and found {amt} gold!")
        else:
            self.player.add_item(choice, 1)
            self.set_info(f"You opened a chest and found a {choice}!")
        self.update_ui()
        self.draw_map()

    # ------------------------------
    # TOWN: Shop, Inn, NPCs (with story + Frostlands quests)
    # ------------------------------
    def enter_town(self, x, y):
        town = self.towns_by_region.get(self.current_region, {}).get((x, y))
        if not town:
            return
        choice = messagebox.askquestion(
            "Town", f"You've entered {town['name']}. Visit shop?")
        if choice == "yes":
            self.open_shop(town)
        else:
            self.open_town_menu(town)

    def open_town_menu(self, town):
        window = tk.Toplevel(self.root)
        window.title(town["name"])
        tk.Label(window, text=f"Welcome to {town['name']}!").pack(pady=6)
        tk.Button(window, text=f"Inn (heal) — {town['inn_cost']} gold", command=lambda: [
                  self.visit_inn(town), window.destroy()]).pack(fill="x", padx=8, pady=4)
        tk.Button(window, text="Talk to NPCs", command=lambda: [
                  self.talk_npcs(town), window.destroy()]).pack(fill="x", padx=8, pady=4)
        tk.Button(window, text="Open Shop", command=lambda: [
                  self.open_shop(town), window.destroy()]).pack(fill="x", padx=8, pady=4)
        tk.Button(window, text="Leave", command=window.destroy).pack(
            fill="x", padx=8, pady=6)

    def open_shop(self, town):
        shop_win = tk.Toplevel(self.root)
        shop_win.title("Shop")
        tk.Label(shop_win, text=f"Shop — Gold: {self.player.gold}").pack(
            pady=4)
        listbox = tk.Listbox(shop_win, width=48)
        for item in town["shop"]:
            if item["type"] == "consumable":
                desc = f"{item['name']} (Heal {item['heal']}) - {item['price']}g"
            elif item["type"] == "weapon":
                desc = f"{item['name']} (ATK +{item['atk']}) - {item['price']}g"
            elif item["type"] == "armor":
                desc = f"{item['name']} (DEF +{item['def']}) - {item['price']}g"
            else:
                desc = f"{item['name']} - {item['price']}g"
            listbox.insert(tk.END, desc)
        listbox.pack(padx=8, pady=4)

        def buy_selected():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            item = town["shop"][idx]
            if self.player.gold < item["price"]:
                messagebox.showinfo("Shop", "Not enough gold.")
                return
            self.player.gold -= item["price"]
            # add to inventory; equipment items are referenced by id -> SHOP_ITEMS for stats
            self.player.add_item(item["id"], 1)
            self.set_info(f"Bought {item['name']}.")
            self.update_ui()
            shop_win.destroy()

        tk.Button(shop_win, text="Buy Selected",
                  command=buy_selected).pack(pady=6)
        tk.Button(shop_win, text="Close",
                  command=shop_win.destroy).pack(pady=2)

    def visit_inn(self, town):
        cost = town["inn_cost"]
        if self.player.gold >= cost:
            self.player.gold -= cost
            self.player.hp = self.player.max_hp
            self.set_info("You rested at the inn and fully recovered.")
        else:
            self.set_info("Not enough gold for the inn.")
        self.update_ui()

    def talk_npcs(self, town):
        window = tk.Toplevel(self.root)
        window.title("NPCs")
        tk.Label(window, text=f"Town NPCs — {town['name']}").pack(pady=6)
        for npc in town["npcs"]:
            def make_cmd(n=npc):
                def cmd():
                    messagebox.showinfo(n["name"], n["dialogue"])
                    # offer region-specific quest examples
                    if "wolves" in n["dialogue"].lower():
                        self.offer_quest(kill_enemy="Wolf", amount=3)
                    # in Frostlands, NPCs may offer main quest
                    if self.current_region == "Frostlands" and "dungeon" in n["dialogue"].lower():
                        # main quest: clear the frost dungeon
                        self.offer_main_quest()
                return cmd
            tk.Button(window, text=npc["name"], command=make_cmd()).pack(
                fill="x", padx=8, pady=4)
        tk.Button(window, text="Close", command=window.destroy).pack(pady=6)

    # ------------------------------
    # QUESTS (including main storyline)
    # ------------------------------
    def create_sample_quests(self):
        # sample kill quest
        q1 = Quest("q_wolf_hunt", "Wolf Hunt", "Kill 3 Wolves in the wild.", "kill", "Wolf", 3,
                   reward={"xp": 80, "gold": 60, "item": "potion"})
        # main quest placeholder: clear frost dungeon
        q2 = Quest("q_clear_frost", "Clear the Frost Dungeon", "Enter the Frost Dungeon and defeat its boss.", "clear_dungeon", "frost_dungeon", 1,
                   reward={"xp": 300, "gold": 200, "item": "frost_blade"})
        self.quests_catalog = {"q_wolf_hunt": q1, "q_clear_frost": q2}

    def offer_quest(self, kill_enemy=None, collect_item=None):
        for qid, q in self.quests_catalog.items():
            if q.qid in self.player.quests:
                continue  # already accepted
            if kill_enemy and q.target_type == "kill" and q.target == kill_enemy:
                ans = messagebox.askyesno(
                    "Quest Offer", f"Quest offered: {q.title}\n{q.description}\nAccept?")
                if ans:
                    self.player.quests[q.qid] = Quest(
                        q.qid, q.title, q.description, q.target_type, q.target, q.amount, q.reward)
                    self.set_info(f"Quest accepted: {q.title}")
                    self.update_ui()
                return

    def offer_main_quest(self):
        # offer the frost dungeon quest if not accepted
        q = self.quests_catalog.get("q_clear_frost")
        if q and q.qid not in self.player.quests:
            ans = messagebox.askyesno(
                "Quest Offer", f"Quest offered: {q.title}\n{q.description}\nAccept?")
            if ans:
                self.player.quests[q.qid] = Quest(
                    q.qid, q.title, q.description, q.target_type, q.target, q.amount, q.reward)
                self.set_info(f"Quest accepted: {q.title}")
                self.update_ui()

    def check_quests_on_kill(self, enemy_name):
        for q in self.player.quests.values():
            if q.completed:
                continue
            if q.target_type == "kill" and q.target == enemy_name:
                q.progress_by(1)
                if q.completed:
                    self.complete_quest(q)

    def complete_quest(self, q):
        reward_texts = []
        if "xp" in q.reward:
            self.player.gain_xp(q.reward["xp"])
            reward_texts.append(f"{q.reward['xp']} XP")
        if "gold" in q.reward:
            self.player.gold += q.reward["gold"]
            reward_texts.append(f"{q.reward['gold']} gold")
        if "item" in q.reward:
            self.player.add_item(q.reward["item"], 1)
            reward_texts.append(f"1 {q.reward['item']}")
        self.set_info(
            f"Quest completed: {q.title}! Rewards: {', '.join(reward_texts)}")
        self.update_ui()

    # ------------------------------
    # BATTLE SYSTEM (region-aware and dungeon support)
    # ------------------------------
    def start_battle(self, scale=1, region="Plains", preset_enemy=None):
        if self.in_battle:
            return
        self.in_battle = True
        # choose enemy template and scale by player level or preset
        if preset_enemy:
            enemy = preset_enemy.copy()
        else:
            if region == "Frostlands":
                # biased choice toward frost enemies
                template = random.choice([t for t in ENEMY_TEMPLATES if t["name"] in (
                    "Ice Wolf", "Frost Golem", "Necromancer", "Wolf", "Bandit")])
            else:
                template = random.choice(
                    ENEMY_TEMPLATES[:3] + ENEMY_TEMPLATES[3:4])  # mix
            enemy = {
                "name": template["name"],
                "hp": int(template["hp"] * (1 + 0.1*scale)),
                "atk": int(template["atk"] * (1 + 0.08*scale)),
                "def": int(template["def"] * (1 + 0.05*scale)),
                "xp": int(template["xp"] * (1 + 0.1*scale)),
                "gold": int(template["gold"] * (1 + 0.1*scale)),
                "level": max(1, self.player.level + random.randint(-1, 2))
            }
        self.current_enemy = enemy
        self.open_battle_window()

    def open_battle_window(self):
        bw = tk.Toplevel(self.root)
        bw.title("Battle!")
        self.battle_window = bw
        tk.Label(
            bw, text=f"You encountered a {self.current_enemy['name']} (Lv {self.current_enemy['level']})").pack(pady=6)
        self.battle_log = tk.Text(bw, height=8, width=50, state="disabled")
        self.battle_log.pack(padx=6, pady=4)
        frame = tk.Frame(bw)
        frame.pack()
        tk.Button(frame, text="Attack", command=self.player_attack).pack(
            side="left", padx=6)
        tk.Button(frame, text="Heal (use potion)",
                  command=self.player_heal_battle).pack(side="left", padx=6)
        tk.Button(frame, text="Flee", command=self.player_flee).pack(
            side="left", padx=6)
        self.update_battle_status()

    def log_battle(self, txt):
        if not hasattr(self, "battle_log") or self.battle_log is None:
            return
        self.battle_log.config(state="normal")
        self.battle_log.insert(tk.END, txt + "\n")
        self.battle_log.see(tk.END)
        self.battle_log.config(state="disabled")

    def update_battle_status(self):
        if not self.battle_window:
            return
        self.battle_window.title(
            f"Battle - {self.current_enemy['name']} HP: {self.current_enemy['hp']} | You: {self.player.hp}/{self.player.max_hp}")

    def player_attack(self):
        dmg = max(1, self.player.atk_value() +
                  random.randint(-3, 3) - self.current_enemy["def"])
        self.current_enemy["hp"] -= dmg
        self.log_battle(f"You hit for {dmg} damage.")
        self.update_battle_status()
        if self.current_enemy["hp"] <= 0:
            self.log_battle("Enemy defeated!")
            self.after_enemy_defeated()
        else:
            self.root.after(700, self.enemy_turn)

    def player_heal_battle(self):
        # use best available consumable automatically if present
        if self.player.inventory.get("potion", 0) > 0:
            item = "potion"
            heal = 30
        elif self.player.inventory.get("superpotion", 0) > 0:
            item = "superpotion"
            heal = 60
        elif self.player.inventory.get("elixir", 0) > 0:
            item = "elixir"
            heal = 120
        else:
            item = None
            heal = 0

        if item:
            self.player.remove_item(item, 1)
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.log_battle(
                f"You used a {self.item_name_from_id(item)} and healed {heal} HP.")
            self.update_ui()
            self.root.after(700, self.enemy_turn)
        else:
            self.log_battle("No healing items left!")
        self.update_battle_status()

    def player_flee(self):
        if random.random() < 0.5:
            self.log_battle("You successfully fled.")
            self.end_battle()
        else:
            self.log_battle("Flee failed!")
            self.root.after(700, self.enemy_turn)

    def enemy_turn(self):
        if self.current_enemy["hp"] <= 0:
            return
        dmg = max(
            1, self.current_enemy["atk"] + random.randint(-2, 3) - self.player.def_value())
        self.player.hp -= dmg
        self.log_battle(
            f"{self.current_enemy['name']} hits you for {dmg} damage.")
        self.update_ui()
        if self.player.hp <= 0:
            self.log_battle("You were defeated...")
            self.root.after(1000, self.player_dead)
        else:
            self.update_battle_status()

    def after_enemy_defeated(self):
        xp = self.current_enemy["xp"]
        gold = self.current_enemy["gold"]
        self.player.gold += gold
        leveled = self.player.gain_xp(xp)
        self.log_battle(f"You gained {xp} XP and {gold} gold!")
        self.set_info(
            f"Defeated {self.current_enemy['name']} — +{xp} XP, +{gold} gold.")
        # update kill quests
        self.check_quests_on_kill(self.current_enemy["name"])
        # small chance to drop items, frost region drops better loots
        if random.random() < 0.3:
            if self.current_region == "Frostlands" and random.random() < 0.3:
                drop = random.choice(["superpotion", "elixir"])
            else:
                drop = random.choice(["potion", "superpotion"])
            self.player.add_item(drop, 1)
            self.log_battle(f"Enemy dropped a {drop}!")
        self.update_ui()
        self.root.after(1000, self.end_battle)

    def player_dead(self):
        loss = int(self.player.gold * 0.1)
        self.player.gold = max(0, self.player.gold - loss)
        self.player.hp = self.player.max_hp
        self.set_info(
            f"You were defeated and lost {loss} gold. You awaken at home.")
        self.player.pos = [MAP_SIZE//2, MAP_SIZE//2]
        self.update_ui()
        self.end_battle()

    def end_battle(self):
        if self.battle_window:
            self.battle_window.destroy()
            self.battle_window = None
        self.in_battle = False
        self.current_enemy = None
        self.draw_map()

    # ------------------------------
    # DUNGEON (simple multi-fight dungeon with boss)
    # ------------------------------
    def enter_dungeon(self, x, y):
        # present intro and require acceptance
        ans = messagebox.askyesno(
            "Dungeon Entrance", "A cold wind whispers from the Frost Dungeon. Enter? (This is a short dungeon run with multiple fights.)")
        if not ans:
            self.set_info("You step away from the dungeon entrance.")
            return
        # Run a simple dungeon: 3 rooms with enemies then boss
        self.set_info("You enter the Frost Dungeon...")
        dungeon_enemies = [
            {"name": "Ice Wolf", "hp": 80, "atk": 14,
                "def": 5, "xp": 45, "gold": 30},
            {"name": "Necromancer", "hp": 100, "atk": 16,
                "def": 6, "xp": 80, "gold": 50},
            {"name": "Frost Golem", "hp": 140, "atk": 20,
                "def": 10, "xp": 120, "gold": 100},
        ]
        # sequentially start battles; we will chain them via callbacks
        self.dungeon_run_index = 0
        self.dungeon_run_list = dungeon_enemies
        # the boss
        self.dungeon_boss = {"name": "Frost Warden", "hp": 220,
                             "atk": 28, "def": 12, "xp": 400, "gold": 400}
        # mark the dungeon entrance as 'opened' (so it won't retrigger unless player chooses again)
        # (we don't change the tile, but quests will track completion)
        # Start first battle:
        self.run_next_dungeon_room()

    def run_next_dungeon_room(self):
        idx = self.dungeon_run_index
        if idx < len(self.dungeon_run_list):
            enemy_template = self.dungeon_run_list[idx]
            # scale enemy a bit by player's level
            preset = {
                "name": enemy_template["name"],
                "hp": int(enemy_template["hp"] * (1 + 0.05 * (self.player.level - 1))),
                "atk": int(enemy_template["atk"] * (1 + 0.04 * (self.player.level - 1))),
                "def": int(enemy_template["def"] * (1 + 0.03 * (self.player.level - 1))),
                "xp": int(enemy_template["xp"] * (1 + 0.1 * (self.player.level - 1))),
                "gold": int(enemy_template["gold"] * (1 + 0.1 * (self.player.level - 1))),
                "level": max(1, self.player.level)
            }
            # set a callback when battle ends: chain to next room
            # We'll use a small trick: after end_battle, check if we are in dungeon and we have a callback attribute
            self.dungeon_callback_after_battle = self.run_next_dungeon_room_after
            self.start_battle(scale=self.player.level,
                              region="Frostlands", preset_enemy=preset)
        else:
            # now boss
            boss = {
                "name": self.dungeon_boss["name"],
                "hp": int(self.dungeon_boss["hp"] * (1 + 0.06 * (self.player.level - 1))),
                "atk": int(self.dungeon_boss["atk"] * (1 + 0.05 * (self.player.level - 1))),
                "def": int(self.dungeon_boss["def"] * (1 + 0.04 * (self.player.level - 1))),
                "xp": int(self.dungeon_boss["xp"] * (1 + 0.2 * (self.player.level - 1))),
                "gold": int(self.dungeon_boss["gold"] * (1 + 0.2 * (self.player.level - 1))),
                "level": max(1, self.player.level + 3)
            }
            self.dungeon_callback_after_battle = self.after_dungeon_boss
            self.start_battle(scale=self.player.level + 2,
                              region="Frostlands", preset_enemy=boss)

    def run_next_dungeon_room_after(self):
        # called after a non-boss dungeon fight finishes
        self.dungeon_run_index += 1
        # if player is alive, continue; if not, dungeon run ends in player_dead
        if self.player.hp > 0:
            self.run_next_dungeon_room()

    def after_dungeon_boss(self):
        # reward player: XP/gold handled in after_enemy_defeated; give unique drop and quest progress
        # give a guaranteed special drop
        reward_item = random.choice(["frost_blade", "crystal_armor", "elixir"])
        self.player.add_item(reward_item, 1)
        self.set_info(
            f"You defeated the Frost Warden and claimed {reward_item}!")
        # check main quest completion if player has accepted it
        q = self.player.quests.get("q_clear_frost")
        if q and not q.completed:
            q.progress_by(1)
            if q.completed:
                self.complete_quest(q)
        self.update_ui()

    # override end_battle to handle dungeon callbacks
    def end_battle(self):
        # capture whether we just ended a dungeon battle
        was_dungeon = hasattr(
            self, "dungeon_callback_after_battle") and self.dungeon_callback_after_battle is not None
        if self.battle_window:
            self.battle_window.destroy()
            self.battle_window = None
        self.in_battle = False
        # if we just finished an in-dungeon battle, call the callback
        cb = getattr(self, "dungeon_callback_after_battle", None)
        # clear current enemy
        self.current_enemy = None
        self.draw_map()
        if cb:
            # consume callback and call (defer briefly so UI updates)
            self.dungeon_callback_after_battle = None
            self.root.after(500, cb)

    # ------------------------------
    # UI WINDOWS: Inventory, Equip, Quests
    # ------------------------------
    def open_inventory_window(self):
        w = tk.Toplevel(self.root)
        w.title("Inventory Details")
        text = tk.Text(w, width=40, height=15)
        text.pack(padx=8, pady=6)
        text.insert(tk.END, f"Region: {self.current_region}\n")
        text.insert(tk.END, f"Gold: {self.player.gold}\n\n")
        text.insert(tk.END, "Items:\n")
        for item_id, count in self.player.inventory.items():
            name = self.item_name_from_id(item_id)
            text.insert(tk.END, f" - {name} x{count}\n")
        text.insert(tk.END, "\nEquipped:\n")
        for slot, item in self.player.equipment.items():
            if item:
                text.insert(tk.END, f" - {slot}: {item['name']}\n")
            else:
                text.insert(tk.END, f" - {slot}: (none)\n")
        text.config(state="disabled")
        tk.Button(w, text="Close", command=w.destroy).pack(pady=6)

    def item_name_from_id(self, iid):
        for s in SHOP_ITEMS:
            if s["id"] == iid:
                return s["name"]
        # fallback
        fallback = {
            "potion": "Potion",
            "superpotion": "Super Potion",
            "elixir": "Elixir",
            "frost_blade": "Frost Blade",
            "crystal_armor": "Crystal Armor"
        }
        return fallback.get(iid, iid)

    def open_use_item(self):
        choices = [iid for iid in self.player.inventory.keys()
                   if iid in ("potion", "superpotion", "elixir")]
        if not choices:
            messagebox.showinfo("Use Item", "No usable items.")
            return
        choice = simpledialog.askstring(
            "Use Item", f"Type item id to use: {', '.join(choices)}")
        if not choice:
            return
        if self.player.inventory.get(choice, 0) <= 0:
            messagebox.showinfo("Use Item", "You don't have that item.")
            return
        if choice == "potion":
            heal = 30
        elif choice == "superpotion":
            heal = 60
        elif choice == "elixir":
            heal = 120
        else:
            heal = 0
        self.player.remove_item(choice, 1)
        self.player.hp = min(self.player.max_hp, self.player.hp + heal)
        self.set_info(
            f"Used {self.item_name_from_id(choice)} and healed {heal} HP.")
        self.update_ui()

    def open_equip_window(self):
        w = tk.Toplevel(self.root)
        w.title("Equip/Unequip")
        lb = tk.Listbox(w, width=50)
        eq_items = []
        for itm in SHOP_ITEMS:
            if itm["type"] in ("weapon", "armor") and self.player.inventory.get(itm["id"], 0) > 0:
                eq_items.append(itm)
                lb.insert(
                    tk.END, f"{itm['name']} - {itm['type']} - Owned x{self.player.inventory.get(itm['id'], 0)}")
        lb.pack(padx=8, pady=6)

        def equip_selected():
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            itm = eq_items[idx]
            if itm["type"] == "weapon":
                self.player.equipment["weapon"] = itm
                self.set_info(f"Equipped {itm['name']}.")
            elif itm["type"] == "armor":
                self.player.equipment["armor"] = itm
                self.set_info(f"Equipped {itm['name']}.")
            self.update_ui()

        def unequip_weapon():
            self.player.equipment["weapon"] = None
            self.set_info("Unequipped weapon.")
            self.update_ui()

        def unequip_armor():
            self.player.equipment["armor"] = None
            self.set_info("Unequipped armor.")
            self.update_ui()

        tk.Button(w, text="Equip Selected",
                  command=equip_selected).pack(pady=4)
        tk.Button(w, text="Unequip Weapon",
                  command=unequip_weapon).pack(pady=2)
        tk.Button(w, text="Unequip Armor", command=unequip_armor).pack(pady=2)
        tk.Button(w, text="Close", command=w.destroy).pack(pady=6)

    def open_quests_window(self):
        w = tk.Toplevel(self.root)
        w.title("Quests")
        tk.Label(w, text="Quest Log").pack(pady=6)
        frame = tk.Frame(w)
        frame.pack(padx=8, pady=4)
        for q in self.player.quests.values():
            text = f"{q.title} — {q.description}\nProgress: {q.progress}/{q.amount} {'(Completed)' if q.completed else ''}\n"
            tk.Label(frame, text=text, justify="left",
                     wraplength=360).pack(anchor="w", pady=4)
        tk.Button(w, text="Close", command=w.destroy).pack(pady=6)

    # ------------------------------
    # HELPERS / UI UPDATES
    # ------------------------------
    def set_info(self, txt):
        self.info_label.config(text=txt)

    def update_ui(self):
        s = (f"HP: {self.player.hp}/{self.player.max_hp}\n"
             f"Level: {self.player.level} (XP {self.player.xp}/{self.player.xp_to_level})\n"
             f"ATK: {self.player.atk_value()}  DEF: {self.player.def_value()}\n"
             f"Gold: {self.player.gold}\nRegion: {self.current_region}\n")
        e = self.player.equipment
        s += f"Weapon: {e['weapon']['name'] if e['weapon'] else '(none)'}\n"
        s += f"Armor: {e['armor']['name'] if e['armor'] else '(none)'}\n"
        self.stats_label.config(text=s)

        inv_text = "Inventory:\n"
        for iid, count in self.player.inventory.items():
            inv_text += f" - {self.item_name_from_id(iid)} x{count}\n"
        if not self.player.inventory:
            inv_text += " (empty)\n"
        self.inv_label.config(text=inv_text)
        self.draw_map()

    def set_status_message(self, msg):
        self.info_label.config(text=msg)


# ------------------------------
# RUN GAME
# ------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()
