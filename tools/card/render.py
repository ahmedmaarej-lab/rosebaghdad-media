import sys,urllib.parse,asyncio
from playwright.async_api import async_playwright
async def main(jobs):
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1920})
    import os;base='file://'+os.path.abspath('tools/card/card.html')
    for k,name,hook,f,out in jobs:
      await pg.goto(base+'?'+urllib.parse.urlencode({'k':k,'name':name,'hook':hook,'f':f}));await pg.wait_for_timeout(400)
      await pg.locator('#r').screenshot(path=out,type='jpeg',quality=92)
    await b.close()
if __name__=='__main__':
  import json;asyncio.run(main(json.load(open(sys.argv[1]))))
