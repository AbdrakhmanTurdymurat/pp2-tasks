"""
=============================================================
  RACER GAME  –  Practice 11  (расширение Practice 8)
  Новые функции:
    • Монеты с разным весом (очки) появляются случайно на дороге
    • Скорость врага увеличивается каждые N собранных монет
    • Полный игровой цикл: меню → игра → пауза → Game Over → рестарт
    • Эффекты частиц при сборе монеты
    • HUD: очки, скорость, прогресс до следующего уровня
=============================================================
  Зависимости:  pip install pygame
  Запуск:       python racer.py
=============================================================
"""

import pygame
import random
import math
import sys

# ─────────────────────────────────────────────────────────────
#  КОНСТАНТЫ
# ─────────────────────────────────────────────────────────────
WIN_W, WIN_H = 600, 800          # Размер окна
FPS          = 60                # Частота обновления

# Цветовая палитра
C_BG         = (15,  17,  26)    # Фон (тёмно-синий)
C_ROAD       = (30,  34,  50)    # Дорога
C_LANE       = (60,  65,  90)    # Разметка полос
C_ACCENT     = (0,  200, 255)    # Акцентный (голубой)
C_DANGER     = (255,  70,  70)   # Опасность (красный)
C_GOLD       = (255, 215,   0)   # Золотая монета
C_SILVER     = (192, 192, 192)   # Серебряная монета
C_BRONZE     = (205, 127,  50)   # Бронзовая монета
C_WHITE      = (255, 255, 255)
C_GRAY       = (120, 120, 140)
C_GREEN      = ( 50, 230, 100)

# Дорога
ROAD_LEFT    = 100               # Левый край дороги
ROAD_RIGHT   = 500               # Правый край
ROAD_W       = ROAD_RIGHT - ROAD_LEFT   # 400 px

