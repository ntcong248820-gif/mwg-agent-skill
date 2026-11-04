#!/usr/bin/env node
/**
 * newcms-auth.mjs — giữ access token NEW CMS (newcms.thegioididong.com) sống lâu nhất có thể
 * bằng refresh trượt của Keycloak, để các skill gọi API bus/cms không cần mở tab mỗi lần.
 *
 * Cơ chế (đo 02/11/2026, realm mwg-central, client web-new-cms):
 * - access token 12h, refresh token 7 ngày; mỗi lần refresh được refresh token MỚI với hạn
 *   trượt về đủ 7 ngày (cùng sid). Trần cuối là SSO Session Max của realm — chưa đo được.
 * - refresh token CŨ vẫn dùng được sau khi xoay (realm không bật Revoke Refresh Token), nên
 *   chuỗi token của script tách khỏi chuỗi của tab: refresh ở đây không làm tab rớt phiên,
 *   và mỗi lần refresh còn giữ sống luôn phiên (session idle) của tab.
 *
 * Seed: lấy refresh token + cấu hình client từ tab newcms đã đăng nhập (qua chrome-devtools-mcp,
 * không qua chat), refresh 1 lần để có chuỗi riêng, lưu file 0600 ngoài repo.
 *
 * KHÔNG in token, refresh token hay client secret ra stdout/stderr. Chỉ in hạn còn lại.
 * Muốn dùng token: import { getAccessToken } trong script Node, đừng pipe qua shell.
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { McpClient, openAndBind, evaluate, CliError } from './cms-cli-mcp.mjs';

export const NEWCMS_ORIGIN = 'https://newcms.thegioididong.com';
export const API_BASE = 'https://webapi.thegioididong.com/gw/bus/cms';
export const SESSION_FILE = process.env.NEWCMS_AUTH_FILE || path.join(os.homedir(), '.config', 'newcms-auth', 'session.json');
const LAUNCH_LABEL = 'com.mwg.newcms-auth-keepalive';
const PLIST = path.join(os.homedir(), 'Library', 'LaunchAgents', `${LAUNCH_LABEL}.plist`);
const LOG_FILE = path.join(os.homedir(), 'Library', 'Logs', 'newcms-auth-keepalive.log');
const HERE = path.dirname(fileURLToPath(import.meta.url));

/**
 * Profile mặc định: khoá `cms.chromeProfiles.<which>` (newcms; CMS cũ: faq) trong harness.config.json (tìm harness/ đi ngược
 * từ thư mục script rồi cwd, như mdm-cli). Không có repo/khoá thì trả null → bắt buộc --profile.
 */
export async function harnessChromeProfile(which = 'newcms') {
  for (const start of [HERE, process.cwd()]) {
    for (let d = start; d !== path.dirname(d); d = path.dirname(d)) {
      const f = path.join(d, 'harness', 'harness-config.mjs');
      if (!fs.existsSync(f)) continue;
      try {
        const { loadHarnessConfig } = await import(pathToFileURL(f).href);
        return loadHarnessConfig({ optional: true })?.get?.(`cms.chromeProfiles.${which}`) ?? null;
      } catch { return null; }
    }
  }
  return null;
}

/** Đọc claim của JWT (không verify chữ ký — chỉ để biết exp/iat/sid). */
export function jwtClaims(jwt) {
  try { return JSON.parse(Buffer.from(String(jwt).split('.')[1], 'base64url').toString('utf8')); } catch { return null; }
}

const hoursLeft = (exp) => (exp ? (exp * 1000 - Date.now()) / 3600000 : null);

export function readSession(file = SESSION_FILE) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; }
}

/** Ghi atomic, thư mục 0700, file 0600 — đây là credential. */
export function writeSession(s, file = SESSION_FILE) {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(s, null, 2), { mode: 0o600 });
  fs.renameSync(tmp, file);
  fs.chmodSync(file, 0o600);
}

/** Gộp kết quả /token vào session, giữ lại cấu hình client + danh tính. */
function mergeTokenResponse(s, v) {
  const a = jwtClaims(v.access_token);
  const r = jwtClaims(v.refresh_token);
  return {
    ...s,
    access_token: v.access_token,
    refresh_token: v.refresh_token || s.refresh_token,
    access_exp: a?.exp ?? Math.floor(Date.now() / 1000) + Number(v.expires_in || 0),
    refresh_exp: r?.exp ?? (v.refresh_expires_in ? Math.floor(Date.now() / 1000) + Number(v.refresh_expires_in) : s.refresh_exp),
    sid: r?.sid ?? s.sid,
    refreshed_at: new Date().toISOString(),
  };
}

