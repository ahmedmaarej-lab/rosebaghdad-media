"""Save preview stills of a video template at chosen seconds, to check a design without rendering the video.

    python3 tools/ugc/shots.py <template.html> <out-dir> <t1> [t2 ...]
e.g. python3 tools/ugc/shots.py tools/ugc/lux.html /tmp/prev 2.8 5.7 11
Works for any template that exposes setT(t) (tools/ugc/*.html, tools/reel/reel.html)."""
import asyncio,os,sys
from playwright.async_api import async_playwright
if len(sys.argv)<4: sys.exit(__doc__)
html,outdir,ts=os.path.abspath(sys.argv[1]),sys.argv[2],[float(t) for t in sys.argv[3:]]
os.makedirs(outdir,exist_ok=True)
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1920})
    await pg.goto('file://'+html);await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(500)
    stem=os.path.splitext(os.path.basename(html))[0]
    for t in ts:
      out=os.path.join(outdir,f'{stem}-{t:g}s.png');await pg.evaluate(f'setT({t})');await pg.screenshot(path=out);print(out)
    await b.close()
asyncio.run(m())
