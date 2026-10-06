/**
 * cms-cli-mcp.mjs — phần chung của các CLI can thiệp CMS MWG: nói chuyện với
 * chrome-devtools-mcp qua stdio JSON-RPC, mở tab đúng profile, bám đúng tab.
 *
 * Skill MDM chỉ dùng McpClient, evaluate, pagesFromListResult, CliError, TimeoutError;
 * phần mở tab theo profile (chrome-profile CLI) giữ lại cho các CLI CMS dùng chung.
 *
 * Không đọc/in cookie, token hay credential. Chỉ đọc URL tab và kết quả evaluate.
 */

import { spawn as nodeSpawn, execFile as nodeExecFile } from 'node:child_process';
import readline from 'node:readline';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const CMS_ORIGIN = 'https://cms.thegioididong.com';

export class CliError extends Error {
  constructor(message, exitCode = 1) {
    super(message);
    this.exitCode = exitCode;
  }
}

export class TimeoutError extends Error {}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Đường chạy chrome-devtools-mcp: env > homebrew > PATH. Cùng cờ --autoConnect như MCP config của máy. */
export function defaultMcpBin() {
  if (process.env.CHROME_DEVTOOLS_MCP_BIN) return process.env.CHROME_DEVTOOLS_MCP_BIN;
  if (fs.existsSync('/opt/homebrew/bin/chrome-devtools-mcp')) return '/opt/homebrew/bin/chrome-devtools-mcp';
  return 'chrome-devtools-mcp';
}

/**
 * Client JSON-RPC tối giản cho MCP stdio. `spawnFn` tiêm được để test bằng MCP giả.
 * Mọi request có timeout riêng; process chết thì mọi request đang chờ bị reject ngay.
 */
export class McpClient {
  constructor({ spawnFn = nodeSpawn, bin = defaultMcpBin(), args = ['--autoConnect'], roots = [process.cwd()] } = {}) {
    this.spawnFn = spawnFn;
    // MCP roots: server chỉ cho upload_file/đọc-ghi file trong các thư mục này. Không khai báo
    // roots thì chrome-devtools-mcp 1.8 chặn mọi path ngoài thư mục temp (đo 24/09/2026) — đừng
    // chữa bằng --allowUnrestrictedPaths, khai đúng thư mục repo là đủ.
    this.roots = roots;
    this.bin = bin;
    this.args = args;
    this.proc = null;
    this.pending = new Map();
    this.nextId = 1;
    this.exited = false;
    this.stderrTail = '';
    this.schemas = null;
    this.pageId = null; // tab đã bám bằng URL-anchor; mọi tool page-scoped nhắm đúng tab này
  }