/** Refresh bằng refresh token đang lưu. invalid_grant → CliError exit 3 (phải seed lại). */
export async function refreshSession({ file = SESSION_FILE, fetchFn = fetch } = {}) {
  const s = readSession(file);
  if (!s?.refresh_token) throw new CliError(`chưa có session — chạy: node newcms-auth.mjs seed [--profile <key>]`, 3);
  const body = new URLSearchParams({ grant_type: 'refresh_token', client_id: s.clientId, refresh_token: s.refresh_token });
  if (s.clientSecret) body.set('client_secret', s.clientSecret);
  const res = await fetchFn(s.tokenEndpoint, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
  const v = await res.json().catch(() => ({}));
  if (!res.ok) {
    const code = v.error === 'invalid_grant' || v.error === 'unauthorized_client' ? 3 : 1;
    throw new CliError(`refresh lỗi HTTP ${res.status}: ${v.error || ''} ${v.error_description || ''}`.trim(), code);
  }
  const next = mergeTokenResponse(s, v);
  writeSession(next, file);
  return next;
}

/**
 * Khoá chống seed song song (nhiều skill cùng lúc thấy thiếu token → chỉ 1 cái mở tab).
 * Khoá là thư mục; quá staleMs thì coi như process giữ khoá đã chết.
 */
async function withSeedLock(file, fn, { staleMs = 12 * 60000, waitMs = 12 * 60000 } = {}) {
  const lock = `${file}.seed.lock`;
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const deadline = Date.now() + waitMs;
  let waited = false;
  for (;;) {
    try { fs.mkdirSync(lock); break; } catch {
      let age = 0;
      try { age = Date.now() - fs.statSync(lock).mtimeMs; } catch {
        if (waited) return null; // process khác vừa seed xong và nhả khoá → caller đọc lại session
        continue;
      }
      if (age > staleMs) { fs.rmSync(lock, { recursive: true, force: true }); continue; }
      if (Date.now() > deadline) throw new CliError('chờ process khác seed token quá lâu', 3);
      waited = true;
      await new Promise((ok) => setTimeout(ok, 2000));
    }
  }
  try { return await fn(); } finally { fs.rmSync(lock, { recursive: true, force: true }); }
}

/** Seed tự động: profile lấy từ session cũ, không có thì harness.config. Log ra stderr. */
async function autoSeed(file) {
  const startedAt = new Date().toISOString();
  const profile = readSession(file)?.profile || (await harnessChromeProfile());
  const seeded = await withSeedLock(file, () => {
    // Vào được khoá nhưng process khác vừa seed xong trước đó → dùng luôn, không mở tab lần 2.
    const cur = readSession(file);
    if (cur?.refresh_token && cur.seeded_at > startedAt) return cur;
    return seedFromProfile({ profile, file, log: console.error });
  });
  return seeded || readSession(file);
}

/**
 * Trả access token còn hạn ≥ minLeftSec. Tự lo hết: chưa có session → seed từ tab; sắp hết hạn →
 * refresh; refresh token hỏng/hết hạn (exit 3) → seed lại. Chỉ ném lỗi khi Chrome đã đăng xuất
 * newcms và không ai đăng nhập lại trong thời gian chờ.
 *   const token = await getAccessToken();
 */
export async function getAccessToken({ minLeftSec = 900, file = SESSION_FILE, fetchFn = fetch, autoSeedOnFail = true } = {}) {
  let s = readSession(file);
  if (!s?.refresh_token) {
    if (!autoSeedOnFail) throw new CliError('chưa có session newcms', 3);
    s = await autoSeed(file);
  }
  if (!s?.access_token || (s.access_exp || 0) - Date.now() / 1000 < minLeftSec) {
    try {
      s = await refreshSession({ file, fetchFn });
    } catch (e) {
      if (e.exitCode !== 3 || !autoSeedOnFail) throw e;
      console.error(`refresh token newcms hỏng (${e.message}) → seed lại từ tab`);
      s = await autoSeed(file);
    }
  }
  return s.access_token;
}

/**
 * fetch tới API bus/cms có sẵn Bearer. `p` là path (`/api/v1/...`) hoặc URL đầy đủ.
 * Gặp 401 thì ép refresh (hỏng thì seed lại) và gọi lại đúng 1 lần.
 */
export async function newcmsFetch(p, init = {}, { file = SESSION_FILE } = {}) {
  const url = /^https?:/.test(p) ? p : `${API_BASE}${p}`;
  const call = async (token) => fetch(url, { ...init, headers: { ...(init.headers || {}), Authorization: `Bearer ${token}` } });
  let res = await call(await getAccessToken({ file }));
  if (res.status !== 401) return res;
  const s = readSession(file);
  if (s) writeSession({ ...s, access_exp: 0 }, file); // ép getAccessToken refresh
  return call(await getAccessToken({ file }));
}

/** Chạy trong tab newcms: đọc user_info + cấu hình Keycloak employee từ bundle đang nạp. */
const SEED_FN = `async () => {
  const u = JSON.parse(localStorage.getItem('user_info') || 'null');
  if (!u || !u.refresh_token) return { ok: false, reason: 'tab không có user_info.refresh_token (chưa đăng nhập newcms?)', url: location.href };
  const src = [...document.scripts].map((s) => s.src).find((s) => /\\/assets\\/index-[^/]+\\.js$/.test(s));
  if (!src) return { ok: false, reason: 'không thấy bundle assets/index-*.js', url: location.href };
  const t = await (await fetch(src)).text();
  // Tên biến minify đổi mỗi lần deploy (02/11: Gw → khác) — bám theo nội dung: object Keycloak của realm nhân viên (authkey.dmx.vn).
  const m = t.match(/\\{url:\`(https:\\/\\/authkey\\.dmx\\.vn\\/?)\`,realm:\`([^\`]+)\`,clientId:\`([^\`]+)\`,clientSecret:\`([^\`]*)\`/);
  if (!m) return { ok: false, reason: 'không tìm thấy cấu hình Keycloak authkey.dmx.vn trong bundle — app đã đổi cách cấu hình?', url: location.href };
  return { ok: true, url: location.href, refresh_token: u.refresh_token, username: u.username || '', fullname: u.fullname || '',
    authVariant: u.authVariant || 'employee', kc: { url: m[1], realm: m[2], clientId: m[3], clientSecret: m[4] } };
}`;

/**
 * Seed từ tab newcms của profile Chrome chỉ định, rồi refresh 1 lần để có chuỗi token riêng.
 * Profile đã đăng xuất newcms → đưa tab login ra trước + bắn notification, chờ người đăng nhập
 * tối đa `waitLoginMs` (agent không tự nhập mật khẩu), rồi lấy token luôn trong tab đó.
 */
export async function seedFromProfile({ profile, file = SESSION_FILE, log = console.log, waitLoginMs = Number(process.env.NEWCMS_WAIT_LOGIN_MS || 10 * 60000) } = {}) {
  if (!profile) throw new CliError('thiếu --profile (key chrome-profile đã đăng nhập newcms) và harness.config.json chưa có cms.chromeProfiles.newcms', 2);
  const client = new McpClient({ roots: [HERE] });
  await client.connect();
  let pageId = null;
  try {
    ({ pageId } = await openAndBind(client, { profile, url: `${NEWCMS_ORIGIN}/Faq/News`, expectUrlPrefix: NEWCMS_ORIGIN }));
    let r = null;
    let askedLogin = false;
    // SPA cần vài giây để Keycloak nạp xong user_info sau khi load; trang login thì chờ người đăng nhập.
    const deadline = Date.now() + 15000;
    let loginDeadline = 0;
    for (;;) {
      r = await evaluate(client, SEED_FN, 30000).catch((e) => ({ ok: false, reason: e.message, url: '' }));
      if (r.ok) break;
      if (/loginv2|authkey\./.test(r.url || '')) {
        if (!askedLogin) {
          askedLogin = true;
          loginDeadline = Date.now() + waitLoginMs;
          await client.callTool('select_page', { pageId, bringToFront: true }).catch(() => {});
          notify(`Đăng nhập NEW CMS trong Chrome (profile ${profile}) để skill chạy tiếp`);
          log(`newcms chưa đăng nhập ở profile ${profile} — đã mở trang login, chờ tối đa ${Math.round(waitLoginMs / 60000)} phút…`);
        }
        if (Date.now() > loginDeadline) break;
      } else if (!askedLogin && Date.now() > deadline) break;
      await new Promise((ok) => setTimeout(ok, 3000));
    }
    if (!r?.ok) throw new CliError(`seed thất bại: ${r?.reason || 'không rõ'} (tab: ${r?.url || '?'}) — đăng nhập newcms trong profile ${profile} rồi chạy lại`, 3);
    if (r.authVariant !== 'employee') throw new CliError(`tài khoản dạng ${r.authVariant}, script chỉ hỗ trợ employee`, 2);
    const base = {
      profile,
      username: r.username,
      fullname: r.fullname,
      clientId: r.kc.clientId,
      clientSecret: r.kc.clientSecret,
      tokenEndpoint: `${r.kc.url.replace(/\/$/, '')}/realms/${r.kc.realm}/protocol/openid-connect/token`,
      refresh_token: r.refresh_token,
      seeded_at: new Date().toISOString(),
    };
    writeSession(base, file);
    const s = await refreshSession({ file });
    log(`seed OK (${s.username}) — ${fmtStatus(s)}`);
    return s;
  } finally {
    if (pageId != null) await client.callTool('close_page', { pageId }, 15000).catch(() => {});
    await client.close().catch(() => {});
  }
}

export function fmtStatus(s) {
  const a = hoursLeft(s.access_exp);
  const r = hoursLeft(s.refresh_exp);
  return `access còn ${a?.toFixed(1)}h, refresh còn ${r?.toFixed(1)}h (${(r / 24).toFixed(1)} ngày), refresh lần cuối ${s.refreshed_at || '-'}`;
}

function notify(msg) {
  execFile('osascript', ['-e', `display notification ${JSON.stringify(msg)} with title "NEW CMS token"`], () => {});
}

/** Lịch: refresh; hỏng thì thử seed lại từ profile đã lưu; vẫn hỏng thì báo notification. */
export async function keepalive() {
  try {
    const s = await refreshSession();
    console.log(`${new Date().toISOString()} refresh OK — ${fmtStatus(s)}`);
  } catch (e) {
    console.error(`${new Date().toISOString()} refresh lỗi: ${e.message}`);
    try { await autoSeed(SESSION_FILE); return; } catch (e2) { console.error(`seed lại lỗi: ${e2.message}`); }
    notify('Token NEW CMS hết hạn — đăng nhập newcms, lần chạy skill sau sẽ tự lấy lại');
    process.exitCode = 3;
  }
}

export function installKeepalive(intervalHours) {
  const node = process.execPath;
  const script = fileURLToPath(import.meta.url);
  const plist = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>${LAUNCH_LABEL}</string>
  <key>ProgramArguments</key><array><string>${node}</string><string>${script}</string><string>keepalive</string></array>
  <key>StartInterval</key><integer>${Math.round(intervalHours * 3600)}</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>${LOG_FILE}</string>
  <key>StandardErrorPath</key><string>${LOG_FILE}</string>
</dict></plist>
`;
  fs.mkdirSync(path.dirname(PLIST), { recursive: true });
  fs.writeFileSync(PLIST, plist);
  const uid = process.getuid();
  return new Promise((resolve) => {
    execFile('launchctl', ['bootout', `gui/${uid}/${LAUNCH_LABEL}`], () => {
      execFile('launchctl', ['bootstrap', `gui/${uid}`, PLIST], (err) => {
        if (err) console.error(`launchctl bootstrap lỗi: ${err.message}`);
        else console.log(`đã cài ${LAUNCH_LABEL}: refresh mỗi ${intervalHours}h, log ${LOG_FILE}`);
        resolve();
      });
    });
  });
}

export function uninstallKeepalive() {
  return new Promise((resolve) => {
    execFile('launchctl', ['bootout', `gui/${process.getuid()}/${LAUNCH_LABEL}`], () => {
      fs.rmSync(PLIST, { force: true });
      console.log(`đã gỡ ${LAUNCH_LABEL}`);
      resolve();
    });
  });
}

async function main(argv) {
  const [cmd, ...rest] = argv;
  const opt = (name) => { const i = rest.indexOf(name); return i >= 0 ? rest[i + 1] : undefined; };
  if (cmd === 'seed') return void (await seedFromProfile({ profile: opt('--profile') || (await harnessChromeProfile()) }));
  if (cmd === 'ensure') {
    await getAccessToken();
    return void console.log(`OK — ${fmtStatus(readSession())}`);
  }
  if (cmd === 'refresh') return void console.log(`refresh OK — ${fmtStatus(await refreshSession())}`);
  if (cmd === 'status') {
    const s = readSession();
    return void console.log(s ? `${s.username} (profile ${s.profile}) — ${fmtStatus(s)}` : 'chưa có session');
  }
  if (cmd === 'keepalive') return keepalive();
  if (cmd === 'install-keepalive') return installKeepalive(Number(opt('--every-hours') || 24));
  if (cmd === 'uninstall-keepalive') return uninstallKeepalive();
  console.log('Dùng: newcms-auth.mjs ensure | seed [--profile <key>] | refresh | status | keepalive | install-keepalive [--every-hours 24] | uninstall-keepalive');
  process.exitCode = cmd ? 2 : 0;
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url))) {
  main(process.argv.slice(2)).catch((e) => { console.error(e.message); process.exitCode = e.exitCode || 1; });
}
