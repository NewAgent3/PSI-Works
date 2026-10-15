"""
Weapons, economy, and round rules — Counter-Strike inspired, original names.
"""
TICK_RATE = 64
MAX_PLAYERS = 10
ROUND_TIME = 115.0
FREEZE_TIME = 5.0
ROUNDS_TO_WIN = 9
DEFAULT_PORT = 27015  # nod to classic dedicated servers

PLAYER_RADIUS = 0.42
PLAYER_HEIGHT = 1.75
WALK_SPEED = 5.2
CROUCH_SPEED = 2.8
GRAVITY = 18.0  # unused in xz-only mode but reserved

TEAM_T = "terrorist"
TEAM_CT = "counter"

START_MONEY = 800
MAX_MONEY = 16000
WIN_BONUS = 3250
LOSS_BONUS = 1400
LOSS_STREAK_BONUS = 500
KILL_REWARD = 300
PLANT_REWARD = 300
DEFUSE_REWARD = 300

# weapon_id: damage, fire_rate, mag, reserve, price, range, spread, armor_pen, team
WEAPONS = {
    "knife": {
        "name": "Crowbar Mk.II",  # valve universe nod
        "dmg": 55,
        "fire_rate": 0.55,
        "mag": 1,
        "reserve": 0,
        "price": 0,
        "range": 2.2,
        "spread": 0,
        "team": "both",
        "slot": "melee",
    },
    "glock": {
        "name": "Glock-18 (fan)",
        "dmg": 28,
        "fire_rate": 0.12,
        "mag": 20,
        "reserve": 120,
        "price": 0,
        "range": 45,
        "spread": 0.04,
        "team": TEAM_T,
        "slot": "secondary",
    },
    "usp": {
        "name": "USP-S (fan)",
        "dmg": 30,
        "fire_rate": 0.14,
        "mag": 12,
        "reserve": 100,
        "price": 0,
        "range": 45,
        "spread": 0.03,
        "team": TEAM_CT,
        "slot": "secondary",
    },
    "ak47": {
        "name": "Kalash-47",
        "dmg": 36,
        "fire_rate": 0.095,
        "mag": 30,
        "reserve": 90,
        "price": 2700,
        "range": 70,
        "spread": 0.035,
        "team": TEAM_T,
        "slot": "primary",
    },
    "m4a1": {
        "name": "M4A1-S (fan)",
        "dmg": 33,
        "fire_rate": 0.09,
        "mag": 25,
        "reserve": 75,
        "price": 2900,
        "range": 70,
        "spread": 0.03,
        "team": TEAM_CT,
        "slot": "primary",
    },
    "awp": {
        "name": "Magnum Scout-90",
        "dmg": 108,
        "fire_rate": 1.2,
        "mag": 5,
        "reserve": 30,
        "price": 4750,
        "range": 100,
        "spread": 0.002,
        "team": "both",
        "slot": "primary",
    },
    "kevlar": {
        "name": "Kevlar + Helmet",
        "dmg": 0,
        "fire_rate": 0,
        "mag": 0,
        "reserve": 0,
        "price": 1000,
        "range": 0,
        "spread": 0,
        "team": "both",
        "slot": "gear",
    },
}

BUY_MENU_ORDER = ["ak47", "m4a1", "awp", "kevlar"]

VALVE_LOADING_TIPS = [
    "Welcome to Global Fan-Strike. Valve is not affiliated with this project.",
    "The cake is a lie, but the bomb is real.",
    "Remember: rush B, blame lag, type gg.",
    "In the event of fiscal apology, accept it gracefully.",
    "Gabe Newell has logged off. The economy remains.",
    "Steam Wallet: insufficient funds? Try eco round.",
    "Half-Life 3 confirmed — in this loading tip only.",
    "Weighted Companion Cube will not talk. It will not betray you.",
    "Real Valve Time adds 0–∞ delay to patch notes.",
    "Chicken on B is community approved since 2013.",
    "Counter-Terrorists: defuse. Terrorists: plant. Lawyers: don't sue us.",
    "Orange Box nostalgia sold separately.",
    "Type 'sv_cheats 1' in console for absolutely nothing.",
    "Dota players: mid or feed also applies here.",
    "Portal gun not included in Standard Edition.",
]

VALVE_KILL_PHRASES = [
    "GabeN approves this headshot.",
    "Accept our fiscal apology.",
    "Valve Anti-Cheat is watching (it isn't).",
    "Cyka — I mean, nice shot!",
    "Steam achievement unlocked: Probably Not Real.",
]