  async connect(timeoutMs = 60000) {
    // Cho phép gọi lại connect() sau khi đã close() (khởi động lại kết nối MCP để phục hồi
    // sau list_pages timeout — xem bindProfileTab). Không reset thì exited=true từ lần đóng
    // trước làm mọi request() sau đó bị reject ngay dù proc mới đã sống.
    this.exited = false;
    this.pending.clear();
    this.proc = this.spawnFn(this.bin, this.args, { stdio: ['pipe', 'pipe', 'pipe'] });
    this.proc.on('exit', (code) => {
      this.exited = true;
      for (const [, p] of this.pending) p.reject(new Error(`chrome-devtools-mcp thoát (code ${code}). stderr: ${this.stderrTail.slice(-300)}`));
      this.pending.clear();
    });
    this.proc.on('error', (err) => {
      this.exited = true;
      for (const [, p] of this.pending) p.reject(err);
      this.pending.clear();
    });
    if (this.proc.stderr) this.proc.stderr.on('data', (d) => { this.stderrTail = (this.stderrTail + d).slice(-2000); });
    const rl = readline.createInterface({ input: this.proc.stdout });
    rl.on('line', (line) => {
      let msg;
      try { msg = JSON.parse(line); } catch { return; }
      if (msg.method === 'roots/list' && msg.id != null) {
        const roots = this.roots.map((r) => ({ uri: pathToFileURL(r).href, name: path.basename(r) }));
        this.proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: msg.id, result: { roots } }) + '\n');
        return;
      }
      if (msg.method) return; // request/notification khác từ server: không phải response
      if (msg.id == null || !this.pending.has(msg.id)) return;
      const p = this.pending.get(msg.id);
      this.pending.delete(msg.id);
      if (msg.error) p.reject(new Error(`MCP ${p.method}: ${msg.error.message || JSON.stringify(msg.error)}`));
      else p.resolve(msg.result);
    });
    await this.request('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: { roots: { listChanged: false } },
      clientInfo: { name: 'mwg-cms-cli', version: '1.0.0' },
    }, timeoutMs);
    this.notify('notifications/initialized');
    // Schema tool thay đổi theo bản/cờ server: bản có pageIdRouting BẮT BUỘC pageId, và server
    // từ chối tham số lạ. Đọc schema một lần để callTool gửi đúng bộ tham số.
    try {
      const r = await this.request('tools/list', {}, timeoutMs);
      this.schemas = Object.fromEntries((r.tools || []).map((t) => [t.name, new Set(Object.keys(t.inputSchema?.properties || {}))]));
    } catch { this.schemas = null; }
  }

  /** Thêm pageId đã bám khi tool nhận pageId; bỏ tham số tuỳ chọn mà bản server này không có. */
  shapeArgs(name, args) {
    const props = this.schemas?.[name];
    if (!props) return args;
    const out = {};
    for (const [k, v] of Object.entries(args)) if (props.has(k)) out[k] = v;
    if (props.has('pageId') && out.pageId === undefined && this.pageId != null) out.pageId = this.pageId;
    return out;
  }

  notify(method, params) {
    this.proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, ...(params ? { params } : {}) }) + '\n');
  }

  request(method, params = {}, timeoutMs = 60000) {
    if (!this.proc || this.exited) return Promise.reject(new Error('MCP chưa kết nối hoặc đã thoát'));
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new TimeoutError(`quá ${Math.round(timeoutMs / 1000)}s chờ ${method}${params.name ? ' ' + params.name : ''}`));
      }, timeoutMs);
      this.pending.set(id, {
        method,
        resolve: (v) => { clearTimeout(timer); resolve(v); },
        reject: (e) => { clearTimeout(timer); reject(e); },
      });
      this.proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
    });
  }

  /** Gọi tool; tool trả isError thì ném lỗi kèm text, không nuốt. */
  async callTool(name, args = {}, timeoutMs = 60000) {
    const result = await this.request('tools/call', { name, arguments: this.shapeArgs(name, args) }, timeoutMs);
    if (result && result.isError) throw new Error(`tool ${name} lỗi: ${toolText(result).slice(0, 500)}`);
    return result;
  }

  /** Đóng process MCP: SIGTERM, đợi tối đa 2s, rồi SIGKILL. Gọi được nhiều lần. */
  async close() {
    const p = this.proc;
    if (!p || this.exited) return;
    try { p.stdin.end(); } catch { /* đã đóng */ }
    try { p.kill('SIGTERM'); } catch { /* đã chết */ }
    const deadline = Date.now() + 2000;
    while (!this.exited && Date.now() < deadline) await sleep(50);
    if (!this.exited) { try { p.kill('SIGKILL'); } catch { /* đã chết */ } }
  }
}

export function toolText(result) {
  return (result?.content || []).filter((c) => c.type === 'text').map((c) => c.text).join('\n');
}

/** evaluate_script trả "```json\n<JSON>\n```". Lấy khối cuối cùng, HTML bên trong có ``` cũng không vỡ. */
export function parseEvaluateResult(result) {
  const raw = toolText(result);
  const start = raw.indexOf('```json');
  const end = raw.lastIndexOf('```');
  const body = start >= 0 && end > start ? raw.slice(start + 7, end) : raw;
  try { return JSON.parse(body.trim()); } catch {
    throw new Error(`evaluate_script trả không phải JSON: ${raw.slice(0, 300)}`);
  }
}

/** list_pages → [{id, url}]. Ưu tiên structuredContent; không có thì parse text "ID: title (url)". */
export function pagesFromListResult(result) {
  const sc = result?.structuredContent?.pages;
  if (Array.isArray(sc)) return sc.map((p) => ({ id: Number(p.id), url: String(p.url || '') }));
  const out = [];
  for (const line of toolText(result).split('\n')) {
    const m = line.match(/^(\d+): (.*)$/);
    if (!m) continue;
    const label = m[2].replace(/ \[selected\]/, '').replace(/ isolatedContext=\S+$/, '');
    const u = label.match(/\((https?:\/\/.*)\)\s*$/);
    out.push({ id: Number(m[1]), url: u ? u[1] : label.trim() });
  }
  return out;
}

const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** URL chứa ĐÚNG marker (vd cdp-open=abc), không nhận marker dài hơn cùng tiền tố. */
export function urlHasMarker(url, marker) {
  return new RegExp(`[#&]${escRe(marker)}(?:&|$)`).test(String(url));
}

