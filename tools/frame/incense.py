"""Rose Baghdad incense: same jar, the name on the label changes. Renders feed + story in the unified frame.
python3 tools/frame/incense.py"""
import asyncio,os,urllib.parse,io
from playwright.async_api import async_playwright
from PIL import Image,ImageFilter,ImageDraw
import numpy as np
N={'azizati':('عزيزتي','ريحة تستقبل ضيوفك قبلك'),'sayidati':('سيدتي','لمسة فخامة تكمل جلستك'),'fakher':('فاخر','بخور يليق بمجلسك'),'shurooq':('شروق','بيتك يستاهل ريحة تبقى بالبال')}
H=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(os.path.dirname(H))
def clean(im):
    w,h=im.size; im=im.crop((int(w*.08),int(h*.12),int(w*.92),int(h*.90)))
    a=np.clip(np.asarray(im).astype(float)*255/228,0,255); im=Image.fromarray(a.astype('uint8'))
    W,Hh=im.size; m=Image.new('L',(W,Hh),0); p=int(W*.07); ImageDraw.Draw(m).rectangle((p,p,W-p,Hh-p),fill=255); m=m.filter(ImageFilter.GaussianBlur(p*.5))
    o=Image.new('RGB',(W,Hh),'white'); o.paste(im,(0,0),m); return o
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1856,'height':2304})
    for k,(n,_) in N.items():
      await pg.goto('file://'+H+'/incense_label.html?'+urllib.parse.urlencode({'n':n}));await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(300)
      im=Image.open(io.BytesIO(await pg.locator('#r').screenshot(type='png'))).convert('RGB')
      clean(im).save(f'{R}/tools/reel/bottles/incense-{k}.jpg',quality=93)
    await pg.set_viewport_size({'width':1080,'height':1920})
    for k,(n,hook) in N.items():
      os.makedirs(f'{R}/posts/incense-{k}',exist_ok=True)
      for f,hh,sz in [('feed','440','1080x1350'),('story','600','1080x1920')]:
        q={'k':'incense-'+k,'name':n,'hook':hook,'ml':'بخور إماراتي','ft':'علبة ٦٠ مل<b>◆</b>١٠ أقراص','pill':'١٥ ألف دينار<b>◆</b>توصيل مجاني','ls':'0','f':f,'h':hh}
        await pg.goto('file://'+H+'/frame.html?'+urllib.parse.urlencode(q));await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(300)
        await pg.locator('#r').screenshot(path=f'{R}/posts/incense-{k}/{f}-{sz}.jpg',type='jpeg',quality=92)
    await b.close()
asyncio.run(main())