# Полосы (3 полосы)
LANES        = [ROAD_LEFT + ROAD_W // 6 * (i * 2 + 1) for i in range(3)]
# LANES ≈ [167, 300, 433]

# Настройки монет
COINS_PER_SPEEDUP = 10           # Монет для увеличения скорости врага
ENEMY_SPEED_INCREMENT = 0.5      # Прирост скорости врага
BASE_ENEMY_SPEED      = 4.0      # Начальная скорость врага
COIN_SPAWN_INTERVAL   = 90       # Кадров между появлением монет (≈1.5 с)

# Типы монет: (название, цвет, очки, вес-вероятность)
COIN_TYPES = [
    ("bronze", C_BRONZE, 1,  60),   # обычная, часто
    ("silver", C_SILVER, 3,  30),   # редкая
    ("gold",   C_GOLD,   7,  10),   # очень редкая
]


# ─────────────────────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────────
def weighted_choice(items):
    """Выбирает элемент из списка (name, color, pts, weight) с учётом весов."""
    total = sum(it[3] for it in items)
    r = random.randint(1, total)
    cumulative = 0
    for it in items:
        cumulative += it[3]
        if r <= cumulative:
            return it
    return items[-1]


def draw_rounded_rect(surf, color, rect, radius=10, alpha=255):
    """Рисует прямоугольник со скруглёнными углами (с поддержкой прозрачности)."""
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
    surf.blit(s, (rect[0], rect[1]))


def lerp_color(c1, c2, t):
    """Линейная интерполяция цвета."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Частица (эффект при сборе монеты)
# ─────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 4)
        self.vx = math.cos(angle) * speed    # Скорость по X
        self.vy = math.sin(angle) * speed    # Скорость по Y
        self.life = 1.0                       # Время жизни (1.0 → 0.0)
        self.radius = random.randint(2, 5)

    def update(self):
        """Обновляет позицию и время жизни частицы."""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1          # Гравитация
        self.life -= 0.04       # Угасание

    def draw(self, surf):
        """Рисует частицу с затуханием прозрачности."""
        if self.life <= 0:
            return
        alpha = int(self.life * 255)
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.radius, self.radius), self.radius)
        surf.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Монета
# ─────────────────────────────────────────────────────────────
class Coin:
    RADIUS = 14

    def __init__(self, road_speed):
        coin_type = weighted_choice(COIN_TYPES)  # Выбор по весу
        self.name   = coin_type[0]
        self.color  = coin_type[1]
        self.points = coin_type[2]

        lane = random.choice(LANES)               # Случайная полоса
        self.x = lane
        self.y = -self.RADIUS                     # Появляется выше экрана
        self.speed = road_speed                   # Движется вместе с дорогой
        self.angle = 0                            # Угол вращения (анимация)
        self.collected = False

    def update(self):
        """Движение монеты вниз + анимация вращения."""
        self.y += self.speed
        self.angle = (self.angle + 3) % 360

    def draw(self, surf):
        """Рисует монету с блеском и тенью."""
        if self.collected:
            return
        # Тень
        pygame.draw.circle(surf, (0, 0, 0, 80), (int(self.x) + 3, int(self.y) + 3), self.RADIUS)
        # Основной круг
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.RADIUS)
        # Блик (эффект 3D)
        highlight_x = int(self.x - self.RADIUS * 0.3)
        highlight_y = int(self.y - self.RADIUS * 0.3)
        pygame.draw.circle(surf, C_WHITE, (highlight_x, highlight_y), self.RADIUS // 3)
        # Буква на монете
        label = {"bronze": "B", "silver": "S", "gold": "G"}[self.name]
        font = pygame.font.SysFont("Arial", 11, bold=True)
        txt = font.render(label, True, (30, 30, 30))
        surf.blit(txt, txt.get_rect(center=(int(self.x), int(self.y))))

    def is_off_screen(self):
        return self.y > WIN_H + self.RADIUS

    def get_rect(self):
        r = self.RADIUS
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Машина (игрок)
# ─────────────────────────────────────────────────────────────
class PlayerCar:
    W, H = 50, 80

    def __init__(self):
        self.lane_idx = 1                         # Начальная полоса (центр)
        self.x = float(LANES[self.lane_idx])
        self.y = float(WIN_H - 140)
        self.target_x = self.x
        self.speed_x = 12                         # Скорость переключения полос
        self.invincible = 0                       # Кадры неуязвимости

    def move_left(self):
        """Перемещение на левую полосу."""
        if self.lane_idx > 0:
            self.lane_idx -= 1
            self.target_x = LANES[self.lane_idx]

    def move_right(self):
        """Перемещение на правую полосу."""
        if self.lane_idx < 2:
            self.lane_idx += 1
            self.target_x = LANES[self.lane_idx]

    def update(self):
        """Плавное движение к целевой позиции и уменьшение кадров неуязвимости."""
        dx = self.target_x - self.x
        if abs(dx) > 1:
            self.x += dx * 0.25    # Интерполяция для плавности
        else:
            self.x = self.target_x
        if self.invincible > 0:
            self.invincible -= 1

    def draw(self, surf):
        """Рисует машину игрока (мигание при неуязвимости)."""
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            return     # Мигание
        cx, cy = int(self.x), int(self.y)
        # Кузов
        body_rect = pygame.Rect(cx - self.W // 2, cy - self.H // 2, self.W, self.H)
        pygame.draw.rect(surf, C_ACCENT, body_rect, border_radius=10)
        # Капот / крыша
        roof_rect = pygame.Rect(cx - 16, cy - 30, 32, 26)
        pygame.draw.rect(surf, lerp_color(C_ACCENT, C_WHITE, 0.3), roof_rect, border_radius=6)
        # Фары
        pygame.draw.circle(surf, (255, 255, 200), (cx - 16, cy - self.H // 2 + 8), 6)
        pygame.draw.circle(surf, (255, 255, 200), (cx + 16, cy - self.H // 2 + 8), 6)
        # Колёса
        for wx, wy in [(-28, -25), (28, -25), (-28, 25), (28, 25)]:
            pygame.draw.rect(surf, (20, 20, 20),
                             pygame.Rect(cx + wx - 7, cy + wy - 10, 14, 20), border_radius=4)

    def get_rect(self):
        return pygame.Rect(int(self.x) - self.W // 2, int(self.y) - self.H // 2,
                           self.W, self.H)


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Вражеская машина
# ─────────────────────────────────────────────────────────────
class EnemyCar:
    W, H = 50, 80
    COLORS = [(255, 80, 80), (255, 140, 0), (160, 50, 255), (50, 220, 120)]

    def __init__(self, speed):
        self.lane_idx = random.randint(0, 2)
        self.x = float(LANES[self.lane_idx])
        self.y = float(-self.H)
        self.speed = speed                         # Текущая скорость (растёт)
        self.color = random.choice(self.COLORS)

    def update(self):
        """Движение врага вниз по экрану."""
        self.y += self.speed

    def draw(self, surf):
        """Рисует вражескую машину."""
        cx, cy = int(self.x), int(self.y)
        body = pygame.Rect(cx - self.W // 2, cy - self.H // 2, self.W, self.H)
        pygame.draw.rect(surf, self.color, body, border_radius=10)
        roof = pygame.Rect(cx - 16, cy - 24, 32, 22)
        pygame.draw.rect(surf, lerp_color(self.color, (30, 30, 30), 0.4), roof, border_radius=6)
        # Фары (красные сзади)
        pygame.draw.circle(surf, C_DANGER, (cx - 16, cy + self.H // 2 - 8), 6)
        pygame.draw.circle(surf, C_DANGER, (cx + 16, cy + self.H // 2 - 8), 6)
        # Колёса
        for wx, wy in [(-28, -25), (28, -25), (-28, 25), (28, 25)]:
            pygame.draw.rect(surf, (20, 20, 20),
                             pygame.Rect(cx + wx - 7, cy + wy - 10, 14, 20), border_radius=4)

    def is_off_screen(self):
        return self.y > WIN_H + self.H

    def get_rect(self):
        return pygame.Rect(int(self.x) - self.W // 2, int(self.y) - self.H // 2,
                           self.W, self.H)


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Дорога (полосы с анимацией)
# ─────────────────────────────────────────────────────────────
class Road:
    DASH_H   = 60    # Высота пунктира
    DASH_GAP = 40    # Промежуток
    STEP     = DASH_H + DASH_GAP

    def __init__(self):
        self.offset = 0.0     # Смещение разметки (анимация движения)

    def update(self, speed):
        """Прокручивает разметку дороги."""
        self.offset = (self.offset + speed) % self.STEP

    def draw(self, surf):
        """Рисует дорогу, обочины и пунктирную разметку."""
        # Фон дороги
        pygame.draw.rect(surf, C_ROAD, (ROAD_LEFT, 0, ROAD_W, WIN_H))
        # Обочины
        pygame.draw.rect(surf, (40, 42, 60), (ROAD_LEFT - 20, 0, 20, WIN_H))
        pygame.draw.rect(surf, (40, 42, 60), (ROAD_RIGHT,     0, 20, WIN_H))
        # Пунктирные линии между полосами
        for lx in [ROAD_LEFT + ROAD_W // 3, ROAD_LEFT + ROAD_W * 2 // 3]:
            y = -self.STEP + self.offset
            while y < WIN_H:
                pygame.draw.rect(surf, C_LANE, (lx - 2, int(y), 4, self.DASH_H),
                                 border_radius=2)
                y += self.STEP
        # Сплошные края дороги
        pygame.draw.rect(surf, (255, 220, 50), (ROAD_LEFT - 4,  0, 4, WIN_H))
        pygame.draw.rect(surf, (255, 220, 50), (ROAD_RIGHT,     0, 4, WIN_H))


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Кнопка (для меню)
# ─────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, color=C_ACCENT):
        self.rect   = pygame.Rect(x, y, w, h)
        self.text   = text
        self.color  = color
        self.hovered = False

    def handle_event(self, event):
        """Возвращает True при нажатии."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def update(self):
        self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, surf, font):
        """Рисует кнопку с hover-эффектом."""
        col = lerp_color(self.color, C_WHITE, 0.2) if self.hovered else self.color
        draw_rounded_rect(surf, col, self.rect, radius=12)
        # Обводка
        pygame.draw.rect(surf, C_WHITE, self.rect, width=2, border_radius=12)
        txt = font.render(self.text, True, C_BG if self.hovered else C_WHITE)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