/** CMS redirect sang /v2/accessdeny khi profile đã đăng nhập nhưng không có quyền trang đó. */
export function isAccessDenyUrl(url) {
  return /\/v2\/accessdeny(?:[/?#]|$)/i.test(String(url));
}

/**
 * Mở URL trong đúng profile Chrome bằng `chrome-profile open --json --no-activate`.
 * Profile là tham số bắt buộc — không có mặc định, vì mở nhầm profile là ghi nhầm tài khoản.
 */
export function openProfileTab({ profile, url, execFileFn = nodeExecFile, bin = process.env.CHROME_PROFILE_BIN || 'chrome-profile' }) {
  if (!profile) throw new CliError('thiếu --profile (key chrome-profile có quyền CMS) — không có mặc định', 2);
  return new Promise((resolve, reject) => {
    execFileFn(bin, ['open', '--json', '--no-activate', profile, url], { timeout: 30000 }, (err, stdout) => {
      if (err) return reject(new CliError(`chrome-profile open lỗi: ${err.message}`));
      let j;
      try { j = JSON.parse(String(stdout).trim()); } catch {
        return reject(new CliError(`chrome-profile open không trả JSON: ${String(stdout).slice(0, 200)}`));
      }
      if (!j.bind_selector || !/^cdp-open=\S+$/.test(j.bind_selector)) {
        return reject(new CliError('chrome-profile open không trả bind_selector cdp-open=<token>'));
      }
      resolve(j);
    });
  });
}

/**
 * Bám tab theo URL-anchor: đúng 1 tab chứa đúng `cdp-open=<token>`, có `cdp-profile=<key>`,
 * và URL bắt đầu bằng `expectUrlPrefix`. Không có / nhiều hơn 1 / sai trang → từ chối.
 * Không bao giờ "lấy tab CMS đầu tiên".
 */
export async function bindProfileTab(client, { bindSelector, profileMarker, expectUrlPrefix, profile, attempts = 10, delayMs = 1000, sleepFn = sleep, listPagesTimeoutMs = 60000 }) {
  let pages = [];
  // list_pages là read-only (không POST) — đo 24/09/2026: đôi khi treo đúng 60s rồi gọi lại
  // NGAY SAU đó thành công (MCP CDP kẹt tạm thời), khác evaluate/POST không bao giờ được retry
  // vì có thể đã ghi. Cho thử lại ĐÚNG 1 LẦN cho CẢ vòng bind (không phải mỗi attempt) — khởi
  // động lại kết nối MCP trước khi thử, giữ tổng thời gian có giới hạn.
  let reconnectUsed = false;
  for (let i = 0; i < attempts; i++) {
    let listed;
    try {
      listed = await client.callTool('list_pages', {}, listPagesTimeoutMs);
    } catch (err) {
      if (!(err instanceof TimeoutError) || reconnectUsed) throw err;
      reconnectUsed = true;
      try { await client.close(); } catch { /* best-effort — proc có thể đã chết */ }
      await client.connect();
      listed = await client.callTool('list_pages', {}, listPagesTimeoutMs);
    }
    pages = pagesFromListResult(listed);
    const hits = pages.filter((p) => urlHasMarker(p.url, bindSelector));
    if (hits.length > 1) throw new CliError(`${hits.length} tab cùng chứa ${bindSelector} — không chọn bừa`);
    if (hits.length === 1) {
      const page = hits[0];
      if (profileMarker && !urlHasMarker(page.url, profileMarker)) {
        throw new CliError(`tab có ${bindSelector} nhưng thiếu ${profileMarker} — từ chối`);
      }
      if (expectUrlPrefix && !page.url.startsWith(expectUrlPrefix)) {
        const landedPath = page.url.split('#')[0];
        // /v2/accessdeny = đã đăng nhập nhưng profile không có quyền trang này — khác hẳn
        // "mất hash / văng ra trang đăng nhập". Tách riêng để agent không đi sửa nhầm hướng.
        if (isAccessDenyUrl(landedPath)) {
          const who = profile || (profileMarker ? profileMarker.replace(/^cdp-profile=/, '') : '?');
          throw new CliError(`profile ${who} không có quyền trang này (CMS redirect ${landedPath})`);
        }
        throw new CliError(`tab đúng token nhưng URL không phải trang cần (${landedPath}) — có thể CMS đòi đăng nhập`);
      }
      await client.callTool('select_page', { pageId: page.id, bringToFront: false });
      client.pageId = page.id;
      return page.id;
    }
    if (i < attempts - 1) await sleepFn(delayMs);
  }
  throw new CliError(`không thấy tab nào chứa ${bindSelector} sau ${attempts} lần list_pages — CMS có thể đã redirect sang trang đăng nhập (mất hash)`);
}

/**
 * Đóng đúng tab vừa mở bằng bindSelector khi bind thất bại (accessdeny, sai profile,
 * mất hash...). Chỉ đóng khi tìm thấy ĐÚNG 1 tab khớp token của lần mở này — không bao
 * giờ đoán bừa hay đóng tab CMS khác đang mở song song. Lỗi dọn dẹp không che lỗi gốc.
 */
async function closeOpenedTabOnBindFailure(client, bindSelector) {
  try {
    const pages = pagesFromListResult(await client.callTool('list_pages', {}));
    const hits = pages.filter((p) => urlHasMarker(p.url, bindSelector));
    if (hits.length === 1) await client.callTool('close_page', { pageId: hits[0].id }, 15000);
  } catch { /* best-effort: tab đã đóng, hoặc list_pages/close_page lỗi — không quan trọng bằng lỗi gốc */ }
}

/**
 * Mở + bám tab trong 1 bước. Trả { pageId, open }.
 * bind thất bại (redirect /accessdeny, sai profile, mất hash...) → tab vừa mở BỊ ĐÓNG
 * trước khi ném lỗi gốc, tránh rò tab (đo 24/09/2026: CMS redirect accessdeny làm tab
 * treo lại vĩnh viễn vì caller không có pageId để đóng).
 */
export async function openAndBind(client, { profile, url, expectUrlPrefix, execFileFn, sleepFn }) {
  const open = await openProfileTab({ profile, url, execFileFn });
  try {
    const pageId = await bindProfileTab(client, {
      bindSelector: open.bind_selector,
      profileMarker: open.profile_marker,
      expectUrlPrefix,
      profile,
      sleepFn,
    });
    return { pageId, open };
  } catch (err) {
    await closeOpenedTabOnBindFailure(client, open.bind_selector);
    throw err;
  }
}

/** Chạy 1 function trong tab đang chọn, trả JSON. Timeout riêng cho từng lần gọi. */
export async function evaluate(client, fnSource, timeoutMs) {
  const result = await client.callTool('evaluate_script', { function: fnSource, waitForStableDom: false }, timeoutMs);
  return parseEvaluateResult(result);
}

/** Dựng function evaluate: nạp runner (IIFE hoặc khai báo hàm) rồi chạy `tail`. */
export function withRunner(runnerCode, tail) {
  return `async () => {\n${runnerCode}\n;\n${tail}\n}`;
}

/** Đoạn JS tính sha256 hex của chuỗi trong trang — khớp sha256() phía Node. */
export const PAGE_SHA256 = `const __sha256 = async (s) => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map((b) => b.toString(16).padStart(2, '0')).join('');`;

/**
 * Tạo input[type=file] riêng (không name, không handler) có aria-label = id để
 * take_snapshot tìm được uid. KHÔNG chạm input có sẵn của trang (#allImagesNews,
 * #fileUploadContentNews có change handler → tự upload).
 */
export const makeInputFn = (id) => `() => { let el = document.getElementById(${JSON.stringify(id)});
  if (!el) { el = document.createElement('input'); el.type = 'file'; el.multiple = true; el.id = ${JSON.stringify(id)};
    el.setAttribute('aria-label', ${JSON.stringify(id)}); el.style.cssText = 'position:fixed;top:0;left:0;z-index:99999';
    document.body.appendChild(el); }
  return { id: el.id, hasName: !!el.name, inForm: !!el.closest('form') }; }`;

export const removeInputFn = (ids) => `() => { for (const id of ${JSON.stringify(ids)}) document.getElementById(id)?.remove(); return 'ok'; }`;

/** Tìm uid theo accessible name trong text snapshot. Phải khớp đúng 1 dòng. */
export function findUidByName(snapshotText, name) {
  const hits = String(snapshotText).split('\n').filter((l) => l.includes(`"${name}"`)).map((l) => (l.match(/uid=(\S+)/) || [])[1]).filter(Boolean);
  if (hits.length !== 1) throw new CliError(`snapshot có ${hits.length} phần tử tên "${name}" — cần đúng 1`);
  return hits[0];
}

/** Nạp file local vào input tự tạo bằng CDP upload_file (cơ chế hiện có của skill air). */
export async function uploadToOwnInput(client, inputId, filePaths) {
  const made = await evaluate(client, makeInputFn(inputId), 30000);
  if (made.hasName || made.inForm) throw new CliError(`input #${inputId} có name hoặc nằm trong form — sẽ lọt vào payload, dừng`);
  const snap = await client.callTool('take_snapshot', {}, 60000);
  const uid = findUidByName(toolText(snap), inputId);
  await client.callTool('upload_file', { uid, filePaths }, 120000);
  const n = await evaluate(client, `() => document.getElementById(${JSON.stringify(inputId)}).files.length`, 30000);
  if (n !== filePaths.length) throw new CliError(`input #${inputId} nhận ${n}/${filePaths.length} file`);
  return uid;
}
