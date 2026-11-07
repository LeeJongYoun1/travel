"""8단계(선택): 공유용 HTML 을 Vercel 사이트 폴더(저장소 루트 public/)에 올리고 첫 화면 목록을 다시 만든다.
사용: python publish_site.py config.json places.json 출력폴더 [사이트폴더=<저장소>/public]
결과: public/<영문이름>/index.html, public/trips.json(목록 데이터), public/index.html(여행지 목록)
그 다음 git commit·push 하면 Vercel 이 자동 배포한다(비밀번호는 루트 middleware.js + Vercel 환경변수 SITE_PASSWORD)."""
import sys, os, re, json, html
from common import load, save
cfg = load(sys.argv[1]); P = load(sys.argv[2]); OUT = sys.argv[3]
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
SITE = sys.argv[4] if len(sys.argv) > 4 else os.path.join(root, 'public')
D = cfg['destination']; key = re.sub(r'[^a-z0-9]+', '', cfg.get('destination_en', '').lower()) or 'trip'
src = os.path.join(OUT, f'{D}_여행노트_공유용.html')
HEAD = ('<link rel="icon" href="/icons/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">'
        '<link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#0B7A75">'
        '<meta name="apple-mobile-web-app-title" content="쏙여행"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">')
# 홈 화면 아이콘(public/icons, manifest.webmanifest)을 쓰도록 <head> 에 링크를 넣는다
os.makedirs(os.path.join(SITE, key), exist_ok=True)
page = open(src, encoding='utf-8').read().replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + HEAD, 1)
open(os.path.join(SITE, key, 'index.html'), 'w', encoding='utf-8').write(page)
tj = os.path.join(SITE, 'trips.json')
trips = load(tj) if os.path.exists(tj) else []
trips = [t for t in trips if t['key'] != key] + [{'key': key, 'name': D, 'en': cfg.get('destination_en', ''), 'built': cfg.get('built', ''),
         'counts': {k: len(v) for k, v in P['sheets'].items()}}]
trips.sort(key=lambda t: t['built'], reverse=True); save(tj, trips)
e = html.escape
cards = '\n'.join(f'<a class="card" href="/{e(t["key"])}/" data-name="{e(t["name"])}" data-en="{e(t["en"])}"><span class="name">{e(t["name"])}</span><span class="en">{e(t["en"])}</span>'
                  f'<span class="meta">{" · ".join(f"{e(k)} {n}" for k, n in t["counts"].items())}</span><span class="date">{e(t["built"])} 정리</span></a>' for t in trips)
# 첫 화면 틀(여행지 추가 폼·대기 카드 포함)은 index_template.html
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index_template.html'), encoding='utf-8').read()
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(tpl.replace('__HEAD__', HEAD + '\n').replace('__CARDS__', cards))
print('published', key, '→', SITE, [t['key'] for t in trips])
