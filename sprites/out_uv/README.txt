UV-lookup sprites
=================
*_uv_sheet.png   frames across, 32 directions down (a00..a31; dir 8 faces screen right, dir 16 faces the camera), 40x40 cells, origin (20,30)
                 pixel = (R: skin texel x, G: skin texel y, B: tone*40, A)
skin_*.png       96x24 skin atlas. Paint these. Body parts are 'unwrapped' as 4 panels: [left | front | right | back]
                 Players get their own atlas from data/players.csv (tool: looks.player_skin).
animations.json  cell, origin, directions, atlas regions, and per animation: frames, ms_per_frame, loop, events, root_forward_px
uv_skin.gdshader Godot 4 shader that applies a skin atlas to a sheet
hair/            hair layer sheets, same layout as the body sheets

Sheets are root-centred: move the player node in code using root_forward_px from animations.json.
Import with nearest filtering, no mipmaps, lossless, and no colour-space conversion.
The tool's EXPORT TO GAME button copies all of this into godot/ (see godot/README.md).
