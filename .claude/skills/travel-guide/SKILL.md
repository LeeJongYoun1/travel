---
name: travel-guide
description: 여행지 하나의 마사지·맛집·가볼만한 곳 정보를 2025년 이후 네이버 블로그·카페·유튜브 후기에서 광고와 AI 글을 걸러내고 모아, 숙소별 거리·이동시간, 원/현지통화 가격, 긍정·부정 평가(출처 링크), 대표 사진, 홈페이지, 구글맵 링크가 들어간 엑셀과 HTML 페이지(카톡 공유용 포함)로 만든다. "OO 여행 정보 정리해줘", "/travel-guide 다낭" 같은 요청에 사용.
---

# 여행 정보 정리 (travel-guide)

푸꾸옥 작업(examples/phuquoc)과 같은 형식·품질의 결과물을 다른 여행지에 대해 만든다.
결과물: `<여행지>_여행정보.xlsx`, `<여행지>_여행노트.html`(Artifact 게시용), `<여행지>_여행노트_공유용.html`(카톡 전송용), `<여행지>_여행자료.zip`.

## 시작 전에 사용자에게 받을 것 (한 번에 묻기)
1. 여행지 이름(한글·영문)
2. 숙소 1~3곳: 이름, 주소, 짧은 이름(예: "중숙", "남숙")
3. 현지 통화 단위와 원화 환율(모르면 검색해서 제안), 이동수단(그랩/택시 등)
나머지는 기본값을 쓴다: 2025년 이후 자료, 광고·AI 제외, 카테고리 = 마사지/맛집/가볼만한 곳, 블로그 사진 + 출처 표기.

## 환경 요구사항 (클라우드 환경 설정)
- 환경변수: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` (NCP NAVER API HUB 키, 2026-07 이후 openapi.naver.com 대신 사용), `YOUTUBE_API_KEY`
- 허용 도메인: `naverapihub.apigw.ntruss.com`, `blog.naver.com`, `*.pstatic.net`, `www.googleapis.com`, `nominatim.openstreetmap.org`, `pf.kakao.com`, `instagram.com`, `www.instagram.com`
- 막혀 있으면 read_documentation(environment.network)을 읽고 사용자에게 추가를 요청한다.

## 진행 순서 (자세한 명령은 references/workflow.md)
1. `config.json` 작성 — examples/phuquoc/config.json 을 복사해 여행지·숙소·통화·검색어·지역 구분을 바꾼다. 숙소 좌표는 `scripts/geo.py` 로 찾는다.
2. 수집 `scripts/collect.py` → 후보 발굴 `scripts/sources.py discover` 로 자주 언급되는 업체명을 보고 `places.json` 초안(장소별 name, region, aliases)을 만든다. 카테고리당 20~40곳.
3. `sources.py fetch` → `classify`(광고/AI 판별) → `dig`(가격·주소·영업시간·장단점 문장 추출)를 보고 각 장소의 desc/price/pros/cons/extra/lat/lon/map_query 를 채운다. 근거는 깨끗한 후기에서만. `scripts/check.py` 로 가격이 깨끗한 후기에 있는지 검증하고, 없으면 지우거나 고친다.
4. `scripts/reviews.py prep` → 서브에이전트 배치(병렬)로 긍정/부정 평가 추출 → `merge`. 부정 평가가 없는 곳은 검색어를 넓혀 후기를 더 찾는다(criteria.md).
5. 사진 `scripts/photos.py cands` → 접촉 시트를 직접 보고 `pick`(엉뚱한 사진은 다른 후보로, 마땅치 않으면 null).
6. 홈페이지: 서브에이전트로 장소별 구글 검색 확인(criteria.md 규칙), 블로그 기재 링크는 직접 접속해 확인. 구글맵: 블로그의 구글맵 카드 등록명·주소로 map_query 설정, 못 찾은 곳은 map_note 표시.
7. 빌드: `scripts/build_xlsx.py` → xlsx 스킬의 `recalc.py`(오류 0 확인) → `scripts/build_html.py`. HTML은 한 번 화면 확인 후 Artifact 로 게시하고, 엑셀·공유용 HTML·zip 을 SendUserFile 로 전달.

## 지켜야 할 기준 (references/criteria.md)
- 2025-01-01 이후 글만. 네이버 카페는 작성일이 없어 출처로 쓰지 않음(언급 빈도 참고만).
- 광고(협찬·체험단·원고료·수수료 고지, 제휴·할인코드·예약 링크, 제작지원 유튜브, 여행사·예약플랫폼·호텔 페이지)와 AI 생성 의심 글 제외.
- 가격은 "원 / 현지통화" 순서, 여러 항목은 `* ` 글머리표 줄바꿈.
- 지어낸 URL·가격 금지. 확인 못 한 것은 "(블로그 기재)" 또는 "확인 못 함"으로 표시.
- 사진 저작권은 블로거에게 있음을 표기하고 개인 여행 준비용으로 안내.
