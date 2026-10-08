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
- Space: split (not implemented yet)
- W: eject mass (not implemented yet)
- Esc: quit

## Tests
```
python3 -m pytest
```
Tests run without a window and do not import pygame.

## Structure
- `agar.py` — entry point (`--frames N` for headless runs)
- `agario/config.py` — all constants (sizes, FPS, speeds, colors, fonts)
- `agario/geometry.py` — pure math: distance, normalize, clamp, `mass_to_radius`
- `agario/entities.py` — data classes: `Food`, `PlayerCell`, `Player`
- `agario/world.py` — `World` state, `Control` input, `World.update(controls)`
- `agario/physics.py` — movement, eating, map bounds
- `agario/camera.py` — zoom and world/screen coordinate transforms
- `agario/render.py` — all pygame drawing (grid, food, players, HUD)
- `agario/game.py` — pygame init, event handling and the main loop
