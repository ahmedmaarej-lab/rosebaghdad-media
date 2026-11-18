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
    a=np.asarray(im).astype(int); light=(a.min(axis=2)>222)&((a.max(axis=2)-a.min(axis=2))<22)
    from scipy import ndimage
    lab,_=ndimage.label(light); edge=np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])); edge=edge[edge>0]
    bg=np.isin(lab,edge)
    al=Image.fromarray(((~bg)*255).astype('uint8')).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(2.2))
    # warm the cold studio whites slightly so the glass sits on the cream ground
    warm=ImageChops.multiply(im,Image.new('RGB',im.size,(255,250,240)))
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
        await pg.locator('#r').screenshot(path=f'{R}/posts/incense-{k}/{f}-{sz}.jpg',type='jpeg',quality=93)
    await b.close()
asyncio.run(main())
