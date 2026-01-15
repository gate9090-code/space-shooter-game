extends Area2D
class_name Enemy
## Enemy - 적 우주선
##
## 다양한 적 타입 지원:
## - NORMAL: 기본 적
## - SWARM: 빠르고 약함
## - ELITE: 강력하고 체력 높음
## - BOSS: 보스 몬스터

signal died(enemy: Enemy, position: Vector2)

enum EnemyType { NORMAL, SWARM, ELITE, BOSS }

# 설정
@export var enemy_type: EnemyType = EnemyType.NORMAL
@export var base_hp: int = 30
@export var base_damage: int = 10
@export var base_speed: float = 100.0
@export var score_value: int = 100
@export var coin_drop_chance: float = 0.3

# 노드 참조
@onready var sprite: Sprite2D = $Sprite2D
@onready var collision: CollisionShape2D = $CollisionShape2D

# 상태
var max_hp: int
var current_hp: int
var damage: int
var speed: float
var is_alive: bool = true
var target: Node2D = null
var velocity: Vector2 = Vector2.ZERO

# 이동 패턴
enum MovePattern { STRAIGHT, ZIGZAG, CHASE, WANDER }
var move_pattern: MovePattern = MovePattern.STRAIGHT
var pattern_timer: float = 0.0
var pattern_offset: float = 0.0


func _ready() -> void:
	add_to_group("enemies")
	_setup_stats()
	_setup_visuals()

	area_entered.connect(_on_area_entered)
	body_entered.connect(_on_body_entered)

	# 플레이어 찾기
	await get_tree().process_frame
	var players = get_tree().get_nodes_in_group("player")
	if players.size() > 0:
		target = players[0]


func _setup_stats() -> void:
	# 타입별 스탯 배율
	var hp_mult = 1.0
	var damage_mult = 1.0
	var speed_mult = 1.0
	var score_mult = 1.0

	match enemy_type:
		EnemyType.NORMAL:
			hp_mult = 1.0
			move_pattern = MovePattern.STRAIGHT
		EnemyType.SWARM:
			hp_mult = 0.5
			speed_mult = 1.5
			score_mult = 0.5
			move_pattern = MovePattern.ZIGZAG
		EnemyType.ELITE:
			hp_mult = 3.0
			damage_mult = 1.5
			speed_mult = 0.8
			score_mult = 3.0
			move_pattern = MovePattern.CHASE
		EnemyType.BOSS:
			hp_mult = 20.0
			damage_mult = 2.0
			speed_mult = 0.5
			score_mult = 50.0
			move_pattern = MovePattern.WANDER

	max_hp = int(base_hp * hp_mult)
	current_hp = max_hp
	damage = int(base_damage * damage_mult)
	speed = base_speed * speed_mult
	score_value = int(score_value * score_mult)


func _setup_visuals() -> void:
	if not sprite:
		sprite = Sprite2D.new()
		add_child(sprite)

	# 타입별 색상
	var color = Color.WHITE
	match enemy_type:
		EnemyType.NORMAL:
			color = Color.RED
		EnemyType.SWARM:
			color = Color.ORANGE
		EnemyType.ELITE:
			color = Color.PURPLE
		EnemyType.BOSS:
			color = Color.DARK_RED

	# 임시 텍스처 생성
	var size = 32 if enemy_type != EnemyType.BOSS else 80
	var image = Image.create(size, size, false, Image.FORMAT_RGBA8)
	image.fill(color)
	sprite.texture = ImageTexture.create_from_image(image)
	sprite.modulate = color


func _physics_process(delta: float) -> void:
	if not is_alive:
		return

	pattern_timer += delta
	_update_movement(delta)

	# 화면 아래로 나가면 제거
	if position.y > get_viewport_rect().size.y + 100:
		queue_free()


func _update_movement(delta: float) -> void:
	match move_pattern:
		MovePattern.STRAIGHT:
			velocity = Vector2.DOWN * speed

		MovePattern.ZIGZAG:
			pattern_offset = sin(pattern_timer * 3) * 150
			velocity = Vector2(pattern_offset, speed)

		MovePattern.CHASE:
			if target and is_instance_valid(target):
				var dir = (target.global_position - global_position).normalized()
				velocity = dir * speed
			else:
				velocity = Vector2.DOWN * speed

		MovePattern.WANDER:
			pattern_offset = sin(pattern_timer * 1.5) * 100
			velocity = Vector2(pattern_offset, speed * 0.3)

	position += velocity * delta


# ============================================================
# 피해 시스템
# ============================================================

func take_damage(amount: float) -> void:
	if not is_alive:
		return

	current_hp -= int(amount)

	# 피격 이펙트
	_flash_white()
	EffectManager.play_hit(global_position)

	if current_hp <= 0:
		die()


func _flash_white() -> void:
	if sprite:
		sprite.modulate = Color.WHITE
		var tween = create_tween()
		tween.tween_property(sprite, "modulate", _get_type_color(), 0.1)


func _get_type_color() -> Color:
	match enemy_type:
		EnemyType.NORMAL: return Color.RED
		EnemyType.SWARM: return Color.ORANGE
		EnemyType.ELITE: return Color.PURPLE
		EnemyType.BOSS: return Color.DARK_RED
	return Color.RED


# ============================================================
# 사망 처리
# ============================================================

func die() -> void:
	is_alive = false
	set_deferred("monitoring", false)
	set_deferred("monitorable", false)

	# 점수 추가
	GameManager.add_score(score_value)

	# 코인 드롭
	if randf() < coin_drop_chance:
		_drop_coin()

	# 사망 이펙트
	var death_type = "boss" if enemy_type == EnemyType.BOSS else "normal"
	if enemy_type == EnemyType.ELITE:
		death_type = "elite"

	EffectManager.play_enemy_death(global_position, death_type)

	if enemy_type == EnemyType.BOSS:
		EffectManager.screen_shake(20.0, 0.8)
		EffectManager.flash_screen(Color.WHITE, 0.3)

	emit_signal("died", self, global_position)

	# 페이드 아웃
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.3)
	tween.tween_callback(queue_free)


func _drop_coin() -> void:
	# 코인 드롭 (간단한 구현)
	GameManager.add_coins(10 * (1 if enemy_type == EnemyType.NORMAL else 3))
	EffectManager.play_collect(global_position, "coin")


# ============================================================
# 충돌 처리
# ============================================================

func _on_area_entered(area: Area2D) -> void:
	# 플레이어 총알과 충돌
	if area.is_in_group("player_bullets"):
		var bullet_damage = area.get("damage") if area.has_method("get") else 10
		take_damage(bullet_damage)
		area.queue_free()


func _on_body_entered(body: Node2D) -> void:
	# 플레이어와 충돌 (체력 데미지)
	if body.is_in_group("player") and body.has_method("take_damage"):
		body.take_damage(damage)
