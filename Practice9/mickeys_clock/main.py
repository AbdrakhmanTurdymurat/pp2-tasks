"""
main.py – Mickey's Clock Application
Displays current time using Mickey Mouse as the clock face.
  • Right arm = minute hand
  • Left arm  = second hand
Updates every second in sync with the system clock.
"""

import pygame
import sys
from clock import draw_clock

# ── Constants ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 500, 560
FPS           = 60
CLOCK_CX      = WIDTH  // 2
CLOCK_CY      = HEIGHT // 2 - 20
CLOCK_RADIUS  = 180
BG_COLOUR     = (240, 240, 245)
TITLE         = "Mickey's Clock"


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Custom event fired every 1 000 ms to refresh the display
    TICK_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(TICK_EVENT, 1000)

    running = True
    while running:
        # ── Event handling ────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ── Drawing ───────────────────────────────────────────────────────
        screen.fill(BG_COLOUR)
        draw_clock(screen, CLOCK_CX, CLOCK_CY, CLOCK_RADIUS)

        # Title label
        title_font = pygame.font.SysFont("Arial", 22, bold=True)
        label = title_font.render(TITLE, True, (80, 80, 80))
        screen.blit(label, label.get_rect(center=(WIDTH // 2, 30)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()