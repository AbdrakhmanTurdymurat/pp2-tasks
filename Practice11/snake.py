"""
=============================================================
  SNAKE GAME  –  Practice 11  (расширение Practice 8)
  Новые функции:
    • Еда с разными весами (очки) генерируется случайно
    • Еда исчезает через случайное время (таймер + визуальный индикатор)
    • Эффекты поедания (вспышка + частицы)
    • Полный игровой цикл: меню → игра → пауза → Game Over → рестарт
    • HUD: очки, длина, рекорд, легенда еды
=============================================================
  Зависимости:  pip install pygame
  Запуск:       python snake.py
=============================================================
"""

import pygame
import random
import math
import sys

# ─────────────────────────────────────────────────────────────
#  КОНСТАНТЫ
# ─────────────────────────────────────────────────────────────
CELL      = 28           # Размер одной клетки сетки
COLS      = 22           # Колонок игрового поля
ROWS      = 22           # Строк игрового поля
HUD_H     = 80           # Высота панели HUD (вверху)
WIN_W     = COLS * CELL
WIN_H     = ROWS * CELL + HUD_H
FPS       = 10           # Начальная скорость змейки (кадров/сек)
FPS_MAX   = 20           # Максимальная скорость

# Цветовая палитра
C_BG      = ( 18,  20,  30)
C_GRID    = ( 28,  30,  45)
C_HUD     = ( 22,  25,  40)
C_WHITE   = (255, 255, 255)
C_GRAY    = (120, 120, 140)
C_ACCENT  = ( 50, 230, 120)    # Зелёный (змейка)
C_HEAD    = ( 80, 255, 150)
C_DANGER  = (255,  70,  70)

# ─────────────────────────────────────────────────────────────
#  ТИПЫ ЕДЫ
#  (имя, цвет, очки, вес-вероятность, мин-тик, макс-тик)
#  тик = количество ходов змейки до исчезновения еды
# ─────────────────────────────────────────────────────────────
FOOD_TYPES = [
    ("apple",   (220,  60,  60),  1, 60, 20, 30),   # Обычное, 60% вероятность, долго
    ("orange",  (255, 165,   0),  3, 25, 12, 20),   # Среднее, 25%
    ("diamond", ( 80, 200, 255),  7, 10,  6, 12),   # Редкое, 10%, быстро исчезает
    ("star",    (255, 220,   0), 15,  5,  4,  8),   # Суперредкое, 5%, очень быстро
]

MAX_FOOD  = 4    # Максимально одновременно на поле

