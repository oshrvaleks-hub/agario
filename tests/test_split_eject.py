import math

import pytest

from agario import config
from agario.entities import EjectedMass, Player, PlayerCell
from agario.geometry import distance
from agario.mechanics.eject import eject_mass, update_ejected
from agario.mechanics.split import apply_impulse, resolve_own_cells, split_player
from agario.world import Control, World


def setup(mass=100):
    world = World(2000, 2000)
    player = Player(cells=[PlayerCell(500, 500, mass)])
    world.players.append(player)
    return world, player


def test_split_halves_and_preserves_mass():
    _, player = setup(101)
    split_player(player, (700, 500))
    assert [c.mass for c in player.cells] == [50.5, 50.5]
    assert player.total_mass == 101
    assert all(c.merge_timer == config.MERGE_BASE_TICKS + 50.5 *
               config.MERGE_TICKS_PER_MASS for c in player.cells)


def test_split_threshold_and_only_original_cells():
    _, player = setup(config.SPLIT_MIN_MASS - 0.1)
    split_player(player, (700, 500))
    assert len(player.cells) == 1
    assert player.cells[0].merge_timer == 0
    player.cells[0].mass = config.SPLIT_MIN_MASS
    split_player(player, (700, 500))
    assert len(player.cells) == 2
    _, player = setup(10000)
    split_player(player, (700, 500))
    assert len(player.cells) == 2


def test_split_limit_and_mass_over_repeated_splits():
    _, player = setup(10000)
    for _ in range(8):
        split_player(player, (700, 500))
        assert len(player.cells) <= config.MAX_CELLS
        assert player.total_mass == 10000
    assert len(player.cells) == 16
    player.cells.pop()
    before = player.total_mass
    split_player(player, (700, 500))
    assert len(player.cells) == 16
    assert player.total_mass == before


def test_impulse_direction_decay_and_bounds():
    _, player = setup()
    split_player(player, (800, 900))
    cell = player.cells[1]
    assert (cell.vx, cell.vy) == pytest.approx(
        (0.6 * config.SPLIT_SPEED, 0.8 * config.SPLIT_SPEED))
    apply_impulse(cell, 2000, 2000)
    assert (cell.x, cell.y) == pytest.approx((512, 516))
    assert (cell.vx, cell.vy) == pytest.approx((10.8, 14.4))
    for _ in range(59):
        apply_impulse(cell, 2000, 2000)
    assert math.hypot(cell.vx, cell.vy) < config.SPLIT_SPEED * 0.01
    cell.x = cell.y = 1999
    cell.vx = cell.vy = 20
    apply_impulse(cell, 2000, 2000)
    assert (cell.x, cell.y) == (2000, 2000)


def test_coincident_target_still_launches():
    world, player = setup()
    split_player(player, (500, 500))
    assert player.cells[1].vx > 0
    eject_mass(player, (500, 500), world)
    assert all(shot.vx > 0 for shot in world.ejected)


def test_locked_cells_repel_preserving_centre_and_mass():
    _, player = setup(60)
    player.cells[0].merge_timer = 5
    player.cells.append(PlayerCell(500, 500, 40))
    centre = player.center
    resolve_own_cells(player)
    a, b = player.cells
    assert a.merge_timer == 4
    assert len(player.cells) == 2
    assert distance((a.x, a.y), (b.x, b.y)) >= a.radius + b.radius - 1e-6
    assert player.center == pytest.approx(centre)
    assert player.total_mass == 100


def test_merge_requires_both_timers_and_deep_overlap():
    a = PlayerCell(500, 500, 40, merge_timer=0)
    b = PlayerCell(500, 500, 40, merge_timer=2)
    player = Player(cells=[a, b])
    resolve_own_cells(player)
    assert len(player.cells) == 2
    b.x, b.y = a.x, a.y
    resolve_own_cells(player)
    assert len(player.cells) == 1
    assert player.total_mass == 80
    a = player.cells[0]
    b = PlayerCell(a.x + a.radius, a.y, 20)
    player.cells.append(b)
    resolve_own_cells(player)
    assert len(player.cells) == 2


def test_split_merge_roundtrip_preserves_mass_and_momentum():
    _, player = setup(1280)
    for _ in range(4):
        split_player(player, (800, 500))
    momentum = sum(c.mass * c.vx for c in player.cells)
    for cell in player.cells:
        cell.merge_timer = 0
    resolve_own_cells(player)
    assert len(player.cells) == 1
    assert player.total_mass == 1280
    assert player.cells[0].mass * player.cells[0].vx == pytest.approx(momentum)


