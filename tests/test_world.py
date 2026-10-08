import pytest

from agario.entities import Food, Player, PlayerCell
from agario.world import Control, World


def setup():
    w = World(1000, 1000)
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
    assert p.total_mass == pytest.approx(20.5)


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
