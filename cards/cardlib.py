import sys, os, math, csv, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sprites'))
import numpy as np
from PIL import Image, ImageDraw
import gen_uv as U

# ------------------------------------------------------------ 3x5 pixel font
G = {
'A':'010101111101101','B':'110101110101110','C':'011100100100011','D':'110101101101110','E':'111100110100111',
'F':'111100110100100','G':'011100101101011','H':'101101111101101','I':'111010010010111','J':'001001001101010',
'K':'101101110101101','L':'100100100100111','M':'101111111101101','N':'110101101101101','O':'010101101101010',
'P':'110101110100100','Q':'010101101111011','R':'110101110101101','S':'011100010001110','T':'111010010010010',
'U':'101101101101111','V':'101101101101010','W':'101101111111101','X':'101101010101101','Y':'101101010010010',
'Z':'111001010100111','0':'111101101101111','1':'010110010010111','2':'111001111100111','3':'111001111001111',
'4':'101101111001001','5':'111100111001111','6':'111100111101111','7':'111001010010010','8':'111101111101111',
'9':'111101111001111','%':'101001010100101','-':'000000111000000','.':'000000000000010',' ':'000000000000000',
'/':'001001010100100',':':'000010000010000','+':'000010111010000','!':'010010010000010','?':'110001010000010',"'":'010010000000000','x':'101101010101101'}
def draw_text(im, x, y, txt, col, scale=1):
    px = im.load(); cx = x
    for ch in txt.upper() if False else txt:
        bits = G.get(ch.upper(), G[' ']); 
        for r in range(5):
            for c in range(3):
                if bits[r * 3 + c] == '1':
                    for sy in range(scale):
                        for sx in range(scale):
                            X, Y = cx + c * scale + sx, y + r * scale + sy
                            if 0 <= X < im.width and 0 <= Y < im.height: px[X, Y] = col
        cx += 4 * scale
    return cx
def text_w(txt, scale=1): return len(txt) * 4 * scale - scale

# ------------------------------------------------------------ palette per category
CAT = {
 'SHOT':   dict(main=(222, 76, 62),  dark=(96, 28, 30),  light=(255, 150, 120)),
 'PASS':   dict(main=(66, 132, 226), dark=(24, 48, 100), light=(140, 190, 255)),
 'DRIBBLE':dict(main=(70, 184, 108), dark=(22, 74, 48),  light=(150, 235, 160)),
 'SUPPORT':dict(main=(236, 198, 60), dark=(100, 78, 20), light=(255, 240, 140)),
 'DEFEND': dict(main=(48, 184, 176), dark=(16, 70, 74),  light=(130, 240, 225)),
 'KEEPER': dict(main=(146, 100, 220),dark=(52, 34, 96),  light=(200, 170, 255)),
 'TITAN':  dict(main=(255, 206, 70), dark=(60, 24, 90),  light=(255, 250, 200)),
}
INK = (14, 12, 26); PANEL = (30, 28, 50)
CW_, CH_ = 56, 80

