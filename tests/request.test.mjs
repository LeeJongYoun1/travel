// 실행: npm test   (GitHub 는 fetch 를 가짜로 바꿔 시험한다)
import test from 'node:test';
import assert from 'node:assert/strict';
import { validateRequest } from '../lib/validate.js';

const good = () => ({
  destination: '다낭', companions: ['아이 동반', '없는보기'], season: '2026-12', interests: ['카페', '쇼핑'],
  hotels: [{ name: '솔 바이 멜리아', short: '중숙', address: 'Bai Truong, Phu Quoc', mapUrl: 'https://maps.app.goo.gl/abc123' }],
});

test('정상 입력은 통과하고 허용 목록 밖 동행자는 걸러진다', () => {
  const r = validateRequest(good(), new Date('2026-11-07'));
  assert.equal(r.ok, true);
  assert.deepEqual(r.value.companions, ['아이 동반']);
  assert.deepEqual(r.value.interests, ['카페', '쇼핑']);
});

test('숙소 없음·4곳·잘못된 링크·봇 칸은 거절', () => {
  const t = f => { const b = good(); f(b); return validateRequest(b, new Date('2026-11-07')); };
  assert.equal(t(b => { b.hotels = []; }).ok, false);
  assert.equal(t(b => { b.hotels = Array(4).fill(b.hotels[0]); }).ok, false);
  assert.equal(t(b => { b.hotels[0].mapUrl = 'https://evil.example/maps/x'; }).ok, false);
  assert.equal(t(b => { b.hotels[0].mapUrl = 'http://maps.app.goo.gl/x'; }).ok, false);
  assert.equal(t(b => { b.hotels[0].mapUrl = 'https://www.google.com/search?q=x'; }).ok, false);
  assert.equal(t(b => { b.website = 'x'; }).ok, false);
});

test('새 분야는 2개까지, 기본 분야·중복은 무시', () => {
  const t = i => { const b = good(); b.interests = i; return validateRequest(b, new Date('2026-11-07')); };
  assert.equal(t(['카페', '쇼핑', '야경']).ok, false);
  assert.deepEqual(t(['맛집', '가볼 만한 곳', '카페', ' 카페 ']).value.interests, ['카페']);
  assert.deepEqual(t(['x`y<b>']).value.interests, ['xyb']);   // 백틱·꺾쇠는 지워진다
  assert.equal(t(['카페!!']).ok, false);
});

test('여행지·시기 형식 검사, 줄바꿈과 백틱 제거', () => {
  const t = f => { const b = good(); f(b); return validateRequest(b, new Date('2026-11-07')); };
  assert.equal(t(b => { b.destination = '다낭\n# 제목'; }).ok, false);
  assert.equal(t(b => { b.destination = '@everyone'; }).ok, false);
  assert.equal(t(b => { b.season = '2026-13'; }).ok, false);
  assert.equal(t(b => { b.season = ''; }).ok, true);
  const r = t(b => { b.hotels[0].name = '호텔`\n<b>이름</b>'; });
  assert.equal(r.ok, true);
  assert.equal(r.value.hotels[0].name, '호텔 b이름/b');
});

// ---- API 핸들러(GitHub 가짜) ----
process.env.GITHUB_TOKEN = 'test-token';
process.env.GITHUB_REPO = 'o/r';
const { POST } = await import('../api/request.js');
const { GET } = await import('../api/requests.js');

function mockGitHub({ open = [], recent = [] } = {}) {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url);
    calls.push({ url: u, init });
    if (u.startsWith('https://api.github.com/repos/o/r/issues') && init.method === 'POST') return new Response(JSON.stringify({ number: 7 }), { status: 201 });
    if (u.includes('state=open')) return new Response(JSON.stringify(open), { status: 200 });
    if (u.includes('state=all')) return new Response(JSON.stringify(recent), { status: 200 });
    if (u.endsWith('/trips.json')) return new Response(JSON.stringify([{ key: 'phuquoc', name: '푸꾸옥', en: 'Phu Quoc' }]), { status: 200 });
    return new Response('{}', { status: 404 });
  };
  return calls;
}
const req = (body, headers = {}) => new Request('https://x.vercel.app/api/request', { method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: JSON.stringify(body) });

test('접수하면 이슈를 만들고 번호를 돌려준다 (토큰·라벨·JSON 블록)', async () => {
  const calls = mockGitHub();
  const res = await POST(req(good()));
  assert.equal(res.status, 201);
  assert.equal((await res.json()).number, 7);
  const post = calls.find(c => c.init.method === 'POST');
  assert.equal(post.init.headers.Authorization, 'Bearer test-token');
  const sent = JSON.parse(post.init.body);
  assert.equal(sent.title, '[여행지 요청] 다낭');
  assert.deepEqual(sent.labels, ['trip-request']);
  assert.match(sent.body, /```json[\s\S]*"mapUrl": "https:\/\/maps\.app\.goo\.gl\/abc123"[\s\S]*```/);
});

test('이미 접수된·이미 게시된 여행지는 409', async () => {
  mockGitHub({ open: [{ number: 3, title: '[여행지 요청] 다 낭', labels: [{ name: 'trip-request' }], created_at: new Date().toISOString() }] });
  assert.equal((await POST(req(good()))).status, 409);
  mockGitHub();
  const b = good(); b.destination = 'phu quoc';
  assert.equal((await POST(req(b))).status, 409);
});

test('대기 요청이 많거나 10분 안에 3건이면 429', async () => {
  const mk = n => Array.from({ length: n }, (_, i) => ({ number: i + 1, title: '[여행지 요청] 곳' + i, labels: [], created_at: new Date().toISOString() }));
  mockGitHub({ open: mk(10) });
  assert.equal((await POST(req(good()))).status, 429);
  mockGitHub({ recent: mk(3) });
  assert.equal((await POST(req(good()))).status, 429);
});

test('다른 사이트에서 온 요청·JSON 아닌 요청·토큰 없음 거절', async () => {
  mockGitHub();
  assert.equal((await POST(req(good(), { origin: 'https://evil.example' }))).status, 403);
  assert.equal((await POST(new Request('https://x.vercel.app/api/request', { method: 'POST', headers: { 'content-type': 'text/plain' }, body: 'x' }))).status, 415);
  const saved = process.env.GITHUB_TOKEN; delete process.env.GITHUB_TOKEN;
  assert.equal((await POST(req(good()))).status, 503);
  const list = await (await GET()).json();
  assert.equal(list.configured, false);
  process.env.GITHUB_TOKEN = saved;
});

test('GET 목록은 번호·여행지·상태·접수일만 돌려준다', async () => {
  mockGitHub({ open: [
    { number: 1, title: '[여행지 요청] 다낭', body: 'SECRET', user: { login: 'x' }, labels: [{ name: 'trip-request' }], created_at: '2026-11-07T00:00:00Z' },
    { number: 2, title: '[여행지 요청] 방콕', labels: [{ name: 'trip-request' }, { name: '승인' }], created_at: '2026-11-07T01:00:00Z' },
    { number: 3, title: '[여행지 요청] 세부', labels: [{ name: 'trip-request' }, { name: '수집중' }], created_at: '2026-11-07T02:00:00Z' },
    { number: 4, title: '[여행지 요청] PR', pull_request: {}, labels: [], created_at: '2026-11-07T02:00:00Z' },
  ] });
  const j = await (await GET()).json();
  assert.deepEqual(j.requests.map(r => [r.destination, r.status]), [['다낭', 'pending'], ['방콕', 'approved'], ['세부', 'collecting']]);
  assert.ok(!JSON.stringify(j).includes('SECRET'));
});
