extends CharacterBody3D

@export var speed := 5.0
@export var turn_speed := 8.0   # higher = snappier rotation

func _physics_process(delta):
	var dir := Vector3.ZERO

	if Input.is_action_pressed("ui_left"):
		dir.x -= 1
	if Input.is_action_pressed("ui_right"):
		dir.x += 1
	if Input.is_action_pressed("ui_up"):
		dir.z -= 1
	if Input.is_action_pressed("ui_down"):
		dir.z += 1

	if dir != Vector3.ZERO:
		dir = dir.normalized()

		# Move
		velocity.x = dir.x * speed
		velocity.z = dir.z * speed

		# Rotate to face movement direction
		var target_yaw := atan2(dir.x, dir.z)
		rotation.y = lerp_angle(rotation.y, target_yaw, turn_speed * delta)
	else:
		velocity.x = 0
		velocity.z = 0

	move_and_slide()
