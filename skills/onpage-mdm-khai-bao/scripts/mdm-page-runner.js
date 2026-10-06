/*
 * mdm-page-runner.js — chạy TRONG tab MDM ẩn danh đã đăng nhập (nạp bằng evaluate_script).
 *
 * Khai báo __mdmRun(cfg, ops): lấy token từ IndexedDB của trang (keyval-store/keyval,
 * key MDM_TOKEN; tab PIM thì key Token), gửi lần lượt từng op, trả kết quả.
 * Token KHÔNG BAO GIỜ được trả ra ngoài — chỉ dùng trong header của fetch.
 *
 * op:
 *   {api:'mdm'|'pim', path, body, project?}   POST JSON. project={top:[...], raw:[...]} cắt bớt
 *                                              danh sách lớn (cây danh mục có bài 60 KB/nút).
 *   {api:'pim', upload:{b64, name, mime, allowedExtensions}}   POST multipart s3/cdnput.
 * Gặp op lỗi mạng thì dừng chuỗi (không chạy op sau) — op ghi không bao giờ được chạy mù.
 */
var __mdmRun = async (cfg, ops) => {
  const readKey = (key) => new Promise((resolve) => {
    const req = indexedDB.open('keyval-store');
    req.onerror = () => resolve(null);
    req.onsuccess = () => {
      try {
        const g = req.result.transaction('keyval').objectStore('keyval').get(key);
        g.onsuccess = () => resolve(g.result && g.result.access_token ? g.result.access_token : null);
        g.onerror = () => resolve(null);
      } catch (e) { resolve(null); }
    };
  });
  const tok = (await readKey('MDM_TOKEN')) || (await readKey('Token'));
  if (!tok) return { ok: false, reason: 'no_token' };

  const base = (api) => (api === 'pim' ? cfg.pimApiBase : cfg.apiBase);
  const projectRow = (row, p) => {
    const out = {};
    for (const k of p.top || []) if (k in row) out[k] = row[k];
    const raw = row.raw_values || row.rawValues;
    if (p.raw && raw) {
      const r = typeof raw === 'string' ? JSON.parse(raw) : raw;
      out.raw = {};
      for (const k of p.raw) if (k in r) out.raw[k] = r[k];
    }
    return out;
  };

  const results = [];
  for (const op of ops) {
    const t0 = Date.now();
    try {
      let res;
      if (op.upload) {
        const bin = atob(op.upload.b64);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const fd = new FormData();
        fd.append('resourceName', 'pim_product');
        fd.append('localeCode', 'vi_VN');
        fd.append('allowedExtensions', op.upload.allowedExtensions);
        fd.append('multipartFile', new Blob([bytes], { type: op.upload.mime }), op.upload.name);
        res = await fetch(base('pim') + 's3/cdnput', { method: 'POST', headers: { authorization: 'Bearer ' + tok }, body: fd });
      } else {
        res = await fetch(base(op.api) + op.path, {
          method: 'POST',
          headers: { 'content-type': 'application/json', authorization: 'Bearer ' + tok },
          body: JSON.stringify(op.body),
        });
      }
      const text = await res.text();
      let json = null;
      try { json = JSON.parse(text); } catch (e) { /* trả text thô bên dưới */ }
      if (json && op.project && Array.isArray(json.object)) json.object = json.object.map((r) => projectRow(r, op.project));
      results.push({ ok: true, status: res.status, ms: Date.now() - t0, json, text: json ? undefined : text.slice(0, 500) });
    } catch (e) {
      results.push({ ok: false, ms: Date.now() - t0, error: String(e && e.message || e) });
      break;
    }
  }
  return { ok: true, results };
};