def lerp_color(c1, c2, t):
    """Линейная интерполяция двух цветов."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def weighted_food():
    """Выбирает тип еды по весу."""
    total = sum(f[3] for f in FOOD_TYPES)
    r = random.randint(1, total)
    acc = 0
    for f in FOOD_TYPES:
        acc += f[3]
        if r <= acc:
            return f
    return FOOD_TYPES[0]


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Частица (эффект съедания еды)
# ─────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, cx, cy, color):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 5)
        self.x  = float(cx)
        self.y  = float(cy)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = 1.0
        self.r = random.randint(2, 5)

    def update(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 0.15     # Гравитация
        self.life -= 0.05

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = int(self.life * 255)
        s = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.r, self.r), self.r)
        surf.blit(s, (int(self.x - self.r), int(self.y - self.r)))


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Еда
# ─────────────────────────────────────────────────────────────
class Food:
    def __init__(self, snake_cells, other_food_cells):
        """Создаёт еду в свободной клетке."""
        ft = weighted_food()
        self.name   = ft[0]
        self.color  = ft[1]
        self.points = ft[2]
        # Случайное время жизни (в тиках/ходах змейки)
        self.ttl     = random.randint(ft[4], ft[5])
        self.max_ttl = self.ttl

        # Найти свободную клетку
        occupied = set(snake_cells) | set(other_food_cells)
        all_cells = {(c, r) for c in range(COLS) for r in range(ROWS)}
        free = list(all_cells - occupied)
        self.cell = random.choice(free) if free else (0, 0)

        # Анимация пульсации
        self.pulse = random.uniform(0, math.pi * 2)

    def tick(self):
        """Уменьшает счётчик времени жизни. Возвращает True если пора исчезать."""
        self.ttl -= 1
        self.pulse += 0.15
        return self.ttl <= 0

    def draw(self, surf):
        """Рисует еду с пульсацией и таймер-кольцом."""
        px = self.cell[0] * CELL + CELL // 2
        py = self.cell[1] * CELL + CELL // 2 + HUD_H

        # Пульсация размера
        pulse_scale = 1.0 + 0.12 * math.sin(self.pulse)
        radius = int(CELL // 2 * 0.75 * pulse_scale)

        # Цвет мигает при низком TTL
        ratio = self.ttl / self.max_ttl
        draw_color = lerp_color(C_DANGER, self.color, ratio) if ratio < 0.35 else self.color

        # Тень
        shadow_s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(shadow_s, (0, 0, 0, 80), (radius + 2, radius + 4), radius)
        surf.blit(shadow_s, (px - radius - 2, py - radius - 2))

        # Иконка по типу
        if self.name == "apple":
            pygame.draw.circle(surf, draw_color, (px, py), radius)
        elif self.name == "orange":
            # Шестиугольник
            pts = [(px + radius * math.cos(math.pi / 2 + i * math.pi / 3),
                    py + radius * math.sin(math.pi / 2 + i * math.pi / 3)) for i in range(6)]
            pygame.draw.polygon(surf, draw_color, pts)
        elif self.name == "diamond":
            pts = [(px, py - radius), (px + radius, py), (px, py + radius), (px - radius, py)]
            pygame.draw.polygon(surf, draw_color, pts)
        elif self.name == "star":
            pts = []
            for i in range(10):
                r = radius if i % 2 == 0 else radius // 2
                angle = math.pi / 2 + i * math.pi / 5
                pts.append((px + r * math.cos(angle), py + r * math.sin(angle)))
            pygame.draw.polygon(surf, draw_color, pts)

        # Блик
        pygame.draw.circle(surf, C_WHITE, (px - radius // 3, py - radius // 3), max(2, radius // 5))

        # Таймер-кольцо (показывает оставшееся время)
        ring_r = radius + 4
        arc_angle = 2 * math.pi * (self.ttl / self.max_ttl)
        # Фон кольца
        ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
        # Нарисуем пунктиром через дуги
        steps = 20
        for i in range(steps):
            seg_start = -math.pi / 2 + (2 * math.pi * i / steps)
            seg_end   = seg_start + arc_angle / steps
            if i / steps < self.ttl / self.max_ttl:
                rc = lerp_color(C_DANGER, draw_color, i / steps)
                pygame.draw.arc(ring_surf, rc,
                                (2, 2, ring_r * 2, ring_r * 2),
                                seg_start, seg_start + 2 * math.pi / steps, 2)
        surf.blit(ring_surf, (px - ring_r - 2, py - ring_r - 2))


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Змейка
# ─────────────────────────────────────────────────────────────
class Snake:
    def __init__(self):
        # Начальное положение (центр поля, 3 сегмента)
        cx, cy = COLS // 2, ROWS // 2
        self.body = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction  = (1, 0)    # Движение вправо
        self.next_dir   = (1, 0)    # Следующее направление (буфер)
        self.grow       = False     # Флаг роста

    def set_direction(self, dx, dy):
        """Задаёт направление, если оно не противоположно текущему."""
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.next_dir = (dx, dy)

    def move(self):
        """
        Двигает змейку на один шаг.
        Возвращает (new_head, ate_tail)
        """
        self.direction = self.next_dir
        head = self.body[0]
        new_head = ((head[0] + self.direction[0]) % COLS,
                    (head[1] + self.direction[1]) % ROWS)   # Проход сквозь стену
        self.body.insert(0, new_head)
        if self.grow:
            self.grow = False    # Не убираем хвост → змейка растёт
        else:
            self.body.pop()
        return new_head

    def eat(self):
        """Помечает, что на следующем ходу змейка вырастет."""
        self.grow = True

    def collides_self(self):
        """Проверяет столкновение головы с телом."""
        return self.body[0] in self.body[1:]

    def cells(self):
        return list(self.body)

    def draw(self, surf):
        """Рисует змейку сегмент за сегментом."""
        n = len(self.body)
        for i, (cx, cy) in enumerate(self.body):
            px = cx * CELL + HUD_H // 2
            py = cy * CELL + HUD_H
            # Цвет: голова ярче, хвост темнее
            t = i / max(n - 1, 1)
            col = lerp_color(C_HEAD, (20, 80, 40), t)
            rect = pygame.Rect(px + 2, py + 2, CELL - 4, CELL - 4)
            pygame.draw.rect(surf, col, rect, border_radius=6)

            if i == 0:
                # Глаза головы
                # Направление → позиция глаз
                dx, dy = self.direction
                ex = px + CELL // 2 + dy * 5
                ey = py + CELL // 2 + dx * 5
                pygame.draw.circle(surf, C_WHITE, (ex - dy * 4, ey - dx * 4), 4)
                pygame.draw.circle(surf, C_WHITE, (ex + dy * 4, ey + dx * 4), 4)
                pygame.draw.circle(surf, (0, 0, 0), (ex - dy * 4, ey - dx * 4), 2)
                pygame.draw.circle(surf, (0, 0, 0), (ex + dy * 4, ey + dx * 4), 2)


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Кнопка
# ─────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, color=C_ACCENT):
        self.rect    = pygame.Rect(x, y, w, h)
        self.text    = text
        self.color   = color
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def update(self):
        self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, surf, font):
        col = lerp_color(self.color, C_WHITE, 0.25) if self.hovered else self.color
        s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*col, 230), (0, 0, self.rect.w, self.rect.h), border_radius=12)
        surf.blit(s, self.rect.topleft)
        pygame.draw.rect(surf, C_WHITE, self.rect, width=2, border_radius=12)
        txt = font.render(self.text, True, C_BG if self.hovered else C_WHITE)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


# ─────────────────────────────────────────────────────────────
#  ГЛАВНЫЙ КЛАСС: Игра Snake
# ─────────────────────────────────────────────────────────────
class SnakeGame:
    STATE_MENU     = "menu"
    STATE_PLAY     = "play"
    STATE_PAUSE    = "pause"
    STATE_GAMEOVER = "gameover"

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("🐍  SNAKE  –  Practice 11")
        self.clock = pygame.time.Clock()

        self.font_big   = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_med   = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)
        self.font_hud   = pygame.font.SysFont("Consolas", 22, bold=True)

        bx = WIN_W // 2 - 110
        self.btn_start   = Button(bx, 380, 220, 50, "▶  СТАРТ")
        self.btn_exit    = Button(bx, 445, 220, 50, "✕  ВЫХОД",  color=(180, 50, 50))
        self.btn_resume  = Button(bx, 340, 220, 50, "▶  ПРОДОЛЖИТЬ")
        self.btn_menu    = Button(bx, 405, 220, 50, "⟵  МЕНЮ",  color=C_GRAY)
        self.btn_restart = Button(bx, 430, 220, 50, "↺  РЕСТАРТ")
        self.btn_menu2   = Button(bx, 495, 220, 50, "⟵  МЕНЮ",  color=C_GRAY)

        self.highscore = 0
        self.state = self.STATE_MENU
        self._init_game()

    def _init_game(self):
        """Сбрасывает игровое состояние."""
        self.snake     = Snake()
        self.foods     = []         # Список объектов Food
        self.particles = []
        self.score     = 0
        self.ticks     = 0          # Общее число ходов змейки
        self.flash     = 0          # Вспышка при поедании (кадры)
        self._spawn_food()          # Создать начальную еду

    def _spawn_food(self):
        """Добавляет еду, если меньше MAX_FOOD."""
        snake_cells = self.snake.cells()
        food_cells  = [f.cell for f in self.foods]
        while len(self.foods) < MAX_FOOD:
            self.foods.append(Food(snake_cells, food_cells))
            food_cells = [f.cell for f in self.foods]

    def run(self):
        while True:
            self.clock.tick(FPS if self.state == self.STATE_PLAY else 60)
            self._handle_events()
            self._update()
            self._draw()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if self.state == self.STATE_MENU:
                if self.btn_start.handle_event(event):
                    self._init_game(); self.state = self.STATE_PLAY
                if self.btn_exit.handle_event(event):
                    pygame.quit(); sys.exit()

            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    k = event.key
                    if   k in (pygame.K_UP,    pygame.K_w): self.snake.set_direction(0, -1)
                    elif k in (pygame.K_DOWN,  pygame.K_s): self.snake.set_direction(0,  1)
                    elif k in (pygame.K_LEFT,  pygame.K_a): self.snake.set_direction(-1, 0)
                    elif k in (pygame.K_RIGHT, pygame.K_d): self.snake.set_direction(1,  0)
                    elif k == pygame.K_ESCAPE: self.state = self.STATE_PAUSE

            elif self.state == self.STATE_PAUSE:
                if self.btn_resume.handle_event(event):  self.state = self.STATE_PLAY
                if self.btn_menu.handle_event(event):    self.state = self.STATE_MENU

            elif self.state == self.STATE_GAMEOVER:
                if self.btn_restart.handle_event(event):
                    self._init_game(); self.state = self.STATE_PLAY
                if self.btn_menu2.handle_event(event):   self.state = self.STATE_MENU

    def _update(self):
        for btn in [self.btn_start, self.btn_exit, self.btn_resume,
                    self.btn_menu, self.btn_restart, self.btn_menu2]:
            btn.update()

        if self.state != self.STATE_PLAY:
            return

        self.ticks += 1

        # Движение змейки
        new_head = self.snake.move()

        # Проверка столкновения с собой → Game Over
        if self.snake.collides_self():
            self.highscore = max(self.highscore, self.score)
            self.state = self.STATE_GAMEOVER
            return

        # Проверка поедания еды
        eaten_idx = None
        for i, food in enumerate(self.foods):
            if food.cell == new_head:
                eaten_idx = i
                break

        if eaten_idx is not None:
            food = self.foods.pop(eaten_idx)
            self.score += food.points                          # Добавляем очки
            self.snake.eat()                                   # Растём
            self.flash = 6                                     # Вспышка экрана
            # Частицы
            px = food.cell[0] * CELL + CELL // 2
            py = food.cell[1] * CELL + CELL // 2 + HUD_H
            for _ in range(16):
                self.particles.append(Particle(px, py, food.color))

        # Тик еды: уменьшаем TTL каждые 2 хода змейки (чтобы не слишком быстро)
        if self.ticks % 2 == 0:
            self.foods = [f for f in self.foods if not f.tick()]   # Удаляем иссякшие

        # Восполняем количество еды
        self._spawn_food()

        # Обновление частиц
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        # Уменьшение вспышки
        if self.flash > 0:
            self.flash -= 1

    def _draw(self):
        self.screen.fill(C_BG)

        if self.state == self.STATE_MENU:
            self._draw_menu()
        elif self.state in (self.STATE_PLAY, self.STATE_PAUSE, self.STATE_GAMEOVER):
            self._draw_game()
            if self.state == self.STATE_PAUSE:
                self._draw_overlay("⏸  ПАУЗА", [self.btn_resume, self.btn_menu])
            elif self.state == self.STATE_GAMEOVER:
                self._draw_overlay("☠  КОНЕЦ!",  [self.btn_restart, self.btn_menu2])

        pygame.display.flip()

    def _draw_grid(self):
        """Рисует сетку игрового поля."""
        for c in range(COLS):
            for r in range(ROWS):
                rect = pygame.Rect(c * CELL, r * CELL + HUD_H, CELL, CELL)
                pygame.draw.rect(self.screen, C_GRID, rect, 1)

    def _draw_hud(self):
        """Рисует верхнюю панель HUD."""
        pygame.draw.rect(self.screen, C_HUD, (0, 0, WIN_W, HUD_H))
        pygame.draw.line(self.screen, C_ACCENT, (0, HUD_H), (WIN_W, HUD_H), 2)
        # Очки
        sc = self.font_hud.render(f"Очки: {self.score}", True, C_ACCENT)
        self.screen.blit(sc, (14, 14))
        # Длина змейки
        ln = self.font_small.render(f"Длина: {len(self.snake.body)}", True, C_WHITE)
        self.screen.blit(ln, (14, 46))
        # Рекорд
        hr = self.font_small.render(f"Рекорд: {self.highscore}", True, C_GRAY)
        self.screen.blit(hr, (WIN_W - hr.get_width() - 14, 14))
        # Легенда еды
        for i, (name, color, pts, *_) in enumerate(FOOD_TYPES):
            ix = WIN_W // 2 - 90 + i * 46
            pygame.draw.circle(self.screen, color, (ix, 28), 8)
            lt = self.font_small.render(f"+{pts}", True, color)
            self.screen.blit(lt, lt.get_rect(center=(ix, 52)))

    def _draw_game(self):
        """Отрисовка игровой сцены."""
        self._draw_grid()
        # Еда
        for food in self.foods:
            food.draw(self.screen)
        # Змейка
        self.snake.draw(self.screen)
        # Частицы
        for p in self.particles:
            p.draw(self.screen)
        # HUD
        self._draw_hud()
        # Вспышка при поедании
        if self.flash > 0:
            flash_surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, int(self.flash / 6 * 60)))
            self.screen.blit(flash_surf, (0, 0))

    def _draw_menu(self):
        """Рисует главное меню."""
        self._draw_grid()
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((18, 20, 30, 210))
        self.screen.blit(overlay, (0, 0))

        title = self.font_big.render("🐍  SNAKE", True, C_ACCENT)
        self.screen.blit(title, title.get_rect(center=(WIN_W // 2, 160)))
        sub = self.font_small.render("Ешь, расти и не врежься в себя!", True, C_GRAY)
        self.screen.blit(sub, sub.get_rect(center=(WIN_W // 2, 225)))

        # Легенда еды в меню
        legend_y = 270
        lbl = self.font_small.render("Типы еды:", True, C_WHITE)
        self.screen.blit(lbl, lbl.get_rect(center=(WIN_W // 2, legend_y)))
        for i, (name, color, pts, w, mn, mx) in enumerate(FOOD_TYPES):
            ix = WIN_W // 2 - 90 + i * 60
            pygame.draw.circle(self.screen, color, (ix, legend_y + 28), 10)
            t = self.font_small.render(f"+{pts}", True, color)
            self.screen.blit(t, t.get_rect(center=(ix, legend_y + 50)))
            d = self.font_small.render(f"{mn}-{mx}х", True, C_GRAY)
            self.screen.blit(d, d.get_rect(center=(ix, legend_y + 68)))

        self.btn_start.draw(self.screen, self.font_med)
        self.btn_exit.draw(self.screen,  self.font_med)

        ctrl = self.font_small.render("WASD / ↑↓←→ — управление  |  ESC — пауза", True, C_GRAY)
        self.screen.blit(ctrl, ctrl.get_rect(center=(WIN_W // 2, WIN_H - 20)))

    def _draw_overlay(self, title_text, buttons):
        """Рисует оверлей паузы/конца игры."""
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        self.screen.blit(ov, (0, 0))

        t = self.font_big.render(title_text, True, C_ACCENT)
        self.screen.blit(t, t.get_rect(center=(WIN_W // 2, WIN_H // 2 - 100)))

        if self.state == self.STATE_GAMEOVER:
            sc = self.font_med.render(f"Очки: {self.score}  |  Рекорд: {self.highscore}", True, (255, 215, 0))
            self.screen.blit(sc, sc.get_rect(center=(WIN_W // 2, WIN_H // 2 - 40)))

        for btn in buttons:
            btn.update()
            btn.draw(self.screen, self.font_med)


# ─────────────────────────────────────────────────────────────
#  ТОЧКА ВХОДА
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    game = SnakeGame()
    game.run()