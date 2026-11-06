"""3단계 검증: places.json 의 가격 숫자가 광고·AI를 뺀 후기 본문에 실제로 나오는지 대조.
사용: python check.py config.json places.json   → 근거 없는 금액을 장소별로 출력(원화 환산값은 무시)"""
import sys, re
from common import load, work
cfg = load(sys.argv[1]); P = load(sys.argv[2]); C = load(work(cfg, 'bodycache.json')); CS = load(work(cfg, 'cleansrc.json'))
def nums(t):
    v = set()
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s?만', t): v.add(round(float(m[1])*10000))
    for m in re.finditer(r'(\d{1,3}(?:[,\.]\d{3})+|\d+)\s?[kK]\b', t): v.add(int(re.sub(r'[,\.]', '', m[1]))*1000)
    for m in re.finditer(r'\d{1,3}(?:[,\.]\d{3})+|\d{4,}', t): v.add(int(re.sub(r'[,\.]', '', m.group(0))))
    return v
u = re.escape(cfg['currency']['unit']); bad = 0
for s in P['sheets'].values():
    for p in s:
        pool = set()
        for l in CS.get(p['name'], {}).get('clean', []): pool |= nums(C.get(l, ''))
        text = re.sub(r'원 / 약 [\d,]+' + u, '원', ' '.join(p.get('price', []) + p.get('extra', [])))
        local = {int(m.replace(',', '')) for m in re.findall(r'(\d{1,3}(?:,\d{3})+)\s?' + u, text)}
        miss = sorted(x for x in local if x not in pool)
        if miss: bad += 1; print(p['name'], '| 후기에서 확인 안 된 금액:', miss)
print('확인 필요 장소', bad)
