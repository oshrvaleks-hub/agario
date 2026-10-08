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
FOOD_MASS = 1
FOOD_MARGIN = 20
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


# --- Eating / growth / speed / zoom (feat/eating-growth) ---
# radius = RADIUS_PER_SQRT_MASS * sqrt(mass); start mass 20 -> radius ~10
RADIUS_PER_SQRT_MASS = 2.236
FOOD_RADIUS = 3                 # food is drawn with this fixed radius; eating it gives +food.mass
EAT_MASS_RATIO = 1.25           # eater needs >= ratio * prey mass
EAT_OVERLAP = 0.4               # prey centre must be within R - r * EAT_OVERLAP
SPEED_MASS_EXPONENT = 0.3       # speed = PLAYER_SPEED * (start_mass / mass) ** exponent
MIN_SPEED = 0.8
FOOD_RESPAWN_PER_TICK = 5       # food added per tick while below FOOD_COUNT
ZOOM_VIEW_K = 20                # target zoom = ZOOM_VIEW_K / radius(total mass)
ZOOM_MIN = 0.15
ZOOM_MAX = 2.0
ZOOM_SMOOTHING = 0.1            # fraction of the gap closed per update

# --- Split, own-cell merging and mass ejection (feat/split-eject) ---
# Speeds are world units per tick.
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

# --- Bots and live leaderboard (feat/bots) ---
BOT_COUNT = 10
BOT_NAMES = ("Blobby", "Nom", "Cookie", "Pebble", "Mochi", "Bean",
             "Bubbles", "Pudding", "Dot", "Jelly")
BOT_VIEW_RADIUS = 500
BOT_DECISION_TICKS = 8
BOT_WANDER_TICKS = 120
BOT_RESPAWN_TICKS = 180
LEADERBOARD_LOCAL_COLOR = (255, 225, 90)

# --- Death, restart and lifetime statistics (feat/death-restart) ---
SAFE_SPAWN_ATTEMPTS = 256
SAFE_SPAWN_GRID_STEPS = 32
FPS_FONT_SIZE = 18
DEATH_OVERLAY_COLOR = (0, 0, 0, 180)
DEATH_LINE_HEIGHT = 32
