/**
 * mdm-browser.mjs — bám tab MDM ẩn danh có sẵn và chạy op trong trang qua chrome-devtools-mcp.
 *
 * Phiên MDM chỉ sống trong CỬA SỔ ẨN DANH người dùng đã đăng nhập. Mở tab mới (chrome-profile
 * hay new_page) rơi vào profile thường → trang đăng nhập Keycloak. Vì vậy module này KHÔNG mở
 * tab, KHÔNG điều hướng: chỉ tìm tab có origin MDM + có token rồi evaluate trong đó.
 * Không điều hướng còn để không làm mất bài người dùng đang sửa dở trên tab đó.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { McpClient, evaluate, pagesFromListResult, CliError, TimeoutError } from './cms-cli-mcp.mjs';

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

export class MdmSession {
  constructor(cfg, { client, pageId } = {}) {
    this.cfg = cfg;
    this.client = client || new McpClient({ roots: [process.cwd()] });
    this.wantPageId = pageId ?? null;
    this.pageId = null;
  }

  async open() {
    await this.client.connect();
    // list_pages chỉ đọc: đôi khi treo đúng 60s rồi gọi lại ngay thì được (giống skill CMS).
    // Khởi động lại kết nối MCP và thử lại ĐÚNG 1 lần. Không áp cho evaluate/POST.
    let listed;
    try {
      listed = await this.client.callTool('list_pages', {}, 60000);
    } catch (err) {
      if (!(err instanceof TimeoutError)) throw err;
      try { await this.client.close(); } catch { /* proc có thể đã chết */ }
      await this.client.connect();
      listed = await this.client.callTool('list_pages', {}, 60000);
    }
    const pages = pagesFromListResult(listed);
    const cands = this.wantPageId != null
      ? pages.filter((p) => p.id === Number(this.wantPageId))
      : pages.filter((p) => p.url.startsWith(this.cfg.uiOrigin));
    if (!cands.length) {
      throw new CliError(`không thấy tab ${this.cfg.uiOrigin} nào — mở MDM trong CỬA SỔ ẨN DANH đã đăng nhập rồi chạy lại`, 4);
    }
    for (const p of cands) {
      await this.client.callTool('select_page', { pageId: p.id, bringToFront: false });
      this.client.pageId = p.id;
      const probe = await evaluate(this.client, pageFn(this.cfg, []), 30000);
      if (probe && probe.ok) { this.pageId = p.id; return p; }
    }
    throw new CliError('các tab MDM đều không có token (phiên hết hạn hoặc không phải cửa sổ ẩn danh) — đăng nhập lại MDM ẩn danh', 4);
  }

  /** Chạy ops trong trang. Trả mảng kết quả; op lỗi mạng làm dừng chuỗi. */
  async run(ops, timeoutMs = 120000) {
    const r = await evaluate(this.client, pageFn(this.cfg, ops), timeoutMs);
    if (!r || !r.ok) throw new CliError(`tab mất token giữa chừng (${r && r.reason}) — đăng nhập lại MDM ẩn danh`, 4);
    return r.results;
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
