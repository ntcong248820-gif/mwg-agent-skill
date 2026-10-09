/**
 * mdm-browser.mjs — bám tab MDM đã đăng nhập có sẵn và chạy op trong trang qua chrome-devtools-mcp.
 *
 * Từ 09/10/2026 MDM/PIM đăng nhập được ở tab THƯỜNG của profile Chrome thật (trước đó chỉ cửa sổ ẩn danh).
 * Module này vẫn KHÔNG mở tab, KHÔNG điều hướng: chỉ tìm tab có origin MDM + có token rồi evaluate trong đó
 * — không điều hướng để không làm mất bài người dùng đang sửa dở trên tab đó.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { McpClient, evaluate, pagesFromListResult, CliError, TimeoutError } from './cms-cli-mcp.mjs';
import { DirectRunner, DirectUnavailable } from './mdm-direct.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RUNNER = fs.readFileSync(path.join(HERE, 'mdm-page-runner.js'), 'utf8');

/** Phần config runner cần (chỉ origin API, không ID màn). */
export function runnerCfg(cfg) {
  return { apiBase: cfg.apiBase, pimApiBase: cfg.pimApiBase };
}

/** Function evaluate: nạp runner rồi chạy ops. */
export function pageFn(cfg, ops) {
  return `async () => {\n${RUNNER}\n;\nreturn await __mdmRun(${JSON.stringify(runnerCfg(cfg))}, ${JSON.stringify(ops)});\n}`;
}

// Chỉ các lệnh đọc DANH SÁCH TĨNH của MDM (cây danh mục, hãng, giá trị filter) mới được cache trong
// 1 phiên batch. getinfor/getlist4tree/mọi lệnh PIM và mọi lệnh ghi KHÔNG bao giờ cache.
const CACHEABLE_MDM_LISTS = new Set(['datatobject/getlistbyroot', 'dataobject/getlist', 'datarelation/getlist2']);
const isCacheableList = (op) => op.api === 'mdm' && !op.upload && CACHEABLE_MDM_LISTS.has(op.path);

export class MdmSession {
  constructor(cfg, { client, pageId, cacheLists = false } = {}) {
    this.cfg = cfg;
    this.client = client || new McpClient({ roots: [process.cwd()] });
    this.wantPageId = pageId ?? null;
    this.pageId = null;
    this.listCache = cacheLists ? new Map() : null;
  }

  /**
   * list_pages là bước đầu tiên chạm Chrome thật, nên cũng là bước Chrome có thể hiện hộp "Allow remote
   * debugging?" và chờ owner bấm. Treo ở đây có 2 nguyên nhân không phân biệt được từ ngoài: hộp đang chờ
   * người, hoặc CDP kẹt tạm (đo 24/09: khởi động lại MCP rồi gọi lại ngay thì qua).
   * Khởi động lại MCP = mở kết nối mới = có thể HIỆN THÊM một hộp thoại chồng lên hộp cũ (owner đi vắng
   * quay lại thấy dồn đống). Vì vậy thử lại TRÊN CÙNG tiến trình trước (đúng 1 lần, chờ lâu hơn để owner
   * kịp bấm); chỉ khi vẫn treo mới khởi động lại, đúng 1 lần như cũ.
   */
  async open({ log = (m) => process.stderr.write(`${m}\n`), firstTimeoutMs = 60000, retryTimeoutMs = 90000 } = {}) {
    await this.client.connect();
    const t0 = Date.now();
    const hint = setTimeout(() => log('đang chờ Chrome trả lời (>8s) — nếu Chrome hiện hộp "Allow remote debugging?" thì bấm Allow; CLI sẽ chờ thêm, không mở kết nối mới'), 8000);
    let listed;
    try {
      try {
        listed = await this.client.callTool('list_pages', {}, firstTimeoutMs);
      } catch (err) {
        if (!(err instanceof TimeoutError)) throw err;
        log(`list_pages chưa trả lời sau ${Math.round(firstTimeoutMs / 1000)}s — thử lại trên cùng kết nối`);
        try {
          listed = await this.client.callTool('list_pages', {}, retryTimeoutMs);
        } catch (err2) {
          if (!(err2 instanceof TimeoutError)) throw err2;
          log('vẫn treo — khởi động lại MCP một lần (có thể hiện thêm một hộp thoại Chrome)');
          try { await this.client.close(); } catch { /* proc có thể đã chết */ }
          await this.client.connect();
          listed = await this.client.callTool('list_pages', {}, firstTimeoutMs);
        }
      }
    } finally { clearTimeout(hint); }
    this.openMs = Date.now() - t0;
    const pages = pagesFromListResult(listed);
    const cands = this.wantPageId != null
      ? pages.filter((p) => p.id === Number(this.wantPageId))
      : pages.filter((p) => p.url.startsWith(this.cfg.uiOrigin));
    if (!cands.length) {
      throw new CliError(`không thấy tab ${this.cfg.uiOrigin} nào — mở MDM (tab thường hoặc ẩn danh) đã đăng nhập rồi chạy lại`, 4);
    }
    for (const p of cands) {
      await this.client.callTool('select_page', { pageId: p.id, bringToFront: false });
      this.client.pageId = p.id;
      const probe = await evaluate(this.client, pageFn(this.cfg, []), 30000);
      if (probe && probe.ok) { this.pageId = p.id; return p; }
    }
    throw new CliError('các tab MDM đều không có token (phiên hết hạn) — đăng nhập lại MDM', 4);
  }

