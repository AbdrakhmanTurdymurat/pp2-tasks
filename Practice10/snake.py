import pygame
import random
import sys
import math

SCREEN_W = 520
SCREEN_H = 590

CELL  = 20          # pixel size of one grid cell
COLS  = 20          # grid width  (cells)
ROWS  = 20          # grid height (cells)

# Pixel origin of the grid (centred, with room for HUD above)
GRID_X = (SCREEN_W - COLS * CELL) // 2   # 60
GRID_Y = 78                               # below the HUD bar

FOODS_PER_LEVEL = 4   # foods required to advance one level
FPS_RENDER      = 60  # rendering frame-rate (smooth)
FPS_SNAKE_BASE  = 8   # snake steps per second at level 1
FPS_SNAKE_INC   = 2   # extra steps per second per level

# Color palette
BG_COLOR     = (10,  10,  20 )
GRID_COLOR   = (22,  22,  38 )
GRID_BORDER  = (60,  60,  90 )
WALL_COLOR   = (55,  55,  75 )
WALL_BORDER  = (80,  80,  105)
HEAD_COLOR   = (55,  225, 125)
BODY_COLOR   = (35,  175, 90 )
BODY_OUTLINE = (20,  120, 60 )
FOOD_COLOR   = (230, 60,  60 )
FOOD_SHINE   = (255, 130, 90 )
WHITE        = (255, 255, 255)
BLACK        = (0,   0,   0  )
GRAY         = (85,  85,  110)
CYAN         = (0,   210, 220)
YELLOW       = (255, 215, 0  )
RED          = (220, 50,  50 )
GREEN        = (55,  200, 90 )
DARK_GREEN   = (20,  110, 55 )


# ════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════
def cell_px(col, row):
    """Return the top-left pixel of a grid cell."""
    return GRID_X + col * CELL, GRID_Y + row * CELL


def draw_rrect(surf, color, rect, r=8, alpha=255):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=r)
    surf.blit(s, (rect[0], rect[1]))


