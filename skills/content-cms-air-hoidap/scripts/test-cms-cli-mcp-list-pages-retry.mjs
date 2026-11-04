/**
 * Test cms-cli-mcp.mjs: list_pages (read-only, bind-phase) được retry ĐÚNG 1 LẦN sau timeout
 * bằng cách khởi động lại kết nối MCP — khác evaluate/POST không bao giờ được retry vì có thể
 * đã ghi. Đo thật 24/09/2026: CLI chết vì "quá 60s chờ tools/call list_pages", gọi lại NGAY
 * SAU đó thành công. Không trình duyệt, không CMS, không mạng.
 *   node .claude/skills/content-cms-air-hoidap/scripts/test-cms-cli-mcp-list-pages-retry.mjs
 */
import { EventEmitter } from 'node:events';
import { PassThrough, Writable } from 'node:stream';
import { McpClient, TimeoutError, bindProfileTab, evaluate } from './cms-cli-mcp.mjs';
import { createFakeMcp, pagesResult, never } from './cms-cli-fake-mcp.mjs';

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };
const rejects = async (p) => { try { await p; return null; } catch (e) { return e; } };

/**
 * cms-cli-fake-mcp.mjs dùng 1 `state.killed` DÙNG CHUNG cho mọi proc được spawn — đúng cho mọi
 * test khác (chỉ spawn 1 lần), nhưng SAI cho test reconnect (list_pages timeout → close() → spawn
 * proc MỚI): proc mới vẫn bị khoá bởi `killed=true` của proc cũ. Bản fake này tách `killed` RIÊNG
 * theo từng proc, chỉ dùng cho test list_pages retry (không sửa cms-cli-fake-mcp.mjs — file dùng
 * chung, ngoài phạm vi task).
 */
function createReconnectableFakeMcp({ tools = {} }) {
  const state = { calls: [], spawned: 0, procs: [] };
  state.spawnFn = () => {
    state.spawned++;
    const proc = new EventEmitter();
    const local = { killed: false };
    state.procs.push(local);
    proc.stdout = new PassThrough();
    proc.stderr = new PassThrough();
    const reply = (msg) => { if (!local.killed) proc.stdout.write(JSON.stringify(msg) + '\n'); };
    let buf = '';
    proc.stdin = new Writable({
      write(chunk, _enc, cb) {
        buf += chunk;
        let nl;
        while ((nl = buf.indexOf('\n')) >= 0) { const line = buf.slice(0, nl); buf = buf.slice(nl + 1); handle(JSON.parse(line)); }
        cb();
      },
    });
    async function handle(msg) {
      if (msg.id == null) return;
      if (msg.method === 'initialize') return reply({ jsonrpc: '2.0', id: msg.id, result: { protocolVersion: '2024-11-05', capabilities: {} } });
      if (msg.method === 'tools/list') return reply({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: 'no tools/list' } });
      if (msg.method !== 'tools/call') return reply({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: 'no method' } });
      const { name, arguments: args } = msg.params;
      state.calls.push({ name, args });
      const h = tools[name];
      if (!h) return reply({ jsonrpc: '2.0', id: msg.id, result: { content: [{ type: 'text', text: 'ok' }] } });
      try { reply({ jsonrpc: '2.0', id: msg.id, result: await h(args, state) }); }
      catch (e) { reply({ jsonrpc: '2.0', id: msg.id, result: { isError: true, content: [{ type: 'text', text: e.message }] } }); }
    }
    proc.kill = () => { if (local.killed) return true; local.killed = true; setImmediate(() => proc.emit('exit', 0)); return true; };
    return proc;
  };
  return state;
}

const TOKEN = 'abc123';
const PROFILE = 'prof';
const CMS_URL = `https://cms.thegioididong.com/v2/News/NewsEdit?newsId=111&siteId=1#cdp-profile=${PROFILE}&cdp-open=${TOKEN}`;

console.log('\n# list_pages timeout 1 lần rồi thành công → bind OK bằng cách khởi động lại kết nối MCP');
{
  let calls = 0;
  const fake = createReconnectableFakeMcp({ tools: { list_pages: () => { calls++; return calls === 1 ? never() : pagesResult([{ id: 7, url: CMS_URL }]); } } });
  const c = new McpClient({ spawnFn: fake.spawnFn });
  await c.connect();
  const pageId = await bindProfileTab(c, {
    bindSelector: `cdp-open=${TOKEN}`, profileMarker: `cdp-profile=${PROFILE}`,
    expectUrlPrefix: 'https://cms.thegioididong.com/v2/News/NewsEdit', attempts: 3, delayMs: 0, listPagesTimeoutMs: 30,
  });
  t('bind thành công sau khi list_pages timeout 1 lần rồi thử lại thành công', pageId === 7, pageId);
  t('list_pages được gọi đúng 2 lần (timeout + thử lại)', calls === 2, calls);
  t('MCP được khởi động lại đúng 1 lần (2 process spawn: ban đầu + reconnect)', fake.spawned === 2, fake.spawned);
  // Kết nối mới vẫn dùng được cho các tool khác sau khi bind xong (exited đã được reset).
  const ok = await c.callTool('select_page', { pageId: 7, bringToFront: false }, 1000).then(() => true, () => false);
  t('kết nối sau reconnect vẫn gọi tool khác được bình thường', ok);
  await c.close();
}

console.log('\n# list_pages timeout 2 lần liên tiếp → KHÔNG retry vòng 2 (giữ tổng thời gian có giới hạn)');
{
  let calls = 0;
  const fake = createReconnectableFakeMcp({ tools: { list_pages: () => { calls++; return never(); } } });
  const c = new McpClient({ spawnFn: fake.spawnFn });
  await c.connect();
  const e = await rejects(bindProfileTab(c, { bindSelector: `cdp-open=${TOKEN}`, attempts: 5, delayMs: 0, listPagesTimeoutMs: 30 }));
  t('timeout lần 2 (sau khi đã reconnect 1 lần) → ném lỗi, không lặp vô hạn', e instanceof TimeoutError, e);
  t('chỉ thử reconnect đúng 1 lần (2 lời gọi list_pages tổng cộng, không lặp tới hết 5 attempts)', calls === 2, calls);
  await c.close();
}

console.log('\n# evaluate (POST) KHÔNG bao giờ được retry khi timeout — dừng ngay, không gọi lại');
{
  let calls = 0;
  const fake = createFakeMcp({
    tools: {
      list_pages: () => pagesResult([{ id: 7, url: CMS_URL }]),
      evaluate_script: () => { calls++; return never(); },
    },
  });
  const c = new McpClient({ spawnFn: fake.spawnFn });
  await c.connect();
  await bindProfileTab(c, { bindSelector: `cdp-open=${TOKEN}`, attempts: 1, delayMs: 0 });
  const e = await rejects(evaluate(c, '() => 1', 30));
  t('evaluate timeout → TimeoutError, không tự retry', e instanceof TimeoutError, e);
  t('evaluate_script chỉ được gọi ĐÚNG 1 LẦN (không retry POST)', calls === 1, calls);
  await c.close();
}

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
