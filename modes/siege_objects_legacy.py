# modes/siege_objects.py
"""
공성 모드 전용 오브젝트 클래스
TileMap, Tower, DestructibleWall, GuardEnemy, PatrolEnemy
"""

import pygame
import math
from typing import List, Tuple, Dict
from pathlib import Path
import config


# =========================================================
# 타일맵 시스템
# =========================================================

class TileMap:
    """타일맵 렌더링 및 충돌 감지 시스템"""

    def __init__(self, stage_num: int, x_offset: int = 0, y_offset: int = 0):
        self.stage_num = stage_num
        self.tile_size = config.TILE_SIZE
        self.x_offset = x_offset
        self.y_offset = y_offset

        self.map_data = config.SIEGE_MAPS.get(stage_num, config.SIEGE_MAP_1)
        self.height = len(self.map_data)
        self.width = len(self.map_data[0]) if self.height > 0 else 0

        self.tile_images = self.load_tile_images()
        self.player_start_pos = self.find_player_start()
        self.tower_positions = self.find_towers()
        self.guard_spawns = self.find_spawns(config.TILE_GUARD_SPAWN)
        self.patrol_spawns = self.find_spawns(config.TILE_PATROL_SPAWN)
        self.destructible_walls = self.find_destructibles()

    def load_tile_images(self) -> Dict[int, pygame.Surface]:
        images = {}
        # 공성 모드 전용 타일 폴더 사용 (실제 파일명에 맞게 수정)
        tile_paths = {
            config.TILE_FLOOR: "assets/siege_mode/tiles/floor_image.jpg",
            config.TILE_WALL: "assets/siege_mode/tiles/wall_image.png",
            config.TILE_SAFE_ZONE: "assets/siege_mode/tiles/safe_zone.png",
            config.TILE_TOWER: "assets/siege_mode/tiles/tower_base.png",
            config.TILE_DESTRUCTIBLE: "assets/siege_mode/tiles/destructible_wall.png",
        }
        for tile_type, path in tile_paths.items():
            try:
                if Path(path).exists():
                    img = pygame.image.load(path)
                    if path.endswith('.png'):
                        img = img.convert_alpha()
                    else:
                        img = img.convert()
                    images[tile_type] = pygame.transform.scale(img, (self.tile_size, self.tile_size))
                    print(f"INFO: Loaded tile image: {path}")
                else:
                    print(f"WARNING: Tile image not found: {path}")
            except Exception as e:
                print(f"ERROR: Failed to load tile image {path}: {e}")
        return images

    def find_player_start(self) -> Tuple[int, int]:
        for row in range(self.height):
            for col in range(self.width):
                if self.map_data[row][col] == config.TILE_PLAYER_START:
                    x = col * self.tile_size + self.tile_size // 2 + self.x_offset
                    y = row * self.tile_size + self.tile_size // 2 + self.y_offset
                    return (x, y)
        return (self.tile_size * 2 + self.x_offset, self.tile_size * 2 + self.y_offset)

    def find_towers(self) -> List[Tuple[int, int]]:
        towers = []
        for row in range(self.height):
            for col in range(self.width):
                if self.map_data[row][col] == config.TILE_TOWER:
                    x = col * self.tile_size + self.tile_size // 2 + self.x_offset
                    y = row * self.tile_size + self.tile_size // 2 + self.y_offset
                    towers.append((x, y))
        return towers

    def find_spawns(self, spawn_type: int) -> List[Tuple[int, int]]:
        spawns = []
        for row in range(self.height):
            for col in range(self.width):
                if self.map_data[row][col] == spawn_type:
                    x = col * self.tile_size + self.tile_size // 2 + self.x_offset
                    y = row * self.tile_size + self.tile_size // 2 + self.y_offset
                    spawns.append((x, y))
        return spawns

    def find_destructibles(self) -> List[Tuple[int, int]]:
        destructibles = []
        for row in range(self.height):
            for col in range(self.width):
                if self.map_data[row][col] == config.TILE_DESTRUCTIBLE:
                    x = col * self.tile_size + self.tile_size // 2 + self.x_offset
                    y = row * self.tile_size + self.tile_size // 2 + self.y_offset
                    destructibles.append((x, y))
        return destructibles

    def is_walkable(self, x: float, y: float) -> bool:
        col = int((x - self.x_offset) // self.tile_size)
        row = int((y - self.y_offset) // self.tile_size)
        if row < 0 or row >= self.height or col < 0 or col >= self.width:
            return False
        tile_type = self.map_data[row][col]
        return tile_type not in [config.TILE_WALL, config.TILE_DESTRUCTIBLE]

    def is_safe_zone(self, x: float, y: float) -> bool:
        col = int((x - self.x_offset) // self.tile_size)
        row = int((y - self.y_offset) // self.tile_size)
        if row < 0 or row >= self.height or col < 0 or col >= self.width:
            return False
        return self.map_data[row][col] == config.TILE_SAFE_ZONE

    def draw(self, screen: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)):
        # 타일 타입별 폴백 색상
        fallback_colors = {
            config.TILE_FLOOR: (40, 40, 50),           # 바닥 - 어두운 회색
            config.TILE_WALL: (80, 80, 100),           # 벽 - 밝은 회색
            config.TILE_SAFE_ZONE: (40, 80, 40),       # 안전지대 - 초록
            config.TILE_TOWER: (100, 60, 60),          # 타워 베이스 - 빨간 톤
            config.TILE_GUARD_SPAWN: (40, 40, 50),     # 경비병 스폰 - 바닥과 동일
            config.TILE_PATROL_SPAWN: (40, 40, 50),    # 순찰병 스폰 - 바닥과 동일
            config.TILE_DESTRUCTIBLE: (100, 80, 50),   # 파괴가능 벽 - 갈색
            config.TILE_PLAYER_START: (40, 60, 80),    # 플레이어 시작 - 파란 톤
        }

        for row in range(self.height):
            for col in range(self.width):
                tile_type = self.map_data[row][col]
                x = col * self.tile_size + self.x_offset - camera_offset[0]
                y = row * self.tile_size + self.y_offset - camera_offset[1]

                if x < -self.tile_size or x > screen.get_width() or \
                   y < -self.tile_size or y > screen.get_height():
                    continue

                # 이미지가 있으면 이미지 사용, 없으면 폴백 색상
                if tile_type in self.tile_images:
                    screen.blit(self.tile_images[tile_type], (x, y))
                elif tile_type in fallback_colors:
                    rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                    pygame.draw.rect(screen, fallback_colors[tile_type], rect)
                    # 벽/파괴가능벽은 테두리 추가
                    if tile_type in [config.TILE_WALL, config.TILE_DESTRUCTIBLE]:
                        pygame.draw.rect(screen, (60, 60, 70), rect, 2)


# =========================================================
# 타워 오브젝트
# =========================================================

class Tower:
    """파괴 목표 타워"""

    def __init__(self, x: float, y: float):
        self.pos = pygame.math.Vector2(x, y)
        self.max_hp = config.TOWER_MAX_HP
        self.hp = self.max_hp
        self.size = config.TOWER_SIZE
        self.is_alive = True

        # tower_palace.png 사용 (타워 오브젝트용)
        tower_path = Path("assets/siege_mode/tiles/tower_palace.png")
        if tower_path.exists():
            self.image = pygame.image.load(str(tower_path)).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
            print(f"INFO: Loaded tower image: {tower_path}")
        else:
            print(f"WARNING: Tower image not found: {tower_path}")
            self.image = None

    def take_damage(self, damage: float):
        if not self.is_alive:
            return
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
            print("INFO: Tower destroyed!")

    def draw(self, screen: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)):
        if not self.is_alive:
            return

        screen_x = int(self.pos.x - camera_offset[0])
        screen_y = int(self.pos.y - camera_offset[1])

        if self.image:
            image_rect = self.image.get_rect(center=(screen_x, screen_y))
            screen.blit(self.image, image_rect)
        else:
            rect = pygame.Rect(screen_x - self.size//2, screen_y - self.size//2, self.size, self.size)
            pygame.draw.rect(screen, (100, 100, 100), rect)

        # HP bar (1/2 크기, 이미지 상단 정중앙)
        bar_width = self.size // 2
        bar_height = 4
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.size // 2 + 2
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)


# =========================================================
# 파괴 가능한 벽
# =========================================================

class DestructibleWall:
    """파괴 가능한 벽"""

    def __init__(self, x: float, y: float):
        self.pos = pygame.math.Vector2(x, y)
        self.max_hp = config.DESTRUCTIBLE_WALL_HP
        self.hp = self.max_hp
        self.size = config.TILE_SIZE
        self.is_alive = True

        wall_path = Path("assets/images/tiles/destructible_wall.png")
        if wall_path.exists():
            self.image = pygame.image.load(str(wall_path)).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
        else:
            self.image = None

    def take_damage(self, damage: float):
        if not self.is_alive:
            return
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False

    def draw(self, screen: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)):
        if not self.is_alive:
            return

        screen_x = int(self.pos.x - camera_offset[0])
        screen_y = int(self.pos.y - camera_offset[1])

        if self.image:
            image_rect = self.image.get_rect(center=(screen_x, screen_y))
            screen.blit(self.image, image_rect)
        else:
            rect = pygame.Rect(screen_x - self.size//2, screen_y - self.size//2, self.size, self.size)
            pygame.draw.rect(screen, (80, 60, 40), rect)

        # HP bar (1/2 크기, 이미지 상단 정중앙)
        bar_width = self.size // 2
        bar_height = 3
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.size // 2 + 2
        pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (200, 150, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))


# =========================================================
# 경비병
# =========================================================

class GuardEnemy:
    """고정 위치에서 경계하는 경비병"""

    _image = None
    _image_loaded = False

    def __init__(self, x: float, y: float):
        self.pos = pygame.math.Vector2(x, y)
        self.max_hp = 50
        self.hp = self.max_hp
        self.size = 32 * 3
        self.is_alive = True
        self.detection_range = config.GUARD_ENEMY_RANGE
        self.attack_range = config.GUARD_ENEMY_ATTACK_RANGE
        self.last_attack_time = 0
        self.attack_cooldown = 1.5

        if not GuardEnemy._image_loaded:
            try:
                image_path = Path("assets/siege_mode/enemies/guard_enemy.png")
                if image_path.exists():
                    GuardEnemy._image = pygame.image.load(str(image_path)).convert_alpha()
                    GuardEnemy._image = pygame.transform.scale(GuardEnemy._image, (self.size, self.size))
                GuardEnemy._image_loaded = True
            except Exception as e:
                print(f"WARNING: Failed to load guard enemy image: {e}")
                GuardEnemy._image_loaded = True

    def update(self, player_pos: pygame.math.Vector2, current_time: float, bullets: list, tilemap):
        if not self.is_alive:
            return
        distance = self.pos.distance_to(player_pos)
        if distance <= self.detection_range and distance <= self.attack_range:
            if current_time - self.last_attack_time >= self.attack_cooldown:
                if not tilemap.is_safe_zone(player_pos.x, player_pos.y):
                    self.shoot_at_player(player_pos, bullets)
                    self.last_attack_time = current_time

    def shoot_at_player(self, player_pos: pygame.math.Vector2, bullets: list):
        direction = (player_pos - self.pos).normalize()
        bullet = {"pos": self.pos.copy(), "vel": direction * 300, "damage": 10, "is_enemy_bullet": True}
        bullets.append(bullet)

    def take_damage(self, damage: float):
        if not self.is_alive:
            return
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False

    def draw(self, screen: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)):
        if not self.is_alive:
            return

        screen_x = int(self.pos.x - camera_offset[0])
        screen_y = int(self.pos.y - camera_offset[1])

        if GuardEnemy._image:
            image_rect = GuardEnemy._image.get_rect(center=(screen_x, screen_y))
            screen.blit(GuardEnemy._image, image_rect)
        else:
            pygame.draw.circle(screen, (200, 50, 50), (screen_x, screen_y), self.size // 2)

        # HP bar (1/2 크기, 이미지 상단 정중앙)
        bar_width = self.size // 2
        bar_height = 3
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.size // 2 + 2
        pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (255, 50, 50), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))


