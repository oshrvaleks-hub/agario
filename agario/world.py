"""Game state and per-tick update. No pygame import."""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from . import config, physics
from .mechanics import eating
from .entities import Food, Player


@dataclass
class Control:
    """Player intent for one tick. `target` is in WORLD coordinates."""
    target: Tuple[float, float] = (0.0, 0.0)
    speed_factor: float = 0.0  # 0..1
    split: bool = False
    eject: bool = False


class World:
    def __init__(self, width=config.MAP_WIDTH, height=config.MAP_HEIGHT,
                 food_target=config.FOOD_COUNT):
        self.width = width
        self.height = height
        self.food_target = food_target
        self.food: List[Food] = []
        self.players: List[Player] = []
        self.viruses: list = []   # reserved for the virus mechanic
        self.ejected: list = []   # reserved for the eject-mass mechanic

    def spawn_food(self, count):
        self.food.extend(Food.random(self.width, self.height) for _ in range(count))

    def update(self, controls: Dict[Player, Control]):
        for player, control in controls.items():
            if not player.alive:
                continue
            # TODO: split — handle control.split (divide cells)
            # TODO: eject — handle control.eject (spawn into self.ejected)
            for cell in player.cells:
                physics.move_cell(cell, control.target, control.speed_factor,
                                  self.width, self.height)
                physics.eat_food(cell, self.food)
        eating.resolve_player_collisions(self)
        self._respawn_food()

    def _respawn_food(self):
        missing = self.food_target - len(self.food)
        if missing > 0:
            self.spawn_food(min(missing, config.FOOD_RESPAWN_PER_TICK))
