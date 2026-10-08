import pytest

from agario import physics
from agario.entities import Food, PlayerCell


def test_move_towards_target_full_speed():
    c = PlayerCell(100, 100)
    physics.move_cell(c, (200, 100), 1.0, 2000, 2000)
    assert (c.x, c.y) == pytest.approx((104, 100))


def test_diagonal_speed_is_constant():
    c = PlayerCell(100, 100)
    physics.move_cell(c, (200, 200), 1.0, 2000, 2000)
    assert ((c.x - 100) ** 2 + (c.y - 100) ** 2) ** 0.5 == pytest.approx(4)


def test_speed_factor_scales_and_zero_stops():
    c = PlayerCell(100, 100)
    physics.move_cell(c, (200, 100), 0.5, 2000, 2000)
    assert c.x == pytest.approx(102)
    physics.move_cell(c, (200, 100), 0.0, 2000, 2000)
    assert c.x == pytest.approx(102)


def test_no_overshoot():
    c = PlayerCell(100, 100)
    physics.move_cell(c, (101, 100), 1.0, 2000, 2000)
    assert c.x == pytest.approx(101)


def test_bounds():
    c = PlayerCell(1, 1999)
    physics.move_cell(c, (-500, 5000), 1.0, 2000, 2000)
    assert 0 <= c.x <= 2000 and 0 <= c.y <= 2000
    c = PlayerCell(-10, 5000)
    physics.keep_in_bounds(c, 2000, 2000)
    assert c.x == pytest.approx(c.radius)
    assert c.y == pytest.approx(2000 - c.radius)


def test_bounds_account_for_radius():
    c = PlayerCell(1000, 1000, mass=500)
    for _ in range(1000):
        physics.move_cell(c, (5000, -5000), 1.0, 2000, 2000)
    assert c.x + c.radius <= 2000 + 1e-9
    assert c.y - c.radius >= -1e-9


def test_speed_factor_for_distance():
    assert physics.speed_factor_for_distance(5) == 0
    assert physics.speed_factor_for_distance(100) == pytest.approx(0.5)
    assert physics.speed_factor_for_distance(1000) == 1


def test_eat_food():
    c = PlayerCell(100, 100, mass=20)  # radius 10
    food = [Food(105, 100), Food(300, 300)]
    assert physics.eat_food(c, food) == 1
    assert c.mass == 21
    assert len(food) == 1 and food[0].x == 300


def test_can_eat_ratio_boundary():
    assert physics.can_eat(125, 100)
    assert physics.can_eat(126, 100)
    assert not physics.can_eat(124.9, 100)
    assert not physics.can_eat(100, 100)


def test_can_eat_cell_needs_overlap():
    big, small = PlayerCell(0, 0, 100), PlayerCell(0, 0, 20)
    assert physics.can_eat_cell(big, small)
    small.x = big.radius  # prey centre on the edge: not inside enough
    assert not physics.can_eat_cell(big, small)
    assert not physics.can_eat_cell(small, big)


def test_speed_drops_monotonically_with_mass():
    speeds = [physics.max_speed_for_mass(m) for m in (10, 20, 50, 100, 500, 5000, 1e6)]
    assert speeds[1] == pytest.approx(4)
    assert all(a >= b for a, b in zip(speeds, speeds[1:]))
    assert speeds[2] < speeds[1] and speeds[-1] > 0


def test_big_cell_moves_slower():
    a, b = PlayerCell(100, 100, 20), PlayerCell(100, 100, 400)
    physics.move_cell(a, (1000, 100), 1.0, 2000, 2000)
    physics.move_cell(b, (1000, 100), 1.0, 2000, 2000)
    assert b.x < a.x
