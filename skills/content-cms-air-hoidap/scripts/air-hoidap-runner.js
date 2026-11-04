/*
 * air-hoidap-runner.js — chạy TRONG page context của tab CMS Hỏi Đáp đã đăng nhập:
 *   https://cms.thegioididong.com/v2/Faq/NewsEdit?newsId={ID}
 *
 * Nạp bằng evaluate_script, rồi gọi:
 *   hdMakeInput('claudeHdImages')                        // tạo input[type=file] không name
 *   await hdUploadImages({ newsId, inputId })            // ảnh -> common/News/{newsId}/
 *   await hdWriteArticle({ newsId, html, set, dryRun })  // thân bài (+ title/meta nếu cần)
 *   await hdPublishArticle({ newsId, dryRun })           // Chờ duyệt -> Xuất bản (bài CLI tự tạo)
 *
 * Khác bài tin (/v2/News/): endpoint là /v2/Faq/SubmitNewsEdit, textarea là
 * #content_FaqNews, chuyên mục là 2 <select multiple> (không phải sticker), và
 * page JS tự gộp LstParentCategory / LstChildCategory (nối bằng dấu cách).
 *
 * Không bao giờ đọc/ghi cookie. Không in credential. dryRun mặc định = true.
 */

(() => {
  const FORM = '#submitEditNews';
  const BODY_ID = 'content_FaqNews';
  // Field được phép đổi qua tham số `set` — mọi field khác phải đi qua nguyên vẹn.
  const SETTABLE = { title: 'txtTitle', metaTitle: 'txtMetaTitle', metaDescription: 'txtMetaDescription' };
  // Ngưỡng mềm lấy theo News CMS (Faq CMS không validate client) — vượt thì ABORT.
  const SOFT_LIMIT = { txtTitle: 130, txtMetaTitle: 70, txtMetaDescription: 170 };

  const crlf = s => String(s).replace(/\r?\n/g, '\r\n');          // serializeArray đổi \n -> \r\n
  const lf = s => String(s).replace(/\r\n?/g, '\n');
  const ampNorm = s => lf(s).replace(/&amp;/g, '&');             // xem failure mode "&amp;"

  const staticDoc = async (newsId) => {
    const raw = await fetch(`/v2/Faq/NewsEdit?newsId=${newsId}&_=${Date.now()}`,
      { credentials: 'same-origin' }).then(r => r.text());
    const doc = new DOMParser().parseFromString(raw, 'text/html');
    if (!doc.getElementById(BODY_ID)) throw new Error('không thấy #content_FaqNews — mất session hoặc sai newsId');
    return { raw, doc };
  };

  // Tương đương GetAllFormData (serializeArray) nhưng chạy trên DOM tĩnh từ server.
  // Multi-select: GetAllFormData chỉ giữ GIÁ TRỊ CUỐI — giả lập đúng hành vi đó.
  const staticFields = (doc) => {
    const F = doc.querySelector(FORM);
    const out = {};
    for (const el of F.querySelectorAll('[name]')) {
      if (el.disabled || !el.name) continue;
      const t = (el.type || '').toLowerCase();
      if (t === 'file' || t === 'button' || t === 'submit') continue;
      if (el.tagName === 'SELECT') {
        const sel = [...el.querySelectorAll('option[selected]')];
        const picked = sel.length ? sel : (el.multiple ? [] : [el.options[0]].filter(Boolean));
        if (picked.length) out[el.name] = crlf(picked[picked.length - 1].getAttribute('value') ?? picked[picked.length - 1].textContent);
      } else if (t === 'checkbox' || t === 'radio') {
        if (el.hasAttribute('checked')) out[el.name] = crlf(el.getAttribute('value') ?? 'on');
      } else if (el.tagName === 'TEXTAREA') {
        out[el.name] = crlf(el.value);
      } else {
        out[el.name] = crlf(el.getAttribute('value') ?? '');
      }
    }
    return out;
  };

  const staticCates = (doc) => {
    const pick = id => [...doc.querySelectorAll(`#${id} option[selected]`)].map(o => o.value);
    return { parent: pick('lst_parentcate'), child: pick('lst_childcate') };
  };

  const liveCates = () => {
    const pick = id => [...(document.getElementById(id)?.selectedOptions || [])].map(o => o.value);
    return { parent: pick('lst_parentcate'), child: pick('lst_childcate') };
  };

  const filesOf = inputId => {
    const el = document.getElementById(inputId);
    if (!el) throw new Error(`không thấy input #${inputId} — gọi hdMakeInput trước`);
    if (!el.files || !el.files.length) throw new Error(`#${inputId} chưa có file (nạp bằng CDP upload_file)`);
    return [...el.files];
  };

  /* ---------- input nạp liệu ---------- */
  // KHÔNG dùng #allImagesNews thứ nhất (có change handler -> tự upload) hay
  // #fileUploadContentNews (có handler html5Uploader). Tạo input riêng, không name
  // => không lọt vào serializeArray, không có handler nào.
  window.hdMakeInput = (id = 'claudeHdImages') => {
    let el = document.getElementById(id);
    if (!el) {
      el = document.createElement('input');
      el.type = 'file'; el.multiple = true; el.id = id;
      el.style.cssText = 'position:fixed;top:0;left:0;z-index:99999';
      document.body.appendChild(el);
    }
    return { id, inForm: !!el.closest(FORM), hasName: !!el.name };
  };

  /* ---------- upload ảnh ---------- */
  // Mirror đúng UploadManyImages() của faq.js: FormData { ID, type: 3, file0..fileN }.
  // (Bản News gửi thêm `site`; bản Faq KHÔNG gửi — giữ nguyên như trang.)
  window.hdUploadImages = async ({ newsId, inputId = 'claudeHdImages', dryRun = true }) => {
    const pageId = document.getElementById('hdNewsId')?.value;
    if (String(pageId) !== String(newsId)) return { status: 'ABORT', reason: `tab đang mở newsId=${pageId}, tham số ${newsId}` };
    if (!newsId || String(newsId) === '0') return { status: 'ABORT', reason: 'newsId=0 -> ảnh rơi vào kho chung common/News/0/' };
    const files = filesOf(inputId);
    const tooBig = files.filter(f => f.size > 10485760).map(f => f.name);
    if (tooBig.length) return { status: 'ABORT', reason: 'file >10MB', tooBig };

    // Chốt trùng tên: CDN không xoá được, CMS từ chối ghi đè.
    const base = `https://cdnv2.tgdd.vn/mwg-static/common/News/${newsId}/`;
    const heads = await Promise.all(files.map(async f => {
      try { const r = await fetch(base + f.name, { method: 'HEAD', cache: 'no-store' }); return [f.name, r.status]; }
      catch (e) { return [f.name, 'ERR']; }
    }));
    const taken = heads.filter(([, s]) => s === 200).map(([n]) => n);
    if (dryRun) return { status: 'DRY', willUpload: files.map(f => ({ name: f.name, size: f.size })), cdnHead: Object.fromEntries(heads), taken };
    if (taken.length) return { status: 'ABORT', reason: 'tên file đã có trên CDN — đổi tên trước', taken };

    const fd = new FormData();
    fd.append('ID', String(newsId));
    fd.append('type', 3);
    files.forEach((f, i) => fd.append('file' + i, f, f.name));
    const t0 = Date.now();
    const res = await fetch('/v2/Common/UploadManyImages', { method: 'POST', body: fd, credentials: 'same-origin' });
    const text = await res.text();
    let asJson = null; try { asJson = JSON.parse(text); } catch (e) { /* thành công trả HTML fragment */ }
    if (asJson && asJson.status === -1) return { status: 'FAIL', error: asJson.error, ms: Date.now() - t0 };

    const urls = [...new Set(text.match(/https?:\/\/[^"'\s<>\\]+\.(?:jpg|jpeg|png|webp|gif)/gi) || [])];
    const uploaded = {};
    for (const f of files) { const hit = urls.find(u => u.endsWith('/' + f.name)); if (hit) uploaded[f.name] = hit; }
    const missing = files.map(f => f.name).filter(n => !uploaded[n]);
    return {
      status: missing.length ? 'PARTIAL' : 'DONE', ms: Date.now() - t0, uploaded, missing,
      wrongFolder: Object.values(uploaded).filter(u => !u.startsWith(base)),
      responseHead: missing.length ? text.slice(0, 400) : undefined,
    };
  };

  /* ---------- ghi bài ---------- */
  // Payload = đúng như SubmitNewsEdit() của faq.js:
  //   data = GetAllFormData('#submitEditNews');
  //   data.LstParentCategory = $('#lst_parentcate').val().join(' ');
  //   data.LstChildCategory  = $('#lst_childcate').val().join(' ');
  //   data.ContentNews = tinymce.get('content_FaqNews').getContent();   <- server ghi CÁI NÀY
  // Ta thay ContentNews (và content_FaqNews cho khớp) bằng HTML của mình, KHÔNG lấy từ TinyMCE.
  window.hdWriteArticle = async ({
    newsId, html = null, inputId = 'claudeHdHtml', set = {}, expectImages = null, dryRun = true,
  }) => {
    const pageId = document.getElementById('hdNewsId')?.value;
    if (String(pageId) !== String(newsId)) return { status: 'ABORT', reason: `tab đang mở newsId=${pageId}, tham số ${newsId}` };
    if (typeof GetAllFormData !== 'function' || typeof tinymce === 'undefined') return { status: 'ABORT', reason: 'sai trang — cần /v2/Faq/NewsEdit' };
    const body = html != null ? html : await filesOf(inputId)[0].text();
    if (!body || body.length < 500) return { status: 'ABORT', reason: 'nội dung mới quá ngắn, nghi nạp nhầm file' };

    const unknown = Object.keys(set).filter(k => !SETTABLE[k]);
    if (unknown.length) return { status: 'ABORT', reason: `set chỉ nhận ${Object.keys(SETTABLE).join('/')}`, unknown };

    const before = await staticDoc(newsId);
    const sFields = staticFields(before.doc);
    const sCates = staticCates(before.doc);
    const bodyBefore = before.doc.getElementById(BODY_ID).value;

    // Payload dựng giống hệt page, từ form live.
    const data = GetAllFormData(FORM);
    const lc = liveCates();
    data.LstParentCategory = lc.parent.join(' ');
    data.LstChildCategory = lc.child.join(' ');

    // Form live phải khớp server (không ai gõ dở trong tab, trang không cũ).
    const liveDrift = Object.keys({ ...sFields, ...data })
      .filter(k => !['LstParentCategory', 'LstChildCategory', BODY_ID].includes(k))
      .filter(k => crlf(data[k] ?? '<vắng>') !== crlf(sFields[k] ?? '<vắng>'));

    const changes = {};
    for (const [k, v] of Object.entries(set)) { changes[SETTABLE[k]] = { from: data[SETTABLE[k]], to: v }; data[SETTABLE[k]] = v; }
    data.ContentNews = body;
    data[BODY_ID] = body;

    const imgSrcs = [...body.matchAll(/<img\b[^>]*?\bsrc=["']([^"']+)["']/gi)].map(m => m[1]);
    const localSrc = imgSrcs.filter(s => !/^https?:\/\//i.test(s));
    const heads = await Promise.all([...new Set(imgSrcs.filter(s => /^https?:\/\//i.test(s)))].map(async u => {
      try { const r = await fetch(u, { method: 'HEAD', cache: 'no-store' }); return [u, r.status]; } catch (e) { return [u, 'ERR']; }
    }));
    const deadImg = heads.filter(([, s]) => s !== 200).map(([u, s]) => `${s} ${u}`);
    const overLimit = Object.entries(SOFT_LIMIT).filter(([k, n]) => (data[k] || '').length > n).map(([k, n]) => `${k} ${data[k].length}>${n}`);

    const checks = {
      dungBai: String(data.hdNewsId) === String(newsId),
      formKhopServer: liveDrift.length === 0,
      chuyenMucChaGiu: lc.parent.join(' ') === sCates.parent.join(' ') && sCates.parent.length > 0,
      chuyenMucConGiu: lc.child.join(' ') === sCates.child.join(' ') && sCates.child.length > 0,
      giuTrangThai: String(data.cboStatus) === String(sFields.hdCurrentStatus),
      giuUrl: data.txtUrl === sFields.txtUrl,
      contentNewsSet: data.ContentNews === body,
      khongConAnhLocal: localSrc.length === 0,
      anhSongHet: deadImg.length === 0,
      soAnhDungKyVong: expectImages == null || imgSrcs.length === expectImages,
      khongConAltRong: !/<img\b[^>]*\balt=["']\s*["']/i.test(body),
      trongNguongDoDai: overLimit.length === 0,
    };
    const failed = Object.entries(checks).filter(([, v]) => !v).map(([k]) => k);
    const backup = { newsId, at: new Date().toISOString(), content_FaqNews_DB: bodyBefore, fields: sFields, cates: sCates, fullPageHtml: before.raw };
    const info = { liveDrift, localSrc, deadImg, overLimit, changes,
      willWrite: { len: body.length, imgs: imgSrcs.length }, current: { len: bodyBefore.length, imgs: (bodyBefore.match(/<img/gi) || []).length },
      payloadKeys: Object.keys(data).length };
    if (failed.length) return { status: 'ABORT', reason: 'bất biến không đạt — KHÔNG POST', failed, checks, ...info, backup };

    // "Đã ghi rồi" (#7): thân bài DB đã khớp bản mới (sau chuẩn hoá) VÀ field trong `set` đã đúng giá
    // trị đích → không POST lại (agent chạy không người trông gọi lại --step all không tốn 1 lần ghi vô ích).
    if (!dryRun) {
      const bodyAlready = ampNorm(lf(bodyBefore)).trimEnd() === ampNorm(lf(body)).trimEnd();
      const setAlready = Object.entries(set).every(([k, v]) => crlf(v) === crlf(sFields[SETTABLE[k]] ?? ''));
      if (bodyAlready && setAlready) return { status: 'ALREADY', checks, ...info, backup };
    }
    if (dryRun) return { status: 'DRY', checks, ...info, backup };

    const skip = document.getElementById('hdIsSkipSecurity');
    const url = '/v2/Faq/SubmitNewsEdit' + (skip && skip.value === '1' ? '?skip=1' : '');
    const t0 = Date.now();
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' },
      body: jQuery.param(data), credentials: 'same-origin',
    });
    const ms = Date.now() - t0;
    const replyText = await res.text();
    let reply = null; try { reply = JSON.parse(replyText); } catch (e) {}

    // Nghiệm thu: đọc lại tĩnh. Thông báo "thành công" của CMS không chứng minh gì.
    const after = await staticDoc(newsId);
    const aFields = staticFields(after.doc);
    const aCates = staticCates(after.doc);
    const bodyAfter = after.doc.getElementById(BODY_ID).value;
    const expectFields = { ...sFields };
    for (const [k, c] of Object.entries(changes)) expectFields[k] = crlf(c.to);
    // hdCurrentName là bản sao server-render của txtTitle -> đổi title thì nó đổi theo.
    if (changes.txtTitle) expectFields.hdCurrentName = crlf(changes.txtTitle.to);
    const fieldKhacBiDoi = Object.keys({ ...expectFields, ...aFields })
      .filter(k => k !== BODY_ID && crlf(aFields[k] ?? '') !== crlf(expectFields[k] ?? ''));

    const verify = {
      byteExact: bodyAfter === body,
      lfEqual: lf(bodyAfter) === lf(body),
      ampNormEqual: ampNorm(bodyAfter) === ampNorm(body),
      // Đo 24/09/2026 (bài 1576257): server cắt khoảng trắng/xuống dòng cuối thân bài.
      trimEndEqual: ampNorm(lf(bodyAfter)).trimEnd() === ampNorm(lf(body)).trimEnd(),
      len: bodyAfter.length, imgs: (bodyAfter.match(/<img/gi) || []).length,
      fieldKhacBiDoi,
      chuyenMucGiu: JSON.stringify(aCates) === JSON.stringify(sCates),
      trangThaiGiu: aFields.hdCurrentStatus === sFields.hdCurrentStatus,
    };
    const ok = (verify.byteExact || verify.lfEqual || verify.ampNormEqual || verify.trimEndEqual) && verify.chuyenMucGiu && verify.trangThaiGiu && fieldKhacBiDoi.length === 0;
    return {
      status: ok ? 'DONE' : 'FAIL', ms, httpStatus: res.status, cmsReply: reply || replyText.slice(0, 300), verify,
      afterBody: ok ? undefined : bodyAfter, backup,
    };
  };

  /* ---------- xuất bản bài do CLI tạo (Chờ duyệt -> Xuất bản) ---------- */
  // Quyết định owner 24/09/2026: bài Hỏi Đáp mới tạo ở status 3 (Chờ duyệt), ghi ảnh + thân bài, verify
  // server, RỒI CLI mới đổi trạng thái. Đây là NGOẠI LỆ DUY NHẤT cho bất biến giuTrangThai của
  // hdWriteArticle — luôn là bước riêng, tường minh, không đụng thân bài/chuyên mục/field khác.
  window.hdPublishArticle = async ({ newsId, expectCurrentStatus = '3', dryRun = true }) => {
    const pageId = document.getElementById('hdNewsId')?.value;
    if (String(pageId) !== String(newsId)) return { status: 'ABORT', reason: `tab đang mở newsId=${pageId}, tham số ${newsId}` };
    if (typeof GetAllFormData !== 'function') return { status: 'ABORT', reason: 'sai trang — cần /v2/Faq/NewsEdit' };

    const before = await staticDoc(newsId);
    const sFields = staticFields(before.doc);
    const sCates = staticCates(before.doc);
    const bodyBefore = before.doc.getElementById(BODY_ID).value;

    if (String(sFields.hdCurrentStatus) !== String(expectCurrentStatus)) {
      return { status: 'ABORT', reason: `trạng thái hiện tại (${sFields.hdCurrentStatus}) khác kỳ vọng (${expectCurrentStatus}) — chỉ xuất bản bài đang đúng trạng thái CLI đã tạo`, currentStatus: sFields.hdCurrentStatus };
    }

    const data = GetAllFormData(FORM);
    const lc = liveCates();
    data.LstParentCategory = lc.parent.join(' ');
    data.LstChildCategory = lc.child.join(' ');
    const liveDrift = Object.keys({ ...sFields, ...data })
      .filter(k => !['LstParentCategory', 'LstChildCategory', BODY_ID].includes(k))
      .filter(k => crlf(data[k] ?? '<vắng>') !== crlf(sFields[k] ?? '<vắng>'));
    // Chỉ đổi cboStatus — thân bài/field khác giữ NGUYÊN giá trị server (không lấy từ TinyMCE).
    data.ContentNews = bodyBefore;
    data[BODY_ID] = bodyBefore;
    data.cboStatus = '2';

    const checks = {
      dungBai: String(data.hdNewsId) === String(newsId),
      formKhopServer: liveDrift.length === 0,
      dangDungTrangThaiKyVong: String(sFields.hdCurrentStatus) === String(expectCurrentStatus),
      chuyenMucChaGiu: lc.parent.join(' ') === sCates.parent.join(' ') && sCates.parent.length > 0,
      chuyenMucConGiu: lc.child.join(' ') === sCates.child.join(' ') && sCates.child.length > 0,
    };
    const failed = Object.entries(checks).filter(([, v]) => !v).map(([k]) => k);
    const backup = { newsId, at: new Date().toISOString(), content_FaqNews_DB: bodyBefore, fields: sFields, cates: sCates, fullPageHtml: before.raw };
    if (failed.length) return { status: 'ABORT', reason: 'bất biến xuất bản không đạt — KHÔNG POST', failed, checks, liveDrift, backup };
    if (dryRun) return { status: 'DRY', checks, backup };

    const skip = document.getElementById('hdIsSkipSecurity');
    const url = '/v2/Faq/SubmitNewsEdit' + (skip && skip.value === '1' ? '?skip=1' : '');
    const t0 = Date.now();
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' },
      body: jQuery.param(data), credentials: 'same-origin',
    });
    const ms = Date.now() - t0;
    const replyText = await res.text();
    let reply = null; try { reply = JSON.parse(replyText); } catch (e) {}

    let after;
    try { after = await staticDoc(newsId); }
    catch (e) { return { status: 'UNKNOWN', reason: e.message, ms, httpStatus: res.status, cmsReply: reply || replyText.slice(0, 300), backup }; }
    const aFields = staticFields(after.doc);
    const aCates = staticCates(after.doc);
    const bodyAfter = after.doc.getElementById(BODY_ID).value;
    const fieldKhacBiDoi = Object.keys({ ...sFields, ...aFields })
      .filter(k => k !== BODY_ID && k !== 'hdCurrentStatus' && crlf(aFields[k] ?? '') !== crlf(sFields[k] ?? ''));
    const verify = {
      trangThaiDaXuatBan: String(aFields.hdCurrentStatus) === '2',
      bodyKhongDoi: ampNorm(lf(bodyAfter)).trimEnd() === ampNorm(lf(bodyBefore)).trimEnd(),
      chuyenMucGiu: JSON.stringify(aCates) === JSON.stringify(sCates),
      fieldKhacBiDoi,
    };
    const ok = verify.trangThaiDaXuatBan && verify.bodyKhongDoi && verify.chuyenMucGiu && fieldKhacBiDoi.length === 0;
    return { status: ok ? 'DONE' : 'FAIL', ms, httpStatus: res.status, cmsReply: reply || replyText.slice(0, 300), verify, backup };
  };

  /* ---------- tạo bài mới (trang NewsEdit?newsId=0) ---------- */
  // Đo read-only 24/09/2026 trên newsId=0: form 25 key GetAllFormData, cboStatus mặc định 3 (Chờ duyệt),
  // txtTitle/txtMetaTitle maxlength 70, txtMetaDescription 170, URL đếm /100. Nhãn (*): Tiêu đề, URL,
  // Tiêu đề SEO, Meta Description, Keyword - Tags. faq.js KHÔNG validate client — server là cổng duy nhất,
  // nên runner tự chặn. Chuyên mục cha do trang tự nạp qua POST Faq/LoadHtmlParentCate khi đổi chuyên mục
  // con (endpoint đọc, trả <option>) — runner gọi y như trang để suy chuyên mục cha.
  const CREATE_LIMIT = { txtTitle: 70, txtMetaTitle: 70, txtMetaDescription: 170, txtUrl: 100 };
  const STATUS_OK = ['1', '2', '3', '4'];                       // 1 Nháp · 2 Xuất bản · 3 Chờ duyệt · 4 Đã duyệt
  const post = (url, body) => fetch(url, { method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' }, body });

  window.hdCreateArticle = async ({ fields = {}, thumbInputId = null, dryRun = true }) => {
    if (String(document.getElementById('hdNewsId')?.value) !== '0') return { status: 'ABORT', reason: 'tab không phải trang tạo mới (hdNewsId phải = 0)' };
    if (typeof GetAllFormData !== 'function') return { status: 'ABORT', reason: 'sai trang — cần /v2/Faq/NewsEdit?newsId=0' };
    const f = fields;
    const childOpts = [...document.querySelectorAll('#lst_childcate option')].map(o => o.value).filter(v => v !== '-1');
    const typeOpts = [...document.querySelectorAll('select[name=cboArticleType] option')].map(o => o.value).filter(Boolean);
    const child = (f.childCategories || []).map(String);
    let parentOpts = [];
    if (child.length && child.every(c => childOpts.includes(c))) {
      const html = await post('/v2/Faq/LoadHtmlParentCate', `lstChildCate=${encodeURIComponent(child.join(','))}&listParentThreadID=`).then(r => r.text());
      parentOpts = [...html.matchAll(/<option[^>]*value="([^"]+)"/g)].map(m => m[1]).filter(v => v !== '-1');
    }
    const parent = f.parentCategories && f.parentCategories.length ? f.parentCategories.map(String) : (parentOpts.length === 1 ? parentOpts : []);

    const data = GetAllFormData(FORM);
    const baseKeys = Object.keys(data).sort().join(',');
    const body = f.html && f.html.length ? f.html : `<p>${String(f.title || '').replace(/[<>&]/g, '')}</p>`;
    Object.assign(data, {
      txtTitle: f.title || '', txtUrl: f.url || '', txtMetaTitle: f.metaTitle || '', txtMetaDescription: f.metaDescription || '',
      hdListKeyword: (f.keywords || []).join(','), cboArticleType: f.articleType || '', cboStatus: String(f.status ?? ''),
      thumbnailNews: f.thumbnailUrl || '', thumbnailNewsWidth: '0', thumbnailNewsHeight: '0',
      cboChildCategory: child[child.length - 1] || '', cboParentCategory: parent[parent.length - 1] || '',
    });
    data.LstParentCategory = parent.join(' ');
    data.LstChildCategory = child.join(' ');
    data.ContentNews = body;
    data[BODY_ID] = body;

    const bodyImgs = [...body.matchAll(/<img\b[^>]*?\bsrc=["']([^"']+)["']/gi)].map(m => m[1]);
    const overLimit = Object.entries(CREATE_LIMIT).filter(([k, n]) => (data[k] || '').length > n).map(([k, n]) => `${k} ${data[k].length}>${n}`);
    const checks = {
      trangTaoMoi: data.hdNewsId === '0',
      duField: ['txtTitle', 'txtUrl', 'txtMetaTitle', 'txtMetaDescription', 'hdListKeyword'].every(k => String(data[k]).trim().length > 0),
      urlDungDang: /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(data.txtUrl),
      trongNguongDoDai: overLimit.length === 0,
      toiDa5Keyword: (f.keywords || []).length <= 5,
      trangThaiHopLe: STATUS_OK.includes(data.cboStatus),
      chuyenMucConCo: child.length > 0 && child.every(c => childOpts.includes(c)),
      chuyenMucChaHopLe: parent.length > 0 && parent.every(p => parentOpts.includes(p)),
      dangBaiHopLe: !f.articleType || typeOpts.includes(f.articleType),
      khongAnhLocal: bodyImgs.every(s => /^https?:\/\//i.test(s)),
      duKeyForm: Object.keys(GetAllFormData(FORM)).sort().join(',') === baseKeys,
    };
    const failed = Object.entries(checks).filter(([, v]) => !v).map(([k]) => k);
    const info = { overLimit, parentOpts, childBad: child.filter(c => !childOpts.includes(c)), bodyLen: body.length, placeholderBody: !(f.html && f.html.length) };
    const payload = { ...data };
    if (failed.length) return { status: 'ABORT', reason: 'bất biến tạo bài không đạt — KHÔNG POST', failed, checks, ...info, payload };
    if (dryRun) return { status: 'DRY', checks, ...info, payload, thumbnailUpload: thumbInputId ? 'sẽ PostImage type=56 lúc --live' : null };

    const t0 = Date.now();
    let thumb = null;
    if (thumbInputId) {
      // Như html5Uploader của ô thumbnail: FormData { uploadedFile }, ảnh vào common/Common/ (kho chung).
      const fd = new FormData();
      fd.append('uploadedFile', filesOf(thumbInputId)[0]);
      const tr = await fetch('/v2/Common/PostImage?type=56&productId=0&categoryId=-1&siteId=-1&dentination=&isSetHeight=True&isValidateImg=True',
        { method: 'POST', body: fd, credentials: 'same-origin' });
      try { thumb = JSON.parse(await tr.text()); } catch (e) { thumb = null; }
      if (!thumb || thumb.status === -1 || !thumb.imageUrl) return { status: 'FAIL', stage: 'thumbnail', reason: 'upload thumbnail lỗi — CHƯA tạo bài', thumb };
      data.thumbnailNews = thumb.imageUrl;
      data.thumbnailNewsWidth = String(thumb.width ?? 0);
      data.thumbnailNewsHeight = String(thumb.height ?? 0);
    }
    const skip = document.getElementById('hdIsSkipSecurity');
    const res = await post('/v2/Faq/SubmitNewsEdit' + (skip && skip.value === '1' ? '?skip=1' : ''), jQuery.param(data));
    const replyText = await res.text();
    let reply = null; try { reply = JSON.parse(replyText); } catch (e) {}
    const newsId = reply && Number.isInteger(Number(reply.status)) && Number(reply.status) > 1 ? Number(reply.status) : null;
    const ms = Date.now() - t0;
    if (!newsId) return { status: 'FAIL', stage: 'submit', ms, httpStatus: res.status, cmsReply: reply || replyText.slice(0, 300), thumb };

    // Nghiệm thu: đọc lại tĩnh bài vừa tạo — thông báo CMS không chứng minh gì.
    // POST đã đi (có newsId) nhưng đọc lại LỖI (mất session, trang không tải được...) là trạng thái
    // KHÔNG RÕ — khác với "đọc lại được nhưng field lệch" (đó là FAIL). Đừng đoán, trả UNKNOWN.
    let after;
    try { after = await staticDoc(newsId); }
    catch (e) { return { status: 'UNKNOWN', stage: 'readback', newsId, ms, httpStatus: res.status, cmsReply: reply || replyText.slice(0, 300), reason: e.message, thumb }; }
    const aF = staticFields(after.doc);
    const aC = staticCates(after.doc);
    const bodyAfter = after.doc.getElementById(BODY_ID).value;
    const eq = (k) => lf(aF[k] ?? '').trim() === lf(data[k] ?? '').trim();
    const verify = {
      dungId: String(aF.hdNewsId) === String(newsId),
      title: eq('txtTitle'), url: eq('txtUrl'), metaTitle: eq('txtMetaTitle'), metaDescription: eq('txtMetaDescription'),
      keyword: eq('hdListKeyword'), trangThai: String(aF.hdCurrentStatus) === data.cboStatus,
      chuyenMucCon: aC.child.join(' ') === data.LstChildCategory, chuyenMucCha: aC.parent.join(' ') === data.LstParentCategory,
      thumbnail: eq('thumbnailNews'),
      body: ampNorm(lf(bodyAfter)).trimEnd() === ampNorm(lf(body)).trimEnd(),
      urlGot: aF.txtUrl,
    };
    // keyword/thumbnail chưa từng đo đọc lại sau tạo → chỉ cảnh báo, không chặn chuỗi air.
    const SOFT = ['keyword', 'thumbnail', 'urlGot'];
    const failedVerify = Object.entries(verify).filter(([k, v]) => !SOFT.includes(k) && v !== true).map(([k]) => k);
    const warn = ['keyword', 'thumbnail'].filter(k => verify[k] !== true);
    return { status: failedVerify.length ? 'FAIL' : 'DONE', stage: 'verify', newsId, ms, httpStatus: res.status, cmsReply: reply, verify, failedVerify, warn, thumb };
  };

  return 'air-hoidap-runner đã nạp: hdMakeInput / hdUploadImages / hdWriteArticle / hdCreateArticle / hdPublishArticle (dryRun mặc định true)';
})();
