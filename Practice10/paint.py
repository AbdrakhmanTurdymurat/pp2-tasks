import pygame
import sys
import math
import os

SCREEN_W  = 900
SCREEN_H  = 680

TOOLBAR_W = 160   # left panel width
CANVAS_X  = TOOLBAR_W
CANVAS_Y  = 0
CANVAS_W  = SCREEN_W - TOOLBAR_W
CANVAS_H  = SCREEN_H

# Color palette
BG_PANEL   = (22,  22,  35 )
BG_CANVAS  = (255, 255, 255)
ACCENT     = (55,  130, 230)
ACCENT_HOV = (80,  160, 255)
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GRAY_DARK  = (40,  40,  55 )
GRAY_MID   = (65,  65,  85 )
GRAY_LIGHT = (120, 120, 145)
TEXT_COLOR = (210, 210, 230)

# Preset palette colors shown in the toolbar
PALETTE = [
    (0,   0,   0  ), (255, 255, 255), (220, 50,  50 ),
    (240, 130, 20 ), (240, 215, 0  ), (55,  185, 65 ),
    (50,  130, 230), (130, 60,  200), (220, 80,  160),
    (40,  195, 195), (140, 90,  55 ), (180, 180, 180),
]

TOOLS  = ["Pencil", "Line", "Rect", "Circle", "Eraser"]
SIZES  = [2, 4, 8, 14, 22]   # brush/eraser sizes


# ════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════
def draw_rrect(surf, color, rect, r=8, alpha=255):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=r)
    surf.blit(s, (rect[0], rect[1]))


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def hsv_to_rgb(h, s, v):
    """Convert HSV (0–360, 0–1, 0–1) → (r, g, b) 0–255."""
    h = h % 360
    hi = int(h / 60) % 6
    f  = h / 60 - int(h / 60)
    p  = v * (1 - s);  q = v * (1 - f*s);  t = v * (1 - (1-f)*s)
    m  = [v,q,p,p,t,v][hi], [t,v,v,q,p,p][hi], [p,p,t,v,v,q][hi]
    return tuple(int(x * 255) for x in m)


# ════════════════════════════════════════════════════════
#  COLOR PICKER  (inline HSV wheel panel)
# ════════════════════════════════════════════════════════
class ColorWheel:
    """Small HSV color picker drawn below the palette."""
    W = TOOLBAR_W - 20   # 140
    H = 140

    def __init__(self, x, y):
        self.x, self.y  = x, y
        self.hue        = 0.0    # 0–360
        self.sat        = 1.0    # 0–1
        self.val        = 1.0    # 0–1
        self._build()

    def _build(self):
        """Pre-render the hue gradient bar."""
        self._hue_surf = pygame.Surface((self.W, 14))
        for px in range(self.W):
            h = px / self.W * 360
            self._hue_surf.set_at((px, 0), hsv_to_rgb(h, 1, 1))
            for py in range(1, 14):
                self._hue_surf.set_at((px, py), hsv_to_rgb(h, 1, 1))

    @property
    def color(self):
        return hsv_to_rgb(self.hue, self.sat, self.val)

    def draw(self, surf):
        bx, by = self.x, self.y
        # Title
        f = pygame.font.SysFont("Arial", 13, bold=True)
        t = f.render("Color Picker", True, GRAY_LIGHT)
        surf.blit(t, (bx, by - 18))

        # Hue bar
        surf.blit(self._hue_surf, (bx, by))
        pygame.draw.rect(surf, WHITE, (bx, by, self.W, 14), 1)
        # Hue cursor
        hx = int(bx + self.hue / 360 * self.W)
        pygame.draw.rect(surf, WHITE, (hx-2, by-2, 4, 18))

        # SV square (sat horizontal, val vertical)
        sv_y = by + 22
        sv_h = self.H - 30
        for px in range(self.W):
            s = px / self.W
            for py in range(sv_h):
                v = 1 - py / sv_h
                rgb = hsv_to_rgb(self.hue, s, v)
                surf.set_at((bx + px, sv_y + py), rgb)
        # SV cursor
        sx = int(bx + self.sat * self.W)
        sy = int(sv_y + (1 - self.val) * sv_h)
        pygame.draw.circle(surf, WHITE, (sx, sy), 5, 2)
        pygame.draw.circle(surf, BLACK, (sx, sy), 7, 1)

        # Current color swatch
        swatch_y = sv_y + sv_h + 6
        pygame.draw.rect(surf, self.color, (bx, swatch_y, self.W, 16))
        pygame.draw.rect(surf, WHITE,      (bx, swatch_y, self.W, 16), 1)

    def handle_mouse(self, mx, my, buttons):
        """Call every frame; updates hue/sat/val if mouse is dragging over picker."""
        bx, by = self.x, self.y
        if not buttons[0]:
            return
        # Hue bar
        if bx <= mx <= bx + self.W and by <= my <= by + 14:
            self.hue = clamp((mx - bx) / self.W * 360, 0, 359.9)
        # SV square
        sv_y = by + 22
        sv_h = self.H - 30
        if bx <= mx <= bx + self.W and sv_y <= my <= sv_y + sv_h:
            self.sat = clamp((mx - bx) / self.W, 0, 1)
            self.val = clamp(1 - (my - sv_y) / sv_h, 0, 1)


