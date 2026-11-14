"""Send due Telegram posts from queue/telegram/*.json (fields: at ISO time, text HTML, plain, chat).
Runs in GitHub Actions with secret TELEGRAM_BOT_TOKEN. Needs no repo write access:
which files were already sent is kept in .state/sent.json (persisted with actions/cache),
and each result is printed to the run log and logged by Claude's scheduled task."""
import json,os,glob,urllib.request,urllib.parse,datetime,time
import re
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
def api(method,params):
    r=urllib.request.Request(f'https://api.telegram.org/bot{tok}/{method}',data=urllib.parse.urlencode(params).encode())
    with urllib.request.urlopen(r,timeout=30) as f:return json.load(f)
def save(): json.dump(sent,open(SP,'w'),ensure_ascii=False)
for p in sorted(glob.glob('queue/telegram/*.json')):
    name=os.path.basename(p)
    if name in sent: continue
    j=json.load(open(p,encoding='utf-8'))
    if j.get('cancel'): sent[name]={'ok':False,'cancelled':True}; save(); continue
    wait=(datetime.datetime.fromisoformat(j['at'])-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    if wait>600: continue                       # not due yet
    if wait>0: time.sleep(wait)                 # due within 10 min: wait for the exact time
    if (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(j['at'])).total_seconds()>3*3600:
        sent[name]={'ok':False,'skipped':'too old'}; save(); continue   # never post something hours late
    chat=j.get('chat','@rosebaghdad_iq')
    try: res=api('sendMessage',{'chat_id':chat,'text':j['text'],'parse_mode':'HTML','disable_web_page_preview':'true'})
    except Exception:
        try: res=api('sendMessage',{'chat_id':chat,'text':j.get('plain') or j['text'],'disable_web_page_preview':'true'})
        except Exception as e: res={'ok':False,'description':str(e)}
    sent[name]={'ok':res.get('ok'),'message_id':(res.get('result') or {}).get('message_id'),'error':res.get('description'),'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    print('RESULT',name,json.dumps(sent[name]))
    if not sent[name]['ok']: runfail.append(name); del sent[name]
    save()
save()
if runfail: raise SystemExit('send failed: '+', '.join(runfail))   # makes the run red so the failure is visible
