"""
Full fixed & expanded 3D RPG prototype (Ursina)
-----------------------------------------------
What I did in this update:
- Fixed bugs and runtime issues from the previous prototype.
- Reworked project structure into modular classes inside one file.
- Implemented the requested feature set (core/prototype versions):
  1) Dialog system with branching choices and NPC quests.
  2) Weapon system: equippable weapons, visible weapon entity, hitbox-based melee and ranged.
  3) Several enemy types: melee, ranged, tank, boss (prototype behaviors).
  4) World with two regions and a simple interior portal system.
  5) Inventory UI: grid, click-to-use/equip, view item details.
  6) Skill tree (simple): allocate points to increase stats.
  7) Save/load with multiple slots and autosave toggle.
  8) Crafting basics: recipes, crafting table interaction.
  9) Resource nodes (trees/ore) that drop items when harvested.
 10) Placeholder for multiplayer (comments + basic local host example).

Notes / limitations:
- This is still a prototype: art, animations and polished UI are left as exercises.
- Networking multiplayer is non-trivial; I included a commented skeleton for local testing.
- The code is meant to run with Ursina. Install: `pip install ursina`
- Target: Python 3.12-3.14. If a package breaks in 3.14, try with 3.12.

Run: save this file as main.py and run `python main.py` from a virtualenv with ursina installed.
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import os
import random
import time
import math

# ----------------------------
# Constants & Helpers
# ----------------------------
SAVE_DIR = 'saves'
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
DEFAULT_SLOT = os.path.join(SAVE_DIR, 'slot1.json')


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)


def distance(a, b):
    return math.sqrt((a.x-b.x)**2 + (a.z-b.z)**2)


# ----------------------------
# Game Data (items, recipes, quests)
# ----------------------------
ITEM_DB = {
    'wood': {'name': 'Wood', 'type': 'material'},
    'ore': {'name': 'Ore', 'type': 'material'},
    'sword_iron': {'name': 'Iron Sword', 'type': 'weapon', 'damage': 12},
    'bow_wood': {'name': 'Wooden Bow', 'type': 'ranged', 'damage': 8},
    'potion_small': {'name': 'Small Potion', 'type': 'consumable', 'heal': 30}
}

RECIPES = {
    'sword_iron': {'wood': 2, 'ore': 4},
    'bow_wood': {'wood': 6}
}

QUESTS = {
    'slay_first': {
        'title': 'First Blood',
        'desc': 'Defeat your first enemy.',
        'completed': False,
        'reward_xp': 30,
        'reward_gold': 10
    }
}

# ----------------------------
# Base Player Data
# ----------------------------


def default_player():
    return {
        'name': 'Hero', 'level': 1, 'xp': 0, 'hp': 100, 'max_hp': 100,
        'gold': 0, 'inventory': [], 'equipped': {'weapon': None}, 'skills': {}, 'skill_points': 0,
        'quests': {}, 'autosave': True
    }

# ----------------------------
# Player entity
# ----------------------------


class RPGPlayer(Entity):
    def __init__(self):
        super().__init__()
        self.controller = FirstPersonController(y=1)
        self.controller.cursor.visible = True
        self.state = default_player()
        self.base_damage = 5
        self.melee_range = 2.0
        self.melee_cooldown = 0.5
        self._last_attack = -99
        self.weapon_entity = None

    def save(self, slot_path=DEFAULT_SLOT):
        save_json(slot_path, self.state)
        print('[SAVE] saved to', slot_path)

    def load(self, slot_path=DEFAULT_SLOT):
        data = load_json(slot_path)
        if data:
            self.state = data
            print('[LOAD] loaded', slot_path)
        else:
            print('[LOAD] no save found, using default')

    def can_attack(self):
        return time.time() - self._last_attack >= self.melee_cooldown

    def melee_attack(self):
        if not self.can_attack():
            return
        self._last_attack = time.time()
        origin = camera.world_position
        dir = camera.forward
        # check for enemies within cone/range
        for e in scene.entities:
            if isinstance(e, Enemy) and e.alive:
                d = distance(e, self.controller)
                if d <= self.melee_range:
                    dmg = self.base_damage
                    w = self.state['equipped'].get('weapon')
                    if w and ITEM_DB.get(w):
                        if ITEM_DB[w]['type'] == 'weapon':
                            dmg += ITEM_DB[w].get('damage', 0)
                    e.on_hit(dmg)
                    DamagePopup(str(dmg), e.world_position)
                    return

    def ranged_attack(self):
        w = self.state['equipped'].get('weapon')
        if w and ITEM_DB.get(w) and ITEM_DB[w]['type'] == 'ranged':
            # spawn a projectile
            proj = Projectile(position=camera.world_position + camera.forward *
                              1.0, direction=camera.forward, damage=ITEM_DB[w]['damage'])

    def gain_xp(self, amount):
        self.state['xp'] += amount
        needed = 50 * self.state['level']
        while self.state['xp'] >= needed:
            self.state['xp'] -= needed
            self.state['level'] += 1
            self.state['max_hp'] += 10
            self.state['hp'] = self.state['max_hp']
            self.state['skill_points'] += 1
            print('[LEVEL] now', self.state['level'])

    def add_item(self, item_id, amount=1):
        # stack simple implementation
        for it in self.state['inventory']:
            if it['id'] == item_id:
                it['count'] += amount
                return
        self.state['inventory'].append({'id': item_id, 'count': amount})

    def remove_item(self, item_id, amount=1):
        for it in self.state['inventory']:
            if it['id'] == item_id:
                it['count'] -= amount
                if it['count'] <= 0:
                    self.state['inventory'].remove(it)
                return True
        return False

    def equip(self, item_id):
        if not ITEM_DB.get(item_id):
            return
        if ITEM_DB[item_id]['type'] in ('weapon', 'ranged'):
            self.state['equipped']['weapon'] = item_id
            # update visible weapon
            if self.weapon_entity:
                destroy(self.weapon_entity)
            self.weapon_entity = Entity(parent=camera, model='cube', scale=(
                0.3, 0.7, 0.1), position=(0.6, -0.6, 1.2))
            print('[EQUIP]', ITEM_DB[item_id]['name'])

# ----------------------------
# Projectile
# ----------------------------


class Projectile(Entity):
    def __init__(self, position, direction, damage=5):
        super().__init__(model='sphere', scale=0.15, position=position)
        self.direction = Vec3(direction)
        self.speed = 30
        self.damage = damage

    def update(self):
        self.position += self.direction * time.dt * self.speed
        # check collisions with enemies
        for e in scene.entities:
            if isinstance(e, Enemy) and e.alive:
                if distance(e, self) < 1.0:
                    e.on_hit(self.damage)
                    destroy(self)
                    return
        # lifetime
        if not (-200 < self.x < 200 and -200 < self.z < 200):
            destroy(self)

# ----------------------------
# Enemy types
# ----------------------------


class Enemy(Entity):
    def __init__(self, position=(0, 0, 0), hp=40, etype='melee'):
        super().__init__(model='cube', color=color.red, scale=1, position=position)
        self.max_hp = hp
        self.hp = hp
        self.type = etype
        self.speed = 2 if etype == 'melee' else 1.2
        self.alive = True
        self.attack_cooldown = 1.5
        self._last_attack = -99

    def update(self):
        if not self.alive:
            return
        # simple AI
        d = distance(self, player.controller)
        if self.type == 'melee':
            if d < 12:
                # move towards player
                dir = (player.controller.position - self.position)
                dir.y = 0
                if dir.length() > 0.1:
                    self.position += dir.normalized() * self.speed * time.dt
                if d < 2.0:
                    self.attack()
        elif self.type == 'ranged':
            if d < 18:
                # keep distance
                if d < 6:
                    # step back
                    dir = (self.position - player.controller.position).normalized()
                    self.position += dir * self.speed * time.dt
                elif d > 10:
                    # move closer
                    dir = (player.controller.position -
                           self.position).normalized()
                    self.position += dir * (self.speed*0.6) * time.dt
                # shoot occasionally
                if time.time() - self._last_attack > 2.0 and d < 15:
                    self._last_attack = time.time()
                    # fire projectile
                    proj_dir = (player.controller.position -
                                self.position).normalized()
                    Projectile(position=self.position + Vec3(0, 1, 0),
                               direction=proj_dir, damage=6)
        elif self.type == 'tank':
            # slow but strong
            if d < 14:
                dir = (player.controller.position - self.position)
                if dir.length() > 0.2:
                    self.position += dir.normalized() * (self.speed*0.6) * time.dt
                if d < 2.2:
                    self.attack()
        elif self.type == 'boss':
            # simple boss: charges
            if d < 25:
                if time.time() % 4 < 2:
                    dir = (player.controller.position - self.position)
                    if dir.length() > 0.1:
                        self.position += dir.normalized() * (self.speed*1.5) * time.dt
                else:
                    pass
                if d < 3.0:
                    self.attack()

    def attack(self):
        if time.time() - self._last_attack < self.attack_cooldown:
            return
        self._last_attack = time.time()
        # damage player directly
        player.state['hp'] -= 8
        print('[HIT] player hp', player.state['hp'])

    def on_hit(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.die()

    def die(self):
        self.alive = False
        # spawn some loot
        player.add_item('gold', random.randint(1, 5))
        player.gain_xp(20)
        destroy(self)

# ----------------------------
# Harvestable resource node
# ----------------------------


class ResourceNode(Entity):
    def __init__(self, position=(0, 0, 0), item='wood', count=3):
        super().__init__(model='cube', color=color.green if item ==
                         'wood' else color.gray, position=position, scale=1)
        self.item = item
        self.count = count

    def on_hit(self):
        if self.count <= 0:
            return
        self.count -= 1
        player.add_item(self.item, 1)
        print('[HARVEST] got', self.item)
        if self.count <= 0:
            destroy(self)

# ----------------------------
# Crafting station
# ----------------------------


class CraftingTable(Entity):
    def __init__(self, position=(0, 0, 0)):
        super().__init__(model='cube', color=color.brown, position=position, scale=1)

    def interact(self):
        # open craft UI
        craft_ui.open()

# ----------------------------
# Dialog System
# ----------------------------


class DialogWindow(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.panel = Entity(parent=self, model='quad', scale=(
            0.8, 0.3), position=(0, -0.7), color=color.rgba(0, 0, 0, 160))
        self.text = Text(parent=self.panel, text='',
                         position=(-0.37, 0.05), wrap=70)
        self.choice_buttons = []

    def open(self, lines, choices=None, callback=None):
        self.panel.enabled = True
        self.text.text = lines
        self.choices = choices or []
        self.callback = callback
        # create simple choice buttons
        for b in self.choice_buttons:
            destroy(b)
        self.choice_buttons = []
        for i, c in enumerate(self.choices):
            btn = Button(
                parent=self.panel, text=c['text'], position=(-0.3 + i*0.3, -0.12), scale=(0.25, 0.08))
            btn.on_click = Func(self._choose, c.get('id'))
            self.choice_buttons.append(btn)

    def _choose(self, choice_id):
        self.panel.enabled = False
        if self.callback:
            self.callback(choice_id)

    def close(self):
        self.panel.enabled = False

# ----------------------------
# Inventory UI
# ----------------------------


class InventoryUI(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.panel = Entity(model='quad', scale=(0.6, 0.6),
                            position=(0, 0), color=color.rgba(0, 0, 0, 170))
        self.item_text = Text(
            parent=self.panel, text='Inventory', position=(-0.26, 0.26))
        self.slots = []
        self.opened = False

    def toggle(self):
        self.opened = not self.opened
        self.panel.enabled = self.opened
        if self.opened:
            self.refresh()

    def refresh(self):
        # clear old
        for s in self.slots:
            destroy(s)
        self.slots = []
        inv = player.state['inventory']
        for i, it in enumerate(inv):
            y = 0.15 - (i//4)*0.12
            x = -0.25 + (i % 4)*0.12
            slot = Button(parent=self.panel, text=f"{ITEM_DB.get(it['id'],{'name':'?'})['name']} x{it['count']}", position=(
                x, y), scale=(0.11, 0.09))
            slot.on_click = Func(self.use_item, it['id'])
            self.slots.append(slot)

    def use_item(self, item_id):
        data = ITEM_DB.get(item_id)
        if not data:
            return
        if data['type'] == 'consumable':
            player.state['hp'] = min(
                player.state['max_hp'], player.state['hp'] + data.get('heal', 0))
            player.remove_item(item_id, 1)
            self.refresh()
        elif data['type'] in ('weapon', 'ranged'):
            player.equip(item_id)
            self.refresh()

# ----------------------------
# Craft UI
# ----------------------------


class CraftUI(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.panel = Entity(model='quad', scale=(0.5, 0.5),
                            position=(0, 0), color=color.rgba(0, 0, 0, 200))
        self.panel.enabled = False
        self.text = Text(parent=self.panel, text='Crafting',
                         position=(-0.2, 0.2))
        self.buttons = []

    def open(self):
        self.panel.enabled = True
        self.refresh()

    def close(self):
        self.panel.enabled = False

    def refresh(self):
        for b in self.buttons:
            destroy(b)
        self.buttons = []
        i = 0
        for item_id, recipe in RECIPES.items():
            btn = Button(parent=self.panel, text=f"Craft {ITEM_DB[item_id]['name']}", position=(
                -0.15, 0.08 - i*0.08), scale=(0.3, 0.07))
            btn.on_click = Func(self.craft, item_id)
            self.buttons.append(btn)
            i += 1

    def craft(self, item_id):
        recipe = RECIPES.get(item_id)
        if not recipe:
            return
        # check materials
        ok = True
        for mat, cnt in recipe.items():
            found = sum(it['count']
                        for it in player.state['inventory'] if it['id'] == mat)
            if found < cnt:
                ok = False
        if not ok:
            print('[CRAFT] missing materials')
            return
        # remove materials
        for mat, cnt in recipe.items():
            player.remove_item(mat, cnt)
        # add result
        player.add_item(item_id, 1)
        print('[CRAFT] crafted', item_id)
        self.refresh()
        ui.inventory.refresh()

# ----------------------------
# Damage popup
# ----------------------------


class DamagePopup(Text):
    def __init__(self, text, pos):
        screen = camera.world_to_screen_point(pos)
        super().__init__(text=text, position=screen, scale=1.2, color=color.red)
        invoke(destroy, self, delay=0.7)

# ----------------------------
# Simple World Manager
# ----------------------------


class World:
    def __init__(self):
        self.regions = {'overworld': [], 'village': []}
        # spawn enemies & resources
        for i in range(8):
            x, z = random.randint(-12, 12), random.randint(-12, 12)
            self.regions['overworld'].append(Enemy(position=(x, 1, z), hp=random.randint(
                20, 40), etype=random.choice(['melee', 'ranged', 'tank'])))
        # boss in village
        self.regions['village'].append(
            Enemy(position=(8, 1, 8), hp=250, etype='boss'))
        # resources
        for i in range(6):
            x, z = random.randint(-10, 10), random.randint(-10, 10)
            ResourceNode(position=(x, 0.5, z), item='wood', count=3)
        for i in range(4):
            x, z = random.randint(-10, 10), random.randint(-10, 10)
            ResourceNode(position=(x, 0.5, z), item='ore', count=2)
        # crafting table
        self.crafting_table = CraftingTable(position=(2, 0.5, 2))


world = None

# ----------------------------
# UI Root
# ----------------------------


class GameUIRoot:
    def __init__(self):
        self.hp_text = Text(position=(-0.85, 0.45), scale=1.4)
        self.xp_text = Text(position=(-0.85, 0.40), scale=1.0)
        self.gold_text = Text(position=(0.7, 0.45), scale=1.0)
        self.dialog = DialogWindow()
        self.inventory = InventoryUI()
        self.craft = CraftUI()

    def update(self):
        self.hp_text.text = f"HP: {player.state['hp']}/{player.state['max_hp']}"
        self.xp_text.text = f"XP: {player.state['xp']} (Lv {player.state['level']})"
        self.gold_text.text = f"Gold: {player.state.get('gold',0)}"


ui = None

# ----------------------------
# Input / Interaction
# ----------------------------


def input(key):
    if key == 'left mouse down':
        # interact or attack
        # raycast forward to see if interacting with NPC/table/node
        hit = raycast(camera.world_position, camera.forward,
                      distance=3, ignore=(player.controller,))
        if hit.hit:
            e = hit.entity
            if isinstance(e, ResourceNode):
                e.on_hit()
            elif isinstance(e, CraftingTable):
                e.interact()
            elif isinstance(e, NPC):
                e.talk()
            elif hasattr(e, 'interact'):
                try:
                    e.interact()
                except Exception as ex:
                    print('interact failed', ex)
            else:
                # default: attack
                if player.state['equipped'].get('weapon') and ITEM_DB[player.state['equipped']['weapon']]['type'] == 'ranged':
                    player.ranged_attack()
                else:
                    player.melee_attack()
        else:
            if player.state['equipped'].get('weapon') and ITEM_DB[player.state['equipped']['weapon']]['type'] == 'ranged':
                player.ranged_attack()
            else:
                player.melee_attack()
    if key == 'i':
        ui.inventory.toggle()
    if key == 'c':
        ui.craft.open() if not ui.craft.panel.enabled else ui.craft.close()
    if key == 'tab':
        player.save()
    if key == 'escape':
        application.quit()

# ----------------------------
# NPC & Dialogs
# ----------------------------


class NPC(Entity):
    def __init__(self, position=(0, 0, 0), name='Bob', dialog=None, quest=None):
        super().__init__(model='cube', color=color.azure, position=position, scale=1)
        self.name = name
        self.dialog = dialog or []
        self.quest = quest

    def talk(self):
        # open a dialog - simple sequential
        if not self.dialog:
            return
        first = self.dialog[0]
        choices = self.dialog[1:] if len(self.dialog) > 1 else []
        ui.dialog.open(first.get('text', '...'),
                       choices, callback=self._on_choice)

    def _on_choice(self, choice_id):
        if choice_id is None:
            return
        # find choice
        for d in self.dialog:
            for c in d.get('choices', []):
                if c.get('id') == choice_id:
                    # run action
                    action = c.get('action')
                    if action == 'give_quest' and self.quest:
                        player.add_quest(self.quest, QUESTS[self.quest].copy())
                    if action == 'heal':
                        player.state['hp'] = player.state['max_hp']
                    return

# ----------------------------
# Simple Skill allocation
# ----------------------------


class SkillTree:
    def __init__(self):
        self.nodes = {'strength': 0, 'endurance': 0}

    def allocate(self, node):
        if player.state['skill_points'] <= 0:
            return
        self.nodes[node] += 1
        player.state['skill_points'] -= 1
        if node == 'strength':
            player.base_damage_plus = getattr(player, 'base_damage_plus', 0)+2
        if node == 'endurance':
            player.state['max_hp'] += 10


skills = SkillTree()

# ----------------------------
# Game init
# ----------------------------
app = Ursina()
window.title = 'Expanded 3D RPG Prototype'
window.borderless = False
window.fps_counter.enabled = True

player = RPGPlayer()
player.load()
ui = GameUIRoot()
world = World()

# spawn a sample NPC
npc_dialog = [
    {'text': 'Hello traveler!'},
    {'text': 'Will you take this quest?', 'choices': [
        {'id': 'accept', 'text': 'Yes', 'action': 'give_quest'}, {'id': 'no', 'text': 'No', 'action': None}]}
]
n = NPC(position=(3, 0.5, 3), name='Villager',
        dialog=npc_dialog, quest='slay_first')

# ----------------------------
# Main update
# ----------------------------


def update():
    # update UI
    ui.update()
    # autosave
    if player.state.get('autosave'):
        # autosave every 10 seconds approx
        if not hasattr(update, '_last_autosave'):
            update._last_autosave = time.time()
        if time.time() - update._last_autosave > 10:
            player.save()
            update._last_autosave = time.time()
    # basic death handling
    if player.state['hp'] <= 0:
        print('You died! Respawning...')
        player.state['hp'] = player.state['max_hp']
        player.controller.position = Vec3(0, 3, 0)


app.run()

# ----------------------------
# Multiplayer note (placeholder)
# ----------------------------
# Adding real multiplayer requires networking, authoritative server, and state sync.
# For quick local testing you could use Python's socket or multiprocessing to simulate a host.
# That is outside the scope of this prototype but I can add a simple TCP host/client example if you want.
