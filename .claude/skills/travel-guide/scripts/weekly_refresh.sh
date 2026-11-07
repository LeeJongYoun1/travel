#!/usr/bin/env bash
# 주간 '새 소식' 갱신: 새로 수집 → 본문 가져오기 → 광고/AI 판별 → HTML 재생성 → public/ 게시.
# 기존 examples/<여행지>/places.json(후기 평가·사진·링크)은 그대로 두고, 후기 글 목록·작성일과 수집 통계만 새로 만든다.
# 사용: bash weekly_refresh.sh [예시폴더이름=phuquoc]   (NAVER_CLIENT_ID/SECRET, YOUTUBE_API_KEY 환경변수 필요)
# 끝나면 변경된 config.json 과 public/ 을 git 으로 커밋·푸시하면 Vercel 이 다시 배포한다.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../../../.." && pwd); SK=$REPO/.claude/skills/travel-guide; EX=$SK/examples/${1:-phuquoc}
W=$(mktemp -d); cd "$W"
cp "$EX/config.json" "$EX/places.json" .; cp -r "$EX/photos" .
TODAY=$(TZ=Asia/Seoul date +%F)
python3 - "$TODAY" <<'PY'
import json, sys
c = json.load(open('config.json')); c['built'] = sys.argv[1]; json.dump(c, open('config.json', 'w'), ensure_ascii=False, indent=1)
PY
python3 "$SK/scripts/collect.py" config.json
python3 "$SK/scripts/sources.py" config.json fetch places.json
python3 "$SK/scripts/sources.py" config.json classify places.json
python3 - <<'PY'
import json, collections
B = json.load(open('work/naver_blog.json')); cls = json.load(open('work/cls.json')); c = json.load(open('config.json'))
n = len({i['link'] for v in B.values() for i in v}); k = collections.Counter(cls['blog'].values()); y = collections.Counter(cls['yt'].values())
c['stats'] = f"수집 규모: 네이버 블로그 {n:,}건(2025년 이후) 중 본문 {sum(k.values()):,}건 분석 → 광고 {k['ad']} · AI 의심 {k['ai']} · 사용 {k['clean']:,}건 / 유튜브 {sum(y.values())}건 중 광고 의심 {y['ad']} 제외"
json.dump(c, open('config.json', 'w'), ensure_ascii=False, indent=1); print(c['stats'])
PY
python3 "$SK/scripts/build_html.py" config.json places.json out
python3 "$SK/scripts/publish_site.py" config.json places.json out
cp config.json "$EX/config.json"
echo "done: $TODAY (작업 폴더 $W)"
