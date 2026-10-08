"""Movement and eating rules. No pygame import."""
from . import config
from .geometry import clamp, distance, normalize


def speed_factor_for_distance(dist):
    """Map pointer distance (px from screen centre) to a 0..1 speed factor."""
    if dist <= config.STOP_RADIUS:
        return 0.0
    return min(1.0, dist / config.FULL_SPEED_DISTANCE)


def move_cell(cell, target, speed_factor, width, height, max_speed=config.PLAYER_SPEED):
    """Move `cell` toward `target` by max_speed * speed_factor, staying in the map.

    Never overshoots the target.
    """
    dx, dy = target[0] - cell.x, target[1] - cell.y
    dist = distance((cell.x, cell.y), target)
    step = min(max_speed * clamp(speed_factor, 0.0, 1.0), dist)
    if step > 0:
        nx, ny = normalize(dx, dy)
        cell.x += nx * step
        cell.y += ny * step
    keep_in_bounds(cell, width, height)


def keep_in_bounds(cell, width, height):
    cell.x = clamp(cell.x, 0, width)
    cell.y = clamp(cell.y, 0, height)


def eat_food(cell, food_list):
    """Eat every food item whose centre is within the cell radius.

    Mutates `food_list` and `cell.mass`; returns the number eaten.
    """
    remaining = []
    eaten = 0
    for f in food_list:
        if distance((f.x, f.y), (cell.x, cell.y)) <= cell.radius:
            cell.mass += config.FOOD_EAT_GAIN
            eaten += 1
        else:
            remaining.append(f)
    food_list[:] = remaining
    return eaten