def draw_button(surf, font, text, rect, hovered):
    base  = (35, 120, 65)
    hover = (55, 175, 90)
    draw_rrect(surf, hover if hovered else base, rect, r=12)
    t = font.render(text, True, WHITE)
    surf.blit(t, (rect[0]+rect[2]//2 - t.get_width()//2,
                  rect[1]+rect[3]//2 - t.get_height()//2))
    return pygame.Rect(rect)


# ════════════════════════════════════════════════════════
#  WALLS — patterns change per level
# ════════════════════════════════════════════════════════
def build_walls(level: int) -> set:
    """
    Return a set of (col, row) wall cells appropriate for the given level.
    Level 1 → no inner walls.
    Level 2 → horizontal bar across the middle.
    Level 3 → two vertical pillars (gaps at centre for passage).
    Level 4+ → cross pattern in the centre.
    """
    walls = set()

    if level >= 2:
        mid_r = ROWS // 2
        for c in range(3, COLS - 3):
            walls.add((c, mid_r))

    if level >= 3:
        q1, q3 = COLS // 4, 3 * COLS // 4
        for r in range(2, ROWS - 2):
            if r not in (ROWS//2 - 1, ROWS//2, ROWS//2 + 1):
                walls.add((q1, r))
                walls.add((q3, r))

    if level >= 4:
        mid_c, mid_r = COLS // 2, ROWS // 2
        for c in range(2, COLS - 2):
            walls.add((c, mid_r))
        for r in range(2, ROWS - 2):
            walls.add((mid_c, r))

    return walls


# ════════════════════════════════════════════════════════
#  FOOD
# ════════════════════════════════════════════════════════
class Food:
    def __init__(self, snake_cells: set, walls: set):
        self.col, self.row = self._place(snake_cells, walls)
        self.phase = random.uniform(0, 360)   # animation offset

    @staticmethod
    def _place(snake_cells, walls):
        """Choose a free cell not occupied by the snake or any wall."""
        free = [(c, r) for c in range(COLS) for r in range(ROWS)
                if (c, r) not in snake_cells and (c, r) not in walls]
        return random.choice(free) if free else (COLS//2, ROWS//2)

    def update(self):
        """Advance pulse animation."""
        self.phase = (self.phase + 3.5) % 360

    def draw(self, surf):
        x, y  = cell_px(self.col, self.row)
        cx, cy = x + CELL//2, y + CELL//2
        pulse  = int(2.5 * abs(math.sin(math.radians(self.phase))))
        r      = CELL//2 - 3 + pulse

        # Glow halo
        g = pygame.Surface((CELL*3, CELL*3), pygame.SRCALPHA)
        pygame.draw.circle(g, (*FOOD_COLOR, 50), (CELL*3//2, CELL*3//2), r+5)
        surf.blit(g, (cx - CELL*3//2, cy - CELL*3//2))

        pygame.draw.circle(surf, FOOD_COLOR, (cx, cy), r)
        pygame.draw.circle(surf, WHITE,      (cx-3, cy-3), 3)   # shine


# ════════════════════════════════════════════════════════
#  SNAKE
# ════════════════════════════════════════════════════════
class Snake:
    def __init__(self):
        sc, sr = COLS // 2, ROWS // 2
        # Start with 3 body segments moving right
        self.body      = [(sc - i, sr) for i in range(3)]
        self.direction = (1, 0)   # (dc, dr)
        self.next_dir  = (1, 0)
        self._pending_grow = False

    # ── Direction ──────────────────────────────────────
    def set_direction(self, dc, dr):
        """Queue a direction change, ignoring direct reversal."""
        if (dc, dr) != (-self.direction[0], -self.direction[1]):
            self.next_dir = (dc, dr)

    # ── Movement ───────────────────────────────────────
    def step(self):
        """Advance the snake by one cell."""
        self.direction = self.next_dir
        hc, hr = self.body[0]
        new_head = (hc + self.direction[0], hr + self.direction[1])
        self.body.insert(0, new_head)
        if self._pending_grow:
            self._pending_grow = False   # keep the extra segment
        else:
            self.body.pop()              # remove tail normally

    def schedule_grow(self):
        """Call after eating food; the next step will add a segment."""
        self._pending_grow = True

    # ── Queries ────────────────────────────────────────
    def head(self):
        return self.body[0]

    def cells(self) -> set:
        return set(self.body)

    def hit_border(self) -> bool:
        """True if the head is outside the grid."""
        c, r = self.body[0]
        return not (0 <= c < COLS and 0 <= r < ROWS)

    def hit_wall(self, walls: set) -> bool:
        """True if the head overlaps a wall cell."""
        return self.body[0] in walls

    def hit_self(self) -> bool:
        """True if the head overlaps any body segment."""
        return self.body[0] in self.body[1:]

    # ── Drawing ────────────────────────────────────────
    def draw(self, surf):
        for i, (c, r) in enumerate(self.body):
            x, y = cell_px(c, r)
            color = HEAD_COLOR if i == 0 else BODY_COLOR
            rect  = (x+1, y+1, CELL-2, CELL-2)
            pygame.draw.rect(surf, color,       rect, border_radius=5)
            pygame.draw.rect(surf, BODY_OUTLINE, rect, 1, border_radius=5)

            # Draw eyes on the head segment
            if i == 0:
                self._draw_eyes(surf, x, y)

    def _draw_eyes(self, surf, x, y):
        """Draw two small eyes facing the current direction."""
        dc, dr = self.direction
        # Offset table: direction → (eye1_offset, eye2_offset) relative to cell
        offsets = {
            (1,  0): [(CELL-7, 4),    (CELL-7, CELL-8)],  # right
            (-1, 0): [(3,      4),    (3,      CELL-8)],  # left
            (0,  1): [(4,      CELL-7),(CELL-8, CELL-7)], # down
            (0, -1): [(4,      3),    (CELL-8, 3)],       # up
        }
        for ex, ey in offsets.get((dc, dr), [(4,4),(CELL-8,4)]):
            pygame.draw.circle(surf, WHITE, (x+ex+2, y+ey+2), 3)
            pygame.draw.circle(surf, BLACK, (x+ex+2, y+ey+2), 1)


# ════════════════════════════════════════════════════════
#  HUD
# ════════════════════════════════════════════════════════
def draw_hud(surf, f_med, f_sm, score, level, foods_this_level):
    # Dark header strip
    bar = pygame.Surface((SCREEN_W, 68), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 165))
    surf.blit(bar, (0, 0))

    # Score (left)
    s = f_med.render(f"Score: {score}", True, WHITE)
    surf.blit(s, (15, 10))

    # Level (centre)
    lv = f_med.render(f"Level {level}", True, CYAN)
    surf.blit(lv, (SCREEN_W//2 - lv.get_width()//2, 10))

    # Progress bar + food fraction (right)
    bx, by, bw, bh = SCREEN_W - 150, 12, 130, 13
    pygame.draw.rect(surf, GRAY, (bx, by, bw, bh), border_radius=6)
    fill = int(bw * foods_this_level / FOODS_PER_LEVEL)
    if fill > 0:
        pygame.draw.rect(surf, GREEN, (bx, by, fill, bh), border_radius=6)
    # label below bar
    lbl = f_sm.render(f"Food: {foods_this_level}/{FOODS_PER_LEVEL}", True, WHITE)
    surf.blit(lbl, (bx, by + bh + 3))


# ════════════════════════════════════════════════════════
#  OVERLAY SCREENS
# ════════════════════════════════════════════════════════
def screen_menu(surf, f_title, f_med, f_sm):
    surf.fill(BG_COLOR)
    shadow = f_title.render("SNAKE", True, DARK_GREEN)
    title  = f_title.render("SNAKE", True, GREEN)
    tx = SCREEN_W//2 - title.get_width()//2
    surf.blit(shadow, (tx+4, 134)); surf.blit(title, (tx, 130))

    sub = f_sm.render("Arrow keys / WASD  ·  P = Pause", True, GRAY)
    surf.blit(sub, (SCREEN_W//2 - sub.get_width()//2, 215))

    mouse = pygame.mouse.get_pos()
    result = {}
    for text, rect in [("PLAY", (SCREEN_W//2-80, 290, 160, 50)),
                        ("EXIT", (SCREEN_W//2-80, 358, 160, 50))]:
        result[text] = draw_button(surf, f_med, text, rect,
                                   pygame.Rect(rect).collidepoint(mouse))
    return result


def screen_game_over(surf, f_title, f_med, f_sm, score, level):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 185)); surf.blit(ov, (0,0))

    t = f_title.render("GAME OVER", True, RED)
    surf.blit(t, (SCREEN_W//2 - t.get_width()//2, 150))

    for i, line in enumerate([f"Score:  {score}", f"Level:  {level}"]):
        s = f_med.render(line, True, WHITE)
        surf.blit(s, (SCREEN_W//2 - s.get_width()//2, 265 + i*46))

    mouse  = pygame.mouse.get_pos()
    result = {}
    for text, rect in [("RESTART", (SCREEN_W//2-90, 385, 180, 50)),
                        ("MENU",    (SCREEN_W//2-90, 450, 180, 50))]:
        result[text] = draw_button(surf, f_med, text, rect,
                                   pygame.Rect(rect).collidepoint(mouse))
    return result


def screen_pause(surf, f_title, f_med):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0,0,0,150)); surf.blit(ov,(0,0))
    t = f_title.render("PAUSED", True, CYAN)
    surf.blit(t, (SCREEN_W//2 - t.get_width()//2, 240))
    h = f_med.render("P  —  continue     ESC  —  menu", True, WHITE)
    surf.blit(h, (SCREEN_W//2 - h.get_width()//2, 340))


def screen_level_up(surf, f_title, f_med, level):
    """Semi-transparent banner shown briefly after levelling up."""
    ov = pygame.Surface((SCREEN_W, 130), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 170))
    surf.blit(ov, (0, SCREEN_H//2 - 65))

    t1 = f_title.render("LEVEL  UP!", True, YELLOW)
    t2 = f_med.render(f"Level {level}  ·  Speed increased!", True, WHITE)
    surf.blit(t1, (SCREEN_W//2 - t1.get_width()//2, SCREEN_H//2 - 55))
    surf.blit(t2, (SCREEN_W//2 - t2.get_width()//2, SCREEN_H//2 + 15))


# ════════════════════════════════════════════════════════
#  MAIN GAME CLASS
# ════════════════════════════════════════════════════════
class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Snake")
        self.clock  = pygame.time.Clock()

        self.f_title = pygame.font.SysFont("Arial", 56, bold=True)
        self.f_med   = pygame.font.SysFont("Arial", 26, bold=True)
        self.f_sm    = pygame.font.SysFont("Arial", 18)

        self.state = "menu"
        self.menu_btns = {}
        self.over_btns = {}
        self._init_game()

    # ── Reset ─────────────────────────────────────────
    def _init_game(self, level=1):
        self.level           = level
        self.score           = 0
        self.foods_this_lvl  = 0
        self.walls           = build_walls(self.level)
        self.snake           = Snake()
        self.food            = Food(self.snake.cells(), self.walls)
        self.game_fps        = FPS_SNAKE_BASE + (self.level - 1) * FPS_SNAKE_INC
        self.tick_ms         = 1000.0 / self.game_fps   # ms between snake steps
        self.accum           = 0.0   # accumulated ms since last step
        self.lvlup_timer     = 0     # frames to show "level up" banner

    # ── Level transition ──────────────────────────────
    def _advance_level(self):
        self.level          += 1
        self.foods_this_lvl  = 0
        self.walls           = build_walls(self.level)
        self.game_fps        = FPS_SNAKE_BASE + (self.level - 1) * FPS_SNAKE_INC
        self.tick_ms         = 1000.0 / self.game_fps
        self.lvlup_timer     = 90    # ~1.5 s at 60 fps
        # Respawn food so it doesn't land on new walls
        self.food = Food(self.snake.cells(), self.walls)

    # ── Grid & wall drawing ───────────────────────────
    def _draw_grid(self):
        # Background grid lines
        for c in range(COLS + 1):
            x = GRID_X + c * CELL
            pygame.draw.line(self.screen, GRID_COLOR,
                             (x, GRID_Y), (x, GRID_Y + ROWS*CELL))
        for r in range(ROWS + 1):
            y = GRID_Y + r * CELL
            pygame.draw.line(self.screen, GRID_COLOR,
                             (GRID_X, y), (GRID_X + COLS*CELL, y))
        # Grid border
        pygame.draw.rect(self.screen, GRID_BORDER,
                         (GRID_X, GRID_Y, COLS*CELL, ROWS*CELL), 2)
        # Wall cells
        for (c, r) in self.walls:
            x, y = cell_px(c, r)
            pygame.draw.rect(self.screen, WALL_COLOR,  (x, y, CELL, CELL))
            pygame.draw.rect(self.screen, WALL_BORDER, (x, y, CELL, CELL), 1)

    # ── Main loop ─────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS_RENDER)   # dt in ms

            # ─ Events ───────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if self.state == "playing":
                        if   event.key in (pygame.K_UP,    pygame.K_w): self.snake.set_direction( 0,-1)
                        elif event.key in (pygame.K_DOWN,  pygame.K_s): self.snake.set_direction( 0, 1)
                        elif event.key in (pygame.K_LEFT,  pygame.K_a): self.snake.set_direction(-1, 0)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d): self.snake.set_direction( 1, 0)
                        elif event.key == pygame.K_p:      self.state = "paused"
                        elif event.key == pygame.K_ESCAPE: self.state = "menu"
                    elif self.state == "paused":
                        if event.key in (pygame.K_p, pygame.K_ESCAPE):
                            self.state = "playing"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if self.state == "menu":
                        if self.menu_btns.get("PLAY", pygame.Rect(0,0,0,0)).collidepoint(pos):
                            self._init_game(); self.state = "playing"
                        elif self.menu_btns.get("EXIT", pygame.Rect(0,0,0,0)).collidepoint(pos):
                            pygame.quit(); sys.exit()
                    elif self.state == "game_over":
                        if self.over_btns.get("RESTART", pygame.Rect(0,0,0,0)).collidepoint(pos):
                            self._init_game(); self.state = "playing"
                        elif self.over_btns.get("MENU", pygame.Rect(0,0,0,0)).collidepoint(pos):
                            self.state = "menu"

            # ─ Game logic (fixed time-step) ──────────────
            if self.state == "playing":
                self.food.update()

                # Count down the level-up banner
                if self.lvlup_timer > 0:
                    self.lvlup_timer -= 1

                # Accumulate render time; fire snake step(s) when ready
                self.accum += dt
                while self.accum >= self.tick_ms:
                    self.accum -= self.tick_ms
                    self.snake.step()

                    # ── Collision checks ──────────────────
                    if self.snake.hit_border():
                        self.state = "game_over"; break
                    if self.snake.hit_wall(self.walls):
                        self.state = "game_over"; break
                    if self.snake.hit_self():
                        self.state = "game_over"; break

                    # ── Food eaten? ───────────────────────
                    if self.snake.head() == (self.food.col, self.food.row):
                        self.snake.schedule_grow()
                        self.score          += 10 * self.level
                        self.foods_this_lvl += 1
                        if self.foods_this_lvl >= FOODS_PER_LEVEL:
                            self._advance_level()
                        else:
                            # New food, not on snake or walls
                            self.food = Food(self.snake.cells(), self.walls)

            # ─ Drawing ──────────────────────────────────
            self.screen.fill(BG_COLOR)

            if self.state == "menu":
                self.menu_btns = screen_menu(
                    self.screen, self.f_title, self.f_med, self.f_sm)

            else:
                self._draw_grid()
                self.food.draw(self.screen)
                self.snake.draw(self.screen)
                draw_hud(self.screen, self.f_med, self.f_sm,
                         self.score, self.level, self.foods_this_lvl)

                # Level-up flash
                if self.state == "playing" and self.lvlup_timer > 0:
                    screen_level_up(self.screen, self.f_title, self.f_med, self.level)

                if self.state == "paused":
                    screen_pause(self.screen, self.f_title, self.f_med)
                elif self.state == "game_over":
                    self.over_btns = screen_game_over(
                        self.screen, self.f_title, self.f_med, self.f_sm,
                        self.score, self.level)

            pygame.display.flip()


# ════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    SnakeGame().run()