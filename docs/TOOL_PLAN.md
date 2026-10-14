# Manager tool plan (tool/)

Goal: a flexible Python tool for editing the game data and preparing sprites.

## Parts
1. **Data editors** (read and write the CSVs in data/): players (stats, roles, look pickers, rating from stats, live sprite
   preview), cards, formations (pitch view), pack-odds simulator, validation (10 outfield slots per formation, unique
   names, role lists valid, rarity counts).
2. **Flexible sprite import with colour-scheme change** (works on any sheet, not just ours):
   - Import a PNG sheet. Detect the grid (cell size, rows, frames) from transparent gaps; allow a manual override.
   - Detect colours: exact unique colours for clean pixel art, quantise first for anti-aliased art.
   - Group colours into ramps by hue (skin, kit, hair, white...), ordered dark to light. User can merge, split and relabel
     by clicking a pixel in the preview.
   - Assign each ramp a slot (skin, hair, jersey, shorts, socks, boots...), pick a target colour per slot, generate the
     matching ramp so shading is kept, live preview.
   - Export either baked recoloured PNGs, or (preferred) an indexed sheet plus a small palette image used by a
     palette-swap shader in Godot. This generalises what sprites/gen_uv.py already does.
   - Known limits: one exact colour used for two parts cannot be separated by colour alone (offer a painted mask on one
     frame); noisy or heavily anti-aliased art recolours less cleanly; imported sheets keep their own hair (colour only,
     no style swap); the user is responsible for rights to imported art.
3. **Per-player look export**: build each player's 96x24 look atlas from players.csv (skin tone, hair colour, beard,
   glasses, chain, headband, wristband, tattoo) and pick the hair layer sheet for their hair style. Body and animation
   sheets are shared, so exporting 300 players is just 300 small atlases. Kit colours come from the team and are
   composited with the player's look at load time (to be settled with the Godot side).

## Interface
Desktop app in tkinter (ships with Python, nothing extra to install): `python tool/app.py`. Logic lives in
`tool/sprite_core.py` (no GUI, testable). Data editors and the per-player atlas view come as extra tabs later.

## Build order
Grid and palette detection -> recolour with live preview -> indexed export and shader -> player/card/formation editors
-> per-player atlas export.
