"""Build the Roza video kits page (tools/roza/page/index.html) from scripts.json.  python3 tools/roza/build_page.py"""
import json,os
H=os.path.dirname(os.path.abspath(__file__))
d=json.load(open(H+'/scripts.json',encoding='utf-8'))
tpl=open(H+'/page.tpl.html',encoding='utf-8').read()
os.makedirs(H+'/page',exist_ok=True)
open(H+'/page/index.html','w',encoding='utf-8').write(tpl.replace('/*DATA*/[]',json.dumps(d,ensure_ascii=False)))
print('ok')
