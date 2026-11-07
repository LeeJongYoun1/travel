// Vercel Routing Middleware: 사이트 전체를 간단한 비밀번호로 보호한다.
// 비밀번호는 Vercel 프로젝트 환경변수 SITE_PASSWORD 에 넣는다(저장소에 적지 않음).
// 로그인하면 30일 동안 쿠키로 기억한다. 비밀번호를 바꾸면 기존 로그인은 모두 풀린다.

export const config = { matcher: '/:path*' };

const COOKIE = 'tg_auth';
const LOGIN = '/__login';
const MAX_AGE = 60 * 60 * 24 * 30;

async function token(pw) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('travel-guide:' + pw));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function cookie(req, name) {
  const m = (req.headers.get('cookie') || '').match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'));
  return m ? m[1] : null;
}

function safeNext(v) {
  return typeof v === 'string' && v.startsWith('/') && !v.startsWith('//') && !v.includes('\\') ? v : '/';
}

const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function page(next, msg, status) {
  const html = `<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>여행 노트</title><style>
:root{--bg:#F2F6F5;--surface:#fff;--ink:#132E2C;--muted:#5B706D;--line:#D5E2DF;--accent:#0B7A75;--bad:#B3322B}
@media (prefers-color-scheme: dark){:root{--bg:#0E1A19;--surface:#152523;--ink:#E4EFED;--muted:#93AAA6;--line:#26403C;--accent:#4FC3BA;--bad:#F08A82}}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);
font-family:system-ui,-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;padding:16px}
form{width:100%;max-width:340px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:24px;display:grid;gap:12px}
h1{margin:0;font-size:22px}p{margin:0;color:var(--muted);font-size:14px}
input{font:inherit;font-size:16px;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink)}
button{font:inherit;font-weight:600;padding:12px;border:0;border-radius:10px;background:var(--accent);color:#fff;cursor:pointer}
.err{color:var(--bad)}</style></head><body>
<form method="post" action="${LOGIN}"><h1>여행 노트</h1><p>비밀번호를 입력하세요.</p>
${msg ? `<p class="err">${esc(msg)}</p>` : ''}
<input type="password" name="pw" autocomplete="current-password" autofocus required aria-label="비밀번호">
<input type="hidden" name="next" value="${esc(next)}"><button type="submit">들어가기</button></form></body></html>`;
  return new Response(html, { status, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex' } });
}

export default async function middleware(req) {
  const pw = process.env.SITE_PASSWORD;
  const url = new URL(req.url);
  if (!pw) return new Response('SITE_PASSWORD 환경변수가 설정되지 않았습니다.', { status: 503, headers: { 'content-type': 'text/plain; charset=utf-8' } });
  const good = await token(pw);

  if (url.pathname === LOGIN) {
    if (req.method !== 'POST') return page('/', '', 200);
    const f = await req.formData();
    const next = safeNext(f.get('next'));
    if ((await token(String(f.get('pw') || ''))) !== good) return page(next, '비밀번호가 맞지 않습니다.', 401);
    return new Response(null, { status: 303, headers: {
      location: next,
      'set-cookie': `${COOKIE}=${good}; Path=/; Max-Age=${MAX_AGE}; HttpOnly; Secure; SameSite=Lax`,
    } });
  }
  if (cookie(req, COOKIE) === good) return; // 통과: 정적 파일 그대로 제공
  return page(url.pathname + url.search, '', 401);
}
