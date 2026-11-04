/**
 * cms-bulk-insert-runner.js
 *
 * Chèn một câu (kèm internal link) vào cuối một đoạn <p> có sẵn trong mục
 * "Nội dung bài viết" của bài sản phẩm CMS, hàng loạt, an toàn.
 *
 * Chạy TRONG page context của tab CMS đã đăng nhập (cùng origin để dùng cookie):
 * chrome-devtools `evaluate_script`, hoặc browser `javascript_tool`.
 * KHÔNG nạp bài vào TinyMCE — đi qua UI editor làm TinyMCE format lại cả bài.
 *
 * Dùng:
 *   const r = await cmsBulkInsert({ rows: [...], dryRun: true });
 *
 * Trả về object JSON gồm `summary` (gọn) và `rows` (đầy đủ, có _before/_after
 * để agent ghi ra file backup). Runner KHÔNG tự ghi đĩa được — caller phải lưu.
 */

const CMS = {
  editPath: (site, pid) => `/v2/Product/Edit?site=${site}&productId=${pid}`,
  submitPath: '/v2/Product/Submit',
  formSelector: '#frmProductSubmit',
  contentSelector: '#txtContent',
  // Mục nào của bài được ghi. Sai giá trị này là ghi đè nhầm mục khác.
  hdType: { thongTinChung: 1, noiDungBaiViet: 2, seo: 4, tongQuan: 6 },
};

/**
 * Field chứa thân bài, theo site. Đo 25/09/2026 (370977, 370982):
 * - site 1/2: bài ở `txtContent` (v2) = `HTMLDescription` (trang cũ), byte-identical.
 * - site 16 TopZone: ĐẢO VAI — bài ở `HotReason`, còn `txtContent` chỉ là gallery
 *   [desktop]/[mobile] + "Nội dung quảng cáo". `HotReason` chỉ có ở trang cũ `/Product/Edit`.
 *
 * `txtContent` ghi qua `/v2/Product/Submit` + hdType=2 (AJAX, trả JSON).
 * `hotReason` ghi qua submit NGUYÊN form `#myForm` (multipart) tới `/Product/Edit` với nút
 * `UpdateHTML` — server phân mục bằng tên nút, không có hdType, trả trang HTML chứ không
 * phải JSON, nên thành công chỉ xác định bằng GET lại verify.
 */
const FIELDS = {
  txtContent: {
    editPath: CMS.editPath,
    contentSelector: CMS.contentSelector,
    contentName: 'txtContent',
    formSelector: CMS.formSelector,
    submit: 'v2',
  },
  hotReason: {
    editPath: (site, pid) => `/Product/Edit?productID=${pid}&site=${site}`,
    contentSelector: '#hotreason',
    contentName: 'HotReason',
    formSelector: '#myForm',
    submit: 'legacyHtml',
    submitPath: '/Product/Edit',
    // Nút "Lưu lại" của box "Bài viết mô tả TGDD/DMX/Topzone" — serializeForm bỏ submit nên phải tự thêm.
    submitButton: { name: 'UpdateHTML', value: 'Lưu lại' },
    // Checkbox "Lưu tất cả các site": tick là ghi đè bài sang site khác. Luôn gỡ khỏi payload.
    forbidden: ['SaveAllProductHTML'],
  },
};

const fieldSpec = (field = 'txtContent') => {
  const f = FIELDS[field];
  if (!f) throw new Error(`field "${field}" không hỗ trợ — chỉ ${Object.keys(FIELDS).join(' | ')}`);
  return f;
};

// 12 dòng/lô vượt protocolTimeout của Runtime.callFunctionOn. Timeout không ghi
// gì, nhưng đã mất một lần chẩn đoán thủ công để biết chắc điều đó.
const MAX_ROWS_PER_CALL = 10;

/* ---------- text helpers ---------- */

const decodeEntities = (s) => {
  const ta = document.createElement('textarea');
  ta.innerHTML = s;
  return ta.value;
};

const stripTags = (html) => html.replace(/<[^>]*>/g, '');

