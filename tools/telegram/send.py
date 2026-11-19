"""Send due Telegram posts from queue/telegram/*.json (fields: at ISO time, text HTML, plain, chat).
Runs in GitHub Actions with secret TELEGRAM_BOT_TOKEN. Needs no repo write access:
which files were already sent is kept in .state/sent.json (persisted with actions/cache).

GitHub's own cron fires only a couple of times a day on this repo, so the workflow chains itself:
each run sends what is due, then sleeps until the next queued post (at most MAX_SLEEP seconds),
sends it, and the workflow step after this script dispatches the next run.
Writes CHAIN=1 to $GITHUB_OUTPUT while posts are still waiting, CHAIN=0 when the queue is empty
or a file named queue/telegram/STOP exists (the off switch)."""
import json,os,glob,urllib.request,urllib.parse,datetime,time,re
MAX_SLEEP=int(os.environ.get('MAX_SLEEP','17400'))   # 4h50m, under the 6h job limit
tok=re.sub(r'\s+','',os.environ.get('TELEGRAM_BOT_TOKEN',''))   # tolerate spaces/newlines pasted with the secret
if tok.lower().startswith('bot'): tok=tok[3:]
m=re.search(r'\d{6,}:[A-Za-z0-9_-]{30,}',tok)
if m: tok=m.group(0)
if not tok: raise SystemExit('TELEGRAM_BOT_TOKEN secret is missing')
os.makedirs('.state',exist_ok=True)
SP='.state/sent.json'
sent=json.load(open(SP)) if os.path.exists(SP) else {}
sent={k:v for k,v in sent.items() if v.get('ok') or v.get('cancelled') or v.get('skipped')}   # failed sends get retried
runfail=[]
now=lambda: datetime.datetime.now(datetime.timezone.utc)
def api(method,params):
    r=urllib.request.Request(f'https://api.telegram.org/bot{tok}/{method}',data=urllib.parse.urlencode(params).encode())
    with urllib.request.urlopen(r,timeout=30) as f:return json.load(f)
def save(): json.dump(sent,open(SP,'w'),ensure_ascii=False)
def pending():
    """Unsent queue files as (at, name, data), oldest first."""
    out=[]
    for p in sorted(glob.glob('queue/telegram/*.json')):
        name=os.path.basename(p)
        if name in sent: continue
        j=json.load(open(p,encoding='utf-8'))
        if j.get('cancel'): sent[name]={'ok':False,'cancelled':True}; save(); continue
        out.append((datetime.datetime.fromisoformat(j['at']),name,j))
    return sorted(out,key=lambda x:x[0])
def send(name,j):
    chat=j.get('chat','@rosebaghdad_iq')
    try: res=api('sendMessage',{'chat_id':chat,'text':j['text'],'parse_mode':'HTML','disable_web_page_preview':'true'})
    except Exception:
        try: res=api('sendMessage',{'chat_id':chat,'text':j.get('plain') or j['text'],'disable_web_page_preview':'true'})
        except Exception as e: res={'ok':False,'description':str(e)}
    sent[name]={'ok':res.get('ok'),'message_id':(res.get('result') or {}).get('message_id'),'error':res.get('description'),'at':now().isoformat()}
    print('RESULT',name,json.dumps(sent[name]),flush=True)
    if not sent[name]['ok']: runfail.append(name); del sent[name]
    save()
def due_pass():
    for at,name,j in pending():
        late=(now()-at).total_seconds()
        if late<0: continue                      # future post
        if late>3*3600: sent[name]={'ok':False,'skipped':'too old'}; save(); print('SKIP too old',name,flush=True); continue
        send(name,j)
due_pass()
future=[x for x in pending() if x[0]>now()]
stop=os.path.exists('queue/telegram/STOP')
if future and not stop:
    wait=(future[0][0]-now()).total_seconds()
    print(f'next post {future[0][1]} in {int(wait)}s; sleeping {int(min(wait,MAX_SLEEP))}s',flush=True)
    time.sleep(max(0,min(wait,MAX_SLEEP)))
    due_pass()
save()
chain=bool([x for x in pending() if x[0]>now()]) and not stop and not runfail
if os.environ.get('GITHUB_OUTPUT'): open(os.environ['GITHUB_OUTPUT'],'a').write(f"chain={'1' if chain else '0'}\n")
print('CHAIN',chain,flush=True)
if runfail: raise SystemExit('send failed: '+', '.join(runfail))   # makes the run red so the failure is visible
