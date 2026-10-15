class_name PitchMap
extends RefCounted
## Named areas and spots of the pitch, so the AI can say "go to the left half space" or "hold at the edge of their box" instead of writing numbers.
## The data is in data/pitch_zones.csv (areas) and data/pitch_spots.csv (points); edit them in the manager tool (Other tables). Add a row, use the id in code.
## Coordinates in the CSVs are percentages in the TEAM's frame, like the formation slots: x 0-100 across (0 = the team's left, facing the opponent goal),
## y 0-100 from the team's own goal (0) to the opponent goal (100). Pass the team's `dir` (+1 attacks towards +x, -1 towards -x) and you get world metres.
## Static: usable from anywhere (AI, rules, HUD). AiContext wraps it as c.spot("id"), c.zone("id"), c.in_zone(pos, "id"), c.zones_at(pos).

static var _zones := {}
static var _spots := {}

static func reload() -> void:
	_zones.clear()
	_spots.clear()

static func _load() -> void:
	if not _zones.is_empty(): return
	for r in Data.table("pitch_zones"): _zones[r["id"]] = r
	for r in Data.table("pitch_spots"): _spots[r["id"]] = r
	if _zones.is_empty(): push_warning("PitchMap: no data/pitch_zones.csv (run Export to game)")

## team-frame percentages -> world metres
static func to_world(x_pct: float, y_pct: float, dir := 1.0) -> Vector2:
	return Vector2((y_pct / 100.0 - 0.5) * Stadium.L * dir, (x_pct / 100.0 - 0.5) * Stadium.W * dir)

## world metres -> team-frame percentages (x across, y along)
static func to_percent(pos: Vector2, dir := 1.0) -> Vector2:
	return Vector2((pos.y * dir / Stadium.W + 0.5) * 100.0, (pos.x * dir / Stadium.L + 0.5) * 100.0)

static func has_spot(id: String) -> bool:
	_load()
	return _spots.has(id)

static func spot(id: String, dir := 1.0) -> Vector2:
	_load()
	if not _spots.has(id):
		push_warning("PitchMap: no spot '%s' in pitch_spots.csv" % id)
		return Vector2.ZERO
	var r: Dictionary = _spots[id]
	return to_world(Data.num(r["x"]), Data.num(r["y"]), dir)

## the area as a world rectangle (always positive size, whatever the direction)
static func rect(id: String, dir := 1.0) -> Rect2:
	_load()
	if not _zones.has(id):
		push_warning("PitchMap: no zone '%s' in pitch_zones.csv" % id)
		return Rect2()
	var r: Dictionary = _zones[id]
	var a := to_world(Data.num(r["x0"]), Data.num(r["y0"]), dir)
	var b := to_world(Data.num(r["x1"]), Data.num(r["y1"]), dir)
	return Rect2(a, Vector2.ZERO).expand(b)

static func centre(id: String, dir := 1.0) -> Vector2:
	return rect(id, dir).get_center()

static func contains(id: String, pos: Vector2, dir := 1.0) -> bool:
	return rect(id, dir).has_point(pos)

## every zone id the point is inside
static func zones_at(pos: Vector2, dir := 1.0) -> Array:
	_load()
	var out: Array = []
	for id in _zones:
		if rect(id, dir).has_point(pos): out.append(id)
	return out

static func random_in(id: String, rng: RandomNumberGenerator, dir := 1.0) -> Vector2:
	var r := rect(id, dir)
	return Vector2(rng.randf_range(r.position.x, r.end.x), rng.randf_range(r.position.y, r.end.y))
