/**
 * test-mdm-g-slug.mjs — tra trang lọc `?g=slug`, chặn query lạ, cookie/header core mới (server giả, không mạng).
 *
 *   node .claude/skills/onpage-mdm-khai-bao/scripts/test-mdm-g-slug.mjs
 */
import { MdmError, parseWebUrl } from './mdm-core.mjs';
import { parseCatalogGSlugs, resolveGSlug, listingQuery } from './mdm-g-slug.mjs';
import { lookup } from './mdm-commands-lookup.mjs';
import { fetchCoreMoi } from './mdm-web-verify.mjs';

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };
const throwsCode = (fn, code) => { try { fn(); return false; } catch (e) { return e instanceof MdmError && e.exitCode === code; } };
const rejectsCode = async (p, code) => { try { await p; return false; } catch (e) { return e instanceof MdmError && e.exitCode === code; } };
const R = (data) => [{ locale: 'all', data }];

// HTML như core mới nhúng: dấu " bị escape thành \". Nhóm 448 và 374 cùng có giá trị mã 1 (attribute_value lặp giữa các dòng).
const child = (name, id, url) => `{\\"name\\":\\"${name}\\",\\"sortName\\":\\"\\",\\"filterId\\":${id},\\"logo\\":\\"https://x/y.png\\",\\"url\\":\\"${url}\\",\\"filterTypeId\\":1}`;
const group = (code, kids) => `{\\"filterTypeId\\":1,\\"name\\":\\"G${code}\\",\\"displayOrder\\":1,\\"attrbuteCode\\":\\"a\\",\\"quickFilter\\":false,\\"code\\":${code},\\"childFilter\\":[${kids.join(',')}]}`;
const HTML = `<html>...self.__next_f.push([1,"${[
  group(448, [child('Laptop AI', 29, 'ai'), child('Gaming', 108, 'g=laptop-gaming'), child('Học tập, văn phòng', 183, 'g=hoc-tap-van-phong')]),
  group(374, [child('IPS', 1, 'g=ips')]),
  group(500, [child('Trùng A', 7, 'g=trung'), ]),
  group(501, [child('Trùng B', 8, 'g=trung')]),
  group(448, [child('Gaming', 108, 'g=laptop-gaming')]),
].join(',')}"])</html>`;

console.log('\n# parseCatalogGSlugs');
{
  const m = parseCatalogGSlugs(HTML);
  t('slug g= gắn đúng nhóm + filterId', JSON.stringify(m.get('laptop-gaming')) === JSON.stringify([{ group: '448', filterId: '108', name: 'Gaming' }]));
  t('filterId trùng giữa nhóm: ips thuộc nhóm 374', m.get('ips')[0].group === '374' && m.get('ips')[0].filterId === '1');
  t('giá trị url không phải g= (ai) bị bỏ', !m.has('ai'));
  t('lặp trong HTML không nhân đôi', m.get('laptop-gaming').length === 1);
  t('slug thuộc 2 nhóm → 2 mục', m.get('trung').length === 2);
  t('HTML không có catalog → map rỗng', parseCatalogGSlugs('<html></html>').size === 0);
}

console.log('\n# listingQuery / parseWebUrl');
{
  t('?g=slug', parseWebUrl('/laptop?g=laptop-gaming', 'https://x.vn').g === 'laptop-gaming');
  t('không query → g null', parseWebUrl('/laptop', 'https://x.vn').g === null);
  t('tham số theo dõi bị bỏ qua (kể cả dấu vết &amp;)', parseWebUrl('/laptop-a?itm_source=a&amp%3Bitm_medium=b&utm_x=1&clearcache=1', 'https://x.vn').g === null);
  t('?p= → exit 2', throwsCode(() => parseWebUrl('/laptop?p=10-15-trieu', 'https://x.vn'), 2));
  t('query lạ → exit 2', throwsCode(() => parseWebUrl('/laptop?sort=1', 'https://x.vn'), 2));
  t('g rỗng → exit 2', throwsCode(() => listingQuery(new URLSearchParams('g=')), 2));
  t('2 tham số g → exit 2', throwsCode(() => listingQuery(new URLSearchParams('g=a&g=b')), 2));
  t('trang sản phẩm không kiểm query', parseWebUrl('/laptop/may-1?p=1', 'https://x.vn').kind === 'product');
}

console.log('\n# resolveGSlug');
{
  const m = parseCatalogGSlugs(HTML);
  const V = [
    { id: 'V-448-108', recordCode: '448', attributeValue: '108' },
    { id: 'V-374-1', recordCode: '374', attributeValue: '1' },
    { id: 'V-448-1', recordCode: '448', attributeValue: '1' }, // cùng attribute_value 1, khác dòng
  ];
  t('khớp (dòng, attribute_value)', resolveGSlug('laptop-gaming', m, V).id === 'V-448-108');
  t('attribute_value lặp: ips chọn đúng dòng 374', resolveGSlug('ips', m, V).id === 'V-374-1');
  t('slug không có trong catalog → exit 5', throwsCode(() => resolveGSlug('khong-co', m, V), 5));
  t('slug thuộc nhiều nhóm → exit 2', throwsCode(() => resolveGSlug('trung', m, V), 2));
  t('catalog có nhưng MDM thiếu giá trị → exit 5', throwsCode(() => resolveGSlug('hoc-tap-van-phong', m, V), 5));
  t('MDM có 2 bản ghi khớp → exit 2', throwsCode(() => resolveGSlug('laptop-gaming', m, [...V, { id: 'DUP', recordCode: '448', attributeValue: '108' }]), 2));
}

