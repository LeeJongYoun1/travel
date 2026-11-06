"""1단계 수집: 네이버 블로그·카페(NAVER API HUB), 유튜브(Data API v3).
사용: python collect.py config.json
필요 환경변수: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET (NCP API HUB 키), YOUTUBE_API_KEY
결과: work/naver_blog.json, work/naver_cafe.json, work/youtube.json"""
import os, sys, json, re, urllib.request, urllib.parse, concurrent.futures as cf
from common import load, save, work
cfg = load(sys.argv[1]); D = cfg['destination']; SINCE = cfg.get('since', '20250101')
H = {'X-NCP-APIGW-API-KEY-ID': os.environ['NAVER_CLIENT_ID'], 'X-NCP-APIGW-API-KEY': os.environ['NAVER_CLIENT_SECRET']}
strip = lambda s: re.sub(r'<[^>]+>', '', s).replace('&quot;', '"').replace('&amp;', '&')
def naver(kind, q, start, sort):
    u = f'https://naverapihub.apigw.ntruss.com/search/v1/{kind}?' + urllib.parse.urlencode({'query': q, 'display': 100, 'start': start, 'sort': sort, 'format': 'json'})
    try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30)).get('items', [])
    except Exception as e: print('ERR', kind, q, e, file=sys.stderr); return []
for kind, fn in [('blog', 'naver_blog.json'), ('cafearticle', 'naver_cafe.json')]:
    out = {}
    for cat, c in cfg['categories'].items():
        qs = [q.format(d=D) for q in c['queries']]
        jobs = [(q, st, so) for q in qs for so in ('sim', 'date') for st in (1, 101, 201)]
        items = {}
        with cf.ThreadPoolExecutor(6) as ex:
            for (q, st, so), res in zip(jobs, ex.map(lambda j: naver(kind, *j), jobs)):
                for it in res:
                    it = {k: strip(v) if isinstance(v, str) else v for k, v in it.items()}
                    if kind == 'blog' and it.get('postdate', '') < SINCE: continue   # 카페는 작성일이 없음
                    items.setdefault(it['link'], it | {'q': q})
        out[cat] = list(items.values()); print(kind, cat, len(out[cat]))
    save(work(cfg, fn), out)
K = os.environ.get('YOUTUBE_API_KEY')
if K:
    def yt(path, **p):
        p['key'] = K; return json.load(urllib.request.urlopen('https://www.googleapis.com/youtube/v3/' + path + '?' + urllib.parse.urlencode(p), timeout=30))
    since = f"{SINCE[:4]}-{SINCE[4:6]}-{SINCE[6:]}T00:00:00Z"; out = {}
    for cat, c in cfg['categories'].items():
        ids = []
        for order in ('relevance', 'viewCount'):
            r = yt('search', part='snippet', q=c['queries'][0].format(d=D), type='video', maxResults=25, publishedAfter=since, regionCode='KR', relevanceLanguage='ko', order=order)
            ids += [i['id']['videoId'] for i in r['items'] if i['id']['videoId'] not in ids]
        v = yt('videos', part='snippet,statistics', id=','.join(ids[:50]))
        out[cat] = [{'id': x['id'], 'title': x['snippet']['title'], 'ch': x['snippet']['channelTitle'], 'date': x['snippet']['publishedAt'][:10],
                     'views': int(x['statistics'].get('viewCount', 0)), 'desc': x['snippet']['description']} for x in v['items']]
        print('youtube', cat, len(out[cat]))
    save(work(cfg, 'youtube.json'), out)
