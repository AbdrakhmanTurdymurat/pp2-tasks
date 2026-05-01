from __future__ import annotations

import pygame

WHITE = (245, 245, 245)
BLACK = (16, 16, 16)
SOFT_BLACK = (35, 35, 35)
BLUE = (81, 132, 255)
GREEN = (70, 200, 120)
RED = (220, 86, 86)
YELLOW = (255, 205, 86)
GRAY = (165, 165, 170)
PANEL = (26, 28, 34)
PANEL_2 = (40, 43, 52)
HOVER = (70, 76, 92)

def draw_text(surface, text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)
    return rect

class Button:
    def __init__(self, rect, text, font, bg=PANEL_2, fg=WHITE, hover=HOVER, border=0):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg = bg
        self.fg = fg
        self.hover = hover
        self.border = border
        self.enabled = True

    def draw(self, surface):
        mouse = pygame.mouse.get_pos()
        active = self.rect.collidepoint(mouse) and self.enabled
        color = self.hover if active else self.bg
        pygame.draw.rect(surface, color, self.rect, border_radius=16)
        if self.border:
            pygame.draw.rect(surface, self.border, self.rect, 2, border_radius=16)
        draw_text(surface, self.text, self.font, self.fg, self.rect.centerx, self.rect.centery, center=True)

    def is_clicked(self, event):
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

class TextInput:
    def __init__(self, rect, font, placeholder="Enter name"):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.placeholder = placeholder
        self.text = ""
        self.active = False
        self.max_len = 16

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                pass
            else:
                if len(self.text) < self.max_len and event.unicode.isprintable():
                    if event.unicode not in "\r\n\t":
                        self.text += event.unicode

    def draw(self, surface):
        bg = (48, 52, 63) if self.active else (34, 38, 47)
        pygame.draw.rect(surface, bg, self.rect, border_radius=14)
        pygame.draw.rect(surface, BLUE if self.active else (90, 95, 110), self.rect, 2, border_radius=14)
        shown = self.text if self.text else self.placeholder
        color = WHITE if self.text else GRAY
        img = self.font.render(shown, True, color)
        surface.blit(img, (self.rect.x + 14, self.rect.y + (self.rect.height - img.get_height()) // 2))

    def get_value(self):
        return self.text.strip()

    def set_value(self, value):
        self.text = value[:self.max_len]
