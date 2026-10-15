class_name AiClearBall
extends AiBehaviour

@export_group("Clear ball")
@export var min_range := 20.0
@export var max_range := 40.0

func _init() -> void:
    roles = PackedStringArray(["CB", "LB", "RB"])
    when = DEFENDING

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
    var carrier := c.carrier
    if carrier == null or not carrier.is_keeper(): return false
    var d := f.pos.distance_to(carrier.pos)
    return d > min_range and d < max_range

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
    var carrier := c.carrier
    var i := AiIntent.new()
    i.move_to = c.clamp_pitch(carrier.pos + (c.own_goal() - carrier.pos).normalized() * 5.0, 1.0)
    i.speed = c.s.sprint_factor
    i.note = "clear ball"
    return i