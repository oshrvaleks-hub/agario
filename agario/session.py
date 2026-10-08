"""Local player's life transitions. No pygame import."""
import random
from enum import Enum

from . import config
from .entities import PlayerCell
from .stats import PlayerStats, find_safe_spawn


class GameState(Enum):
    PLAYING = "playing"
    DEAD = "dead"


class GameSession:
    def __init__(self, world, player, rng=None):
        self.world = world
        self.player = player
        self.rng = rng if rng is not None else random.Random()
        self.state = GameState.PLAYING
        self.stats = PlayerStats()
        self.stats.reset(world, player)
        if not player.alive or not player.cells:
            self.player.alive = False
            self.state = GameState.DEAD

    def update(self):
        """Observe one completed world tick; death statistics stay frozen."""
        if self.state is GameState.PLAYING:
            self.stats.update(self.world, self.player)
            if not self.player.alive or not self.player.cells:
                self.player.alive = False
                self.state = GameState.DEAD

    def restart(self):
        """Revive the same player without replacing any world objects.

        Return False while alive or if the map has no safe spawn candidate.
        """
        if self.state is not GameState.DEAD:
            return False
        try:
            x, y = find_safe_spawn(self.world, config.PLAYER_START_MASS, self.rng)
        except ValueError:
            return False
        self.player.cells = [PlayerCell(x, y, config.PLAYER_START_MASS)]
        self.player.alive = True
        self.world.tick_peak_mass.pop(self.player, None)
        self.stats.reset(self.world, self.player)
        self.state = GameState.PLAYING
        return True
