// 서버에서 장소 ID를 구글에 한 번 더 조회해 브라우저가 보낸 좌표가 맞는지 확인한다(선택 기능).
// 환경변수 GOOGLE_MAPS_SERVER_KEY(Places API (New) 전용 키, 사이트 주소 제한 없이 API 제한만)가 있을 때만 동작한다.
const TOL = 0.002;   // 약 200m

export const verifyEnabled = () => Boolean(process.env.GOOGLE_MAPS_SERVER_KEY);

// 반환: true(일치) / false(불일치·없는 장소) / null(확인하지 못함 → 막지 않음)
export async function verifyPlace(h) {
  try {
    const res = await fetch(`https://places.googleapis.com/v1/places/${encodeURIComponent(h.placeId)}`, {
      headers: { 'X-Goog-Api-Key': process.env.GOOGLE_MAPS_SERVER_KEY, 'X-Goog-FieldMask': 'location' },
    });
    if (res.status === 404 || res.status === 400) return false;
    if (!res.ok) return null;
    const { location } = await res.json();
    if (!location) return null;
    return Math.abs(location.latitude - h.lat) <= TOL && Math.abs(location.longitude - h.lng) <= TOL;
  } catch { return null; }
}
