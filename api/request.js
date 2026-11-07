// POST /api/request — 여행지 추가 요청을 GitHub 이슈로 접수한다. 사이트 전체가 비밀번호(middleware.js) 뒤에 있다.
import { validateRequest } from '../lib/validate.js';
import { configured, listOpen, recentCount, createRequest, sameDest, MAX_OPEN, MAX_PER_WINDOW } from '../lib/github.js';

const json = (status, obj) => new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });
const fail = (status, error) => json(status, { ok: false, error });

function sameOrigin(req) {
  const o = req.headers.get('origin');
  if (!o) return true;
  try { const host = req.headers.get('x-forwarded-host') || req.headers.get('host') || new URL(req.url).host; return new URL(o).host === host; } catch { return false; }
}

// 이미 게시된 여행지인지(같은 사이트의 trips.json 확인). 실패하면 건너뛴다.
async function published(req) {
  try {
    const res = await fetch(new URL('/trips.json', req.url), { headers: { cookie: req.headers.get('cookie') || '' } });
    return res.ok ? await res.json() : [];
  } catch { return []; }
}

export async function POST(req) {
  if (!sameOrigin(req)) return fail(403, '허용되지 않은 요청이에요.');
  if (!(req.headers.get('content-type') || '').includes('application/json')) return fail(415, '요청 형식이 올바르지 않아요.');
  if (!configured()) return fail(503, '접수 기능이 아직 설정되지 않았어요. (GITHUB_TOKEN 필요)');

  let body;
  try { body = await req.json(); } catch { return fail(400, '요청 형식이 올바르지 않아요.'); }
  const v = validateRequest(body);
  if (!v.ok) return fail(400, v.error);
  const { destination } = v.value;

  try {
    const open = await listOpen();
    if (open.some(r => sameDest(r.destination, destination))) return fail(409, `"${destination}"은(는) 이미 접수돼 있어요.`);
    if ((await published(req)).some(t => sameDest(t.name, destination) || sameDest(t.en, destination))) return fail(409, `"${destination}"은(는) 이미 만들어져 있어요.`);
    if (open.length >= MAX_OPEN) return fail(429, '대기 중인 요청이 많아요. 잠시 뒤에 다시 시도해 주세요.');
    if ((await recentCount()) >= MAX_PER_WINDOW) return fail(429, '짧은 시간에 요청이 너무 많아요. 10분 뒤에 다시 시도해 주세요.');
    const { number } = await createRequest(v.value);
    return json(201, { ok: true, number, destination });
  } catch {
    return fail(502, '접수하지 못했어요. 잠시 뒤에 다시 시도해 주세요.');
  }
}
