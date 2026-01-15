extends Node
## GameManager - 전역 게임 상태 관리
##
## 싱글톤으로 게임 전반의 상태를 관리합니다.
## - 점수, 웨이브, 플레이어 상태
## - 게임 일시정지, 게임오버 처리
## - 저장/불러오기

# 시그널 정의
signal score_changed(new_score: int)
signal wave_changed(new_wave: int)
signal player_hp_changed(current: int, max_hp: int)
signal game_over
signal game_paused(is_paused: bool)

# 게임 상태
enum GameState { MENU, PLAYING, PAUSED, GAME_OVER, VICTORY }

var current_state: GameState = GameState.MENU
var score: int = 0
var high_score: int = 0
var current_wave: int = 1
var coins: int = 0

# 플레이어 데이터
var player_max_hp: int = 100
var player_current_hp: int = 100
var player_damage: float = 10.0
var player_speed: float = 400.0
var player_fire_rate: float = 0.15

# 업그레이드 레벨
var upgrades: Dictionary = {
	"hp": 0,
	"damage": 0,
	"speed": 0,
	"fire_rate": 0
}

# 설정
var save_path: String = "user://save_data.json"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS  # 일시정지 중에도 동작
	load_game()
	print("GameManager initialized")


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") and current_state == GameState.PLAYING:
		toggle_pause()


# ============================================================
# 게임 상태 관리
# ============================================================

func start_game() -> void:
	current_state = GameState.PLAYING
	score = 0
	current_wave = 1
	player_current_hp = player_max_hp
	get_tree().paused = false
	emit_signal("score_changed", score)
	emit_signal("wave_changed", current_wave)
	emit_signal("player_hp_changed", player_current_hp, player_max_hp)


func toggle_pause() -> void:
	if current_state == GameState.PLAYING:
		current_state = GameState.PAUSED
		get_tree().paused = true
		emit_signal("game_paused", true)
	elif current_state == GameState.PAUSED:
		current_state = GameState.PLAYING
		get_tree().paused = false
		emit_signal("game_paused", false)


func trigger_game_over() -> void:
	current_state = GameState.GAME_OVER
	if score > high_score:
		high_score = score
		save_game()
	emit_signal("game_over")


func return_to_menu() -> void:
	current_state = GameState.MENU
	get_tree().paused = false
	# get_tree().change_scene_to_file("res://scenes/main_menu.tscn")


# ============================================================
# 점수 및 웨이브
# ============================================================

func add_score(amount: int) -> void:
	score += amount
	emit_signal("score_changed", score)


func add_coins(amount: int) -> void:
	coins += amount


func next_wave() -> void:
	current_wave += 1
	emit_signal("wave_changed", current_wave)


# ============================================================
# 플레이어 상태
# ============================================================

func damage_player(amount: int) -> void:
	player_current_hp = max(0, player_current_hp - amount)
	emit_signal("player_hp_changed", player_current_hp, player_max_hp)

	if player_current_hp <= 0:
		trigger_game_over()


func heal_player(amount: int) -> void:
	player_current_hp = min(player_max_hp, player_current_hp + amount)
	emit_signal("player_hp_changed", player_current_hp, player_max_hp)


func get_player_stats() -> Dictionary:
	# 업그레이드 적용된 스탯 반환
	return {
		"max_hp": player_max_hp + (upgrades.hp * 20),
		"damage": player_damage + (upgrades.damage * 5),
		"speed": player_speed + (upgrades.speed * 50),
		"fire_rate": max(0.05, player_fire_rate - (upgrades.fire_rate * 0.02))
	}


# ============================================================
# 업그레이드
# ============================================================

func purchase_upgrade(upgrade_type: String, cost: int) -> bool:
	if coins >= cost and upgrades.has(upgrade_type):
		coins -= cost
		upgrades[upgrade_type] += 1
		save_game()
		return true
	return false


# ============================================================
# 저장/불러오기
# ============================================================

func save_game() -> void:
	var save_data = {
		"high_score": high_score,
		"coins": coins,
		"upgrades": upgrades
	}

	var file = FileAccess.open(save_path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(save_data, "\t"))
		file.close()
		print("Game saved")


func load_game() -> void:
	if not FileAccess.file_exists(save_path):
		print("No save file found, using defaults")
		return

	var file = FileAccess.open(save_path, FileAccess.READ)
	if file:
		var json_string = file.get_as_text()
		file.close()

		var json = JSON.new()
		var error = json.parse(json_string)
		if error == OK:
			var data = json.get_data()
			high_score = data.get("high_score", 0)
			coins = data.get("coins", 0)
			upgrades = data.get("upgrades", upgrades)
			print("Game loaded")
		else:
			print("Error parsing save file")
