/**
 * mdm-web-verify.mjs — nghiệm thu nội dung MDM đã lên web core mới.
 *
 * Đo thật 05/10/2026 (Filter): dữ liệu MDM lên core mới sau 4–15 phút, LAN DẦN TỪNG NODE
 * (cùng lúc node mới, node cũ). `?clearcache=1` KHÔNG có tác dụng với dữ liệu MDM trên core mới;
 * core cũ không hiện thay đổi MDM. Nên: ép cookie core mới, chỉ tính response không có header
 * x-version (core cũ có x-version Mwg-*), và đòi N mẫu core mới LIÊN TIẾP đều đúng.
 */

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36';

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };

export function decodeEntities(s) {
  return String(s)
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&([a-z]+);/gi, (m, n) => (n.toLowerCase() in ENTITIES ? ENTITIES[n.toLowerCase()] : m));
}

/** Gom khoảng trắng — chỉ dùng cho kiểm tra đoạn chữ trong thân trang (core mới dựng lại HTML infobox). */
export const squash = (s) => String(s).replace(/[\s ]+/g, ' ').trim();

export function extractTitle(html) {
  const m = String(html).match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return m ? decodeEntities(m[1]) : null;
}

export function extractMetaDescription(html) {
  const m = String(html).match(/<meta\s+name="description"\s+content="([^"]*)"/i);
  return m ? decodeEntities(m[1]) : null;
}

/** HTML → chữ thuần (bỏ script/style/thẻ), đã gom khoảng trắng. */
export function bodyText(html) {
  return squash(decodeEntities(String(html)
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')));
}

/**
 * Kiểm 1 trang theo kỳ vọng. Title/description so tuyệt đối (sau giải entity) vì MDM lưu y
 * nguyên byte; text so sau khi gom khoảng trắng vì core mới dựng lại infobox.
 */
export function checkPage(html, expect) {
  const got = {};
  const fails = [];
  if (expect.title != null) {
    got.title = extractTitle(html);
    if (got.title !== expect.title) fails.push('title');
  }
  if (expect.description != null) {
    got.description = extractMetaDescription(html);
    if (got.description !== expect.description) fails.push('description');
  }
  if (expect.text != null && !bodyText(html).includes(squash(expect.text))) fails.push('text');
  return { pass: fails.length === 0, fails, got };
}

export async function fetchCoreMoi(url, fetchFn = fetch) {
  // Từ 06/10/2026 cookie chọn core là webmoi_v3 (1 = cũ, 2 = mới); webmoi_v2 cũ cho core NGƯỢC.
  const res = await fetchFn(url, { headers: { 'User-Agent': UA, Cookie: 'webmoi_v3=2' }, redirect: 'manual' });
  const html = await res.text();
  const version = res.headers.get('x-version');
  const server = res.headers.get('x-app-server');
  // Có x-app-server thì tin nó (core mới = BE-webfe-tmdt-tgdd…); không có thì dựa x-version (core cũ có x-version Mwg-*).
  return { status: res.status, coreMoi: server ? /webfe/i.test(server) && !version : !version, version, server, html };
}

/**
 * Poll đến khi đủ `samples` mẫu core mới liên tiếp đều đạt, hoặc hết `maxMinutes`.
 * Mẫu core cũ (lạc node) bỏ qua, không làm đứt chuỗi; mẫu core mới sai làm đứt chuỗi.
 */
export async function pollUntil(url, expect, { samples = 4, intervalSec = 30, maxMinutes = 20, fetchFn = fetch, sleepFn, log = () => {} } = {}) {
  const sleep = sleepFn || ((ms) => new Promise((r) => setTimeout(r, ms)));
  const t0 = Date.now();
  let streak = 0;
  const history = [];
  while (Date.now() - t0 <= maxMinutes * 60000) {
    let r;
    try { r = await fetchCoreMoi(url, fetchFn); } catch (e) { r = { status: -1, error: String(e.message || e) }; }
    const sec = Math.round((Date.now() - t0) / 1000);
    if (r.status === 200 && r.coreMoi) {
      const c = checkPage(r.html, expect);
      streak = c.pass ? streak + 1 : 0;
      history.push({ sec, pass: c.pass, fails: c.fails, got: c.got });
      log(`+${sec}s core mới ${c.pass ? 'ĐẠT' : `chưa (${c.fails.join(',')})`} — chuỗi ${streak}/${samples}`);
      if (streak >= samples) return { verdict: 'PASS', seconds: sec, history };
    } else {
      history.push({ sec, status: r.status, coreMoi: r.coreMoi ?? null, skipped: true });
      log(`+${sec}s bỏ qua (status ${r.status}${r.version ? `, core cũ ${r.version}` : ''})`);
    }
    await sleep(intervalSec * 1000);
  }
  return { verdict: 'TIMEOUT', seconds: Math.round((Date.now() - t0) / 1000), history };
}
