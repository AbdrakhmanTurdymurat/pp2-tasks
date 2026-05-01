import os
from pathlib import Path

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 720
CELL_SIZE = 20
TOP_BAR_HEIGHT = 80
GRID_COLS = SCREEN_WIDTH // CELL_SIZE
GRID_ROWS = (SCREEN_HEIGHT - TOP_BAR_HEIGHT) // CELL_SIZE

FPS = 60

SETTINGS_FILE = Path("settings.json")

DEFAULT_SETTINGS = {
    "snake_color": [0, 200, 0],
    "grid": True,
    "sound": True,
}

SNAKE_COLOR_PRESETS = [
    [0, 200, 0],
    [0, 150, 255],
    [255, 120, 0],
    [170, 0, 255],
    [255, 80, 120],
    [240, 240, 240],
]

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "postgres"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "0"),
}
