"""View transform between world and screen. No pygame import."""
from . import config


class Camera:
    def __init__(self, screen_width=config.SCREEN_WIDTH, screen_height=config.SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = 0.0   # screen offset of world origin
        self.y = 0.0
        self.zoom = 0.5

    def update(self, player):
        """Zoom out as the player grows and centre the view on them."""
        self.zoom = config.ZOOM_MASS_FACTOR / player.total_mass + config.ZOOM_BASE
        px, py = player.center
        self.x = self.screen_width / 2 - px * self.zoom
        self.y = self.screen_height / 2 - py * self.zoom

    def world_to_screen(self, pos):
        return pos[0] * self.zoom + self.x, pos[1] * self.zoom + self.y

    def screen_to_world(self, pos):
        return (pos[0] - self.x) / self.zoom, (pos[1] - self.y) / self.zoom
