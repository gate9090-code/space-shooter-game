extends Node2D
## Main - 게임 메인 씬 컨트롤러
##
## 웨이브 시스템, 적 스폰, UI 업데이트 관리

# 노드 참조
@onready var player: CharacterBody2D = $Player
@onready var enemy_spawner: Timer = $EnemySpawner
@onready var score_label: Label = $UI/HUD/ScoreLabel
@onready var wave_label: Label = $UI/HUD/WaveLabel
@onready var hp_bar: ProgressBar = $UI/HUD/HPBar
@onready var hp_label: Label = $UI/HUD/HPLabel

# 웨이브 설정
var current_wave: int = 1
var enemies_to_spawn: int = 5
var enemies_spawned: int = 0
var enemies_killed: int = 0
var wave_in_progress: bool = false

# 적 스폰 설정
var spawn_margin: float = 50.0


func _ready() -> void:
	# 플레이어 이미지 설정 (임시)
	_setup_player_sprite()

	# 시그널 연결
	GameManager.score_changed.connect(_on_score_changed)
	GameManager.wave_changed.connect(_on_wave_changed)
	GameManager.player_hp_changed.connect(_on_player_hp_changed)
	GameManager.game_over.connect(_on_game_over)

	if player:
		player.died.connect(_on_player_died)
		player.hp_changed.connect(_on_player_hp_changed)

	# 게임 시작
	GameManager.start_game()
	_start_wave()

	print("Main scene ready - Space Shooter Godot")


func _setup_player_sprite() -> void:
	if player and player.has_node("Sprite2D"):
		var sprite = player.get_node("Sprite2D")
		# 삼각형 우주선 모양 생성
		var image = Image.create(64, 64, false, Image.FORMAT_RGBA8)
		image.fill(Color.TRANSPARENT)

		# 간단한 우주선 모양 그리기
		for y in range(64):
			for x in range(64):
				# 삼각형 형태
				var center_x = 32
				var top_y = 5
				var bottom_y = 58
				var width_at_bottom = 25

				var progress = float(y - top_y) / (bottom_y - top_y)
				if y >= top_y and y <= bottom_y:
					var half_width = progress * width_at_bottom
					if abs(x - center_x) <= half_width:
						image.set_pixel(x, y, Color.CYAN)

		sprite.texture = ImageTexture.create_from_image(image)


func _process(_delta: float) -> void:
	# 웨이브 완료 체크
	if wave_in_progress and enemies_killed >= enemies_to_spawn:
		_complete_wave()


# ============================================================
# 웨이브 시스템
# ============================================================

func _start_wave() -> void:
	wave_in_progress = true
	enemies_spawned = 0
	enemies_killed = 0
	enemies_to_spawn = 5 + (current_wave - 1) * 3

	# 스폰 속도 조절
	enemy_spawner.wait_time = max(0.5, 1.5 - (current_wave * 0.1))
	enemy_spawner.start()

	print("Wave %d started - %d enemies" % [current_wave, enemies_to_spawn])


func _complete_wave() -> void:
	wave_in_progress = false
	enemy_spawner.stop()

	# 웨이브 클리어 이펙트
	EffectManager.flash_screen(Color(0.2, 0.5, 1.0, 0.3), 0.5)

	# 다음 웨이브 준비
	current_wave += 1
	GameManager.next_wave()

	# 잠시 후 다음 웨이브 시작
	await get_tree().create_timer(2.0).timeout

	if GameManager.current_state == GameManager.GameState.PLAYING:
		_start_wave()


func _on_enemy_spawner_timeout() -> void:
	if enemies_spawned >= enemies_to_spawn:
		enemy_spawner.stop()
		return

	_spawn_enemy()
	enemies_spawned += 1


# ============================================================
# 적 스폰
# ============================================================

func _spawn_enemy() -> void:
	var enemy = _create_enemy()

	# 랜덤 위치 (화면 상단)
	var viewport_size = get_viewport_rect().size
	enemy.position = Vector2(
		randf_range(spawn_margin, viewport_size.x - spawn_margin),
		-50
	)

	# 타입 결정 (웨이브에 따라)
	if current_wave >= 5 and randf() < 0.1:
		enemy.enemy_type = Enemy.EnemyType.ELITE
	elif current_wave >= 3 and randf() < 0.3:
		enemy.enemy_type = Enemy.EnemyType.SWARM

	# 보스 스폰 (5웨이브마다)
	if current_wave % 5 == 0 and enemies_spawned == enemies_to_spawn - 1:
		enemy.enemy_type = Enemy.EnemyType.BOSS
		enemy.position.x = viewport_size.x / 2

	add_child(enemy)

	# 스폰 이펙트
	EffectManager.create_effect("spawn_portal", enemy.position)

	# 사망 시그널 연결
	enemy.died.connect(_on_enemy_died)


func _create_enemy() -> Enemy:
	var enemy = Enemy.new()

	# CollisionShape 추가
	var collision = CollisionShape2D.new()
	var shape = CircleShape2D.new()
	shape.radius = 15
	collision.shape = shape
	collision.name = "CollisionShape2D"
	enemy.add_child(collision)

	# Sprite 추가
	var sprite = Sprite2D.new()
	sprite.name = "Sprite2D"
	enemy.add_child(sprite)

	# 충돌 레이어 설정
	enemy.set_collision_layer_value(2, true)  # enemy
	enemy.set_collision_mask_value(1, true)   # player
	enemy.set_collision_mask_value(3, true)   # player_bullet

	return enemy


func _on_enemy_died(_enemy: Enemy, _position: Vector2) -> void:
	enemies_killed += 1


# ============================================================
# UI 업데이트
# ============================================================

func _on_score_changed(new_score: int) -> void:
	if score_label:
		score_label.text = "Score: %d" % new_score


func _on_wave_changed(new_wave: int) -> void:
	if wave_label:
		wave_label.text = "Wave: %d" % new_wave


func _on_player_hp_changed(current: int, max_hp: int) -> void:
	if hp_bar:
		hp_bar.max_value = max_hp
		hp_bar.value = current

	if hp_label:
		hp_label.text = "%d / %d" % [current, max_hp]


# ============================================================
# 게임 오버
# ============================================================

func _on_player_died() -> void:
	GameManager.trigger_game_over()


func _on_game_over() -> void:
	enemy_spawner.stop()

	# 게임 오버 UI 표시
	var game_over_label = Label.new()
	game_over_label.text = "GAME OVER\n\nScore: %d\nWave: %d\n\nPress R to Restart" % [GameManager.score, current_wave]
	game_over_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	game_over_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	game_over_label.add_theme_font_size_override("font_size", 32)
	game_over_label.anchors_preset = Control.PRESET_CENTER
	game_over_label.position = Vector2(640, 360) - Vector2(150, 60)

	$UI/HUD.add_child(game_over_label)


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().quit()

	# 재시작
	if GameManager.current_state == GameManager.GameState.GAME_OVER:
		if event is InputEventKey and event.keycode == KEY_R:
			get_tree().reload_current_scene()
