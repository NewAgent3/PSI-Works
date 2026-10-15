# Global Fan-Strike: Dust Valley

A **fan-made**, educational 3D bomb-defusal multiplayer shooter inspired by classic
Counter-Strike gameplay and the desert defusal map layout. Built with **Python**,
**Ursina (Panda3D)**, and an authoritative TCP server — same stack as the sibling
`brawl_clone` project.

**Counter-Strike, CS:GO, Dust II, and Valve are trademarks of Valve Corporation.**
This project is not affiliated with, endorsed by, or sponsored by Valve. No Valve
assets or logos are included.

## Features

- **3D first-person** multiplayer on `de_dust_valley` (block homage: Long A, Cat, Mid, B).
- **Bomb defusal**: plant / defuse, round timer, economy, buy menu, knife round.
- **Teams**: Terrorists vs Counter-Terrorists (up to 10 players).
- **Hitscan weapons**: pistols, AK/M4-style rifles, AWP-style sniper, kevlar, knife.
- **Valve charm** (legal easter eggs): Orange Box UI, loading tips, chicken on B,
  Companion Cube at CT, lambda graffiti, port `27015`, Steam Wallet jokes, GabeN
  kill-feed lines, developer console gag, and more.
- **Host Local** spawns AI bots so you can play solo immediately.

## Setup

```bat
install.bat
```

Requires **Python 3.10+**.

## Play

```bat
launch_client.bat
```

1. Enter your name and pick a team.
2. Click **Host Local (+ bots)** for instant practice, or **Join Server** for LAN.

Dedicated server:

```bat
launch_server.bat
```

Default port: **27015** (classic game-server nod).

## Controls

| Action | Key |
| --- | --- |
| Move | W A S D |
| Look | Mouse |
| Shoot | Left click / Space |
| Reload | R |
| Crouch | Ctrl / C |
| Plant / Defuse bomb | Hold E on site |
| Buy menu | B (then 1–4) |
| Developer console (joke) | ` |
| Leave match | Esc |

## LAN / Internet

- Host runs `launch_server.bat` or **Host Local** on one machine.
- Clients use the host IPv4 (`ipconfig`) and port `27015`.
- Forward **TCP 27015** for internet play.

## Project layout

```text
cs3/
  client/client.py      3D FPS client + lobby
  server/server.py      Authoritative game server
  shared/               Map layout + weapons config
  requirements.txt
  install.bat
  launch_client.bat
  launch_server.bat
```

## Direct launch

```bat
python client\client.py --no-menu --host-local --name Player --team terrorist
```

```bat
python client\client.py --no-menu --host 192.168.1.10 --port 27015 --name Player --team counter
```
