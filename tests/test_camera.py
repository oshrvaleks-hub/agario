import pytest

from agario.camera import Camera
from agario.entities import Player, PlayerCell


def make_player(x, y, mass):
    return Player(name="t", cells=[PlayerCell(x, y, mass)])


def test_zoom_formula():
    cam = Camera(800, 500)
    cam.update(make_player(500, 500, 100))
    assert cam.zoom == pytest.approx(1.3)


def test_player_is_centered():
    cam = Camera(800, 500)
    cam.update(make_player(700, 300, 20))
    assert cam.world_to_screen((700, 300)) == pytest.approx((400, 250))


def test_roundtrip():
    cam = Camera(800, 500)
    cam.update(make_player(700, 300, 50))
    p = (123.0, 456.0)
    assert cam.screen_to_world(cam.world_to_screen(p)) == pytest.approx(p)
