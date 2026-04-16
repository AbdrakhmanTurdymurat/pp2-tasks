"""
clock.py - Mickey Mouse Clock drawing logic
Draws Mickey Mouse body + animated clock hands
"""

import pygame
import math
import datetime


# ── Colour palette ──────────────────────────────────────────────────────────
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
RED    = (200,  30,  30)
YELLOW = (255, 220,  80)
SKIN   = (255, 220, 185)
GRAY   = (160, 160, 160)


def draw_clock_face(surface, cx, cy, radius):
    """Draw the clock background, tick marks, and numbers."""
    # Outer bezel
    pygame.draw.circle(surface, GRAY,  (cx, cy), radius + 12)
    pygame.draw.circle(surface, WHITE, (cx, cy), radius + 8)

    # Sunburst background
    for i in range(24):
        angle = math.radians(i * 15)
        x1 = cx + int((radius - 10) * math.sin(angle))
        y1 = cy - int((radius - 10) * math.cos(angle))
        x2 = cx + int(5 * math.sin(angle))
        y2 = cy - int(5 * math.cos(angle))
        pygame.draw.line(surface, YELLOW, (x1, y1), (x2, y2), 2)

    # Clock face fill
    pygame.draw.circle(surface, (255, 248, 210), (cx, cy), radius - 4)

    # Minute tick marks (60 marks)
    for i in range(60):
        angle = math.radians(i * 6)
        if i % 5 == 0:
            length, width, colour = 16, 3, (80, 80, 80)   # hour mark
        else:
            length, width, colour = 8, 1, (160, 160, 160) # minute mark
        x1 = cx + int((radius - 5)          * math.sin(angle))
        y1 = cy - int((radius - 5)          * math.cos(angle))
        x2 = cx + int((radius - 5 - length) * math.sin(angle))
        y2 = cy - int((radius - 5 - length) * math.cos(angle))
        pygame.draw.line(surface, colour, (x1, y1), (x2, y2), width)

    # Hour numbers
    font = pygame.font.SysFont("Arial", max(14, radius // 8), bold=True)
    for i in range(1, 13):
        angle = math.radians(i * 30)
        nx = cx + int((radius - 38) * math.sin(angle))
        ny = cy - int((radius - 38) * math.cos(angle))
        text = font.render(str(i), True, (50, 50, 50))
        surface.blit(text, text.get_rect(center=(nx, ny)))


def draw_mickey_body(surface, cx, cy, scale=1.0):
    """Draw Mickey Mouse figure centered at (cx, cy)."""
    s = scale  # shorthand

    # ── Ears ──────────────────────────────────────────────────────────────
    ear_r = int(38 * s)
    pygame.draw.circle(surface, BLACK, (cx - int(38 * s), cy - int(70 * s)), ear_r)
    pygame.draw.circle(surface, BLACK, (cx + int(38 * s), cy - int(70 * s)), ear_r)

    # ── Head ──────────────────────────────────────────────────────────────
    head_r = int(48 * s)
    pygame.draw.circle(surface, BLACK, (cx, cy - int(48 * s)), head_r)

    # Face (white oval)
    pygame.draw.ellipse(surface, WHITE,
        (cx - int(34 * s), cy - int(90 * s), int(68 * s), int(72 * s)))

    # Eyes
    eye_y = cy - int(62 * s)
    pygame.draw.circle(surface, BLACK, (cx - int(12 * s), eye_y), int(5 * s))
    pygame.draw.circle(surface, BLACK, (cx + int(12 * s), eye_y), int(5 * s))

    # Nose
    pygame.draw.ellipse(surface, BLACK,
        (cx - int(9 * s), cy - int(52 * s), int(18 * s), int(12 * s)))

    # Smile
    smile_rect = pygame.Rect(cx - int(20 * s), cy - int(44 * s), int(40 * s), int(22 * s))
    pygame.draw.arc(surface, BLACK, smile_rect, math.radians(200), math.radians(340), int(3 * s))

    # ── Torso (red shorts) ────────────────────────────────────────────────
    body_top = cy + int(2 * s)
    pygame.draw.ellipse(surface, RED,
        (cx - int(28 * s), body_top, int(56 * s), int(55 * s)))

    # Shirt buttons (white dots)
    for i in range(2):
        bx = cx + int((-6 + i * 12) * s)
        by = cy + int(18 * s)
        pygame.draw.circle(surface, WHITE, (bx, by), int(4 * s))

    # ── Legs ──────────────────────────────────────────────────────────────
    pygame.draw.rect(surface, BLACK,
        (cx - int(20 * s), cy + int(48 * s), int(14 * s), int(28 * s)))
    pygame.draw.rect(surface, BLACK,
        (cx + int(6  * s), cy + int(48 * s), int(14 * s), int(28 * s)))

    # Shoes (big white ovals)
    pygame.draw.ellipse(surface, WHITE,
        (cx - int(30 * s), cy + int(68 * s), int(28 * s), int(16 * s)))
    pygame.draw.ellipse(surface, WHITE,
        (cx + int(2  * s), cy + int(68 * s), int(28 * s), int(16 * s)))


def _hand_surface(length, width, colour):
    """Create a transparent surface with a hand drawn pointing UP from centre."""
    size = length * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    # Draw from centre upward
    pygame.draw.polygon(surf, colour, [
        (cx - width // 2, cx),
        (cx + width // 2, cx),
        (cx + width // 4, cx - length),
        (cx - width // 4, cx - length),
    ])
    # Rounded tip circle
    pygame.draw.circle(surf, colour, (cx, cx - length), width // 4 + 1)
    return surf, cx, cx


def draw_hand(surface, cx, cy, length, width, colour, angle_deg):
    """Draw a rotated clock hand.  angle_deg: 0 = 12 o'clock, clockwise positive."""
    hand_surf, ox, oy = _hand_surface(length, width, colour)
    rotated = pygame.transform.rotate(hand_surf, -angle_deg)   # pygame rotates CCW
    rect = rotated.get_rect(center=(cx, cy))
    surface.blit(rotated, rect)


def draw_clock(surface, cx, cy, radius):
    """Main draw function called each frame."""
    now = datetime.datetime.now()
    minutes = now.minute
    seconds = now.second

    draw_clock_face(surface, cx, cy, radius)
    draw_mickey_body(surface, cx, cy, scale=radius / 130)

    # ── Minute hand (right arm of Mickey) ─────────────────────────────────
    min_angle = minutes * 6 + seconds * 0.1        # 6° per minute
    draw_hand(surface, cx, cy, int(radius * 0.60), 8, (40, 40, 40), min_angle)

    # ── Second hand (left arm of Mickey) ──────────────────────────────────
    sec_angle = seconds * 6                         # 6° per second
    draw_hand(surface, cx, cy, int(radius * 0.70), 4, RED, sec_angle)

    # Centre cap
    pygame.draw.circle(surface, BLACK, (cx, cy), 8)
    pygame.draw.circle(surface, WHITE, (cx, cy), 4)

    # Digital readout
    font = pygame.font.SysFont("Courier New", max(18, radius // 7), bold=True)
    time_str = now.strftime("%H:%M:%S")
    text = font.render(time_str, True, (50, 50, 50))
    surface.blit(text, text.get_rect(center=(cx, cy + radius + 22)))