  /** Chạy ops, có cache danh sách tĩnh nếu bật. Trả mảng kết quả; op lỗi mạng làm dừng chuỗi. */
  async run(ops, timeoutMs = 120000) {
    const ck = this.listCache && ops.length && ops.every(isCacheableList) ? JSON.stringify(ops) : null;
    if (ck && this.listCache.has(ck)) return this.listCache.get(ck);
    const results = await this._exec(ops, timeoutMs);
    // Chỉ nhớ kết quả sạch: lỗi mạng/HTTP/server không được ở lại cache.
    if (ck && results.every((x) => x && x.ok && x.json && !x.json.error)) this.listCache.set(ck, results);
    return results;
  }

  /** Đường lái tab: fetch chạy TRONG trang, token không rời tab. */
  async _exec(ops, timeoutMs) {
    const r = await evaluate(this.client, pageFn(this.cfg, ops), timeoutMs);
    if (!r || !r.ok) throw new CliError(`tab mất token giữa chừng (${r && r.reason}) — đăng nhập lại MDM`, 4);
    return r.results;
  }

  /**
   * Đọc token từ tab đang bám, để đường gọi thẳng giữ trong RAM. Lỗi được che sạch: thông điệp lỗi gốc
   * của evaluate có thể chứa nguyên văn kết quả tool (tức token), nên không bao giờ chuyển tiếp.
   */
  async readToken() {
    let r;
    try {
      r = await evaluate(this.client, `async () => {\n${RUNNER}\n;\nreturn { token: await __mdmToken() };\n}`, 30000);
    } catch { throw new DirectUnavailable('không đọc được token từ tab (đã che chi tiết)', 'no-token'); }
    if (!r || typeof r.token !== 'string' || r.token.length < 16) throw new DirectUnavailable('tab không có token hợp lệ', 'no-token');
    return r.token;
  }

  /** 1 POST JSON, trả json; lỗi mạng/HTTP/không phải JSON → ném. */
  async post(api, p, body, project) {
    const [res] = await this.run([{ api, path: p, body, project }]);
    if (!res || !res.ok) throw new CliError(`gọi ${p} lỗi mạng: ${res && res.error}`, 1);
    if (!res.json) throw new CliError(`gọi ${p} trả HTTP ${res.status} không phải JSON: ${res.text}`, 1);
    return res.json;
  }

  async close() { await this.client.close(); }
}

/**
 * Phiên 2 đường: direct (HTTP thẳng từ Node, token trong RAM) và tab (lái trang). Luôn mở tab trước
 * (cần cho cả hai: lấy token và làm đường rơi về), nên rơi về tab không mở thêm kết nối Chrome nào.
 *   transport 'auto' (mặc định)  direct; gặp DirectUnavailable thì chuyển sang tab cho phần còn lại của phiên
 *   transport 'tab'              chỉ lái tab, không bao giờ đọc token ra khỏi trang
 */
export class AutoSession extends MdmSession {
  constructor(cfg, { transport = 'auto', fetchFn, log = (m) => process.stderr.write(`${m}\n`), ...rest } = {}) {
    super(cfg, rest);
    if (!['auto', 'tab'].includes(transport)) throw new CliError(`--transport phải là auto | tab (nhận "${transport}")`, 2);
    this.wantTransport = transport;
    this.fetchFn = fetchFn;
    this.log = log;
    this.direct = null;
    this.mode = 'tab';
    this.fallbacks = [];
  }

  async open(opts) {
    const page = await super.open(opts);
    if (this.wantTransport === 'auto') {
      try {
        this.direct = new DirectRunner(this.cfg, await this.readToken(), { fetchFn: this.fetchFn });
        this.mode = 'direct';
      } catch (e) {
        this.log(`đường gọi thẳng không dùng được (${e.reason || e.message}) — chạy bằng lái tab`);
        this.fallbacks.push(e.reason || 'error');
      }
    }
    return page;
  }

  async _exec(ops, timeoutMs) {
    if (this.mode === 'direct') {
      try { return await this.direct.run(ops); } catch (e) {
        if (!(e instanceof DirectUnavailable)) throw e;
        this.log(`đường gọi thẳng lỗi (${e.reason}: ${e.message}) — chuyển sang lái tab cho phần còn lại của phiên`);
        this.fallbacks.push(e.reason);
        this.mode = 'tab';
        this.direct = null; // bỏ token khỏi RAM ngay khi không còn dùng
      }
    }
    return super._exec(ops, timeoutMs);
  }

  async close() { this.direct = null; await super.close(); }
}
