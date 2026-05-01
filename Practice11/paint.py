"""
=============================================================
  PAINT  –  Practice 11  (расширение Practice 8)
  Новые инструменты:
    • Квадрат         (Square)
    • Прямоугольный треугольник  (Right Triangle)
    • Равносторонний треугольник (Equilateral Triangle)
    • Ромб            (Rhombus)
  Остальные инструменты:
    • Карандаш (Pencil) — свободное рисование
    • Линия (Line)
    • Прямоугольник (Rectangle)
    • Круг (Circle / Ellipse)
    • Заливка (Fill / Bucket)
    • Ластик (Eraser)
  Дополнительно:
    • Цветовая палитра (24 цвета + пользовательский ввод)
    • Размер кисти / толщина
    • Заливка фигур (filled / outline)
    • Undo (Ctrl+Z), Redo (Ctrl+Y)
    • Очистить холст
    • Сохранить PNG (Ctrl+S)
    • Современный UI: тёмная тема, иконки, hover-эффекты
=============================================================
  Зависимости:  pip install pygame
  Запуск:       python paint.py
=============================================================
"""

import pygame
import math
import sys
import os
from copy import deepcopy

pygame.init()

# ─────────────────────────────────────────────────────────────
#  КОНСТАНТЫ
# ─────────────────────────────────────────────────────────────
WIN_W, WIN_H  = 1100, 750       # Размер окна
TOOLBAR_W     = 220              # Ширина левой панели инструментов
CANVAS_X      = TOOLBAR_W       # Начало холста по X
CANVAS_Y      = 0
CANVAS_W      = WIN_W - TOOLBAR_W
CANVAS_H      = WIN_H

# Цветовая палитра приложения (UI)
C_BG          = ( 18,  20,  30)   # Фон панели
C_PANEL       = ( 25,  28,  42)   # Фон кнопок
C_BORDER      = ( 45,  50,  75)   # Обводки
C_ACCENT      = ( 80, 160, 255)   # Акцентный синий
C_WHITE       = (255, 255, 255)
C_GRAY        = (100, 110, 135)
C_CANVAS_BG   = (240, 242, 248)   # Фон холста (светло-серый)
C_HOVER       = ( 40,  45,  65)   # Hover кнопки
C_SELECTED    = ( 50,  90, 170)   # Выбранный инструмент

# 24 стандартных цвета палитры (6 колонок × 4 строки)
PALETTE = [
    (  0,   0,   0), ( 64,  64,  64), (128, 128, 128), (192, 192, 192), (224, 224, 224), (255, 255, 255),
    (128,   0,   0), (255,   0,   0), (255, 128,   0), (255, 200,   0), (255, 255,   0), (128, 255,   0),
    (  0, 128,   0), (  0, 200,  80), (  0, 200, 200), (  0, 128, 255), (  0,   0, 255), (100,   0, 200),
    (180,   0, 255), (255,   0, 180), (255, 128, 200), (160,  82,  45), (210, 170, 120), (255, 215,   0),
]

# Максимальный размер стека Undo
UNDO_LIMIT = 30

# ─────────────────────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────────
def lerp_color(c1, c2, t):
    """Линейная интерполяция двух цветов (для hover-эффектов)."""
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_rounded_rect(surf, color, rect, radius=8, border=0, border_color=None):
    """Рисует прямоугольник со скруглёнными углами."""
    x, y, w, h = rect
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, width=border, border_radius=radius)


def canvas_pos(mx, my):
    """Преобразует координаты мыши в координаты холста."""
    return mx - CANVAS_X, my - CANVAS_Y


def point_in_canvas(mx, my):
    """Проверяет, находится ли точка в пределах холста."""
    return CANVAS_X <= mx < WIN_W and 0 <= my < WIN_H


