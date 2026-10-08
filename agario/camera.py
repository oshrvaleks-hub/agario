"""View transform between world and screen. No pygame import."""
from . import config
from .geometry import clamp, mass_to_radius


def target_zoom(total_mass):
    """Zoom the camera settles at for a player of `total_mass`."""
    radius = mass_to_radius(total_mass)
    return clamp(config.ZOOM_VIEW_K / radius, config.ZOOM_MIN, config.ZOOM_MAX)


class Camera:
    def __init__(self, screen_width=config.SCREEN_WIDTH, screen_height=config.SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = 0.0   # screen offset of world origin
        self.y = 0.0
        self.zoom = 0.5

    def update(self, player, snap=False):
        """Ease the zoom toward the player's target zoom and centre on them.

        `snap=True` jumps straight to the target (use for the first frame).
        """
        if not player.cells or player.total_mass <= 0:
            return
        target = target_zoom(player.total_mass)
        if snap:
            self.zoom = target
        else:
            self.zoom += (target - self.zoom) * config.ZOOM_SMOOTHING
        px, py = player.center
        self.x = self.screen_width / 2 - px * self.zoom
        self.y = self.screen_height / 2 - py * self.zoom

    def world_to_screen(self, pos):
        return pos[0] * self.zoom + self.x, pos[1] * self.zoom + self.y

    def screen_to_world(self, pos):
        return (pos[0] - self.x) / self.zoom, (pos[1] - self.y) / self.zoom
