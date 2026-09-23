/**
 * cms-news-bulk-insert-runner.js
 *
 * Chèn một câu (kèm internal link) hoặc biên tập nội dung bài viết trong mục
 * Nội dung bài viết của bài Tin tức (News TGDĐ / Kinh nghiệm hay ĐMX / Tekzone TopZone) trên CMS MWG.
 *
 * CHẠY TRONG page context của tab CMS đã đăng nhập:
 * DevTools Console hoặc evaluate_script.
 * TUYỆT ĐỐI KHÔNG nạp bài qua UI TinyMCE editor (tránh re-format toàn bài).
 *
 * Dùng:
 *   const r = await cmsNewsBulkInsert({
 *     rows: [
 *       {
 *         row: 1,
 *         newsId: 1598548,
 *         siteId: 1, // 1 = TGDĐ, 2 = ĐMX, 16 = TopZone
 *         title: "iPhone 18 Series cọc kỷ lục",
 *         oldText: "<đoạn văn cũ nguyên gốc>",
 *         sentence: "<câu mới chứa từ khoá>",
 *         links: [
 *           { anchor: "iPhone 18 Pro", href: "https://www.thegioididong.com/dtdd/iphone-18-pro", title: "iPhone 18 Pro" },
 *           { anchor: "iPhone 18 series", href: "https://www.thegioididong.com/dtdd-apple-iphone-18-series", title: "iPhone 18 series" }
 *         ]
 *       }
 *     ],
 *     dryRun: true // luôn chạy dryRun trước
 *   });
 */

const CMS_NEWS = {
  editPath: (siteId, newsId) => `/v2/News/NewsEdit?newsId=${newsId}&siteId=${siteId || 1}`,
  submitPath: '/v2/News/SubmitNewsEdit',
  formSelectors: ['#submitEditNews', '#frmNewsEdit', '#frmNewsSubmit', '#frmNews', 'form'],
  contentSelectors: ['#contentNewsAva', 'textarea[name="contentNewsAva"]', '#txtContent', 'textarea[name="txtContent"]', '#Content', 'textarea'],
  maxRowsPerCall: 10,
};

/* ---------- text helpers ---------- */

const decodeEntities = (s) => {
  if (typeof document !== 'undefined' && document.createElement) {
    const ta = document.createElement('textarea');
    ta.innerHTML = s;
    return ta.value;
  }
  const ENT = { nbsp: ' ', amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" };
  return String(s || '')
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&([a-z]+);/gi, (m, n) => (n.toLowerCase() in ENT ? ENT[n.toLowerCase()] : m));
};

const stripTags = (html) => String(html || '').replace(/<[^>]*>/g, '');

