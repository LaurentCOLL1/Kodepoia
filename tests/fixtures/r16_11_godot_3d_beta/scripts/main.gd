extends Node3D

var elapsed_seconds: float = 0.0

func _process(delta: float) -> void:
    elapsed_seconds += delta
