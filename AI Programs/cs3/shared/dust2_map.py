"""
de_dust_valley — a block-layout homage to the classic desert defusal map.
Not affiliated with Valve. Layout evokes Long A, Cat, Mid, and B Tunnels.
"""
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Wall:
    x: float
    z: float
    hw: float  # half width (x extent)
    hd: float  # half depth (z extent)
    h: float = 4.0
    kind: str = "wall"  # wall | crate | door


@dataclass
class Prop:
    x: float
    z: float
    y: float
    kind: str
    label: str = ""


MAP_NAME = "de_dust_valley"
FLOOR_SIZE = 100.0
SKY_TINT = (0.55, 0.42, 0.28)
SAND_COLOR = (0.76, 0.62, 0.38)
WALL_COLOR = (0.62, 0.52, 0.40)
CRATE_COLOR = (0.45, 0.35, 0.22)

# Bombsites (center x, z, radius)
BOMBSITE_A = (-32.0, 28.0, 7.0)
BOMBSITE_B = (30.0, 22.0, 7.0)

PLANT_TIME = 3.2
DEFUSE_TIME = 5.0
BOMB_TIMER = 40.0

T_SPAWNS = [(38.0, -32.0), (42.0, -28.0), (35.0, -35.0), (40.0, -38.0)]
CT_SPAWNS = [(-38.0, 36.0), (-42.0, 32.0), (-35.0, 40.0), (-40.0, 38.0)]

# Valve-flavoured map callouts (client HUD)
CALLOUTS = [
    {"name": "Long A", "x": 18, "z": 10},
    {"name": "Cat", "x": -5, "z": 8},
    {"name": "Mid", "x": 0, "z": -2},
    {"name": "B Tunnels", "x": 22, "z": 12},
    {"name": "B Site", "x": 30, "z": 22},
    {"name": "A Site", "x": -32, "z": 28},
    {"name": "CT Spawn", "x": -38, "z": 36},
    {"name": "T Spawn", "x": 38, "z": -32},
]

# Chicken on B (iconic community meme)
CHICKEN_PROP = Prop(28.0, 20.0, 0.35, "chicken", "Nuggets Jr.")

# Companion cube nod (Portal) at CT
COMPANION_CUBE = Prop(-36.0, 34.0, 0.5, "cube", "Weighted Companion Cube")

# Lambda graffiti (Half-Life)
LAMBDA_PROP = Prop(-28.0, 26.0, 2.2, "lambda", "λ")


def _box(x, z, hw, hd, h=4.0, kind="wall") -> Wall:
    return Wall(x=x, z=z, hw=hw, hd=hd, h=h, kind=kind)


def build_walls() -> List[Wall]:
    w: List[Wall] = []

    # Outer perimeter (open sky — low outer lip only for bounds)
    w.append(_box(0, -48, 50, 1.5, 6))
    w.append(_box(0, 48, 50, 1.5, 6))
    w.append(_box(-50, 0, 1.5, 48, 6))
    w.append(_box(50, 0, 1.5, 48, 6))

    # --- CT spawn / A site (northwest) ---
    w.append(_box(-38, 32, 8, 6, 5))  # CT back wall
    w.append(_box(-32, 28, 9, 9, 3.5))  # A site platform lip
    w.append(_box(-22, 32, 2, 8, 4))  # A site entry choke
    w.append(_box(-14, 28, 2, 6, 4))

    # Long A corridor walls (T -> A)
    w.append(_box(28, 8, 2, 18, 4))
    w.append(_box(20, 12, 2, 14, 4))
    w.append(_box(12, 16, 2, 10, 4))
    w.append(_box(6, 20, 2, 8, 3.5))
    # Long A pit boxes
    w.append(_box(24, 4, 3, 3, 2.5, "crate"))
    w.append(_box(16, 8, 2.5, 2.5, 2.5, "crate"))
    w.append(_box(10, 14, 2, 2, 2, "crate"))

    # Catwalk / short (mid to A)
    w.append(_box(-6, 14, 10, 1.5, 3))
    w.append(_box(-8, 8, 1.5, 8, 4))
    w.append(_box(-2, 6, 8, 1.5, 2.5))

    # --- Mid ---
    w.append(_box(0, -4, 14, 2, 4))  # mid divider
    w.append(_box(-4, -12, 2, 10, 4))
    w.append(_box(6, -12, 2, 10, 4))
    w.append(_box(0, -18, 8, 2, 3.5))  # mid doors sill
    w.append(_box(-8, -8, 3, 3, 2.5, "crate"))
    w.append(_box(8, -8, 3, 3, 2.5, "crate"))
    w.append(_box(0, -10, 2, 2, 2, "crate"))

    # Mid to B upper
    w.append(_box(14, 4, 2, 12, 4))
    w.append(_box(20, 10, 2, 8, 4))

    # --- T spawn (southeast) ---
    w.append(_box(38, -32, 7, 7, 4))
    w.append(_box(32, -26, 2, 8, 3.5))
    w.append(_box(42, -26, 2, 6, 3.5))

    # Tunnels to B
    w.append(_box(28, 0, 2, 14, 4))
    w.append(_box(32, 8, 2, 10, 4))
    w.append(_box(36, 16, 2, 8, 4))
    w.append(_box(26, 14, 6, 2, 3.5))
    w.append(_box(30, 18, 2, 6, 3.5))

    # B site
    w.append(_box(30, 22, 9, 8, 3.5))
    w.append(_box(22, 20, 2, 6, 4))
    w.append(_box(38, 18, 2, 5, 4))
    w.append(_box(28, 16, 2, 2, 2, "crate"))
    w.append(_box(34, 24, 2.5, 2.5, 2.5, "crate"))
    w.append(_box(32, 20, 2, 2, 2, "crate"))

    # CT mid hold
    w.append(_box(-18, -6, 2, 12, 4))
    w.append(_box(-12, 0, 2, 8, 3.5))

    return w


def build_props() -> List[Prop]:
    return [CHICKEN_PROP, COMPANION_CUBE, LAMBDA_PROP]


def wall_dicts() -> List[dict]:
    return [
        {"x": w.x, "z": w.z, "hw": w.hw, "hd": w.hd, "h": w.h, "kind": w.kind}
        for w in build_walls()
    ]


def prop_dicts() -> List[dict]:
    return [
        {"x": p.x, "z": p.z, "y": p.y, "kind": p.kind, "label": p.label}
        for p in build_props()
    ]


def in_bombsite(x: float, z: float, site: str) -> bool:
    if site == "A":
        cx, cz, r = BOMBSITE_A
    else:
        cx, cz, r = BOMBSITE_B
    return (x - cx) ** 2 + (z - cz) ** 2 <= r * r


def nearest_site(x: float, z: float) -> str | None:
    if in_bombsite(x, z, "A"):
        return "A"
    if in_bombsite(x, z, "B"):
        return "B"
    return None
