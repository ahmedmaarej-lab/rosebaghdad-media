"""Starting frames for Roza videos: Roza's first frame with the real bottle of each perfume on the table.
python3 tools/roza/frames.py [key ...]   -> tools/roza/frames/<key>.jpg (1080x1920)
Upload the frame to Gemini as the starting image, so the girl, the room and the bottle stay the same."""
import os,sys,numpy as np
from PIL import Image,ImageFilter,ImageEnhance
from scipy import ndimage
H=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(os.path.dirname(H))
B=R+'/tools/reel/bottles'
BOX=(912,1122,1056,1462)       # where the bottle stands in the 1080x1920 frame (left, top, right, bottom)
def cut(path):
    im=Image.open(path).convert('RGB'); a=np.asarray(im).astype(int); mn=a.min(2); sat=a.max(2)-mn
    light=(mn>238)&(sat<14)
    lab,_=ndimage.label(light); e=np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])); e=e[e>0]
    fg=ndimage.binary_fill_holes(~np.isin(lab,e))
    al=Image.fromarray((fg*255).astype('uint8')).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    im.putalpha(al); return im.crop(im.getbbox())
def frame(key):
    base=Image.open(H+'/roza-base.jpg').convert('RGB').resize((1080,1920),Image.LANCZOS)
    b=cut(f'{B}/{key}.jpg')
    w,h=BOX[2]-BOX[0],BOX[3]-BOX[1]; s=min(w/b.width,h/b.height); b=b.resize((round(b.width*s),round(b.height*s)),Image.LANCZOS)
    rgb=b.convert('RGB'); rgb=ImageEnhance.Brightness(rgb).enhance(.80); rgb=ImageEnhance.Color(rgb).enhance(1.12)
    r,g,bl=rgb.split(); rgb=Image.merge('RGB',(r.point(lambda v:min(255,v*1.03)),g.point(lambda v:v*.97),bl.point(lambda v:v*.80))).filter(ImageFilter.GaussianBlur(.5))   # warm room light, soft like the render
    b=Image.merge('RGBA',(*rgb.split(),b.split()[3]))
    x=BOX[0]+(w-b.width)//2; y=BOX[3]-b.height
    sh=Image.new('L',base.size,0); sh.paste(b.split()[3].point(lambda v:v*.45),(x+10,y+6)); sh=sh.filter(ImageFilter.GaussianBlur(9))
    base=Image.composite(Image.new('RGB',base.size,(60,40,25)),base,sh)
    base.paste(b,(x,y),b); return base
if __name__=='__main__':
    keys=sys.argv[1:] or sorted(f[:-4] for f in os.listdir(B) if not f.startswith('incense'))
    os.makedirs(H+'/frames',exist_ok=True)
    for k in keys: frame(k).save(f'{H}/frames/{k}.jpg',quality=92); print(k)
