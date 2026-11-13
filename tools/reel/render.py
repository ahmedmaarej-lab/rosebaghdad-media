"""Render a Rose Baghdad product reel: python3 render.py <img-key> "<NAME>" "<hook>" <out.mp4>
Needs: playwright (chromium) + ffmpeg."""
import asyncio,subprocess,os,sys,urllib.parse
FPS=30;DUR=9.0;N=int(FPS*DUR)
img,name,hook,out=sys.argv[1:5]
here=os.path.dirname(os.path.abspath(__file__))
async def main():
    from playwright.async_api import async_playwright
    tmp=out[:-4]+'.tmp.mp4'
    ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p','-movflags','+faststart',tmp],stdin=subprocess.PIPE)
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1920})
        await pg.goto('file://'+here+'/reel.html?'+urllib.parse.urlencode({'img':img,'name':name,'hook':hook}))
        await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(500)
        for i in range(N):
            await pg.evaluate(f'setT({i/FPS})');ff.stdin.write(await pg.screenshot(type='jpeg',quality=92))
        await b.close()
    ff.stdin.close()
    if ff.wait()==0: os.replace(tmp,out);print('ok',out)
    else: print('ffmpeg failed');sys.exit(1)
asyncio.run(main())
