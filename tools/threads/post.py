"""Publish due Threads text posts from queue/threads/*.json (fields: at ISO time, text).
Runs in GitHub Actions with secret THREADS_TOKEN (a long-lived Threads user token, 60 days).
The token is refreshed automatically every ~7 days and the fresh one is kept in .state
(persisted with actions/cache), so it never expires as long as the workflow runs.
Never prints the token: this repository and its logs are public."""
import json,os,glob,re,urllib.request,urllib.parse,datetime,time
G='https://graph.threads.net/v1.0'
os.makedirs('.state',exist_ok=True)
TP='.state/threads_token.json'; SP='.state/threads_sent.json'
now=datetime.datetime.now(datetime.timezone.utc)
sec=re.sub(r'\s+','',os.environ.get('THREADS_TOKEN',''))
st=json.load(open(TP)) if os.path.exists(TP) else {}
# a newly pasted secret wins over the cached refreshed token
if sec and st.get('seed')!=sec[-12:]: st={'tok':sec,'seed':sec[-12:],'at':'2000-01-01T00:00:00+00:00'}
tok=st.get('tok')
if not tok: raise SystemExit('THREADS_TOKEN secret is missing')
def call(url,params,post=True):
    data=urllib.parse.urlencode(params).encode()
    r=urllib.request.Request(url if post else url+'?'+data.decode(),data=data if post else None)
    try:
        with urllib.request.urlopen(r,timeout=40) as f: return json.load(f)
    except urllib.error.HTTPError as e:
        try: return json.load(e)
        except Exception: return {'error':{'message':'HTTP %s'%e.code}}
if (now-datetime.datetime.fromisoformat(st['at'])).days>=7:
    r=call('https://graph.threads.net/refresh_access_token',{'grant_type':'th_refresh_token','access_token':tok},post=False)
    if r.get('access_token'):
        st.update(tok=r['access_token'],at=now.isoformat()); tok=st['tok']; print('TOKEN refreshed')
    else: print('TOKEN refresh failed:',(r.get('error') or {}).get('message'))
json.dump(st,open(TP,'w'))
sent=json.load(open(SP)) if os.path.exists(SP) else {}
sent={k:v for k,v in sent.items() if v.get('ok') or v.get('skipped') or v.get('cancelled')}
def save(): json.dump(sent,open(SP,'w'),ensure_ascii=False)
fail=[]
for p in sorted(glob.glob('queue/threads/*.json')):
    name=os.path.basename(p)
    if name in sent: continue
    j=json.load(open(p,encoding='utf-8'))
    if j.get('cancel'): sent[name]={'cancelled':True}; save(); continue
    at=datetime.datetime.fromisoformat(j['at']); wait=(at-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    if wait>600: continue
    if wait>0: time.sleep(wait)
    if (datetime.datetime.now(datetime.timezone.utc)-at).total_seconds()>3*3600: sent[name]={'skipped':'too old'}; save(); continue
    c=call(G+'/me/threads',{'media_type':'TEXT','text':j['text'][:500],'access_token':tok})
    res={'ok':False,'error':(c.get('error') or {}).get('message')}
    if c.get('id'):
        time.sleep(5)
        pub=call(G+'/me/threads_publish',{'creation_id':c['id'],'access_token':tok})
        res={'ok':bool(pub.get('id')),'id':pub.get('id'),'error':(pub.get('error') or {}).get('message')}
    res['at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    print('RESULT',name,json.dumps(res,ensure_ascii=False))
    if res['ok']: sent[name]=res
    else: fail.append(name)
    save()
if fail: raise SystemExit('threads post failed: '+', '.join(fail))
