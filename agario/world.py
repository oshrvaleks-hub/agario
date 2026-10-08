"""Game state and per-tick update. No pygame import."""
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from . import config, physics
from .entities import Food, Player


@dataclass
class Control:
    """Player intent for one tick. `target` is in WORLD coordinates."""
    target: Tuple[float, float] = (0.0, 0.0)
    speed_factor: float = 0.0  # 0..1
    split: bool = False
    eject: bool = False


class World:
    def __init__(self, width=config.MAP_WIDTH, height=config.MAP_HEIGHT):
        self.width = width
        self.height = height
        self.food: List[Food] = []
        self.players: List[Player] = []
        self.viruses: list = []   # reserved for the virus mechanic
        self.ejected: list = []   # reserved for the eject-mass mechanic
        self._bot_respawn_timers = {}
        self._bot_rng = random.Random()

    def spawn_food(self, count):
        self.food.extend(Food.random(self.width, self.height) for _ in range(count))

    def spawn_bots(self, n=config.BOT_COUNT, names=None, rng=None):
        from .ai import spawn_bots
        if rng is not None:
            self._bot_rng = rng
        return spawn_bots(self, n, names, self._bot_rng)

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

        from .ai import respawn_bots
        respawn_bots(self, self._bot_respawn_timers, self._bot_rng)
