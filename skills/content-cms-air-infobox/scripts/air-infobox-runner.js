/*
 * air-infobox-runner.js — chạy TRONG page context của tab CMS đã đăng nhập.
 *
 * Nạp file bằng CDP (upload_file) vào một input[type=file], rồi gọi:
 *   await airUploadImages({ newsId, siteId, inputId })
 *   await airWriteBody({ newsId, siteId, inputId })
 *
 * Không bao giờ đọc/ghi cookie. Không in credential.
 */

(() => {
  const CATE_INFOBOX = '2424';                  // "Mô tả dòng sản phẩm" — bắt buộc cho bài Infobox
  const SLOW_POST_MS = 2000;                    // POST ghi thật mất ~30s; nhanh hơn ngưỡng này là đáng ngờ

  const staticDoc = async (newsId, siteId) => {
    const raw = await fetch(`/v2/News/NewsEdit?newsId=${newsId}&siteId=${siteId}&_=${Date.now()}`,
      { credentials: 'same-origin' }).then(r => r.text());
    return { raw, doc: new DOMParser().parseFromString(raw, 'text/html') };
  };

  const readBody = doc => {
    const el = doc.getElementById('contentNewsAva');
    if (!el) throw new Error('không thấy #contentNewsAva — mất session đăng nhập hoặc sai newsId');
    return el.value;
  };

  const readCates = doc =>
    [...doc.querySelectorAll('ul.sticker.newscategory li[data-id]')].map(li => li.getAttribute('data-id'));

  const filesOf = inputId => {
    const el = document.getElementById(inputId);
    if (!el) throw new Error(`không thấy input #${inputId}`);
    if (!el.files || !el.files.length) throw new Error(`#${inputId} chưa có file (nạp bằng CDP upload_file trước)`);
    return [...el.files];
  };

  /* ---------- Bước 1: upload ảnh ---------- */
  // Ảnh vào https://cdnv2.tgdd.vn/mwg-static/common/News/{newsId}/{tên file}
  // newsId = 0 (bài chưa tạo) sẽ rơi vào kho chung /News/0/ — xem SKILL.md Bước 0.
  window.airUploadImages = async ({ newsId, siteId = 1, inputId = 'claudeProbeUpload' }) => {
    const files = filesOf(inputId);
    const fd = new FormData();
    fd.append('ID', String(newsId));
    fd.append('site', String(siteId));
    fd.append('type', 3);
    files.forEach((f, i) => fd.append('file' + i, f, f.name));

    const t0 = Date.now();
    const res = await fetch('/v2/Common/UploadManyImages',
      { method: 'POST', body: fd, credentials: 'same-origin' });
    const text = await res.text();

    let asJson = null; try { asJson = JSON.parse(text); } catch (e) { /* thành công trả HTML */ }
    if (asJson && asJson.status === -1) {
      // Hay gặp nhất: "Tên file đã tồn tại" — CMS TỪ CHỐI ghi đè, không phải lỗi mạng.
      return { ok: false, error: asJson.error, sent: files.map(f => f.name), ms: Date.now() - t0 };
    }

    const urls = [...new Set((text.match(/https?:\/\/[^"'\s<>\\]+\.(?:jpg|jpeg|png|webp)/gi) || []))];
    const byName = {};
    for (const f of files) {
      const hit = urls.find(u => u.endsWith('/' + f.name));
      if (hit) byName[f.name] = hit;
    }
    const missing = files.map(f => f.name).filter(n => !byName[n]);

    return {
      ok: missing.length === 0,
      ms: Date.now() - t0,
      uploaded: byName,
      missing,                                   // file không thấy URL trả về => coi như CHƯA lên
      wrongFolder: Object.values(byName).filter(u => !u.includes(`/News/${newsId}/`)),
    };
  };

  /* ---------- Bước 2: ghi thân bài ---------- */
  // BẤT BIẾN SỐNG CÒN: server đọc `ContentNews`, KHÔNG phải `contentNewsAva`.
  // getDataSubmitNews() gán data.ContentNews = tinymce.get("contentNewsAva").getContent().
  // Xoá ContentNews => CMS vẫn trả "Cập nhật thành công" nhưng thân bài KHÔNG đổi.
  window.airWriteBody = async ({
    newsId, siteId = 1, inputId = 'claudeProbeUpload',
    html = null, expectCategoryId = CATE_INFOBOX, expectImages = null, dryRun = false,
  }) => {
    const body = html != null ? html : await filesOf(inputId)[0].text();
    if (!body || body.length < 500) return { status: 'ABORT', reason: 'nội dung mới quá ngắn, nghi nạp nhầm file' };

    const before = await staticDoc(newsId, siteId);
    const bodyBefore = readBody(before.doc);
    const catesBefore = readCates(before.doc);
    const statusBefore = (before.doc.getElementById('hdCurrentStatus') || {}).value;

    const data = getDataSubmitNews();
    data.ContentNews = body;        // field server thật sự ghi
    data.contentNewsAva = body;     // giữ form field khớp

    const imgs = (body.match(/<img/g) || []).length;
    const checks = {
      contentNewsSet: data.ContentNews === body,
      chuyenMucDung: data.LstCategoryId === expectCategoryId,
      chuyenMucKhongMat: catesBefore.length === 0 || data.LstCategoryId.split(',').length >= catesBefore.length,
      giuTrangThai: data.cboStatus === statusBefore,
      anhDungThuMuc: imgs === 0 || (body.match(new RegExp(`News/${newsId}/`, 'g')) || []).length === imgs,
      soAnhDungKyVong: expectImages == null || imgs === expectImages,
      khongConAltRong: !/alt=""/.test(body),
    };
    const failed = Object.entries(checks).filter(([, v]) => !v).map(([k]) => k);
    if (failed.length) return { status: 'ABORT', reason: 'bất biến không đạt — KHÔNG POST', failed, checks };

    if (dryRun) {
      return { status: 'DRY', checks, willWrite: { len: body.length, imgs },
               current: { len: bodyBefore.length, imgs: (bodyBefore.match(/<img/g) || []).length },
               backup: { contentNewsAva_DB: bodyBefore, fullPageHtml: before.raw } };
    }

    const skip = document.getElementById('hdIsSkipSecurity');
    const url = '/v2/News/SubmitNewsEdit' + (skip && skip.value === '1' ? '?skip=1' : '');
    const t0 = Date.now();
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' },
      body: jQuery.param(data), credentials: 'same-origin',
    });
    const ms = Date.now() - t0;
    let reply = null; try { reply = JSON.parse(await res.text()); } catch (e) {}

    // Nghiệm thu: thông báo "Cập nhật thành công" của CMS KHÔNG chứng minh gì.
    const after = await staticDoc(newsId, siteId);
    const bodyAfter = readBody(after.doc);
    const catesAfter = readCates(after.doc);

    const verify = {
      byteExact: bodyAfter === body,
      len: bodyAfter.length,
      imgs: (bodyAfter.match(/<img/g) || []).length,
      links: (bodyAfter.match(/<a /g) || []).length,
      chuyenMucGiuNguyen: catesAfter.join(',') === catesBefore.join(',') && catesAfter.includes(expectCategoryId),
      trangThaiGiuNguyen: (after.doc.getElementById('hdCurrentStatus') || {}).value === statusBefore,
      nghiNgoNhanhBatThuong: ms < SLOW_POST_MS,   // POST ghi thật mất ~30s
    };

    return {
      status: verify.byteExact && verify.chuyenMucGiuNguyen && verify.trangThaiGiuNguyen ? 'DONE' : 'FAIL',
      ms, cmsReply: reply, verify,
      backup: { contentNewsAva_DB: bodyBefore, fullPageHtml: before.raw },
    };
  };

  /* ---------- Bước 3 (bài mới): tạo bài lấy newsId ---------- */
  // Trả về newsId mới ở reply.status khi > 1. Bài mới có hdNewsId=0 nên PHẢI tạo trước rồi mới upload ảnh.
  window.airCreateNews = async ({ siteId = 1, dryRun = true } = {}) => {
    const data = getDataSubmitNews();
    if (data.LstCategoryId !== CATE_INFOBOX) {
      return { status: 'ABORT', reason: `chuyên mục phải là ${CATE_INFOBOX} (Mô tả dòng sản phẩm), đang là "${data.LstCategoryId}"` };
    }
    if (dryRun) return { status: 'DRY', fields: Object.keys(data).length, cate: data.LstCategoryId, cboStatus: data.cboStatus };

    const res = await fetch('/v2/News/SubmitNewsEdit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' },
      body: jQuery.param(data), credentials: 'same-origin',
    });
    let reply = null; try { reply = JSON.parse(await res.text()); } catch (e) {}
    const newsId = reply && reply.status > 1 ? reply.status : null;
    return { status: newsId ? 'DONE' : 'FAIL', newsId, cmsReply: reply };
  };

  return 'air-infobox-runner đã nạp: airUploadImages / airWriteBody / airCreateNews';
})();
