import pygame
import random
import sys
import math

SCREEN_W, SCREEN_H = 480, 660
FPS = 60

# Color palette (dark theme + accent)
BG_COLOR     = (12,  12,  22 )
BLACK        = (0,   0,   0  )
WHITE        = (255, 255, 255)
GRAY         = (80,  80,  100)
DARK_GRAY    = (30,  30,  45 )
ROAD_COLOR   = (38,  38,  50 )
ROAD_EDGE    = (200, 200, 220)
LANE_COLOR   = (90,  90,  110)
GRASS_DARK   = (15,  55,  15 )
GRASS_LIGHT  = (20,  70,  20 )
RED          = (220, 55,  55 )
BLUE         = (55,  110, 230)
BLUE_LIGHT   = (80,  160, 255)
YELLOW       = (255, 215, 0  )
YELLOW_DARK  = (200, 165, 0  )
GREEN        = (55,  200, 80 )
ORANGE       = (255, 145, 0  )
CYAN         = (0,   210, 215)
PURPLE       = (160, 50,  210)

# Road geometry
ROAD_LEFT  = 80
ROAD_RIGHT = 400
ROAD_W     = ROAD_RIGHT - ROAD_LEFT   # 320
LANE_COUNT = 3
LANE_W     = ROAD_W // LANE_COUNT     # ~106

# X-centre of each lane
LANE_X = [ROAD_LEFT + LANE_W * i + LANE_W // 2 for i in range(LANE_COUNT)]

# Gameplay tuning
BASE_SPEED       = 4.0    # initial scroll speed (px/frame)
SPEED_PER_LEVEL  = 0.6    # extra speed per level
SCORE_PER_LEVEL  = 600    # score threshold to advance a level
ENEMY_INTERVAL   = 85     # frames between enemy spawns
COIN_INTERVAL    = 110    # frames between coin spawns (centre value)
COIN_SCORE       = 50     # score for collecting a coin
SURVIVE_SCORE    = 1      # score per frame of survival


# ════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════
def draw_rrect(surface, color, rect, radius=10, alpha=255):
    """Draw a rounded rectangle with optional transparency."""
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]),
                     border_radius=radius)
    surface.blit(s, (rect[0], rect[1]))


