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
cards = '\n'.join(f'<a class="card" href="/{e(t["key"])}/"><span class="name">{e(t["name"])}</span><span class="en">{e(t["en"])}</span>'
                  f'<span class="meta">{" · ".join(f"{e(k)} {n}" for k, n in t["counts"].items())}</span><span class="date">{e(t["built"])} 정리</span></a>' for t in trips)
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>쏙여행</title>
{HEAD}<style>
:root{{--bg:#F2F6F5;--surface:#fff;--ink:#132E2C;--muted:#5B706D;--line:#D5E2DF;--accent:#0B7A75}}
@media (prefers-color-scheme: dark){{:root{{--bg:#0E1A19;--surface:#152523;--ink:#E4EFED;--muted:#93AAA6;--line:#26403C;--accent:#4FC3BA}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}
main{{max-width:720px;margin:0 auto;padding:32px 16px 64px;display:grid;gap:16px}}h1{{margin:0;font-size:28px}}p{{margin:0;color:var(--muted)}}
.list{{display:grid;gap:12px}}.card{{display:grid;gap:2px;padding:18px;border:1px solid var(--line);border-radius:14px;background:var(--surface);color:inherit;text-decoration:none}}
.card:hover{{border-color:var(--accent)}}.name{{font-size:20px;font-weight:700}}.en{{color:var(--muted);font-size:14px}}
.meta{{color:var(--accent);font-size:14px;margin-top:6px}}.date{{color:var(--muted);font-size:13px}}
</style></head><body><main><h1>쏙여행</h1><p>2025년 이후 후기에서 광고·AI 글을 걸러 정리한 여행지별 마사지·맛집·가볼만한 곳. 개인 여행 준비용(사진 저작권은 각 블로거에게 있음).</p>
<div class="list">
{cards}
</div></main></body></html>
''')
print('published', key, '→', SITE, [t['key'] for t in trips])
