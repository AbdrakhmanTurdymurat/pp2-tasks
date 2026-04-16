"""
main.py – Moving Ball Game

Controls:
  Arrow Keys  – Move the ball (20 px per press)
  R           – Reset ball to centre
  ESC / Q     – Quit
"""

import pygame
import sys
from ball import Ball

# ── Constants ────────────────────────────────────────────────────────────────
WIDTH,  HEIGHT = 600, 500
FPS            = 60
BG_COLOUR      = (255, 255, 255)
GRID_COLOUR    = (230, 230, 230)
TEXT_COLOUR    = (80,  80,  80)
ACCENT         = (60, 120, 220)


def draw_grid(surface, step=40):
    """Draw a light grid to help visualise movement."""
    for x in range(0, WIDTH,  step):
        pygame.draw.line(surface, GRID_COLOUR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, step):
        pygame.draw.line(surface, GRID_COLOUR, (0, y), (WIDTH, y))


def draw_hud(surface, ball: Ball, font):
    """Display position and controls hint."""
    x, y = ball.position
    pos_text = font.render(f"Position: ({x}, {y})", True, TEXT_COLOUR)
    surface.blit(pos_text, (10, 10))

    hint = font.render("Arrow keys: move  |  R: reset  |  ESC: quit", True, TEXT_COLOUR)
    surface.blit(hint, hint.get_rect(bottomleft=(10, HEIGHT - 8)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Moving Ball")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("Arial", 15)

    ball = Ball(WIDTH, HEIGHT)

    # Direction → (dx, dy) mapping
    KEY_MAP = {
        pygame.K_UP:    ( 0, -Ball.STEP),
        pygame.K_DOWN:  ( 0, +Ball.STEP),
        pygame.K_LEFT:  (-Ball.STEP, 0),
        pygame.K_RIGHT: (+Ball.STEP, 0),
    }

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif k == pygame.K_r:
                    ball = Ball(WIDTH, HEIGHT)   # reset to centre
                elif k in KEY_MAP:
                    dx, dy = KEY_MAP[k]
                    ball.move(dx, dy)

        # ── Render ────────────────────────────────────────────────────────
        screen.fill(BG_COLOUR)
        draw_grid(screen)
        ball.draw(screen)
        draw_hud(screen, ball, font)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()