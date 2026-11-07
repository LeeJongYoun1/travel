// GitHub 이슈를 요청 저장소로 쓴다. 토큰은 Vercel 환경변수 GITHUB_TOKEN(이 저장소 Issues 읽기/쓰기만), 저장소는 GITHUB_REPO(기본 LeeJongYoun1/travel).
import { normName } from './validate.js';

export const LABEL_REQ = 'trip-request';
export const LABEL_APPROVED = '승인';
export const LABEL_RUNNING = '수집중';
export const TITLE_PREFIX = '[여행지 요청] ';
export const MAX_OPEN = 10;          // 대기 중 요청 상한
export const MAX_PER_WINDOW = 3;     // 10분 안에 접수할 수 있는 건수(서버 저장소 없이 이슈 목록으로 계산)
export const WINDOW_MS = 10 * 60 * 1000;

export const configured = () => Boolean(process.env.GITHUB_TOKEN);
const repo = () => process.env.GITHUB_REPO || 'LeeJongYoun1/travel';

async function gh(path, init = {}) {
  const res = await fetch('https://api.github.com/repos/' + repo() + path, {
    ...init,
    headers: {
      Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'ssok-travel',
      Authorization: 'Bearer ' + process.env.GITHUB_TOKEN, ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    },
  });
  if (!res.ok) throw new Error('GitHub ' + res.status);
  return res.json();
}

const destOf = issue => String(issue.title || '').startsWith(TITLE_PREFIX) ? issue.title.slice(TITLE_PREFIX.length) : issue.title;
const statusOf = issue => {
  const names = (issue.labels || []).map(l => (typeof l === 'string' ? l : l.name));
  return names.includes(LABEL_RUNNING) ? 'collecting' : names.includes(LABEL_APPROVED) ? 'approved' : 'pending';
};

// 열린 요청 목록(화면 표시용: 번호·여행지·상태·접수일만)
export async function listOpen() {
  const items = await gh(`/issues?labels=${encodeURIComponent(LABEL_REQ)}&state=open&per_page=30&sort=created&direction=desc`);
  return items.filter(i => !i.pull_request).map(i => ({ number: i.number, destination: destOf(i), status: statusOf(i), createdAt: i.created_at }));
}

export async function recentCount(now = Date.now()) {
  const since = new Date(now - WINDOW_MS).toISOString();
  const items = await gh(`/issues?labels=${encodeURIComponent(LABEL_REQ)}&state=all&since=${encodeURIComponent(since)}&per_page=30`);
  return items.filter(i => !i.pull_request && Date.parse(i.created_at) >= now - WINDOW_MS).length;
}

export function issueBody(v) {
  const payload = { version: 1, ...v, submittedAt: new Date().toISOString() };
  return `쏙여행 폼에서 접수된 요청입니다. 승인하려면 이 이슈에 \`${LABEL_APPROVED}\` 라벨을 붙이세요.\n\n- 여행지: ${v.destination}\n\n\`\`\`json\n${JSON.stringify(payload, null, 2)}\n\`\`\`\n\n<!-- trip-request:v1 -->\n`;
}

export async function createRequest(v) {
  const issue = await gh('/issues', { method: 'POST', body: JSON.stringify({ title: TITLE_PREFIX + v.destination, body: issueBody(v), labels: [LABEL_REQ] }) });
  return { number: issue.number };
}

export const sameDest = (a, b) => normName(a) === normName(b);
