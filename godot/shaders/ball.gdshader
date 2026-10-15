shader_type canvas_item;
// The pixel-art ball: wraps an equirectangular panel map (assets/balls/<id>_map.png) round a 14 px sphere and turns it with the ball's real orientation, so any spin works
// (rolling, backspin, a trivela's tilted axis, a knuckle ball that barely turns). Mirrors balls/balllib.py render_orient(): keep them in step.
// Put it on a 16x16 Sprite2D. The pixel grid stays 16x16 whatever the sprite scale.
// The orientation is passed as the ball's three local axes expressed in view space (x right, y up, z towards the viewer); Ball sets them.

uniform sampler2D map : filter_nearest, repeat_enable;
uniform vec3 axis_x = vec3(1.0, 0.0, 0.0);
uniform vec3 axis_y = vec3(0.0, 1.0, 0.0);
uniform vec3 axis_z = vec3(0.0, 0.0, 1.0);
uniform float shine = 1.0;

void fragment() {
	float radius = 7.0;
	vec2 px = floor(UV * 16.0) + vec2(0.5, 0.5);
	vec2 p = vec2((px.x - 8.0) / radius, -(px.y - 8.0) / radius);
	float r2 = dot(p, p);
	vec4 result = vec4(0.0, 0.0, 0.0, 0.0);
	if (r2 <= 1.0) {
		vec3 n = vec3(p.x, p.y, sqrt(max(0.0, 1.0 - r2)));
		vec3 nl = vec3(dot(n, axis_x), dot(n, axis_y), dot(n, axis_z));     // the point of the ball that faces us
		float lon = atan(nl.z, nl.x);
		float lat = asin(clamp(nl.y, -1.0, 1.0));
		vec3 col = texture(map, vec2(lon / 6.28318530718 + 0.5, 0.5 - lat / 3.14159265359)).rgb;
		vec3 light = normalize(vec3(-0.45, 0.6, 0.66));
		float lam = clamp(dot(n, light), 0.0, 1.0);
		float mult = 1.08;
		if (lam < 0.8) { mult = 1.0; }
		if (lam < 0.5) { mult = 0.88; }
		if (lam < 0.18) { mult = 0.74; }
		col = clamp(col * mult, vec3(0.0), vec3(1.0));
		if (shine > 0.5 && lam > 0.93) { col = vec3(1.0, 1.0, 1.0); }
		float edge = 1.0 - 2.0 / radius;
		if (r2 > edge * edge) { col = col * 0.62; }
		result = vec4(col, 1.0);
	}
	COLOR = result;
}
