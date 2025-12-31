"""
Siege Mode Entities - 갈라그 스타일 적과 웨이브 관리
"""
import pygame
import math
import random
from typing import List, Tuple, Dict


class FormationEnemy:
    """
    포메이션 기반 적 클래스
    - 갈라그 스타일의 적 배치와 다이브 공격
    """

    # 이미지 캐시 (클래스 변수)
    _image_cache = {}

    def __init__(self, x: float, y: float, enemy_type: str = "basic", formation_pos: Tuple[float, float] = None):
        self.x = x
        self.y = y
        self.formation_x = formation_pos[0] if formation_pos else x
        self.formation_y = formation_pos[1] if formation_pos else y
        self.enemy_type = enemy_type

        # 상태
        self.hp = 50
        self.max_hp = 50
        self.alive = True
        self.in_formation = True

        # 크기
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)

        # 다이브 공격
        self.diving = False
        self.dive_path = []
        self.dive_index = 0

        # 애니메이션
        self.animation_timer = 0.0
        self.image = None

    @classmethod
    def reset_image_cache(cls):
        """이미지 캐시 초기화"""
        cls._image_cache.clear()

    def update(self, dt: float):
        """적 업데이트"""
        if not self.alive:
            return

        self.animation_timer += dt

        if self.diving:
            # 다이브 공격 중
            if self.dive_index < len(self.dive_path):
                target_x, target_y = self.dive_path[self.dive_index]

                # 타겟으로 이동
                dx = target_x - self.x
                dy = target_y - self.y
                dist = math.sqrt(dx*dx + dy*dy)

                if dist < 5:
                    self.dive_index += 1
                else:
                    speed = 300 * dt
                    self.x += (dx / dist) * speed
                    self.y += (dy / dist) * speed
            else:
                # 다이브 완료 - 포메이션으로 복귀
                self.diving = False
                self.dive_index = 0
        else:
            # 포메이션 위치로 부드럽게 이동
            dx = self.formation_x - self.x
            dy = self.formation_y - self.y
            self.x += dx * 2.0 * dt
            self.y += dy * 2.0 * dt

        # rect 업데이트
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    def start_dive(self, player_pos: pygame.math.Vector2, screen_size: Tuple[int, int]):
        """다이브 공격 시작"""
        if self.diving:
            return

        self.diving = True
        self.dive_index = 0
        self.dive_path = []

        # 간단한 다이브 경로: 플레이어 방향 -> 화면 아래
        mid_x = player_pos.x
        mid_y = player_pos.y

        self.dive_path = [
            (mid_x, mid_y),
            (mid_x, screen_size[1] + 50)
        ]

    def take_damage(self, damage: int) -> bool:
        """데미지 받기. 사망시 True 반환"""
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, screen: pygame.Surface):
        """적 그리기"""
        if not self.alive:
            return

        # 간단한 사각형으로 그리기 (이미지가 없을 때)
        color = (255, 100, 100) if self.diving else (200, 50, 50)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

        # HP 바
        if self.hp < self.max_hp:
            bar_width = self.width
            bar_height = 4
            bar_x = self.rect.x
            bar_y = self.rect.y - 8

            pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
            hp_ratio = self.hp / self.max_hp
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))


class WaveManager:
    """
    웨이브 관리 클래스
    - 적 생성 및 포메이션 관리
    - 웨이브 진행 관리
    """

    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_size = screen_size
        self.current_wave = 0
        self.enemies: List[FormationEnemy] = []

        # 포메이션 설정
        self.formation_offset_y = 0.0
        self.formation_sway = 0.0
        self.sway_timer = 0.0

        # 다이브 공격 타이머
        self.dive_timer = 0.0
        self.dive_cooldown = 3.0

    def start_wave(self, wave_num: int):
        """웨이브 시작"""
        self.current_wave = wave_num
        self.enemies.clear()

        # 웨이브에 따라 적 생성
        rows = min(3 + wave_num // 2, 6)
        cols = min(6 + wave_num // 3, 10)

        screen_w, screen_h = self.screen_size
        start_x = screen_w // 2 - (cols * 60) // 2
        start_y = 100

        for row in range(rows):
            for col in range(cols):
                x = start_x + col * 60
                y = start_y + row * 50
                enemy_type = "elite" if row == 0 else "basic"
                enemy = FormationEnemy(x, y, enemy_type, (x, y))
                enemy.hp = 50 + wave_num * 10
                enemy.max_hp = enemy.hp
                self.enemies.append(enemy)

    def update(self, dt: float, current_time: float, player_pos: pygame.math.Vector2,
               enemy_bullets: List[Dict]) -> Tuple[int, bool]:
        """
        웨이브 업데이트
        Returns: (score_gained, wave_complete)
        """
        score = 0

        # 포메이션 흔들림
        self.sway_timer += dt
        self.formation_sway = math.sin(self.sway_timer * 1.5) * 20

        # 모든 적 포메이션 위치 업데이트
        for enemy in self.enemies:
            if enemy.alive and not enemy.diving:
                enemy.formation_x += self.formation_sway * dt

        # 적 업데이트
        for enemy in self.enemies:
            if enemy.alive:
                enemy.update(dt)

        # 다이브 공격 시작
        self.dive_timer += dt
        if self.dive_timer >= self.dive_cooldown:
            self.dive_timer = 0.0
            self._try_start_dive(player_pos)

        # 사망한 적 제거 및 점수 계산
        alive_enemies = []
        for enemy in self.enemies:
            if enemy.alive:
                alive_enemies.append(enemy)
            else:
                score += 100

        self.enemies = alive_enemies

        # 웨이브 완료 체크
        wave_complete = len(self.enemies) == 0

        return score, wave_complete

    def _try_start_dive(self, player_pos: pygame.math.Vector2):
        """랜덤 적 다이브 공격 시작"""
        available = [e for e in self.enemies if e.alive and not e.diving]
        if available:
            diver = random.choice(available)
            diver.start_dive(player_pos, self.screen_size)

    def get_all_enemy_rects(self) -> List[pygame.Rect]:
        """모든 적의 충돌 rect 반환"""
        return [e.rect for e in self.enemies if e.alive]

    def check_hit(self, rect: pygame.Rect, damage: int = 10) -> int:
        """적과의 충돌 체크 및 데미지. 점수 반환"""
        score = 0
        for enemy in self.enemies:
            if enemy.alive and enemy.rect.colliderect(rect):
                if enemy.take_damage(damage):
                    score += 150
        return score

    def get_wave_name(self) -> str:
        """현재 웨이브 이름"""
        return f"Wave {self.current_wave}"

    def get_enemies_alive(self) -> int:
        """살아있는 적 수"""
        return len([e for e in self.enemies if e.alive])

    def draw(self, screen: pygame.Surface):
        """모든 적 그리기"""
        for enemy in self.enemies:
            if enemy.alive:
                enemy.draw(screen)


print("INFO: siege_entities.py loaded")
