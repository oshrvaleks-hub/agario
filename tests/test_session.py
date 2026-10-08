import random
from types import SimpleNamespace

import pytest

from agario import config
from agario.entities import Food, Player, PlayerCell
from agario.session import GameSession, GameState
from agario.world import Control, World


def setup():
    world = World(food_target=0)
    player = Player(name='Local', cells=[PlayerCell(500, 500, 20)])
    bot = Player(name='Bot', cells=[PlayerCell(1500, 1500, 30)], is_bot=True)
    world.players = [player, bot]
    world.food = [Food(500, 500)]
    return world, player, bot, GameSession(world, player, random.Random(42))


@pytest.mark.parametrize('empty', [True, False])
def test_death_freezes_stats_while_world_lives(empty):
    world, player, bot, session = setup()
    world.update({player: Control(player.center)})
    session.update()
    assert session.state is GameState.PLAYING
    if empty:
        player.cells.clear()
    else:
        player.alive = False
    session.update()
    assert session.state is GameState.DEAD and not player.alive
    frozen = vars(session.stats).copy()
    position = bot.center
    for _ in range(5):
        world.update({bot: Control((1800, 1500), 1)})
        session.update()
    assert vars(session.stats) == frozen
    assert bot.center != position


def test_restart_same_world_resets_every_stat_and_does_not_touch_bots_food():
    world, player, bot, session = setup()
    world.update({player: Control(player.center)})
    session.update()
    player.alive = False
    session.update()
    players, food, bot_cells = world.players, world.food, bot.cells
    bot_position = bot.center
    food_copy = list(food)
    assert session.restart()
    assert session.world is world and session.player is player
    assert world.players is players and world.food is food and food == food_copy
    assert bot.cells is bot_cells and bot.center == bot_position
    assert player.name == 'Local' and player.alive
    assert len(player.cells) == 1 and player.total_mass == config.PLAYER_START_MASS
    assert player.cells[0].vx == player.cells[0].vy == player.cells[0].merge_timer == 0
    assert session.state is GameState.PLAYING
    assert session.stats.max_mass == config.PLAYER_START_MASS
    assert session.stats.food_eaten == session.stats.players_eaten == session.stats.ticks_alive == 0
    assert session.stats.best_rank == 2
    world.food.append(Food(*player.center))
    world.update({player: Control(player.center)})
    session.update()
    assert session.stats.food_eaten == 1 and session.stats.ticks_alive == 1
    assert not session.restart()


def test_restart_fails_safely_when_map_blocked():
    world, player, bot, session = setup()
    player.cells.clear()
    session.update()
    world.viruses = [SimpleNamespace(x=1000, y=1000, mass=1e9)]
    assert not session.restart()
    assert session.state is GameState.DEAD and not player.alive
    assert not player.cells


def test_session_can_start_dead():
    world, player, _, _ = setup()
    player.cells.clear()
    session = GameSession(world, player)
    assert session.state is GameState.DEAD and not player.alive
    assert session.restart()
