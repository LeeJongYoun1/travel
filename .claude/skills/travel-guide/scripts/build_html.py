"""7단계: places.json → HTML 페이지(사진 내장, 단독 실행). 게시용(Artifact) 파일과 카톡 공유용 파일, zip 생성.
사용: python build_html.py config.json places.json 출력폴더 [엑셀경로]
결과: 출력폴더/<여행지>_여행노트.html (Artifact 게시용, 문서 뼈대 없음)
      출력폴더/<여행지>_여행노트_공유용.html (doctype·charset 포함, 카톡 전송용)
      출력폴더/<여행지>_여행자료.zip (엑셀경로를 주면 함께 묶음)"""
import sys, os, json, math, base64, urllib.parse, zipfile
from common import load, Money, slug
cfg = load(sys.argv[1]); P = load(sys.argv[2]); OUT = sys.argv[3]; XL = sys.argv[4] if len(sys.argv) > 4 else None
base = os.path.dirname(os.path.abspath(sys.argv[2])); here = os.path.dirname(os.path.abspath(__file__))
M = Money(cfg); T = cfg['travel']; D = cfg['destination']
def lst(items): return [M.conv(x) for x in items if x and x != '–']
def dist(p, h):
    if p.get('lat') is None: return {'km': None, 't': ''}
    a1, o1, a2, o2 = map(math.radians, (h['lat'], h['lon'], p['lat'], p['lon']))
    km = round(6371*2*math.asin(math.sqrt(math.sin((a2-a1)/2)**2 + math.cos(a1)*math.cos(a2)*math.sin((o2-o1)/2)**2))*T['road_factor'], 1)
    if km < 1: return {'km': km, 't': f"도보 약 {max(5, round(km/T['walk_kmh']*60/5)*5)}분"}
    return {'km': km, 't': f"{T['mode']} 약 {max(5, round((T['wait_min']+km/T['speed_kmh']*60)/5)*5)}분"}
S = {}; regions = []
for sname, rows in P['sheets'].items():
    out = []
    for p in rows:
        rv = p.get('reviews', {}); ph = p.get('photo')
        img = base64.b64encode(open(os.path.join(base, ph['file']), 'rb').read()).decode() if ph and os.path.exists(os.path.join(base, ph['file'])) else None
        if p['region'] not in regions: regions.append(p['region'])
        out.append({'region': p['region'], 'name': p['name'], 'desc': p.get('desc', ''), 'price': lst(p.get('price', [])), 'pro': lst(p.get('pros', [])),
            'con': lst(p.get('cons', [])), 'extra': lst(p.get('extra', [])), 'basis': rv.get('basis', ''), 'reviews': int(''.join(c for c in rv.get('basis', '0').split('건')[0] if c.isdigit()) or 0),
            'pos': rv.get('pos', []), 'neg': rv.get('neg', []), 'negnote': rv.get('neg_note', ''), 'dist': [dist(p, h) for h in cfg['hotels']],
            'home': [{'l': h['label'], 'u': h['url']} for h in p.get('home', [])], 'img': img, 'imgsrc': ph['src'] if ph else '',
            'gmap': 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(p.get('map_query') or p['name'] + ' ' + cfg.get('destination_en', '')), 'gnote': p.get('map_note', '')})
    S[sname] = out
order = [r for r in cfg.get('region_order', []) if r in regions] + [r for r in regions if r not in cfg.get('region_order', [])]
data = {'built': cfg.get('built', ''), 'sheets': S, 'hotels': [{'short': h['short'], 'label': h['label']} for h in cfg['hotels']], 'rate': cfg['currency']['krw_per_unit'],
        'unit': cfg['currency']['unit'], 'sample': cfg['currency'].get('sample', '100,000'), 'regions': order,
        'priceLabel': {k: v.get('price_label', '가격') for k, v in cfg['categories'].items()}, 'footer': cfg.get('footer', '')}
t = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
t = t.replace('__TITLE__', f"{D} 여행 노트").replace('__SUBTITLE__', ' · '.join(P['sheets'])).replace('__LEDE__', cfg.get('lede', ''))
t = t.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
os.makedirs(OUT, exist_ok=True); f1 = os.path.join(OUT, f'{D}_여행노트.html'); open(f1, 'w', encoding='utf-8').write(t)
head = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}</style>\n')
i = t.index('<div class="wrap">'); f2 = os.path.join(OUT, f'{D}_여행노트_공유용.html')
open(f2, 'w', encoding='utf-8').write(head + t[:i] + '</head>\n<body>\n' + t[i:] + '\n</body>\n</html>\n')
if XL:
    with zipfile.ZipFile(os.path.join(OUT, f'{D}_여행자료.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(XL, os.path.basename(XL)); z.write(f2, f'{D}_여행노트.html')
print('saved', f1, f2, {k: len(v) for k, v in S.items()})