# ─────────────────────────────────────────────────────────────
#  ГЛАВНЫЙ КЛАСС: Игра
# ─────────────────────────────────────────────────────────────
class RacerGame:
    # Состояния игры
    STATE_MENU    = "menu"
    STATE_PLAY    = "play"
    STATE_PAUSE   = "pause"
    STATE_GAMEOVER= "gameover"

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        pygame.display.set_caption("🏎  RACER  –  Practice 11")
        self.clock = pygame.time.Clock()

        # Шрифты
        self.font_big   = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_med   = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)
        self.font_hud   = pygame.font.SysFont("Consolas", 22, bold=True)

        # Кнопки меню
        bx, bw, bh = WIN_W // 2 - 110, 220, 54
        self.btn_start  = Button(bx, 360, bw, bh, "▶  СТАРТ")
        self.btn_exit   = Button(bx, 430, bw, bh, "✕  ВЫХОД", color=(180, 50, 50))
        self.btn_resume = Button(bx, 350, bw, bh, "▶  ПРОДОЛЖИТЬ")
        self.btn_menu   = Button(bx, 420, bw, bh, "⟵  МЕНЮ",  color=C_GRAY)
        self.btn_restart= Button(bx, 420, bw, bh, "↺  РЕСТАРТ")
        self.btn_menu2  = Button(bx, 490, bw, bh, "⟵  МЕНЮ",  color=C_GRAY)

        self.state = self.STATE_MENU
        self._init_game()

    # ── Инициализация игровых переменных ──────────────────────
    def _init_game(self):
        """Сбрасывает все игровые объекты к начальным значениям."""
        self.road        = Road()
        self.player      = PlayerCar()
        self.enemies     = []
        self.coins       = []
        self.particles   = []

        self.score       = 0         # Общие очки
        self.coins_total = 0         # Всего собрано монет
        self.road_speed  = 5.0       # Скорость прокрутки дороги
        self.enemy_speed = BASE_ENEMY_SPEED

        # Таймеры появления объектов
        self.enemy_timer = 0
        self.coin_timer  = 0

        # Уровень (сколько раз ускорялся враг)
        self.level       = 1
        # Монет до следующего ускорения
        self.coins_to_next = COINS_PER_SPEEDUP

        # Флаг: показывать уведомление об ускорении
        self.speedup_flash = 0

    # ── Главный игровой цикл ─────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()

    # ── Обработка событий ────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.state == self.STATE_MENU:
                if self.btn_start.handle_event(event):
                    self._init_game()
                    self.state = self.STATE_PLAY
                if self.btn_exit.handle_event(event):
                    pygame.quit()
                    sys.exit()

            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.player.move_left()
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.player.move_right()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = self.STATE_PAUSE

            elif self.state == self.STATE_PAUSE:
                if self.btn_resume.handle_event(event):
                    self.state = self.STATE_PLAY
                if self.btn_menu.handle_event(event):
                    self.state = self.STATE_MENU

            elif self.state == self.STATE_GAMEOVER:
                if self.btn_restart.handle_event(event):
                    self._init_game()
                    self.state = self.STATE_PLAY
                if self.btn_menu2.handle_event(event):
                    self.state = self.STATE_MENU

    # ── Логика обновления ────────────────────────────────────
    def _update(self):
        if self.state != self.STATE_PLAY:
            # Обновление hover-эффектов кнопок в нужном состоянии
            for btn in [self.btn_start, self.btn_exit, self.btn_resume,
                        self.btn_menu, self.btn_restart, self.btn_menu2]:
                btn.update()
            return

        # Обновление дороги
        self.road.update(self.road_speed)

        # Обновление игрока
        self.player.update()

        # Таймер появления врагов (интервал уменьшается с ростом скорости)
        self.enemy_timer += 1
        spawn_interval = max(40, int(80 - self.level * 3))
        if self.enemy_timer >= spawn_interval:
            self.enemies.append(EnemyCar(self.enemy_speed))
            self.enemy_timer = 0

        # Таймер появления монет
        self.coin_timer += 1
        if self.coin_timer >= COIN_SPAWN_INTERVAL:
            self.coins.append(Coin(self.road_speed))
            self.coin_timer = 0

        # Обновление врагов + проверка столкновений с игроком
        player_rect = self.player.get_rect()
        for enemy in self.enemies:
            enemy.update()
            if self.player.invincible == 0 and player_rect.colliderect(enemy.get_rect()):
                # Столкновение → Game Over
                self.state = self.STATE_GAMEOVER
                return
        self.enemies = [e for e in self.enemies if not e.is_off_screen()]

        # Обновление монет + проверка сбора
        for coin in self.coins:
            coin.update()
            if not coin.collected and player_rect.colliderect(coin.get_rect()):
                coin.collected = True
                self.score       += coin.points       # Добавляем очки
                self.coins_total += 1                 # Считаем монеты
                self._spawn_particles(coin.x, coin.y, coin.color)
                self._check_speedup()                 # Проверяем ускорение

        self.coins = [c for c in self.coins if not c.is_off_screen() and not c.collected]

        # Обновление частиц
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        # Уменьшение таймера уведомления
        if self.speedup_flash > 0:
            self.speedup_flash -= 1

        # Постепенное ускорение дороги со временем
        self.road_speed = 5.0 + self.level * 0.3

    def _spawn_particles(self, x, y, color):
        """Создаёт взрыв частиц при сборе монеты."""
        for _ in range(12):
            self.particles.append(Particle(x, y, color))

    def _check_speedup(self):
        """Проверяет, нужно ли увеличить скорость врага."""
        self.coins_to_next -= 1
        if self.coins_to_next <= 0:
            self.level        += 1
            self.enemy_speed  += ENEMY_SPEED_INCREMENT   # Ускоряем врага!
            self.coins_to_next = COINS_PER_SPEEDUP
            self.speedup_flash = 90                      # Показываем уведомление 1.5 с
            # Ускоряем уже существующих врагов
            for e in self.enemies:
                e.speed = self.enemy_speed

    # ── Отрисовка ────────────────────────────────────────────
    def _draw(self):
        self.screen.fill(C_BG)

        if self.state == self.STATE_MENU:
            self._draw_menu()
        elif self.state == self.STATE_PLAY:
            self._draw_game()
        elif self.state == self.STATE_PAUSE:
            self._draw_game()
            self._draw_overlay("⏸  ПАУЗА", [(self.btn_resume,), (self.btn_menu,)])
        elif self.state == self.STATE_GAMEOVER:
            self._draw_game()
            self._draw_overlay("💥  АВАРИЯ!", [(self.btn_restart,), (self.btn_menu2,)])

        pygame.display.flip()

    def _draw_menu(self):
        """Рисует главное меню."""
        # Анимированный фон-дорога
        self.road.update(3)
        self.road.draw(self.screen)

        # Полупрозрачный оверлей
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((15, 17, 26, 200))
        self.screen.blit(overlay, (0, 0))

        # Заголовок
        title = self.font_big.render("🏎  RACER", True, C_ACCENT)
        self.screen.blit(title, title.get_rect(center=(WIN_W // 2, 200)))
        sub = self.font_small.render("Собирай монеты · Избегай врагов · Побей рекорд", True, C_GRAY)
        self.screen.blit(sub, sub.get_rect(center=(WIN_W // 2, 265)))

        # Легенда монет
        legend_y = 300
        for i, (name, color, pts, _) in enumerate(COIN_TYPES):
            pygame.draw.circle(self.screen, color, (WIN_W // 2 - 80 + i * 80, legend_y), 10)
            lbl = self.font_small.render(f"{pts} очк.", True, C_WHITE)
            self.screen.blit(lbl, lbl.get_rect(center=(WIN_W // 2 - 80 + i * 80, legend_y + 22)))

        self.btn_start.draw(self.screen, self.font_med)
        self.btn_exit.draw(self.screen,  self.font_med)

        ctrl = self.font_small.render("← → или A D — смена полосы  |  ESC — пауза", True, C_GRAY)
        self.screen.blit(ctrl, ctrl.get_rect(center=(WIN_W // 2, WIN_H - 30)))

    def _draw_game(self):
        """Рисует игровую сцену."""
        self.road.draw(self.screen)
        # Монеты
        for coin in self.coins:
            coin.draw(self.screen)
        # Враги
        for enemy in self.enemies:
            enemy.draw(self.screen)
        # Игрок
        self.player.draw(self.screen)
        # Частицы
        for p in self.particles:
            p.draw(self.screen)
        # HUD
        self._draw_hud()

    def _draw_hud(self):
        """Рисует интерфейс (очки, уровень, прогресс)."""
        # Панель очков
        draw_rounded_rect(self.screen, (25, 28, 45), (10, 10, 200, 90), radius=10, alpha=200)
        score_txt = self.font_hud.render(f"Очки: {self.score}", True, C_ACCENT)
        self.screen.blit(score_txt, (20, 18))
        coins_txt = self.font_small.render(f"Монет: {self.coins_total}", True, C_GOLD)
        self.screen.blit(coins_txt, (20, 48))
        lvl_txt = self.font_small.render(f"Уровень: {self.level}", True, C_WHITE)
        self.screen.blit(lvl_txt, (20, 72))

        # Прогресс-бар до следующего ускорения
        bar_x, bar_y, bar_w, bar_h = 10, 108, 200, 12
        draw_rounded_rect(self.screen, (40, 43, 65), (bar_x, bar_y, bar_w, bar_h), radius=6)
        progress = 1 - (self.coins_to_next / COINS_PER_SPEEDUP)
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            draw_rounded_rect(self.screen, C_DANGER, (bar_x, bar_y, fill_w, bar_h), radius=6)
        hint = self.font_small.render(f"До ускорения: {self.coins_to_next}", True, C_GRAY)
        self.screen.blit(hint, (bar_x, bar_y + 16))

        # Скорость врага
        spd_txt = self.font_small.render(f"Враг ×{self.enemy_speed:.1f}", True, C_DANGER)
        self.screen.blit(spd_txt, (WIN_W - 150, 10))

        # Уведомление об ускорении
        if self.speedup_flash > 0:
            alpha = min(255, self.speedup_flash * 4)
            msg = self.font_med.render("⚡ ВРАГ УСКОРИЛСЯ!", True, C_DANGER)
            s = pygame.Surface(msg.get_size(), pygame.SRCALPHA)
            s.blit(msg, (0, 0))
            s.set_alpha(alpha)
            self.screen.blit(s, s.get_rect(center=(WIN_W // 2, WIN_H // 2 - 80)))

    def _draw_overlay(self, title_text, button_rows):
        """Рисует полупрозрачный оверлей (пауза / game over)."""
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        title = self.font_big.render(title_text, True, C_ACCENT)
        self.screen.blit(title, title.get_rect(center=(WIN_W // 2, 260)))

        if self.state == self.STATE_GAMEOVER:
            sc = self.font_med.render(f"Очки: {self.score}  |  Монет: {self.coins_total}", True, C_GOLD)
            self.screen.blit(sc, sc.get_rect(center=(WIN_W // 2, 330)))

        for row in button_rows:
            for btn in row:
                btn.update()
                btn.draw(self.screen, self.font_med)


# ─────────────────────────────────────────────────────────────
#  ТОЧКА ВХОДА
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    game = RacerGame()
    game.run()