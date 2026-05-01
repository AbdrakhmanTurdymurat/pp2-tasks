from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from config import (
    CELL_SIZE,
    DEFAULT_SETTINGS,
    FPS,
    GRID_COLS,
    GRID_ROWS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SNAKE_COLOR_PRESETS,
    SETTINGS_FILE,
    TOP_BAR_HEIGHT,
)
from db import get_leaderboard, get_personal_best, init_db, save_game_session

Vec = Tuple[int, int]
Point = Tuple[int, int]


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            snake_color = data.get("snake_color", DEFAULT_SETTINGS["snake_color"])
            if not (isinstance(snake_color, list) and len(snake_color) == 3):
                snake_color = DEFAULT_SETTINGS["snake_color"]
            return {
                "snake_color": [int(x) for x in snake_color],
                "grid": bool(data.get("grid", DEFAULT_SETTINGS["grid"])),
                "sound": bool(data.get("sound", DEFAULT_SETTINGS["sound"])),
            }
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


@dataclass
class Button:
    rect: pygame.Rect
    text: str

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, hover: bool = False):
        fill = (60, 60, 70) if not hover else (90, 90, 105)
        pygame.draw.rect(surface, fill, self.rect, border_radius=12)
        pygame.draw.rect(surface, (200, 200, 210), self.rect, 2, border_radius=12)
        label = font.render(self.text, True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, event: pygame.event.Event) -> bool:
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

    def hover(self, pos) -> bool:
        return self.rect.collidepoint(pos)


