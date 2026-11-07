# travel

여행지별 마사지·맛집·가볼만한 곳 정보를 정리하는 Claude Code 스킬 저장소입니다.

- 스킬: `.claude/skills/travel-guide/` (SKILL.md, scripts/, references/)
- 예시: `.claude/skills/travel-guide/examples/phuquoc/` (푸꾸옥 결과 데이터·사진)

이 저장소로 Claude Code 세션을 열고 예를 들어 이렇게 요청하면 됩니다.

> /travel-guide 다낭 — 숙소: 미케비치 ○○호텔(주소), 호이안 △△리조트(주소)

필요한 환경 설정(API 키, 허용 도메인)은 `SKILL.md`의 "환경 요구사항"을 참고하세요.

## 웹사이트(Vercel)

`public/` 폴더가 그대로 웹사이트가 되고, 루트의 `middleware.js` 가 사이트 전체를 비밀번호로 막습니다.

1. vercel.com 에 GitHub 계정으로 로그인 → **Add New… → Project** → 이 저장소(`travel`) Import
2. Framework Preset 은 **Other** 그대로, 설정은 `vercel.json` 이 처리합니다.
3. **Settings → Environment Variables** 에 `SITE_PASSWORD` = 원하는 비밀번호 추가(Production·Preview 모두) → **Deployments** 에서 Redeploy
4. `https://<프로젝트>.vercel.app` 접속 → 비밀번호 입력(30일 동안 기억)

새 여행지는 `publish_site.py` 로 `public/` 에 추가하고 메인에 푸시하면 자동 배포됩니다. 비밀번호를 바꾸면 기존 로그인은 모두 풀립니다.

### 여행지 추가 요청 폼 (1단계)

첫 화면의 "＋ 여행지 추가"로 받은 요청은 서버 함수(`api/request.js`)가 GitHub 이슈(라벨 `trip-request`)로 만들고, 열린 요청은 `api/requests.js`가 첫 화면에 "수집 대기" 카드로 보여줍니다. 기획은 `docs/add-destination-plan.md`.

1. GitHub → Settings → Developer settings → **Fine-grained personal access tokens** 에서 이 저장소 한 곳만 선택하고 **Issues: Read and write** 권한만 주어 토큰 생성
2. Vercel → Settings → Environment Variables 에 `GITHUB_TOKEN` 으로 추가(저장소를 바꾸려면 `GITHUB_REPO` = `소유자/이름`) → Redeploy
3. 토큰이 없으면 폼 버튼이 "준비 중"으로 비활성화됩니다.

시험: `npm test` (GitHub 는 가짜로 대체).

### 숙소 검색 (구글 장소 검색, 선택)

폼의 숙소 입력은 `GOOGLE_MAPS_BROWSER_KEY` 가 있으면 구글 장소 검색(Places API New)으로 숙소를 골라 주소·좌표·장소 ID 를 자동으로 채우고, 없으면 구글맵 링크 직접 입력으로 동작합니다. 지도 화면(Maps JavaScript API)은 쓰지 않습니다.

1. Google Cloud 콘솔에서 프로젝트를 만들고 결제 계정을 연결, **Places API (New)** 사용 설정
2. **브라우저용 키**: 사용자 인증 정보 → API 키 만들기 → 애플리케이션 제한은 *웹사이트(HTTP 리퍼러)* 에 사이트 주소(`https://<도메인>/*`), API 제한은 *Places API (New)* 만 → Vercel 환경변수 `GOOGLE_MAPS_BROWSER_KEY`
3. **한도 걸기(중요)**: API 및 서비스 → Places API (New) → 할당량에서 일일 요청 한도를 무료 사용량보다 낮게 설정하고, 결제 → 예산 및 알림도 설정
4. (선택) **서버 검증 키**: 같은 방식으로 키를 하나 더 만들되 애플리케이션 제한 없이 API 제한만 *Places API (New)* → `GOOGLE_MAPS_SERVER_KEY`. 있으면 접수할 때 서버가 장소 ID 로 좌표를 다시 조회해 다르면 거절합니다.

