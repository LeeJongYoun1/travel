"""6단계: places.json → 엑셀(시트: 카테고리별 + 설명 + 좌표). 거리·이동시간은 엑셀 수식으로 계산(설명 시트의 노란 칸을 바꾸면 재계산).
사용: python build_xlsx.py config.json places.json 출력.xlsx
그 다음 반드시: python <xlsx 스킬>/scripts/recalc.py 출력.xlsx 180   (LibreOffice 재계산, 오류 0 확인)"""
import sys, os, io, re, collections, urllib.parse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PImage
from common import load, Money, bl
cfg = load(sys.argv[1]); P = load(sys.argv[2]); OUT = sys.argv[3]; base = os.path.dirname(os.path.abspath(sys.argv[2]))
M = Money(cfg); T = cfg['travel']; HOT = cfg['hotels']
F = Font(name='Arial', size=10); FB = Font(name='Arial', size=10, bold=True, color='FFFFFF'); FIN = Font(name='Arial', size=10, color='0000FF')
LINK = Font(name='Arial', size=10, color='0563C1', underline='single')
HF = PatternFill('solid', fgColor='305496'); YF = PatternFill('solid', fgColor='FFFF00')
th = Side(style='thin', color='BFBFBF'); BD = Border(left=th, right=th, top=th, bottom=th); WR = Alignment(wrap_text=True, vertical='top')
def gmap(p): return 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(p.get('map_query') or (p['name'] + ' ' + cfg.get('destination_en', '')))
wb = Workbook(); info = wb.active; info.title = '설명'; coord = wb.create_sheet('좌표')
# ---- 설명 시트: 숙소 좌표(행 5~), 이동 가정값 ----
info.column_dimensions['B'].width = 26; info.column_dimensions['C'].width = 14; info.column_dimensions['D'].width = 14; info.column_dimensions['E'].width = 80
info['B1'] = f"{cfg['destination']} 여행 정보 시트 설명"; info['B1'].font = Font(name='Arial', size=14, bold=True)
info['B2'] = f"작성일 {cfg.get('built', '')} · {cfg.get('since', '20250101')[:4]}년 이후 자료 · 환율 가정 1{cfg['currency']['unit']} ≈ {cfg['currency']['krw_per_unit']}원"; info['B2'].font = F
for i, h in enumerate(['구분', '위도', '경도', '설명'], 2):
    c = info.cell(4, i, h); c.font = FB; c.fill = HF; c.border = BD
HROW = {}
for k, h in enumerate(HOT):
    r = 5 + k; HROW[h['short']] = r
    for i, v in enumerate([h['label'], h['lat'], h['lon'], h.get('note', '')], 2):
        c = info.cell(r, i, v); c.font = FIN if i in (3, 4) else F; c.border = BD; c.alignment = WR
        if i in (3, 4): c.fill = YF
pr = 5 + len(HOT) + 1
params = [('도로 보정계수', T['road_factor'], '직선거리 × 보정계수 = 예상 도로거리(km)'),
          (f"{T['mode']} 대기·승하차(분)", T['wait_min'], f"{T['mode']} 예상시간 = 대기 + 도로거리 ÷ 평균속도, 5분 단위 반올림(최소 5분). 1km 미만은 도보(시속 {T['walk_kmh']}km)"),
          (f"{T['mode']} 평균속도(km/h)", T['speed_kmh'], '현지 도로 사정 가정값. 후기의 실제 이동시간 사례와 맞춰 조정')]
PROW = {}
for k, (a, v, d) in enumerate(params):
    r = pr + k; PROW[k] = r
    info.cell(r, 2, a).font = F; c = info.cell(r, 3, v); c.font = FIN; c.fill = YF; e = info.cell(r, 5, d); e.font = F; e.alignment = WR
def dist(r, hs, nmc):
    hr = HROW[hs]; la = f"INDEX(좌표!$B:$B,MATCH(${nmc}{r},좌표!$A:$A,0))"; lo = f"INDEX(좌표!$C:$C,MATCH(${nmc}{r},좌표!$A:$A,0))"
    D = (f"ROUND(6371*2*ASIN(SQRT(SIN(RADIANS({la}-설명!$C${hr})/2)^2+COS(RADIANS(설명!$C${hr}))*COS(RADIANS({la}))"
         f"*SIN(RADIANS({lo}-설명!$D${hr})/2)^2))*설명!$C${PROW[0]},1)")
    return (f'=IFERROR(TEXT({D},"0.0")&"km · "&IF({D}<1,"도보 약 "&MAX(5,ROUND({D}/{T["walk_kmh"]}*60/5,0)*5),'
            f'"{T["mode"]} 약 "&MAX(5,ROUND((설명!$C${PROW[1]}+{D}/설명!$C${PROW[2]}*60)/5,0)*5))&"분","확인필요")')
