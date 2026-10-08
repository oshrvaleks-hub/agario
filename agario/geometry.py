"""Pure math helpers. No pygame import."""
import math

from . import config


def distance(a, b):
    """Euclidean distance between points a and b."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def normalize(vx, vy):
    """Unit vector in the direction (vx, vy); (0, 0) for a zero vector."""
    length = math.hypot(vx, vy)
    if length == 0:
        return 0.0, 0.0
    return vx / length, vy / length


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def mass_to_radius(mass):
    """The single place that defines how mass maps to radius."""
    return config.RADIUS_PER_SQRT_MASS * math.sqrt(max(mass, 0))
