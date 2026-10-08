"""Lifetime statistics and safe spawn selection, independent of pygame."""
from dataclasses import dataclass, field
from typing import Optional

from . import config
from .geometry import distance, mass_to_radius
from .leaderboard import rank_players


@dataclass
class PlayerStats:
    max_mass: float = 0.0
    food_eaten: int = 0
    players_eaten: int = 0
    ticks_alive: int = 0
    best_rank: Optional[int] = None
    _food_start: int = field(default=0, repr=False)
    _players_start: int = field(default=0, repr=False)
    _finished: bool = field(default=False, repr=False)

    def reset(self, world, player):
        """Start a life without counting a simulation tick."""
        self.max_mass = player.total_mass
        self.food_eaten = self.players_eaten = self.ticks_alive = 0
        self.best_rank = None
        self._food_start = world.food_eaten.get(player, 0)
        self._players_start = world.players_eaten.get(player, 0)
        self._finished = False
        self._observe(world, player)

    def _observe(self, world, player):
        self.max_mass = max(self.max_mass, player.total_mass,
                            world.tick_peak_mass.get(player, 0))
        self.food_eaten = world.food_eaten.get(player, 0) - self._food_start
        self.players_eaten = world.players_eaten.get(player, 0) - self._players_start
        rows = rank_players(world.players, player, top=0)
        if rows:
            rank = rows[0][0]
            self.best_rank = rank if self.best_rank is None else min(self.best_rank, rank)

    def update(self, world, player):
        """Call after each playing tick, including the fatal tick; freeze on death."""
        if self._finished:
            return
        self._observe(world, player)
        self.ticks_alive += 1
        self._finished = not player.alive or not player.cells


def find_safe_spawn(world, mass, rng):
    """Return a bounded circle clear of larger live cells and all viruses.

    Try random positions, then a deterministic grid. Raise ValueError if none
    of the candidates is safe, rather than silently spawning inside a hazard.
    """
    radius = mass_to_radius(mass)
    if world.width < 2 * radius or world.height < 2 * radius:
        raise ValueError("Map is too small for the spawn circle")
    hazards = [(cell.x, cell.y, cell.radius)
               for player in world.players if player.alive
               for cell in player.cells if cell.mass > mass]
    hazards.extend((virus.x, virus.y, mass_to_radius(virus.mass))
                   for virus in world.viruses)

    def safe(x, y):
        return all(distance((x, y), (hx, hy)) > radius + hr
                   for hx, hy, hr in hazards)

    for _ in range(config.SAFE_SPAWN_ATTEMPTS):
        x = rng.uniform(radius, world.width - radius)
        y = rng.uniform(radius, world.height - radius)
        if safe(x, y):
            return x, y
    steps = config.SAFE_SPAWN_GRID_STEPS
    for i in range(steps + 1):
        for j in range(steps + 1):
            x = radius + (world.width - 2 * radius) * i / steps
            y = radius + (world.height - 2 * radius) * j / steps
            if safe(x, y):
                return x, y
    raise ValueError("No safe spawn candidate available")