# ─────────────────────────────────────────────────────────────
#  МАТЕМАТИКА ДЛЯ ФИГУР
# ─────────────────────────────────────────────────────────────
def make_square_pts(x1, y1, x2, y2):
    """
    Возвращает 4 вершины квадрата по двум углам.
    Сторона = min(|dx|, |dy|), сохраняется направление мыши.
    """
    dx = x2 - x1
    dy = y2 - y1
    side = min(abs(dx), abs(dy))
    sx   = math.copysign(side, dx)
    sy   = math.copysign(side, dy)
    return [(x1, y1), (x1 + sx, y1), (x1 + sx, y1 + sy), (x1, y1 + sy)]


def make_right_triangle_pts(x1, y1, x2, y2):
    """
    Прямоугольный треугольник:
      • прямой угол в точке (x1, y2)
      • гипотенуза от (x1, y1) до (x2, y2)
    """
    return [(x1, y1), (x2, y2), (x1, y2)]


def make_equilateral_pts(x1, y1, x2, y2):
    """
    Равносторонний треугольник:
      Основание от (x1,y2) до (x2,y2), вершина на высоте h = √3/2 * сторона.
    """
    base_len = abs(x2 - x1)
    h        = base_len * math.sqrt(3) / 2
    cx       = (x1 + x2) / 2
    # Вершина выше или ниже в зависимости от направления перетаскивания
    direction = -1 if y2 <= y1 else 1
    apex_y    = y2 - direction * h
    return [(x1, y2), (x2, y2), (cx, apex_y)]


def make_rhombus_pts(x1, y1, x2, y2):
    """
    Ромб: описывается bounding box (x1,y1)→(x2,y2).
    Вершины — середины сторон bounding box.
    """
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    return [(mx, y1), (x2, my), (mx, y2), (x1, my)]


# ─────────────────────────────────────────────────────────────
#  FLOOD FILL (заливка)
# ─────────────────────────────────────────────────────────────
def flood_fill(surface, cx, cy, fill_color):
    """
    Итеративный алгоритм заливки (scanline flood fill).
    Заполняет область одного цвета начиная с (cx, cy).
    """
    if not (0 <= cx < surface.get_width() and 0 <= cy < surface.get_height()):
        return
    target_color = surface.get_at((cx, cy))[:3]
    if target_color == fill_color[:3]:
        return

    # Используем стек вместо рекурсии (избегаем stack overflow)
    stack = [(cx, cy)]
    w, h  = surface.get_width(), surface.get_height()
    visited = set()

    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue
        if not (0 <= x < w and 0 <= y < h):
            continue
        if surface.get_at((x, y))[:3] != target_color:
            continue
        visited.add((x, y))
        surface.set_at((x, y), fill_color)
        stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Кнопка инструмента
