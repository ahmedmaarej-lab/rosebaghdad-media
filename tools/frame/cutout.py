"""Cut a bottle photo (white background) to a transparent PNG: python3 tools/frame/cutout.py <key> ..."""
import sys,os,numpy as np
from PIL import Image,ImageFilter
from scipy import ndimage as ndi
H=os.path.dirname(os.path.abspath(__file__))
for k in sys.argv[1:]:
    im=Image.open(f'{H}/../reel/bottles/{k}.jpg').convert('RGB');a=np.asarray(im).astype(int)
    white=(a.min(2)>243)&((a.max(2)-a.min(2))<10)
    lab,n=ndi.label(white);edge=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bg=np.isin(lab,list(edge));bg=ndi.binary_dilation(bg,iterations=2)
    al=Image.fromarray(((~bg)*255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))
    out=im.filter(ImageFilter.UnsharpMask(radius=2,percent=70,threshold=2)).convert('RGBA');out.putalpha(al)
    out.save(f'{H}/cut/{k}.png');print(k,out.size,round(bg.mean(),2))
