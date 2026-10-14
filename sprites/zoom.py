import sys
from PIL import Image
name, row, frames, S = sys.argv[1], int(sys.argv[2]), [int(x) for x in sys.argv[3].split(',')], int(sys.argv[4])
im = Image.open(f'out_actions/{name}_sheet.png').convert('RGBA')
CW, CH = 72, 84
W = CW*len(frames)
bg = Image.new('RGBA', (W, CH), (80,150,76,255))
for i,k in enumerate(frames):
    bg.alpha_composite(im.crop((k*CW,row*CH,(k+1)*CW,(row+1)*CH)),(i*CW,0))
bg.resize((W*S,CH*S),Image.NEAREST).convert('RGB').save('zoom.png'); print(W*S, CH*S)
