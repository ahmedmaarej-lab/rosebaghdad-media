"""Rose Baghdad incense: same jar, the name on the label changes. Cuts the jar out of its backdrop and
renders feed + story in the unified frame (name on top, jar below).  python3 tools/frame/incense.py"""
import asyncio,os,urllib.parse,io
from playwright.async_api import async_playwright
from PIL import Image,ImageFilter,ImageDraw,ImageChops
import numpy as np
N={'shaikha':('شيخه','تفاصيل تحبها بجلساتك'),'azizati':('عزيزتي','ريحة تستقبل ضيوفك قبلك'),'sayidati':('سيدتي','لمسة فخامة تكمل جلستك'),'fakher':('فاخر','بخور يليق بمجلسك'),'shurooq':('شروق','بيتك يستاهل ريحة تبقى بالبال')}
H=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(os.path.dirname(H))
def cut(im):
    """Remove the white studio backdrop: everything near-white that is connected to the picture edge."""
    a=np.asarray(im).astype(int); mn=a.min(axis=2); sat=a.max(axis=2)-mn
    from scipy import ndimage
    # backdrop = near-white OR the soft grey cast shadow (bright, colourless, smooth), grown in from the picture edge
    smooth=ndimage.uniform_filter(np.abs(ndimage.sobel(mn.astype(float))),9)<10
    low=np.zeros_like(smooth); low[int(mn.shape[0]*.72):]=True   # the cast shadow only exists at the base
    light=((mn>222)&(sat<22))|((mn>168)&(sat<16)&smooth&low)
    lab,_=ndimage.label(light); edge=np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])); edge=edge[edge>0]
    bg=np.isin(lab,edge)
    fg=ndimage.binary_opening(~bg,iterations=6); l2,n=ndimage.label(fg)
    if n>1: fg=l2==(1+np.argmax(ndimage.sum(fg,l2,range(1,n+1))))
    bg=~fg
    # the opening in the lid shows the white backdrop: tone it down to dark metal
    ys=np.where(fg.any(axis=1))[0]; top=ys[0]; hole=(mn>225)&fg; hole[top+int((ys[-1]-top)*.10):]=False
    im=im.copy(); px=np.asarray(im).copy(); px[hole]=(px[hole]*0.32).astype('uint8'); im=Image.fromarray(px)
    al=Image.fromarray(((~bg)*255).astype('uint8')).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(2.5))
    # warm the cold studio whites slightly so the glass sits on the cream ground
    warm=ImageChops.multiply(im,Image.new('RGB',im.size,(255,250,240)))
    # clarity: local contrast + crisp edges so the ribs, lid and label read sharply at post size
    from PIL import ImageEnhance
    warm=warm.filter(ImageFilter.UnsharpMask(radius=14,percent=45,threshold=0))
    warm=ImageEnhance.Contrast(warm).enhance(1.14)
    warm=warm.filter(ImageFilter.UnsharpMask(radius=2.2,percent=130,threshold=2))
    o=warm.convert('RGBA'); o.putalpha(al); return o.crop(o.getbbox())
async def main():
  os.makedirs(H+'/cut',exist_ok=True)
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1856,'height':2304})
    for k,(n,_) in N.items():
      if k=='shaikha': im=Image.open(H+'/incense-jar-src.jpg').convert('RGB')
      else:
        await pg.goto('file://'+H+'/incense_label.html?'+urllib.parse.urlencode({'n':n}));await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(300)
        im=Image.open(io.BytesIO(await pg.locator('#r').screenshot(type='png'))).convert('RGB')
      cut(im).save(f'{H}/cut/incense-{k}.png')
    await pg.set_viewport_size({'width':1080,'height':1920})
    for k,(n,hook) in N.items():
      os.makedirs(f'{R}/posts/incense-{k}',exist_ok=True)
      for f,sz in [('feed','1080x1350'),('story','1080x1920')]:
        await pg.goto('file://'+H+'/incense_card.html?'+urllib.parse.urlencode({'k':'incense-'+k,'name':n,'hook':hook,'f':f}));await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(400)
        await pg.locator('#r').screenshot(path=f'{R}/posts/incense-{k}/{f}-{sz}.jpg',type='jpeg',quality=97)
    await b.close()
asyncio.run(main())
