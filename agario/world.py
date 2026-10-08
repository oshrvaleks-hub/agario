"""Game state and per-tick update. No pygame import."""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from . import config, physics
from .entities import EjectedMass, Food, Player
from .mechanics.eject import eject_mass, update_ejected
from .mechanics.split import apply_impulse, resolve_own_cells, split_player


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
        self.ejected: List[EjectedMass] = []

    def spawn_food(self, count):
        self.food.extend(Food.random(self.width, self.height) for _ in range(count))

    def update(self, controls: Dict[Player, Control]):
        for player, control in controls.items():
            if not player.alive:
                continue
            if control.split:
                split_player(player, control.target)
            if control.eject:
                eject_mass(player, control.target, self)
            for cell in player.cells:
                physics.move_cell(cell, control.target, control.speed_factor,
                                  self.width, self.height)
                physics.eat_food(cell, self.food)
        for player in dict.fromkeys([*self.players, *controls]):
            if player.alive:
                for cell in player.cells:
                    apply_impulse(cell, self.width, self.height)
                resolve_own_cells(player)
                for cell in player.cells:
                    physics.keep_in_bounds(cell, self.width, self.height)
        update_ejected(self)
