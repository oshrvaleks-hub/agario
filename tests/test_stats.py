import random
from types import SimpleNamespace

import pytest

from agario import config
from agario.entities import Food, Player, PlayerCell
from agario.geometry import distance, mass_to_radius
from agario.stats import PlayerStats, find_safe_spawn
from agario.world import Control, World


def setup(mass=20):
    world = World(food_target=0)
    player = Player(cells=[PlayerCell(500, 500, mass)])
    world.players.append(player)
    stats = PlayerStats()
    stats.reset(world, player)
    return world, player, stats


def test_max_mass_and_rank_never_worsen():
    world, player, stats = setup()
    other = Player(cells=[PlayerCell(1500, 1500, 30)])
    world.players.append(other)
    stats.reset(world, player)
    assert stats.best_rank == 2 and stats.ticks_alive == 0
    player.cells[0].mass = 40
    stats.update(world, player)
    assert stats.max_mass == 40 and stats.best_rank == 1
    player.cells[0].mass = 10
    stats.update(world, player)
    assert stats.max_mass == 40 and stats.best_rank == 1
    assert stats.ticks_alive == 2


def test_food_counts_exactly_despite_replenishment_and_other_eaters():
    world, player, stats = setup()
    other = Player(cells=[PlayerCell(1500, 1500, 20)])
    world.players.append(other)
    world.food_target = 3
    world.food = [Food(500, 500, 7), Food(501, 500, 2), Food(1500, 1500)]
    world.update({player: Control(player.center), other: Control(other.center)})
    stats.update(world, player)
    assert len(world.food) == 3
    assert stats.food_eaten == 2 and stats.max_mass == 29
    assert stats.players_eaten == 0


def test_players_count_only_final_cell_and_credit_final_eater():
    world, player, stats = setup(100)
    prey = Player(cells=[PlayerCell(500, 500, 10), PlayerCell(1500, 1500, 10)])
    world.players.append(prey)
    world.update({})
    stats.update(world, player)
    assert prey.alive and len(prey.cells) == 1
    assert stats.players_eaten == 0
    prey.cells[0].x = prey.cells[0].y = 500
    world.update({})
    stats.update(world, player)
    assert not prey.alive
    assert stats.players_eaten == 1 and stats.max_mass == 120


def test_same_tick_gain_and_death_preserves_peak_and_counts():
    world, player, stats = setup(100)
    prey = Player(cells=[PlayerCell(500, 500, 10)])
    killer = Player(cells=[PlayerCell(500, 500, 1000)])
    world.players.extend([prey, killer])
    world.food = [Food(500, 500)]
    world.update({player: Control(player.center)})
    stats.update(world, player)
    assert not player.alive
    assert stats.max_mass == 111
    assert stats.food_eaten == 1 and stats.players_eaten == 1
    assert stats.ticks_alive == 1
    world.update({})
    stats.update(world, player)
    assert stats.max_mass == 111 and stats.ticks_alive == 1


def test_split_and_eject_are_not_consumption():
    world, player, stats = setup(100)
    world.update({player: Control((800, 500), split=True, eject=True)})
    stats.update(world, player)
    assert stats.max_mass == 100
    assert stats.food_eaten == stats.players_eaten == 0


def test_safe_spawn_bounds_hazards_and_seed():
    world, player, _ = setup(5000)
    world.viruses = [SimpleNamespace(x=1500, y=1500, mass=5000)]
    radius = mass_to_radius(config.PLAYER_START_MASS)
    rng = random.Random(42)
    target = find_safe_spawn(world, config.PLAYER_START_MASS, rng)
    assert target == find_safe_spawn(world, config.PLAYER_START_MASS, random.Random(42))
    for _ in range(100):
        x, y = find_safe_spawn(world, config.PLAYER_START_MASS, rng)
        assert radius <= x <= world.width - radius
        assert radius <= y <= world.height - radius
        assert distance((x, y), player.center) > radius + player.cells[0].radius
        assert distance((x, y), (1500, 1500)) > radius + mass_to_radius(5000)


def test_safe_spawn_grid_fallback():
    world, player, _ = setup(5000)

    class BlockedRng:
        def uniform(self, lo, hi):
            return 500

    x, y = find_safe_spawn(world, 20, BlockedRng())
    assert distance((x, y), player.center) > player.cells[0].radius + mass_to_radius(20)


def test_no_safe_spawn_and_too_small_map():
    world = World(100, 100, food_target=0)
    world.viruses = [SimpleNamespace(x=50, y=50, mass=100000)]
    with pytest.raises(ValueError):
        find_safe_spawn(world, 20, random.Random(1))
    with pytest.raises(ValueError):
        find_safe_spawn(World(1, 1), 20, random.Random(1))


def test_dead_and_smaller_players_do_not_block_spawn():
    world = World(100, 100, food_target=0)
    world.players = [Player(cells=[PlayerCell(50, 50, 100000)], alive=False),
                     Player(cells=[PlayerCell(50, 50, 10)])]
    assert find_safe_spawn(world, 20, random.Random(1))


def test_elimination_credited_to_eater_of_final_cell():
    world, player, stats = setup(100)
    other = Player(cells=[PlayerCell(1500, 1500, 100)])
    prey = Player(cells=[PlayerCell(500, 500, 10), PlayerCell(1500, 1500, 10)])
    world.players.extend([other, prey])
    other_stats = PlayerStats()
    other_stats.reset(world, other)
    world.update({})
    stats.update(world, player)
    other_stats.update(world, other)
    assert not prey.alive
    assert stats.players_eaten == 0
    assert other_stats.players_eaten == 1
