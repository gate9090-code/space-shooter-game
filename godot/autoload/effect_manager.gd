extends Node
## EffectManager - 동적 이펙트 시스템
##
## Pygame의 advanced_effect_system.py를 Godot으로 포팅
## - 데이터 주도 이펙트 (JSON 설정)
## - 트윈 애니메이션 + 이징 함수
## - 파티클 효과
## - 핫 리로드 지원

# 이펙트 설정 캐시
var effects_config: Dictionary = {}
var composites_config: Dictionary = {}
var config_path: String = "res://assets/effects_config.json"

# 활성 이펙트 목록
var active_effects: Array[Node] = []


func _ready() -> void:
	load_config()
	print("EffectManager initialized")


# ============================================================
# 설정 로드
# ============================================================

func load_config() -> void:
	if not FileAccess.file_exists(config_path):
		print("Effect config not found, using defaults")
		_load_defaults()
		return

	var file = FileAccess.open(config_path, FileAccess.READ)
	if file:
		var json = JSON.new()
		var error = json.parse(file.get_as_text())
		file.close()

		if error == OK:
			var data = json.get_data()
			effects_config = data.get("effects", {})
			composites_config = data.get("composites", {})
			print("Loaded %d effects, %d composites" % [effects_config.size(), composites_config.size()])
		else:
			_load_defaults()


func _load_defaults() -> void:
	effects_config = {
		"hit_normal": {
			"color": [1.0, 1.0, 1.0, 1.0],
			"duration": 0.5,
			"scale_from": 0.1,
			"scale_to": 1.5,
			"particles": 10
		},
		"hit_fire": {
			"color": [1.0, 0.5, 0.2, 1.0],
			"duration": 0.8,
			"scale_from": 0.2,
			"scale_to": 2.0,
			"particles": 20
		},
		"explosion": {
			"color": [1.0, 0.8, 0.3, 1.0],
			"duration": 1.0,
			"scale_from": 0.3,
			"scale_to": 3.0,
			"particles": 30
		}
	}


func hot_reload() -> void:
	load_config()
	print("Effect config reloaded")


# ============================================================
# 이펙트 생성 - 메인 API
# ============================================================

func create_effect(effect_name: String, position: Vector2, overrides: Dictionary = {}) -> void:
	var config = effects_config.get(effect_name, effects_config.get("hit_normal", {}))
	config = config.duplicate()

	# 오버라이드 적용
	for key in overrides:
		config[key] = overrides[key]

	_spawn_effect(position, config)


func create_composite(composite_name: String, position: Vector2) -> void:
	if not composites_config.has(composite_name):
		create_effect("hit_normal", position)
		return

	for effect_name in composites_config[composite_name]:
		create_effect(effect_name, position)


# ============================================================
# 편의 메서드 - 게임 상황별 이펙트
# ============================================================

func play_hit(position: Vector2, damage_type: String = "normal", is_critical: bool = false) -> void:
	if is_critical:
		create_effect("critical_hit", position)
		_spawn_damage_number(position, "CRITICAL!", Color.YELLOW)
	else:
		create_effect("hit_" + damage_type, position)


func play_enemy_death(position: Vector2, enemy_type: String = "normal") -> void:
	match enemy_type:
		"boss":
			create_composite("boss_death_full", position)
		"elite":
			create_composite("explosion_full", position)
		_:
			create_effect("explosion", position)

	# 파티클 버스트 추가
	_spawn_death_particles(position, enemy_type)


func play_collect(position: Vector2, item_type: String = "coin") -> void:
	create_effect("collect_" + item_type, position)
	_spawn_collect_particles(position)


func play_level_up(position: Vector2) -> void:
	create_effect("level_up", position)
	_spawn_level_up_particles(position)


# ============================================================
# 내부 이펙트 생성
# ============================================================