# ─────────────────────────────────────────────────────────────
class ToolButton:
    H = 40    # Высота кнопки

    def __init__(self, x, y, w, tool_id, label, icon=None):
        self.rect    = pygame.Rect(x, y, w, self.H)
        self.tool_id = tool_id     # Строковый идентификатор инструмента
        self.label   = label       # Текст на кнопке
        self.icon    = icon        # Символ-иконка (юникод)
        self.hovered = False

    def handle_event(self, event):
        """Возвращает tool_id при клике."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.tool_id
        return None

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surf, font, selected):
        """Рисует кнопку: подсветка если выбрана или hovered."""
        if selected:
            bg = C_SELECTED
        elif self.hovered:
            bg = C_HOVER
        else:
            bg = C_PANEL
        draw_rounded_rect(surf, bg, self.rect, radius=8,
                          border=1, border_color=C_BORDER)
        # Иконка + текст
        label_text = (self.icon + "  " if self.icon else "") + self.label
        txt = font.render(label_text, True, C_WHITE if selected or self.hovered else C_GRAY)
        surf.blit(txt, txt.get_rect(midleft=(self.rect.x + 12, self.rect.centery)))


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Ползунок (размер кисти)
# ─────────────────────────────────────────────────────────────
class Slider:
    def __init__(self, x, y, w, min_val=1, max_val=40, value=4):
        self.rect    = pygame.Rect(x, y, w, 6)
        self.min_val = min_val
        self.max_val = max_val
        self.value   = value
        self.dragging = False

    def handle_event(self, event):
        """Обрабатывает перетаскивание ползунка."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle = self._handle_rect()
            if handle.collidepoint(event.pos):
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            t = (event.pos[0] - self.rect.x) / self.rect.w
            t = max(0.0, min(1.0, t))
            self.value = int(self.min_val + t * (self.max_val - self.min_val))

    def _handle_rect(self):
        """Возвращает rect ручки ползунка."""
        t  = (self.value - self.min_val) / (self.max_val - self.min_val)
        hx = int(self.rect.x + t * self.rect.w)
        return pygame.Rect(hx - 8, self.rect.y - 7, 16, 20)

    def draw(self, surf, font):
        """Рисует дорожку и ручку ползунка."""
        # Дорожка
        draw_rounded_rect(surf, C_BORDER, self.rect, radius=3)
        # Заполненная часть
        t  = (self.value - self.min_val) / (self.max_val - self.min_val)
        fw = max(3, int(self.rect.w * t))
        draw_rounded_rect(surf, C_ACCENT, (self.rect.x, self.rect.y, fw, 6), radius=3)
        # Ручка
        h = self._handle_rect()
        draw_rounded_rect(surf, C_WHITE, h, radius=5)
        # Значение
        val_txt = font.render(str(self.value), True, C_GRAY)
        surf.blit(val_txt, (self.rect.right + 8, self.rect.y - 4))