def icon(d, x, y, cat, col):
    P = d.point
    pts = {
     'SHOT': [(3,0),(4,0),(5,0),(2,1),(6,1),(1,2),(7,2),(1,3),(4,3),(7,3),(1,4),(3,4),(4,4),(5,4),(7,4),(1,5),(7,5),(2,6),(6,6),(3,7),(4,7),(5,7)],
     'PASS': [(0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(5,2),(4,1),(5,4),(4,5),(6,3)],
     'DRIBBLE': [(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(1,2),(2,3),(3,4),(4,5),(5,6),(0,0)],
     'SUPPORT': [(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(0,3),(1,3),(2,3),(4,3),(5,3),(6,3)],
     'DEFEND': [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(0,1),(6,1),(0,2),(6,2),(0,3),(6,3),(1,4),(5,4),(2,5),(4,5),(3,6)],
     'KEEPER': [(1,3),(1,4),(2,1),(2,2),(2,3),(3,0),(3,1),(3,2),(4,1),(4,2),(5,2),(5,3),(2,4),(3,4),(4,4),(5,4),(2,5),(3,5),(4,5),(3,6)],
     'TITAN': [(4,0),(5,0),(3,1),(4,1),(2,2),(3,2),(2,3),(3,3),(4,3),(5,3),(4,4),(3,5),(4,5),(2,6),(3,6)],
    }[cat]
    for (px_, py_) in pts: P((x + px_, y + py_), col)

def make_skin_sprite(anim, k, di, skin='home'):
    sh = Image.open(f'/home/claude/out_uv/{anim}_uv_sheet.png').convert('RGBA')
    arr = np.array(sh.crop((k * 40, di * 40, (k + 1) * 40, (di + 1) * 40)))
    return U.apply_skin(arr, U.make_skin(U.SKINS[skin]))
_sk = {}
def sprite(anim, k, di, skin='home'):
    key = (anim, k, di, skin)
    if key not in _sk: _sk[key] = make_skin_sprite(anim, k, di, skin)
    return _sk[key]

def card_face(c, state='ready', t=0):
    cat = c['cat']; pal = CAT[cat]; im = Image.new('RGBA', (CW_, CH_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    titan = cat == 'TITAN'
    # frame
    d.rectangle([0, 0, CW_ - 1, CH_ - 1], fill=INK + (255,))
    d.rectangle([1, 1, CW_ - 2, CH_ - 2], fill=pal['main'] + (255,))
    d.rectangle([2, 2, CW_ - 3, CH_ - 3], fill=pal['dark'] + (255,) if titan else PANEL + (255,))
    if titan:
        for (x, y) in ((1, 1), (CW_ - 2, 1), (1, CH_ - 2), (CW_ - 2, CH_ - 2)):
            for dx in (-1, 0, 1):
                d.point((x + dx, y), (255, 120, 220, 255)); d.point((x, y + dx), (255, 120, 220, 255))
        d.rectangle([2, 2, CW_ - 3, 2], fill=(255, 120, 220, 255)); d.rectangle([2, CH_ - 3, CW_ - 3, CH_ - 3], fill=(255, 120, 220, 255))
    # top strip: slot gem + category label + icon
    d.rectangle([3, 3, 11, 11], fill=INK + (255,)); d.rectangle([4, 4, 10, 10], fill=(70, 80, 120, 255))
    draw_text(im, 6, 5, str(c['slots']), (255, 255, 255, 255))
    draw_text(im, 15, 5, cat, pal['light'] + (255,))
    icon(d, CW_ - 12, 3, cat, pal['light'] + (255,))
    # art window
    ax0, ay0, ax1, ay1 = 4, 13, CW_ - 5, 46
    for y in range(ay0, ay1 + 1):
        t_ = (y - ay0) / (ay1 - ay0)
        base = tuple(int(pal['dark'][i] * (1 - 0.5 * t_) + 20 * t_) for i in range(3))
        d.line([(ax0, y), (ax1, y)], fill=base + (255,))
    for x in range(ax0, ax1 + 1, 2):                       # dither band
        for y in range(ay0 + 14, ay0 + 22):
            if (x + y) % 4 == 0: d.point((x, y), tuple(min(255, v + 18) for v in pal['dark']) + (255,))
    d.ellipse([ax0 + 12, ay1 - 6, ax1 - 12, ay1 - 1], fill=(8, 8, 24, 140))
    spr = sprite(*c['art'][:3], skin=(c['art'][3] if len(c['art']) > 3 else 'home'))
    ax = (ax0 + ax1) // 2 - 20; ay = ay1 - 35
    layer = Image.new('RGBA', (CW_, CH_), (0, 0, 0, 0)); layer.alpha_composite(spr, (ax, ay))
    clip = Image.new('L', (CW_, CH_), 0); ImageDraw.Draw(clip).rectangle([ax0, ay0, ax1, ay1], fill=255)
    lm = np.array(layer); lm[..., 3] = np.minimum(lm[..., 3], np.array(clip)); im.alpha_composite(Image.fromarray(lm, 'RGBA'))
    if c.get('buff'):                                       # buff-window chip
        d.rectangle([ax0 + 1, ay0 + 1, ax0 + 17, ay0 + 7], fill=INK + (230,)); draw_text(im, ax0 + 3, ay0 + 2, 'BUFF', (255, 230, 120, 255))
    d.rectangle([ax0 - 1, ay0 - 1, ax1 + 1, ay1 + 1], outline=INK + (255,))
    # name plate
    d.rectangle([4, 48, CW_ - 5, 61], fill=INK + (255,)); d.rectangle([5, 49, CW_ - 6, 60], fill=pal['main'] + (255,))
    words = c['name'].upper().split(' ')
    if text_w(c['name']) <= CW_ - 12:
        draw_text(im, (CW_ - text_w(c['name'])) // 2, 52, c['name'].upper(), INK + (255,))
    else:
        mid = len(words) // 2 if len(words) > 1 else 1
        l1, l2 = ' '.join(words[:mid]), ' '.join(words[mid:])
        draw_text(im, (CW_ - text_w(l1)) // 2, 50, l1, INK + (255,)); draw_text(im, (CW_ - text_w(l2)) // 2, 56, l2, INK + (255,))
    # stat cells
    cells = [(f"{c['succ']}%", c['succ'], (96, 220, 120)), (f"R{c['risk']}", c['risk'], (236, 84, 76)), (f"{c['cd']}S", min(100, c['cd'] * 100 // 60), (110, 170, 250))]
    for ci, (lab, val, col) in enumerate(cells):
        x0 = 4 + ci * 17
        d.rectangle([x0, 63, x0 + 15, 75], fill=INK + (255,))
        draw_text(im, x0 + 2, 65, lab, col + (255,))
        d.rectangle([x0 + 2, 72, x0 + 13, 73], fill=(48, 48, 70, 255))
        d.rectangle([x0 + 2, 72, x0 + 2 + max(0, int(11 * val / 100)), 73], fill=col + (255,))
    # states
    arr = np.array(im)
    if state == 'cooldown':
        arr[..., :3] = (arr[..., :3] * 0.42).astype(np.uint8)
        cx, cy = CW_ // 2, 30
        ov = Image.fromarray(arr, 'RGBA'); od = ImageDraw.Draw(ov)
        od.pieslice([cx - 13, cy - 13, cx + 13, cy + 13], -90, -90 + 360 * (1 - t), fill=(8, 8, 20, 200))
        od.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], outline=(200, 205, 230, 255))
        im = ov
    elif state == 'unavailable':
        arr[..., :3] = (arr[..., :3] * 0.3).astype(np.uint8); im = Image.fromarray(arr, 'RGBA')
    return im

def glow(im, col, strength=2):
    big = Image.new('RGBA', (im.width + 8, im.height + 8), (0, 0, 0, 0)); a = np.array(im)[..., 3] > 0
    ga = np.zeros((im.height + 8, im.width + 8), bool)
    for dy in range(-strength - 1, strength + 2):
        for dx in range(-strength - 1, strength + 2):
            if abs(dx) + abs(dy) <= strength + 1:
                ys, xs = np.nonzero(a)
                ga[ys + 4 + dy, xs + 4 + dx] = True
    arr = np.zeros((im.height + 8, im.width + 8, 4), np.uint8); arr[ga] = col + (200,); big = Image.fromarray(arr, 'RGBA'); big.alpha_composite(im, (4, 4)); return big

def detail_panel(c, w=150, h=96):
    pal = CAT[c['cat']]; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=INK + (255,)); d.rectangle([1, 1, w - 2, h - 2], fill=pal['main'] + (255,)); d.rectangle([2, 2, w - 3, h - 3], fill=PANEL + (255,))
    draw_text(im, 6, 6, c['name'].upper(), pal['light'] + (255,), 1)
    draw_text(im, 6, 14, c['cat'] + ' CARD  ' + str(c['slots']) + ' SLOT' + ('S' if c['slots'] > 1 else ''), (150, 156, 190, 255))
    rows = [('SUCCESS', f"{c['succ']}%", (96, 220, 120)), ('RISK', f"{c['risk']}%", (236, 84, 76)), ('COOLDOWN', f"{c['cd']}S", (110, 170, 250))]
    for i, (lab, v, col) in enumerate(rows):
        y = 24 + i * 8
        draw_text(im, 6, y, lab, (170, 176, 208, 255)); draw_text(im, 56, y, v, col + (255,))
        d.rectangle([76, y + 1, 76 + 60, y + 3], fill=(48, 48, 70, 255))
        d.rectangle([76, y + 1, 76 + int(60 * min(100, (c['cd'] * 100 // 60) if lab == 'COOLDOWN' else int(v[:-1])) / 100), y + 3], fill=col + (255,))
    import textwrap
    y = 52
    for line in textwrap.wrap(c['effect'].upper(), (w - 12) // 4)[:3]:
        draw_text(im, 6, y, line, (235, 238, 250, 255)); y += 7
    draw_text(im, 6, h - 10, 'BEATEN BY: ' + c.get('beaten', '-').upper(), (255, 170, 150, 255))
    return im
