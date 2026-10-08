import pytest

from agario.entities import Player, PlayerCell
from agario.leaderboard import rank_players


def player(mass):
    return Player(cells=[PlayerCell(0, 0, mass)])


def test_order_total_mass_and_stable_ties():
    a, b, c = player(20), player(30), player(20)
    a.cells.append(PlayerCell(0, 0, 20))
    assert rank_players([b, c, a], c) == [(1, a), (2, b), (3, c)]
    assert rank_players([c, player(20)], c)[0] == (1, c)


def test_dead_and_empty_excluded_including_local():
    alive, dead, empty = player(20), player(100), Player()
    dead.alive = False
    assert rank_players([dead, empty, alive], dead) == [(1, alive)]
    assert rank_players([], alive) == []


def test_local_outside_top_has_real_rank():
    players = [player(mass) for mass in range(1, 14)]
    local = players[0]
    rows = rank_players(players, local)
    assert rows[:10] == list(enumerate(reversed(players[3:]), start=1))
    assert rows[-1] == (13, local)
    assert len(rows) == 11
    assert rank_players(players, players[-1], top=2) == [(1, players[-1]), (2, players[-2])]
    assert rank_players(players, local, top=0) == [(13, local)]
    with pytest.raises(ValueError):
        rank_players(players, local, top=-1)
