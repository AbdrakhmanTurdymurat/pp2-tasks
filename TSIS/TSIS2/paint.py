import math
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pygame


WIDTH, HEIGHT = 1320, 860
TOOLBAR_W = 320
CANVAS_X = TOOLBAR_W
CANVAS_Y = 0
CANVAS_W = WIDTH - TOOLBAR_W
CANVAS_H = HEIGHT
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (230, 230, 230)
DARK_GRAY = (70, 70, 70)
LIGHT_GRAY = (245, 245, 245)
RED = (220, 40, 40)
BLUE = (60, 90, 210)
GREEN = (55, 160, 80)
ORANGE = (240, 160, 50)
PURPLE = (160, 70, 190)
BROWN = (140, 95, 60)
CYAN = (70, 180, 200)
PINK = (235, 120, 170)

PALETTE = [BLACK, RED, BLUE, GREEN, ORANGE, PURPLE, BROWN, CYAN, PINK, WHITE]
BRUSH_SIZES = {1: 2, 2: 5, 3: 10}
BASE_DIR = Path(__file__).resolve().parent
SAVE_DIR = BASE_DIR / "saves"


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: str
    value: str | int | tuple | None = None


class PaintApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("TSIS 2 - Paint Application")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18)
        self.small_font = pygame.font.SysFont("arial", 14)
        self.big_font = pygame.font.SysFont("arial", 22, bold=True)

        self.canvas = pygame.Surface((CANVAS_W, CANVAS_H))
        self.canvas.fill(WHITE)

        self.running = True
        self.current_tool = "pencil"
        self.current_color = BLACK
        self.brush_level = 2
        self.brush_size = BRUSH_SIZES[self.brush_level]

        self.mouse_down = False
        self.start_pos = None
        self.prev_pos = None
        self.preview_surface = None
        self.temp_text_pos = None
        self.text_input = ""
        self.typing_text = False
        self.last_message = ""

        self.buttons = self._build_buttons()
        self.color_buttons = self._build_color_buttons()
        self.size_buttons = self._build_size_buttons()

    # ---------------- UI BUILD ----------------
    def _build_buttons(self):
        buttons = []
        x_positions = [14, 112, 210]
        y_top = 70
        w = 90
        h = 32
        gap_x = 8
        gap_y = 8

        labels = [
            ("Pencil", "tool", "pencil"),
            ("Line", "tool", "line"),
            ("Rect", "tool", "rect"),
            ("Circle", "tool", "circle"),
            ("Eraser", "tool", "eraser"),
            ("Fill", "tool", "fill"),
            ("Text", "tool", "text"),
            ("Square", "tool", "square"),
            ("Right tri", "tool", "right_triangle"),
            ("Equil tri", "tool", "equilateral_triangle"),
            ("Rhombus", "tool", "rhombus"),
            ("Clear", "action", "clear"),
            ("Save", "action", "save"),
        ]

        for i, (label, action, value) in enumerate(labels):
            col = i % 3
            row = i // 3
            x = x_positions[col]
            y = y_top + row * (h + gap_y)
            buttons.append(Button(pygame.Rect(x, y, w, h), label, action, value))
        return buttons

    def _build_color_buttons(self):
        buttons = []
        x0 = 14
        y0 = 565
        size = 38
        gap = 8
        for i, color in enumerate(PALETTE):
            row = i // 5
            col = i % 5
            rect = pygame.Rect(x0 + col * (size + gap), y0 + row * (size + gap), size, size)
            buttons.append(Button(rect, "", "color", color))
        return buttons

    def _build_size_buttons(self):
        buttons = []
        x0 = 14
        y = 688
        for i, level in enumerate([1, 2, 3]):
            rect = pygame.Rect(x0 + i * 74, y, 62, 36)
            buttons.append(Button(rect, str(level), "size", level))
        return buttons

    def _draw_panel(self):
        self.screen.fill((212, 212, 212))
        pygame.draw.rect(self.screen, LIGHT_GRAY, (0, 0, TOOLBAR_W, HEIGHT))
        pygame.draw.line(self.screen, DARK_GRAY, (TOOLBAR_W, 0), (TOOLBAR_W, HEIGHT), 2)

        title = self.big_font.render("TSIS 2 Paint", True, DARK_GRAY)
        self.screen.blit(title, (14, 14))

        self._draw_section_label("Tools", 42)
        for btn in self.buttons:
            self._draw_button(btn, active=(btn.action == "tool" and btn.value == self.current_tool))

        self._draw_section_label("Colors", 520)
        for btn in self.color_buttons:
            self._draw_color_button(btn)

        self._draw_section_label("Brush size", 645)
        for btn in self.size_buttons:
            self._draw_size_button(btn)

        info_y = 748
        info_lines = [
            f"Tool: {self._tool_name(self.current_tool)}",
            f"Color: {self._color_name(self.current_color)}",
            f"Brush: {self.brush_size}px",
            "Ctrl+S saves PNG",
            "1 / 2 / 3 change size",
        ]
        for i, line in enumerate(info_lines):
            surf = self.small_font.render(line, True, DARK_GRAY)
            self.screen.blit(surf, (14, info_y + i * 18))

        if self.last_message:
            msg = self.small_font.render(self.last_message, True, DARK_GRAY)
            self.screen.blit(msg, (14, HEIGHT - 24))

    def _draw_section_label(self, text, y):
        label = self.font.render(text, True, DARK_GRAY)
        self.screen.blit(label, (14, y))
        pygame.draw.line(self.screen, (210, 210, 210), (14, y + 18), (TOOLBAR_W - 14, y + 18), 1)

    def _draw_button(self, btn: Button, active=False):
        fill = (200, 220, 255) if active else WHITE
        pygame.draw.rect(self.screen, fill, btn.rect, border_radius=6)
        pygame.draw.rect(self.screen, DARK_GRAY, btn.rect, 1, border_radius=6)
        surf = self.small_font.render(btn.label, True, DARK_GRAY)
        self.screen.blit(surf, surf.get_rect(center=btn.rect.center))

    def _draw_color_button(self, btn: Button):
        pygame.draw.rect(self.screen, btn.value, btn.rect)
        pygame.draw.rect(self.screen, DARK_GRAY, btn.rect, 1)
        if btn.value == self.current_color:
            pygame.draw.rect(self.screen, RED, btn.rect, 3)

    def _draw_size_button(self, btn: Button):
        active = btn.value == self.brush_level
        fill = (210, 235, 210) if active else WHITE
        pygame.draw.rect(self.screen, fill, btn.rect, border_radius=6)
        pygame.draw.rect(self.screen, DARK_GRAY, btn.rect, 1, border_radius=6)
        surf = self.small_font.render(btn.label, True, DARK_GRAY)
        self.screen.blit(surf, surf.get_rect(center=btn.rect.center))

    def _draw_text_preview(self):
        if not self.temp_text_pos:
            return
        x, y = self.temp_text_pos
        text_surf = self.font.render(self.text_input, True, self.current_color)
        self.screen.blit(text_surf, (CANVAS_X + x, y))
        cursor_x = CANVAS_X + x + text_surf.get_width() + 1
        cursor = self.font.render("|", True, self.current_color)
        self.screen.blit(cursor, (cursor_x, y))

    # ---------------- HELPERS ----------------
    def _tool_name(self, tool):
        return {
            "pencil": "Pencil",
            "line": "Line",
            "rect": "Rectangle",
            "circle": "Circle",
            "eraser": "Eraser",
            "fill": "Fill",
            "text": "Text",
            "square": "Square",
            "right_triangle": "Right triangle",
            "equilateral_triangle": "Equilateral triangle",
            "rhombus": "Rhombus",
        }.get(tool, tool)

    def _color_name(self, color):
        names = {
            BLACK: "Black",
            WHITE: "White",
            RED: "Red",
            BLUE: "Blue",
            GREEN: "Green",
            ORANGE: "Orange",
            PURPLE: "Purple",
            BROWN: "Brown",
            CYAN: "Cyan",
            PINK: "Pink",
        }
        return names.get(color, str(color))

    def canvas_pos(self, pos):
        return pos[0] - CANVAS_X, pos[1]

    def inside_canvas(self, pos):
        return CANVAS_X <= pos[0] < WIDTH and 0 <= pos[1] < HEIGHT

    def set_brush_level(self, level):
        self.brush_level = level
        self.brush_size = BRUSH_SIZES[level]

    def save_canvas(self):
        SAVE_DIR.mkdir(exist_ok=True)
        filename = SAVE_DIR / datetime.now().strftime("paint_%Y%m%d_%H%M%S.png")
        pygame.image.save(self.canvas, str(filename))
        self.last_message = f"Saved: {filename.name}"
        print(self.last_message)

    def clear_canvas(self):
        self.canvas.fill(WHITE)
        self.last_message = "Canvas cleared"

    def flood_fill(self, start_pos, target_color, replacement_color):
        if target_color == replacement_color:
            return

        w, h = self.canvas.get_size()
        q = deque([start_pos])
        while q:
            x, y = q.popleft()
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            if self.canvas.get_at((x, y))[:3] != target_color[:3]:
                continue
            self.canvas.set_at((x, y), replacement_color)
            q.append((x + 1, y))
            q.append((x - 1, y))
            q.append((x, y + 1))
            q.append((x, y - 1))

    def draw_brush_line(self, surf, color, p1, p2, size):
        pygame.draw.line(surf, color, p1, p2, size)
        pygame.draw.circle(surf, color, p1, max(1, size // 2))
        pygame.draw.circle(surf, color, p2, max(1, size // 2))

    def draw_shape(self, surf, shape, start, end, color, size):
        x1, y1 = start
        x2, y2 = end

        if shape == "line":
            pygame.draw.line(surf, color, start, end, size)
            return

        if shape == "rect":
            rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            pygame.draw.rect(surf, color, rect, size)
            return

        if shape == "square":
            side = max(abs(x2 - x1), abs(y2 - y1))
            sx = x1 + side if x2 >= x1 else x1 - side
            sy = y1 + side if y2 >= y1 else y1 - side
            rect = pygame.Rect(min(x1, sx), min(y1, sy), abs(sx - x1), abs(sy - y1))
            pygame.draw.rect(surf, color, rect, size)
            return

        if shape == "circle":
            radius = max(1, int(math.hypot(x2 - x1, y2 - y1)))
            pygame.draw.circle(surf, color, start, radius, size)
            return

        if shape == "right_triangle":
            pts = [(x1, y2), (x1, y1), (x2, y2)]
            pygame.draw.polygon(surf, color, pts, size)
            return

        if shape == "equilateral_triangle":
            side = math.hypot(x2 - x1, y2 - y1)
            if side < 1:
                return
            height = side * math.sqrt(3) / 2
            direction = 1 if y2 >= y1 else -1
            pts = [
                (x1, y1),
                (x1 - side / 2, y1 + direction * height),
                (x1 + side / 2, y1 + direction * height),
            ]
            pygame.draw.polygon(surf, color, pts, size)
            return

        if shape == "rhombus":
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            pts = [(mx, y1), (x2, my), (mx, y2), (x1, my)]
            pygame.draw.polygon(surf, color, pts, size)
            return

    def apply_draw(self, start, end):
        if self.current_tool == "pencil":
            self.draw_brush_line(self.canvas, self.current_color, start, end, self.brush_size)
        elif self.current_tool == "eraser":
            self.draw_brush_line(self.canvas, WHITE, start, end, self.brush_size)
        elif self.current_tool in {"line", "rect", "circle", "square", "right_triangle", "equilateral_triangle", "rhombus"}:
            self.draw_shape(self.canvas, self.current_tool, start, end, self.current_color, self.brush_size)

    def handle_toolbar_click(self, pos):
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                if btn.action == "tool":
                    self.current_tool = btn.value
                    self.typing_text = False
                    self.text_input = ""
                    self.temp_text_pos = None
                    self.preview_surface = None
                elif btn.action == "action":
                    if btn.value == "clear":
                        self.clear_canvas()
                    elif btn.value == "save":
                        self.save_canvas()
                return True

        for btn in self.color_buttons:
            if btn.rect.collidepoint(pos):
                self.current_color = btn.value
                self.last_message = "Color changed"
                return True

        for btn in self.size_buttons:
            if btn.rect.collidepoint(pos):
                self.set_brush_level(btn.value)
                self.last_message = f"Brush size: {self.brush_size}px"
                return True

        return False

    # ---------------- EVENTS ----------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.typing_text:
                        self.typing_text = False
                        self.text_input = ""
                        self.temp_text_pos = None
                    else:
                        self.running = False

                elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.save_canvas()

                elif event.key == pygame.K_1:
                    self.set_brush_level(1)
                    self.last_message = "Brush size: 2px"
                elif event.key == pygame.K_2:
                    self.set_brush_level(2)
                    self.last_message = "Brush size: 5px"
                elif event.key == pygame.K_3:
                    self.set_brush_level(3)
                    self.last_message = "Brush size: 10px"
                elif self.typing_text:
                    if event.key == pygame.K_RETURN:
                        if self.text_input and self.temp_text_pos:
                            text_surf = self.font.render(self.text_input, True, self.current_color)
                            self.canvas.blit(text_surf, self.temp_text_pos)
                        self.typing_text = False
                        self.text_input = ""
                        self.temp_text_pos = None
                        self.last_message = "Text placed"
                    elif event.key == pygame.K_BACKSPACE:
                        self.text_input = self.text_input[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        self.text_input += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.handle_toolbar_click(event.pos):
                    continue

                if not self.inside_canvas(event.pos):
                    continue

                cpos = self.canvas_pos(event.pos)

                if self.current_tool == "fill":
                    target = self.canvas.get_at(cpos)
                    self.flood_fill(cpos, target, self.current_color)
                    self.last_message = "Fill applied"
                    continue

                if self.current_tool == "text":
                    self.typing_text = True
                    self.text_input = ""
                    self.temp_text_pos = cpos
                    self.last_message = "Typing text"
                    continue

                self.mouse_down = True
                self.start_pos = cpos
                self.prev_pos = cpos
                self.preview_surface = self.canvas.copy() if self.current_tool not in {"pencil", "eraser"} else None

                if self.current_tool in {"pencil", "eraser"}:
                    self.apply_draw(cpos, cpos)

            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_down and self.inside_canvas(event.pos):
                    cpos = self.canvas_pos(event.pos)
                    if self.current_tool in {"pencil", "eraser"}:
                        self.apply_draw(self.prev_pos, cpos)
                        self.prev_pos = cpos
                    else:
                        preview = self.canvas.copy()
                        self.draw_shape(preview, self.current_tool, self.start_pos, cpos, self.current_color, self.brush_size)
                        self.preview_surface = preview

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.mouse_down:
                    self.mouse_down = False
                    if self.inside_canvas(event.pos):
                        end_pos = self.canvas_pos(event.pos)
                        if self.current_tool in {"line", "rect", "circle", "square", "right_triangle", "equilateral_triangle", "rhombus"}:
                            self.draw_shape(self.canvas, self.current_tool, self.start_pos, end_pos, self.current_color, self.brush_size)
                        elif self.current_tool in {"pencil", "eraser"}:
                            self.apply_draw(self.prev_pos, end_pos)
                    self.start_pos = None
                    self.prev_pos = None
                    self.preview_surface = None

    # ---------------- MAIN LOOP ----------------
    def run(self):
        while self.running:
            self.handle_events()
            self._draw_panel()
            self.screen.blit(self.canvas, (CANVAS_X, CANVAS_Y))

            if self.preview_surface is not None:
                self.screen.blit(self.preview_surface, (CANVAS_X, CANVAS_Y))

            if self.typing_text:
                self._draw_text_preview()
                hint = self.small_font.render("Enter = confirm, Esc = cancel", True, DARK_GRAY)
                self.screen.blit(hint, (CANVAS_X + 12, 12))
            elif self.current_tool == "fill":
                hint = self.small_font.render("Click inside a closed area to fill", True, DARK_GRAY)
                self.screen.blit(hint, (CANVAS_X + 12, 12))
            elif self.current_tool == "line":
                hint = self.small_font.render("Click, drag, release to draw a line", True, DARK_GRAY)
                self.screen.blit(hint, (CANVAS_X + 12, 12))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    PaintApp().run()
