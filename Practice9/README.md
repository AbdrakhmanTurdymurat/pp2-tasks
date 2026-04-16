# Practice 9 – Pygame Games

Three mini-projects built with **Pygame**.

## Projects

| Folder | Description | Run |
|---|---|---|
| `mickeys_clock/` | Animated Mickey Mouse clock | `python main.py` |
| `music_player/` | Keyboard-controlled music player | `python main.py` |
| `moving_ball/` | Arrow-key ball with boundary check | `python main.py` |

## Setup

```bash
pip install pygame
```

## Mickey's Clock
Draws Mickey Mouse as the clock face. His **right arm = minute hand**, **left arm = second hand**. Updates every second via `pygame.time.set_timer`.

## Music Player
Put `.mp3` / `.wav` / `.ogg` files in `music_player/music/` then run.

| Key | Action |
|---|---|
| P | Play |
| S | Stop |
| SPACE | Pause / Resume |
| N | Next track |
| B | Previous track |
| ↑ / ↓ | Volume up / down |
| Q / ESC | Quit |

## Moving Ball
Red circle (radius 25) on a white background.  
Arrow keys move it 20 px per press. Ball cannot leave the screen.  
Press **R** to reset to centre.