/** Chuẩn hoá để SO SÁNH. Không bao giờ dùng bản normalize này để ghi. */
const norm = (s) =>
  decodeEntities(String(s ?? ''))
    .replace(/ /g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const escAttr = (s) =>
  String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const escText = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const countOf = (haystack, needle) => haystack.split(needle).length - 1;

const tokenSet = (s) => new Set(norm(s).toLowerCase().split(' ').filter(Boolean));

const jaccard = (a, b) => {
  const A = tokenSet(a);
  const B = tokenSet(b);
  if (!A.size || !B.size) return 0;
  let inter = 0;
  for (const t of A) if (B.has(t)) inter++;
  return inter / (A.size + B.size - inter);
};

/* ---------- đọc CMS ---------- */

/**
 * GET trang edit, trả về { raw, doc }.
 * DOMParser ở đây chỉ để lấy textarea.value và serialize form — KHÔNG dùng để
 * re-serialize nội dung bài (innerHTML sẽ đổi U+00A0 thành &nbsp; hàng loạt).
 */
async function fetchEdit(site, pid, field = 'txtContent') {
  const f = fieldSpec(field);
  const res = await fetch(f.editPath(site, pid), { credentials: 'same-origin' });
  if (!res.ok) throw new Error(`GET edit ${pid} → HTTP ${res.status}`);
  const html = await res.text();
  const doc = new DOMParser().parseFromString(html, 'text/html');
  const ta = doc.querySelector(f.contentSelector);
  if (!ta) throw new Error(`không thấy ${f.contentSelector} (pid ${pid}) — có thể đã mất session`);
  return { raw: ta.value, doc };
}

/** jQuery.serializeArray() tương đương, trên document đã parse. */
function serializeForm(form) {
  const skipTypes = new Set(['submit', 'button', 'reset', 'image', 'file']);
  const out = [];
  for (const el of Array.from(form.elements || [])) {
    const name = el.name;
    if (!name || el.disabled) continue;
    const tag = el.tagName.toLowerCase();
    const type = (el.type || '').toLowerCase();
    if (tag === 'input' && skipTypes.has(type)) continue;
    if ((type === 'checkbox' || type === 'radio') && !el.checked) continue;
    if (tag === 'select') {
      for (const opt of Array.from(el.selectedOptions || [])) {
        out.push({ name, value: opt.value });
      }
      continue;
    }
    out.push({ name, value: el.value ?? '' });
  }
  return out;
}

/** Gộp mảng {name,value} của serializeForm() thành map name -> [values] (giữ multi-value). */
function fieldsToMap(fields) {
  const out = {};
  for (const f of fields) (out[f.name] ??= []).push(f.value);
  return out;
}

/**
 * So field TĨNH trước/sau khi ghi — mọi field khác ngoài whitelist đổi là dấu hiệu payload
 * đã ghi đè nhầm mục khác. Trả danh sách tên field bị đổi; rỗng = chỉ đúng field cho phép.
 */
function diffFields(beforeFields, afterFields, allowNames) {
  const b = fieldsToMap(beforeFields);
  const a = fieldsToMap(afterFields);
  const keys = new Set([...Object.keys(b), ...Object.keys(a)]);
  const changed = [];
  for (const k of keys) {
    if (allowNames.has(k)) continue;
    if (JSON.stringify(b[k] || []) !== JSON.stringify(a[k] || [])) changed.push(k);
  }
  return changed;
}

/* ---------- định vị ---------- */

/**
 * Quét các block <p>/<h1..h6> trên STRING THÔ, giữ nguyên chỉ số ký tự để splice.
 * Phải đi trên string thô: dựng lại HTML từ DOM làm lệch hàng chục dòng không
 * liên quan, và cột "Nội dung cũ" là plain text nên indexOf() trên HTML luôn -1.
 */
function scanBlocks(raw) {
  const re = /<(p|h[1-6])\b[^>]*>([\s\S]*?)<\/\1>/gi;
  const blocks = [];
  let m;
  while ((m = re.exec(raw)) !== null) {
    const tag = m[1].toLowerCase();
    const closeLen = `</${m[1]}>`.length;
    blocks.push({
      tag,
      inner: m[2],
      text: norm(stripTags(m[2])),
      insertAt: m.index + m[0].length - closeLen, // ngay trước thẻ đóng
    });
  }
  return blocks;
}

/**
 * Khớp BẰNG ĐÚNG cả đoạn, không phải "chứa". Đây là chốt chống chèn 2 lần:
 * dòng đã chèn rồi sẽ dài hơn cột "Nội dung cũ" → khớp 0 → tự skip.
 *
 * @param {string} sentence câu đã (có thể) được chèn ở lần chạy trước — dùng để
 *   phân biệt "đã chèn thật" với "oldText chỉ là câu đầu của 1 đoạn dài hơn".
 * @param {Array} [links] link kỳ vọng của lần chèn này — phân biệt "đã chèn ĐÚNG link"
 *   với "đã chèn nhưng href/anchor sai" (chạy lại sau khi sửa rows). Không truyền = bỏ
 *   qua kiểm href (giữ tương thích lời gọi cũ / test cũ).
 */
function locate(raw, oldText, sentence, links) {
  const target = norm(oldText);
  if (!target) return { ok: false, reason: 'cột Nội dung cũ rỗng' };

  const blocks = scanBlocks(raw);
  const hits = blocks.filter((b) => b.text === target);

  if (hits.length === 1 && hits[0].tag === 'p') return { ok: true, block: hits[0] };

  if (hits.length === 1) {
    // Khớp 100% nhưng là heading: rule content-html-optimizer cấm chèn internal
    // link từ <h3> trở xuống. Ca này cần user quyết, không phải lỗi kỹ thuật.
    return { ok: false, reason: `đoạn khớp nhưng là <${hits[0].tag}>, không phải <p>`, tag: hits[0].tag };
  }
  if (hits.length > 1) return { ok: false, reason: `match không duy nhất (${hits.length})` };

  // Đoạn dài hơn target, bắt đầu bằng target: 2 khả năng, phải phân biệt bằng
  // phần dư sau target — đừng dùng ngưỡng similarity ở đây (câu chèn làm tăng
  // gấp đôi token nên Jaccard chỉ còn ~0,5, dễ nhầm với "đoạn không tồn tại").
  // (a) ĐÃ CHÈN ở lần chạy trước — phần dư khớp đúng sentence đã khai.
  // (b) oldText chỉ là CÂU ĐẦU của 1 đoạn dài hơn chưa từng chèn gì — phần dư
  //     là câu gốc khác. Coi (b) là "đã chèn" (false ALREADY) làm CLI báo
  //     thành công giả trong khi thực ra không ghi gì.
  const candidate = blocks.find((b) => b.text.startsWith(target) && b.text.length > target.length);
  if (candidate) {
    const remainder = norm(candidate.text.slice(target.length));
    const expectSentence = norm(sentence || '');
    if (expectSentence && remainder.startsWith(expectSentence)) {
      // Phần dư khớp câu đã khai — nhưng lần chèn trước có thể đã dùng href/anchor SAI.
      // "Đã chèn" chỉ tính khi ĐỦ mọi link kỳ vọng có mặt (đúng href lẫn anchor) trong
      // raw HTML của đoạn — soi trên candidate.inner (HTML thô), không phải .text (đã strip tag).
      const linksOk = !Array.isArray(links) || links.every((l) => (
        candidate.inner.includes(`href="${escAttr(l.href)}"`) && candidate.inner.includes(`>${escText(l.anchor)}<`)
      ));
      if (linksOk) return { ok: false, reason: 'đoạn đã được chèn ở lần chạy trước', tag: candidate.tag, already: true };
      return { ok: false, reason: 'đã chèn nhưng link khác', tag: candidate.tag, alreadyMismatch: true };
    }
    return { ok: false, reason: 'oldText chỉ là phần đầu của đoạn — cần nguyên đoạn', tag: candidate.tag };
  }

  // Còn lại: phân biệt "sheet soạn từ nguồn khác" với lỗi normalize, bằng
  // similarity. Đừng gộp chung hai ca này khi báo cáo.
  const ranked = blocks
    .map((b) => ({ tag: b.tag, sim: +jaccard(target, b.text).toFixed(2), preview: b.text.slice(0, 120) }))
    .sort((a, b) => b.sim - a.sim)
    .slice(0, 3);
  return { ok: false, reason: 'match không duy nhất (0)', nearest: ranked };
}

/* ---------- dựng câu chèn ---------- */

/**
 * Bọc anchor DÀI TRƯỚC NGẮN SAU, qua placeholder, để `iPhone 18` không ăn vào
 * `iPhone 18 Pro Max`. Mỗi anchor phải xuất hiện đúng 1 lần trong câu.
 */
function wrapAnchors(sentence, links) {
  const sorted = [...links].sort((a, b) => b.anchor.length - a.anchor.length);
  const swaps = [];
  let out = escText(sentence);

  sorted.forEach((l, i) => {
    const anchor = escText(l.anchor);
    const first = out.indexOf(anchor);
    if (first === -1) throw new Error(`anchor không có trong câu chèn: "${l.anchor}"`);
    if (out.indexOf(anchor, first + anchor.length) !== -1) {
      throw new Error(`anchor xuất hiện >1 lần: "${l.anchor}"`);
    }
    const token = ` A${i} `;
    const title = escAttr(l.title || l.anchor);
    swaps.push([
      token,
      `<a title="${title}" href="${escAttr(l.href)}" target="_blank" rel="noopener">${anchor}</a>`,
    ]);
    out = out.slice(0, first) + token + out.slice(first + anchor.length);
  });

  for (const [token, html] of swaps) out = out.split(token).join(html);
  return out;
}

/* ---------- bất biến ---------- */

/**
 * 6 bất biến. Fail bất kỳ cái nào là BỎ DÒNG, không ghi. Không có rollback từ
 * CMS ("Lịch sử cập nhật" không lưu diff cho mục Bài viết), nên cổng này là
 * lớp bảo vệ duy nhất trước khi POST.
 */
function checkInvariants({ before, after, insert, nLinks, block, oldText, plainSentence, sep }) {
  const spliced = after.slice(0, block.insertAt) + after.slice(block.insertAt + insert.length);
  const afterBlocks = scanBlocks(after);
  const newText = afterBlocks.find((b) => b.insertAt === block.insertAt + insert.length)?.text;
  return {
    reversible: spliced === before,
    lenExact: after.length === before.length + insert.length,
    linkPlusN: countOf(after, '<a ') === countOf(before, '<a ') + nLinks,
    imgSame: countOf(after, '<img') === countOf(before, '<img'),
    pCountSame: countOf(after, '<p') === countOf(before, '<p'),
    textOk: newText === norm(`${oldText}${sep}${plainSentence}`),
  };
}

/* ---------- ghi ---------- */

const fieldValue = (fields, name) => fields.find((f) => f.name === name)?.value;

/**
 * Gửi thân bài mới theo đúng đường ghi của field. Trả { ok, sent, reason, response }.
 * `sent: false` = chặn trước khi gọi mạng (chắc chắn chưa ghi) → caller báo ABORT.
 */
async function postContent(fspec, fields, after, r) {
  if (fspec.submit === 'v2') {
    const body = new URLSearchParams();
    for (const f of fields) {
      if (f.name === fspec.contentName || f.name === 'hdType') continue;
      body.append(f.name, f.value);
    }
    body.set(fspec.contentName, after);
    body.set('hdType', String(CMS.hdType.noiDungBaiViet));
    const res = await fetch(CMS.submitPath, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: body.toString(),
    });
    const payload = await res.json().catch(() => null);
    const response = { ok: res.ok, e: payload };
    if (!res.ok || !payload || payload.status !== 1) {
      return { ok: false, sent: true, response, reason: `POST không thành công: ${JSON.stringify(payload)}` };
    }
    return { ok: true, sent: true, response };
  }

  // legacyHtml: form trang cũ mang ProductID/SiteID/LangID của chính trang đã đọc. Lệch là
  // payload sẽ ghi sang bài/site/ngôn ngữ khác — chặn trước khi gửi.
  const mismatch = [
    ['ProductID', String(r.pid)],
    ['SiteID', String(r.site)],
    ['LangID', 'vi-VN'],
  ].filter(([n, v]) => fieldValue(fields, n) !== v).map(([n, v]) => `${n}=${fieldValue(fields, n)} (cần ${v})`);
  if (mismatch.length) return { ok: false, sent: false, reason: `form trang cũ lệch: ${mismatch.join(', ')} — không ghi` };
  if (!fields.some((f) => f.name === fspec.contentName)) {
    return { ok: false, sent: false, reason: `form trang cũ không có field ${fspec.contentName} — không ghi` };
  }

  const body = new FormData();
  for (const f of fields) {
    if (f.name === fspec.contentName || fspec.forbidden.includes(f.name)) continue;
    body.append(f.name, f.value);
  }
  body.append(fspec.contentName, after);
  body.append(fspec.submitButton.name, fspec.submitButton.value);
  // Không tự đặt Content-Type: trình duyệt tự sinh multipart boundary.
  const res = await fetch(fspec.submitPath, { method: 'POST', credentials: 'same-origin', body });
  const response = { ok: res.ok, status: res.status, redirected: !!res.redirected };
  if (!res.ok) return { ok: false, sent: true, response, reason: `POST trang cũ HTTP ${res.status}` };
  // Server trả trang HTML (không phải JSON) — đúng/sai chỉ biết ở bước verify.
  return { ok: true, sent: true, response };
}