# ---- 카테고리 시트 ----
SRCRANGE = {}; ALLURLS = []
for sname, rows in P['sheets'].items():
    ws = wb.create_sheet(sname); plabel = cfg['categories'].get(sname, {}).get('price_label', '가격') + ' (원 / ' + cfg['currency']['unit'] + ')'
    H = ['지역'] + [h['short'] + '거리' for h in HOT] + ['업체명', '대표사진', '홈페이지', '예약', '구글맵', '설명', plabel, '장점', '단점', '추가정보', '긍정평가 (출처)', '부정평가 (출처)']
    W = [9] + [15]*len(HOT) + [20, 25, 30, 30, 18, 40, 52, 34, 30, 34, 62, 62]
    nc = 1 + len(HOT)  # 업체명 직전 열
    for i, h in enumerate(H, 1):
        c = ws.cell(1, i, h); c.font = FB; c.fill = HF; c.border = BD; c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = W[i-1]
    namecol = get_column_letter(nc + 1)
    SRCRANGE[sname] = f"${get_column_letter(len(H)-1)}:${get_column_letter(len(H))}"
    for r, p in enumerate(rows, 2):
        rv = p.get('reviews', {}); pos = rv.get('pos', []); neg = rv.get('neg', [])
        fmt = lambda L, e: '\n'.join(f"* {x['t']}\n   출처: {x['u']}" for x in L) if L else e
        ALLURLS += list(dict.fromkeys([x['u'] for x in pos + neg]))
        ph = p.get('photo'); hp = p.get('home', [])
        extra = list(p.get('extra', [])) + ([rv['basis']] if rv.get('basis') else [])
        vals = [p['region']] + [dist(r, h['short'], namecol) for h in HOT] + [
            p['name'], ('사진: ' + ph['src']) if ph else '사진 없음', bl([f"{h['label']} {h['url']}" for h in hp]) if hp else cfg.get('no_home_text', '구글 검색으로 확인된 공식 홈페이지·채널 없음'),
            bl([f"{x['label']} {x['url']}" for x in p.get('booking', [])] + p.get('booking_note', [])) if (p.get('booking') or p.get('booking_note')) else '온라인 예약 페이지 없음(현장·전화 예약)',
            '구글맵에서 보기' + (f" ({p['map_note']})" if p.get('map_note') else ''), p.get('desc', ''),
            bl([M.conv(x) for x in p.get('price', [])]), bl([M.conv(x) for x in p.get('pros', [])]), bl([M.conv(x) for x in p.get('cons', [])]),
            bl([M.conv(x) for x in extra]), fmt(pos, '검토한 후기에서 긍정 평가를 찾지 못함'), fmt(neg, rv.get('neg_note') or '검토한 후기에서 부정 평가를 찾지 못함')]
        for i, v in enumerate(vals, 1):
            c = ws.cell(r, i, v); c.font = F; c.alignment = WR; c.border = BD
            col = H[i-1]
            if col == '지역' or col.endswith('거리'): c.alignment = Alignment(horizontal='center', vertical='top', wrap_text=True)
            if col == '대표사진':
                c.font = Font(name='Arial', size=8, color='5B706D'); c.alignment = Alignment(vertical='bottom', wrap_text=True)
                if ph: c.hyperlink = ph['src']
            if col == '구글맵': c.hyperlink = gmap(p); c.font = LINK
            if col == '홈페이지' and len(hp) == 1: c.hyperlink = hp[0]['url']; c.font = LINK
            if col == '예약' and len(p.get('booking', [])) >= 1: c.hyperlink = p['booking'][0]['url']; c.font = LINK
        if ph and os.path.exists(os.path.join(base, ph['file'])):
            im = PImage.open(os.path.join(base, ph['file'])); im.thumbnail((170, 128)); b = io.BytesIO(); im.convert('RGB').save(b, 'JPEG', quality=72); b.seek(0)
            xi = XLImage(b); xi.width, xi.height = 170, 128; ws.add_image(xi, f"{get_column_letter(nc+2)}{r}")
        lines = max(sum(max(1, len(x)//max(1, int(W[i]*1.1))+1) for x in str(v).split('\n')) for i, v in enumerate(vals) if isinstance(v, str) and i > nc+4)
        ws.row_dimensions[r].height = max(125 if ph else 40, min(409, lines*13.5))
    ws.freeze_panes = f"{get_column_letter(nc+2)}2"; ws.auto_filter.ref = f"A1:{get_column_letter(len(H))}{len(rows)+1}"
# ---- 좌표 시트 ----
for i, h in enumerate(['업체명', '위도', '경도', '좌표 기준'], 1):
    c = coord.cell(1, i, h); c.font = FB; c.fill = HF
r = 2
for rows in P['sheets'].values():
    for p in rows:
        if p.get('lat') is None: continue
        for i, v in enumerate([p['name'], p['lat'], p['lon'], p.get('coord_note', '근사(지역 기준)')], 1): coord.cell(r, i, v).font = FIN if i in (2, 3) else F
        r += 1
for col, w in zip('ABCD', [30, 12, 12, 40]): coord.column_dimensions[col].width = w
coord.cell(r+1, 1, '좌표 출처: OpenStreetMap Nominatim 검색. "근사"는 주소·지역 기준 추정 좌표(거리 오차 1~2km). 파란 숫자는 직접 수정 가능.').font = F
# ---- 컬럼 설명 + 상위 출처 ----
r0 = pr + len(params) + 1
info.cell(r0, 2, '컬럼 설명').font = Font(name='Arial', size=11, bold=True)
cols = [('지역', cfg.get('region_note', '권역 구분')),
        ('○○거리', f"각 숙소에서 업체까지 예상 도로거리(km)와 {T['mode']}(1km 미만은 도보) 예상시간. 좌표 시트 위경도로 계산"),
        ('대표사진', '광고가 아닌 후기 글의 대표 사진과 그 글 주소(저작권은 블로거에게 있음, 개인 여행 준비용)'),
        ('홈페이지', '구글 검색·직접 접속으로 확인한 업체 자체 홈페이지(없으면 공식 SNS·카카오톡 채널). "(블로그 기재)"는 후기에만 적혀 있고 확인 못 한 것'),
        ('예약', '업체·운영사의 공식 온라인 예약/티켓 페이지(예약 대행·OTA 제외)와 후기에 반복해서 나온 카카오톡 ID·WhatsApp 예약 연락처. 링크는 첫 번째 예약 페이지로 연결'),
        ('구글맵', '구글맵 검색 링크(블로그 구글맵 카드의 등록명·주소 우선). 괄호 표시는 목록에서 골라야 하거나 주소 위치로만 이동'),
        ('설명', '위치와 업체·장소 소개'), ('가격', f"후기에서 확인한 금액을 '원 / {cfg['currency']['unit']}' 순서로 표기. 여러 항목은 * 글머리표"),
        ('장점 / 단점 / 추가정보', '광고·AI 제외 후기에서 반복해서 나온 내용. 추가정보 마지막 줄은 근거 후기 수'),
        ('긍정평가 / 부정평가', '후기 글마다 좋았던 점·아쉬웠던 점을 한 줄로 요약하고 바로 아래 그 글 URL(출처)')]
for k, (a, b) in enumerate(cols, r0+1):
    info.cell(k, 2, a).font = Font(name='Arial', size=10, bold=True); c = info.cell(k, 5, b); c.font = F; c.alignment = WR
r1 = r0 + len(cols) + 2
info.cell(r1, 2, '주요 출처 상위 10 (블로거·채널 단위, 긍정·부정평가 컬럼 등장 횟수)').font = Font(name='Arial', size=11, bold=True)
for i, h in enumerate(['순위', '출처', '등장 행 수'], 2):
    c = info.cell(r1+1, i, h); c.font = FB; c.fill = HF
cnt = collections.Counter(); keys = {}
for u in ALLURLS:
    m = re.search(r'blog\.naver\.com/([^/]+)/', u)
    k, key = (('네이버 블로그 ' + m[1]), 'blog.naver.com/' + m[1] + '/') if m else (re.sub(r'https?://(www\.)?([^/]+).*', r'\2', u),) * 2
    cnt[k] += 1; keys[k] = key
for i, (name, n) in enumerate(cnt.most_common(10), 1):
    rr = r1 + 1 + i; info.cell(rr, 2, i).font = F; info.cell(rr, 3, name).font = F
    parts = [f'COUNTIF({("" if " " not in s else chr(39))}{s}{("" if " " not in s else chr(39))}!{SRCRANGE[s]},"*{keys[name]}*")' for s in P['sheets']]
    info.cell(rr, 4, '=' + '+'.join(parts)).font = F
if cfg.get('stats'): info.cell(r1 + 13, 2, cfg['stats']).font = F
wb._sheets = [wb[s] for s in P['sheets']] + [info, coord]; wb.active = 0
wb.save(OUT); print('saved', OUT)