def draw_button(surface, font, text, rect, hovered):
    """Draw a styled button; return its Rect."""
    base  = (45, 100, 200)
    hover = (65, 135, 255)
    draw_rrect(surface, hover if hovered else base, rect, radius=12)
    # subtle shadow
    pygame.draw.rect(surface, (20, 55, 130),
                     (rect[0]+2, rect[1]+2, rect[2], rect[3]),
                     border_radius=12, width=0)
    draw_rrect(surface, hover if hovered else base, rect, radius=12)
    t = font.render(text, True, WHITE)
    surface.blit(t, (rect[0] + rect[2]//2 - t.get_width()//2,
                     rect[1] + rect[3]//2 - t.get_height()//2))
    return pygame.Rect(rect)


# ════════════════════════════════════════════════════════
#  PARTICLE  (spawned when coin is collected)
# ════════════════════════════════════════════════════════
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.color = color
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(1.5, 4.5)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.life = self.max_life = random.randint(22, 36)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12   # gravity
        self.life -= 1

    def draw(self, surf):
        a = int(255 * self.life / self.max_life)
        sz = max(1, int(5 * self.life / self.max_life))
        s = pygame.Surface((sz*2, sz*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, a), (sz, sz), sz)
        surf.blit(s, (int(self.x)-sz, int(self.y)-sz))


# ════════════════════════════════════════════════════════
#  ROAD  (scrolling lane markings + grass)
# ════════════════════════════════════════════════════════
class Road:
    DASH_H   = 42   # height of one lane dash
    DASH_GAP = 28   # gap between dashes
    DASH_W   = 6    # width of lane marker

    def __init__(self):
        self.scroll = 0.0   # current scroll offset

    def update(self, speed):
        """Advance scroll position; wrap when one cycle passes."""
        cycle = self.DASH_H + self.DASH_GAP
        self.scroll = (self.scroll + speed) % cycle

    def draw(self, surf):
        # ── Grass strips ──
        surf.fill(GRASS_DARK, (0, 0, ROAD_LEFT, SCREEN_H))
        surf.fill(GRASS_DARK, (ROAD_RIGHT, 0, SCREEN_W - ROAD_RIGHT, SCREEN_H))
        # Grass accent stripes
        for x_off, w in [(0, 14), (ROAD_LEFT - 14, 14),
                         (ROAD_RIGHT, 14), (SCREEN_W - 14, 14)]:
            surf.fill(GRASS_LIGHT, (x_off, 0, w, SCREEN_H))

        # ── Road surface ──
        surf.fill(ROAD_COLOR, (ROAD_LEFT, 0, ROAD_W, SCREEN_H))

        # ── Edge lines ──
        pygame.draw.rect(surf, ROAD_EDGE, (ROAD_LEFT,  0, 4, SCREEN_H))
        pygame.draw.rect(surf, ROAD_EDGE, (ROAD_RIGHT-4, 0, 4, SCREEN_H))

        # ── Dashed lane dividers ──
        cycle = self.DASH_H + self.DASH_GAP
        for lane in range(1, LANE_COUNT):
            lx = ROAD_LEFT + lane * LANE_W - self.DASH_W // 2
            y = -self.DASH_H + self.scroll
            while y < SCREEN_H:
                pygame.draw.rect(surf, LANE_COLOR,
                                 (lx, int(y), self.DASH_W, self.DASH_H))
                y += cycle


# ════════════════════════════════════════════════════════
#  PLAYER CAR
# ════════════════════════════════════════════════════════
class PlayerCar:
    W = 36
    H = 62

    def __init__(self):
        self.lane     = 1          # starting lane (centre)
        self.x        = float(LANE_X[self.lane])
        self.y        = float(SCREEN_H - 130)
        self.target_x = self.x
        self.color    = BLUE

    def try_move(self, direction):
        """Move one lane left or right if possible."""
        if direction == "left"  and self.lane > 0:
            self.lane -= 1
        elif direction == "right" and self.lane < LANE_COUNT - 1:
            self.lane += 1
        self.target_x = float(LANE_X[self.lane])

    def update(self):
        """Smooth lateral slide towards target lane."""
        self.x += (self.target_x - self.x) * 0.18
        if abs(self.target_x - self.x) < 0.5:
            self.x = self.target_x

    def get_rect(self):
        return pygame.Rect(int(self.x) - self.W//2,
                           int(self.y) - self.H//2,
                           self.W, self.H)

    def draw(self, surf):
        self._draw_car(surf, int(self.x), int(self.y), self.color)

    @staticmethod
    def _draw_car(surf, cx, cy, color):
        """Shared car-drawing routine for player & enemies."""
        hw, hh = PlayerCar.W//2, PlayerCar.H//2
        # Body
        pygame.draw.rect(surf, color,
                         (cx-hw, cy-hh, PlayerCar.W, PlayerCar.H),
                         border_radius=9)
        # Windshield (front = top of screen)
        pygame.draw.rect(surf, (*CYAN[:2], 200),
                         (cx-hw+5, cy-hh+7, PlayerCar.W-10, 15),
                         border_radius=5)
        # Rear window
        pygame.draw.rect(surf, (*CYAN[:2], 150),
                         (cx-hw+5, cy+hh-22, PlayerCar.W-10, 13),
                         border_radius=5)
        # Headlights (two small yellow rects at top)
        for ox in (-hw+3, hw-11):
            pygame.draw.rect(surf, YELLOW, (cx+ox, cy-hh+2, 8, 5), border_radius=2)
        # Taillights (red at bottom)
        for ox in (-hw+3, hw-11):
            pygame.draw.rect(surf, RED, (cx+ox, cy+hh-7, 8, 5), border_radius=2)
        # Wheels
        wheel_color = (20, 20, 30)
        for wx, wy in [(-hw-2, -hh+6), (hw-8, -hh+6),
                       (-hw-2, hh-20), (hw-8, hh-20)]:
            pygame.draw.rect(surf, wheel_color,
                             (cx+wx, cy+wy, 10, 18), border_radius=4)


# ════════════════════════════════════════════════════════
#  ENEMY CAR
# ════════════════════════════════════════════════════════
ENEMY_COLORS = [RED, ORANGE, GREEN, PURPLE, (200, 80, 40)]

class EnemyCar:
    def __init__(self, speed, occupied_lanes):
        # Choose a lane not already occupied at the top
        free = [l for l in range(LANE_COUNT) if l not in occupied_lanes]
        self.lane = random.choice(free) if free else random.randint(0, LANE_COUNT-1)
        self.x    = float(LANE_X[self.lane])
        self.y    = float(-PlayerCar.H)
        self.speed = speed
        self.color = random.choice(ENEMY_COLORS)

    def update(self):
        self.y += self.speed

    def off_screen(self):
        return self.y > SCREEN_H + PlayerCar.H

    def get_rect(self):
        return pygame.Rect(int(self.x) - PlayerCar.W//2,
                           int(self.y) - PlayerCar.H//2,
                           PlayerCar.W, PlayerCar.H)

    def draw(self, surf):
        PlayerCar._draw_car(surf, int(self.x), int(self.y), self.color)


# ════════════════════════════════════════════════════════
#  COIN
# ════════════════════════════════════════════════════════
class Coin:
    R = 11   # coin radius

    def __init__(self, speed, occupied_lanes):
        free = [l for l in range(LANE_COUNT) if l not in occupied_lanes]
        self.lane  = random.choice(free) if free else random.randint(0, LANE_COUNT-1)
        self.x     = float(LANE_X[self.lane])
        self.y     = float(-self.R * 2)
        self.speed = speed * 0.65   # coins scroll slower than cars
        self.phase = random.uniform(0, 360)   # for pulse animation

    def update(self):
        self.y    += self.speed
        self.phase = (self.phase + 3) % 360

    def off_screen(self):
        return self.y > SCREEN_H + self.R * 2

    def get_rect(self):
        return pygame.Rect(int(self.x) - self.R, int(self.y) - self.R,
                           self.R*2, self.R*2)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        # Outer glow (soft surface)
        g = pygame.Surface((self.R*4, self.R*4), pygame.SRCALPHA)
        pygame.draw.circle(g, (255, 215, 0, 55), (self.R*2, self.R*2), self.R*2)
        surf.blit(g, (cx - self.R*2, cy - self.R*2))
        # Coin body
        pygame.draw.circle(surf, YELLOW,      (cx, cy), self.R)
        pygame.draw.circle(surf, YELLOW_DARK, (cx, cy), self.R, 2)
        # Shine highlight
        pygame.draw.circle(surf, WHITE, (cx - 3, cy - 3), 3)


# ════════════════════════════════════════════════════════
#  HUD
# ════════════════════════════════════════════════════════
class HUD:
    def __init__(self, font_med, font_small):
        self.fm = font_med
        self.fs = font_small

    def draw(self, surf, score, coins, level):
        # Translucent header bar
        bar = pygame.Surface((SCREEN_W, 52), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 160))
        surf.blit(bar, (0, 0))

        # Score — top left (clear of grass)
        s = self.fm.render(f"Score: {score}", True, WHITE)
        surf.blit(s, (ROAD_LEFT + 5, 12))

        # Level — top centre
        lv = self.fm.render(f"Level {level}", True, CYAN)
        surf.blit(lv, (SCREEN_W//2 - lv.get_width()//2, 12))

        # Coins — top right with small icon
        coin_x = SCREEN_W - 105
        pygame.draw.circle(surf, YELLOW, (coin_x + 10, 26), 10)
        pygame.draw.circle(surf, WHITE,  (coin_x + 7,  23),  3)
        c = self.fm.render(f"× {coins}", True, YELLOW)
        surf.blit(c, (coin_x + 24, 12))


# ════════════════════════════════════════════════════════
#  GAME SCREENS
# ════════════════════════════════════════════════════════
def screen_menu(surf, f_title, f_med, f_small):
    surf.fill(BG_COLOR)
    # Title with glow shadow
    shadow = f_title.render("RACER", True, (0, 80, 120))
    title  = f_title.render("RACER", True, CYAN)
    tx = SCREEN_W//2 - title.get_width()//2
    surf.blit(shadow, (tx+4, 154))
    surf.blit(title,  (tx,   150))

    sub = f_small.render("Top-Down  ·  Dodge Cars  ·  Collect Coins", True, GRAY)
    surf.blit(sub, (SCREEN_W//2 - sub.get_width()//2, 235))

    mouse   = pygame.mouse.get_pos()
    btns_def = [("PLAY", (SCREEN_W//2-80, 310, 160, 50)),
                ("EXIT", (SCREEN_W//2-80, 378, 160, 50))]
    result  = {}
    for text, r in btns_def:
        result[text] = draw_button(surf, f_med, text, r,
                                   pygame.Rect(r).collidepoint(mouse))
    return result


def screen_game_over(surf, f_title, f_med, f_small, score, coins, level):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    surf.blit(overlay, (0, 0))

    t = f_title.render("GAME OVER", True, RED)
    surf.blit(t, (SCREEN_W//2 - t.get_width()//2, 155))

    for i, line in enumerate([f"Score:   {score}",
                               f"Coins:   {coins}",
                               f"Level:   {level}"]):
        s = f_med.render(line, True, WHITE)
        surf.blit(s, (SCREEN_W//2 - s.get_width()//2, 265 + i*44))

    mouse  = pygame.mouse.get_pos()
    btns_d = [("RESTART", (SCREEN_W//2-90, 425, 180, 50)),
              ("MENU",    (SCREEN_W//2-90, 490, 180, 50))]
    result = {}
    for text, r in btns_d:
        result[text] = draw_button(surf, f_med, text, r,
                                   pygame.Rect(r).collidepoint(mouse))
    return result


def screen_pause(surf, f_title, f_med):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    surf.blit(overlay, (0, 0))
    t = f_title.render("PAUSED", True, CYAN)
    surf.blit(t, (SCREEN_W//2 - t.get_width()//2, 260))
    h = f_med.render("P  —  resume     ESC  —  menu", True, WHITE)
    surf.blit(h, (SCREEN_W//2 - h.get_width()//2, 360))


# ════════════════════════════════════════════════════════
#  MAIN GAME CLASS
# ════════════════════════════════════════════════════════
class RacerGame:
    STATE_MENU      = "menu"
    STATE_PLAYING   = "playing"
    STATE_PAUSED    = "paused"
    STATE_GAME_OVER = "game_over"

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Racer")
        self.clock  = pygame.time.Clock()

        # Font hierarchy
        self.f_title = pygame.font.SysFont("Arial", 60, bold=True)
        self.f_med   = pygame.font.SysFont("Arial", 28, bold=True)
        self.f_small = pygame.font.SysFont("Arial", 19)
        self.hud     = HUD(self.f_med, self.f_small)

        self.state    = self.STATE_MENU
        self.menu_btns = {}
        self.over_btns = {}
        self._new_game()

    # ── Game reset ───────────────────────────────────────
    def _new_game(self):
        self.player       = PlayerCar()
        self.road         = Road()
        self.enemies      = []
        self.coins        = []
        self.particles    = []
        self.score        = 0
        self.coin_count   = 0
        self.level        = 1
        self.speed        = BASE_SPEED
        self.enemy_timer  = 0
        self.coin_timer   = 0
        self.key_cooldown = 0   # frames between allowed lane changes

    # ── Spawn helpers ────────────────────────────────────
    def _occupied_lanes_near_top(self):
        """Return set of lanes already occupied near the top of screen."""
        return {e.lane for e in self.enemies if e.y < 120} | \
               {c.lane for c in self.coins   if c.y < 120}

    def _spawn_enemy(self):
        occ = self._occupied_lanes_near_top()
        self.enemies.append(EnemyCar(self.speed * 0.82, occ))

    def _spawn_coin(self):
        """Randomly add a coin to a free lane."""
        occ = self._occupied_lanes_near_top()
        self.coins.append(Coin(self.speed, occ))

    # ── Collision detection ──────────────────────────────
    def _check_collisions(self):
        p = self.player.get_rect()

        # Player touches enemy → game over
        for enemy in self.enemies:
            if p.colliderect(enemy.get_rect()):
                self.state = self.STATE_GAME_OVER
                return

        # Player touches coin → collect
        for coin in self.coins[:]:
            if p.colliderect(coin.get_rect()):
                self.coins.remove(coin)
                self.coin_count += 1
                self.score += COIN_SCORE
                # Burst of sparkle particles
                for _ in range(14):
                    self.particles.append(
                        Particle(coin.x, coin.y, YELLOW))

    # ── Level progression ────────────────────────────────
    def _update_level(self):
        new_lvl = 1 + self.score // SCORE_PER_LEVEL
        if new_lvl > self.level:
            self.level = new_lvl
            self.speed = BASE_SPEED + (self.level - 1) * SPEED_PER_LEVEL

    # ── Main loop ────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(FPS)

            # ─ Events ─────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if self.state == self.STATE_PLAYING:
                        if   event.key == pygame.K_p:     self.state = self.STATE_PAUSED
                        elif event.key == pygame.K_ESCAPE: self.state = self.STATE_MENU
                    elif self.state == self.STATE_PAUSED:
                        if event.key in (pygame.K_p, pygame.K_ESCAPE):
                            self.state = self.STATE_PLAYING

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    p = event.pos
                    if self.state == self.STATE_MENU:
                        if self.menu_btns.get("PLAY", pygame.Rect(0,0,0,0)).collidepoint(p):
                            self._new_game(); self.state = self.STATE_PLAYING
                        elif self.menu_btns.get("EXIT", pygame.Rect(0,0,0,0)).collidepoint(p):
                            pygame.quit(); sys.exit()
                    elif self.state == self.STATE_GAME_OVER:
                        if self.over_btns.get("RESTART", pygame.Rect(0,0,0,0)).collidepoint(p):
                            self._new_game(); self.state = self.STATE_PLAYING
                        elif self.over_btns.get("MENU", pygame.Rect(0,0,0,0)).collidepoint(p):
                            self.state = self.STATE_MENU

            # ─ Continuous key input ────────────────────────
            if self.state == self.STATE_PLAYING:
                keys = pygame.key.get_pressed()
                if self.key_cooldown <= 0:
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        self.player.try_move("left");  self.key_cooldown = 14
                    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        self.player.try_move("right"); self.key_cooldown = 14
                else:
                    self.key_cooldown -= 1

            # ─ Game logic ──────────────────────────────────
            if self.state == self.STATE_PLAYING:
                self.player.update()
                self.road.update(self.speed)
                self.score += SURVIVE_SCORE

                # Enemy spawning
                self.enemy_timer += 1
                if self.enemy_timer >= ENEMY_INTERVAL:
                    self._spawn_enemy()
                    self.enemy_timer = 0

                # Coin spawning (with slight randomness)
                self.coin_timer += 1
                next_coin = COIN_INTERVAL + random.randint(-18, 18)
                if self.coin_timer >= next_coin:
                    self._spawn_coin()
                    self.coin_timer = 0

                # Update & cull enemies
                for e in self.enemies[:]:
                    e.update()
                    if e.off_screen(): self.enemies.remove(e)

                # Update & cull coins
                for c in self.coins[:]:
                    c.update()
                    if c.off_screen(): self.coins.remove(c)

                # Update & cull particles
                for p in self.particles[:]:
                    p.update()
                    if p.life <= 0: self.particles.remove(p)

                self._check_collisions()
                self._update_level()

            # ─ Drawing ─────────────────────────────────────
            self.screen.fill(BG_COLOR)

            if self.state == self.STATE_MENU:
                self.menu_btns = screen_menu(
                    self.screen, self.f_title, self.f_med, self.f_small)

            else:
                # Road + game objects (drawn even during pause/game-over)
                self.road.draw(self.screen)
                for c in self.coins:    c.draw(self.screen)
                for e in self.enemies:  e.draw(self.screen)
                for p in self.particles: p.draw(self.screen)
                self.player.draw(self.screen)
                self.hud.draw(self.screen, self.score,
                              self.coin_count, self.level)

                if self.state == self.STATE_PAUSED:
                    screen_pause(self.screen, self.f_title, self.f_med)

                elif self.state == self.STATE_GAME_OVER:
                    self.over_btns = screen_game_over(
                        self.screen, self.f_title, self.f_med, self.f_small,
                        self.score, self.coin_count, self.level)

            pygame.display.flip()


# ════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    RacerGame().run()