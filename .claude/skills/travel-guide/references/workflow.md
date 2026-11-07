# 작업 명령 순서

작업 폴더 하나를 만들고(예: `~/trip_danang`) 그 안에서 실행한다. `SK=<이 스킬 폴더>/scripts`.

```bash
cp $SK/../examples/phuquoc/config.json config.json   # 편집: destination, destination_en, currency, hotels, categories.queries, region_order, region_note, lede, stopwords
python3 $SK/geo.py "숙소 영문명 도시" "지역 기준점"    # 숙소·지역 좌표 (GEO_CC=th 등 국가코드)
python3 $SK/collect.py config.json                     # work/naver_blog.json, naver_cafe.json, youtube.json
python3 $SK/sources.py config.json discover            # 제목 빈도 → places.json 초안 작성
```

`places.json` 형식(장소 하나):
```json
{"sheets": {"마사지": [{
  "name": "델루나 스파", "region": "중부", "aliases": ["델루나"],
  "lat": 10.13, "lon": 103.98, "coord_note": "근사(지역 기준)",
  "desc": "소나시 야시장 안(Đường Sonashi 9)",
  "price": ["아로마 전신 90분 780,000동", "60분 590,000동"],
  "pros": ["압이 센 편", "카톡 한국어 예약"], "cons": ["픽업 유료"], "extra": ["영업 09:00~23:00"],
  "map_query": "Delluna Spa 139 Đường Trần Hưng Đạo Phú Quốc", "map_note": "",
  "home": [{"label": "인스타그램(접속 확인)", "url": "https://..."}],
  "booking": [{"label": "공식 예약", "url": "https://..."}], "booking_note": ["카카오톡 ID: xxx"],
  "photo": {"file": "photos/델루나_스파.jpg", "src": "https://blog.naver.com/..."},
  "reviews": {"pos": [{"t": "...", "u": "..."}], "neg": [], "basis": "광고·AI 제외 후기 23건(...)", "neg_note": ""}
}]}}
```
- price/pros/cons/extra 는 현지 통화 금액 그대로 적는다(원화는 빌드 때 자동으로 붙음, 이미 붙어 있어도 중복 안 됨).
- 좌표가 없으면 lat/lon 을 null 로 두면 거리 칸이 "확인필요"가 된다.

```bash
python3 $SK/sources.py config.json fetch places.json        # 장소별 최근 20건 본문 수집
python3 $SK/sources.py config.json classify places.json     # 광고/AI 판별 → work/cleansrc.json
python3 $SK/sources.py config.json dig places.json [이름,...] # 작성 근거 문장 보기 → places.json 채우기
python3 $SK/check.py config.json places.json                # 근거 없는 금액 확인 → 수정
python3 $SK/reviews.py config.json prep places.json 6       # work/rev/batch0..5.json
#  → 서브에이전트 6개 병렬(criteria.md 지시문), 각자 work/rev/out{i}.json 작성
python3 $SK/reviews.py config.json merge places.json
python3 $SK/photos.py config.json cands places.json         # work/photo/sheet*.jpg 를 Read 로 보고
python3 $SK/photos.py config.json pick places.json '{"델루나 스파": 0, "라온 스파": null}'
#  홈페이지: 서브에이전트 4개 병렬 확인(criteria.md) → places.json home 갱신
#  예약: 서브에이전트 3개 병렬로 공식 예약/티켓 페이지 확인 → places.json booking, 후기의 카톡 ID 등은 booking_note
python3 $SK/build_xlsx.py config.json places.json out/<여행지>_여행정보.xlsx
python3 <xlsx 스킬>/scripts/recalc.py out/<여행지>_여행정보.xlsx 180   # total_errors 0 확인
python3 $SK/build_html.py config.json places.json out out/<여행지>_여행정보.xlsx
```
마지막으로 Playwright 로 공유용 HTML 을 한 번 열어 오류·가로 스크롤이 없는지 보고, `out/<여행지>_여행노트.html` 을 Artifact 로 게시, 엑셀·공유용 HTML·zip 을 SendUserFile(attach)로 보낸다.

웹사이트(Vercel) 게시:
```bash
python3 $SK/publish_site.py config.json places.json out   # → <저장소>/public/<영문이름>/index.html, public/index.html 목록 갱신
git add public && git commit -m "Publish <여행지> to site" && git push   # Vercel 자동 배포(메인 브랜치 기준)
```
