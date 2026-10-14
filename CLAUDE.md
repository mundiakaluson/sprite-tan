# Project notes for Claude

Pixel-art football manager-card game (see README.md). Design source of truth: the Claude Docs document
"Pixel Football Card Game - Design Document" (https://claude.ai/code/artifact/0d90f732-ad07-4972-8473-3f28f323153c),
summarised in docs/DECISIONS.md.

## Rules of engagement with the user
- Brainstorm first and write decisions into the design doc; put a checkpoint before each new stage. Do not start
  Godot or big builds until the user says so.
- Keep replies short and plain. Do not over-explain on card faces or in the UI.
- Data lives in CSVs under data/ and is loaded by the game at runtime, so keep columns stable and values tweakable.

## Conventions
- Sprite scripts import each other as top-level modules; run them from `sprites/`.
- Pitch coordinates: x 0-100 left to right, y 0-100 own goal to opponent goal.
- Roles: GK, CB, LB, RB, CDM, CM, CAM, LW, RW, ST. Outfield stats PAC SHO PAS DRI DEF PHY, keeper stats REF HAN POS.

## Tool status
Manager tool in tool/ is built (see README). Run `python tool/selftest.py` after changes. Custom animations live in data/animations/*.json and are
registered into sprites/gen_uv.py via sprites/custom_anims.py.

## Next up
1. Tool follow-ups: hair-style and kit editors, pack-odds simulator, Windows test pass, palette-swap shader for indexed export.
2. Card emblems for all 200 cards.
3. Godot skeleton loading the CSVs.
