"""Rose Baghdad poster v2 (bigger, sharper bottle on a tinted arch).
python3 tools/frame/v2.py jobs.json  -> jobs: [{"k":..,"name":..,"hook":..,"th":"rose|lav|sand|sage","f":"feed|story|reel","out":..,"sub":..,"pill":..,"music":..}]"""
import sys,os,json,urllib.parse,asyncio,subprocess
from playwright.async_api import async_playwright
H=os.path.dirname(os.path.abspath(__file__));FPS=30;DUR=9
async def main(jobs):
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1920})
    for j in jobs:
      f=j['f'];qs={k:v for k,v in j.items() if k in('k','name','hook','th','sub','pill','sc')};qs['f']='feed' if f=='feed' else 'story'
      await pg.goto('file://'+H+'/v2.html?'+urllib.parse.urlencode(qs));await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(300)
      if f!='reel': await pg.locator('#r').screenshot(path=j['out'],type='jpeg',quality=93);print('ok',j['out']);continue
      cmd=['ffmpeg','-y','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-']
      if j.get('music'): cmd+=['-i',j['music'],'-af',f'afade=t=in:d=0.5,afade=t=out:st={DUR-1.2}:d=1.2','-c:a','aac','-b:a','160k','-shortest']
      cmd+=['-c:v','libx264','-crf','19','-preset','veryfast','-pix_fmt','yuv420p','-t',str(DUR),'-movflags','+faststart',j['out']]
      ff=subprocess.Popen(cmd,stdin=subprocess.PIPE)
      for i in range(FPS*DUR):
        await pg.evaluate(f'setT({i/FPS})');ff.stdin.write(await pg.screenshot(type='jpeg',quality=92))
      ff.stdin.close();print('ok' if ff.wait()==0 else 'FAILED',j['out'])
    await b.close()
if __name__=='__main__': asyncio.run(main(json.load(open(sys.argv[1]))))
