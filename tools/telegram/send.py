"""Send due Telegram posts from queue/telegram/*.json (fields: at ISO time, text HTML, chat).
Runs in GitHub Actions with secret TELEGRAM_BOT_TOKEN. Moves sent files to queue/sent with result."""
import json,os,glob,urllib.request,urllib.parse,datetime,shutil
tok=os.environ['TELEGRAM_BOT_TOKEN'];now=datetime.datetime.now(datetime.timezone.utc)
def send(chat,text,html=True):
    d={'chat_id':chat,'text':text,'disable_web_page_preview':'true'}
    if html:d['parse_mode']='HTML'
    r=urllib.request.Request(f'https://api.telegram.org/bot{tok}/sendMessage',data=urllib.parse.urlencode(d).encode())
    with urllib.request.urlopen(r,timeout=30) as f:return json.load(f)
for p in sorted(glob.glob('queue/telegram/*.json')):
    j=json.load(open(p,encoding='utf-8'))
    if j.get('cancel'):res={'ok':False,'cancelled':True}
    else:
        at=datetime.datetime.fromisoformat(j['at'])
        if at>now:continue
        try:res=send(j.get('chat','@rosebaghdad_iq'),j['text'])
        except Exception as e:
            try:res=send(j.get('chat','@rosebaghdad_iq'),j.get('plain') or j['text'],html=False)
            except Exception as e2:res={'ok':False,'error':str(e2)}
    j['result']={'ok':res.get('ok'),'message_id':(res.get('result') or {}).get('message_id'),'error':res.get('error') or res.get('description'),'sent_at':now.isoformat()}
    out='queue/sent/'+os.path.basename(p)
    json.dump(j,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1);os.remove(p)
    print(os.path.basename(p),j['result'])
