"""Mass projectiles and their consumption; no pygame dependencies."""
from .. import config
from ..entities import EjectedMass
from ..geometry import clamp, distance, normalize


def eject_mass(player, target, world):
    """Each eligible cell pays 18 mass to launch 14; four units are lost."""
    for cell in player.cells:
        if cell.mass < config.EJECT_MIN_MASS:
            continue
        nx, ny = normalize(target[0] - cell.x, target[1] - cell.y)
        if nx == ny == 0:
            nx = 1.0
        cell.mass -= config.EJECT_COST
        shot = EjectedMass(cell.x, cell.y, config.EJECT_MASS, player.color,
                           nx * config.EJECT_SPEED, ny * config.EJECT_SPEED,
                           cell, config.EJECT_IMMUNITY_TICKS)
        offset = cell.radius + shot.radius
        shot.x = clamp(cell.x + nx * offset, 0, world.width)
        shot.y = clamp(cell.y + ny * offset, 0, world.height)
        world.ejected.append(shot)


def update_ejected(world):
    """Advance shots once per tick; any larger live cell covering a centre eats.

    Source immunity is identity-based and lasts eight complete updates. Other
    cells, including siblings, may eat immediately. Stationary shots persist.
    """
    remaining = []
    for shot in world.ejected:
        shot.x = clamp(shot.x + shot.vx, 0, world.width)
        shot.y = clamp(shot.y + shot.vy, 0, world.height)
        shot.vx *= config.EJECT_FRICTION
        shot.vy *= config.EJECT_FRICTION
        eaten = False
        for player in world.players:
            if not player.alive:
                continue
            for cell in player.cells:
                if cell is shot.source and shot.immunity_ticks > 0:
                    continue
                if (cell.mass > shot.mass and
                        distance((cell.x, cell.y), (shot.x, shot.y)) <= cell.radius):
                    cell.mass += shot.mass
                    eaten = True
                    break
            if eaten:
                break
        if not eaten:
            shot.immunity_ticks = max(0, shot.immunity_ticks - 1)
            if shot.immunity_ticks == 0:
                shot.source = None
            remaining.append(shot)
    world.ejected[:] = remaining
