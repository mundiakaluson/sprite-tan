shader_type canvas_item;
// The pixel-art ball: wraps an equirectangular panel map (assets/balls/<id>_map.png) round a 14 px sphere and turns it with the ball's real orientation, so any spin works
// (rolling, backspin, a trivela's tilted axis, a knuckle ball that barely turns). Mirrors balls/balllib.py render_orient(): keep them in step.
// Put it on a 16x16 Sprite2D. The pixel grid stays 16x16 whatever the sprite scale.

uniform sampler2D map : filter_nearest, repeat_enable;
uniform mat3 orient = mat3(1.0);        // ball-local -> view space (x right, y up, z towards the viewer); set by Ball
uniform float shine = 1.0;

const float R = 7.0;
const vec3 LIGHT = vec3(-0.45, 0.6, 0.66);

void fragment() {
	vec2 px = floor(UV * 16.0) + vec2(0.5);
	vec2 p = vec2((px.x - 8.0) / R, -(px.y - 8.0) / R);
	float r2 = dot(p, p);
	if (r2 > 1.0) {
		COLOR = vec4(0.0);
	} else {
		vec3 n = vec3(p, sqrt(max(0.0, 1.0 - r2)));
		vec3 nl = n * orient;                                   // = transpose(orient) * n: the point on the ball that faces us
		float lon = atan(nl.z, nl.x);
		float lat = asin(clamp(nl.y, -1.0, 1.0));
		vec3 col = texture(map, vec2(lon / TAU + 0.5, 0.5 - lat / PI)).rgb;
		float lam = clamp(dot(n, normalize(LIGHT)), 0.0, 1.0);
		float mult = lam < 0.18 ? 0.74 : (lam < 0.5 ? 0.88 : (lam < 0.8 ? 1.0 : 1.08));
		col = clamp(col * mult, 0.0, 1.0);
		if (shine > 0.5 && lam > 0.93) col = vec3(1.0);
		float edge = 1.0 - 2.0 / R;
		if (r2 > edge * edge) col *= 0.62;
		COLOR = vec4(col, 1.0);
	}
}
