import sys, numpy as np
from PIL import Image, ImageDraw
import gen_uv as U, gen_hair as H
from gen_uv import CW, CH, OX, OY, apply_skin, DIRS, centered, bg_pitch, make_skin, SKINS
from gen_actions import BASE, run_pose, DEFAULT
poses=[dict(DEFAULT, **run_pose(BASE, k/12.0, 0.0)) for k in range(12)]
pose=centered(poses[3])
colors={'black':(24,18,26),'brown':(98,66,42),'blonde':(214,170,76),'ginger':(176,82,40)}
dirs=[DIRS[i*U.NDIR//8] for i in (0,1,2,4,6)]
S=14
# crop around the head
HX,HY=OX-9,OY-27
tw,th=18,16
sheet=Image.new('RGB',(tw*S*5, (th*S+4)*10),(60,120,64))
d=ImageDraw.Draw(sheet)
for si,style in enumerate(H.STYLE_ORDER):
    skin=make_skin(dict(SKINS['home'],hair=colors['brown'],hair_style=style))
    chains=H.simulate(style,poses,True,'run')[3]
    for di,dn in enumerate(dirs):
        sc,info=U.build_scene(pose,dn)
        body=apply_skin(U.finish_uv(sc),skin)
        hl=apply_skin(H.hair_layer(sc,info,style,chains),skin)
        tile=Image.new('RGBA',(CW,CH),(78,150,74,255)); tile.alpha_composite(body); tile.alpha_composite(hl)
        crop=tile.crop((HX,HY,HX+tw,HY+th)).resize((tw*S,th*S),Image.NEAREST).convert('RGB')
        sheet.paste(crop,(di*tw*S, si*(th*S+4)))
    d.text((3,si*(th*S+4)+2),style,fill=(255,255,255))
sheet.save('hair_test.png'); print(sheet.size)
