"""공통 유틸: 설정 로드, 통화 변환(원 / 현지통화), 글머리표, 목록 분리."""
import json, os, re, sys

def load(path):
    with open(path, encoding='utf-8') as f: return json.load(f)

def save(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: json.dump(obj, f, ensure_ascii=False, indent=1)

def work(cfg, *p):
    d = cfg.get('work_dir', 'work'); os.makedirs(d, exist_ok=True); return os.path.join(d, *p)

class Money:
    """현지 통화 금액을 '원 / 현지' 형식으로 바꾼다. 이미 바뀐 문자열은 건드리지 않는다(멱등)."""
    def __init__(self, cfg):
        c = cfg['currency']; self.unit = c['unit']; self.rate = c['krw_per_unit']
    def _w(self, v): return f"{int(round(v*self.rate, -2 if v*self.rate >= 1000 else 0)):,}"
    def _l(self, v):
        x = v / self.rate
        nd = -3 if x >= 1e4 else (-2 if x >= 1e3 else 0)
        return f"{int(round(x, nd if x < 1e6 else -4)):,}"
    def conv(self, s):
        u = re.escape(self.unit)
        s = re.sub(r'\s*\(약\s?[\d,\.~]+\s?(만\s?)?원\)', '', s)
        s = re.sub(r'(\d+)만\s?원', lambda m: f"{int(m[1])*10000:,}원", s)
        def loc(m):
            a = int(m[1].replace(',', '')); b = int(m[2].replace(',', '')) if m[2] else None
            return f"{self._w(a)}~{self._w(b)}원 / {m[1]}~{m[2]}{self.unit}" if b else f"{self._w(a)}원 / {m[1]}{self.unit}"
        s = re.sub(r'(?<!원 / )(?<!원 / 약 )(?<!대 / )(?<!대 / 약 )(?<![\d,~])(\d{1,3}(?:,\d{3})+|\d{3,})(?:\s?~\s?(\d{1,3}(?:,\d{3})+|\d{3,}))?' + u, loc, s)
        def won(m):
            a = int(m[1].replace(',', '')); suf = m[2]
            return f"{m[1]}{suf} / 약 {self._l(a)}{self.unit}{'대' if suf == '원대' else ''}"
        s = re.sub(r'(?<![\d,~])(\d{1,3}(?:,\d{3})+)(원대|원)(?!대?\s?/)', won, s)
        return s

def bl(items):
    items = [i.strip() for i in items if i and str(i).strip() and str(i).strip() != '–']
    if not items: return '–'
    return items[0] if len(items) == 1 else '\n'.join('* ' + i for i in items)

def slug(s): return re.sub(r'[^0-9A-Za-z가-힣]+', '_', s).strip('_')[:60]