console.log('\n# lookup ?g= trên server giả');
{
  const CFG = {
    category: { objectId: 'OBJ-C', tableId: 'TBL-C', functionId: 'FN-C', rootId: 'ROOT' },
    brand: { objectId: 'OBJ-B', tableId: 'TBL-B', functionId: 'FN-B' },
    filter: { objectId: 'OBJ-F', tableId: 'TBL-F', functionId: 'FN-F', relationId: 'REL-F' },
    webOrigin: 'https://www.example.vn',
  };
  const records = { 'V-448-108': { id: 'V-448-108', rowVersion: 6, dataObjectId: 'LINE-448', rawValues: { title: R('T cũ'), description: R('D'), filter_type_attribute_code: R('448'), attribute_value: R('108') } } };
  const lines = [{ id: 'LINE-448', record_code: '448', name: 'Loại sản phẩm' }, { id: 'LINE-374', record_code: '374', name: 'Tấm nền' }];
  const values = {
    'LINE-448': [{ id: 'V-448-108', record_code: '2', name: 'Gaming', raw: { attribute_value: R('108') } }, { id: 'V-448-1', record_code: '9', name: 'X', raw: { attribute_value: R('1') } }],
    'LINE-374': [{ id: 'V-374-1', record_code: '1', name: 'IPS', raw: { attribute_value: R('1') } }],
  };
  const brands = [{ id: 'B-APPLE', record_code: '5', url: 'apple', name: 'Apple', isActivated: true }];
  const fake = {
    async post(api, p, body) {
      if (p === 'datatobject/getlistbyroot') return { object: [{ id: 'CAT', name: 'Laptop', lvl: 1, record_code: '17', raw: { url: R('laptop'), code: R('17'), cms_category_id: R(44) } }].map((r) => ({ ...r, raw: Object.fromEntries(Object.entries(r.raw).map(([k, v]) => [k, v])) })) };
      if (p === 'dataobject/getlist' && body.objectCode === 'tgdd_brand_category') return { object: brands };
      if (p === 'dataobject/getlist') return { object: lines };
      if (p === 'datarelation/getinfor') return { object: JSON.parse(JSON.stringify(records[body.dataRelation.id])) };
      throw new Error(`gọi ngoài dự kiến: ${p}`);
    },
    async run(ops) { return ops.map((o) => ({ ok: true, status: 200, json: { object: values[o.body.dataObjectId] || [] } })); },
  };
  // getlistbyroot trả field raw dạng mảng locale như runner thật (val() đọc rawGet) → dùng shape rawValues
  fake.post = ((orig) => async (api, p, body) => {
    const r = await orig(api, p, body);
    if (p === 'datatobject/getlistbyroot') r.object = r.object.map((x) => ({ ...x, raw_values: x.raw }));
    return r;
  })(fake.post);
  const page = (server, version) => ({ status: 200, text: async () => HTML, headers: { get: (k) => (k === 'x-app-server' ? server : k === 'x-version' ? version : null) } });
  const seq = [page('BE-Web-80', 'Mwg-1'), page('BE-webfe-tmdt-tgdd.vn-80', null)];
  let calls = 0;
  const fetchFn = async () => seq[Math.min(calls++, seq.length - 1)];
  try {
    const r = await lookup(fake, CFG, 'https://www.example.vn/laptop?g=laptop-gaming', fetchFn);
    t('?g= → filter-value đúng id, variant filter-g', r.screen === 'filter-value' && r.id === 'V-448-108' && r.variant === 'filter-g' && r.rowVersion === 6, JSON.stringify(r));
    t('lấy lại trang khi rơi node core cũ', calls === 2);
    t('hiện giá trị SEO hiện tại', r.current.title.value === 'T cũ');
  } catch (e) { t('lookup ?g= chạy được', false, e.message); }
  t('?p= bị chặn trước khi gọi server', await rejectsCode(lookup(fake, CFG, '/laptop?p=10-15-trieu', fetchFn), 2));
  try {
    const b = await lookup(fake, CFG, '/laptop-apple?g=laptop-gaming', fetchFn);
    t('hãng + ?g= → filter-value variant brand-filter kèm hãng', b.id === 'V-448-108' && b.variant === 'brand-filter' && b.brand.id === 'B-APPLE', JSON.stringify(b));
  } catch (e) { t('lookup hãng + ?g= chạy được', false, e.message); }
  t('đường dẫn không phải ngành hàng/hãng + ?g= → không đoán', await rejectsCode(lookup(fake, CFG, '/laptop-khong-co?g=laptop-gaming', fetchFn), 5));
}

console.log('\n# fetchCoreMoi: cookie + nhận diện core');
{
  let sent;
  const mk = (server, version) => async (url, opt) => { sent = opt.headers.Cookie; return { status: 200, text: async () => '', headers: { get: (k) => (k === 'x-app-server' ? server : k === 'x-version' ? version : null) } }; };
  t('core mới: x-app-server webfe, không x-version', (await fetchCoreMoi('u', mk('BE-webfe-tmdt-tgdd.vn-80', null))).coreMoi === true);
  t('gửi cookie webmoi_v3=2 (v2 cũ cho core ngược)', sent === 'webmoi_v3=2');
  t('core cũ: BE-Web-80 + x-version → không phải core mới', (await fetchCoreMoi('u', mk('BE-Web-80', 'Mwg-6.9'))).coreMoi === false);
  t('x-app-server không phải webfe dù thiếu x-version → không phải core mới', (await fetchCoreMoi('u', mk('BE-Web-80', null))).coreMoi === false);
  t('không có header nào → dựa x-version (như trước)', (await fetchCoreMoi('u', mk(null, null))).coreMoi === true);
}

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