/** Chuẩn hoá để SO SÁNH. Không bao giờ dùng bản normalize này để ghi. */
const norm = (s) =>
  decodeEntities(String(s ?? ''))
    .replace(/ /g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const escAttr = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const escText = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

const countOf = (haystack, needle) => String(haystack || '').split(needle).length - 1;

const tokenSet = (s) => new Set(norm(s).toLowerCase().split(' ').filter(Boolean));

const jaccard = (a, b) => {
  const A = tokenSet(a);
  const B = tokenSet(b);
  if (!A.size || !B.size) return 0;
  let inter = 0;
  for (const t of A) if (B.has(t)) inter++;
  return inter / (A.size + B.size - inter);
};

/* ---------- sticker taxonomy (chuyên mục / hình thức bài) ---------- */

/**
 * Đọc các list taxonomy mà CMS render SẴN ở server dưới dạng
 * <ul class="sticker newscategory"><li data-id="31" id="liCate_31">…</li></ul>.
 *
 * Vì sao phải đọc ở đây: checkbox `input[name='NewsCate']` trong cây chọn
 * LUÔN có checked=false, kể cả trên trang thật đã chạy đủ JS. Serialize form
 * sẽ không bao giờ lấy được chuyên mục. CMS gửi chúng qua các field gộp
 * `LstCategoryId` / `LstCategoryName` do JS tự tính từ chính sticker này.
 *
 * Bỏ qua bước này = submit không kèm chuyên mục = CMS bỏ tick toàn bộ.
 */
function readStickers(doc) {
  const pick = (cls) => {
    const ul = doc.querySelector(`ul.sticker.${cls}`);
    if (!ul) return [];
    return Array.from(ul.querySelectorAll('li')).map((li) => ({
      id: li.getAttribute('data-id') || String(li.id || '').replace(/^liCate_|^liPostFormat_/, ''),
      name: (li.textContent || '').trim(),
    })).filter((x) => x.id);
  };
  const cate = pick('newscategory');
  const pf = pick('newspostformat');
  return {
    cate,
    postFormat: pf,
    fields: {
      LstCategoryId: cate.map((c) => c.id).join(','),
      LstCategoryName: cate.map((c) => c.name).join(','),
      LstPostFormatId: pf.map((c) => c.id).join(','),
      LstPostFormatName: pf.map((c) => c.name).join(','),
    },
  };
}

/* ---------- đọc CMS News ---------- */

/**
 * GET trang edit bài tin tức, trả về { raw, doc, form, contentEl, submitUrl }.
 */
async function fetchNewsEdit(siteId, newsId) {
  const url = CMS_NEWS.editPath(siteId, newsId);
  const res = await fetch(url, { credentials: 'same-origin' });
  if (!res.ok) throw new Error(`GET newsEdit ${newsId} (site ${siteId}) → HTTP ${res.status}`);
  const html = await res.text();
  const doc = new DOMParser().parseFromString(html, 'text/html');

  // Tìm textarea chứa nội dung bài viết (#contentNewsAva)
  let contentEl = null;
  for (const sel of CMS_NEWS.contentSelectors) {
    const el = doc.querySelector(sel);
    if (el) {
      contentEl = el;
      break;
    }
  }

  if (!contentEl) {
    throw new Error(`không tìm thấy textarea nội dung (#contentNewsAva) cho newsId ${newsId} — có thể phiên đăng nhập đã hết hạn`);
  }

  // Tìm form submit (#submitEditNews)
  let form = null;
  for (const sel of CMS_NEWS.formSelectors) {
    const f = doc.querySelector(sel);
    if (f) {
      form = f;
      break;
    }
  }

  return {
    raw: contentEl.value ?? '',
    page: html, // full page HTML — CẦN cho backup, đừng vứt đi như bản cũ
    doc,
    form,
    stickers: readStickers(doc),
    contentName: contentEl.name || 'contentNewsAva',
    submitUrl: CMS_NEWS.submitPath,
  };
}

/** Serialize form elements tương đương jQuery.serializeArray() */
function serializeForm(form) {
  if (!form) return [];
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

/* ---------- định vị trên string thô ---------- */

/**
 * Quét các block <p>/<h1..h6> trên STRING THÔ, giữ nguyên vị trí ký tự để splice.
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
      insertAt: m.index + m[0].length - closeLen, // vị trí ngay trước thẻ đóng
    });
  }
  return blocks;
}

/**
 * Định vị đoạn văn cần chèn. Khớp BẰNG ĐÚNG toàn bộ text đoạn.
 */
function locate(raw, oldText) {
  const target = norm(oldText);
  if (!target) return { ok: false, reason: 'cột Nội dung cũ rỗng' };

  const blocks = scanBlocks(raw);
  const hits = blocks.filter((b) => b.text === target);

  if (hits.length === 1 && hits[0].tag === 'p') return { ok: true, block: hits[0] };

  if (hits.length === 1) {
    return { ok: false, reason: `đoạn khớp nhưng là <${hits[0].tag}>, không phải <p>`, tag: hits[0].tag };
  }
  if (hits.length > 1) return { ok: false, reason: `match không duy nhất (${hits.length} đoạn trùng)` };

  // Kiểm tra ca ĐÃ ĐƯỢC CHÈN ở lần chạy trước (tiền tố chuẩn)
  const already = blocks.find((b) => b.text.startsWith(target) && b.text.length > target.length);
  if (already) {
    return { ok: false, reason: 'đoạn đã được chèn ở lần chạy trước', tag: already.tag, already: true };
  }

  // Không khớp: tìm 3 đoạn gần nhất theo similarity để chẩn đoán
  const ranked = blocks
    .map((b) => ({ tag: b.tag, sim: +jaccard(target, b.text).toFixed(2), preview: b.text.slice(0, 120) }))
    .sort((a, b) => b.sim - a.sim)
    .slice(0, 3);
  return { ok: false, reason: 'match không duy nhất (0)', nearest: ranked };
}

/* ---------- dựng câu và anchor ---------- */

/**
 * Bọc anchor DÀI TRƯỚC NGẮN SAU, qua placeholder token, tránh link ngắn ăn vào link dài.
 */
function wrapAnchors(sentence, links) {
  if (!Array.isArray(links) || !links.length) return escText(sentence);
  const sorted = [...links].sort((a, b) => b.anchor.length - a.anchor.length);
  const swaps = [];
  let out = escText(sentence);

  sorted.forEach((l, i) => {
    const anchor = escText(l.anchor);
    const first = out.indexOf(anchor);
    if (first === -1) throw new Error(`anchor không có trong câu chèn: "${l.anchor}"`);
    if (out.indexOf(anchor, first + anchor.length) !== -1) {
      throw new Error(`anchor xuất hiện >1 lần trong câu: "${l.anchor}"`);
    }
    const token = `___NEWS_ANCHOR_${i}___`;
    const title = escAttr(l.title || l.anchor);
    swaps.push([
      token,
      `<a title="${title}" href="${escAttr(l.href)}" target="_blank" rel="noopener">${anchor}</a>`,
    ]);
    out = out.slice(0, first) + token + out.slice(first + anchor.length);
  });

  for (const [token, html] of swaps) {
    out = out.split(token).join(html);
  }
  return out;
}

/* ---------- kiểm tra 6 bất biến ---------- */

/**
 * 6 Bất biến an toàn tuyệt đối trước khi POST lên CMS.
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

/* ---------- hàm runner chính ---------- */

/**
 * @param {Object}  opts
 * @param {Array}   opts.rows      [{row, newsId, siteId, title?, oldText, sentence, links:[{anchor,href,title?}]}]
 * @param {boolean} [opts.dryRun]  true = chạy bước 1-5, không POST
 * @param {string}  [opts.sep]     phân cách câu cũ và mới, mặc định ' '
 * @param {boolean} [opts.keepHtml] giữ _before/_after trong kết quả để ghi backup
 */
async function cmsNewsBulkInsert({ rows, dryRun = false, sep = ' ', keepHtml = true }) {
  if (!Array.isArray(rows) || !rows.length) throw new Error('rows rỗng');
  if (rows.length > CMS_NEWS.maxRowsPerCall) {
    throw new Error(`${rows.length} dòng vượt giới hạn ${CMS_NEWS.maxRowsPerCall}/lô — hãy chia nhỏ lô`);
  }

  const t0 = Date.now();
  const results = [];

  for (const r of rows) {
    const siteId = r.siteId || r.site || 1;
    const newsId = r.newsId || r.id;
    const rec = {
      row: r.row,
      newsId,
      siteId,
      title: r.title ?? null,
      steps: [],
      status: null,
      reason: null,
    };
    const rt = Date.now();

    try {
      // 1. Đọc + backup
      const first = await fetchNewsEdit(siteId, newsId);
      rec.steps.push('đọc');
      rec.backupLen = first.raw.length;
      rec.cateBefore = first.stickers.fields.LstCategoryId;
      if (keepHtml) {
        rec._before = first.raw;
        rec._beforePage = first.page; // full page: chỗ DUY NHẤT còn giữ chuyên mục gốc
      }

      // 2. Định vị đoạn
      const hit = locate(first.raw, r.oldText);
      rec.matches = hit.ok ? 1 : 0;
      if (!hit.ok) {
        rec.status = 'SKIP';
        rec.reason = hit.reason;
        if (hit.nearest) rec.nearest = hit.nearest;
        if (hit.tag) rec.tag = hit.tag;
        if (hit.already) rec.already = true;
        results.push(rec);
        continue;
      }
      rec.steps.push('định vị');

      // 3 + 4. Dựng câu, splice ngay trước </p>
      const insert = sep + wrapAnchors(r.sentence, r.links);
      const after = first.raw.slice(0, hit.block.insertAt) + insert + first.raw.slice(hit.block.insertAt);

      // 5. Kiểm tra 6 bất biến
      rec.inv = checkInvariants({
        before: first.raw,
        after,
        insert,
        nLinks: (r.links || []).length,
        block: hit.block,
        oldText: r.oldText,
        plainSentence: r.sentence,
        sep,
      });
      const failed = Object.entries(rec.inv).filter(([, v]) => !v).map(([k]) => k);
      if (failed.length) {
        rec.status = 'SKIP';
        rec.reason = `bất biến fail: ${failed.join(', ')}`;
        results.push(rec);
        continue;
      }
      rec.steps.push('bất biến');

      if (dryRun) {
        rec.status = 'DRY';
        if (keepHtml) rec._after = after;
        results.push(rec);
        continue;
      }

      // 6. Re-GET sát trước POST để chống đè người sửa tay song song
      const fresh = await fetchNewsEdit(siteId, newsId);
      if (fresh.raw !== first.raw) {
        rec.status = 'SKIP';
        rec.reason = 'nội dung bài đã thay đổi giữa lúc đọc và lúc ghi — có thể có người đang sửa song song';
        results.push(rec);
        continue;
      }
      rec.steps.push('re-check');

      // 7. POST form submission lên News CMS (/v2/News/SubmitNewsEdit)
      const fields = serializeForm(fresh.form);
      const body = new URLSearchParams();
      for (const f of fields) {
        if (f.name === 'contentNewsAva' || f.name === 'ContentNews' || f.name === 'txtContent') continue;
        body.append(f.name, f.value);
      }
      // Ghi cả 2 field ContentNews & contentNewsAva để tương thích hoàn toàn
      body.set('ContentNews', after);
      body.set('contentNewsAva', after);

      // 7b. Bơm lại taxonomy. KHÔNG được bỏ: serializeForm không bao giờ lấy
      // được chuyên mục, thiếu field này là CMS bỏ tick sạch toàn bài.
      const tax = fresh.stickers;
      for (const [k, v] of Object.entries(tax.fields)) body.set(k, v);
      rec.taxonomy = { cate: tax.fields.LstCategoryId, postFormat: tax.fields.LstPostFormatId };

      // 7c. BẤT BIẾN 7 — taxonomy phải đi qua nguyên vẹn, lệch thì dừng, không POST.
      const taxBad = [];
      if (tax.cate.length && body.get('LstCategoryId') !== tax.fields.LstCategoryId) {
        taxBad.push('LstCategoryId không khớp sticker');
      }
      if (tax.cate.length && body.get('LstCategoryId').split(',').filter(Boolean).length !== tax.cate.length) {
        taxBad.push(`số chuyên mục lệch: gửi ${body.get('LstCategoryId')} / đọc được ${tax.cate.length}`);
      }
      if (tax.postFormat.length && body.get('LstPostFormatId').split(',').filter(Boolean).length !== tax.postFormat.length) {
        taxBad.push('số hình thức bài lệch');
      }
      if (taxBad.length) {
        rec.status = 'ABORT';
        rec.reason = `bất biến taxonomy fail: ${taxBad.join('; ')}`;
        results.push(rec);
        continue;
      }
      rec.payloadFields = fields.length;

      const submitUrl = fresh.submitUrl;
      const res = await fetch(submitUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: body.toString(),
      });

      const resText = await res.text();
      let resJson = null;
      try { resJson = JSON.parse(resText); } catch (_) {}

      rec.response = { ok: res.ok, status: res.status, json: resJson };
      if (!res.ok || (resJson && resJson.status <= 0)) {
        rec.status = 'FAIL';
        rec.reason = `POST trả về lỗi: ${resJson ? JSON.stringify(resJson) : ('HTTP ' + res.status)}`;
        results.push(rec);
        continue;
      }
      rec.steps.push('POST');

      // 8. Verify byte-exact và xác nhận link tồn tại
      const saved = await fetchNewsEdit(siteId, newsId);
      rec.verify = {
        exactMatch: saved.raw === after,
        savedLen: saved.raw.length,
        expectLen: after.length,
        links: countOf(saved.raw, '<a '),
        imgs: countOf(saved.raw, '<img'),
        hasAnchors: (r.links || []).every((l) => saved.raw.includes(l.href)),
        cateKept: saved.stickers.fields.LstCategoryId === first.stickers.fields.LstCategoryId,
        cateAfter: saved.stickers.fields.LstCategoryId,
      };
      if (keepHtml) rec._after = saved.raw;
      rec.status = rec.verify.exactMatch && rec.verify.hasAnchors && rec.verify.cateKept ? 'DONE' : 'FAIL';
      if (rec.status === 'FAIL') {
        rec.reason = !rec.verify.cateKept
          ? `MẤT CHUYÊN MỤC sau ghi: trước="${first.stickers.fields.LstCategoryId}" sau="${rec.verify.cateAfter}" — dừng batch, xử lý tay trước khi chạy tiếp`
          : 'verify sau ghi không khớp byte-exact hoặc thiếu anchor link';
      }
    } catch (err) {
      rec.status = 'ERROR';
      rec.reason = String(err && err.message ? err.message : err);
    }
    rec.ms = Date.now() - rt;
    results.push(rec);
  }

  return {
    totalMs: Date.now() - t0,
    dryRun,
    summary: results.map((r) => ({
      row: r.row,
      newsId: r.newsId,
      status: r.status,
      reason: r.reason,
      ms: r.ms ?? null,
    })),
    rows: results,
  };
}

if (typeof window !== 'undefined') {
  window.cmsNewsBulkInsert = cmsNewsBulkInsert;
  window.CMS_NEWS = CMS_NEWS;
}
