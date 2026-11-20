"""Turn a saved Metricool getScheduledPosts result into tools/roza/schedule.json for the publishing board.
python3 tools/roza/refresh_schedule.py <metricool-result.txt>   (prints failed/late posts, if any)"""
import json,sys,os,datetime
H=os.path.dirname(os.path.abspath(__file__))
s=open(sys.argv[1],encoding='utf-8').read(); posts=json.loads(s[s.find('{'):])['data']
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
NET={'instagram':'إنستغرام','facebook':'فيسبوك','tiktok':'تيك توك','threads':'ثريدز'}
TYPE={'REEL':'ريل','STORY':'ستوري','POST':'بوست'}
rows=[];bad=[]
for p in posts:
    dt=p['publicationDate']['dateTime']; types=set()
    for n in p['providers']:
        t=(p.get(n['network']+'Data') or {}).get('type')
        types.add(TYPE.get(t,'فيديو' if n['network']=='tiktok' else 'بوست'))
    text=p.get('text') or ''
    r={'date':dt[:10],'time':dt[11:16],'kind':' + '.join(sorted(types)),'title':text.split('\n')[0].strip() or '(ستوري بدون نص)',
       'nets':[NET.get(n['network'],n['network']) for n in p['providers']],
       'done':all(n['status']=='PUBLISHED' for n in p['providers']),
       'roza':bool((p.get('instagramData') or {}).get('isAiGenerated')) or 'روزة' in text,
       'url':next((n.get('publicUrl') for n in sorted(p['providers'],key=lambda n:n['network']!='instagram') if n.get('publicUrl')),None)}
    late=datetime.datetime.fromisoformat(dt+'+03:00')<now-datetime.timedelta(minutes=20)
    for n in p['providers']:
        if n['status'] not in ('PUBLISHED','PENDING') or (late and n['status']!='PUBLISHED'):
            bad.append(f"{dt} {r['title'][:40]} {n['network']}: {n.get('detailedStatus') or n['status']}")
    rows.append(r)
rows.sort(key=lambda r:(r['date'],r['time']))
json.dump({'checked':now.strftime('%Y-%m-%d %H:%M'),'rows':rows},open(H+'/schedule.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
print(len(rows),'rows'); [print('PROBLEM',b) for b in bad]
today=now.strftime('%Y-%m-%d')
for r in rows:
    if r['roza'] and r['date']==today and 'ستوري' in r['kind']: print('ROZA_STORY_TODAY',r['time'],r['done'],r['url'])
