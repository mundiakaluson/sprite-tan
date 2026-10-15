shader_type canvas_item;
// Godot 4. Put this on a Sprite2D/AnimatedSprite2D that shows a *_uv_sheet.png frame.
// Import the sheet with: Filter = Nearest, Mipmaps = off, Compress = Lossless, no sRGB/"source_color" hint.
// The kit parts of the look atlas are painted in fixed KEY colours (tool/looks.py KEY_KIT); with use_kit on they are swapped for the team's colours.
uniform sampler2D skin : filter_nearest, repeat_disable;
uniform bool use_kit = false;
uniform vec3 kit_jersey = vec3(0.84, 0.2, 0.25);
uniform vec3 kit_trim = vec3(0.96);
uniform vec3 kit_shorts = vec3(0.94);
uniform vec3 kit_shorts_trim = vec3(0.84, 0.2, 0.25);
uniform vec3 kit_stripe = vec3(0.84, 0.2, 0.25);
uniform vec3 kit_socks = vec3(0.84, 0.2, 0.25);
uniform vec3 kit_sock_trim = vec3(0.96);
uniform vec3 kit_boots = vec3(0.94);
uniform vec3 kit_accent = vec3(0.14, 0.14, 0.24);
uniform vec3 kit_glove = vec3(0.9, 0.94, 0.24);

const vec3 TONE_MUL[6] = vec3[6](
    vec3(0.55, 0.52, 0.72), vec3(0.78, 0.76, 0.90), vec3(1.0), vec3(0.72),
    vec3(0.45, 0.42, 0.60), vec3(0.32, 0.30, 0.42));
const vec3 TONE_ADD[6] = vec3[6](
    vec3(0.0), vec3(0.0), vec3(0.0), vec3(0.28 * 1.0, 0.28 * 0.96, 0.28 * 0.88),
    vec3(0.0), vec3(0.0));

bool is_key(vec3 c, float r, float g, float b) {
    return all(lessThan(abs(c * 255.0 - vec3(r, g, b)), vec3(3.0)));
}

vec3 swap_kit(vec3 c) {
    if (is_key(c, 255.0, 0.0, 0.0)) return kit_jersey;
    if (is_key(c, 0.0, 255.0, 0.0)) return kit_trim;
    if (is_key(c, 0.0, 0.0, 255.0)) return kit_shorts;
    if (is_key(c, 255.0, 255.0, 0.0)) return kit_shorts_trim;
    if (is_key(c, 255.0, 0.0, 255.0)) return kit_stripe;
    if (is_key(c, 0.0, 255.0, 255.0)) return kit_socks;
    if (is_key(c, 255.0, 128.0, 0.0)) return kit_sock_trim;
    if (is_key(c, 128.0, 0.0, 255.0)) return kit_boots;
    if (is_key(c, 70.0, 0.0, 140.0)) return kit_boots * 0.55;
    if (is_key(c, 0.0, 255.0, 128.0)) return kit_accent;
    if (is_key(c, 128.0, 255.0, 0.0)) return kit_glove;
    return c;
}

void fragment() {
    vec4 m = texture(TEXTURE, UV);
    if (m.a < 0.5) { discard; }
    ivec2 texel = ivec2(int(m.r * 255.0 + 0.5), int(m.g * 255.0 + 0.5));
    vec3 base = texelFetch(skin, texel, 0).rgb;
    if (use_kit) { base = swap_kit(base); }
    int tone = clamp(int(m.b * 255.0 / 40.0 + 0.5), 0, 5);
    COLOR = vec4(base * TONE_MUL[tone] + TONE_ADD[tone], 1.0);
}
