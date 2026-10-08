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
    c = PlayerCell(0, 0)
    physics.keep_in_bounds(c, 2000, 2000)
    c.x = -10
    physics.keep_in_bounds(c, 2000, 2000)
    assert c.x == 0


def test_speed_factor_for_distance():
    assert physics.speed_factor_for_distance(5) == 0
    assert physics.speed_factor_for_distance(100) == pytest.approx(0.5)
    assert physics.speed_factor_for_distance(1000) == 1


def test_eat_food():
    c = PlayerCell(100, 100, mass=20)  # radius 10
    food = [Food(105, 100), Food(300, 300)]
    assert physics.eat_food(c, food) == 1
    assert c.mass == 20.5
    assert len(food) == 1 and food[0].x == 300