# =========================================================
# 순찰병
# =========================================================

class PatrolEnemy:
    """정해진 경로를 순찰하는 순찰병"""

    _image = None
    _image_loaded = False

    def __init__(self, x: float, y: float):
        self.start_pos = pygame.math.Vector2(x, y)
        self.pos = self.start_pos.copy()
        self.max_hp = 40
        self.hp = self.max_hp
        self.size = 28 * 3
        self.is_alive = True
        self.speed = config.PATROL_ENEMY_SPEED
        self.detection_range = config.PATROL_ENEMY_RANGE
        self.patrol_radius = 80
        self.last_attack_time = 0
        self.attack_cooldown = 2.0
        self.patrol_angle = 0
        self.patrol_speed = 1.0

        if not PatrolEnemy._image_loaded:
            try:
                image_path = Path("assets/siege_mode/enemies/patrol_enemy.png")
                if image_path.exists():
                    PatrolEnemy._image = pygame.image.load(str(image_path)).convert_alpha()
                    PatrolEnemy._image = pygame.transform.scale(PatrolEnemy._image, (self.size, self.size))
                PatrolEnemy._image_loaded = True
            except Exception as e:
                print(f"WARNING: Failed to load patrol enemy image: {e}")
                PatrolEnemy._image_loaded = True

    def update(self, player_pos: pygame.math.Vector2, current_time: float, dt: float, bullets: list, tilemap):
        if not self.is_alive:
            return

        self.patrol_angle += self.patrol_speed * dt
        offset_x = math.cos(self.patrol_angle) * self.patrol_radius
        offset_y = math.sin(self.patrol_angle) * self.patrol_radius
        self.pos = self.start_pos + pygame.math.Vector2(offset_x, offset_y)

        distance = self.pos.distance_to(player_pos)
        if distance <= self.detection_range:
            if current_time - self.last_attack_time >= self.attack_cooldown:
                if not tilemap.is_safe_zone(player_pos.x, player_pos.y):
                    self.shoot_at_player(player_pos, bullets)
                    self.last_attack_time = current_time

    def shoot_at_player(self, player_pos: pygame.math.Vector2, bullets: list):
        direction = (player_pos - self.pos).normalize()
        bullet = {"pos": self.pos.copy(), "vel": direction * 250, "damage": 8, "is_enemy_bullet": True}
        bullets.append(bullet)

    def take_damage(self, damage: float):
        if not self.is_alive:
            return
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False

    def draw(self, screen: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)):
        if not self.is_alive:
            return

        screen_x = int(self.pos.x - camera_offset[0])
        screen_y = int(self.pos.y - camera_offset[1])

        if PatrolEnemy._image:
            image_rect = PatrolEnemy._image.get_rect(center=(screen_x, screen_y))
            screen.blit(PatrolEnemy._image, image_rect)
        else:
            points = [
                (screen_x, screen_y - self.size // 2),
                (screen_x - self.size // 2, screen_y + self.size // 2),
                (screen_x + self.size // 2, screen_y + self.size // 2),
            ]
            pygame.draw.polygon(screen, (255, 150, 50), points)

        # HP bar (1/2 크기, 이미지 상단 정중앙)
        bar_width = self.size // 2
        bar_height = 3
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.size // 2 + 2
        pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (255, 150, 50), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))


print("INFO: siege_objects.py loaded")
