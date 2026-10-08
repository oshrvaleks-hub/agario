"""All pygame drawing."""
import pygame

from . import config
from .geometry import mass_to_radius
from .leaderboard import rank_players


class Renderer:
    def __init__(self, surface):
        self.surface = surface
        try:
            self.font = pygame.font.Font(config.FONT_FILE, config.FONT_SIZE)
            self.big_font = pygame.font.Font(config.FONT_FILE, config.BIG_FONT_SIZE)
        except (FileNotFoundError, OSError):
            self.font = pygame.font.SysFont(config.FONT_FALLBACK_NAME, config.FONT_SIZE, True)
            self.big_font = pygame.font.SysFont(config.FONT_FALLBACK_NAME, config.BIG_FONT_SIZE, True)
        self.scoreboard_surface = pygame.Surface((95, 25), pygame.SRCALPHA)
        self.leaderboard_surface = pygame.Surface((155, 278), pygame.SRCALPHA)
        self.scoreboard_surface.fill(config.HUD_PANEL_COLOR)
        self.leaderboard_surface.fill(config.HUD_PANEL_COLOR)
        self._text_cache = {}

    def draw(self, world, camera, local_player):
        self.surface.fill(config.BACKGROUND_COLOR)
        self.draw_grid(world, camera)
        self.draw_food(world, camera)
        self.draw_ejected(world, camera)
        for player in world.players:
            self.draw_player(player, camera)
        self.draw_hud(world, local_player)

    def _text(self, font, message, color, aa=1):
        """Rendered text surface, cached: font.render is expensive."""
        key = (id(font), message, color, aa)
        surf = self._text_cache.get(key)
        if surf is None:
            if len(self._text_cache) > 512:
                self._text_cache.clear()
            surf = self._text_cache[key] = font.render(message, aa, color)
        return surf

    def draw_text(self, message, pos, color=config.HUD_TEXT_COLOR):
        self.surface.blit(self._text(self.font, message, color), pos)

    def draw_grid(self, world, camera):
        zoom = camera.zoom
        x, y = camera.x, camera.y
        w, h = world.width, world.height
        step = config.GRID_STEP
        sw, sh = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        # Only lines that cross the screen (with a small margin for line width).
        first_x = max(0, int((-x) / zoom // step) * step)
        last_x = min(int(max(w, h)), int((sw - x) / zoom // step + 1) * step)
        first_y = max(0, int((-y) / zoom // step) * step)
        last_y = min(int(max(w, h)), int((sh - y) / zoom // step + 1) * step)
        for i in range(first_y, last_y + 1, step):
            if i <= h:
                pygame.draw.line(self.surface, config.GRID_COLOR,
                                 (x, i * zoom + y), ((w + 1) * zoom + x, i * zoom + y), 3)
        for i in range(first_x, last_x + 1, step):
            if i <= w:
                pygame.draw.line(self.surface, config.GRID_COLOR,
                                 (i * zoom + x, y), (i * zoom + x, (h + 1) * zoom + y), 3)

    def draw_food(self, world, camera):
        zoom = camera.zoom
        sw, sh = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        margin = config.FOOD_RADIUS + 2   # world units, covers the min-2px floor too
        x0, y0 = camera.screen_to_world((0, 0))
        x1, y1 = camera.screen_to_world((sw, sh))
        for f in world.food.grid.query_rect(x0 - margin, y0 - margin, x1 + margin, y1 + margin):
            center = camera.world_to_screen((f.x, f.y))
            pygame.draw.circle(self.surface, f.color,
                               (int(center[0]), int(center[1])), max(2, int(config.FOOD_RADIUS * zoom)))

    def draw_ejected(self, world, camera):
        for shot in world.ejected:
            sx, sy = camera.world_to_screen((shot.x, shot.y))
            pygame.draw.circle(self.surface, shot.color, (int(sx), int(sy)),
                               max(1, int(shot.radius * camera.zoom)))

    def draw_player(self, player, camera):
        zoom = camera.zoom
        for cell in player.cells:
            sx, sy = camera.world_to_screen((cell.x, cell.y))
            center = (int(sx), int(sy))
            r = mass_to_radius(cell.mass)
            pygame.draw.circle(self.surface, player.outline_color, center, int((r + 3) * zoom))
            pygame.draw.circle(self.surface, player.color, center, int(r * zoom))
            label = self._text(self.font, player.name, config.PLAYER_NAME_COLOR)
            fw, fh = label.get_size()
            self.surface.blit(label, (sx - int(fw / 2), sy - int(fh / 2)))

    def draw_hud(self, world, local_player):
        sw, sh = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        score = "Score: " + str(int(local_player.total_mass * 2))
        w, h = self.font.size(score + " ")
        self.surface.blit(pygame.transform.scale(self.scoreboard_surface, (w, h)), (8, sh - 30))
        self.draw_text(score, (10, sh - 30))

        rows = rank_players(world.players, local_player, config.LEADERBOARD_SIZE)
        panel_height = 28 + 25 * len(rows)
        panel = pygame.transform.scale(self.leaderboard_surface, (155, panel_height))
        self.surface.blit(panel, (sw - 160, 15))
        self.surface.blit(self._text(self.big_font, "Leaderboard", config.HUD_TEXT_COLOR, 0),
                          (sw - 157, 20))
        for line, (rank, player) in enumerate(rows, start=1):
            color = (config.LEADERBOARD_LOCAL_COLOR if player is local_player
                     else config.HUD_TEXT_COLOR)
            self.draw_text("{}. {}".format(rank, player.name),
                           (sw - 157, 20 + 25 * line), color)
