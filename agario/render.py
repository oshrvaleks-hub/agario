"""All pygame drawing."""
import pygame

from . import config
from .geometry import mass_to_radius


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

    def draw(self, world, camera, local_player):
        self.surface.fill(config.BACKGROUND_COLOR)
        self.draw_grid(world, camera)
        self.draw_food(world, camera)
        self.draw_ejected(world, camera)
        for player in world.players:
            self.draw_player(player, camera)
        self.draw_hud(world, local_player)

    def draw_text(self, message, pos, color=config.HUD_TEXT_COLOR):
        self.surface.blit(self.font.render(message, 1, color), pos)

    def draw_grid(self, world, camera):
        zoom = camera.zoom
        x, y = camera.x, camera.y
        w, h = world.width, world.height
        for i in range(0, int(max(w, h)) + 1, config.GRID_STEP):
            if i <= h:
                pygame.draw.line(self.surface, config.GRID_COLOR,
                                 (x, i * zoom + y), ((w + 1) * zoom + x, i * zoom + y), 3)
            if i <= w:
                pygame.draw.line(self.surface, config.GRID_COLOR,
                                 (i * zoom + x, y), (i * zoom + x, (h + 1) * zoom + y), 3)

    def draw_food(self, world, camera):
        zoom = camera.zoom
        for f in world.food:
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
            fw, fh = self.font.size(player.name)
            self.draw_text(player.name, (sx - int(fw / 2), sy - int(fh / 2)),
                           config.PLAYER_NAME_COLOR)

    def draw_hud(self, world, local_player):
        sw, sh = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        score = "Score: " + str(int(local_player.total_mass * 2))
        w, h = self.font.size(score + " ")
        self.surface.blit(pygame.transform.scale(self.scoreboard_surface, (w, h)), (8, sh - 30))
        self.draw_text(score, (10, sh - 30))

        self.surface.blit(self.leaderboard_surface, (sw - 160, 15))
        self.surface.blit(self.big_font.render("Leaderboard", 0, config.HUD_TEXT_COLOR),
                          (sw - 157, 20))
        # Stub: ranks the players currently in the world by mass.
        ranked = sorted(world.players, key=lambda p: p.total_mass, reverse=True)
        for i, p in enumerate(ranked[:config.LEADERBOARD_SIZE], start=1):
            self.draw_text("{}. {}".format(i, p.name), (sw - 157, 20 + 25 * i))
