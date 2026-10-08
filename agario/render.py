"""All pygame drawing."""
import math

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
        self.small_font = pygame.font.Font(None, config.FPS_FONT_SIZE)
        self.scoreboard_surface = pygame.Surface((95, 25), pygame.SRCALPHA)
        self.leaderboard_surface = pygame.Surface((155, 278), pygame.SRCALPHA)
        self.scoreboard_surface.fill(config.HUD_PANEL_COLOR)
        self.leaderboard_surface.fill(config.HUD_PANEL_COLOR)

    def draw(self, world, camera, local_player):
        self.surface.fill(config.BACKGROUND_COLOR)
        self.draw_grid(world, camera)
        self.draw_food(world, camera)
        self.draw_ejected(world, camera)
        objects = [(cell.mass, player, cell)
                   for player in world.players for cell in player.cells]
        objects.extend((virus.mass, None, virus) for virus in world.viruses)
        for _, player, entity in sorted(objects, key=lambda item: item[0]):
            if player is None:
                self.draw_virus(entity, camera)
            else:
                self.draw_player(player, camera, cells=[entity])
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

    def draw_virus(self, virus, camera):
        sx, sy = camera.world_to_screen((virus.x, virus.y))
        radius = virus.radius * camera.zoom
        points = []
        for i in range(config.VIRUS_SPIKES * 2):
            angle = math.pi * i / config.VIRUS_SPIKES
            r = radius * (1.0 if i % 2 == 0 else 0.86)
            points.append((int(sx + math.cos(angle) * r),
                           int(sy + math.sin(angle) * r)))
        pygame.draw.polygon(self.surface, config.VIRUS_COLOR, points)
        pygame.draw.polygon(self.surface, config.VIRUS_OUTLINE_COLOR, points,
                            max(1, int(2 * camera.zoom)))

    def draw_player(self, player, camera, cells=None):
        zoom = camera.zoom
        for cell in player.cells if cells is None else cells:
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
        score = "Score: " + str(int(local_player.total_mass))
        w, h = self.font.size(score + " ")
        self.surface.blit(pygame.transform.scale(self.scoreboard_surface, (w, h)), (8, sh - 30))
        self.draw_text(score, (10, sh - 30))

        rows = rank_players(world.players, local_player, config.LEADERBOARD_SIZE)
        panel_height = 28 + 25 * len(rows)
        panel = pygame.transform.scale(self.leaderboard_surface, (155, panel_height))
        self.surface.blit(panel, (sw - 160, 15))
        self.surface.blit(self.big_font.render("Leaderboard", 0, config.HUD_TEXT_COLOR),
                          (sw - 157, 20))
        for line, (rank, player) in enumerate(rows, start=1):
            color = (config.LEADERBOARD_LOCAL_COLOR if player is local_player
                     else config.HUD_TEXT_COLOR)
            self.draw_text("{}. {}".format(rank, player.name),
                           (sw - 157, 20 + 25 * line), color)

    def draw_fps(self, fps):
        text = self.small_font.render("FPS: {:.0f}".format(fps), True,
                                      config.PLAYER_NAME_COLOR)
        self.surface.blit(text, (8, 8))

    def draw_death(self, stats):
        overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        overlay.fill(config.DEATH_OVERLAY_COLOR)
        self.surface.blit(overlay, (0, 0))
        lines = [
            "You were eaten!",
            "Final score: {:.0f}".format(stats.max_mass),
            "Food eaten: {}".format(stats.food_eaten),
            "Players eaten: {}".format(stats.players_eaten),
            "Time alive: {:.1f}s".format(stats.ticks_alive / config.FPS),
            "Best rank: {}".format(stats.best_rank if stats.best_rank is not None else "-"),
            "Press Enter / Space to play again",
            "or click to restart",
        ]
        width, height = self.surface.get_size()
        top = (height - len(lines) * config.DEATH_LINE_HEIGHT) // 2
        for i, line in enumerate(lines):
            font = self.big_font if i == 0 else self.font
            text = font.render(line, True, config.HUD_TEXT_COLOR)
            self.surface.blit(text, ((width - text.get_width()) // 2,
                                     top + i * config.DEATH_LINE_HEIGHT))
