from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pygame

from persistence import record_score
from ui import draw_text

SCREEN_W = 960
SCREEN_H = 720
ROAD_W = 420
ROAD_LEFT = (SCREEN_W - ROAD_W) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_W
LANE_COUNT = 4
LANE_W = ROAD_W / LANE_COUNT

WHITE = (245, 245, 245)
BLACK = (12, 12, 12)
ROAD = (40, 44, 52)
ROAD_EDGE = (210, 210, 210)
LINE = (245, 220, 100)
GRASS_1 = (27, 95, 42)
GRASS_2 = (24, 84, 37)

CAR_COLORS = {
    "Red": (231, 76, 60),
    "Blue": (66, 135, 245),
    "Green": (50, 205, 100),
    "Yellow": (245, 205, 65),
    "Purple": (170, 93, 220),
}

DIFFICULTY_PRESETS = {
    "Easy": {
        "speed_mul": 0.9,
        "traffic_gap": 1.35,
        "obstacle_gap": 1.70,
        "powerup_gap": 5.7,
    },
    "Normal": {
        "speed_mul": 1.0,
        "traffic_gap": 1.10,
        "obstacle_gap": 1.45,
        "powerup_gap": 6.2,
    },
    "Hard": {
        "speed_mul": 1.16,
        "traffic_gap": 0.92,
        "obstacle_gap": 1.18,
        "powerup_gap": 6.8,
    },
}

ROAD_EVENT_TYPES = ("moving_barrier", "speed_bump", "nitro_strip")
POWERUP_TYPES = ("nitro", "shield", "repair")
COIN_VALUES = (1, 2, 5)
HAZARD_TYPES = ("oil", "slow", "pothole")

def lane_center(lane: int) -> float:
    return ROAD_LEFT + lane * LANE_W + LANE_W / 2

def clamp(value, lo, hi):
    return max(lo, min(hi, value))

@dataclass
class SpawnedObject:
    kind: str
    lane: int
    rect: pygame.Rect
    speed: float
    ttl: float | None = None
    value: int = 0
    horizontal_phase: float = 0.0
    horizontal_amp: float = 0.0
    label: str = ""

    def update(self, dt: float, road_speed: float, now: float):
        self.rect.y += int((self.speed + road_speed) * dt)
        if self.kind == "event" and self.label == "moving_barrier":
            self.horizontal_phase += dt * 3.2
            x = lane_center(self.lane) - self.rect.width / 2 + math.sin(self.horizontal_phase) * self.horizontal_amp
            self.rect.x = int(clamp(x, ROAD_LEFT + 8, ROAD_RIGHT - self.rect.width - 8))
        if self.ttl is not None:
            self.ttl -= dt

    def expired(self):
        return self.ttl is not None and self.ttl <= 0

class Player:
    def __init__(self, color_name: str):
        self.color_name = color_name
        self.color = CAR_COLORS[color_name]
        self.lane = 1
        self.width = 44
        self.height = 82
        self.y = SCREEN_H - 115
        self.x = int(lane_center(self.lane) - self.width / 2)
        self.shield = False
        self.repair_ready = False
        self.nitro_until = 0.0
        self.slow_until = 0.0
        self.oil_until = 0.0
        self.ghost_until = 0.0
        self.distance = 0.0
        self.score = 0
        self.coins = 0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def move_left(self):
        self.lane = max(0, self.lane - 1)
        self.x = int(lane_center(self.lane) - self.width / 2)

    def move_right(self):
        self.lane = min(LANE_COUNT - 1, self.lane + 1)
        self.x = int(lane_center(self.lane) - self.width / 2)

    def speed_multiplier(self, now: float) -> float:
        mult = 1.0
        if now < self.nitro_until:
            mult *= 1.45
        if now < self.slow_until:
            mult *= 0.72
        if now < self.oil_until:
            mult *= 0.84
        if now < self.ghost_until:
            mult *= 1.08
        return mult

    def active_powerup(self, now: float) -> tuple[str | None, float | None]:
        if now < self.nitro_until:
            return "Nitro", self.nitro_until - now
        if self.shield:
            return "Shield", None
        if self.repair_ready:
            return "Repair", None
        return None, None

    def apply_powerup(self, powerup: str, now: float) -> bool:
        if self.has_active_powerup(now):
            return False
        if powerup == "nitro":
            self.nitro_until = now + 4.0
        elif powerup == "shield":
            self.shield = True
        elif powerup == "repair":
            self.repair_ready = True
        return True

    def has_active_powerup(self, now: float) -> bool:
        return now < self.nitro_until or self.shield or self.repair_ready

    def consume_shield(self):
        self.shield = False

    def consume_repair(self):
        self.repair_ready = False

    def draw(self, surface):
        shadow_rect = self.rect.move(6, 8)
        shadow = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 70))
        surface.blit(shadow, shadow_rect.topleft)

        body = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, body, border_radius=10)
        pygame.draw.rect(surface, (250, 250, 250), body.inflate(-18, -28), 2, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 20), (self.x + 8, self.y + 10, self.width - 16, 20), border_radius=6)
        pygame.draw.rect(surface, (20, 20, 20), (self.x + 8, self.y + 48, self.width - 16, 24), border_radius=6)
        wheel_w = 10
        wheel_h = 16
        for wx, wy in ((self.x - 4, self.y + 10), (self.x + self.width - 6, self.y + 10),
                       (self.x - 4, self.y + self.height - 26), (self.x + self.width - 6, self.y + self.height - 26)):
            pygame.draw.rect(surface, (18, 18, 18), (wx, wy, wheel_w, wheel_h), border_radius=3)

        if self.shield:
            pygame.draw.ellipse(surface, (100, 210, 255), body.inflate(26, 26), 3)
        if self.repair_ready:
            pygame.draw.circle(surface, (255, 165, 70), (body.centerx, body.centery), 32, 3)

