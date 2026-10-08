import pytest

from agario.geometry import clamp, distance, mass_to_radius, normalize


def test_distance():
    assert distance((0, 0), (3, 4)) == 5
    assert distance((1, 1), (1, 1)) == 0


def test_normalize():
    assert normalize(3, 4) == pytest.approx((0.6, 0.8))
    assert normalize(0, 0) == (0.0, 0.0)


def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


def test_mass_to_radius():
    assert mass_to_radius(20) == 10
