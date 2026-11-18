"""Unified Rose Baghdad frame (feed 1080x1350 + story 1080x1920).
python3 tools/frame/render.py jobs.json   -> jobs: [[key, NAME, hook, "feed"|"story", out.jpg], ...]"""
import sys,os,json,urllib.parse,asyncio
from playwright.async_api import async_playwright
async def main(jobs):
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1920})
    base='file://'+os.path.dirname(os.path.abspath(__file__))+'/frame.html'
    for k,name,hook,f,out in jobs:
      await pg.goto(base+'?'+urllib.parse.urlencode({'k':k,'name':name,'hook':hook,'f':f}))
      await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(300)
      await pg.locator('#r').screenshot(path=out,type='jpeg',quality=92)
    await b.close()
if __name__=='__main__': asyncio.run(main(json.load(open(sys.argv[1]))))
