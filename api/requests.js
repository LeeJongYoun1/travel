// GET /api/requests — 열린 여행지 요청(대기·승인·수집 중)을 첫 화면에 보여주기 위한 목록.
import { configured, listOpen } from '../lib/github.js';

const json = (status, obj) => new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });

export async function GET() {
  if (!configured()) {
    // 토큰이 없을 때만 원인 찾기용 정보를 준다(변수 값은 절대 내보내지 않고, 이름·환경·커밋만).
    const env = process.env;
    return json(200, { configured: false, requests: [], diag: {
      vercelEnv: env.VERCEL_ENV || null, commit: (env.VERCEL_GIT_COMMIT_SHA || '').slice(0, 7) || null,
      tokenVarEmpty: 'GITHUB_TOKEN' in env && !env.GITHUB_TOKEN,
      similarNames: Object.keys(env).filter(k => /git|token|repo/i.test(k) && !k.startsWith('VERCEL_')).sort(),
    } });
  }
  try { return json(200, { configured: true, requests: await listOpen() }); }
  catch { return json(502, { configured: true, requests: [], error: '요청 목록을 불러오지 못했어요.' }); }
}