func _spawn_effect(position: Vector2, config: Dictionary) -> void:
	# 간단한 스프라이트 기반 이펙트 생성
	var effect = Sprite2D.new()
	effect.position = position
	effect.modulate = Color(
		config.get("color", [1, 1, 1, 1])[0],
		config.get("color", [1, 1, 1, 1])[1],
		config.get("color", [1, 1, 1, 1])[2],
		config.get("color", [1, 1, 1, 1])[3]
	)
	effect.scale = Vector2.ONE * config.get("scale_from", 0.1)

	# 임시 원형 텍스처 생성 (이미지 없을 때)
	var image = Image.create(64, 64, false, Image.FORMAT_RGBA8)
	image.fill(Color.WHITE)
	var texture = ImageTexture.create_from_image(image)
	effect.texture = texture

	get_tree().current_scene.add_child(effect)
	active_effects.append(effect)

	# 트윈 애니메이션
	var duration = config.get("duration", 0.5)
	var scale_to = config.get("scale_to", 1.5)

	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(effect, "scale", Vector2.ONE * scale_to, duration).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tween.tween_property(effect, "modulate:a", 0.0, duration).set_ease(Tween.EASE_IN)

	tween.chain().tween_callback(func():
		effect.queue_free()
		active_effects.erase(effect)
	)

	# 파티클 스폰
	var particle_count = config.get("particles", 10)
	_spawn_particles(position, particle_count, effect.modulate)


func _spawn_particles(position: Vector2, count: int, color: Color) -> void:
	for i in range(count):
		var particle = Sprite2D.new()
		particle.position = position

		# 작은 원형 텍스처
		var image = Image.create(8, 8, false, Image.FORMAT_RGBA8)
		image.fill(Color.WHITE)
		var texture = ImageTexture.create_from_image(image)
		particle.texture = texture

		particle.modulate = color
		particle.scale = Vector2.ONE * randf_range(0.5, 1.5)

		get_tree().current_scene.add_child(particle)

		# 랜덤 방향으로 이동
		var angle = randf() * TAU
		var speed = randf_range(100, 300)
		var velocity = Vector2(cos(angle), sin(angle)) * speed
		var lifetime = randf_range(0.3, 0.8)

		var tween = create_tween()
		tween.set_parallel(true)
		tween.tween_property(particle, "position", position + velocity * lifetime, lifetime)
		tween.tween_property(particle, "modulate:a", 0.0, lifetime)
		tween.tween_property(particle, "scale", Vector2.ZERO, lifetime)

		tween.chain().tween_callback(particle.queue_free)


func _spawn_death_particles(position: Vector2, enemy_type: String) -> void:
	var count = 20 if enemy_type == "normal" else 40
	var color = Color.ORANGE_RED if enemy_type == "boss" else Color.ORANGE
	_spawn_particles(position, count, color)


func _spawn_collect_particles(position: Vector2) -> void:
	_spawn_particles(position, 8, Color.GOLD)


func _spawn_level_up_particles(position: Vector2) -> void:
	_spawn_particles(position, 30, Color.YELLOW)


func _spawn_damage_number(position: Vector2, text: String, color: Color) -> void:
	var label = Label.new()
	label.text = text
	label.position = position - Vector2(30, 20)
	label.add_theme_color_override("font_color", color)
	label.add_theme_font_size_override("font_size", 24)

	get_tree().current_scene.add_child(label)

	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(label, "position:y", position.y - 60, 0.8).set_ease(Tween.EASE_OUT)
	tween.tween_property(label, "modulate:a", 0.0, 0.8).set_ease(Tween.EASE_IN)

	tween.chain().tween_callback(label.queue_free)


# ============================================================
# 화면 효과
# ============================================================

func screen_shake(intensity: float = 10.0, duration: float = 0.3) -> void:
	var camera = get_tree().current_scene.get_node_or_null("Camera2D")
	if not camera:
		return

	var original_offset = camera.offset
	var tween = create_tween()

	for i in range(int(duration * 30)):
		var offset = Vector2(
			randf_range(-intensity, intensity),
			randf_range(-intensity, intensity)
		)
		tween.tween_property(camera, "offset", original_offset + offset, 0.033)

	tween.tween_property(camera, "offset", original_offset, 0.1)


func flash_screen(color: Color = Color.WHITE, duration: float = 0.1) -> void:
	var flash = ColorRect.new()
	flash.color = color
	flash.size = get_viewport().get_visible_rect().size
	flash.mouse_filter = Control.MOUSE_FILTER_IGNORE

	get_tree().current_scene.add_child(flash)

	var tween = create_tween()
	tween.tween_property(flash, "modulate:a", 0.0, duration)
	tween.tween_callback(flash.queue_free)
