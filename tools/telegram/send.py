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
        wait=(at-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        if wait>600:continue          # not due yet; a later run will send it
        if wait>0:import time;time.sleep(wait)   # due within 10 min: wait for the exact time
        try:res=send(j.get('chat','@rosebaghdad_iq'),j['text'])
        except Exception as e:
            try:res=send(j.get('chat','@rosebaghdad_iq'),j.get('plain') or j['text'],html=False)
            except Exception as e2:res={'ok':False,'error':str(e2)}
    j['result']={'ok':res.get('ok'),'message_id':(res.get('result') or {}).get('message_id'),'error':res.get('error') or res.get('description'),'sent_at':now.isoformat()}
    out='queue/sent/'+os.path.basename(p)
    json.dump(j,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1);os.remove(p)
    print(os.path.basename(p),j['result'])

# --- Order inbox (approved by Ahmed 2026-11-14): Ahmed and his sales staff send one line per order to the bot
# (e.g. "good girl بصرة"); saved for Claude to log in the dashboard. Replies only acknowledge receipt.
def api(method,params):
    r=urllib.request.Request(f'https://api.telegram.org/bot{tok}/{method}',data=urllib.parse.urlencode(params).encode())
    with urllib.request.urlopen(r,timeout=30) as f:return json.load(f)
try:
    st_path='queue/inbox/state.json'
    st=json.load(open(st_path)) if os.path.exists(st_path) else {'offset':0}
    allow=set(json.load(open('tools/telegram/allow.json')).get('allowed',[]))
    ups=api('getUpdates',{'offset':st['offset'],'timeout':0,'allowed_updates':json.dumps(['message'])}).get('result',[])
    for u in ups:
        st['offset']=u['update_id']+1
        m=u.get('message') or {}
        if (m.get('chat') or {}).get('type')!='private' or not m.get('text'):continue
        uid=m['from']['id'];txt=m['text'].strip()
        if txt.startswith('/start'):
            api('sendMessage',{'chat_id':uid,'text':'هلا بيك 🌹 هذا بوت تسجيل طلبات روز بغداد. دز كل طلب بسطر واحد، مثلاً: good girl بصرة\nرقمك للموافقة: '+str(uid)});continue
        rec={'uid':uid,'name':(m['from'].get('first_name') or ''),'text':txt[:300],'date':m['date'],'approved':uid in allow}
        json.dump(rec,open(f"queue/inbox/{m['date']}-{m['message_id']}.json",'w',encoding='utf-8'),ensure_ascii=False)
        api('sendMessage',{'chat_id':uid,'text':('انسجل ✓' if uid in allow else 'وصل ✓ (ينتظر موافقة الأدمن، رقمك '+str(uid)+')'),'reply_to_message_id':m['message_id']})
    json.dump(st,open(st_path,'w'))
except Exception as e:
    print('inbox error',e)