class SnakeGame:
    def __init__(self, username: str, settings: dict, personal_best: int):
        self.username = username.strip() or "Player"
        self.settings = settings
        self.personal_best = personal_best
        self.board_w = GRID_COLS
        self.board_h = GRID_ROWS
        self.reset()

    def reset(self):
        self.snake: List[Point] = [(self.board_w // 2, self.board_h // 2)]
        self.direction: Vec = (1, 0)
        self.next_direction: Vec = (1, 0)

        self.score = 0
        self.level = 1
        self.move_delay = 180
        self.last_move = 0

        self.normal_food = None
        self.bonus_food = None
        self.poison_food = None
        self.powerup = None
        self.obstacles = set()

        self.bonus_spawn_at = 0
        self.poison_spawn_at = 0
        self.powerup_spawn_at = 0
        self.bonus_expires_at = 0
        self.poison_expires_at = 0
        self.powerup_expires_at = 0

        self.speed_boost_until = 0
        self.slow_motion_until = 0
        self.shield_ready = False

        self.game_over = False
        self.game_over_reason = ""
        self.paused = False
        self.pending_save = True
        self.obstacle_level = 0

        self.normal_food = self.spawn_point()
        now = pygame.time.get_ticks()
        self.schedule_specials(now)
        self.generate_obstacles(force=True)

    def occupied(self) -> set:
        occ = set(self.snake) | set(self.obstacles)
        if self.normal_food:
            occ.add(self.normal_food)
        if self.bonus_food:
            occ.add(self.bonus_food)
        if self.poison_food:
            occ.add(self.poison_food)
        if self.powerup and self.powerup.get("pos"):
            occ.add(self.powerup["pos"])
        return occ

    def spawn_point(self, avoid_head_zone: bool = False) -> Point:
        head = self.snake[0]
        blocked = self.occupied()
        for _ in range(3000):
            p = (random.randint(0, self.board_w - 1), random.randint(0, self.board_h - 1))
            if p in blocked:
                continue
            if avoid_head_zone and abs(p[0] - head[0]) <= 2 and abs(p[1] - head[1]) <= 2:
                continue
            return p
        return (1, 1)

    def schedule_specials(self, now: int):
        self.bonus_spawn_at = now + random.randint(4000, 7000)
        self.poison_spawn_at = now + random.randint(5000, 9000)
        self.powerup_spawn_at = now + random.randint(7000, 12000)

    def generate_obstacles(self, force: bool = False):
        if self.level < 3:
            if force:
                self.obstacles = set()
            return

        if not force and self.level == self.obstacle_level:
            return

        self.obstacle_level = self.level
        self.obstacles = set()
        head = self.snake[0]
        safe_zone = {(head[0] + dx, head[1] + dy) for dx in range(-2, 3) for dy in range(-2, 3)}
        count = min(4 + self.level * 2, 20)

        attempts = 0
        while len(self.obstacles) < count and attempts < 4000:
            attempts += 1
            p = (random.randint(1, self.board_w - 2), random.randint(1, self.board_h - 2))
            if p in self.snake or p in self.obstacles or p in safe_zone:
                continue
            if abs(p[0] - head[0]) + abs(p[1] - head[1]) <= 2:
                continue
            self.obstacles.add(p)

    def effective_delay(self, now: int) -> int:
        base = max(65, 180 - (self.level - 1) * 15)
        mult = 1.0
        if now < self.speed_boost_until:
            mult *= 0.65
        if now < self.slow_motion_until:
            mult *= 1.35
        return max(50, int(base * mult))

    def update_level(self):
        new_level = 1 + self.score // 5
        if new_level != self.level:
            self.level = new_level
            self.generate_obstacles(force=True)

    def maybe_spawn_items(self, now: int):
        if self.bonus_food is None and now >= self.bonus_spawn_at:
            self.bonus_food = self.spawn_point()
            self.bonus_expires_at = now + 7000

        if self.poison_food is None and now >= self.poison_spawn_at:
            if random.random() < 0.75:
                self.poison_food = self.spawn_point()
                self.poison_expires_at = now + 8000
            self.poison_spawn_at = now + random.randint(6000, 11000)

        if self.powerup is None and now >= self.powerup_spawn_at:
            kind = random.choice(["speed_boost", "slow_motion", "shield"])
            self.powerup = {"type": kind, "pos": self.spawn_point()}
            self.powerup_expires_at = now + 8000

    def expire_items(self, now: int):
        if self.bonus_food and now >= self.bonus_expires_at:
            self.bonus_food = None
            self.bonus_spawn_at = now + random.randint(4000, 8000)

        if self.poison_food and now >= self.poison_expires_at:
            self.poison_food = None
            self.poison_spawn_at = now + random.randint(5000, 9000)

        if self.powerup and now >= self.powerup_expires_at:
            self.powerup = None
            self.powerup_spawn_at = now + random.randint(7000, 12000)

    def set_game_over(self, reason: str):
        self.game_over = True
        self.game_over_reason = reason

    def shorten_snake(self, amount: int = 2):
        for _ in range(amount):
            if len(self.snake) > 1:
                self.snake.pop()

    def move(self, now: int):
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        hit_wall = new_head[0] < 0 or new_head[0] >= self.board_w or new_head[1] < 0 or new_head[1] >= self.board_h
        hit_obstacle = new_head in self.obstacles
        hit_self = new_head in self.snake

        if hit_wall or hit_obstacle or hit_self:
            if self.shield_ready:
                self.shield_ready = False
            else:
                reason = "wall"
                if hit_obstacle:
                    reason = "obstacle"
                elif hit_self:
                    reason = "self"
                self.set_game_over(reason)
                return

        self.snake.insert(0, new_head)
        ate = False

        if self.normal_food == new_head:
            self.normal_food = self.spawn_point()
            self.score += 1
            ate = True
            self.bonus_spawn_at = now + random.randint(1500, 4500)
            if self.poison_food is None:
                self.poison_spawn_at = now + random.randint(1500, 5000)

        if self.bonus_food == new_head:
            self.bonus_food = None
            self.score += 3
            ate = True
            self.bonus_spawn_at = now + random.randint(4000, 8000)

        if self.poison_food == new_head:
            self.poison_food = None
            self.shorten_snake(2)
            if len(self.snake) <= 1:
                self.set_game_over("poison")
                return

        if self.powerup and self.powerup.get("pos") == new_head:
            kind = self.powerup["type"]
            if kind == "speed_boost":
                self.speed_boost_until = now + 5000
            elif kind == "slow_motion":
                self.slow_motion_until = now + 5000
            elif kind == "shield":
                self.shield_ready = True
            self.powerup = None
            self.powerup_spawn_at = now + random.randint(7000, 12000)

        if not ate:
            self.snake.pop()

        self.update_level()
        self.move_delay = self.effective_delay(now)
        if self.score > self.personal_best:
            self.personal_best = self.score

    def update(self):
        now = pygame.time.get_ticks()
        self.expire_items(now)
        self.maybe_spawn_items(now)
        self.move_delay = self.effective_delay(now)

        if self.game_over or self.paused:
            return

        if now - self.last_move >= self.move_delay:
            self.last_move = now
            self.move(now)

    def handle_key(self, key: int):
        if key == pygame.K_UP and self.direction != (0, 1):
            self.next_direction = (0, -1)
        elif key == pygame.K_DOWN and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif key == pygame.K_LEFT and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif key == pygame.K_RIGHT and self.direction != (-1, 0):
            self.next_direction = (1, 0)
        elif key == pygame.K_p:
            self.paused = not self.paused

    def save_result(self) -> bool:
        if not self.pending_save:
            return False
        self.pending_save = False
        return save_game_session(self.username, self.score, self.level)

    def draw_grid(self, surface: pygame.Surface):
        if not self.settings.get("grid", True):
            return
        line = (38, 38, 42)
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(surface, line, (x, TOP_BAR_HEIGHT), (x, SCREEN_HEIGHT))
        for y in range(TOP_BAR_HEIGHT, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(surface, line, (0, y), (SCREEN_WIDTH, y))

    def draw_cell(self, surface: pygame.Surface, cell: Point, color: Tuple[int, int, int], inset: int = 1):
        x = cell[0] * CELL_SIZE
        y = TOP_BAR_HEIGHT + cell[1] * CELL_SIZE
        rect = pygame.Rect(x + inset, y + inset, CELL_SIZE - inset * 2, CELL_SIZE - inset * 2)
        pygame.draw.rect(surface, color, rect, border_radius=5)

    def draw(self, surface: pygame.Surface, fonts):
        font, small, big = fonts
        surface.fill((20, 20, 24))
        pygame.draw.rect(surface, (14, 14, 18), (0, TOP_BAR_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - TOP_BAR_HEIGHT))
        self.draw_grid(surface)

        for obs in self.obstacles:
            self.draw_cell(surface, obs, (90, 90, 100), inset=2)

        if self.normal_food:
            self.draw_cell(surface, self.normal_food, (70, 220, 90), inset=3)
        if self.bonus_food:
            self.draw_cell(surface, self.bonus_food, (255, 200, 40), inset=3)
        if self.poison_food:
            self.draw_cell(surface, self.poison_food, (120, 0, 0), inset=3)

        if self.powerup:
            kind = self.powerup["type"]
            color = (80, 170, 255) if kind == "speed_boost" else (255, 120, 200) if kind == "slow_motion" else (220, 220, 255)
            self.draw_cell(surface, self.powerup["pos"], color, inset=2)

        snake_color = tuple(self.settings.get("snake_color", DEFAULT_SETTINGS["snake_color"]))
        for i, segment in enumerate(self.snake):
            col = tuple(clamp(c + 35, 0, 255) for c in snake_color) if i == 0 else snake_color
            self.draw_cell(surface, segment, col, inset=1)

        pygame.draw.rect(surface, (30, 30, 38), (0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.line(surface, (70, 70, 80), (0, TOP_BAR_HEIGHT - 1), (SCREEN_WIDTH, TOP_BAR_HEIGHT - 1))

        texts = [
            f"Player: {self.username}",
            f"Score: {self.score}",
            f"Level: {self.level}",
            f"Best: {self.personal_best}",
        ]
        x = 20
        for t in texts:
            label = font.render(t, True, (240, 240, 240))
            surface.blit(label, (x, 18))
            x += label.get_width() + 26

        status = []
        now = pygame.time.get_ticks()
        if self.shield_ready:
            status.append("Shield ready")
        if now < self.speed_boost_until:
            status.append("Speed boost")
        if now < self.slow_motion_until:
            status.append("Slow motion")
        if self.paused:
            status.append("Paused")

        label = small.render(" | ".join(status) if status else "Use arrow keys to move", True, (210, 210, 210))
        surface.blit(label, label.get_rect(topright=(SCREEN_WIDTH - 20, 18)))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))
            msg = big.render("GAME OVER", True, (255, 255, 255))
            surface.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
            sub = font.render(f"Reason: {self.game_over_reason}", True, (220, 220, 220))
            surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 5)))


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("TSIS 3 - Snake Game")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("arial", 24)
        self.small_font = pygame.font.SysFont("arial", 18)
        self.big_font = pygame.font.SysFont("arial", 42)

        self.settings = load_settings()
        try:
            init_db()
            self.db_ready = True
        except Exception:
            self.db_ready = False

        self.username = "Player"
        self.personal_best = 0
        self.leaderboard_cache = []
        self.state = "menu"
        self.menu_input_active = True
        self.game: Optional[SnakeGame] = None

        self.menu_buttons = [
            Button(pygame.Rect(80, 250, 220, 50), "Play"),
            Button(pygame.Rect(80, 315, 220, 50), "Leaderboard"),
            Button(pygame.Rect(80, 380, 220, 50), "Settings"),
            Button(pygame.Rect(80, 445, 220, 50), "Quit"),
        ]
        self.over_buttons = [
            Button(pygame.Rect(80, 460, 220, 50), "Retry"),
            Button(pygame.Rect(80, 525, 220, 50), "Main Menu"),
        ]
        self.lb_back = Button(pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 80, 240, 48), "Back")
        self.settings_buttons = [
            Button(pygame.Rect(70, 280, 260, 50), "Toggle Grid"),
            Button(pygame.Rect(70, 345, 260, 50), "Toggle Sound"),
            Button(pygame.Rect(70, 410, 260, 50), "Change Snake Color"),
            Button(pygame.Rect(70, 500, 260, 50), "Save & Back"),
        ]
        self.selected_color_index = self.find_color_index(tuple(self.settings["snake_color"]))

    def find_color_index(self, color: Tuple[int, int, int]) -> int:
        for i, c in enumerate(SNAKE_COLOR_PRESETS):
            if tuple(c) == tuple(color):
                return i
        return 0

    def start_game(self):
        self.personal_best = get_personal_best(self.username)
        self.game = SnakeGame(self.username, self.settings, self.personal_best)
        self.state = "game"

    def enter_game_over(self):
        if self.game:
            self.game.save_result()
            self.personal_best = max(self.personal_best, self.game.personal_best)
        self.state = "game_over"

    def open_leaderboard(self):
        self.leaderboard_cache = get_leaderboard(10)
        self.state = "leaderboard"

    def draw_center(self, y: int, text: str, font, color=(255, 255, 255)):
        label = font.render(text, True, color)
        self.screen.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, y)))

    def draw_menu(self):
        self.screen.fill((18, 18, 22))
        self.screen.blit(self.big_font.render("Snake Game", True, (255, 255, 255)), (70, 80))
        self.screen.blit(self.font.render("Type your username, then press Play.", True, (210, 210, 210)), (70, 140))

        box = pygame.Rect(70, 185, 360, 48)
        pygame.draw.rect(self.screen, (42, 42, 50), box, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 210), box, 2, border_radius=10)
        txt = self.font.render(self.username, True, (255, 255, 255))
        self.screen.blit(txt, (box.x + 12, box.y + 10))
        if self.menu_input_active and (pygame.time.get_ticks() // 500) % 2:
            pygame.draw.line(self.screen, (255, 255, 255), (box.x + 12 + txt.get_width() + 4, box.y + 10), (box.x + 12 + txt.get_width() + 4, box.y + 34), 2)

        db_text = "Database: connected" if self.db_ready else "Database: unavailable"
        db_color = (120, 220, 140) if self.db_ready else (255, 140, 140)
        self.screen.blit(self.small_font.render(db_text, True, db_color), (70, 545))
        self.screen.blit(self.small_font.render("Arrow keys move. P pauses. Settings are saved in settings.json.", True, (180, 180, 180)), (70, 575))

        mouse = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            button.draw(self.screen, self.font, button.hover(mouse))

    def draw_game_over(self):
        self.screen.fill((18, 18, 22))
        self.draw_center(90, "Game Over", self.big_font)
        if self.game:
            lines = [
                f"Username: {self.username}",
                f"Final score: {self.game.score}",
                f"Level reached: {self.game.level}",
                f"Personal best: {max(self.personal_best, self.game.personal_best)}",
            ]
            y = 170
            for line in lines:
                self.draw_center(y, line, self.font, (230, 230, 230))
                y += 42
            self.draw_center(340, f"Reason: {self.game.game_over_reason}", self.font, (200, 200, 200))

        mouse = pygame.mouse.get_pos()
        for button in self.over_buttons:
            button.draw(self.screen, self.font, button.hover(mouse))

    def draw_leaderboard(self):
        self.screen.fill((18, 18, 22))
        self.draw_center(50, "Leaderboard", self.big_font)

        headers = ["Rank", "Username", "Score", "Level", "Date"]
        xs = [80, 180, 470, 580, 680]
        for i, h in enumerate(headers):
            self.screen.blit(self.font.render(h, True, (255, 255, 255)), (xs[i], 110))
        pygame.draw.line(self.screen, (100, 100, 110), (70, 145), (SCREEN_WIDTH - 70, 145), 2)

        if not self.leaderboard_cache:
            self.draw_center(230, "No records yet.", self.font, (220, 220, 220))
        else:
            y = 170
            for idx, row in enumerate(self.leaderboard_cache, start=1):
                date_str = row["played_at"].strftime("%Y-%m-%d %H:%M") if row["played_at"] else "-"
                values = [str(idx), row["username"], str(row["score"]), str(row["level_reached"]), date_str]
                for i, value in enumerate(values):
                    self.screen.blit(self.small_font.render(value, True, (230, 230, 230)), (xs[i], y))
                y += 42

        mouse = pygame.mouse.get_pos()
        self.lb_back.draw(self.screen, self.font, self.lb_back.hover(mouse))

    def draw_settings(self):
        self.screen.fill((18, 18, 22))
        self.draw_center(55, "Settings", self.big_font)

        options = [
            f"Grid overlay: {'ON' if self.settings.get('grid', True) else 'OFF'}",
            f"Sound: {'ON' if self.settings.get('sound', True) else 'OFF'}",
            f"Snake color: {tuple(self.settings.get('snake_color', [0, 200, 0]))}",
        ]
        y = 180
        for text in options:
            self.screen.blit(self.font.render(text, True, (240, 240, 240)), (380, y))
            y += 65

        preview_rect = pygame.Rect(680, 287, 70, 70)
        pygame.draw.rect(self.screen, tuple(self.settings["snake_color"]), preview_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), preview_rect, 2, border_radius=12)

        mouse = pygame.mouse.get_pos()
        for button in self.settings_buttons:
            button.draw(self.screen, self.font, button.hover(mouse))

    def handle_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.username = self.username[:-1]
            elif event.key == pygame.K_RETURN:
                self.start_game()
            elif event.key == pygame.K_TAB:
                self.menu_input_active = not self.menu_input_active
            else:
                if len(self.username) < 20 and event.unicode.isprintable() and event.unicode not in "\r\n\t":
                    self.username += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.menu_buttons:
                if button.clicked(event):
                    if button.text == "Play":
                        self.start_game()
                    elif button.text == "Leaderboard":
                        self.open_leaderboard()
                    elif button.text == "Settings":
                        self.state = "settings"
                    elif button.text == "Quit":
                        raise SystemExit

    def handle_game_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "menu"
            elif self.game:
                self.game.handle_key(event.key)

    def handle_game_over_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.over_buttons:
                if button.clicked(event):
                    if button.text == "Retry":
                        self.start_game()
                    else:
                        self.state = "menu"

    def handle_leaderboard_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.lb_back.clicked(event):
            self.state = "menu"

    def handle_settings_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.settings_buttons:
                if button.clicked(event):
                    if button.text == "Toggle Grid":
                        self.settings["grid"] = not self.settings.get("grid", True)
                    elif button.text == "Toggle Sound":
                        self.settings["sound"] = not self.settings.get("sound", True)
                    elif button.text == "Change Snake Color":
                        self.selected_color_index = (self.selected_color_index + 1) % len(SNAKE_COLOR_PRESETS)
                        self.settings["snake_color"] = SNAKE_COLOR_PRESETS[self.selected_color_index]
                    elif button.text == "Save & Back":
                        save_settings(self.settings)
                        self.state = "menu"

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                try:
                    if self.state == "menu":
                        self.handle_menu_event(event)
                    elif self.state == "game":
                        self.handle_game_event(event)
                    elif self.state == "game_over":
                        self.handle_game_over_event(event)
                    elif self.state == "leaderboard":
                        self.handle_leaderboard_event(event)
                    elif self.state == "settings":
                        self.handle_settings_event(event)
                except SystemExit:
                    running = False

            if self.state == "game" and self.game:
                self.game.update()
                if self.game.game_over:
                    self.enter_game_over()

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "game" and self.game:
                self.game.draw(self.screen, (self.font, self.small_font, self.big_font))
            elif self.state == "game_over":
                self.draw_game_over()
            elif self.state == "leaderboard":
                self.draw_leaderboard()
            elif self.state == "settings":
                self.draw_settings()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    App().run()


if __name__ == "__main__":
    main()
