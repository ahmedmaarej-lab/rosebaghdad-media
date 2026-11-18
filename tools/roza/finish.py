"""Finish Roza clips from Gemini into one ready-to-post 1080x1920 video: join the clips, add the
Rose Baghdad logo, on-screen key-point captions and an end card.
    python3 tools/roza/finish.py spec.json out.mp4
spec: {"clips": [{"path": "a.mp4", "end": 14.9}, ...],            # end = cut the clip here (seconds), optional
       "cards": [[from, to, "text with <b>gold</b> words"], ...,  # times on the joined video
                 [from, to, "end:اطلبوه هسه|www.rosebaghdad.iq"]]}
Needs playwright (chromium) + ffmpeg."""
import json,sys,os,subprocess,asyncio,urllib.parse,tempfile
H=os.path.dirname(os.path.abspath(__file__))
spec=json.load(open(sys.argv[1],encoding='utf-8')); out=sys.argv[2]
tmp=tempfile.mkdtemp()
async def pngs():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1080,'height':1920})
        async def shot(kind,text,path):
            await pg.goto('file://'+H+'/overlay.html?'+urllib.parse.urlencode({'kind':kind,'text':text}))
            await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(150)
            await pg.locator('#r').screenshot(path=path,omit_background=True)
        await shot('logo','',f'{tmp}/logo.png')
        for i,(a,z,t) in enumerate(spec['cards']):
            await shot('end' if t.startswith('end:') else 'cap',t[4:] if t.startswith('end:') else t,f'{tmp}/c{i}.png')
        await b.close()
asyncio.run(pngs())
clips=spec['clips']; args=['ffmpeg','-y','-loglevel','error']; f=[]
for c in clips: args+=['-i',c['path']]
for i,c in enumerate(clips):
    tr=f"trim=0:{c['end']}," if c.get('end') else ''; atr=f"atrim=0:{c['end']}," if c.get('end') else ''
    f.append(f"[{i}:v:0]{tr}setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,fps=30,setsar=1[v{i}];[{i}:a:0]{atr}asetpts=PTS-STARTPTS,aresample=48000[a{i}]")
n=len(clips); f.append(''.join(f'[v{i}][a{i}]' for i in range(n))+f'concat=n={n}:v=1:a=1[base][aud]')
total=sum(c.get('end') or float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',c['path']])) for c in clips)
args+=['-loop','1','-t',str(total),'-i',f'{tmp}/logo.png']; li=n
f.append(f'[{li}:v]format=rgba,fade=in:st=0.2:d=0.4:alpha=1[lg];[base][lg]overlay=0:0[x0]'); last='x0'
for i,(a,z,t) in enumerate(spec['cards']):
    j=n+1+i; args+=['-loop','1','-t',str(total),'-i',f'{tmp}/c{i}.png']
    f.append(f"[{j}:v]format=rgba,fade=in:st={a}:d=0.25:alpha=1,fade=out:st={max(a,z-0.25)}:d=0.25:alpha=1[o{i}];[{last}][o{i}]overlay=0:0:enable='between(t,{a},{z})'[y{i}]"); last=f'y{i}'
args+=['-filter_complex',';'.join(f),'-map',f'[{last}]','-map','[aud]','-t',str(total),'-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',out]
subprocess.run(args,check=True); print('ok',out,round(total,2),'s')
