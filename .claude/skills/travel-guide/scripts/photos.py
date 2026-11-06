"""5단계 대표 사진: 장소마다 깨끗한 후기 글의 사진 후보를 받아 접촉 시트를 만들고, 사람이(Claude가) 눈으로 골라 확정.
  python photos.py config.json cands places.json [이름,...]   → work/photo/cands.json, work/photo/sheet{n}.jpg (행=장소, 열=후보번호)
  python photos.py config.json pick places.json '{"장소명": 2, "다른장소": null}'  → 선택 사진 저장, null 은 사진 없음
선택 기준: 간판·외관·대표 메뉴 등 그 장소임을 알 수 있는 사진. 사람 셀카·호텔·다른 가게·제목 이미지는 제외(criteria.md)."""
import sys, os, io, re, json, base64, glob, urllib.request, concurrent.futures as cf
from PIL import Image, ImageDraw, ImageFont
from common import load, save, work, slug
cfg = load(sys.argv[1]); cmd = sys.argv[2]; P = load(sys.argv[3]); os.makedirs(work(cfg, 'photo'), exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://blog.naver.com/'}
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read()
items = {p['name']: p for s in P['sheets'].values() for p in s}
def thumb(iu):
    try:
        im = Image.open(io.BytesIO(get(iu + '?type=w773'))).convert('RGB')
        if im.width < 300 or im.height < 200: return None
        im.thumbnail((640, 640)); w, h = im.size
        tw, th = (w, int(w*0.75)) if h > w*0.75 else (int(h/0.75), h)
        im = im.crop(((w-tw)//2, (h-th)//2, (w-tw)//2+tw, (h-th)//2+th)).resize((560, 420))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=68, optimize=True, progressive=True); return b.getvalue()
    except Exception: return None
def cands(name):
    p = items[name]; al = p['aliases']
    urls = [r['u'] for r in p.get('reviews', {}).get('pos', [])] + load(work(cfg, 'cleansrc.json'))[name]['clean']
    out = []
    for u in list(dict.fromkeys(urls))[:5]:
        m = re.search(r'blog\.naver\.com/([^/?]+)/(\d+)', u)
        if not m: continue
        try: h = get(f'https://blog.naver.com/PostView.naver?blogId={m[1]}&logNo={m[2]}').decode('utf-8', 'ignore')
        except Exception: continue
        pos = min([h.find(a) for a in al if h.find(a) > 0] or [0])
        og = re.findall(r'og:image" content="([^"]+)', h)
        imgs = ([re.sub(r'\?type=.*', '', og[0]).replace('blogthumb.pstatic.net', 'postfiles.pstatic.net')] if og else []) + \
               re.findall(r'https://postfiles\.pstatic\.net/[^"\' ?]+\.(?:jpg|jpeg|png|JPG|JPEG|PNG)', h[pos:])[:3]
        for iu in list(dict.fromkeys(imgs))[:3]:
            t = thumb(iu)
            if t: out.append({'src': u, 'b64': base64.b64encode(t).decode()})
            if len(out) >= 8: return out
    return out
if cmd == 'cands':
    names = sys.argv[4].split(',') if len(sys.argv) > 4 else list(items)
    C = {}
    with cf.ThreadPoolExecutor(10) as ex:
        for n, r in zip(names, ex.map(cands, names)): C[n] = r
    save(work(cfg, 'photo', 'cands.json'), C)
    fp = glob.glob('/usr/share/fonts/**/*CJK*', recursive=True) + glob.glob('/usr/share/fonts/**/*Nanum*', recursive=True)
    f = ImageFont.truetype(fp[0], 13) if fp else ImageFont.load_default()
    for part in range(0, len(names), 9):
        sub = names[part:part+9]; W, H = 170, 140
        sheet = Image.new('RGB', (8*W+120, len(sub)*H), 'white'); d = ImageDraw.Draw(sheet)
        for r, n in enumerate(sub):
            d.text((4, r*H+50), f'{part+r} {n[:7]}', fill='black', font=f)
            for k, c in enumerate(C[n][:8]):
                sheet.paste(Image.open(io.BytesIO(base64.b64decode(c['b64']))).resize((166, 125)), (120+k*W, r*H)); d.text((122+k*W, r*H+126), str(k), fill='red', font=f)
        sheet.save(work(cfg, 'photo', f'sheet{part//9}.jpg'), quality=75)
    print({n: len(v) for n, v in C.items()}, '→ work/photo/sheet*.jpg 를 보고 pick')
elif cmd == 'pick':
    C = load(work(cfg, 'photo', 'cands.json')); sel = json.loads(sys.argv[4]); pdir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[3])), 'photos')
    os.makedirs(pdir, exist_ok=True)
    for n, k in sel.items():
        if k is None: items[n].pop('photo', None); continue
        c = C[n][k]; fn = slug(n) + '.jpg'
        open(os.path.join(pdir, fn), 'wb').write(base64.b64decode(c['b64'])); items[n]['photo'] = {'file': 'photos/' + fn, 'src': c['src']}
    save(sys.argv[3], P); print('saved', len(sel))
