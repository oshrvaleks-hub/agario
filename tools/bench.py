"""Benchmark: logic ms/tick and full-frame ms/frame in pygame's dummy video mode.

    python3 tools/bench.py [--frames 600] [--seed 1]

A fixed seed gives the same world every run, so before/after numbers compare.
The scripted player circles the map so the camera and bots keep working.
"""
import argparse
import math
import os
import random
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pygame  # noqa: E402

from agario import config, physics  # noqa: E402
from agario.ai import BotBrain  # noqa: E402
from agario.camera import Camera  # noqa: E402
from agario.entities import Player  # noqa: E402
from agario.render import Renderer  # noqa: E402
from agario.world import Control, World  # noqa: E402


def build(seed):
    random.seed(seed)
    world = World()
    world.spawn_food(config.FOOD_COUNT)
    player = Player.spawn(config.PLAYER_NAME)
    world.players.append(player)
    world.spawn_bots(rng=random.Random(seed))
    brains = {b: BotBrain(random.Random(seed + i)) for i, b in enumerate(
        p for p in world.players if p.is_bot)}
    return world, player, brains


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frames", type=int, default=600)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)

    pygame.init()
    surface = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    renderer = Renderer(surface)
    camera = Camera()
    world, player, brains = build(args.seed)
    camera.update(player, snap=True)

    logic = render = 0.0
    logic_max = render_max = 0.0
    for n in range(args.frames):
        angle = n / 150.0
        target = (1000 + 800 * math.cos(angle), 1000 + 800 * math.sin(angle))

        t0 = time.perf_counter()
        controls = {b: br.decide(b, world) for b, br in brains.items() if b.alive and b.cells}
        controls[player] = Control(target=target, speed_factor=1.0)
        world.update(controls)
        t1 = time.perf_counter()
        camera.update(player)
        renderer.draw(world, camera, player)
        pygame.display.flip()
        t2 = time.perf_counter()

        logic += t1 - t0
        render += t2 - t1
        logic_max = max(logic_max, t1 - t0)
        render_max = max(render_max, t2 - t1)

    pygame.quit()
    f = args.frames
    print("frames: {}  seed: {}".format(f, args.seed))
    print("logic : {:6.2f} ms/tick   (max {:.2f})".format(logic / f * 1000, logic_max * 1000))
    print("render: {:6.2f} ms/frame  (max {:.2f})".format(render / f * 1000, render_max * 1000))
    print("total : {:6.2f} ms/frame  (~{:.0f} FPS uncapped)".format(
        (logic + render) / f * 1000, f / (logic + render)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