/* ---------- runner: mode insert-link (mặc định, hành vi cũ giữ nguyên byte-exact) ---------- */

/** 1 dòng mode insert-link — tách nguyên logic cũ ra hàm riêng, không đổi hành vi. */
async function processInsertLinkRow(r, dryRun, sep, keepHtml) {
  const field = r.field || 'txtContent';
  const rec = { row: r.row, pid: r.pid, site: r.site, field, name: r.name ?? null, steps: [], status: null, reason: null };
  const rt = Date.now();
  try {
    const fspec = fieldSpec(field);
    // 1. đọc + backup
    const first = await fetchEdit(r.site, r.pid, field);
    rec.steps.push('đọc');
    rec.backupLen = first.raw.length;
    if (keepHtml) rec._before = first.raw;

    // 2. định vị
    const hit = locate(first.raw, r.oldText, r.sentence, r.links);
    rec.matches = hit.ok ? 1 : 0;
    if (!hit.ok) {
      // Đã chèn nhưng link SAI (href/anchor khác lần khai báo hiện tại) — không được
      // coi là ALREADY (exit 0 im lặng để lại link sai). Trạng thái riêng, exit ≠ 0.
      rec.status = hit.alreadyMismatch ? 'ALREADY_MISMATCH' : 'SKIP';
      rec.reason = hit.reason;
      if (hit.nearest) rec.nearest = hit.nearest;
      if (hit.tag) rec.tag = hit.tag;
      if (hit.already) rec.already = true;
      if (hit.alreadyMismatch) rec.alreadyMismatch = true;
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('định vị');

    // 3 + 4. dựng câu, splice ngay trước </p>
    const insert = sep + wrapAnchors(r.sentence, r.links);
    const after = first.raw.slice(0, hit.block.insertAt) + insert + first.raw.slice(hit.block.insertAt);

    // 5. bất biến
    rec.inv = checkInvariants({
      before: first.raw,
      after,
      insert,
      nLinks: r.links.length,
      block: hit.block,
      oldText: r.oldText,
      plainSentence: r.sentence,
      sep,
    });
    const failed = Object.entries(rec.inv).filter(([, v]) => !v).map(([k]) => k);
    if (failed.length) {
      rec.status = 'SKIP';
      rec.reason = `bất biến fail: ${failed.join(', ')}`;
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('bất biến');

    if (dryRun) {
      rec.status = 'DRY';
      if (keepHtml) rec._after = after;
      rec.ms = Date.now() - rt;
      return rec;
    }

    // 6. re-GET sát trước POST — chống đè bài người đang sửa tay song song
    const fresh = await fetchEdit(r.site, r.pid, field);
    if (fresh.raw !== first.raw) {
      rec.status = 'SKIP';
      rec.reason = 'nội dung đổi giữa lúc đọc và lúc ghi — có người đang sửa';
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('re-check');

    // 7. POST, chỉ mục Nội dung bài viết
    const fields = serializeForm(fresh.doc.querySelector(fspec.formSelector));
    rec.payloadFields = fields.length;
    const posted = await postContent(fspec, fields, after, r);
    rec.response = posted.response;
    if (!posted.ok) {
      rec.status = posted.sent ? 'FAIL' : 'ABORT';
      rec.reason = posted.reason;
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('POST');

    // 8. verify byte-exact + KHÔNG field nào khác bị đổi (fields = trước ghi, xem bước 7).
    const saved = await fetchEdit(r.site, r.pid, field);
    const afterFields = serializeForm(saved.doc.querySelector(fspec.formSelector));
    // hdType luôn bị ép về noiDungBaiViet (2) — coi là field ĐƯỢC PHÉP đổi, không phải
    // ghi đè ngoài ý muốn; contentName là nội dung ta chủ đích ghi. Với hotReason, so trên
    // ~180 field của form trang cũ: HTMLDescription/SEO/thông số… đổi là FAIL.
    const fieldKhacBiDoi = diffFields(fields, afterFields, new Set([fspec.contentName, 'hdType']));
    rec.verify = {
      exactMatch: saved.raw === after,
      savedLen: saved.raw.length,
      expectLen: after.length,
      links: countOf(saved.raw, '<a '),
      imgs: countOf(saved.raw, '<img'),
      hasAnchors: r.links.every((l) => saved.raw.includes(l.href)),
      fieldKhacBiDoi,
    };
    if (keepHtml) rec._after = saved.raw;
    rec.status = rec.verify.exactMatch && rec.verify.hasAnchors && fieldKhacBiDoi.length === 0 ? 'DONE' : 'FAIL';
    if (rec.status === 'FAIL') {
      rec.reason = fieldKhacBiDoi.length
        ? `field khác bị đổi ngoài ý muốn: ${fieldKhacBiDoi.join(', ')} — dừng batch, kiểm tay`
        : 'verify sau ghi không khớp';
    }
  } catch (err) {
    rec.status = 'ERROR';
    rec.reason = String(err && err.message ? err.message : err);
  }
  rec.ms = Date.now() - rt;
  return rec;
}

/* ---------- runner: mode apply-ops ---------- */

/**
 * 1 dòng mode apply-ops. Dựa vào `buildContentOps`/`checkOpsInvariants`/`allOpsAlreadyApplied`/
 * `sha256Hex` của cms-content-ops-engine.js — file đó PHẢI được nối đứng trước file này trong
 * cùng 1 script (page context) hoặc import chung 1 scope (test); không import ESM ở đây.
 *
 * Khác mode insert-link ở đúng 3 chỗ: (a) guard sha256(live) === expectedBeforeSha256 TRƯỚC khi
 * định vị — bảo đảm nội dung chưa đổi so với lúc fact-check ops; (b) định vị bằng ops (nhiều vị
 * trí) thay vì 1 đoạn oldText; (c) 5 bất biến riêng (`checkOpsInvariants`) thay cho 6 bất biến
 * append-1-câu. Bước re-GET-trước-POST, POST, verify byte-exact + fieldKhacBiDoi TÁI DÙNG
 * nguyên `postContent`/`serializeForm`/`diffFields` của mode insert-link.
 */
async function processApplyOpsRow(r, dryRun, keepHtml) {
  const field = r.field;
  const rec = { row: r.row, pid: r.pid, site: r.site, field, name: r.name ?? null, steps: [], status: null, reason: null };
  const rt = Date.now();
  try {
    const fspec = fieldSpec(field);
    const first = await fetchEdit(r.site, r.pid, field);
    rec.steps.push('đọc');
    if (keepHtml) rec._before = first.raw;

    // Idempotence: mọi ops đã có mặt trong live (đã ghi ở lần chạy trước) → ALREADY, không
    // cần khớp expectedBeforeSha256 (live giờ là bản SAU, không phải bản trước fact-check).
    if (allOpsAlreadyApplied(first.raw, r.ops)) {
      rec.status = 'ALREADY';
      rec.reason = 'mọi ops đã được áp dụng ở lần chạy trước (đối chiếu find/new của từng op với live)';
      if (keepHtml) rec._after = first.raw;
      rec.ms = Date.now() - rt;
      return rec;
    }

    // Guard: nội dung fact-check (expectedBeforeSha256) phải khớp ĐÚNG live hiện tại —
    // bảo đảm không ai sửa bài giữa lúc fact-check ops và lúc chạy. Lệch là ABORT, không POST.
    const liveSha = await sha256Hex(first.raw);
    if (liveSha !== r.expectedBeforeSha256) {
      rec.status = 'ABORT';
      rec.reason = `sha256 live (${liveSha}) khác expectedBeforeSha256 (${r.expectedBeforeSha256}) — nội dung đã đổi giữa lúc fact-check và lúc chạy, không ghi`;
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('guard-sha');

    const built = buildContentOps(first.raw, r.ops);
    if (!built.ok) {
      rec.status = 'SKIP';
      rec.reason = built.reason;
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('build-ops');

    rec.inv = checkOpsInvariants({ before: first.raw, after: built.final, edits: built.edits, opsLength: r.ops.length });
    const failed = Object.entries(rec.inv).filter(([, v]) => !v).map(([k]) => k);
    if (failed.length) {
      rec.status = 'SKIP';
      rec.reason = `bất biến fail: ${failed.join(', ')}`;
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('bất biến');

    if (dryRun) {
      rec.status = 'DRY';
      if (keepHtml) rec._after = built.final;
      rec.ms = Date.now() - rt;
      return rec;
    }

    // re-GET sát trước POST — chống đè bài người đang sửa tay song song (cùng chốt an toàn
    // như mode insert-link, ĐỘC LẬP với guard sha256 phía trên vốn chỉ soát fact-check cũ).
    const fresh = await fetchEdit(r.site, r.pid, field);
    if (fresh.raw !== first.raw) {
      rec.status = 'SKIP';
      rec.reason = 'nội dung đổi giữa lúc đọc và lúc ghi — có người đang sửa';
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('re-check');

    const fields = serializeForm(fresh.doc.querySelector(fspec.formSelector));
    rec.payloadFields = fields.length;
    const posted = await postContent(fspec, fields, built.final, r);
    rec.response = posted.response;
    if (!posted.ok) {
      rec.status = posted.sent ? 'FAIL' : 'ABORT';
      rec.reason = posted.reason;
      rec.ms = Date.now() - rt;
      return rec;
    }
    rec.steps.push('POST');

    const saved = await fetchEdit(r.site, r.pid, field);
    const afterFields = serializeForm(saved.doc.querySelector(fspec.formSelector));
    const fieldKhacBiDoi = diffFields(fields, afterFields, new Set([fspec.contentName, 'hdType']));
    rec.verify = {
      exactMatch: saved.raw === built.final,
      savedLen: saved.raw.length,
      expectLen: built.final.length,
      fieldKhacBiDoi,
    };
    if (keepHtml) rec._after = saved.raw;
    rec.status = rec.verify.exactMatch && fieldKhacBiDoi.length === 0 ? 'DONE' : 'FAIL';
    if (rec.status === 'FAIL') {
      rec.reason = fieldKhacBiDoi.length
        ? `field khác bị đổi ngoài ý muốn: ${fieldKhacBiDoi.join(', ')} — dừng batch, kiểm tay`
        : 'verify sau ghi không khớp';
    }
  } catch (err) {
    rec.status = 'ERROR';
    rec.reason = String(err && err.message ? err.message : err);
  }
  rec.ms = Date.now() - rt;
  return rec;
}

/* ---------- runner ---------- */

/**
 * @param {Object}  opts
 * @param {Array}   opts.rows      mode insert-link: [{row, pid, site, oldText, sentence, links:[{anchor,href,title?}], name?, field?}] — field: txtContent (mặc định) | hotReason.
 *                                 mode apply-ops: [{row, pid, site, field, name?, expectedBeforeSha256, ops:[...]}] — field bắt buộc.
 * @param {boolean} [opts.dryRun]  true = chạy hết các bước kiểm, không POST
 * @param {string}  [opts.mode]    'insert-link' (mặc định, hành vi cũ) | 'apply-ops'
 * @param {string}  [opts.sep]     ngăn cách câu cũ và câu mới (chỉ mode insert-link), mặc định ' '
 * @param {boolean} [opts.keepHtml] true = giữ _before/_after trong kết quả (để backup)
 */
async function cmsBulkInsert({ rows, dryRun = false, mode = 'insert-link', sep = ' ', keepHtml = true }) {
  if (!Array.isArray(rows) || !rows.length) throw new Error('rows rỗng');
  if (rows.length > MAX_ROWS_PER_CALL) {
    throw new Error(`${rows.length} dòng vượt giới hạn ${MAX_ROWS_PER_CALL}/lô — chia nhỏ lô`);
  }
  if (mode !== 'insert-link' && mode !== 'apply-ops') {
    throw new Error(`mode "${mode}" không hỗ trợ — chỉ insert-link | apply-ops`);
  }

  const t0 = Date.now();
  const results = [];

  // Tuần tự, có chủ ý. Đo thật: 12 request ở conc 1/4/8 → 21,2s/20,7s/19,7s.
  // CMS serialize theo session, chạy song song chỉ phình latency từng request.
  for (const r of rows) {
    const rec = mode === 'apply-ops'
      ? await processApplyOpsRow(r, dryRun, keepHtml)
      : await processInsertLinkRow(r, dryRun, sep, keepHtml);
    results.push(rec);
  }

  return {
    totalMs: Date.now() - t0,
    dryRun,
    mode,
    summary: results.map((r) => ({ row: r.row, status: r.status, reason: r.reason, ms: r.ms ?? null })),
    rows: results,
  };
}

if (typeof window !== 'undefined') window.cmsBulkInsert = cmsBulkInsert;
