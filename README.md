# Agar.io clone

Python clone of agar.io, made with pygame. Requires Python 3.9+.

![Screenshot](https://cloud.githubusercontent.com/assets/13442473/10423082/287f4852-711f-11e5-8882-9cef137180eb.png "Screenshot")

## Install
```
python3 -m pip install -r requirements.txt
```

## Run
```
python3 agar.py
```
Headless smoke test: `SDL_VIDEODRIVER=dummy python3 agar.py --frames 600`

## Controls
- Mouse: move (the farther the pointer from the screen centre, the faster you go)
- Space: split each cell of mass 35 or more in half (up to 16 cells)
- W: eject mass from each cell of mass 32 or more (cost 18, projectile mass 14)
- Esc: quit

## Tests
```
python3 -m pytest
```
Tests run without a window and do not import pygame.

Split halves launch toward the pointer, with velocity multiplied by 0.9 each
tick (below 1% in about 0.73 seconds). Their merge cooldown is 10 seconds plus
0.05 seconds per unit of half-mass, measured at 60 FPS. During cooldown, own
cells repel; afterwards they merge when their centres are within half the sum
of their radii, conserving mass and momentum. Ejected mass also slows by 0.9
per tick and can be eaten by any larger cell covering its centre; the exact
source cell cannot eat it for the first eight ticks. Each shot loses four mass
units overall. Positions stay inside the map.

The map maintains at least 18 green spiked viruses of base mass 100. New ones
spawn outside living cells' radii, with an extra virus radius and 80 units of
clearance. Crowded maps retry spawning on later ticks. A cell with at least
1.25 times a virus's current mass can swallow it using the normal eating
overlap rule. It gains the virus mass and bursts into equal pieces aiming for
mass 20 each, limited to 16 total cells. Pieces launch radially at speed 20
and use the ordinary split merge cooldown; at the cell cap only mass and
cooldown are added. Smaller cells pass through and can hide underneath viruses.

Ejected shots feed viruses before players can eat the shots. Each hit adds
the shot's mass; the seventh resets the parent to mass 100 and launches a new
mass-100 virus at speed 18 along the last shot's direction. The reset is a
gameplay rule and does not conserve projectile mass. Launched viruses use the
same 0.9 impulse damping as cells. Virus hits and bursts resolve before
player-vs-player eating, and population replenishment follows bot respawning.
Large bots treat edible viruses as threats. Rendering orders cells and viruses
by mass, allowing small cells to hide under viruses and large ones to cover them.

## Structure
- `agar.py` — entry point (`--frames N` for headless runs)
- `agario/config.py` — all constants (sizes, FPS, speeds, colors, fonts)
- `agario/geometry.py` — pure math: distance, normalize, clamp, `mass_to_radius`
- `agario/entities.py` — data classes: `Food`, `PlayerCell`, `EjectedMass`, `Virus`, `Player`
- `agario/mechanics/split.py` — split impulses, cooldowns, own-cell collisions and merging
- `agario/mechanics/eject.py` — mass ejection, projectile movement and consumption
- `agario/mechanics/virus.py` — safe spawning, virus feeding and radial cell bursts
- `agario/world.py` — `World` state, `Control` input, `World.update(controls)`
- `agario/physics.py` — movement, eating, map bounds
- `agario/camera.py` — zoom and world/screen coordinate transforms
- `agario/render.py` — all pygame drawing (grid, food, players, HUD)
- `agario/game.py` — pygame init, event handling and the main loop
