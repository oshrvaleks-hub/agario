import pytest

from agario.entities import Food, Player, PlayerCell
from agario.world import Control, World


def setup():
    w = World(1000, 1000, food_target=0)
    p = Player(name="p", cells=[PlayerCell(500, 500, 20)])
    w.players.append(p)
    return w, p


def test_empty_hooks():
    w, _ = setup()
    assert w.viruses == [] and w.ejected == []


def test_moves_toward_target():
    w, p = setup()
    w.update({p: Control(target=(600, 500), speed_factor=1.0)})
    assert p.cells[0].x == pytest.approx(504)
    assert p.cells[0].y == pytest.approx(500)


def test_eats_food():
    w, p = setup()
    w.food.append(Food(505, 500))
    w.food.append(Food(900, 900))
    w.update({p: Control(target=(500, 500), speed_factor=0.0)})
    assert len(w.food) == 1
    assert p.total_mass == pytest.approx(21)


def test_map_bounds():
    w, p = setup()
    p.cells[0].x = p.cells[0].y = 999
    for _ in range(10):
        w.update({p: Control(target=(5000, 5000), speed_factor=1.0)})
    assert p.cells[0].x <= 1000 and p.cells[0].y <= 1000


def test_split_eject_ignored():
    w, p = setup()
    w.update({p: Control(target=(500, 500), split=True, eject=True)})
    assert len(p.cells) == 1 and w.ejected == []


def test_food_respawns_gradually():
    w = World(1000, 1000, food_target=100)
    w.update({})
    assert 0 < len(w.food) < 100
    for _ in range(100):
        w.update({})
    assert len(w.food) == 100


def test_big_player_eats_small_player():
    w, big = setup()
    small = Player(name="s", cells=[PlayerCell(502, 500, 20)])
    big.cells[0].mass = 100
    w.players.append(small)
    w.update({big: Control(target=(500, 500)), small: Control(target=(502, 500))})
    assert big.total_mass == pytest.approx(120)
    assert small.cells == [] and not small.alive and big.alive


def test_similar_size_do_not_eat():
    w, a = setup()
    b = Player(name="b", cells=[PlayerCell(500, 500, 24)])
    w.players.append(b)
    w.update({a: Control(target=(500, 500)), b: Control(target=(500, 500))})
    assert a.alive and b.alive and len(a.cells) == 1 and len(b.cells) == 1


def test_own_cells_do_not_eat_each_other():
    w, p = setup()
    p.cells = [PlayerCell(500, 500, 100), PlayerCell(500, 500, 20)]
    w.update({p: Control(target=(500, 500))})
    assert len(p.cells) == 2 and p.alive