# ════════════════════════════════════════════════════════
#  TOOLBAR
# ════════════════════════════════════════════════════════
class Toolbar:
    PAD    = 10
    BTN_H  = 34

    def __init__(self):
        self.active_tool  = "Pencil"
        self.active_size  = 4
        self.draw_color   = BLACK
        self.filled       = False    # fill shapes?
        self.font_med     = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_sm      = pygame.font.SysFont("Arial", 13)

        # Color wheel positioned near bottom of toolbar
        wheel_y = SCREEN_H - 220
        self.wheel = ColorWheel(self.PAD, wheel_y)

        self._build_layout()

    def _build_layout(self):
        p = self.PAD
        y = 10

        # Tool buttons (stacked)
        self.tool_rects = {}
        for name in TOOLS:
            self.tool_rects[name] = pygame.Rect(p, y, TOOLBAR_W - p*2, self.BTN_H)
            y += self.BTN_H + 5

        y += 8
        # Size buttons (row)
        self.size_rects = {}
        sz_w = (TOOLBAR_W - p*2) // len(SIZES)
        for i, sz in enumerate(SIZES):
            self.size_rects[sz] = pygame.Rect(p + i*sz_w, y, sz_w-2, self.BTN_H)
        y += self.BTN_H + 8

        # Palette swatches (3 columns)
        self.pal_rects = []
        sw = (TOOLBAR_W - p*2) // 3
        sh = sw
        for i, _ in enumerate(PALETTE):
            col = i % 3
            row = i // 3
            r   = pygame.Rect(p + col*sw, y + row*sh, sw-2, sh-2)
            self.pal_rects.append(r)
        y += ((len(PALETTE)-1)//3 + 1) * sh + 10

        # Fill toggle
        self.fill_rect = pygame.Rect(p, y, TOOLBAR_W - p*2, self.BTN_H)
        y += self.BTN_H + 6

        # Clear button
        self.clear_rect = pygame.Rect(p, y, TOOLBAR_W - p*2, self.BTN_H)
        y += self.BTN_H + 6

        # Save button
        self.save_rect = pygame.Rect(p, y, TOOLBAR_W - p*2, self.BTN_H)

    def draw(self, surf):
        surf.fill(BG_PANEL, (0, 0, TOOLBAR_W, SCREEN_H))
        # Subtle right border
        pygame.draw.line(surf, GRAY_MID, (TOOLBAR_W-1, 0), (TOOLBAR_W-1, SCREEN_H))

        mouse = pygame.mouse.get_pos()

        # ── Tool buttons ──────────────────────────────
        for name, r in self.tool_rects.items():
            active = name == self.active_tool
            hov    = r.collidepoint(mouse) and not active
            col    = ACCENT if active else (ACCENT_HOV if hov else GRAY_MID)
            draw_rrect(surf, col, r, r=7)
            # Tool icon (simple symbol)
            icon_map = {"Pencil": "✏", "Line": "╱", "Rect": "▭",
                        "Circle": "○", "Eraser": "⬜"}
            t = self.font_med.render(f"{icon_map.get(name,'·')}  {name}",
                                     True, WHITE)
            surf.blit(t, (r.x+8, r.y + r.h//2 - t.get_height()//2))

        # ── Size buttons ──────────────────────────────
        for sz, r in self.size_rects.items():
            active = sz == self.active_size
            col = ACCENT if active else GRAY_MID
            draw_rrect(surf, col, r, r=5)
            # Show a circle representing the size
            cr = (r.x + r.w//2, r.y + r.h//2)
            dot_r = max(2, min(sz//2, 12))
            pygame.draw.circle(surf, WHITE, cr, dot_r)

        # ── Palette swatches ──────────────────────────
        for i, (r, col) in enumerate(zip(self.pal_rects, PALETTE)):
            pygame.draw.rect(surf, col, r, border_radius=4)
            if col == self.draw_color:
                pygame.draw.rect(surf, WHITE, r, 2, border_radius=4)

        # ── Fill toggle ───────────────────────────────
        col = ACCENT if self.filled else GRAY_MID
        draw_rrect(surf, col, self.fill_rect, r=7)
        t = self.font_med.render("Fill  " + ("ON" if self.filled else "OFF"),
                                 True, WHITE)
        surf.blit(t, (self.fill_rect.x+8,
                      self.fill_rect.y + self.fill_rect.h//2 - t.get_height()//2))

        # ── Clear button ──────────────────────────────
        hov = self.clear_rect.collidepoint(mouse)
        draw_rrect(surf, (180, 50, 50) if hov else (130, 40, 40),
                   self.clear_rect, r=7)
        t = self.font_med.render("⊗  Clear", True, WHITE)
        surf.blit(t, (self.clear_rect.x+8,
                      self.clear_rect.y + self.clear_rect.h//2 - t.get_height()//2))

        # ── Save button ───────────────────────────────
        hov = self.save_rect.collidepoint(mouse)
        draw_rrect(surf, (40, 140, 80) if hov else (30, 100, 60),
                   self.save_rect, r=7)
        t = self.font_med.render("💾  Save PNG", True, WHITE)
        surf.blit(t, (self.save_rect.x+6,
                      self.save_rect.y + self.save_rect.h//2 - t.get_height()//2))

        # ── Color wheel ───────────────────────────────
        self.wheel.draw(surf)

        # Active color large swatch at very top right of toolbar
        pygame.draw.rect(surf, self.draw_color,
                         (TOOLBAR_W - 34, 2, 30, 30), border_radius=5)
        pygame.draw.rect(surf, WHITE,
                         (TOOLBAR_W - 34, 2, 30, 30), 1, border_radius=5)

    def handle_click(self, pos, buttons) -> str | None:
        """
        Handle single clicks on toolbar controls.
        Returns "clear", "save", or None.
        """
        mx, my = pos

        # Update wheel (drag-based)
        self.wheel.handle_mouse(mx, my, buttons)
        self.draw_color = self.wheel.color

        if not buttons[0]:
            return None

        # Tool buttons
        for name, r in self.tool_rects.items():
            if r.collidepoint(pos):
                self.active_tool = name
                return None

        # Size buttons
        for sz, r in self.size_rects.items():
            if r.collidepoint(pos):
                self.active_size = sz
                return None

        # Palette
        for i, r in enumerate(self.pal_rects):
            if r.collidepoint(pos):
                self.draw_color = PALETTE[i]
                # Sync hue to the new palette color — approximate
                return None

        # Fill toggle
        if self.fill_rect.collidepoint(pos):
            self.filled = not self.filled
            return None

        if self.clear_rect.collidepoint(pos): return "clear"
        if self.save_rect.collidepoint(pos):  return "save"
        return None


# ════════════════════════════════════════════════════════
#  CANVAS
# ════════════════════════════════════════════════════════
class Canvas:
    def __init__(self):
        self.surface = pygame.Surface((CANVAS_W, CANVAS_H))
        self.surface.fill(BG_CANVAS)
        self.clear()

    def clear(self):
        self.surface.fill(BG_CANVAS)

    def save(self, path="paint_output.png"):
        pygame.image.save(self.surface, path)
        return path

    def draw_to_screen(self, screen):
        screen.blit(self.surface, (CANVAS_X, CANVAS_Y))

    # ── Permanent drawing operations ──────────────────
    def draw_pencil(self, p1, p2, color, size):
        """Continuous freehand stroke segment."""
        pygame.draw.line(self.surface, color, p1, p2, max(1, size))

    def draw_line_final(self, p1, p2, color, size):
        pygame.draw.line(self.surface, color, p1, p2, max(1, size))

    def draw_rect_final(self, p1, p2, color, size, filled):
        r = pygame.Rect(min(p1[0],p2[0]), min(p1[1],p2[1]),
                        abs(p2[0]-p1[0]),  abs(p2[1]-p1[1]))
        if r.width < 1 or r.height < 1:
            return
        w = 0 if filled else max(1, size)
        pygame.draw.rect(self.surface, color, r, w)

    def draw_circle_final(self, centre, edge, color, size, filled):
        r = int(math.hypot(edge[0]-centre[0], edge[1]-centre[1]))
        if r < 1: return
        w = 0 if filled else max(1, size)
        pygame.draw.circle(self.surface, color, centre, r, w)

    def erase(self, p1, p2, size):
        """Erase by drawing white."""
        pygame.draw.line(self.surface, BG_CANVAS, p1, p2, max(1, size * 2))


# ════════════════════════════════════════════════════════
#  PREVIEW LAYER  (drawn on top of canvas, not committed)
# ════════════════════════════════════════════════════════
def draw_preview(screen, tool, start, end, color, size, filled):
    """Draw a ghost/preview shape while the mouse is held down."""
    if start is None or end is None:
        return
    if tool == "Line":
        pygame.draw.line(screen, color,
                         (start[0]+CANVAS_X, start[1]+CANVAS_Y),
                         (end[0]+CANVAS_X,   end[1]+CANVAS_Y),
                         max(1, size))
    elif tool == "Rect":
        r = pygame.Rect(
            CANVAS_X + min(start[0], end[0]),
            CANVAS_Y + min(start[1], end[1]),
            abs(end[0]-start[0]), abs(end[1]-start[1]))
        if r.width > 0 and r.height > 0:
            w = 0 if filled else max(1, size)
            pygame.draw.rect(screen, color, r, w)
    elif tool == "Circle":
        cx = start[0] + CANVAS_X
        cy = start[1] + CANVAS_Y
        rad = int(math.hypot(end[0]-start[0], end[1]-start[1]))
        if rad > 0:
            w = 0 if filled else max(1, size)
            pygame.draw.circle(screen, color, (cx, cy), rad, w)


# ════════════════════════════════════════════════════════
#  SAVE NOTIFICATION
# ════════════════════════════════════════════════════════
class SaveNotice:
    def __init__(self):
        self.text    = ""
        self.timer   = 0
        self.font    = pygame.font.SysFont("Arial", 16, bold=True)

    def show(self, path):
        self.text  = f"Saved → {path}"
        self.timer = 150   # frames

    def update_draw(self, surf):
        if self.timer <= 0: return
        self.timer -= 1
        a = min(255, self.timer * 6)
        s = self.font.render(self.text, True, WHITE)
        bx, by = CANVAS_X + 10, SCREEN_H - 34
        draw_rrect(surf, (20, 20, 30), (bx-6, by-4, s.get_width()+12, s.get_height()+8),
                   r=6, alpha=a)
        s.set_alpha(a)
        surf.blit(s, (bx, by))


# ════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ════════════════════════════════════════════════════════
class PaintApp:
    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Paint")
        self.clock   = pygame.time.Clock()

        self.toolbar = Toolbar()
        self.canvas  = Canvas()
        self.notice  = SaveNotice()

        # Drawing state
        self.drawing     = False    # mouse button held
        self.last_pos    = None     # last canvas position (for pencil/eraser)
        self.start_pos   = None     # start position for shape tools

    def _canvas_pos(self, screen_pos):
        """Convert screen coordinates to canvas-local coordinates."""
        return (screen_pos[0] - CANVAS_X, screen_pos[1] - CANVAS_Y)

    def _on_canvas(self, pos):
        """True if the position is within the canvas area."""
        cx, cy = self._canvas_pos(pos)
        return 0 <= cx < CANVAS_W and 0 <= cy < CANVAS_H

    def run(self):
        while True:
            self.clock.tick(60)
            mouse_pos    = pygame.mouse.get_pos()
            mouse_buttons = pygame.mouse.get_pressed()
            tool  = self.toolbar.active_tool
            color = self.toolbar.draw_color
            size  = self.toolbar.active_size
            filled = self.toolbar.filled

            # ─ Events ─────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        pass  # undo placeholder

                # ── Mouse button down ──────────────────────
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if pos[0] < TOOLBAR_W:
                        # Toolbar click
                        action = self.toolbar.handle_click(pos, mouse_buttons)
                        if action == "clear":
                            self.canvas.clear()
                        elif action == "save":
                            path = self.canvas.save()
                            self.notice.show(path)
                    elif self._on_canvas(pos):
                        # Canvas click — begin stroke/shape
                        self.drawing   = True
                        cp = self._canvas_pos(pos)
                        self.start_pos = cp
                        self.last_pos  = cp
                        # Instant dot for pencil/eraser
                        if tool == "Pencil":
                            self.canvas.draw_pencil(cp, cp, color, size)
                        elif tool == "Eraser":
                            self.canvas.erase(cp, cp, size)

                # ── Mouse button up ────────────────────────
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.drawing and self._on_canvas(mouse_pos):
                        cp = self._canvas_pos(mouse_pos)
                        if tool == "Line":
                            self.canvas.draw_line_final(self.start_pos, cp, color, size)
                        elif tool == "Rect":
                            self.canvas.draw_rect_final(self.start_pos, cp, color, size, filled)
                        elif tool == "Circle":
                            self.canvas.draw_circle_final(self.start_pos, cp, color, size, filled)
                    self.drawing   = False
                    self.start_pos = None
                    self.last_pos  = None

            # ── Continuous drawing (pencil / eraser) ──────
            if self.drawing and mouse_buttons[0] and self._on_canvas(mouse_pos):
                cp = self._canvas_pos(mouse_pos)
                if tool == "Pencil" and self.last_pos:
                    self.canvas.draw_pencil(self.last_pos, cp, color, size)
                elif tool == "Eraser" and self.last_pos:
                    self.canvas.erase(self.last_pos, cp, size)
                self.last_pos = cp

            # ── Toolbar hover update (color wheel drag) ───
            if mouse_pos[0] < TOOLBAR_W:
                self.toolbar.handle_click(mouse_pos, mouse_buttons)

            # ─ Render ──────────────────────────────────────
            self.screen.fill(BG_PANEL)
            self.canvas.draw_to_screen(self.screen)
            self.toolbar.draw(self.screen)

            # Preview ghost shape while dragging
            if self.drawing and self.start_pos and tool in ("Line", "Rect", "Circle"):
                cp = self._canvas_pos(mouse_pos)
                draw_preview(self.screen, tool, self.start_pos, cp,
                             color, size, filled)

            # Canvas border
            pygame.draw.rect(self.screen, GRAY_MID,
                             (CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H), 1)

            # Cursor crosshair on canvas
            if self._on_canvas(mouse_pos):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            self.notice.update_draw(self.screen)
            pygame.display.flip()


# ════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    PaintApp().run()