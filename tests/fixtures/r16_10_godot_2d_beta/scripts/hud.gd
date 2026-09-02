extends CanvasLayer

var frames_seen: int = 0

func _process(_delta: float) -> void:
    frames_seen += 1
