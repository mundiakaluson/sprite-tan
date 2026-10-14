"""Contact sheets for reviewing moves without opening the tool:  python moves_preview.py NAME [dir ...]
Shows every frame of an animation (built-in or data/animations/NAME.json) from the chosen directions, on turf, with the ball."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
import gen_uv as U

HERE = os.path.dirname(os.path.abspath(__file__))
_atlas = None


def atlas():
    global _atlas
    if _atlas is None:
        _atlas = np.array(Image.open(os.path.join(HERE, 'out_uv', 'skin_home.png')).convert('RGBA'))
    return _atlas


def poses_of(name):
    import custom_anims as C
    if name in C.files():
        return C.build_poses(C.load(name))
    return U.ANIMS[name][0]()[0]


def frame(pose, dn, prev=None):
    bg = U.bg_pitch(U.CW, U.CH)
    under, over = U.extras(U.centered(pose), dn)
    body = U.apply_skin(U.render_uv(U.centered(pose), dn, with_ball=pose.get('bvis', 0) > 0.5), atlas())
    bg.alpha_composite(under)
    gh = U.leg_trail(prev or [], pose, dn)
    if gh is not None: bg.alpha_composite(gh)
    bg.alpha_composite(body)
    bg.alpha_composite(over)
    return bg


def strip(poses, dirs=(8,), path='/tmp/strip.png', S=2, per_row=11, label=''):
    cells = []
    for d in dirs:
        for i, p in enumerate(poses):
            cells.append((d, i, frame(p, U.DIRS[d], poses[max(0, i - 3):i][::-1])))
    W, H = U.CW * S, U.CH * S
    rows = (len(cells) + per_row - 1) // per_row
    sheet = Image.new('RGBA', (per_row * W, rows * H), (30, 34, 46, 255))
    dr = ImageDraw.Draw(sheet)
    for n, (d, i, im) in enumerate(cells):
        x, y = (n % per_row) * W, (n // per_row) * H
        sheet.alpha_composite(im.resize((W, H), Image.NEAREST), (x, y)); dr.text((x + 3, y + 2), f'{i}', fill=(255, 255, 255, 255))
        if i == 0: dr.text((x + 3, y + H - 12), f'{label} a{d:02d}', fill=(255, 230, 120, 255))
    sheet.convert('RGB').save(path)
    return path


if __name__ == '__main__':
    name = sys.argv[1]; dirs = [int(a) for a in sys.argv[2:]] or [8]
    print(strip(poses_of(name), dirs, f'/tmp/strip_{name}.png', label=name))
