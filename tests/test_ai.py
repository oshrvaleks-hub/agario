import random

import pytest

from agario import config, physics
from agario.ai import BotBrain
from agario.entities import Food, Player, PlayerCell
from agario.world import World


def scene(mass=20):
    world = World()
    bot = Player('bot', cells=[PlayerCell(1000, 1000, mass)], is_bot=True)
    world.players.append(bot)
    return world, bot, BotBrain(random.Random(42))


def add_player(world, x, y, mass):
    player = Player(cells=[PlayerCell(x, y, mass)])
    world.players.append(player)
    return player


def test_flees_before_hunting_or_eating():
    world, bot, brain = scene()
    add_player(world, 1100, 1000, 25)
    add_player(world, 1000, 1100, 10)
    world.food.append(Food(1010, 1000))
    control = brain.decide(bot, world)
    assert control.target[0] < 1000
    assert control.target[1] == pytest.approx(1000)
    assert control.speed_factor == 1
    assert not control.split and not control.eject


def test_multiple_threats_weighted_by_distance():
    world, bot, brain = scene()
    add_player(world, 1050, 1000, 30)
    add_player(world, 900, 1000, 30)
    add_player(world, 1000, 1100, 30)
    control = brain.decide(bot, world)
    assert control.target[0] < 1000 and control.target[1] < 1000


def test_hunts_nearest_edible_cell():
    world, bot, brain = scene(25)
    prey = add_player(world, 1050, 1000, 20)
    add_player(world, 1200, 1000, 10)
    world.food.append(Food(1001, 1000))
    assert brain.decide(bot, world).target == prey.center


def test_food_and_outside_view_threat():
    world, bot, brain = scene()
    add_player(world, 1000 + config.BOT_VIEW_RADIUS + 1, 1000, 200)
    world.food.extend([Food(1020, 1000), Food(1100, 1000)])
    assert brain.decide(bot, world).target == (1020, 1000)


def test_dead_and_own_cells_are_not_targets():
    world, bot, brain = scene()
    dead = add_player(world, 1010, 1000, 200)
    dead.alive = False
    bot.cells.append(PlayerCell(1000, 1000, 200))
    world.food.append(Food(1020, 1000))
    assert brain.decide(bot, world).target == (1020, 1000)


def test_split_player_uses_individual_cell_mass():
    world, bot, brain = scene()
    bot.cells = [PlayerCell(1000, 1000, 10), PlayerCell(1000, 1000, 40)]
    add_player(world, 1100, 1000, 20)
    assert brain.decide(bot, world).target[0] < 1000


def test_shared_eating_rule_is_used_when_available(monkeypatch):
    world, bot, brain = scene()
    monkeypatch.setattr(physics, 'can_eat', lambda eater, prey: False, raising=False)
    add_player(world, 1010, 1000, 200)
    world.food.append(Food(1020, 1000))
    assert brain.decide(bot, world).target == (1020, 1000)


def test_perception_is_cached(monkeypatch):
    world, bot, brain = scene()
    calls = []
    original = brain._choose

    def counted(*args):
        calls.append(1)
        return original(*args)

    monkeypatch.setattr(brain, '_choose', counted)
    for _ in range(config.BOT_DECISION_TICKS * 2):
        brain.decide(bot, world)
    assert len(calls) == 2


def test_wandering_is_seeded_and_changes_after_interval():
    world, bot, brain = scene()
    other = BotBrain(random.Random(42))
    target = brain.decide(bot, world).target
    assert other.decide(bot, world).target == target
    for _ in range(config.BOT_WANDER_TICKS - 1):
        assert brain.decide(bot, world).target == target
    assert brain.decide(bot, world).target != target
    assert 0 <= target[0] <= world.width and 0 <= target[1] <= world.height


@pytest.mark.parametrize('empty', [False, True])
def test_respawn_after_exact_delay(empty):
    world = World(750, 900)
    bot = world.spawn_bots(1, ['Nom'], random.Random(3))[0]
    brain = BotBrain(random.Random(1))
    brain.decide(bot, world)
    if empty:
        bot.cells.clear()
    else:
        bot.alive = False
        bot.cells[0].mass = 200
    assert brain.decide(bot, world).speed_factor == 0
    for _ in range(config.BOT_RESPAWN_TICKS - 1):
        world.update({})
        assert not bot.alive
    world.update({})
    assert bot.alive and len(bot.cells) == 1
    assert bot.total_mass == config.PLAYER_START_MASS
    assert bot.name == 'Nom' and bot.is_bot
    assert 0 <= bot.center[0] <= world.width
    assert 0 <= bot.center[1] <= world.height
    assert brain.decide(bot, world).speed_factor == 1
    # A second death gets a full delay too.
    bot.cells.clear()
    world.update({})
    assert not bot.alive


def test_human_does_not_respawn():
    world, bot, _ = scene()
    bot.is_bot = False
    bot.alive = False
    for _ in range(config.BOT_RESPAWN_TICKS + 1):
        world.update({})
    assert not bot.alive


def test_spawn_seeded_and_names_cycle():
    first, second = World(123, 456), World(123, 456)
    a = first.spawn_bots(3, ['A', 'B'], random.Random(5))
    b = second.spawn_bots(3, ['A', 'B'], random.Random(5))
    assert [p.name for p in a] == ['A', 'B', 'A']
    assert [(p.center, p.color) for p in a] == [(p.center, p.color) for p in b]
    assert all(p.is_bot and p.alive for p in a)
    with pytest.raises(ValueError):
        first.spawn_bots(1, [])


def test_ten_bots_600_ticks():
    world = World()
    world.food = [Food(random.Random(i).uniform(0, world.width),
                       random.Random(i + 2000).uniform(0, world.height))
                  for i in range(2000)]
    bots = world.spawn_bots(10, rng=random.Random(123))
    brains = {p: BotBrain(random.Random(i)) for i, p in enumerate(bots)}
    for _ in range(600):
        world.update({p: brain.decide(p, world) for p, brain in brains.items()
                      if p.alive and p.cells})
    assert len(world.players) == 10
    assert all(0 <= p.center[0] <= world.width and
               0 <= p.center[1] <= world.height for p in bots)
