"""좌표 찾기(OpenStreetMap Nominatim). 정확한 업체 좌표가 없으면 지역 기준점을 쓰고 coord_note 에 '근사' 표시.
사용: python geo.py "검색어1" "검색어2" ...   (국가코드는 환경변수 GEO_CC, 기본 vn)"""
import sys, os, json, time, urllib.request, urllib.parse
cc = os.environ.get('GEO_CC', 'vn')
for q in sys.argv[1:]:
    u = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({'q': q, 'format': 'json', 'limit': 3, 'countrycodes': cc})
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'travel-guide-skill/1.0'}), timeout=20))
    print(q, '->', [(x['display_name'][:80], x['lat'], x['lon']) for x in r]); time.sleep(1.1)
