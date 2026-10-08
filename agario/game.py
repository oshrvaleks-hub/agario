"""pygame setup and the main loop."""
import pygame

from . import config, physics
from .ai import BotBrain
from .camera import Camera
from .entities import Player
from .geometry import distance
from .render import Renderer
from .world import Control, World


def build_world():
    world = World()
    world.spawn_food(config.FOOD_COUNT)
    player = Player.spawn(config.PLAYER_NAME)
    world.players.append(player)
    world.spawn_bots()
    return world, player


def run(max_frames=None):
    """Run the game; stop after `max_frames` frames if given. Returns 0."""
    pygame.init()
    pygame.display.set_caption("{} - v{}".format(config.NAME, config.VERSION))
    surface = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    renderer = Renderer(surface)
    camera = Camera()
    world, player = build_world()
    camera.update(player)
    brains = {bot: BotBrain() for bot in world.players if bot.is_bot}

    frames = 0
    running = True
    while running and (max_frames is None or frames < max_frames):
        clock.tick(config.FPS)

        split = eject = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_SPACE:
                    split = True
                elif e.key == pygame.K_w:
                    eject = True

        mouse = pygame.mouse.get_pos()
        centre = (config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2)
        control = Control(target=camera.screen_to_world(mouse),
                          speed_factor=physics.speed_factor_for_distance(distance(mouse, centre)),
                          split=split, eject=eject)

        controls = {bot: brain.decide(bot, world) for bot, brain in brains.items()
                    if bot.alive and bot.cells}
        controls[player] = control
        world.update(controls)
        camera.update(player)
        renderer.draw(world, camera, player)
        pygame.display.flip()
        frames += 1

    pygame.quit()
    return 0
