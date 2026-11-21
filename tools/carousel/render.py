"""Render Rose Baghdad carousels: python3 tools/carousel/render.py tools/carousel/carousels.json
Each carousel -> posts/carousel-<key>/NN.jpg (1080x1350)."""
import asyncio,os,sys,json,urllib.parse
from playwright.async_api import async_playwright
H=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(os.path.dirname(H)); AR='٠١٢٣٤٥٦٧٨٩'
ar=lambda n:''.join(AR[int(c)] for c in str(n))
async def main(C):
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1350})
    for key,c in C.items():
      out=f'{R}/posts/carousel-{key}';os.makedirs(out,exist_ok=True)
      n=len(c['tips'])+2
      slides=[dict(t='cover',kick=c['kick'],title=c['title'],img=c.get('img',''),ih=c.get('ih',360))]
      slides+=[dict(t='tip',n=ar(i+1),h=h,b=bb,pg=f'{i+2} / {n}') for i,(h,bb) in enumerate(c['tips'])]
      slides+=[dict(t='end',h=c['end'][0],b=c['end'][1],pill=c['end'][2])]
      for i,s in enumerate(slides):
        await pg.goto('about:blank');await pg.goto('file://'+H+'/slide.html#'+urllib.parse.quote(json.dumps(s,ensure_ascii=False)))
        await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(350)
        await pg.locator('#r').screenshot(path=f'{out}/{i+1:02d}.jpg',type='jpeg',quality=95)
    await b.close()
asyncio.run(main(json.load(open(sys.argv[1]))))
