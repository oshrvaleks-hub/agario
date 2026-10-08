import math
import random

import pytest

from agario import config, physics
from agario.ai import BotBrain
from agario.entities import EjectedMass, Food, Player, PlayerCell, Virus
from agario.geometry import distance, mass_to_radius
from agario.mechanics.eject import update_ejected
from agario.mechanics.virus import maintain_viruses, update_viruses
from agario.world import World


def scene(mass=200):
    world = World(food_target=0, virus_target=0)
    player = Player(cells=[PlayerCell(1000, 1000, mass)])
    world.players.append(player)
    world.viruses.append(Virus(1000, 1000, config.VIRUS_MASS))
    return world, player


def shot_at(virus, vx=0, vy=0):
    return EjectedMass(virus.x, virus.y, config.EJECT_MASS, (1, 2, 3), vx, vy)


def test_virus_defaults_and_shared_radius():
    virus = Virus(1, 2, 100)
    assert (virus.vx, virus.vy, virus.fed) == (0, 0, 0)
    assert virus.radius == mass_to_radius(100)


def test_large_cell_bursts_radially_and_preserves_total_mass():
    world, player = scene(200)
    world.update({})
    assert world.viruses == []
    assert len(player.cells) == 15
    assert player.total_mass == pytest.approx(300)
    assert all(c.merge_timer > 0 for c in player.cells)
    assert all(math.hypot(c.vx, c.vy) == pytest.approx(config.VIRUS_BURST_SPEED)
               for c in player.cells)
    assert any(c.vx < 0 for c in player.cells)
    assert any(c.vx > 0 for c in player.cells)
    assert any(c.vy < 0 for c in player.cells)
    assert any(c.vy > 0 for c in player.cells)
    assert sum(c.mass * c.vx for c in player.cells) == pytest.approx(0, abs=1e-9)
    assert sum(c.mass * c.vy for c in player.cells) == pytest.approx(0, abs=1e-9)
    positions = [(c.x, c.y) for c in player.cells]
    world.update({})
    assert player.total_mass == pytest.approx(300)
    assert len(player.cells) == 15  # Cooldown prevents immediate re-merging.
    assert [(c.x, c.y) for c in player.cells] != positions


@pytest.mark.parametrize('existing', [1, 14, 15, 16])
def test_burst_respects_available_cell_slots(existing):
    world, player = scene(1000)
    player.cells.extend(PlayerCell(200, 200, 20, merge_timer=100)
                        for _ in range(existing - 1))
    total = player.total_mass + config.VIRUS_MASS
    update_viruses(world)
    assert len(player.cells) == config.MAX_CELLS
    assert player.total_mass == pytest.approx(total)
    assert world.viruses == []
    assert player.cells[0].merge_timer > 0


@pytest.mark.parametrize('mass', [20, 100, 124.99])
def test_small_cell_passes_through_without_effect(mass):
    world, player = scene(mass)
    world.update({})
    assert len(player.cells) == 1
    assert player.total_mass == mass
    assert player.cells[0].merge_timer == 0
    assert len(world.viruses) == 1


def test_exact_eating_ratio_can_burst():
    world, player = scene(config.VIRUS_MASS * config.EAT_MASS_RATIO)
    update_viruses(world)
    assert world.viruses == []
    assert len(player.cells) > 1
    assert player.total_mass == pytest.approx(225)


def test_virus_centre_requires_normal_eating_overlap():
    world, player = scene()
    world.viruses[0].x += player.cells[0].radius
    update_viruses(world)
    assert len(world.viruses) == 1
    assert player.total_mass == 200


def test_shared_can_eat_rule_is_used(monkeypatch):
    world, player = scene()
    monkeypatch.setattr(physics, 'can_eat', lambda eater, prey: False)
    update_viruses(world)
    assert len(world.viruses) == 1 and len(player.cells) == 1


def test_dead_player_does_not_consume_virus():
    world, player = scene()
    player.alive = False
    update_viruses(world)
    assert len(world.viruses) == 1
    assert player.total_mass == 200


def test_virus_is_consumed_only_once():
    world, player = scene()
    other = Player(cells=[PlayerCell(1000, 1000, 200)])
    world.players.append(other)
    update_viruses(world)
    assert world.viruses == []
    assert player.total_mass + other.total_mass == pytest.approx(500)