def test_eject_cost_projectile_and_threshold():
    world, player = setup(config.EJECT_MIN_MASS)
    player.cells.append(PlayerCell(300, 300, config.EJECT_MIN_MASS - 0.1))
    eject_mass(player, (800, 900), world)
    assert player.cells[0].mass == config.EJECT_MIN_MASS - config.EJECT_COST
    assert player.cells[1].mass == config.EJECT_MIN_MASS - 0.1
    assert len(world.ejected) == 1
    shot = world.ejected[0]
    assert isinstance(shot, EjectedMass)
    assert shot.mass == config.EJECT_MASS
    assert shot.color == player.color
    assert (shot.vx, shot.vy) == pytest.approx(
        (config.EJECT_SPEED * 0.6, config.EJECT_SPEED * 0.8))
    assert shot.source is player.cells[0]


def test_projectile_movement_decay_and_bounds_without_controls():
    world = World(100, 100)
    shot = EjectedMass(90, 50, 14, (1, 2, 3), 16, -5)
    world.ejected.append(shot)
    world.update({})
    assert (shot.x, shot.y) == (100, 45)
    assert (shot.vx, shot.vy) == pytest.approx((14.4, -4.5))


@pytest.mark.parametrize('consumer_mass,alive,eaten', [
    (config.EJECT_MASS, True, False),
    (config.EJECT_MASS - 1, True, False),
    (100, False, False),
    (100, True, True),
])
def test_ejected_consumption(consumer_mass, alive, eaten):
    world, player = setup(consumer_mass)
    player.alive = alive
    world.ejected.append(EjectedMass(500, 500, config.EJECT_MASS, player.color, 0, 0))
    update_ejected(world)
    assert len(world.ejected) == (0 if eaten else 1)
    assert player.total_mass == consumer_mass + (config.EJECT_MASS if eaten else 0)


def test_projectile_outside_radius_is_not_eaten():
    world, player = setup()
    cell = player.cells[0]
    world.ejected.append(EjectedMass(cell.x + cell.radius + 1, cell.y,
                                     config.EJECT_MASS, player.color, 0, 0))
    update_ejected(world)
    assert len(world.ejected) == 1


def test_source_immunity_then_consumption():
    world, player = setup()
    eject_mass(player, (800, 500), world)
    shot = world.ejected[0]
    shot.x = shot.y = 500
    shot.vx = shot.vy = 0
    for _ in range(config.EJECT_IMMUNITY_TICKS):
        update_ejected(world)
        assert len(world.ejected) == 1
    update_ejected(world)
    assert world.ejected == []
    assert player.total_mass == 100 - config.EJECT_COST + config.EJECT_MASS


@pytest.mark.parametrize('sibling', [False, True])
def test_immunity_only_applies_to_exact_source(sibling):
    world, player = setup()
    eject_mass(player, (800, 500), world)
    shot = world.ejected[0]
    shot.vx = shot.vy = 0
    consumer = PlayerCell(shot.x, shot.y, 100)
    if sibling:
        player.cells.append(consumer)
    else:
        world.players.append(Player(cells=[consumer]))
    update_ejected(world)
    assert world.ejected == []
    assert consumer.mass == 100 + config.EJECT_MASS


def test_world_split_and_eject_hooks_and_idle_cooldown():
    world, player = setup()
    world.update({player: Control(target=(900, 500), split=True, eject=True)})
    assert len(player.cells) == 2
    # A sibling may immediately eat the other half's shot.
    assert player.total_mass + sum(s.mass for s in world.ejected) == (
        100 - 2 * (config.EJECT_COST - config.EJECT_MASS))
    assert world.ejected
    assert player.cells[1].vx > 0
    timer = player.cells[0].merge_timer
    x = player.cells[1].x
    world.update({})
    assert player.cells[0].merge_timer == timer - 1
    assert player.cells[1].x > x


def test_eject_from_every_eligible_cell():
    world, player = setup(80)
    player.cells.append(PlayerCell(1000, 1000, 60))
    eject_mass(player, (1500, 1500), world)
    assert [c.mass for c in player.cells] == [80 - config.EJECT_COST,
                                             60 - config.EJECT_COST]
    assert len(world.ejected) == 2
    assert all(s.mass == config.EJECT_MASS for s in world.ejected)


def test_world_resolves_cooldowns_without_controls():
    world, player = setup(40)
    player.cells[0].merge_timer = 1
    player.cells.append(PlayerCell(500, 500, 40, merge_timer=1))
    world.update({})
    assert len(player.cells) == 1
    assert player.total_mass == 80


def test_world_split_near_edge_stays_in_bounds():
    world, player = setup()
    player.cells[0].x = 0
    for _ in range(5):
        world.update({player: Control(target=(-100, 500), split=True)})
        assert all(0 <= c.x <= world.width and 0 <= c.y <= world.height
                   for c in player.cells)
