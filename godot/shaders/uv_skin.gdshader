shader_type canvas_item;
// Godot 4. Put this on a Sprite2D/AnimatedSprite2D that shows a *_uv_sheet.png frame.
// Import the sheet with: Filter = Nearest, Mipmaps = off, Compress = Lossless, no sRGB/"source_color" hint.
uniform sampler2D skin : filter_nearest, repeat_disable;

const vec3 TONE_MUL[6] = vec3[6](
    vec3(0.55, 0.52, 0.72), vec3(0.78, 0.76, 0.90), vec3(1.0), vec3(0.72),
    vec3(0.45, 0.42, 0.60), vec3(0.32, 0.30, 0.42));
const vec3 TONE_ADD[6] = vec3[6](
    vec3(0.0), vec3(0.0), vec3(0.0), vec3(0.28 * 1.0, 0.28 * 0.96, 0.28 * 0.88),
    vec3(0.0), vec3(0.0));

void fragment() {
    vec4 m = texture(TEXTURE, UV);
    if (m.a < 0.5) { discard; }
    ivec2 texel = ivec2(int(m.r * 255.0 + 0.5), int(m.g * 255.0 + 0.5));
    vec3 base = texelFetch(skin, texel, 0).rgb;
    int tone = clamp(int(m.b * 255.0 / 40.0 + 0.5), 0, 5);
    COLOR = vec4(base * TONE_MUL[tone] + TONE_ADD[tone], 1.0);
}
