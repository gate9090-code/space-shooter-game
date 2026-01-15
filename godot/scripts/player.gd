extends CharacterBody2D
class_name Player
## Player - 플레이어 우주선
##
## WASD/방향키로 이동, 스페이스/마우스 클릭으로 발사
## 스킬 시스템, 무적 시간, 피격 이펙트 등

signal died
signal hp_changed(current: int, max_hp: int)

# 노드 참조
@onready var sprite: Sprite2D = $Sprite2D
@onready var collision: CollisionShape2D = $CollisionShape2D
@onready var fire_timer: Timer = $FireTimer
@onready var invincibility_timer: Timer = $InvincibilityTimer
@onready var muzzle: Marker2D = $Muzzle

# 스탯
var max_hp: int = 100
var current_hp: int = 100
var speed: float = 400.0
var damage: float = 10.0
var fire_rate: float = 0.15

# 상태
var is_invincible: bool = false
var can_fire: bool = true
var is_alive: bool = true

# 총알 씬 (프리로드)
var bullet_scene: PackedScene


func _ready() -> void:
	# GameManager에서 스탯 로드
	var stats = GameManager.get_player_stats()
	max_hp = stats.max_hp
	current_hp = max_hp
	damage = stats.damage
	speed = stats.speed
	fire_rate = stats.fire_rate

	fire_timer.wait_time = fire_rate
	fire_timer.timeout.connect(_on_fire_timer_timeout)
	invincibility_timer.timeout.connect(_on_invincibility_timeout)

	# 총알 씬 로드
	if ResourceLoader.exists("res://scenes/bullet.tscn"):
		bullet_scene = load("res://scenes/bullet.tscn")

	emit_signal("hp_changed", current_hp, max_hp)


func _physics_process(delta: float) -> void:
	if not is_alive:
		return

	# 입력 처리
	var input_dir = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = input_dir * speed

	move_and_slide()

	# 화면 경계 제한
	_clamp_to_screen()

	# 발사 처리
	if Input.is_action_pressed("shoot") and can_fire:
		fire()


func _clamp_to_screen() -> void:
	var viewport_rect = get_viewport_rect()
	var margin = 30

	position.x = clamp(position.x, margin, viewport_rect.size.x - margin)
	position.y = clamp(position.y, margin, viewport_rect.size.y - margin)


# ============================================================
# 발사 시스템
# ============================================================

func fire() -> void:
	if not bullet_scene:
		# 씬이 없으면 간단한 총알 생성
		_create_simple_bullet()
		return

	var bullet = bullet_scene.instantiate()
	bullet.position = muzzle.global_position
	bullet.damage = damage
	bullet.direction = Vector2.UP
	bullet.set_collision_mask_value(2, true)  # enemy 레이어

	get_tree().current_scene.add_child(bullet)

	can_fire = false
	fire_timer.start()


func _create_simple_bullet() -> void:
	# 씬 없이 간단한 총알 생성
	var bullet = Area2D.new()
	bullet.position = muzzle.global_position if muzzle else global_position + Vector2(0, -30)

	var collision_shape = CollisionShape2D.new()
	var shape = CircleShape2D.new()
	shape.radius = 5
	collision_shape.shape = shape
	bullet.add_child(collision_shape)

	var sprite = Sprite2D.new()
	var image = Image.create(10, 20, false, Image.FORMAT_RGBA8)
	image.fill(Color.CYAN)
	sprite.texture = ImageTexture.create_from_image(image)
	bullet.add_child(sprite)

	bullet.set_collision_layer_value(3, true)  # player_bullet
	bullet.set_collision_mask_value(2, true)   # enemy

	get_tree().current_scene.add_child(bullet)

	# 이동 처리
	var tween = create_tween()
	tween.tween_property(bullet, "position:y", bullet.position.y - 1000, 1.5)
	tween.tween_callback(bullet.queue_free)

	# 충돌 처리
	bullet.area_entered.connect(func(area):
		if area.is_in_group("enemies"):
			area.take_damage(damage)
			EffectManager.play_hit(bullet.global_position)
			bullet.queue_free()
	)

	can_fire = false
	fire_timer.start()


func _on_fire_timer_timeout() -> void:
	can_fire = true


# ============================================================
# 피해 시스템
# ============================================================

func take_damage(amount: int) -> void:
	if is_invincible or not is_alive:
		return

	current_hp = max(0, current_hp - amount)
	emit_signal("hp_changed", current_hp, max_hp)
	GameManager.damage_player(amount)

	# 피격 이펙트
	EffectManager.play_hit(global_position, "normal", false)
	EffectManager.screen_shake(5.0, 0.2)
	_flash_red()

	# 무적 시간 시작
	is_invincible = true
	invincibility_timer.start()

	if current_hp <= 0:
		die()


func heal(amount: int) -> void:
	current_hp = min(max_hp, current_hp + amount)
	emit_signal("hp_changed", current_hp, max_hp)
	GameManager.heal_player(amount)

	EffectManager.create_effect("skill_heal", global_position)


func _flash_red() -> void:
	var original_modulate = sprite.modulate if sprite else Color.WHITE
	if sprite:
		sprite.modulate = Color.RED

	var tween = create_tween()
	tween.tween_property(sprite if sprite else self, "modulate", original_modulate, 0.2)


func _on_invincibility_timeout() -> void:
	is_invincible = false


# ============================================================
# 사망 처리
# ============================================================

func die() -> void:
	is_alive = false
	EffectManager.play_enemy_death(global_position, "boss")
	EffectManager.screen_shake(15.0, 0.5)
	EffectManager.flash_screen(Color.WHITE, 0.2)

	emit_signal("died")

	# 페이드 아웃 후 제거
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.5)
	tween.tween_callback(queue_free)
