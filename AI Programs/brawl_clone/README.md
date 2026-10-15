# Brawl Clone

A fan-made 3D top-down arena shooter inspired by Brawl Stars, built in Python
with Ursina/Panda3D and a small authoritative TCP server.

This is a personal/educational project. Brawl Stars is owned by Supercell.

## What Is Included

- A proper in-game lobby instead of command-line prompts.
- Player name, server host, server port, and brawler selection in the client UI.
- One-click local hosting from the client with **Host Local**.
- LAN/online play through the standalone server.
- 9 brawlers: Spike, Edgar, Buzz, Damian, Lumi, Sirius, Alli, Kaze, and Kit.
- Server-authoritative movement, projectiles, damage, respawns, bushes, walls,
  and scoreboard state.
- **Host Local** fills the arena with 3 AI bots for solo practice.
- 3-minute matches with a winner screen (most kills wins ties).
- Bush stealth: enemies hidden in bushes until they shoot.

## Setup

1. Install Python 3.10 or newer.
2. Run:

```bat
install.bat
```

## Play Locally

Run:

```bat
launch_client.bat
```

In the lobby:

- Choose a name.
- Pick a brawler.
- Click **Host Local**.

The client starts a local server in the background and joins it automatically.

## Join A Server

1. On the host machine, run:

```bat
launch_server.bat
```

Optional bots on a dedicated server (spawn when the first player joins):

```bat
python server\server.py --bots 4
```

2. On each client, run:

```bat
launch_client.bat
```

3. Enter the host IP in the lobby and click **Join Server**.

For LAN play, the host IP is usually shown as the IPv4 address in `ipconfig`.
For internet play, forward TCP port `5555` to the host machine.

## Controls

| Action | Key |
| --- | --- |
| Move | W A S D or arrow keys |
| Aim | Mouse |
| Shoot | Left click or Space |
| Scoreboard | Hold Tab |
| Leave match | Esc |
| Match timer | Top center (3:00 FFA) |
| Kill feed | Top right |

## Direct Launch Options

The lobby is the default. For automation or quick testing, direct connect is
still available:

```bat
python client\client.py --no-menu --host 127.0.0.1 --port 5555 --name Player --brawler spike
```

Start a local embedded server and connect immediately:

```bat
python client\client.py --no-menu --host-local --name Player --brawler spike
```

## Project Layout

```text
brawl_clone/
  assets/
    glb/              character models loaded by Ursina
    textures/         matching brawler textures
  client/client.py    Ursina client, lobby, rendering, and networking
  server/server.py    authoritative asyncio TCP server
  requirements.txt
  install.bat
  launch_client.bat
  launch_server.bat
```

## Troubleshooting

- `ModuleNotFoundError: ursina`: run `install.bat`.
- Cannot connect: make sure the server is running, the IP is correct, and the
  firewall allows Python on TCP port `5555`.
- Port already in use: change the port in the lobby or stop the other server.
- Models look untextured: make sure `assets/textures/<brawler>.png` exists.
