"""Game state and per-tick update. No pygame import."""
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from . import config, physics
from .entities import EjectedMass, Food, Player
from .mechanics import eating
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
    def __init__(self, width=config.MAP_WIDTH, height=config.MAP_HEIGHT,
                 food_target=config.FOOD_COUNT):
        self.width = width
        self.height = height
        self.food_target = food_target
        self.food: List[Food] = []
        self.players: List[Player] = []
        self.viruses: list = []   # reserved for the virus mechanic
        self.ejected: List[EjectedMass] = []
        self._bot_respawn_timers = {}
        self._bot_rng = random.Random()
        # Cumulative exact consumption counts; session statistics take baselines.
        self.food_eaten = {}
        self.players_eaten = {}
        self.tick_peak_mass = {}

    def spawn_food(self, count):
        self.food.extend(Food.random(self.width, self.height) for _ in range(count))

    def spawn_bots(self, n=config.BOT_COUNT, names=None, rng=None):
        from .ai import spawn_bots
        if rng is not None:
            self._bot_rng = rng
        return spawn_bots(self, n, names, self._bot_rng)

    def update(self, controls: Dict[Player, Control]):
        self.tick_peak_mass = {p: p.total_mass for p in self.players if p.alive}
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
                eaten = physics.eat_food(cell, self.food)
                self.food_eaten[player] = self.food_eaten.get(player, 0) + eaten
            self.tick_peak_mass[player] = max(self.tick_peak_mass.get(player, 0),
                                              player.total_mass)
        for player in dict.fromkeys([*self.players, *controls]):
            if player.alive:
                for cell in player.cells:
                    apply_impulse(cell, self.width, self.height)
                resolve_own_cells(player)
                for cell in player.cells:
                    physics.keep_in_bounds(cell, self.width, self.height)
        update_ejected(self)
        for player in self.players:
            if player.alive:
                self.tick_peak_mass[player] = max(self.tick_peak_mass.get(player, 0),
                                                  player.total_mass)
        kills = eating.resolve_player_collisions(self)
        for player, count in kills.items():
            self.players_eaten[player] = self.players_eaten.get(player, 0) + count
        self._respawn_food()
        from .ai import respawn_bots
        respawn_bots(self, self._bot_respawn_timers, self._bot_rng)

    def _respawn_food(self):
        missing = self.food_target - len(self.food)
        if missing > 0:
            self.spawn_food(min(missing, config.FOOD_RESPAWN_PER_TICK))
