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
