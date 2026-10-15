class_name AiFormation
extends Resource
## Base of a formation's team play. A formation file (one per formation, in scripts/ai/formations/) decides what each ROLE does inside that formation
## where it differs from the plain role AI: banks, press triggers, who drops and who stays, overlaps. Add the file's resource to AiProfile > Formations
## and list the ids it covers (data/formations.csv). think() returns an AiIntent, or null to let the role's own AI decide.

## formation ids this applies to, e.g. ["F01"]
@export var formation_ids: PackedStringArray = []

func think(_f: Footballer, _c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	return null
