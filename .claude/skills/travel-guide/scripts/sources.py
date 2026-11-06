"""2단계: 블로그 본문 수집 + 광고/AI 판별 + 장소별 '깨끗한' 출처 목록.
사용:
  python sources.py config.json discover            # 제목에서 자주 나오는 업체명 후보 출력(장소 목록 작성용)
  python sources.py config.json fetch places.json   # 장소별 제목 언급 글 최근 20건 본문 수집
  python sources.py config.json classify places.json# 광고/AI 판별 → work/cls.json, work/cleansrc.json
  python sources.py config.json dig places.json [이름,...]  # 장소별 가격·주소·영업시간·장단점 문장 추출(작성 참고용)
places.json 의 각 장소에는 aliases(블로그 제목 매칭용 별칭 목록)가 있어야 한다."""
import sys, json, re, html, urllib.request, concurrent.futures as cf, collections
from common import load, save, work
cfg = load(sys.argv[1]); cmd = sys.argv[2]
def allposts():
    d = load(work(cfg, 'naver_blog.json')); out = {}
    for v in d.values():
        for i in v: out[i['link']] = i
    return out
def cache():
    try: return load(work(cfg, 'bodycache.json'))
    except Exception: return {}
def body(link):
    m = re.search(r'blog\.naver\.com/([^/?]+)/(\d+)', link)
    if not m: return ''
    try: h = urllib.request.urlopen(urllib.request.Request(f'https://blog.naver.com/PostView.naver?blogId={m[1]}&logNo={m[2]}', headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode('utf-8', 'ignore')
    except Exception: return ''
    i = h.find('se-main-container'); h = h[i:] if i > 0 else h
    t = html.unescape(re.sub(r'<[^>]+>', '\n', re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)))
    return '\n'.join(x.strip() for x in t.split('\n') if x.strip())[:25000]
# ---- 광고/AI 판별 규칙 (references/criteria.md 참고) ----
STRONG = re.compile(r'원고료|소정의|체험단으로 제공|작성 조건|후기 조건|조건으로 (할인|무료)|협찬|지원\s?받아|체험단|유료\s?광고|광고\s?(포함|입니다|글)|파트너스|수수료를\s?(제공|받)|업체로부터|초대\s?받아|할인\s?코드|쿠폰\s?코드|진짜 나다운 여행|링크를 통해 (예약|구매)|아래 링크(에서|로) 예약|제작 지원|#광고|#협찬|#제공')
AFF = re.compile(r'클룩|피크타임|제휴|예매하기|예약하러 가기|할인받기|myrealtrip|kkday|klook|agoda\.com|tourpik|waug\.com|link\.coupang|tripstore|mamap|trip\.com/t/')
AI = re.compile(r'결론부터 말(하면|씀)|자주 묻는 질문|FAQ|Q\s?[\.:]|한눈에 (정리|보기)|정리해\s?(드릴게요|드리겠습니다|봤어요|보았습니다)|알아보(겠습니다|도록 하겠습니다|았습니다)|살펴보(겠습니다|았습니다)|마무리하며|체크리스트|핵심 (정리|요약)|총정리|에 대해 (알아|소개)|추천 대상|이런 분께 추천|✅|📌|1️⃣|👉')
FP = re.compile(r'저는|저희|제가|우리는|우리가|남편|아내|와이프|아이가|아이들|엄마|아빠|친구랑|먹었|갔어|다녀왔|받았|했어요|했는데|였어요|더라고요|더라구요|ㅋㅋ|ㅎㅎ|ㅠ')
def classify(b):
    if not b: return 'unknown'
    if STRONG.search(b) or AFF.search(b): return 'ad'
    ai, fp = len(AI.findall(b)), len(FP.findall(b))
    if (ai >= 6 and fp < 8) or (ai >= 3 and fp < 3) or (fp < 2 and len(b) > 1500): return 'ai'
    return 'clean'
def places():
    P = load(sys.argv[3]); return [p for s in P['sheets'].values() for p in s]
def titled(al, posts):
    return sorted([i for i in posts.values() if any(a.lower() in i['title'].lower() for a in al)], key=lambda i: i['postdate'], reverse=True)

if cmd == 'discover':
    d = load(work(cfg, 'naver_blog.json')); stop = set(cfg.get('stopwords', []))
    for cat, items in d.items():
        c = collections.Counter()
        for i in items:
            for w in set(re.findall(r"[가-힣A-Za-z0-9']{2,15}", i['title'])):
                if w not in stop and cfg['destination'] not in w: c[w] += 1
        print('\n==', cat, len(items)); print([x for x in c.most_common(200) if x[1] >= 5])
elif cmd == 'fetch':
    posts = allposts(); C = cache(); need = set()
    for p in places(): need |= {i['link'] for i in titled(p['aliases'], posts)[:20] if i['link'] not in C}
    need = list(need); print('fetch', len(need))
    with cf.ThreadPoolExecutor(16) as ex:
        for l, b in zip(need, ex.map(body, need)): C[l] = b
    save(work(cfg, 'bodycache.json'), C)
elif cmd == 'classify':
    posts = allposts(); C = cache(); cls = {l: classify(b) for l, b in C.items()}
    yt = load(work(cfg, 'youtube.json')) if __import__('os').path.exists(work(cfg, 'youtube.json')) else {}
    YAD = re.compile(r'제작 지원|제작지원|유료 광고|유료광고|협찬|지원을 받|지원 받|수수료|할인\s?코드|쿠폰|제휴|광고 포함|includes paid|최저가로|예약은|예약하기|링크')
    vids = {x['id']: x for l in yt.values() for x in l}
    ycls = {i: ('ad' if YAD.search(x['desc']) else 'clean') for i, x in vids.items()}
    out = {}
    for p in places():
        ps = titled(p['aliases'], posts); al = [a.lower() for a in p['aliases']]
        out[p['name']] = {'n_title': len(ps), 'n_checked': sum(1 for x in ps if x['link'] in C),
            'clean': [x['link'] for x in ps if cls.get(x['link']) == 'clean'],
            'n_ad': sum(1 for x in ps if cls.get(x['link']) == 'ad'), 'n_ai': sum(1 for x in ps if cls.get(x['link']) == 'ai'),
            'yt': ['https://www.youtube.com/watch?v=' + i for i, x in vids.items() if ycls[i] == 'clean' and any(a in (x['title'] + x['desc']).lower() for a in al)]}
    save(work(cfg, 'cls.json'), {'blog': cls, 'yt': ycls}); save(work(cfg, 'cleansrc.json'), out)
    print(collections.Counter(cls.values()), collections.Counter(ycls.values()))
elif cmd == 'dig':
    C = cache(); CS = load(work(cfg, 'cleansrc.json')); only = sys.argv[4].split(',') if len(sys.argv) > 4 else None
    PR = re.compile(r'\d[\d,\.]*\s?(만\s?)?(' + re.escape(cfg['currency']['unit']) + r'|원|k\b|K\b|달러|불)|\$\s?\d')
    AD = re.compile(r'주소|위치\s?:|📍'); HR = re.compile(r'영업\s?시간|운영\s?시간|\d{1,2}:\d{2}\s?[~\-–]\s?\d{1,2}:\d{2}')
    NG = re.compile(r'아쉬|단점|별로|불친절|비추|실망|비싸|웨이팅|약했|더러|위생|바가지'); PO = re.compile(r'추천|최고|만족|맛있|친절|깨끗|시원|강추|재방문|가성비')
    for p in places():
        if only and p['name'] not in only: continue
        acc = {k: [] for k in '$@H-+'}
        for l in CS[p['name']]['clean'][:12]:
            L = C.get(l, '').split('\n')
            for i, x in enumerate(L):
                if any(a.lower() in x.lower() for a in p['aliases']):
                    for y in L[i:i+40]:
                        if not (6 < len(y) < 140): continue
                        for k, rx in (('$', PR), ('@', AD), ('H', HR), ('-', NG), ('+', PO)):
                            if rx.search(y) and y not in acc[k] and len(acc[k]) < 8: acc[k].append(y); break
        print(f"\n### {p['name']} (깨끗한 후기 {len(CS[p['name']]['clean'])}건)")
        for k, v in acc.items():
            for y in v: print(k, y)
