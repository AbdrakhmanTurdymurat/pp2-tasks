from __future__ import annotations

import sys
from pathlib import Path

import pygame

from persistence import load_settings, save_settings, load_leaderboard
from racer import SCREEN_W, SCREEN_H, RaceGame, CAR_COLORS, DIFFICULTY_PRESETS
from ui import Button, TextInput, draw_text, WHITE, BLACK, GRAY, YELLOW, PANEL, PANEL_2

ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = ROOT / "settings.json"
LEADERBOARD_PATH = ROOT / "leaderboard.json"

pygame.init()
pygame.display.set_caption("TSIS4 Racer")
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 24, bold=True)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 42, bold=True)
title_font = pygame.font.SysFont("arial", 58, bold=True)

settings = load_settings(SETTINGS_PATH)
leaderboard = load_leaderboard(LEADERBOARD_PATH)

state = "username"
username_input = TextInput((SCREEN_W // 2 - 170, 310, 340, 52), font, placeholder="Enter your name")
username_input.set_value("")
game: RaceGame | None = None

def save_and_reload_settings():
    save_settings(SETTINGS_PATH, settings)

def draw_panel(title, subtitle=None):
    screen.fill((18, 21, 28))
    pygame.draw.rect(screen, PANEL, (80, 70, SCREEN_W - 160, SCREEN_H - 140), border_radius=26)
    pygame.draw.rect(screen, (85, 92, 110), (80, 70, SCREEN_W - 160, SCREEN_H - 140), 2, border_radius=26)
    draw_text(screen, title, title_font, WHITE, SCREEN_W // 2, 128, center=True)
    if subtitle:
        draw_text(screen, subtitle, font, GRAY, SCREEN_W // 2, 182, center=True)

def draw_username_screen():
    draw_panel("TSIS4 Racer", "Enter your name before starting")
    draw_text(screen, "Player name", font, WHITE, SCREEN_W // 2 - 170, 276)
    username_input.draw(screen)
    start_btn.draw(screen)
    draw_text(screen, "Press Enter or click Start", small_font, GRAY, SCREEN_W // 2, 385, center=True)

def draw_menu():
    draw_panel("Main Menu", f"Welcome, {username}")
    for b in menu_buttons:
        b.draw(screen)
    draw_text(screen, "Use Settings to change sound, car color and difficulty.", small_font, GRAY, SCREEN_W // 2, 590, center=True)

def draw_settings():
    draw_panel("Settings", "Preferences are saved in settings.json")
    sound_btn.draw(screen)
    car_left.draw(screen); car_right.draw(screen)
    diff_left.draw(screen); diff_right.draw(screen)
    back_btn.draw(screen)
    draw_text(screen, f"Sound: {'On' if settings['sound_enabled'] else 'Off'}", font, WHITE, 220, 255)
    draw_text(screen, f"Car color: {settings['car_color']}", font, WHITE, 220, 335)
    draw_text(screen, f"Difficulty: {settings['difficulty']}", font, WHITE, 220, 415)
    draw_text(screen, "Saved instantly when changed.", small_font, GRAY, SCREEN_W // 2, 540, center=True)

    preview = pygame.Rect(640, 250, 170, 170)
    pygame.draw.rect(screen, (48, 53, 64), preview, border_radius=22)
    pygame.draw.rect(screen, (95, 104, 124), preview, 2, border_radius=22)
    car_color = CAR_COLORS[settings["car_color"]]
    car = pygame.Rect(692, 286, 66, 96)
    pygame.draw.rect(screen, car_color, car, border_radius=12)
    pygame.draw.rect(screen, (245, 245, 245), car.inflate(-20, -28), 2, border_radius=8)

def draw_leaderboard():
    draw_panel("Leaderboard", "Top 10 scores")
    back_btn.draw(screen)
    rows = load_leaderboard(LEADERBOARD_PATH)
    if not rows:
        draw_text(screen, "No scores yet.", font, GRAY, SCREEN_W // 2, 320, center=True)
        return
    top = rows[:10]
    header_y = 230
    draw_text(screen, "Rank", font, YELLOW, 160, header_y)
    draw_text(screen, "Name", font, YELLOW, 260, header_y)
    draw_text(screen, "Score", font, YELLOW, 500, header_y)
    draw_text(screen, "Distance", font, YELLOW, 650, header_y)
    draw_text(screen, "Coins", font, YELLOW, 800, header_y)
    y = 270
    for idx, row in enumerate(top, start=1):
        pygame.draw.rect(screen, PANEL_2 if idx % 2 else (34, 37, 45), (130, y - 6, 700, 34), border_radius=8)
        draw_text(screen, str(idx), font, WHITE, 160, y)
        draw_text(screen, row.get("name", "Player"), font, WHITE, 260, y)
        draw_text(screen, str(row.get("score", 0)), font, WHITE, 500, y)
        draw_text(screen, str(row.get("distance", 0)), font, WHITE, 650, y)
        draw_text(screen, str(row.get("coins", 0)), font, WHITE, 800, y)
        y += 36

def draw_game_over():
    draw_panel("Game Over", game.reason if game else "")
    retry_btn.draw(screen)
    menu_btn.draw(screen)
    if game:
        stats = [
            f"Player: {game.username}",
            f"Score: {game.score_value()}",
            f"Distance: {int(game.player.distance)}",
            f"Coins: {game.player.coins}",
        ]
        y = 270
        for s in stats:
            draw_text(screen, s, font, WHITE, SCREEN_W // 2, y, center=True)
            y += 42
    draw_text(screen, "Your score has been saved to leaderboard.json", small_font, GRAY, SCREEN_W // 2, 515, center=True)

start_btn = Button((SCREEN_W // 2 - 90, 430, 180, 52), "Start", font, bg=(65, 110, 220), hover=(90, 135, 255))
play_btn = Button((SCREEN_W // 2 - 110, 250, 220, 52), "Play", font, bg=(65, 110, 220), hover=(90, 135, 255))
leaderboard_btn = Button((SCREEN_W // 2 - 110, 318, 220, 52), "Leaderboard", font)
settings_btn = Button((SCREEN_W // 2 - 110, 386, 220, 52), "Settings", font)
quit_btn = Button((SCREEN_W // 2 - 110, 454, 220, 52), "Quit", font, bg=(130, 55, 55), hover=(170, 70, 70))
back_btn = Button((SCREEN_W // 2 - 90, 560, 180, 52), "Back", font)
retry_btn = Button((SCREEN_W // 2 - 190, 600, 170, 52), "Retry", font, bg=(65, 110, 220), hover=(90, 135, 255))
menu_btn = Button((SCREEN_W // 2 + 20, 600, 170, 52), "Main Menu", font)

sound_btn = Button((460, 250, 250, 48), "Toggle Sound", font)
car_left = Button((460, 330, 52, 48), "<", font)
car_right = Button((658, 330, 52, 48), ">", font)
diff_left = Button((460, 410, 52, 48), "<", font)
diff_right = Button((658, 410, 52, 48), ">", font)

menu_buttons = [play_btn, leaderboard_btn, settings_btn, quit_btn]

username = ""
running = True

while running:
    dt = clock.tick(60) / 1000.0
    now = pygame.time.get_ticks() / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        if state == "username":
            username_input.handle_event(event)
            if start_btn.is_clicked(event):
                username = username_input.get_value() or "Player"
                state = "menu"
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                username = username_input.get_value() or "Player"
                state = "menu"

        elif state == "menu":
            if play_btn.is_clicked(event):
                game = RaceGame(settings, username, LEADERBOARD_PATH)
                state = "playing"
            elif leaderboard_btn.is_clicked(event):
                state = "leaderboard"
            elif settings_btn.is_clicked(event):
                state = "settings"
            elif quit_btn.is_clicked(event):
                running = False

        elif state == "settings":
            if sound_btn.is_clicked(event):
                settings["sound_enabled"] = not settings.get("sound_enabled", True)
                save_and_reload_settings()
            elif car_left.is_clicked(event):
                colors = list(CAR_COLORS.keys())
                idx = colors.index(settings["car_color"])
                settings["car_color"] = colors[(idx - 1) % len(colors)]
                save_and_reload_settings()
            elif car_right.is_clicked(event):
                colors = list(CAR_COLORS.keys())
                idx = colors.index(settings["car_color"])
                settings["car_color"] = colors[(idx + 1) % len(colors)]
                save_and_reload_settings()
            elif diff_left.is_clicked(event):
                diffs = list(DIFFICULTY_PRESETS.keys())
                idx = diffs.index(settings["difficulty"])
                settings["difficulty"] = diffs[(idx - 1) % len(diffs)]
                save_and_reload_settings()
            elif diff_right.is_clicked(event):
                diffs = list(DIFFICULTY_PRESETS.keys())
                idx = diffs.index(settings["difficulty"])
                settings["difficulty"] = diffs[(idx + 1) % len(diffs)]
                save_and_reload_settings()
            elif back_btn.is_clicked(event):
                state = "menu"

        elif state == "leaderboard":
            if back_btn.is_clicked(event):
                state = "menu"

        elif state == "playing":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    game.player.move_left()
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    game.player.move_right()
                elif event.key == pygame.K_ESCAPE:
                    state = "menu"
            if game and game.game_over:
                state = "game_over"

        elif state == "game_over":
            if retry_btn.is_clicked(event):
                game = RaceGame(settings, username, LEADERBOARD_PATH)
                state = "playing"
            elif menu_btn.is_clicked(event):
                state = "menu"

    if not running:
        break

    if state == "playing" and game:
        game.update(dt, now)
        if game.game_over:
            state = "game_over"

    if state == "username":
        draw_username_screen()
    elif state == "menu":
        draw_menu()
    elif state == "settings":
        draw_settings()
    elif state == "leaderboard":
        draw_leaderboard()
    elif state == "playing" and game:
        game.draw(screen, font, small_font)
    elif state == "game_over":
        if game:
            game.draw(screen, font, small_font)
        draw_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit()
