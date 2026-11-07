// GET /api/config — 브라우저에서 구글 장소 검색을 쓰는 데 필요한 키(사이트 주소로 제한한 브라우저용 키)를 비밀번호 뒤에서 내려준다.
const json = obj => new Response(JSON.stringify(obj), { status: 200, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });

export async function GET() {
  return json({ placesKey: process.env.GOOGLE_MAPS_BROWSER_KEY || null });
}
