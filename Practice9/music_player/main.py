

import pygame
import sys
import os
import struct
import wave
import math
from player import Player

WIDTH, HEIGHT = 600, 420
FPS = 30


BG         = (18,  18,  30)
PANEL      = (30,  30,  50)
ACCENT     = (100, 200, 255)
WHITE      = (255, 255, 255)
GRAY       = (140, 140, 160)
DARK_GRAY  = (60,  60,  80)
GREEN      = (80,  200, 120)
RED_C      = (255, 80,  80)


def generate_demo_wav(path, frequency=440, duration=3, volume=0.3):
    
    sample_rate = 44100
    n_samples   = int(sample_rate * duration)
    wav_file = wave.open(path, "w")
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)      
    wav_file.setframerate(sample_rate)
    for i in range(n_samples):
        val = int(volume * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        wav_file.writeframes(struct.pack("<h", val))
    wav_file.close()


def ensure_demo_tracks(music_dir):
   
    os.makedirs(music_dir, exist_ok=True)
    files = [f for f in os.listdir(music_dir) if f.lower().endswith((".mp3", ".wav", ".ogg"))]
    if not files:
        freqs = [440, 523, 659]  
        names = ["Demo_Track_A440.wav", "Demo_Track_C523.wav", "Demo_Track_E659.wav"]
        for freq, name in zip(freqs, names):
            generate_demo_wav(os.path.join(music_dir, name), frequency=freq)


def draw_button(surface, rect, label, font, active=False):
    
    color = ACCENT if active else DARK_GRAY
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, GRAY, rect, 1, border_radius=8)
    text = font.render(label, True, WHITE)
    surface.blit(text, text.get_rect(center=rect.center))


def draw_progress_bar(surface, x, y, w, h, ratio):
    
    pygame.draw.rect(surface, DARK_GRAY, (x, y, w, h), border_radius=4)
    fill_w = int(w * max(0, min(1, ratio)))
    if fill_w > 0:
        pygame.draw.rect(surface, ACCENT, (x, y, fill_w, h), border_radius=4)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🎵 Music Player")
    clock = pygame.time.Clock()

    music_dir = os.path.join(os.path.dirname(__file__), "music")
    ensure_demo_tracks(music_dir)

    player = Player(music_dir=music_dir)

    
    font_lg  = pygame.font.SysFont("Arial", 28, bold=True)
    font_md  = pygame.font.SysFont("Arial", 20)
    font_sm  = pygame.font.SysFont("Arial", 16)
    font_key = pygame.font.SysFont("Arial", 18, bold=True)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    player.play()
                elif event.key == pygame.K_s:
                    player.stop()
                elif event.key == pygame.K_n:
                    player.next_track()
                elif event.key == pygame.K_b:
                    player.prev_track()
                elif event.key == pygame.K_q:
                    running = False

        player.check_track_ended()

        
        screen.fill(BG)

        
        pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, 70))
        title = font_lg.render("🎵  Music Player", True, ACCENT)
        screen.blit(title, (20, 20))

        
        pygame.draw.rect(screen, PANEL, (20, 90, WIDTH - 40, 90), border_radius=12)
        np_label = font_sm.render("NOW PLAYING", True, GRAY)
        screen.blit(np_label, (40, 105))
        track_name = player.get_current_name()
        track_surf = font_md.render(track_name, True, WHITE)
        screen.blit(track_surf, (40, 128))

        
        count_str = f"{player.current_index + 1} / {player.get_track_count()}"
        count_surf = font_sm.render(count_str, True, GRAY)
        screen.blit(count_surf, (WIDTH - 40 - count_surf.get_width(), 135))

   
        status_color = GREEN if player.is_playing else RED_C
        pygame.draw.circle(screen, status_color, (40, 165), 6)
        status_str = "Playing" if player.is_playing else "Stopped"
        status_surf = font_sm.render(status_str, True, status_color)
        screen.blit(status_surf, (52, 158))

       
        pos_surf = font_sm.render(player.get_position_str(), True, GRAY)
        screen.blit(pos_surf, (WIDTH - 40 - pos_surf.get_width(), 158))

       
        draw_progress_bar(screen, 40, 182, WIDTH - 80, 8, 0)

       
        controls_label = font_sm.render("KEYBOARD CONTROLS", True, GRAY)
        screen.blit(controls_label, (20, 210))

        btn_data = [
            (pygame.K_p, "P  Play",     player.is_playing),
            (pygame.K_s, "S  Stop",     not player.is_playing),
            (pygame.K_n, "N  Next",     False),
            (pygame.K_b, "B  Back",     False),
        ]
        keys_pressed = pygame.key.get_pressed()
        bw, bh, gap = 110, 48, 14
        start_x = (WIDTH - (bw * 4 + gap * 3)) // 2
        for i, (key, label, active) in enumerate(btn_data):
            rect = pygame.Rect(start_x + i * (bw + gap), 230, bw, bh)
            draw_button(screen, rect, label, font_key, active=active)

       
        pygame.draw.rect(screen, PANEL, (20, 300, WIDTH - 40, 90), border_radius=12)
        pl_title = font_sm.render("PLAYLIST", True, GRAY)
        screen.blit(pl_title, (40, 312))
        for i, name in enumerate(player.track_names):
            col = ACCENT if i == player.current_index else GRAY
            marker = "▶  " if i == player.current_index else "    "
            line = font_sm.render(f"{marker}{i + 1}. {name}", True, col)
            screen.blit(line, (40, 330 + i * 18))
            if 330 + i * 18 > 375:
                break

        
        quit_surf = font_sm.render("Q  Quit", True, DARK_GRAY)
        screen.blit(quit_surf, (WIDTH - 20 - quit_surf.get_width(), HEIGHT - 22))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
