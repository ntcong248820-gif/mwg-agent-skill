/**
 * cms-cli-fake-mcp.mjs — MCP giả nói JSON-RPC qua stdio giả, CHỈ dùng cho test CLI CMS.
 * Không mở trình duyệt, không gọi mạng. BẢN COPY Y HỆT trong scripts/ của các skill CMS.
 *
 *   const fake = createFakeMcp({ tools: { list_pages: (args, st) => ({...}), evaluate_script: ... } });
 *   main(argv, { spawnFn: fake.spawnFn, execFileFn: fakeChromeProfile('tok1', 'prof') })
 *   fake.calls  → [{ name, args }] mọi tool đã gọi;  fake.killed → process đã bị đóng chưa.
 * Handler trả Promise không bao giờ resolve = giả lập evaluate treo (timeout).
 */

import { EventEmitter } from 'node:events';
import { PassThrough, Writable } from 'node:stream';

export const textResult = (text) => ({ content: [{ type: 'text', text }] });
export const evalResult = (obj) => textResult('Script ran on page and returned:\n```json\n' + JSON.stringify(obj) + '\n```');
export const pagesResult = (pages) => textResult('## Pages\n' + pages.map((p) => `${p.id}: ${p.title || 'CMS'} (${p.url})`).join('\n'));
export const never = () => new Promise(() => {});

/** Schema giống chrome-devtools-mcp 1.8 bật pageIdRouting (pageId bắt buộc ở tool page-scoped). */
export const PAGE_ROUTED_SCHEMAS = {
  list_pages: [], select_page: ['pageId', 'bringToFront'], close_page: ['pageId'],
  evaluate_script: ['pageId', 'function', 'args', 'filePath', 'dialogAction', 'waitForStableDom'],
  take_snapshot: ['pageId', 'verbose', 'filePath'], upload_file: ['pageId', 'uid', 'filePaths', 'includeSnapshot'],
};

export function createFakeMcp({ tools = {}, schemas = PAGE_ROUTED_SCHEMAS } = {}) {
  const state = { calls: [], killed: false, spawned: 0 };
  state.spawnFn = () => {
    state.spawned++;
    const proc = new EventEmitter();
    proc.stdout = new PassThrough();
    proc.stderr = new PassThrough();
    const reply = (msg) => { if (!state.killed) proc.stdout.write(JSON.stringify(msg) + '\n'); };
    let buf = '';
    proc.stdin = new Writable({
      write(chunk, _enc, cb) {
        buf += chunk;
        let nl;
        while ((nl = buf.indexOf('\n')) >= 0) {
          const line = buf.slice(0, nl);
          buf = buf.slice(nl + 1);
          handle(JSON.parse(line));
        }
        cb();
      },
    });
    async function handle(msg) {
      if (msg.id == null) return; // notification
      if (msg.method === 'initialize') return reply({ jsonrpc: '2.0', id: msg.id, result: { protocolVersion: '2024-11-05', capabilities: {} } });
      if (msg.method === 'tools/list') {
        if (!schemas) return reply({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: 'no tools/list' } });
        return reply({ jsonrpc: '2.0', id: msg.id, result: { tools: Object.entries(schemas).map(([name, props]) => ({ name, inputSchema: { type: 'object', properties: Object.fromEntries(props.map((k) => [k, {}])) } })) } });
      }
      if (msg.method !== 'tools/call') return reply({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: 'no method' } });
      const { name, arguments: args } = msg.params;
      state.calls.push({ name, args });
      // Như server thật: tham số lạ → isError; thiếu pageId khi schema đòi → isError.
      const props = schemas?.[name];
      if (props) {
        const unknown = Object.keys(args || {}).filter((k) => !props.includes(k));
        if (unknown.length) return reply({ jsonrpc: '2.0', id: msg.id, result: { isError: true, content: [{ type: 'text', text: `unknown args ${unknown}` }] } });
        if (props.includes('pageId') && name !== 'list_pages' && typeof args.pageId !== 'number') return reply({ jsonrpc: '2.0', id: msg.id, result: { isError: true, content: [{ type: 'text', text: 'pageId required' }] } });
      }
      const h = tools[name];
      if (!h) return reply({ jsonrpc: '2.0', id: msg.id, result: textResult('ok') });
      try {
        const result = await h(args, state);
        reply({ jsonrpc: '2.0', id: msg.id, result });
      } catch (e) {
        reply({ jsonrpc: '2.0', id: msg.id, result: { isError: true, content: [{ type: 'text', text: e.message }] } });
      }
    }
    proc.kill = () => {
      if (state.killed) return true;
      state.killed = true;
      setImmediate(() => proc.emit('exit', 0));
      return true;
    };
    return proc;
  };
  return state;
}

/** chrome-profile giả: trả JSON bind_selector như `chrome-profile open --json`. */
export function fakeChromeProfile(token, profile, calls = []) {
  return (bin, args, _opts, cb) => {
    calls.push({ bin, args });
    const url = args[args.length - 1];
    cb(null, JSON.stringify({
      bind_selector: `cdp-open=${token}`,
      open_marker: `cdp-open=${token}`,
      opened_url: `${url}#cdp-profile=${profile}&cdp-open=${token}`,
      profile_key: profile,
      profile_marker: `cdp-profile=${profile}`,
    }));
  };
}
