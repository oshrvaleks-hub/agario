"""Bot decisions and lifecycle helpers. No pygame import."""
import math
import random

from . import config, physics
from .entities import Player, PlayerCell
from .world import Control


class BotBrain:
    """One brain per player; expensive perception runs once every few ticks."""

    def __init__(self, rng=None):
        self.rng = rng if rng is not None else random.Random()
        self._remaining = 0
        self._control = Control()
        self._cell = None
        self._wander_target = None
        self._wander_remaining = 0

    def decide(self, player, world) -> Control:
        if not player.alive or not player.cells:
            self._remaining = 0
            return Control()
        # A new first cell also invalidates cached intent after respawning.
        if self._cell is not player.cells[0]:
            self._cell = player.cells[0]
            self._remaining = 0
            self._wander_remaining = 0
        self._wander_remaining -= 1
        if self._remaining <= 0:
            self._control = self._choose(player, world)
            self._remaining = config.BOT_DECISION_TICKS
        self._remaining -= 1
        return self._control

    def _choose(self, player, world):
        x, y = player.center
        radius2 = config.BOT_VIEW_RADIUS ** 2
        threats, prey = [], []
        for other in world.players:
            if other is player or not other.alive:
                continue
            for cell in other.cells:
                # Compare individual cells, never the combined mass of a split player.
                visible = [own for own in player.cells
                           if (cell.x - own.x) ** 2 + (cell.y - own.y) ** 2 <= radius2]
                for own in visible:
                    dx, dy = own.x - cell.x, own.y - cell.y
                    dist2 = dx * dx + dy * dy
                    if physics.can_eat(cell.mass, own.mass):
                        threats.append((dx, dy, dist2))
                    if physics.can_eat(own.mass, cell.mass):
                        prey.append((dist2, cell))
        if threats:
            # Unit escape vectors weighted by inverse distance.
            vx = sum(dx / max(d2, 1.0) for dx, dy, d2 in threats)
            vy = sum(dy / max(d2, 1.0) for dx, dy, d2 in threats)
            if math.hypot(vx, vy) < 1e-9:
                dx, dy, _ = min(threats, key=lambda t: t[2])
                vx, vy = (dx, dy) if dx or dy else (1.0, 0.0)
            length = math.hypot(vx, vy)
            return Control((x + vx / length * config.BOT_VIEW_RADIUS,
                            y + vy / length * config.BOT_VIEW_RADIUS), 1.0)
        if prey:
            cell = min(prey, key=lambda item: item[0])[1]
            return Control((cell.x, cell.y), 1.0)
        nearest, best = None, radius2 + 1
        for food in world.food:
            d2 = (food.x - x) ** 2 + (food.y - y) ** 2
            if d2 <= radius2 and d2 < best:
                nearest, best = food, d2
        if nearest is not None:
            return Control((nearest.x, nearest.y), 1.0)
        if self._wander_remaining <= 0 or self._wander_target is None:
            self._wander_target = (self.rng.uniform(0, world.width),
                                   self.rng.uniform(0, world.height))
            self._wander_remaining = config.BOT_WANDER_TICKS
        return Control(self._wander_target, 1.0)


def _reset_bot(player, world, rng):
    player.cells = [PlayerCell(rng.uniform(0, world.width),
                               rng.uniform(0, world.height), config.PLAYER_START_MASS)]
    player.alive = True


def spawn_bots(world, n, names=None, rng=None):
    """Add bots and return them; a supplied RNG makes spawning reproducible."""
    rng = rng if rng is not None else random.Random()
    names = list(config.BOT_NAMES if names is None else names)
    if not names and n > 0:
        raise ValueError("Bot names must not be empty")
    bots = []
    for i in range(n):
        player = Player(name=names[i % len(names)], is_bot=True,
                        color=rng.choice(config.PLAYER_COLORS))
        _reset_bot(player, world, rng)
        bots.append(player)
    world.players.extend(bots)
    return bots


def respawn_bots(world, timers, rng):
    """Count dead simulation ticks, preserving each bot's identity and name."""
    for player in world.players:
        if not player.is_bot:
            continue
        if player.alive and player.cells:
            timers.pop(player, None)
            continue
        player.alive = False
        timers[player] = timers.get(player, 0) + 1
        if timers[player] >= config.BOT_RESPAWN_TICKS:
            _reset_bot(player, world, rng)
            timers.pop(player, None)
