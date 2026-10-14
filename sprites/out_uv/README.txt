UV-lookup sprites
=================
*_uv_sheet.png   frames across, 8 directions down (S, SE, E, NE, N, NW, W, SW), 56x56 cells, origin (28,42)
                 pixel = (R: skin texel x, G: skin texel y, B: tone*40, A)
skin_*.png       96x24 skin atlas. Paint these. skin_template_8x.png shows the regions.
                 Body parts are 'unwrapped' as 4 panels: [left | front | right | back]
animations.json  frame counts, timing, strike/contact frames, root motion per frame
uv_skin.gdshader Godot 4 shader that applies a skin atlas to a sheet

Sheets are root-centred: move the player node in code using root_forward_px from animations.json.
Import with nearest filtering, no mipmaps, lossless, and no colour-space conversion.
