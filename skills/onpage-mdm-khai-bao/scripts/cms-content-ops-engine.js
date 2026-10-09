/**
 * cms-content-ops-engine.js — áp một danh sách "ops" (replace / after_p / before_h3 /
 * before_p / before_tr) lên HTML thô của bài sản phẩm, dùng cho mode `apply-ops` của
 * cms-bulk-insert-runner.js.
 *
 * Port JS của `flex()` / `find_one()` / `build()` trong một script Python nội bộ dựng Google Doc
 * highlight — GIỮ NGUYÊN thuật toán định vị/anchor (flex theo
 * entity, khớp đúng 1 lần, sort theo start, chặn chồng lấn); bỏ phần dựng `ranges` phục vụ
 * Google Doc highlight (không cần khi ghi CMS), thêm bookkeeping vị trí trong bản final để
 * bất biến `reversible` kiểm được.
 *
 * File THUẦN (không import/export ESM) để nạp được cả 2 nơi:
 *   - Node test: đọc file, bỏ dòng gán window ở cuối, `import(...)` qua data-url kèm
 *     `export {...}` (cùng thủ thuật `test-runner-logic.mjs` đang dùng).
 *   - Page context CMS: CLI nối chuỗi source file này ĐỨNG TRƯỚC cms-bulk-insert-runner.js
 *     rồi mới paste vào `evaluate_script` — cùng scope top-level nên runner gọi thẳng các
 *     hàm ở đây, không cần import.
 *
 * Không dùng DOM (khác `decodeEntities` trong runner, vốn dùng <textarea> để CHỈ so sánh
 * — norm() — không bao giờ dùng để ghi). Ở đây quyết định match/no-match nên phải chạy
 * được ngoài browser (Node test, không có `document`).
 */

/* ---------- flex match theo entity (faithful port của flex()/find_one() Python) ---------- */

const escapeRegExpChar = (ch) => ch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/**
 * Regex khớp chuỗi thô: mỗi ký tự ASCII giữ nguyên; mỗi ký tự non-ASCII có thể là
 * chính nó, một entity tên (`&tên;`), hoặc một entity số thập phân (`&#123;`).
 * Y hệt `flex()` Python — không thêm nhánh hex (`&#x..;`) vì bản gốc không có.
 */
function flexPattern(text) {
  let out = '';
  for (const ch of Array.from(text)) {
    if (ch.codePointAt(0) < 128) out += escapeRegExpChar(ch);
    else out += `(?:${escapeRegExpChar(ch)}|&[a-zA-Z]+;|&#\\d+;)`;
  }
  return out;
}

/**
 * Bảng entity tên tối thiểu để giải mã lại 1 match trước khi so với text gốc —
 * KHÔNG đầy đủ như bảng HTML5 (~2000 tên) của Python `html.unescape`, nhưng đủ cho các
 * entity thực tế gặp trong bài CMS (dấu câu/ký hiệu kỹ thuật). Tên lạ không có trong
 * bảng thì giữ nguyên chuỗi entity (giống hành vi mặc định của `html.unescape`).
 */
const NAMED_ENTITIES = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ',
  hellip: '…', ndash: '–', mdash: '—',
  lsquo: '‘', rsquo: '’', ldquo: '“', rdquo: '”',
  trade: '™', copy: '©', reg: '®', deg: '°',
  times: '×', divide: '÷', plusmn: '±',
  frac12: '½', frac14: '¼', frac34: '¾',
  micro: 'µ', sect: '§', para: '¶', bull: '•',
  dagger: '†', Dagger: '‡', permil: '‰',
  euro: '€', pound: '£', yen: '¥', cent: '¢',
  laquo: '«', raquo: '»', sup1: '¹', sup2: '²', sup3: '³',
};

