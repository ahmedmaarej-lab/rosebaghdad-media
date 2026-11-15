import asyncio,os,sys
from playwright.async_api import async_playwright
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1920})
    await pg.goto('file://'+os.path.abspath('lux.html'));await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(500)
    for t in [2.8,5.7,7.2,11.0]:
      await pg.evaluate(f'setT({t})');await pg.screenshot(path=f'/tmp/claude-0/-home-claude/18302f8e-dc17-5097-b2f2-0d9a35889652/scratchpad/u{t}.png')
    await b.close()
asyncio.run(m())
