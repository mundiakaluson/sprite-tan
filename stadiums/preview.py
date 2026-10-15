"""Software preview of the stadium as the TV camera sees it (same camera maths and same geometry as godot/scripts/stadium/stadium.gd).
Used by the tool's Stadiums and Goal simulator tabs. No Tk in here.
    img = render(row, cam=Cam(...), size=(960, 540))"""
import math
import numpy as np
from PIL import Image, ImageDraw
import stadiumlib as SL
import goallib as GL

L, W = SL.LEN, SL.WID


class Cam:
    """pinhole camera behind the near touchline, aimed at (x, 0, look_z). Matches Godot's Camera3D with look_at (vertical fov)."""
    def __init__(self, height=26.0, back=16.0, look_z=-4.0, fov=34.0, x=0.0, size=(960, 540)):
        self.size = size; self.pos = np.array([x, height, W / 2 + back], float); tgt = np.array([x, 0.0, look_z])
        self.fwd = tgt - self.pos; self.fwd /= np.linalg.norm(self.fwd); self.right = np.cross(self.fwd, [0, 1, 0]); self.right /= np.linalg.norm(self.right); self.up = np.cross(self.right, self.fwd)
        self.f = (size[1] / 2) / math.tan(math.radians(fov) / 2)

    @classmethod
    def look(cls, pos, target, fov=40.0, size=(960, 540)):
        c = cls(size=size, fov=fov); c.pos = np.array(pos, float); tgt = np.array(target, float); c.fwd = tgt - c.pos; c.fwd /= np.linalg.norm(c.fwd)
        c.right = np.cross(c.fwd, [0, 1, 0]); c.right /= np.linalg.norm(c.right); c.up = np.cross(c.right, c.fwd); return c

    @classmethod
    def from_row(cls, row, x=0.0, size=(960, 540)):
        return cls(SL.num(row.get('cam_height'), 26), SL.num(row.get('cam_back'), 16), SL.num(row.get('look_z'), -4), SL.num(row.get('fov'), 34), x, size)

    def project(self, p):
        """3D point(s) -> (screen x, screen y, depth)"""
        p = np.atleast_2d(np.array(p, float)) - self.pos; z = p @ self.fwd; z = np.where(np.abs(z) < 1e-6, 1e-6, z)
        return self.size[0] / 2 + self.f * (p @ self.right) / z, self.size[1] / 2 - self.f * (p @ self.up) / z, z

    def pt(self, p):
        x, y, z = self.project(p); return float(x[0]), float(y[0]), float(z[0])


def _rays(cam):
    if getattr(cam, '_rays', None) is None:
        W0, H0 = cam.size; xs = np.arange(W0) + 0.5 - W0 / 2; ys = np.arange(H0) + 0.5 - H0 / 2
        cam._rays = cam.fwd * cam.f + xs[None, :, None] * cam.right - ys[:, None, None] * cam.up
    return cam._rays


