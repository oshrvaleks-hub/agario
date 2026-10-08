"""Plain game data. No pygame import."""
import random
from dataclasses import dataclass, field
from typing import List

from . import config
from .geometry import mass_to_radius


@dataclass
class Food:
    x: float
    y: float
    mass: float = config.FOOD_MASS
    color: tuple = (0, 255, 0)

    @classmethod
    def random(cls, width=config.MAP_WIDTH, height=config.MAP_HEIGHT):
        m = config.FOOD_MARGIN
        return cls(random.randint(m, int(width) - m),
                   random.randint(m, int(height) - m),
                   config.FOOD_MASS,
                   random.choice(config.FOOD_COLORS))


@dataclass
class PlayerCell:
    x: float
    y: float
    mass: float = config.PLAYER_START_MASS

    @property
    def radius(self):
        return mass_to_radius(self.mass)


# eq=False: players are used as dict keys (controls) so identity hashing is needed
@dataclass(eq=False)
class Player:
    name: str = "Anonymous"
    color: tuple = (37, 7, 255)
    cells: List[PlayerCell] = field(default_factory=list)
    is_bot: bool = False
    alive: bool = True

    @property
    def total_mass(self):
        return sum(c.mass for c in self.cells)

    @property
    def center(self):
        """Mass-weighted centre of all cells."""
        total = self.total_mass
        if not self.cells or total == 0:
            return 0.0, 0.0
        return (sum(c.x * c.mass for c in self.cells) / total,
                sum(c.y * c.mass for c in self.cells) / total)

    @property
    def outline_color(self):
        return tuple(int(v - v / 3) for v in self.color)

    @classmethod
    def spawn(cls, name="", is_bot=False):
        return cls(name=name or "Anonymous",
                   color=random.choice(config.PLAYER_COLORS),
                   cells=[PlayerCell(random.randint(100, 400),
                                     random.randint(100, 400))],
                   is_bot=is_bot)
