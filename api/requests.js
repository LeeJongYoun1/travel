// GET /api/requests — 열린 여행지 요청(대기·승인·수집 중)을 첫 화면에 보여주기 위한 목록.
import { configured, listOpen } from '../lib/github.js';

const json = (status, obj) => new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });

export async function GET() {
  if (!configured()) return json(200, { configured: false, requests: [] });
  try { return json(200, { configured: true, requests: await listOpen() }); }
  catch { return json(502, { configured: true, requests: [], error: '요청 목록을 불러오지 못했어요.' }); }
}
