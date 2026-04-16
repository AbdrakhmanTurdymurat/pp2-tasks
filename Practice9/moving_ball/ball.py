"""
ball.py – Ball entity for the Moving Ball game.
Handles position, movement, and boundary collision.
"""

import pygame


class Ball:
    """A red circle that moves by 20-pixel steps inside screen bounds."""

    RADIUS    = 25          # px
    STEP      = 20          # px per key press
    COLOUR    = (220, 40, 40)
    HIGHLIGHT = (255, 120, 120)

    def __init__(self, screen_width: int, screen_height: int):
        self.sw = screen_width
        self.sh = screen_height
        # Start at screen centre
        self.x = screen_width  // 2
        self.y = screen_height // 2

    # ── Movement ─────────────────────────────────────────────────────────────

    def _clamp(self, x: int, y: int) -> tuple[int, int]:
        """Return (x, y) clamped so the ball stays fully on screen."""
        r = self.RADIUS
        x = max(r, min(self.sw - r, x))
        y = max(r, min(self.sh - r, y))
        return x, y

    def move(self, dx: int, dy: int):
        """Attempt to move by (dx, dy). Ignore if it would leave the screen."""
        nx, ny = self.x + dx, self.y + dy
        # Discard the move if either axis would go out of bounds
        if nx - self.RADIUS < 0 or nx + self.RADIUS > self.sw:
            return
        if ny - self.RADIUS < 0 or ny + self.RADIUS > self.sh:
            return
        self.x, self.y = nx, ny

    # ── Drawing ──────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        """Draw the ball with a simple highlight for a 3-D look."""
        cx, cy = self.x, self.y
        r = self.RADIUS
        pygame.draw.circle(surface, self.COLOUR,    (cx, cy),          r)
        pygame.draw.circle(surface, self.HIGHLIGHT, (cx - r//4, cy - r//4), r // 3)
        pygame.draw.circle(surface, (150, 10, 10),  (cx, cy),          r, 2)

    # ── State ────────────────────────────────────────────────────────────────

    @property
    def position(self) -> tuple[int, int]:
        return (self.x, self.y)