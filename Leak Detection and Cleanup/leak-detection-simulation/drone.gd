extends CharacterBody3D

@export var mouse_sensitivity := 0.002
@export var pitch_limit := deg_to_rad(89)
@export var speed := 6

@onready var camera_pivot = $CameraPivot # Assumes Node3D pivot
@onready var camera = $CameraPivot/Camera3D

var _pitch := 0.0

func _ready():
	# Capture the mouse for FPS controls
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event):
	# Toggle mouse capture with ESC
	if event.is_action_pressed("ui_cancel"):
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		else:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

	# Handle mouse motion
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		# 1. Rotate body horizontally (Yaw)
		rotate_y(-event.relative.x * mouse_sensitivity)
		
		# 2. Rotate pivot vertically (Pitch)
		_pitch -= event.relative.y * mouse_sensitivity
		_pitch = clamp(_pitch, -pitch_limit, pitch_limit)
		camera_pivot.rotation.x = _pitch
			
func _physics_process(delta):
	if Input.is_action_pressed("mouse_click"):
		var forward: Vector3 = camera_pivot.global_transform.basis.z
		velocity = forward.normalized() * speed
	else: 
		velocity = Vector3.ZERO
			
	move_and_slide()
