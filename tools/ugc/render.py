"""Render one of the UGC / cinematic video templates to MP4 (1080x1920, 30 fps).

    python3 tools/ugc/render.py <template> <out.mp4> [--music file.wav]

Templates (HTML in this folder, length in seconds):
    ugc   ugc.html   15 s  how-to-spray, UGC style
    lux   lux.html   12 s  cinematic product reel
    roza  roza.html  27 s  Roza notes reel
--music muxes an audio track in (AAC, cut to the video length).
Needs: playwright (chromium) + ffmpeg."""
import asyncio,subprocess,os,sys,argparse
T={'ugc':('ugc.html',15.0),'lux':('lux.html',12.0),'roza':('roza.html',27.0)}
FPS=30
here=os.path.dirname(os.path.abspath(__file__))
ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('template',choices=T);ap.add_argument('out');ap.add_argument('--music')
a=ap.parse_args()
html,dur=T[a.template];N=int(FPS*dur)
async def main():
    from playwright.async_api import async_playwright
    tmp=a.out[:-4]+'.tmp.mp4'
    ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p','-movflags','+faststart',tmp],stdin=subprocess.PIPE)
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1920})
        await pg.goto('file://'+here+'/'+html)
        await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(500)
        for i in range(N):
            await pg.evaluate(f'setT({i/FPS})');ff.stdin.write(await pg.screenshot(type='jpeg',quality=92))
        await b.close()
    ff.stdin.close()
    if ff.wait()!=0: print('ffmpeg failed');sys.exit(1)
    if a.music:
        tmp2=a.out[:-4]+'.mux.mp4'
        r=subprocess.run(['ffmpeg','-y','-loglevel','error','-i',tmp,'-i',a.music,'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',tmp2])
        os.remove(tmp)
        if r.returncode!=0: print('ffmpeg mux failed');sys.exit(1)
        tmp=tmp2
    os.replace(tmp,a.out);print('ok',a.out)
asyncio.run(main())
