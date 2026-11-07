// 여행지 추가 요청 폼의 입력 검사·정리. 서버 함수(api/request.js)와 테스트에서 쓴다.
// 이슈에는 사용자가 입력한 글이 그대로 들어가므로, 허용 문자를 좁게 잡고 줄바꿈·백틱·꺾쇠는 지운다.

export const MAX_HOTELS = 3;
export const MAX_NEW_CATS = 2;
export const COMPANIONS = ['혼자', '커플', '친구', '아이 동반', '부모님'];
const BASE_CATS = ['마사지', '맛집', '가볼만한곳'];
const MAP_HOSTS = new Set(['maps.app.goo.gl', 'goo.gl', 'google.com', 'www.google.com', 'maps.google.com', 'google.co.kr', 'www.google.co.kr']);

const DEST_RE = /^[\p{L}\p{N}][\p{L}\p{N} ·&'’().-]{0,29}$/u;
const CAT_RE = /^[\p{L}\p{N}][\p{L}\p{N} ·&-]{0,11}$/u;

export const clean = (s, max) => String(s ?? '').replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/[`<>]/g, '').replace(/\s+/g, ' ').trim().slice(0, max);
export const normName = s => String(s ?? '').toLowerCase().replace(/[\s\-_.,·()&'’"/]+/g, '');

function mapUrl(raw) {
  let u;
  try { u = new URL(String(raw ?? '').trim()); } catch { return null; }
  if (u.protocol !== 'https:' || !MAP_HOSTS.has(u.hostname)) return null;
  if (u.hostname === 'goo.gl' && !u.pathname.startsWith('/maps')) return null;
  if (/google\./.test(u.hostname) && !u.pathname.startsWith('/maps')) return null;
  return u.toString().slice(0, 500);
}

// 반환: { ok: true, value } 또는 { ok: false, error }
export function validateRequest(body, now = new Date()) {
  if (!body || typeof body !== 'object') return { ok: false, error: '요청 형식이 올바르지 않아요.' };
  if (body.website) return { ok: false, error: '요청 형식이 올바르지 않아요.' };   // 봇이 채우는 숨김 칸

  const destination = clean(body.destination, 30);
  if (!DEST_RE.test(destination)) return { ok: false, error: '여행지 이름은 글자·숫자 위주로 30자 이내로 적어 주세요.' };

  const rawHotels = Array.isArray(body.hotels) ? body.hotels.slice(0, MAX_HOTELS + 1) : [];
  if (rawHotels.length < 1) return { ok: false, error: '숙소를 1곳 이상 입력해 주세요.' };
  if (rawHotels.length > MAX_HOTELS) return { ok: false, error: `숙소는 최대 ${MAX_HOTELS}곳까지 받아요.` };
  const hotels = [];
  for (const [i, h] of rawHotels.entries()) {
    const n = i + 1;
    const name = clean(h?.name, 60), address = clean(h?.address, 150), short = clean(h?.short, 8), url = mapUrl(h?.mapUrl);
    if (name.length < 2) return { ok: false, error: `숙소 ${n}: 이름을 입력해 주세요.` };
    if (address.length < 5) return { ok: false, error: `숙소 ${n}: 주소를 입력해 주세요.` };
    if (!url) return { ok: false, error: `숙소 ${n}: 구글맵 링크(https://maps.app.goo.gl/… 또는 google.com/maps…)를 붙여넣어 주세요.` };
    hotels.push({ name, short, address, mapUrl: url });
  }

  const companions = [...new Set(Array.isArray(body.companions) ? body.companions : [])].filter(c => COMPANIONS.includes(c));

  let season = '';
  if (body.season) {
    const m = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(String(body.season).trim());
    const y = now.getFullYear();
    if (!m || +m[1] < y - 1 || +m[1] > y + 3) return { ok: false, error: '여행 시기는 2026-12 같은 형식으로 적어 주세요.' };
    season = m[0];
  }

  const interests = [];
  for (const raw of Array.isArray(body.interests) ? body.interests : []) {
    const c = clean(raw, 12);
    if (!c) continue;
    if (!CAT_RE.test(c)) return { ok: false, error: `관심 분야 "${c}"는 글자·숫자 12자 이내로 적어 주세요.` };
    if (BASE_CATS.includes(normName(c)) || interests.some(x => normName(x) === normName(c))) continue;   // 기본 분야·중복은 무시
    interests.push(c);
  }
  if (interests.length > MAX_NEW_CATS) return { ok: false, error: `새 분야는 최대 ${MAX_NEW_CATS}개까지 받아요.` };

  return { ok: true, value: { destination, hotels, companions, season, interests } };
}
