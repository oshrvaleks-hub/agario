"""Splitting, decaying launch velocity and own-cell collisions; no pygame."""
from .. import config
from ..entities import PlayerCell
from ..geometry import clamp, distance, normalize


def split_player(player, target):
    """Split each eligible original cell once, up to MAX_CELLS.

    Both halves wait 10 seconds + 0.05 seconds per unit of half-mass before
    merging (all timers are in ticks at config.FPS). A coincident target
    launches to the right so splitting remains usable with a centred pointer.
    """
    for cell in list(player.cells):
        if len(player.cells) >= config.MAX_CELLS:
            break
        if cell.mass < config.SPLIT_MIN_MASS:
            continue
        nx, ny = normalize(target[0] - cell.x, target[1] - cell.y)
        if nx == ny == 0:
            nx = 1.0
        cell.mass /= 2
        timer = config.MERGE_BASE_TICKS + cell.mass * config.MERGE_TICKS_PER_MASS
        cell.merge_timer = timer
        player.cells.append(PlayerCell(
            cell.x, cell.y, cell.mass,
            nx * config.SPLIT_SPEED, ny * config.SPLIT_SPEED, timer))


def apply_impulse(cell, width, height):
    """Apply velocity after ordinary steering, then damp it and clamp position."""
    cell.x = clamp(cell.x + cell.vx, 0, width)
    cell.y = clamp(cell.y + cell.vy, 0, height)
    cell.vx *= config.IMPULSE_FRICTION
    cell.vy *= config.IMPULSE_FRICTION


def resolve_own_cells(player):
    """Tick cooldowns, merge deeply overlapping ready cells, separate others.

    Ready cells can overlap while approaching the merge threshold. Locked
    cells share separation inversely to mass; repeated pair relaxation handles
    groups without an abrupt teleport of the entire group. World clamps bounds
    after resolution. Merging preserves mass, centre of mass and momentum.
    """
    for cell in player.cells:
        cell.merge_timer = max(0, cell.merge_timer - 1)
    i = 0
    while i < len(player.cells):
        first = player.cells[i]
        j = i + 1
        while j < len(player.cells):
            second = player.cells[j]
            separation = distance((first.x, first.y), (second.x, second.y))
            if (first.merge_timer == second.merge_timer == 0 and
                    separation <= (first.radius + second.radius) * config.MERGE_OVERLAP_RATIO):
                total = first.mass + second.mass
                first.x = (first.x * first.mass + second.x * second.mass) / total
                first.y = (first.y * first.mass + second.y * second.mass) / total
                first.vx = (first.vx * first.mass + second.vx * second.mass) / total
                first.vy = (first.vy * first.mass + second.vy * second.mass) / total
                first.mass = total
                player.cells.pop(j)
                # A larger merged cell can now reach an earlier neighbour.
                i = -1
                break
            j += 1
        i += 1

    for _ in range(config.OWN_CELL_RELAX_PASSES):
        moved = False
        for i, first in enumerate(player.cells):
            for second in player.cells[i + 1:]:
                if first.merge_timer == second.merge_timer == 0:
                    continue
                dx, dy = second.x - first.x, second.y - first.y
                separation = distance((first.x, first.y), (second.x, second.y))
                overlap = first.radius + second.radius - separation
                if overlap <= 1e-6:
                    continue
                nx, ny = normalize(dx, dy)
                if nx == ny == 0:
                    nx = 1.0
                total = first.mass + second.mass
                first_shift = overlap * second.mass / total
                second_shift = overlap * first.mass / total
                first.x -= nx * first_shift
                first.y -= ny * first_shift
                second.x += nx * second_shift
                second.y += ny * second_shift
                moved = True
        if not moved:
            break
