shader_type canvas_item;
// A flat-colour silhouette of a player frame (the afterimages of a zap). TEXTURE is the player's uv sheet; only its alpha is used.
uniform vec4 tint : source_color = vec4(0.35, 0.82, 1.0, 1.0);
uniform float alpha = 0.35;

void fragment() {
    vec4 m = texture(TEXTURE, UV);
    if (m.a < 0.5) { discard; }
    COLOR = vec4(tint.rgb, tint.a * alpha);
}