def warp(canvas, tex, tl, tr, br, bl, cam, rep=1.0):
    """draw the texture on the 3D quad (corners in texture order tl, tr, br, bl) by intersecting each screen ray with the quad's plane (no clipping trouble near the camera).
    rep = how many times the texture repeats along the top edge."""
    O = np.array(tl, float); U = np.array(tr, float) - O; V = np.array(bl, float) - O; n = np.cross(U, V); rays = _rays(cam)
    denom = rays @ n; denom = np.where(np.abs(denom) < 1e-9, 1e-9, denom); t = ((O - cam.pos) @ n) / denom
    hit = cam.pos + t[..., None] * rays - O; u = (hit @ U) / (U @ U); v = (hit @ V) / (V @ V)
    m = (t > 0) & (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    if not m.any(): return
    ta = np.asarray(tex.convert('RGBA')); th, tw = ta.shape[:2]
    tx = (np.floor((u[m] * rep) % 1.0 * tw)).astype(int).clip(0, tw - 1); ty = np.floor(v[m] * th).astype(int).clip(0, th - 1)
    arr = np.array(canvas); px = ta[ty, tx].astype(np.float32); a = px[:, 3:4] / 255.0
    arr[m, :3] = (arr[m, :3] * (1 - a) + px[:, :3] * a).astype(np.uint8); canvas.paste(Image.fromarray(arr, canvas.mode))


def poly(canvas, cam, corners, color):
    pts = [cam.pt(c) for c in corners]
    if min(p[2] for p in pts) < 0.5: return
    ImageDraw.Draw(canvas).polygon([(p[0], p[1]) for p in pts], fill=tuple(color) + (255,))


def line3(draw, cam, a, b, fill, width=1):
    pa, pb = cam.pt(a), cam.pt(b)
    if pa[2] > 0.5 and pb[2] > 0.5: draw.line([pa[:2], pb[:2]], fill=fill, width=width)


def draw_goal(canvas, cam, net, side, row=None, alpha=None):
    """the goal frame and net (net = goallib.Net, side -1 = own goal on the left, +1 = right). Posts and bar sway with net.posts."""
    d = ImageDraw.Draw(canvas, 'RGBA'); g = net.g; x0 = side * L / 2; P = net.p
    ncol = tuple(int(g['net_color'][i:i + 2], 16) for i in (1, 3, 5)); pcol = tuple(int(g['post_color'][i:i + 2], 16) for i in (1, 3, 5))
    na = int(SL.num(g.get('net_alpha'), 200) if alpha is None else alpha)
    W3 = lambda p: (x0 + side * p[0], p[1], p[2])
    pts = [W3(p) for p in P]; sc = cam.project(np.array(pts)); sx, sy, sz = sc
    for a, b in net.edges:
        if sz[a] > 0.5 and sz[b] > 0.5: d.line([(sx[a], sy[a]), (sx[b], sy[b])], fill=ncol + (na,), width=1)
    sway = net.posts; hw, h = net.hw, net.h; wl, wr, wb = sway['left'].x, sway['right'].x, sway['bar'].x
    lt = W3((wl * GL.SWAY_SCALE, h, -hw)); rt = W3((wr * GL.SWAY_SCALE, h, hw)); lb = W3((0, 0, -hw)); rb = W3((0, 0, hw))
    wd = max(2, int(cam.f * net.pr * 2 / max(1.0, cam.pt(lb)[2])))
    line3(d, cam, lb, lt, pcol + (255,), wd); line3(d, cam, rb, rt, pcol + (255,), wd)
    line3(d, cam, (lt[0], lt[1] + wb * GL.SWAY_SCALE * 0.5, lt[2]), (rt[0], rt[1] + wb * GL.SWAY_SCALE * 0.5, rt[2]), pcol + (255,), wd)


def render(row, cam=None, size=(960, 540), nets=None, cache=None, ball=None, goals=True):
    """full stadium frame. nets: {-1: Net, 1: Net} to draw (else static nets for the row's goal style). cache: dict reused between calls for the textures."""
    cam = cam or Cam.from_row(row, size=size); cache = {} if cache is None else cache
    key = tuple(row.get(k) for k in ('grass_a', 'grass_b', 'mow', 'worn', 'time', 'towers', 'light', 'stand', 'seat', 'stand_trim', 'crowd', 'crowd_colors', 'board', 'id'))
    if cache.get('key') != key: cache.update(key=key, pitch=SL.render_pitch(row), stand=SL.render_stand(row), boards=SL.render_boards(row))
    sky = SL.SKY[row.get('time', 'day')]; canvas = Image.new('RGBA', size, sky + (255,)); apr = SL.APR; hx, hz = L / 2 + apr, W / 2 + apr
    stand_col = tuple(int(v * 0.45) for v in SL.hexrgb(row['stand'])); rise, run, yb = 14.0, 17.0, 1.0; sx = hx + 14.0
    poly(canvas, cam, [(-sx, yb + rise, -hz - 1 - run), (sx, yb + rise, -hz - 1 - run), (sx, yb + rise + 16, -hz - 1 - run), (-sx, yb + rise + 16, -hz - 1 - run)], stand_col)
    st = cache['stand']
    warp(canvas, st, (-sx, yb + rise, -hz - 1 - run), (sx, yb + rise, -hz - 1 - run), (sx, yb, -hz - 1), (-sx, yb, -hz - 1), cam, rep=sx * 2 / 58)
    for s in (-1.0, 1.0):
        ex, ox = s * (hx + 1), s * run; rp = (hz * 2 + 9) / 58
        warp(canvas, st, (ex + ox, yb + rise, -hz - 1 - run), (ex + ox, yb + rise, hz + 8), (ex, yb, hz + 8), (ex, yb, -hz - 1), cam, rep=rp)
    warp(canvas, cache['pitch'], (-hx, 0, -hz), (hx, 0, -hz), (hx, 0, hz), (-hx, 0, hz), cam)
    bm = cache['boards']
    warp(canvas, bm, (-hx, 1, -hz), (hx, 1, -hz), (hx, 0, -hz), (-hx, 0, -hz), cam, rep=hx * 2 / 32)
    for s in (-1.0, 1.0): warp(canvas, bm, (s * hx, 1, -hz), (s * hx, 1, hz), (s * hx, 0, hz), (s * hx, 0, -hz), cam, rep=hz * 2 / 32)
    d = ImageDraw.Draw(canvas, 'RGBA')
    for cx in (-L / 2, L / 2):                                                                     # corner flags
        for cz in (-W / 2, W / 2):
            line3(d, cam, (cx, 0, cz), (cx, 1.5, cz), (245, 245, 235, 255), 2); line3(d, cam, (cx, 1.4, cz), (cx + 0.4, 1.3, cz), (237, 70, 50, 255), 3)
    if str(row.get('towers', '0')) == '1':
        for tx in (-hx - 6, hx + 6):
            for tz in (-hz - 8, hz + 8):
                line3(d, cam, (tx, 0, tz), (tx, 32, tz), (60, 64, 74, 255), 3); line3(d, cam, (tx - 3.5, 33.5, tz), (tx + 3.5, 33.5, tz), (255, 247, 210, 255), 7)
    if goals:
        gs = GL.style(row.get('goal', 'G01'))
        nets = nets or {-1: GL.Net(gs), 1: GL.Net(gs)}
        for side in (-1, 1): draw_goal(canvas, cam, nets[side], side)
    if ball is not None:
        bx, by, bz = ball; px, py, pz = cam.pt((bx, by, bz)); gx, gy, _ = cam.pt((bx, 0, bz)); r = max(2, cam.f * 0.11 / pz)
        d.ellipse([gx - r * 1.1, gy - r * 0.4, gx + r * 1.1, gy + r * 0.4], fill=(0, 0, 0, 90)); d.ellipse([px - r, py - r, px + r, py + r], fill=(250, 250, 250, 255), outline=(30, 30, 30, 255))
    return canvas.convert('RGB')


if __name__ == '__main__':
    import sys, time
    rows = SL.load(); out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/stad3'
    import os; os.makedirs(out, exist_ok=True)
    for r in rows:
        t0 = time.time(); render(r, cam=Cam.from_row(r, x=0)).save(os.path.join(out, r['id'] + '.png')); print(r['id'], round(time.time() - t0, 2), 's')
