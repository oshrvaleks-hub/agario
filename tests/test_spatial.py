import math
import random

import pytest

from agario.entities import Food, PlayerCell
from agario.physics import eat_food
from agario.spatial import SpatialGrid, SpatialList
from agario.world import World


def pt(x, y):
    return Food(x, y)


def test_add_and_query_rect_inclusive_edges():
    g = SpatialGrid(100)
    a, b, c = pt(100, 100), pt(250, 100), pt(99.9, 100)
    for o in (a, b, c):
        g.add(o)
    assert len(g) == 3
    found = g.query_rect(100, 100, 250, 100)
    assert {id(o) for o in found} == {id(a), id(b)}


def test_remove_and_double_remove():
    g = SpatialGrid(100)
    a = pt(10, 10)
    g.add(a)
    g.add(a)  # adding twice is a no-op
    assert len(g) == 1
    assert g.remove(a) is True
    assert g.remove(a) is False
    assert len(g) == 0 and g.query_rect(0, 0, 100, 100) == []


def test_equal_valued_objects_are_distinct():
    g = SpatialGrid(100)
    a, b = pt(5, 5), pt(5, 5)
    g.add(a)
    g.add(b)
    g.remove(a)
    assert g.query_rect(0, 0, 10, 10) == [b]


@pytest.mark.parametrize("cx", [99.9, 100.0, 100.1, 200.0])
def test_circle_query_on_cell_borders(cx):
    g = SpatialGrid(100)
    pts = [pt(x, 150) for x in (0, 99.99, 100, 100.01, 200, 300)]
    for o in pts:
        g.add(o)
    got = {id(o) for o in g.query_circle(cx, 150, 50)}
    want = {id(o) for o in pts if abs(o.x - cx) <= 50}
    assert got == want


def test_circle_boundary_is_inclusive():
    g = SpatialGrid(100)
    g.add(pt(103, 104))  # exactly 5 from (100, 100)
    assert len(g.query_circle(100, 100, 5)) == 1
    assert g.query_circle(100, 100, 4.999) == []


def test_map_corners_and_outside_points():
    g = SpatialGrid(100)
    corners = [pt(0, 0), pt(2000, 0), pt(0, 2000), pt(2000, 2000)]
    for o in corners:
        g.add(o)
    assert g.query_circle(0, 0, 1) == [corners[0]]
    assert g.query_circle(2000, 2000, 1) == [corners[3]]
    assert len(g.query_rect(-50, -50, 2050, 2050)) == 4
    g.add(pt(-30, -30))  # negative coordinates must bucket correctly
    assert len(g.query_circle(-30, -30, 1)) == 1


def test_random_queries_match_brute_force():
    rng = random.Random(1)
    g = SpatialGrid(100)
    pts = [pt(rng.uniform(0, 2000), rng.uniform(0, 2000)) for _ in range(500)]
    for o in pts:
        g.add(o)
    for o in rng.sample(pts, 100):
        g.remove(o)
        pts.remove(o)
    for _ in range(50):
        x, y, r = rng.uniform(0, 2000), rng.uniform(0, 2000), rng.uniform(1, 400)
        got = {id(o) for o in g.query_circle(x, y, r)}
        assert got == {id(o) for o in pts if math.hypot(o.x - x, o.y - y) <= r}
        n = g.nearest(x, y, r)
        within = [o for o in pts if math.hypot(o.x - x, o.y - y) <= r]
        if within:
            best = min(math.hypot(o.x - x, o.y - y) for o in within)
            assert math.hypot(n.x - x, n.y - y) == pytest.approx(best)
        else:
            assert n is None


def test_nearest_respects_max_radius():
    g = SpatialGrid(100)
    g.add(pt(500, 0))
    assert g.nearest(0, 0, 499) is None
    assert g.nearest(0, 0, 500).x == 500


def test_spatial_list_stays_in_sync():
    items = SpatialList()
    a, b, c = pt(1, 1), pt(2, 2), pt(300, 300)
    items.append(a)
    items.extend([b, c])
    assert len(items.grid) == 3
    items.remove_many([a, c])
    assert items == [b] and len(items.grid) == 1
    items.insert(0, a)
    assert items.pop() is b and len(items.grid) == 1
    items[:] = [b, c]
    assert len(items.grid) == 2 and items.grid.query_circle(300, 300, 1) == [c]
    del items[0]
    assert len(items.grid) == 1
    items += [a]
    assert len(items.grid) == 2
    items.clear()
    assert len(items.grid) == 0


def test_eat_food_uses_grid_and_matches_plain_list():
    rng = random.Random(2)
    pts = [(rng.uniform(0, 300), rng.uniform(0, 300)) for _ in range(300)]
    plain = [Food(x, y) for x, y in pts]
    indexed = SpatialList(Food(x, y) for x, y in pts)
    c1, c2 = PlayerCell(150, 150, 400), PlayerCell(150, 150, 400)
    assert eat_food(c1, plain) == eat_food(c2, indexed) > 0
    assert c1.mass == pytest.approx(c2.mass)
    assert len(plain) == len(indexed) == len(indexed.grid)


def test_world_food_is_indexed_even_when_assigned_a_plain_list():
    w = World(1000, 1000, food_target=0)
    w.food = [Food(10, 10), Food(500, 500)]
    assert len(w.food.grid) == 2
    w.food.append(Food(20, 20))
    assert len(w.food.grid) == 3