class RaceGame:
    def __init__(self, settings: dict, username: str, leaderboard_path: Path):
        self.settings = settings
        self.username = username or "Player"
        self.leaderboard_path = leaderboard_path
        self.difficulty = settings.get("difficulty", "Normal")
        self.preset = DIFFICULTY_PRESETS.get(self.difficulty, DIFFICULTY_PRESETS["Normal"])
        self.player = Player(settings.get("car_color", "Red"))
        self.reset()

    def reset(self):
        self.player = Player(self.settings.get("car_color", "Red"))
        self.objects: list[SpawnedObject] = []
        self.road_offset = 0.0
        self.elapsed = 0.0
        self.base_speed = 260.0 * self.preset["speed_mul"]
        self.distance_goal = 5200
        self.traffic_timer = 0.7
        self.obstacle_timer = 0.8
        self.powerup_timer = 2.0
        self.coin_timer = 0.4
        self.event_timer = 1.5
        self.hazard_timer = 2.0
        self.game_over = False
        self.finished = False
        self.reason = ""
        self.invincible_until = 0.0
        self.road_boost_until = 0.0
        self.speed_bump_until = 0.0
        self.notifications: list[tuple[str, float]] = []
        self.saved_to_leaderboard = False

    def add_notification(self, text: str, duration: float = 1.5):
        self.notifications.append((text, duration))

    def current_speed(self, now: float) -> float:
        speed = self.base_speed + min(240, self.player.distance / 24)
        if now < self.road_boost_until:
            speed *= 1.25
        if now < self.speed_bump_until:
            speed *= 0.82
        speed *= self.player.speed_multiplier(now)
        if self.player.ghost_until > now:
            speed *= 1.03
        return speed

    def spawn_lane(self, player_lane_safe=True) -> int:
        choices = list(range(LANE_COUNT))
        if player_lane_safe and self.player.lane in choices and random.random() < 0.72:
            choices.remove(self.player.lane)
        if not choices:
            choices = list(range(LANE_COUNT))
        return random.choice(choices)

    def lane_is_clear(self, lane: int, y: int, min_gap: int = 120) -> bool:
        for obj in self.objects:
            if obj.lane == lane and abs(obj.rect.y - y) < min_gap:
                return False
        return True

    def spawn_traffic(self, now: float):
        lane = self.spawn_lane(player_lane_safe=True)
        y = -110
        if not self.lane_is_clear(lane, y):
            lane = (lane + 1) % LANE_COUNT
        w, h = 44, 86
        rect = pygame.Rect(int(lane_center(lane) - w / 2), y, w, h)
        speed = random.uniform(0, 35) + self.current_speed(now) * 0.18
        self.objects.append(SpawnedObject("traffic", lane, rect, speed, ttl=12.0, label="traffic"))

    def spawn_obstacle(self, now: float):
        lane = self.spawn_lane(player_lane_safe=False)
        y = -90
        kind = random.choices(["barrier", "oil", "pothole"], weights=[0.42, 0.31, 0.27])[0]
        if not self.lane_is_clear(lane, y, 90):
            lane = (lane + 1) % LANE_COUNT
        if kind == "barrier":
            rect = pygame.Rect(int(lane_center(lane) - 28), y, 56, 56)
            speed = self.current_speed(now) * 0.10
        elif kind == "oil":
            rect = pygame.Rect(int(lane_center(lane) - 34), y, 68, 44)
            speed = self.current_speed(now) * 0.04
        else:
            rect = pygame.Rect(int(lane_center(lane) - 28), y, 56, 42)
            speed = self.current_speed(now) * 0.08
        self.objects.append(SpawnedObject("obstacle", lane, rect, speed, ttl=13.0, label=kind))

    def spawn_powerup(self, now: float):
        active = self.player.active_powerup(now)[0]
        if active is not None:
            return
        lane = self.spawn_lane(player_lane_safe=False)
        y = -80
        if not self.lane_is_clear(lane, y, 90):
            lane = (lane + 1) % LANE_COUNT
        power = random.choice(list(POWERUP_TYPES))
        rect = pygame.Rect(int(lane_center(lane) - 18), y, 36, 36)
        speed = self.current_speed(now) * 0.06
        self.objects.append(SpawnedObject("powerup", lane, rect, speed, ttl=8.5, value=power, label=power))

    def spawn_coin(self, now: float):
        lane = self.spawn_lane(player_lane_safe=False)
        y = -70
        if not self.lane_is_clear(lane, y, 70):
            lane = (lane + 1) % LANE_COUNT
        value = random.choices(list(COIN_VALUES), weights=[68, 23, 9])[0]
        rect = pygame.Rect(int(lane_center(lane) - 14), y, 28, 28)
        speed = self.current_speed(now) * 0.05
        self.objects.append(SpawnedObject("coin", lane, rect, speed, ttl=8.0, value=value, label=str(value)))

    def spawn_event(self, now: float):
        lane = self.spawn_lane(player_lane_safe=False)
        y = -100
        event = random.choice(list(ROAD_EVENT_TYPES))
        if event == "moving_barrier":
            rect = pygame.Rect(int(lane_center(lane) - 30), y, 60, 72)
            obj = SpawnedObject("event", lane, rect, self.current_speed(now) * 0.10, ttl=11.0, label=event)
            obj.horizontal_amp = 38
            obj.horizontal_phase = random.random() * math.pi * 2
        elif event == "speed_bump":
            rect = pygame.Rect(int(lane_center(lane) - 38), y, 76, 28)
            obj = SpawnedObject("event", lane, rect, self.current_speed(now) * 0.04, ttl=11.0, label=event)
        else:
            rect = pygame.Rect(int(lane_center(lane) - 34), y, 68, 36)
            obj = SpawnedObject("event", lane, rect, self.current_speed(now) * 0.05, ttl=11.0, label=event)
        self.objects.append(obj)

    def spawn_hazard(self, now: float):
        lane = random.randrange(LANE_COUNT)
        y = -120
        hazard = random.choice(list(HAZARD_TYPES))
        if not self.lane_is_clear(lane, y, 80):
            lane = (lane + 1) % LANE_COUNT
        if hazard == "oil":
            rect = pygame.Rect(int(lane_center(lane) - 36), y, 72, 46)
            speed = self.current_speed(now) * 0.02
        elif hazard == "slow":
            rect = pygame.Rect(int(lane_center(lane) - 30), y, 60, 48)
            speed = self.current_speed(now) * 0.04
        else:
            rect = pygame.Rect(int(lane_center(lane) - 28), y, 56, 40)
            speed = self.current_speed(now) * 0.03
        self.objects.append(SpawnedObject("hazard", lane, rect, speed, ttl=12.0, label=hazard))

    def handle_hazard_collision(self, now: float) -> bool:
        if self.player.shield:
            self.player.consume_shield()
            self.add_notification("Shield saved you!")
            self.player.score += 30
            return True
        if self.player.repair_ready:
            self.player.consume_repair()
            self.invincible_until = now + 1.0
            self.player.ghost_until = now + 1.0
            self.add_notification("Repair used!")
            self.player.score += 50
            return True
        return False

    def apply_collision(self, obj: SpawnedObject, now: float) -> bool:
        if obj.kind == "powerup":
            if self.player.apply_powerup(obj.label, now):
                if obj.label == "nitro":
                    self.add_notification("Nitro activated!")
                elif obj.label == "shield":
                    self.add_notification("Shield activated!")
                elif obj.label == "repair":
                    self.add_notification("Repair ready!")
                self.player.score += 40
                return True
            return True

        if obj.kind == "event":
            if obj.label == "nitro_strip":
                self.road_boost_until = max(self.road_boost_until, now + 3.5)
                self.player.score += 25
                self.add_notification("Nitro strip!")
                return True
            if obj.label == "speed_bump":
                self.speed_bump_until = max(self.speed_bump_until, now + 2.0)
                self.player.score = max(0, self.player.score - 10)
                self.add_notification("Speed bump!")
                return True
            if obj.label == "moving_barrier":
                return self.handle_hazard_collision(now)
            return True

        if obj.kind == "hazard":
            if obj.label == "oil":
                self.player.oil_until = max(self.player.oil_until, now + 2.0)
                self.player.score = max(0, self.player.score - 8)
                self.add_notification("Oil spill!")
                return True
            if obj.label == "slow":
                self.player.slow_until = max(self.player.slow_until, now + 2.5)
                self.add_notification("Slow zone!")
                return True
            if obj.label == "pothole":
                self.player.score = max(0, self.player.score - 12)
                self.add_notification("Pothole!")
                return self.handle_hazard_collision(now)

        return self.handle_hazard_collision(now)

    def update(self, dt: float, now: float):
        if self.game_over:
            return

        self.elapsed += dt
        speed = self.current_speed(now)
        self.player.distance += speed * dt * 0.16
        self.player.score += int(speed * dt * 0.03)
        self.road_offset = (self.road_offset + speed * dt) % 80

        progress = clamp(self.player.distance / self.distance_goal, 0.0, 1.0)
        traffic_gap = max(0.42, self.preset["traffic_gap"] - progress * 0.52)
        obstacle_gap = max(0.55, self.preset["obstacle_gap"] - progress * 0.58)
        powerup_gap = max(3.5, self.preset["powerup_gap"] - progress * 2.0)
        event_gap = max(1.25, 2.4 - progress * 0.9)
        hazard_gap = max(1.1, 2.3 - progress * 0.95)

        self.traffic_timer += dt
        self.obstacle_timer += dt
        self.powerup_timer += dt
        self.coin_timer += dt
        self.event_timer += dt
        self.hazard_timer += dt

        if self.traffic_timer >= traffic_gap:
            self.traffic_timer = 0.0
            self.spawn_traffic(now)
        if self.obstacle_timer >= obstacle_gap:
            self.obstacle_timer = 0.0
            self.spawn_obstacle(now)
        if self.powerup_timer >= powerup_gap:
            self.powerup_timer = 0.0
            if random.random() < 0.9:
                self.spawn_powerup(now)
        if self.coin_timer >= max(0.16, 0.42 - progress * 0.18):
            self.coin_timer = 0.0
            self.spawn_coin(now)
        if self.event_timer >= event_gap:
            self.event_timer = 0.0
            if random.random() < 0.75:
                self.spawn_event(now)
        if self.hazard_timer >= hazard_gap:
            self.hazard_timer = 0.0
            if random.random() < 0.8:
                self.spawn_hazard(now)

        if self.player.distance >= self.distance_goal:
            self.finished = True
            self.game_over = True
            self.reason = "Finished"
            self.player.score += 500
            self._save_score()
            return

        player_rect = self.player.rect
        for obj in list(self.objects):
            obj.update(dt, speed * 0.11, now)
            if obj.expired():
                self.objects.remove(obj)
                continue
            if obj.rect.top > SCREEN_H + 50:
                self.objects.remove(obj)
                continue
            if now < self.invincible_until:
                continue
            if obj.rect.colliderect(player_rect):
                if obj.kind == "coin":
                    self.player.coins += int(obj.value)
                    self.player.score += int(obj.value * 25)
                    self.add_notification(f"+{obj.value} coin")
                    if obj in self.objects:
                        self.objects.remove(obj)
                    continue

                survived = self.apply_collision(obj, now)
                if obj in self.objects:
                    self.objects.remove(obj)
                if not survived:
                    self.game_over = True
                    self.reason = f"Hit by {obj.label or obj.kind}"
                    self._save_score()
                    return

        new_notifications = []
        for text, left in self.notifications:
            left -= dt
            if left > 0:
                new_notifications.append((text, left))
        self.notifications = new_notifications

    def _save_score(self):
        if self.saved_to_leaderboard:
            return
        self.saved_to_leaderboard = True
        entry = {
            "name": self.username,
            "score": int(self.score_value()),
            "distance": int(self.player.distance),
            "coins": int(self.player.coins),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        record_score(self.leaderboard_path, entry)

    def score_value(self, now: float | None = None) -> int:
        if now is None:
            now = pygame.time.get_ticks() / 1000.0
        power_bonus = 0
        if now < self.player.nitro_until:
            power_bonus += 50
        if self.player.shield:
            power_bonus += 60
        if self.player.repair_ready:
            power_bonus += 75
        return int(self.player.score + self.player.coins * 100 + self.player.distance * 0.7 + power_bonus)

    def draw_track(self, surface):
        surface.fill(GRASS_1)
        for y in range(0, SCREEN_H, 44):
            stripe = pygame.Rect(0, y, SCREEN_W, 22)
            pygame.draw.rect(surface, GRASS_2 if (y // 44) % 2 == 0 else GRASS_1, stripe)

        pygame.draw.rect(surface, ROAD, (ROAD_LEFT, 0, ROAD_W, SCREEN_H))
        pygame.draw.rect(surface, ROAD_EDGE, (ROAD_LEFT - 8, 0, 8, SCREEN_H))
        pygame.draw.rect(surface, ROAD_EDGE, (ROAD_RIGHT, 0, 8, SCREEN_H))

        for i in range(1, LANE_COUNT):
            x = int(ROAD_LEFT + i * LANE_W)
            dash_y = -80 + int(self.road_offset)
            while dash_y < SCREEN_H + 80:
                pygame.draw.rect(surface, LINE, (x - 4, dash_y, 8, 30), border_radius=3)
                dash_y += 60

        for y in range(-80, SCREEN_H + 80, 160):
            yy = y + int(self.road_offset * 0.8)
            pygame.draw.circle(surface, (120, 120, 140), (ROAD_LEFT + 10, yy), 4)
            pygame.draw.circle(surface, (120, 120, 140), (ROAD_RIGHT - 10, yy), 4)

        if self.player.distance >= self.distance_goal * 0.82:
            fy = int(SCREEN_H * 0.20)
            for i in range(12):
                c = WHITE if i % 2 == 0 else BLACK
                pygame.draw.rect(surface, c, (ROAD_LEFT, fy + i * 16, ROAD_W, 16))

    def draw_object(self, surface, obj: SpawnedObject):
        if obj.kind == "traffic":
            color = (110, 110, 120)
            pygame.draw.rect(surface, color, obj.rect, border_radius=8)
            pygame.draw.rect(surface, (220, 220, 230), obj.rect.inflate(-16, -20), 2, border_radius=6)
            pygame.draw.rect(surface, (25, 25, 25), (obj.rect.x + 7, obj.rect.y + 12, obj.rect.w - 14, 22), border_radius=5)
            pygame.draw.rect(surface, (25, 25, 25), (obj.rect.x + 7, obj.rect.bottom - 26, obj.rect.w - 14, 18), border_radius=5)
        elif obj.kind == "obstacle":
            if obj.label == "barrier":
                pygame.draw.rect(surface, (180, 75, 60), obj.rect, border_radius=6)
                pygame.draw.line(surface, (240, 220, 100), obj.rect.topleft, obj.rect.bottomright, 4)
                pygame.draw.line(surface, (240, 220, 100), obj.rect.topright, obj.rect.bottomleft, 4)
            elif obj.label == "oil":
                pygame.draw.ellipse(surface, (28, 28, 30), obj.rect)
                pygame.draw.ellipse(surface, (60, 60, 70), obj.rect.inflate(-14, -10), 2)
            else:
                pygame.draw.rect(surface, (110, 65, 40), obj.rect, border_radius=5)
                pygame.draw.circle(surface, (70, 40, 20), obj.rect.center, 8)
        elif obj.kind == "powerup":
            if obj.label == "nitro":
                color = (255, 95, 75)
                pygame.draw.polygon(surface, color, [
                    (obj.rect.centerx, obj.rect.top),
                    (obj.rect.right, obj.rect.centery),
                    (obj.rect.centerx + 4, obj.rect.bottom),
                    (obj.rect.left, obj.rect.centery),
                ])
            elif obj.label == "shield":
                color = (90, 200, 255)
                pygame.draw.circle(surface, color, obj.rect.center, 18)
                pygame.draw.circle(surface, (230, 250, 255), obj.rect.center, 10, 2)
            else:
                color = (255, 185, 80)
                pygame.draw.rect(surface, color, obj.rect, border_radius=8)
                pygame.draw.rect(surface, (255, 245, 210), obj.rect.inflate(-16, -16), 2, border_radius=6)
        elif obj.kind == "event":
            if obj.label == "moving_barrier":
                pygame.draw.rect(surface, (200, 90, 60), obj.rect, border_radius=8)
                pygame.draw.rect(surface, (255, 230, 110), obj.rect.inflate(-18, -18), 3, border_radius=6)
            elif obj.label == "speed_bump":
                pygame.draw.rect(surface, (95, 62, 40), obj.rect, border_radius=6)
                for i in range(4):
                    pygame.draw.line(surface, (150, 110, 80), (obj.rect.x + 8 + i * 16, obj.rect.y + 5), (obj.rect.x + 12 + i * 16, obj.rect.bottom - 5), 2)
            else:
                pygame.draw.rect(surface, (255, 170, 50), obj.rect, border_radius=6)
                pygame.draw.polygon(surface, (255, 240, 190), [
                    (obj.rect.left + 10, obj.rect.centery),
                    (obj.rect.centerx, obj.rect.top + 4),
                    (obj.rect.right - 10, obj.rect.centery),
                    (obj.rect.centerx, obj.rect.bottom - 4),
                ])
        elif obj.kind == "hazard":
            if obj.label == "oil":
                pygame.draw.ellipse(surface, (20, 20, 24), obj.rect)
                pygame.draw.ellipse(surface, (65, 65, 75), obj.rect.inflate(-12, -8), 2)
            elif obj.label == "slow":
                pygame.draw.rect(surface, (70, 150, 160), obj.rect, border_radius=6)
                pygame.draw.line(surface, (220, 250, 250), obj.rect.topleft, obj.rect.bottomright, 3)
            else:
                pygame.draw.rect(surface, (85, 85, 95), obj.rect, border_radius=6)
                pygame.draw.circle(surface, (30, 30, 32), obj.rect.center, 7)

    def draw(self, surface, font, small_font):
        self.draw_track(surface)

        for obj in self.objects:
            self.draw_object(surface, obj)

        self.player.draw(surface)

        panel = pygame.Surface((SCREEN_W - 36, 98), pygame.SRCALPHA)
        panel.fill((15, 18, 22, 190))
        surface.blit(panel, (18, 12))

        now = pygame.time.get_ticks() / 1000.0
        active, remaining = self.player.active_powerup(now)
        distance_left = max(0, int(self.distance_goal - self.player.distance))

        pygame.draw.rect(surface, (60, 60, 74), (26, 18, 280, 72), border_radius=16)
        pygame.draw.rect(surface, (60, 60, 74), (318, 18, 220, 72), border_radius=16)
        pygame.draw.rect(surface, (60, 60, 74), (550, 18, 190, 72), border_radius=16)
        pygame.draw.rect(surface, (60, 60, 74), (752, 18, 182, 72), border_radius=16)

        draw_text(surface, f"Player: {self.username}", font, WHITE, 38, 25)
        draw_text(surface, f"Score: {self.score_value(now)}", font, WHITE, 38, 55)
        draw_text(surface, f"Coins: {self.player.coins}", font, WHITE, 330, 26)
        draw_text(surface, f"Distance: {int(self.player.distance)} / {self.distance_goal}", font, WHITE, 330, 54)
        draw_text(surface, f"Left: {distance_left}", font, WHITE, 560, 26)
        draw_text(surface, f"Speed: {int(self.current_speed(now))}", font, WHITE, 560, 54)

        if active == "Nitro" and remaining is not None:
            label = f"Power-up: Nitro ({remaining:0.1f}s)"
        elif active == "Shield":
            label = "Power-up: Shield"
        elif active == "Repair":
            label = "Power-up: Repair"
        else:
            label = "Power-up: none"
        draw_text(surface, label, font, WHITE, 762, 26)
        draw_text(surface, f"Difficulty: {self.difficulty}", font, WHITE, 762, 54)

        y = 122
        for text, left in self.notifications[:3]:
            bubble = pygame.Surface((250, 30), pygame.SRCALPHA)
            bubble.fill((12, 12, 12, 160))
            surface.blit(bubble, (18, y))
            draw_text(surface, text, small_font, WHITE, 30, y + 6)
            y += 36

    def get_leaderboard_entry(self):
        return {
            "name": self.username,
            "score": int(self.score_value()),
            "distance": int(self.player.distance),
            "coins": int(self.player.coins),
        }