/** Giải mã numeric refs (thập phân + hex) + bảng entity tên tối thiểu. Fallback: giữ nguyên. */
function decodeHtmlEntities(s) {
  return String(s)
    .replace(/&#x([0-9a-fA-F]+);/g, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
    .replace(/&([a-zA-Z]+);/g, (m, name) => (name in NAMED_ENTITIES ? NAMED_ENTITIES[name] : (name.toLowerCase() in NAMED_ENTITIES ? NAMED_ENTITIES[name.toLowerCase()] : m)));
}

/**
 * Tìm CHÍNH XÁC 1 lần khớp của `text` trong `raw` (flex theo entity, giải mã rồi so
 * đúng bằng). Trả `{ ok, count, start, end, reason }` — `count` luôn có để phân biệt
 * "0 lần" (có thể đã bị thay/xoá ở lần chạy trước) với "≥2 lần" (mơ hồ).
 */
function findOne(raw, text) {
  if (!text) return { ok: false, count: 0, reason: 'anchor/find rỗng' };
  const re = new RegExp(flexPattern(text), 'g');
  let count = 0;
  let start = -1;
  let end = -1;
  let m;
  while ((m = re.exec(raw)) !== null) {
    if (decodeHtmlEntities(m[0]) === text) {
      count++;
      start = m.index;
      end = m.index + m[0].length;
    }
    if (m[0].length === 0) re.lastIndex++;
  }
  if (count !== 1) {
    return { ok: false, count, reason: `anchor khớp ${count} lần (cần đúng 1): ${text.slice(0, 60)}` };
  }
  return { ok: true, count, start, end };
}

/* ---------- dựng 1 edit theo từng loại op ---------- */

const BEFORE_TAG_OF = { before_h3: 'h3', before_p: 'p', before_tr: 'tr' };

/** Trả `{ ok:true, edit:{start,end,new,id} }` hoặc `{ ok:false, reason }` — không bao giờ ném lỗi cho ca dữ liệu xấu (SKIP, không phải crash). */
function resolveOp(raw, op) {
  const id = op && op.id != null ? op.id : '?';
  if (!op || typeof op.type !== 'string') return { ok: false, reason: `op ${id}: thiếu type` };

  if (op.type === 'replace') {
    if (typeof op.find !== 'string' || typeof op.new !== 'string') return { ok: false, reason: `op ${id}: replace thiếu find/new` };
    const m = findOne(raw, op.find);
    if (!m.ok) return { ok: false, reason: `op ${id} (replace): ${m.reason}` };
    return { ok: true, edit: { start: m.start, end: m.end, new: op.new, id } };
  }

  if (op.type === 'after_p') {
    if (typeof op.anchor !== 'string' || typeof op.new !== 'string') return { ok: false, reason: `op ${id}: after_p thiếu anchor/new` };
    const m = findOne(raw, op.anchor);
    if (!m.ok) return { ok: false, reason: `op ${id} (after_p): ${m.reason}` };
    const closeIdx = raw.indexOf('</p>', m.end);
    if (closeIdx === -1) return { ok: false, reason: `op ${id} (after_p): không thấy </p> sau anchor` };
    const e = closeIdx + 4;
    return { ok: true, edit: { start: e, end: e, new: '\n' + op.new, id } };
  }

  if (op.type in BEFORE_TAG_OF) {
    if (typeof op.anchor !== 'string' || typeof op.new !== 'string') return { ok: false, reason: `op ${id}: ${op.type} thiếu anchor/new` };
    const m = findOne(raw, op.anchor);
    if (!m.ok) return { ok: false, reason: `op ${id} (${op.type}): ${m.reason}` };
    const tag = BEFORE_TAG_OF[op.type];
    const s = raw.lastIndexOf(`<${tag}`, m.start);
    if (s === -1) return { ok: false, reason: `op ${id} (${op.type}): không thấy <${tag} đứng trước anchor` };
    return { ok: true, edit: { start: s, end: s, new: op.new, id } };
  }

  return { ok: false, reason: `op ${id}: type lạ "${op.type}"` };
}

/**
 * Áp toàn bộ ops lên `raw`. Trả:
 *   { ok:true, final, edits:[{start,end,new,id,finalStart,finalEnd}] }  — edits giữ cả vị trí
 *     trong `raw` (để tra) lẫn trong `final` (để bất biến `reversible` gỡ lại đúng chỗ).
 *   { ok:false, reason }  — bất kỳ op nào không định vị được, hoặc 2 op chồng lấn.
 * Không ném lỗi cho ca dữ liệu xấu (khác `build-doc-bo-sung-highlight.py` dùng `sys.exit`
 * vì đó là script chạy tay 1 lần) — ở đây là SKIP có lý do, để pipeline ghi log tiếp lô.
 */
function buildContentOps(raw, ops) {
  if (!Array.isArray(ops) || !ops.length) return { ok: false, reason: 'ops rỗng' };
  const resolved = [];
  for (const op of ops) {
    const r = resolveOp(raw, op);
    if (!r.ok) return { ok: false, reason: r.reason };
    resolved.push(r.edit);
  }
  resolved.sort((a, b) => a.start - b.start || a.end - b.end);
  for (let i = 1; i < resolved.length; i++) {
    if (resolved[i - 1].end > resolved[i].start) {
      return { ok: false, reason: `op chồng nhau: ${resolved[i - 1].id} và ${resolved[i].id}` };
    }
  }
  let out = '';
  let pos = 0;
  const edits = [];
  for (const e of resolved) {
    out += raw.slice(pos, e.start);
    const finalStart = out.length;
    out += e.new;
    // origText = đoạn thô bị THAY (rỗng với after_p/before_* vì start===end — chỉ chèn,
    // không thay gì). Cần để `reversible` phục hồi ĐÚNG bản gốc (không phải xoá trắng).
    edits.push({ ...e, origText: raw.slice(e.start, e.end), finalStart, finalEnd: finalStart + e.new.length });
    pos = e.end;
  }
  out += raw.slice(pos);
  return { ok: true, final: out, edits };
}

/* ---------- bất biến riêng của apply-ops ---------- */

const A_TAG_RE = /<a\b[^>]*>/gi;
const IMG_TAG_RE = /<img\b[^>]*>/gi;

function tagMultiset(html, re) {
  const map = new Map();
  const r = new RegExp(re.source, re.flags);
  let m;
  while ((m = r.exec(html)) !== null) {
    map.set(m[0], (map.get(m[0]) || 0) + 1);
    if (m[0].length === 0) r.lastIndex++;
  }
  return map;
}

/** Mọi thẻ mở gốc (chuỗi y hệt) phải còn mặt trong `after` với số lần ≥ ở `before`. */
function tagsKept(before, after, re) {
  const b = tagMultiset(before, re);
  const a = tagMultiset(after, re);
  for (const [tag, n] of b) {
    if ((a.get(tag) || 0) < n) return false;
  }
  return true;
}

/**
 * Gỡ ĐÚNG các edit khỏi `after`: mỗi vùng `[finalStart, finalEnd)` (nội dung mới) được
 * THAY LẠI bằng `origText` (nội dung cũ tại đúng chỗ đó — rỗng với op chỉ chèn, chuỗi
 * `find` cũ với op replace) — không phải xoá trắng, nếu không "reversible" luôn fail
 * với op `replace` (undo của replace là trả lại `find`, không phải xoá `new`).
 * Xử lý theo thứ tự finalStart giảm dần để offset các vùng còn lại không bị lệch.
 */
function reverseApplyEdits(after, edits) {
  let s = after;
  const sorted = [...edits].sort((a, b) => b.finalStart - a.finalStart);
  for (const e of sorted) s = s.slice(0, e.finalStart) + e.origText + s.slice(e.finalEnd);
  return s;
}

/**
 * 5 bất biến của apply-ops: `reversible`, `oldLinksKept`, `oldImgsKept`, `changed`,
 * `opsAllApplied`. Fail bất kỳ cái nào là SKIP, không ghi.
 */
function checkOpsInvariants({ before, after, edits, opsLength }) {
  return {
    reversible: reverseApplyEdits(after, edits) === before,
    oldLinksKept: tagsKept(before, after, A_TAG_RE),
    oldImgsKept: tagsKept(before, after, IMG_TAG_RE),
    changed: after !== before,
    opsAllApplied: edits.length === opsLength,
  };
}

/* ---------- idempotence: ops đã được áp ở lần chạy trước ---------- */

/**
 * Đoán 1 op đã được áp vào `raw` HAY CHƯA, dựa trên chính nội dung của op — không có
 * "expectedAfterSha256" nào được khai trong rows.json để so trực tiếp (spec chỉ có
 * expectedBeforeSha256), nên đây là suy luận theo từng loại op:
 *   - replace: coi là "đã áp" khi `new` có mặt đúng 1 lần VÀ `find` đã biến mất (0 lần)
 *     — vì find/new luôn khác nhau nên không thể cả hai cùng đúng nếu chưa từng ghi.
 *   - after_p/before_*: coi là "đã áp" khi thân của `new` (bỏ newline dẫn đầu) đã có mặt
 *     nguyên văn (substring thô, không flex — vì chính CLI này ghi ra byte-exact) trong raw.
 * Hạn chế đã biết: chỉ coi TOÀN BỘ ops "đã áp" khi TẤT CẢ ops đều khớp kiểu trên; ca áp
 * dở dang (1 phần ops đã ghi, phần khác chưa) rơi về nhánh guard-sha/build bình thường,
 * không tự nhận ALREEADY.
 */
function opLooksAlreadyApplied(raw, op) {
  if (!op || typeof op.type !== 'string' || typeof op.new !== 'string') return false;
  if (op.type === 'replace') {
    if (typeof op.find !== 'string') return false;
    const newHit = findOne(raw, op.new);
    const findHit = findOne(raw, op.find);
    return newHit.ok && findHit.count === 0;
  }
  const body = op.new.replace(/^\n+/, '');
  return body.length > 0 && raw.includes(body);
}

function allOpsAlreadyApplied(raw, ops) {
  return Array.isArray(ops) && ops.length > 0 && ops.every((op) => opLooksAlreadyApplied(raw, op));
}

/* ---------- sha256 dùng chung page context / Node (Web Crypto có ở cả 2) ---------- */

async function sha256Hex(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(String(s)));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

if (typeof window !== 'undefined') {
  window.flexPattern = flexPattern;
  window.findOne = findOne;
  window.buildContentOps = buildContentOps;
  window.checkOpsInvariants = checkOpsInvariants;
  window.allOpsAlreadyApplied = allOpsAlreadyApplied;
  window.sha256Hex = sha256Hex;
}
