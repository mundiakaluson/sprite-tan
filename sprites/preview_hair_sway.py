import json, numpy as np
from PIL import Image, ImageDraw
import gen_uv as U
from gen_uv import CW,CH,DIRS,apply_skin,make_skin,SKINS,bg_pitch
import gen_hair as H
meta=json.load(open('out_uv/animations.json'))
S=6
styles=['H07_braids','H08_long','H09_ponytail','H10_bun','H06_afro']
anims=['run','kick','finesse','slide']
dirs=[DIRS[i*U.NDIR//8] for i in (0,2,4,6)]   # front, east-ish, back, west-ish
cols={'H07_braids':(24,18,26),'H08_long':(214,170,76),'H09_ponytail':(176,82,40),'H10_bun':(98,66,42),'H06_afro':(24,18,26)}
frames=[]
bodies={a:Image.open(f'out_uv/{a}_uv_sheet.png').convert('RGBA') for a in anims}
hairs={(s,a):Image.open(f'out_uv/hair/{s}__{a}.png').convert('RGBA') for s in styles for a in anims}
skins={s:make_skin(dict(SKINS['home'],hair=cols[s],hair_style=s)) for s in styles}
def cell(sheet,r,k): return sheet.crop((k*CW,r*CH,(k+1)*CW,(r+1)*CH))
def tile(a,s,r,k):
    b=apply_skin(np.array(cell(bodies[a],r,k)),skins[s]); h=apply_skin(np.array(cell(hairs[(s,a)],r,k)),skins[s])
    t=Image.new('RGBA',(CW,CH),(78,150,74,255)); t.alpha_composite(b); t.alpha_composite(h); return t
for f in range(24):
    W_=CW*len(styles); Hh=CH*len(anims)*2
    bg=Image.new('RGBA',(W_,Hh),(78,150,74,255))
    for ai,a in enumerate(anims):
        n=meta['animations'][a]['frames']; k=f%n
        for si,s in enumerate(styles):
            for di,dn in enumerate((dirs[1],dirs[2])):
                r=DIRS.index(dn)
                bg.alpha_composite(tile(a,s,r,k),(si*CW,(ai*2+di)*CH))
    big=bg.resize((W_*S//2*1,Hh*S//2*1),Image.NEAREST).convert('RGB'); frames.append(big)
frames[0].save('hair_sway.gif',save_all=True,append_images=frames[1:],duration=70,loop=0)
print(frames[0].size)
