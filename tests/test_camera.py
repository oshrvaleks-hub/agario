import pytest

from agario import config
from agario.camera import Camera, target_zoom
from agario.entities import Player, PlayerCell


def make_player(x, y, mass):
    return Player(name="t", cells=[PlayerCell(x, y, mass)])


def test_snap_goes_to_target_zoom():
    cam = Camera(800, 500)
    cam.update(make_player(500, 500, 100), snap=True)
    assert cam.zoom == pytest.approx(target_zoom(100))


def test_zoom_smoothly_approaches_target():
    cam = Camera(800, 500)
    p = make_player(500, 500, 400)
    goal = target_zoom(400)
    cam.zoom = 2.0
    prev = abs(cam.zoom - goal)
    for _ in range(200):
        cam.update(p)
        gap = abs(cam.zoom - goal)
        assert gap <= prev
        prev = gap
    assert cam.zoom == pytest.approx(goal, abs=1e-3)
    cam.zoom = 2.0
    cam.update(p)
    assert cam.zoom > goal  # moved only part of the way


def test_zoom_clamped_and_shrinks_with_growth():
    assert target_zoom(1) == config.ZOOM_MAX
    assert target_zoom(1e9) == config.ZOOM_MIN
    assert target_zoom(1000) < target_zoom(100)


def test_player_is_centered():
    cam = Camera(800, 500)
    cam.update(make_player(700, 300, 20))
    assert cam.world_to_screen((700, 300)) == pytest.approx((400, 250))


def test_roundtrip():
    cam = Camera(800, 500)
    cam.update(make_player(700, 300, 50))
    p = (123.0, 456.0)
    assert cam.screen_to_world(cam.world_to_screen(p)) == pytest.approx(p)