# ─────────────────────────────────────────────────────────────
#  КЛАСС: Ячейка палитры
# ─────────────────────────────────────────────────────────────
class ColorSwatch:
    SIZE = 26

    def __init__(self, x, y, color):
        self.rect  = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.color = color

    def handle_event(self, event):
        """Возвращает цвет при клике."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 1:
                    return ("primary", self.color)
                if event.button == 3:
                    return ("secondary", self.color)
        return None

    def draw(self, surf, primary, secondary):
        """Рисует ячейку цвета с маркером выбора."""
        pygame.draw.rect(surf, self.color, self.rect, border_radius=4)
        # Маркер основного цвета (внутренний белый кант)
        if self.color == primary:
            pygame.draw.rect(surf, C_WHITE, self.rect, width=2, border_radius=4)
        elif self.color == secondary:
            pygame.draw.rect(surf, C_GRAY,  self.rect, width=2, border_radius=4)
        else:
            pygame.draw.rect(surf, C_BORDER, self.rect, width=1, border_radius=4)


# ─────────────────────────────────────────────────────────────
#  ГЛАВНЫЙ КЛАСС: Приложение Paint
# ─────────────────────────────────────────────────────────────
class PaintApp:

    # Список всех инструментов (id, метка, иконка)
    TOOLS = [
        ("pencil",      "Карандаш",     "✏"),
        ("line",        "Линия",        "╱"),
        ("rect",        "Прямоугольник","▭"),
        ("square",      "Квадрат",      "■"),
        ("circle",      "Эллипс",       "◯"),
        ("right_tri",   "Пр. треуг.",   "◺"),
        ("eq_tri",      "Равн. треуг.", "△"),
        ("rhombus",     "Ромб",         "◇"),
        ("fill",        "Заливка",      "🪣"),
        ("eraser",      "Ластик",       "◻"),
    ]

    def __init__(self):
        self.screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        pygame.display.set_caption("🎨  PAINT  –  Practice 11")
        self.clock = pygame.time.Clock()

        # Шрифты
        self.font_bold  = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 12)
        self.font_med   = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI", 16, bold=True)

        # Холст (отдельная поверхность)
        self.canvas = pygame.Surface((CANVAS_W, CANVAS_H))
        self.canvas.fill(C_CANVAS_BG)

        # Стек отмены / повтора
        self.undo_stack = []          # Стек состояний холста для Undo
        self.redo_stack = []          # Стек состояний холста для Redo
        self._save_undo()             # Сохраняем начальное пустое состояние

        # Текущее состояние
        self.tool          = "pencil"  # Активный инструмент
        self.primary_color = (0, 0, 0)
        self.secondary_color = (255, 255, 255)
        self.filled        = False     # Заливка фигур (True = filled, False = outline)
        self.brush_size    = 4
        self.drawing       = False     # Рисуем ли сейчас?
        self.start_pos     = None      # Начало фигуры (canvas coords)
        self.last_pos      = None      # Последняя позиция (для карандаша)
        self.preview_layer = None      # Временный слой предпросмотра

        # Уведомление (Save / Undo)
        self.notification      = ""
        self.notification_timer= 0

        # Создаём UI-элементы
        self._build_ui()

    # ── Построение UI ─────────────────────────────────────────
    def _build_ui(self):
        """Создаёт кнопки инструментов, ползунок и палитру."""
        px  = 10          # Отступ слева внутри панели
        pw  = TOOLBAR_W - 20
        y   = 50

        # Кнопки инструментов
        self.tool_buttons = []
        for tool_id, label, icon in self.TOOLS:
            btn = ToolButton(px, y, pw, tool_id, label, icon)
            self.tool_buttons.append(btn)
            y += ToolButton.H + 4

        # Флажок "Заливка фигур"
        self.fill_checkbox_rect = pygame.Rect(px, y + 8, 18, 18)
        y += 34

        # Ползунок размера кисти
        self.size_slider = Slider(px, y + 20, pw - 30, min_val=1, max_val=40, value=4)
        y += 50

        # Палитра цветов (6 столбцов)
        palette_y = y + 10
        self.swatches = []
        cols = 6
        cell = (pw) // cols
        for i, color in enumerate(PALETTE):
            col = i % cols
            row = i // cols
            sx = px + col * cell
            sy = palette_y + row * (ColorSwatch.SIZE + 4)
            self.swatches.append(ColorSwatch(sx, sy, color))

        # Кнопки действий
        action_y = palette_y + (len(PALETTE) // cols) * (ColorSwatch.SIZE + 4) + 20
        self.btn_clear = ToolButton(px, action_y,      pw, "clear",  "Очистить",  "🗑")
        self.btn_save  = ToolButton(px, action_y + 46, pw, "save",   "Сохранить", "💾")
        self.btn_undo  = ToolButton(px, action_y + 92, pw // 2 - 2, "undo", "Undo", "↩")
        self.btn_redo  = ToolButton(px + pw // 2 + 2, action_y + 92, pw // 2 - 2, "redo", "Redo", "↪")

    # ── Главный цикл ──────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(60)
            self._handle_events()
            self._update()
            self._draw()

    # ── Обработка событий ────────────────────────────────────
    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # Горячие клавиши
            if event.type == pygame.KEYDOWN:
                ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL
                if ctrl and event.key == pygame.K_z: self._undo()
                if ctrl and event.key == pygame.K_y: self._redo()
                if ctrl and event.key == pygame.K_s: self._save_image()
                if event.key == pygame.K_DELETE:      self._clear_canvas()

            # Ползунок
            self.size_slider.handle_event(event)
            self.brush_size = self.size_slider.value

            # Кнопки инструментов
            for btn in self.tool_buttons:
                result = btn.handle_event(event)
                if result:
                    self.tool = result

            # Флажок "Заливка"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.fill_checkbox_rect.collidepoint(event.pos):
                    self.filled = not self.filled

            # Кнопки действий
            if self.btn_clear.handle_event(event): self._clear_canvas()
            if self.btn_save.handle_event(event):  self._save_image()
            if self.btn_undo.handle_event(event):  self._undo()
            if self.btn_redo.handle_event(event):  self._redo()

            # Палитра
            for sw in self.swatches:
                res = sw.handle_event(event)
                if res:
                    if res[0] == "primary":   self.primary_color = res[1]
                    if res[0] == "secondary": self.secondary_color = res[1]

            # ── Рисование на холсте ────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                if point_in_canvas(*event.pos):
                    cx, cy = canvas_pos(*event.pos)
                    color = self.primary_color if event.button == 1 else self.secondary_color

                    if self.tool == "fill":
                        # Заливка: сохраняем undo и заливаем
                        self._save_undo()
                        flood_fill(self.canvas, cx, cy, color)
                    elif self.tool == "pencil":
                        self._save_undo()
                        self.drawing  = True
                        self.last_pos = (cx, cy)
                        self._active_color = color
                    else:
                        # Фигуры и линии: начало рисования
                        self.drawing   = True
                        self.start_pos = (cx, cy)
                        self._active_color = color
                        self.preview_layer = self.canvas.copy()

            if event.type == pygame.MOUSEMOTION and self.drawing:
                if point_in_canvas(*event.pos):
                    cx, cy = canvas_pos(*event.pos)
                    if self.tool == "pencil":
                        # Карандаш: рисуем линию от предыдущей точки
                        if self.last_pos:
                            pygame.draw.line(self.canvas, self._active_color,
                                             self.last_pos, (cx, cy), self.brush_size)
                        self.last_pos = (cx, cy)
                    elif self.tool == "eraser":
                        # Ластик: рисуем цветом фона
                        if self.last_pos:
                            pygame.draw.line(self.canvas, C_CANVAS_BG,
                                             self.last_pos, (cx, cy), self.brush_size * 3)
                        self.last_pos = (cx, cy)
                    else:
                        # Для фигур: показываем предпросмотр
                        self._draw_preview(cx, cy)

            if event.type == pygame.MOUSEBUTTONUP and self.drawing:
                if self.start_pos:
                    cx, cy = canvas_pos(*event.pos)
                    # Фиксируем фигуру на холсте
                    if self.preview_layer is not None:
                        self.canvas.blit(self.preview_layer, (0, 0))
                    self._save_undo()
                    self._draw_shape(self.canvas, self.tool, self.start_pos, (cx, cy),
                                     self._active_color, self.brush_size, self.filled)
                self.drawing       = False
                self.start_pos     = None
                self.last_pos      = None
                self.preview_layer = None

            # Ластик: начало движения с нажатой кнопкой
            if event.type == pygame.MOUSEBUTTONDOWN and self.tool == "eraser":
                if point_in_canvas(*event.pos):
                    self._save_undo()
                    self.drawing  = True
                    self.last_pos = canvas_pos(*event.pos)

    # ── Предпросмотр фигуры во время рисования ───────────────
    def _draw_preview(self, cx, cy):
        """Копирует сохранённый слой и рисует поверх него предпросмотр фигуры."""
        if self.preview_layer is None:
            return
        self.canvas.blit(self.preview_layer, (0, 0))
        self._draw_shape(self.canvas, self.tool, self.start_pos, (cx, cy),
                         self._active_color, self.brush_size, self.filled)

    # ── Рисование фигуры ─────────────────────────────────────
    def _draw_shape(self, surf, tool, p1, p2, color, size, filled):
        """
        Главная функция рисования.
        Вызывается и для предпросмотра, и для финального рисования.
        """
        x1, y1 = p1
        x2, y2 = p2
        lw = 0 if filled else size    # 0 = залитый прямоугольник

        if tool == "line":
            pygame.draw.line(surf, color, p1, p2, size)

        elif tool == "rect":
            # Прямоугольник по двум углам
            rect = pygame.Rect(min(x1, x2), min(y1, y2),
                               abs(x2 - x1), abs(y2 - y1))
            if rect.width > 0 and rect.height > 0:
                pygame.draw.rect(surf, color, rect, lw, border_radius=0)

        elif tool == "square":
            # ── КВАДРАТ: сторона = min(|dx|, |dy|) ────────────
            pts = make_square_pts(x1, y1, x2, y2)
            pygame.draw.polygon(surf, color, pts, lw)

        elif tool == "circle":
            # Эллипс по bounding box
            rect = pygame.Rect(min(x1, x2), min(y1, y2),
                               abs(x2 - x1), abs(y2 - y1))
            if rect.width > 0 and rect.height > 0:
                pygame.draw.ellipse(surf, color, rect, lw)

        elif tool == "right_tri":
            # ── ПРЯМОУГОЛЬНЫЙ ТРЕУГОЛЬНИК ──────────────────────
            pts = make_right_triangle_pts(x1, y1, x2, y2)
            pygame.draw.polygon(surf, color, pts, lw)

        elif tool == "eq_tri":
            # ── РАВНОСТОРОННИЙ ТРЕУГОЛЬНИК ─────────────────────
            pts = make_equilateral_pts(x1, y1, x2, y2)
            pygame.draw.polygon(surf, color, pts, lw)

        elif tool == "rhombus":
            # ── РОМБ ────────────────────────────────────────────
            pts = make_rhombus_pts(x1, y1, x2, y2)
            pygame.draw.polygon(surf, color, pts, lw)

    # ── Undo / Redo ───────────────────────────────────────────
    def _save_undo(self):
        """Сохраняет текущее состояние холста в стек Undo."""
        if len(self.undo_stack) >= UNDO_LIMIT:
            self.undo_stack.pop(0)   # Удаляем самое старое
        self.undo_stack.append(self.canvas.copy())
        self.redo_stack.clear()      # Redo сбрасывается при новом действии

    def _undo(self):
        """Отменяет последнее действие."""
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.canvas.copy())
            self.canvas.blit(self.undo_stack.pop(), (0, 0))
            self._notify("↩ Отменено")

    def _redo(self):
        """Повторяет отменённое действие."""
        if self.redo_stack:
            self.undo_stack.append(self.canvas.copy())
            self.canvas.blit(self.redo_stack.pop(), (0, 0))
            self._notify("↪ Повторено")

    # ── Очистить / Сохранить ─────────────────────────────────
    def _clear_canvas(self):
        """Очищает холст белым цветом."""
        self._save_undo()
        self.canvas.fill(C_CANVAS_BG)
        self._notify("🗑 Холст очищен")

    def _save_image(self):
        """Сохраняет холст как PNG-файл рядом со скриптом."""
        path = os.path.join(os.path.dirname(__file__), "paint_output.png")
        pygame.image.save(self.canvas, path)
        self._notify(f"💾 Сохранено: paint_output.png")

    def _notify(self, msg, duration=120):
        """Показывает уведомление внизу экрана на duration кадров."""
        self.notification       = msg
        self.notification_timer = duration

    # ── Обновление ───────────────────────────────────────────
    def _update(self):
        """Обновляет hover-состояния всех кнопок."""
        mp = pygame.mouse.get_pos()
        for btn in self.tool_buttons:
            btn.update(mp)
        self.btn_clear.update(mp)
        self.btn_save.update(mp)
        self.btn_undo.update(mp)
        self.btn_redo.update(mp)
        if self.notification_timer > 0:
            self.notification_timer -= 1

    # ── Отрисовка ────────────────────────────────────────────
    def _draw(self):
        self.screen.fill(C_BG)

        # Рисуем холст
        self.screen.blit(self.canvas, (CANVAS_X, CANVAS_Y))
        # Рамка холста
        pygame.draw.rect(self.screen, C_BORDER,
                         (CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H), 2)

        # Левая панель
        self._draw_panel()

        # Курсор-кружок (только на холсте)
        mx, my = pygame.mouse.get_pos()
        if point_in_canvas(mx, my) and self.tool in ("pencil", "eraser"):
            r = self.brush_size if self.tool == "pencil" else self.brush_size * 3
            pygame.draw.circle(self.screen, C_ACCENT, (mx, my), r, 1)

        # Уведомление
        if self.notification_timer > 0:
            alpha = min(255, self.notification_timer * 4)
            notif = self.font_med.render(self.notification, True, C_WHITE)
            s = pygame.Surface(notif.get_size(), pygame.SRCALPHA)
            s.fill((0, 0, 0, 0))
            s.blit(notif, (0, 0))
            s.set_alpha(alpha)
            nx = CANVAS_X + (CANVAS_W - notif.get_width()) // 2
            ny = WIN_H - 40
            bg = pygame.Surface((notif.get_width() + 24, notif.get_height() + 12), pygame.SRCALPHA)
            bg.fill((20, 22, 35, int(alpha * 0.85)))
            self.screen.blit(bg, (nx - 12, ny - 6))
            self.screen.blit(s, (nx, ny))

        pygame.display.flip()

    def _draw_panel(self):
        """Рисует левую панель инструментов."""
        # Фон панели
        pygame.draw.rect(self.screen, C_PANEL, (0, 0, TOOLBAR_W, WIN_H))
        pygame.draw.line(self.screen, C_BORDER, (TOOLBAR_W - 1, 0), (TOOLBAR_W - 1, WIN_H), 2)

        # Заголовок
        title = self.font_title.render("🎨 PAINT", True, C_ACCENT)
        self.screen.blit(title, title.get_rect(center=(TOOLBAR_W // 2, 28)))

        # Кнопки инструментов
        for btn in self.tool_buttons:
            btn.draw(self.screen, self.font_bold, self.tool == btn.tool_id)

        # Флажок "Заливка фигур"
        pygame.draw.rect(self.screen, C_BORDER, self.fill_checkbox_rect, border_radius=4)
        if self.filled:
            pygame.draw.rect(self.screen, C_ACCENT, self.fill_checkbox_rect.inflate(-4, -4), border_radius=3)
        lbl = self.font_small.render("Залитая фигура", True, C_GRAY)
        self.screen.blit(lbl, (self.fill_checkbox_rect.right + 6, self.fill_checkbox_rect.y + 2))

        # Ползунок размера
        lbl2 = self.font_small.render(f"Толщина кисти", True, C_GRAY)
        self.screen.blit(lbl2, (10, self.size_slider.rect.y - 18))
        self.size_slider.draw(self.screen, self.font_small)

        # Палитра цветов
        lbl3 = self.font_small.render("Цвета  (ЛКМ / ПКМ)", True, C_GRAY)
        top_sw = self.swatches[0].rect.y - 18
        self.screen.blit(lbl3, (10, top_sw))
        for sw in self.swatches:
            sw.draw(self.screen, self.primary_color, self.secondary_color)

        # Активные цвета (большие квадраты)
        swatch_bottom = self.swatches[-1].rect.bottom + 8
        # Вторичный (под основным)
        sec_rect = pygame.Rect(36, swatch_bottom + 14, 36, 36)
        pygame.draw.rect(self.screen, self.secondary_color, sec_rect, border_radius=5)
        pygame.draw.rect(self.screen, C_WHITE, sec_rect, width=2, border_radius=5)
        # Основной (поверх)
        pri_rect = pygame.Rect(16, swatch_bottom + 4, 36, 36)
        pygame.draw.rect(self.screen, self.primary_color, pri_rect, border_radius=5)
        pygame.draw.rect(self.screen, C_WHITE, pri_rect, width=2, border_radius=5)
        c_lbl = self.font_small.render("Осн. / Доп.", True, C_GRAY)
        self.screen.blit(c_lbl, (60, swatch_bottom + 18))

        # Кнопки действий
        self.btn_clear.draw(self.screen, self.font_bold, False)
        self.btn_save.draw(self.screen,  self.font_bold, False)
        self.btn_undo.draw(self.screen,  self.font_bold, False)
        self.btn_redo.draw(self.screen,  self.font_bold, False)

        # Подсказка внизу
        tips = ["Ctrl+Z: Undo", "Ctrl+Y: Redo", "Ctrl+S: Save"]
        for i, tip in enumerate(tips):
            t = self.font_small.render(tip, True, C_BORDER)
            self.screen.blit(t, (10, WIN_H - 60 + i * 16))


# ─────────────────────────────────────────────────────────────
#  ТОЧКА ВХОДА
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PaintApp()
    app.run()