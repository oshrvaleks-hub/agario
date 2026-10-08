"""All game constants. No pygame import."""

NAME = "agar.io"
VERSION = "0.2"

# Dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 500
MAP_WIDTH, MAP_HEIGHT = 2000, 2000
GRID_STEP = 25

FPS = 60

# Gameplay
FOOD_COUNT = 2000
FOOD_MASS = 7
FOOD_MARGIN = 20
FOOD_EAT_GAIN = 0.5
PLAYER_START_MASS = 20
PLAYER_SPEED = 4
PLAYER_NAME = "GeoVas"

# Mouse control: below STOP_RADIUS px from screen centre the player stays still,
# at FULL_SPEED_DISTANCE px and beyond it moves at full speed.
STOP_RADIUS = 10
FULL_SPEED_DISTANCE = SCREEN_WIDTH / 4

# Camera zoom = ZOOM_MASS_FACTOR / mass + ZOOM_BASE
ZOOM_MASS_FACTOR = 100
ZOOM_BASE = 0.3

# Colors
BACKGROUND_COLOR = (242, 251, 255)
GRID_COLOR = (230, 240, 240)
HUD_TEXT_COLOR = (255, 255, 255)
HUD_PANEL_COLOR = (50, 50, 50, 80)
PLAYER_NAME_COLOR = (50, 50, 50)
PLAYER_COLORS = [
    (37, 7, 255), (35, 183, 253), (48, 254, 241), (19, 79, 251),
    (255, 7, 230), (255, 7, 23), (6, 254, 13),
]
FOOD_COLORS = [
    (80, 252, 54), (36, 244, 255), (243, 31, 46), (4, 39, 243),
    (254, 6, 178), (255, 211, 7), (216, 6, 254), (145, 255, 7),
    (7, 255, 182), (255, 6, 86), (147, 7, 255),
]

# Fonts
FONT_FILE = "Ubuntu-B.ttf"
FONT_FALLBACK_NAME = "Ubuntu"
FONT_SIZE = 20
BIG_FONT_SIZE = 24

# HUD
LEADERBOARD_SIZE = 10

# Split, own-cell merging and mass ejection (speeds are world units per tick).
MAX_CELLS = 16
SPLIT_MIN_MASS = 35
SPLIT_SPEED = 20.0
IMPULSE_FRICTION = 0.90  # Below 1% of initial speed after 44 ticks (~0.73 s).
MERGE_BASE_TICKS = 10 * FPS
MERGE_TICKS_PER_MASS = 0.05 * FPS  # Delay uses the mass of each new half.
MERGE_OVERLAP_RATIO = 0.5  # Merge within half the sum of the two radii.
OWN_CELL_RELAX_PASSES = 16
EJECT_MIN_MASS = 32
EJECT_COST = 18
EJECT_MASS = 14  # Four mass units are lost on each shot.
EJECT_SPEED = 16.0
EJECT_FRICTION = 0.90
EJECT_IMMUNITY_TICKS = 8  # Only the exact source cell is temporarily excluded.
