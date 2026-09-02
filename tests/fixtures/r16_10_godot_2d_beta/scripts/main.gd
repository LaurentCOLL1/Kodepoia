extends Node2D

@export var player_profile: Resource
var elapsed_seconds: float = 0.0

func _process(delta: float) -> void:
    elapsed_seconds += delta
