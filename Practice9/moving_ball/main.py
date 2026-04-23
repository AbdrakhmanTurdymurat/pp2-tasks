

import pygame
import sys
from ball import Ball


WIDTH, HEIGHT = 600, 500
FPS = 60


WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
DARK_GRAY  = (50,  50,  50)
LIGHT_GRAY = (210, 210, 210)
BLUE       = (50,  100, 220)


def draw_hud(surface, ball, font):
    
    pos_txt = font.render(f"Position  x={ball.x}  y={ball.y}", True, DARK_GRAY)
    surface.blit(pos_txt, (10, 8))

   
    pygame.draw.rect(surface, LIGHT_GRAY, (0, HEIGHT - 30, WIDTH, 30))
    hint = font.render("Arrow keys to move  |  Q to quit", True, DARK_GRAY)
    surface.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 15)))


def draw_grid(surface):
    
    for x in range(0, WIDTH, 40):
        pygame.draw.line(surface, (235, 235, 235), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(surface, (235, 235, 235), (0, y), (WIDTH, y))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Moving Ball Game")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("Arial", 18)

    ball = Ball(WIDTH, HEIGHT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    ball.move_up()
                elif event.key == pygame.K_DOWN:
                    ball.move_down()
                elif event.key == pygame.K_LEFT:
                    ball.move_left()
                elif event.key == pygame.K_RIGHT:
                    ball.move_right()
                elif event.key == pygame.K_q:
                    running = False

       
        screen.fill(WHITE)
        draw_grid(screen)

        
        pygame.draw.circle(screen, LIGHT_GRAY,
                           (ball.x + 4, ball.y + 4), ball.radius)

     
        pygame.draw.circle(screen, ball.color, ball.get_pos(), ball.radius)

        pygame.draw.circle(screen, (255, 130, 130),
                           (ball.x - 8, ball.y - 8), 7)

        
        draw_hud(screen, ball, font)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
