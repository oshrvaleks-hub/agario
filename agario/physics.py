"""Movement and eating rules. No pygame import."""
from . import config
from .geometry import clamp, distance, normalize


def speed_factor_for_distance(dist):
    """Map pointer distance (px from screen centre) to a 0..1 speed factor."""
    if dist <= config.STOP_RADIUS:
        return 0.0
    return min(1.0, dist / config.FULL_SPEED_DISTANCE)


def max_speed_for_mass(mass):
    """Top speed of a cell: falls monotonically as mass grows, never below MIN_SPEED."""
    ratio = config.PLAYER_START_MASS / max(mass, 1e-9)
    speed = config.PLAYER_SPEED * ratio ** config.SPEED_MASS_EXPONENT
    return clamp(speed, config.MIN_SPEED, config.PLAYER_SPEED)


def can_eat(eater_mass, prey_mass):
    """True if a cell of `eater_mass` is big enough to eat one of `prey_mass`."""
    return eater_mass >= config.EAT_MASS_RATIO * prey_mass


def can_eat_cell(eater, prey):
    """Eater is big enough and the prey's centre is well inside the eater."""
    if not can_eat(eater.mass, prey.mass):
        return False
    reach = eater.radius - prey.radius * config.EAT_OVERLAP
    return distance((eater.x, eater.y), (prey.x, prey.y)) <= reach


def move_cell(cell, target, speed_factor, width, height, max_speed=None):
    """Move `cell` toward `target` by max_speed * speed_factor, staying in the map.

    `max_speed` defaults to max_speed_for_mass(cell.mass). Never overshoots the target.
    """
    if max_speed is None:
        max_speed = max_speed_for_mass(cell.mass)
    dx, dy = target[0] - cell.x, target[1] - cell.y
    dist = distance((cell.x, cell.y), target)
    step = min(max_speed * clamp(speed_factor, 0.0, 1.0), dist)
    if step > 0:
        nx, ny = normalize(dx, dy)
        cell.x += nx * step
        cell.y += ny * step
    keep_in_bounds(cell, width, height)


def keep_in_bounds(cell, width, height):
    """Keep the whole circle inside the map (its edge touches the map edge)."""
    r = cell.radius
    cell.x = clamp(cell.x, r, width - r)
    cell.y = clamp(cell.y, r, height - r)


def eat_food(cell, food_list):
    """Eat every food item whose centre is within the cell radius.

    Mutates `food_list` and `cell.mass`; returns the number eaten.
    """
    remaining = []
    eaten = 0
    for f in food_list:
        if distance((f.x, f.y), (cell.x, cell.y)) <= cell.radius:
            cell.mass += f.mass
            eaten += 1
        else:
            remaining.append(f)
    food_list[:] = remaining
    return eaten
