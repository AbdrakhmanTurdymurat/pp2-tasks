import pygame
import sys
import math
from clock import Clock

WIDTH, HEIGHT = 600, 650
FPS = 30
CENTER = (WIDTH // 2, 290)

WHITE     = (255, 255, 255)
BLACK     = (0,   0,   0)
CREAM     = (255, 248, 220)
RED       = (210, 30,  30)
DARK_GRAY = (40,  40,  40)
GOLD      = (218, 165, 32)
YELLOW    = (255, 220,  0)
L_GRAY    = (190, 190, 190)
SKIN      = (255, 218, 170)


def draw_clock_face(surface, cx, cy, radius):
    pygame.draw.circle(surface, DARK_GRAY, (cx, cy), radius + 14)
    pygame.draw.circle(surface, CREAM, (cx, cy), radius)
    for i in range(24):
        a = math.radians(i * 15)
        x1 = cx + int((radius - 18) * math.sin(a))
        y1 = cy - int((radius - 18) * math.cos(a))
        x2 = cx + int(radius * math.sin(a))
        y2 = cy - int(radius * math.cos(a))
        pygame.draw.line(surface, L_GRAY, (x1, y1), (x2, y2), 1)
    font_num = pygame.font.SysFont("Arial", 26, bold=True)
    for h in range(1, 13):
        a = math.radians(h * 30)
        nx = cx + int((radius - 42) * math.sin(a))
        ny = cy - int((radius - 42) * math.cos(a))
        lbl = font_num.render(str(h), True, DARK_GRAY)
        surface.blit(lbl, lbl.get_rect(center=(nx, ny)))
    for i in range(60):
        a = math.radians(i * 6)
        tl, tw = (14, 3) if i % 5 == 0 else (6, 1)
        x1 = cx + int((radius - 2) * math.sin(a))
        y1 = cy - int((radius - 2) * math.cos(a))
        x2 = cx + int((radius - 2 - tl) * math.sin(a))
        y2 = cy - int((radius - 2 - tl) * math.cos(a))
        pygame.draw.line(surface, DARK_GRAY, (x1, y1), (x2, y2), tw)


def make_hand(length, shaft_w, shaft_color, glove_r):
    pad = 12
    sw = max(shaft_w + 10, glove_r * 2 + 6) + pad * 2
    sh = length + glove_r * 2 + pad * 2
    surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx     = sw // 2
    tip_y  = pad + glove_r
    base_y = sh - pad
    bw = shaft_w // 2
    tw = max(2, shaft_w // 4)
    pygame.draw.polygon(surf, shaft_color, [
        (cx - bw, base_y),
        (cx + bw, base_y),
        (cx + tw, tip_y + glove_r),
        (cx - tw, tip_y + glove_r),
    ])
    pygame.draw.circle(surf, WHITE, (cx, tip_y), glove_r)
    pygame.draw.circle(surf, BLACK, (cx, tip_y), glove_r, 2)
    br = max(2, glove_r // 3)
    for ox, oy in [(-br, -glove_r // 2), (0, -glove_r + 2), (br, -glove_r // 2)]:
        pygame.draw.circle(surf, WHITE, (cx + ox, tip_y + oy), br)
        pygame.draw.circle(surf, BLACK, (cx + ox, tip_y + oy), br, 1)
    return surf, (cx, base_y)


def blit_rotated_hand(surface, hand_surf, pivot_in_surf, angle_cw, screen_pivot):
    rotated    = pygame.transform.rotate(hand_surf, -angle_cw)
    image_rect = hand_surf.get_rect(
        topleft=(screen_pivot[0] - pivot_in_surf[0],
                 screen_pivot[1] - pivot_in_surf[1])
    )
    offset         = pygame.math.Vector2(screen_pivot) - pygame.math.Vector2(image_rect.center)
    rotated_offset = offset.rotate(angle_cw)
    rotated_center = pygame.math.Vector2(screen_pivot) - rotated_offset
    blit_rect      = rotated.get_rect(center=rotated_center)
    surface.blit(rotated, blit_rect)


def draw_mickey(surface, cx, cy):
    pygame.draw.circle(surface, BLACK, (cx - 32, cy - 88), 23)
    pygame.draw.circle(surface, BLACK, (cx + 32, cy - 88), 23)
    pygame.draw.circle(surface, BLACK, (cx, cy - 62), 38)
    pygame.draw.ellipse(surface, SKIN,  pygame.Rect(cx - 20, cy - 62, 40, 30))
    pygame.draw.circle(surface, WHITE,  (cx - 14, cy - 72), 10)
    pygame.draw.circle(surface, WHITE,  (cx + 14, cy - 72), 10)
    pygame.draw.circle(surface, BLACK,  (cx - 13, cy - 72), 6)
    pygame.draw.circle(surface, BLACK,  (cx + 13, cy - 72), 6)
    pygame.draw.circle(surface, WHITE,  (cx - 11, cy - 74), 2)
    pygame.draw.circle(surface, WHITE,  (cx + 15, cy - 74), 2)
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(cx - 8,  cy - 58, 16, 10))
    pygame.draw.arc(surface, BLACK,
                    pygame.Rect(cx - 13, cy - 52, 26, 16),
                    math.pi + 0.2, 2 * math.pi - 0.2, 2)
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(cx - 30, cy - 28, 60, 68))
    pygame.draw.ellipse(surface, RED,   pygame.Rect(cx - 24, cy + 8,  48, 36))
    pygame.draw.circle(surface, GOLD,   (cx, cy - 6), 5)
    pygame.draw.circle(surface, YELLOW, (cx, cy - 6), 3)
    pygame.draw.circle(surface, GOLD,   (cx, cy + 6), 5)
    pygame.draw.circle(surface, YELLOW, (cx, cy + 6), 3)
    pygame.draw.line(surface, BLACK, (cx - 28, cy - 14), (cx - 58, cy + 12), 11)
    pygame.draw.circle(surface, WHITE,  (cx - 64, cy + 16), 13)
    pygame.draw.circle(surface, BLACK,  (cx - 64, cy + 16), 13, 2)
    pygame.draw.circle(surface, WHITE,  (cx - 73, cy + 10), 7)
    pygame.draw.circle(surface, BLACK,  (cx - 73, cy + 10), 7, 1)
    pygame.draw.circle(surface, WHITE,  (cx - 75, cy + 20), 6)
    pygame.draw.circle(surface, BLACK,  (cx - 75, cy + 20), 6, 1)
    pygame.draw.circle(surface, WHITE,  (cx - 64, cy + 4),  6)
    pygame.draw.circle(surface, BLACK,  (cx - 64, cy + 4),  6, 1)
    pygame.draw.line(surface, BLACK, (cx + 28, cy - 14), (cx + 58, cy + 12), 11)
    pygame.draw.circle(surface, WHITE,  (cx + 64, cy + 16), 13)
    pygame.draw.circle(surface, BLACK,  (cx + 64, cy + 16), 13, 2)
    pygame.draw.circle(surface, WHITE,  (cx + 73, cy + 10), 7)
    pygame.draw.circle(surface, BLACK,  (cx + 73, cy + 10), 7, 1)
    pygame.draw.circle(surface, WHITE,  (cx + 75, cy + 20), 6)
    pygame.draw.circle(surface, BLACK,  (cx + 75, cy + 20), 6, 1)
    pygame.draw.circle(surface, WHITE,  (cx + 64, cy + 4),  6)
    pygame.draw.circle(surface, BLACK,  (cx + 64, cy + 4),  6, 1)
    pygame.draw.line(surface, BLACK, (cx - 12, cy + 40), (cx - 16, cy + 68), 11)
    pygame.draw.ellipse(surface, WHITE, pygame.Rect(cx - 32, cy + 64, 34, 18))
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(cx - 32, cy + 64, 34, 18), 2)
    pygame.draw.line(surface, BLACK, (cx + 12, cy + 40), (cx + 16, cy + 68), 11)
    pygame.draw.ellipse(surface, WHITE, pygame.Rect(cx - 2,  cy + 64, 34, 18))
    pygame.draw.ellipse(surface, BLACK, pygame.Rect(cx - 2,  cy + 64, 34, 18), 2)


def main():
    pygame.init()
    screen  = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mickey's Clock")
    clk_obj = Clock()
    tick    = pygame.time.Clock()

    CLOCK_R = 230
    min_surf, min_pivot = make_hand(168, 12, DARK_GRAY, 16)
    sec_surf, sec_pivot = make_hand(195,  5, RED,        10)
    font_time = pygame.font.SysFont("Arial", 30, bold=True)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False

        screen.fill(WHITE)
        draw_clock_face(screen, *CENTER, CLOCK_R)

        now       = clk_obj.get_time()
        min_angle = clk_obj.get_minute_angle(now)
        sec_angle = clk_obj.get_second_angle(now)

        blit_rotated_hand(screen, min_surf, min_pivot, min_angle, CENTER)
        blit_rotated_hand(screen, sec_surf, sec_pivot, sec_angle, CENTER)

        draw_mickey(screen, CENTER[0], CENTER[1] + 40)

        pygame.draw.circle(screen, DARK_GRAY, CENTER, 10)
        pygame.draw.circle(screen, GOLD,      CENTER,  6)

        lbl = font_time.render(now.strftime("%H:%M:%S"), True, DARK_GRAY)
        screen.blit(lbl, lbl.get_rect(center=(WIDTH // 2, HEIGHT - 28)))

        pygame.display.flip()
        tick.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()