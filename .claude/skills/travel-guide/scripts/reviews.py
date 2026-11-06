"""4단계: 장소별 긍정/부정 평가 추출 준비와 병합.
  python reviews.py config.json prep places.json [배치수=6]   → work/rev/batch{i}.json (서브에이전트 입력)
  python reviews.py config.json merge places.json             → work/rev/out{i}.json 을 places.json 의 reviews 에 병합
서브에이전트 지시문은 references/criteria.md '긍정·부정 평가 추출' 참고."""
import sys, glob, json, os
from common import load, save, work
cfg = load(sys.argv[1]); cmd = sys.argv[2]; P = load(sys.argv[3])
C = load(work(cfg, 'bodycache.json')); CS = load(work(cfg, 'cleansrc.json')); os.makedirs(work(cfg, 'rev'), exist_ok=True)
items = [p for s in P['sheets'].values() for p in s]
if cmd == 'prep':
    B = int(sys.argv[4]) if len(sys.argv) > 4 else 6; batch = []
    for p in items:
        src = []
        for k, u in enumerate(CS[p['name']]['clean'][:8], 1):
            L = C.get(u, '').split('\n'); idx = [i for i, l in enumerate(L) if any(a.lower() in l.lower() for a in p['aliases'])]
            ch, seen = [], set()
            for i in idx:
                if i in seen: continue
                ch.append(' '.join(L[i:i+16])); seen |= set(range(i, i+16))
                if sum(map(len, ch)) > 800: break
            if ch: src.append({'i': k, 'url': u, 'text': ' … '.join(ch)[:900]})
        batch.append({'name': p['name'], 'sources': src})
    for b in range(B): save(work(cfg, 'rev', f'batch{b}.json'), batch[b::B])
    print('batches', B, 'places', len(batch))
elif cmd == 'merge':
    urls = {}
    for f in glob.glob(work(cfg, 'rev', 'batch*.json')):
        for it in load(f): urls[it['name']] = {s['i']: s['url'] for s in it['sources']}
    EV = {}
    for f in glob.glob(work(cfg, 'rev', 'out*.json')): EV.update(load(f))
    for p in items:
        pos, neg = [], []
        for e in EV.get(p['name'], []):
            u = urls.get(p['name'], {}).get(e['i'])
            if not u: continue
            if e.get('pos') and len(pos) < 10: pos.append({'t': e['pos'], 'u': u})
            if e.get('neg'): neg.append({'t': e['neg'], 'u': u})
        c = CS[p['name']]
        p['reviews'] = {'pos': pos, 'neg': neg, 'basis': f"광고·AI 제외 후기 {len(c['clean'])}건(장소명이 제목에 들어간 글 {c['n_title']}건 중 최근 {c['n_checked']}건 검토, 광고 {c['n_ad']}·AI {c['n_ai']}건 제외)"}
    save(sys.argv[3], P); print('merged')
