"""
main.py – Interactive Music Player with Keyboard Controls

Keyboard bindings:
  P        – Play / Resume
  S        – Stop
  SPACE    – Pause / Resume
  N        – Next track
  B        – Previous (Back) track
  UP/DOWN  – Volume up / down
  Q / ESC  – Quit
"""

import pygame
import sys
import os
from player import MusicPlayer

# ── Constants ────────────────────────────────────────────────────────────────
WIDTH,  HEIGHT = 480, 340
FPS            = 30
MUSIC_DIR      = os.path.join(os.path.dirname(__file__), "music")

# Colours
BG          = (18,  18,  35)
PANEL       = (30,  30,  55)
ACCENT      = (100, 180, 255)
WHITE       = (240, 240, 250)
GRAY        = (130, 130, 150)
GREEN       = (80,  200, 120)
RED_C       = (220,  80,  80)
YELLOW_C    = (255, 200,  60)


def draw_ui(screen, player: MusicPlayer, fonts: dict):
    """Render the entire player UI."""
    screen.fill(BG)

    # ── Title bar ─────────────────────────────────────────────────────────
    pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, 60))
    title = fonts["large"].render("🎵  Music Player", True, ACCENT)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 30)))

    # ── Album art placeholder ──────────────────────────────────────────────
    art_rect = pygame.Rect(30, 80, 140, 140)
    pygame.draw.rect(screen, PANEL, art_rect, border_radius=12)
    pygame.draw.rect(screen, ACCENT, art_rect, 2, border_radius=12)
    note = fonts["huge"].render("♪", True, ACCENT)
    screen.blit(note, note.get_rect(center=art_rect.center))

    # ── Track info ────────────────────────────────────────────────────────
    info_x = 190
    pos_label = fonts["small"].render(player.position_label, True, GRAY)
    screen.blit(pos_label, (info_x, 85))

    # Track name (truncated)
    name = player.current_name
    if len(name) > 26:
        name = name[:23] + "..."
    track_label = fonts["medium"].render(name, True, WHITE)
    screen.blit(track_label, (info_x, 110))

    # Status badge
    status_colour = {
        "PLAYING": GREEN, "PAUSED": YELLOW_C, "STOPPED": GRAY, "EMPTY": RED_C
    }.get(player.status, WHITE)
    status_label = fonts["small"].render(f"● {player.status}", True, status_colour)
    screen.blit(status_label, (info_x, 145))

    # Volume bar
    vol_text = fonts["small"].render(f"Volume: {int(player.volume * 100)}%", True, GRAY)
    screen.blit(vol_text, (info_x, 175))
    bar_bg = pygame.Rect(info_x, 195, 220, 10)
    bar_fg = pygame.Rect(info_x, 195, int(220 * player.volume), 10)
    pygame.draw.rect(screen, PANEL, bar_bg, border_radius=5)
    pygame.draw.rect(screen, ACCENT, bar_fg, border_radius=5)

    # ── Controls reference ────────────────────────────────────────────────
    pygame.draw.rect(screen, PANEL, (0, 240, WIDTH, HEIGHT - 240), border_radius=10)
    controls = [
        ("[P] Play", GREEN),   ("[S] Stop", RED_C),     ("[SPACE] Pause", YELLOW_C),
        ("[N] Next", ACCENT),  ("[B] Back", ACCENT),    ("[↑/↓] Volume", WHITE),
    ]
    for i, (label, colour) in enumerate(controls):
        x = 20 + (i % 3) * 155
        y = 255 + (i // 3) * 28
        btn = fonts["small"].render(label, True, colour)
        screen.blit(btn, (x, y))

    # Quit hint
    quit_hint = fonts["tiny"].render("Q / ESC  –  Quit", True, GRAY)
    screen.blit(quit_hint, quit_hint.get_rect(bottomright=(WIDTH - 12, HEIGHT - 6)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Music Player")
    tick = pygame.time.Clock()

    # Fonts
    fonts = {
        "huge":   pygame.font.SysFont("Segoe UI Emoji", 54),
        "large":  pygame.font.SysFont("Arial", 22, bold=True),
        "medium": pygame.font.SysFont("Arial", 17, bold=True),
        "small":  pygame.font.SysFont("Arial", 14),
        "tiny":   pygame.font.SysFont("Arial", 11),
    }

    player = MusicPlayer(MUSIC_DIR)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif k == pygame.K_p:
                    player.play()
                elif k == pygame.K_s:
                    player.stop()
                elif k == pygame.K_SPACE:
                    player.pause()
                elif k == pygame.K_n:
                    player.next_track()
                elif k == pygame.K_b:
                    player.prev_track()
                elif k == pygame.K_UP:
                    player.volume_up()
                elif k == pygame.K_DOWN:
                    player.volume_down()

            elif event.type == player.END_EVENT:
                player.on_track_end()

        draw_ui(screen, player, fonts)
        pygame.display.flip()
        tick.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()