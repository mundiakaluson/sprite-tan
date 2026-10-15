class_name AiBehaviour
extends Resource
## One thing a player can decide to do, as its own small script. Make a new one by extending this class (see ai_jockey.gd), write `wants()` (when) and `act()` (what), save it as a
## .tres in scenes/ai/behaviours/ and add it to AiProfile > Behaviours. No other file changes: AiRole.think tries the list, top to bottom, for every player whose role and situation
## match, BEFORE the role's own five cases (and after the formation file). The first behaviour whose `wants()` says yes decides what the player does this frame.

const RECEIVING := 1       ## he is the intended target of a pass and the ball is on its way
const WITH_BALL := 2       ## he has the ball
const SUPPORT := 4         ## his team has the ball (someone else carries it)
const LOOSE := 8           ## nobody has the ball
const DEFENDING := 16      ## the other team has the ball

@export var enabled := true
## role ids this applies to (GK CB LB RB CDM CM CAM LW RW ST); empty = every role
@export var roles := PackedStringArray()
## which situations it is asked about (so `wants()` need not check them)
@export_flags("Receiving:1", "With ball:2", "Support:4", "Loose:8", "Defending:16") var when := 16

## yes = this behaviour decides for him now. f = the player, c = what his team sees (c.carrier, c.ball, c.other, c.own_goal(), c.nearest_opponent(pos), c.s = settings ...), role = his role resource
func wants(_f: Footballer, _c: AiContext, _role: AiRole) -> bool:
	return false

## what he does (move_to / speed / action, see AiIntent); only called when wants() said yes
func act(_f: Footballer, _c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	return null

# ---------------------------------------------------------------- used by AiRole.think
func applies(f: Footballer, situation: int) -> bool:
	if not enabled or (when & situation) == 0: return false
	return roles.is_empty() or f.role in roles

static func situation_of(f: Footballer, c: AiContext) -> int:
	if c.game.pass_target == f and c.carrier == null: return RECEIVING
	if c.carrier == f: return WITH_BALL
	if c.has_ball: return SUPPORT
	if c.carrier == null: return LOOSE
	return DEFENDING