def test_seven_shots_launch_child_along_last_shot():
    world, _ = scene(20)
    parent = world.viruses[0]
    for i in range(config.VIRUS_FEED_SHOTS - 1):
        world.ejected.append(shot_at(parent, -3, 0))
        update_ejected(world)
        assert world.ejected == []
        assert len(world.viruses) == 1
        assert parent.fed == i + 1
        assert parent.mass == config.VIRUS_MASS + (i + 1) * config.EJECT_MASS
    world.ejected.append(shot_at(parent, 3, 4))
    update_ejected(world)
    assert world.ejected == []
    assert len(world.viruses) == 2
    assert (parent.mass, parent.fed) == (config.VIRUS_MASS, 0)
    child = world.viruses[1]
    assert child.mass == config.VIRUS_MASS and child.fed == 0
    assert (child.vx, child.vy) == pytest.approx(
        (0.6 * config.VIRUS_LAUNCH_SPEED, 0.8 * config.VIRUS_LAUNCH_SPEED))
    before = (child.x, child.y)
    update_viruses(world)
    assert child.x > before[0] and child.y > before[1]
    assert math.hypot(child.vx, child.vy) == pytest.approx(
        config.VIRUS_LAUNCH_SPEED * config.IMPULSE_FRICTION)
    # Parent can start another feeding cycle.
    world.ejected.append(shot_at(parent))
    update_ejected(world)
    assert parent.fed == 1


def test_feeding_has_priority_over_player_consumption():
    world, player = scene(100)
    virus = world.viruses[0]
    world.ejected.append(shot_at(virus))
    world.update({})
    assert virus.fed == 1
    assert world.ejected == []
    assert player.total_mass == 100


def test_shots_missing_virus_do_not_feed_it():
    world, _ = scene(20)
    virus = world.viruses[0]
    world.ejected.append(EjectedMass(virus.x + virus.radius + 1, virus.y,
                                     14, (1, 2, 3), 0, 0))
    update_ejected(world)
    assert virus.fed == 0 and virus.mass == config.VIRUS_MASS
    assert len(world.ejected) == 1


def test_burst_precedes_player_vs_player_eating():
    world, player = scene(200)
    other = Player(cells=[PlayerCell(1000, 1000, 50)])
    world.players.append(other)
    world.update({})
    assert world.viruses == []
    assert other.alive  # The large cell burst before it could swallow this player.
    assert player.total_mass + other.total_mass == pytest.approx(350)


def test_population_is_filled_and_replenished_safely():
    world = World(food_target=0)
    player = Player(cells=[PlayerCell(1000, 1000, 200)])
    world.players.append(player)
    maintain_viruses(world, random.Random(42))
    assert len(world.viruses) == config.VIRUS_COUNT
    for virus in world.viruses:
        assert virus.radius <= virus.x <= world.width - virus.radius
        assert virus.radius <= virus.y <= world.height - virus.radius
        assert distance(player.center, (virus.x, virus.y)) >= (
            player.cells[0].radius + virus.radius + config.VIRUS_SPAWN_MARGIN)
    del world.viruses[:5]
    world.update({})
    assert len(world.viruses) == config.VIRUS_COUNT
    # An excess produced by feeding is retained.
    world.viruses.append(Virus(1500, 1500, config.VIRUS_MASS))
    maintain_viruses(world, random.Random(42))
    assert len(world.viruses) == config.VIRUS_COUNT + 1


def test_spawn_avoids_all_live_cells_but_ignores_dead_players():
    world = World(100, 100, food_target=0, virus_target=1)
    player = Player(cells=[PlayerCell(50, 50, 500)])
    world.players.append(player)
    maintain_viruses(world, random.Random(1))
    assert world.viruses == []
    player.alive = False
    maintain_viruses(world, random.Random(1))
    assert len(world.viruses) == 1


def test_spawning_handles_tiny_maps_without_looping():
    world = World(10, 10, food_target=0)
    world.update({})
    assert world.viruses == []


def test_burst_and_launched_virus_stay_inside_map():
    world, player = scene()
    cell, virus = player.cells[0], world.viruses[0]
    cell.x = cell.radius
    cell.y = cell.radius
    virus.x, virus.y = cell.x, cell.y
    update_viruses(world)
    assert len(player.cells) > 1
    assert all(c.radius <= c.x <= world.width - c.radius and
               c.radius <= c.y <= world.height - c.radius for c in player.cells)
    virus = Virus(1990, 1990, config.VIRUS_MASS, 100, 100)
    world.viruses.append(virus)
    update_viruses(world)
    assert virus.x + virus.radius <= world.width
    assert virus.y + virus.radius <= world.height


@pytest.mark.parametrize('mass,should_flee', [(125, True), (124.9, False), (20, False)])
def test_bot_avoids_only_viruses_it_can_swallow(mass, should_flee):
    world, bot = scene(mass)
    bot.is_bot = True
    world.viruses[0].x += 100
    world.food.append(Food(1010, 1000))
    control = BotBrain(random.Random(1)).decide(bot, world)
    if should_flee:
        assert control.target[0] < bot.center[0]
    else:
        assert control.target == (1010, 1000)


def test_bot_uses_individual_cell_mass_for_virus_threat():
    world, bot = scene(70)
    bot.cells.append(PlayerCell(1000, 1000, 70, merge_timer=100))
    world.viruses[0].x += 100
    world.food.append(Food(1010, 1000))
    assert BotBrain().decide(bot, world).target == (1010, 1000)
    bot.cells[1].mass = 125
    assert BotBrain().decide(bot, world).target[0] < bot.center[0]
