"""Virus spawning, feeding and cell bursts. No pygame import."""
import math
import random

from .. import config, physics
from ..entities import PlayerCell, Virus
from ..geometry import distance, normalize
from .split import apply_impulse


def maintain_viruses(world, rng=None):
    """Fill the minimum population without spawning near living player cells.

    Attempts are bounded: a crowded or undersized map can temporarily have
    fewer viruses. Feeding-created excess viruses are never removed.
    """
    rng = rng if rng is not None else random
    radius = Virus(0, 0, config.VIRUS_MASS).radius
    if world.width < 2 * radius or world.height < 2 * radius:
        return
    cells = [c for p in world.players if p.alive for c in p.cells]
    for _ in range(max(0, world.virus_target - len(world.viruses))):
        for _ in range(config.VIRUS_SPAWN_ATTEMPTS):
            virus = Virus(rng.uniform(radius, world.width - radius),
                          rng.uniform(radius, world.height - radius),
                          config.VIRUS_MASS)
            if any(distance((virus.x, virus.y), (c.x, c.y)) <
                   c.radius + radius + config.VIRUS_SPAWN_MARGIN for c in cells):
                continue
            if any(distance((virus.x, virus.y), (v.x, v.y)) < radius + v.radius
                   for v in world.viruses):
                continue
            world.viruses.append(virus)
            break
        else:
            break


def feed_virus(world, shot):
    """Consume a shot whose centre hits a virus, before player consumption.

    Each hit adds shot mass. The seventh resets the parent to VIRUS_MASS
    and launches a base-mass child along the incoming shot's velocity. This
    reset follows the gameplay rule rather than conserving projectile mass.
    A stationary shot uses source-to-virus direction, falling back to right.
    """
    for virus in world.viruses:
        if distance((virus.x, virus.y), (shot.x, shot.y)) > virus.radius:
            continue
        virus.mass += shot.mass
        virus.fed += 1
        if virus.fed >= config.VIRUS_FEED_SHOTS:
            nx, ny = normalize(shot.vx, shot.vy)
            if nx == ny == 0 and shot.source is not None:
                nx, ny = normalize(virus.x - shot.source.x, virus.y - shot.source.y)
            if nx == ny == 0:
                nx = 1.0
            virus.mass = config.VIRUS_MASS
            virus.fed = 0
            child = Virus(virus.x, virus.y, config.VIRUS_MASS,
                          nx * config.VIRUS_LAUNCH_SPEED,
                          ny * config.VIRUS_LAUNCH_SPEED)
            offset = virus.radius + child.radius
            child.x += nx * offset
            child.y += ny * offset
            physics.keep_in_bounds(child, world.width, world.height)
            world.viruses.append(child)
        return True
    return False


def burst_cell(player, cell, virus):
    """Add virus mass and spread equal fragments radially within MAX_CELLS.

    At the cap, the original cell gains mass and a cooldown but cannot split.
    New cells use the same velocity and timer primitives as ordinary splits.
    """
    total = cell.mass + virus.mass
    slots = max(1, config.MAX_CELLS - len(player.cells) + 1)
    count = min(slots, max(2, int(total / config.VIRUS_FRAGMENT_MASS)))
    mass = total / count
    x, y, vx, vy = cell.x, cell.y, cell.vx, cell.vy
    timer = max(cell.merge_timer,
                config.MERGE_BASE_TICKS + mass * config.MERGE_TICKS_PER_MASS)
    for i in range(count):
        fragment = cell if i == 0 else PlayerCell(x, y)
        fragment.mass = mass if i < count - 1 else total - mass * (count - 1)
        fragment.merge_timer = timer
        if count > 1:
            angle = math.tau * i / count
            nx, ny = math.cos(angle), math.sin(angle)
            fragment.x = x + nx * fragment.radius
            fragment.y = y + ny * fragment.radius
            fragment.vx = vx + nx * config.VIRUS_BURST_SPEED
            fragment.vy = vy + ny * config.VIRUS_BURST_SPEED
        if i:
            player.cells.append(fragment)


def update_viruses(world):
    """Move viruses, then burst eligible cells before player-vs-player eating.

    A virus is consumed at most once. Newly created fragments are considered
    for subsequent viruses, always respecting the player's remaining slots.
    """
    remaining = []
    for virus in world.viruses:
        apply_impulse(virus, world.width, world.height)
        physics.keep_in_bounds(virus, world.width, world.height)
        eaten = False
        for player in world.players:
            if not player.alive:
                continue
            for cell in player.cells:
                if physics.can_eat_cell(cell, virus):
                    burst_cell(player, cell, virus)
                    for fragment in player.cells:
                        physics.keep_in_bounds(fragment, world.width, world.height)
                    eaten = True
                    break
            if eaten:
                break
        if not eaten:
            remaining.append(virus)
    world.viruses[:] = remaining
