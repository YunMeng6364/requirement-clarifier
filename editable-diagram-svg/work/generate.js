const fs = require('fs');
const ROOT = 'd:/GitHub/requirement-clarifier/editable-diagram-svg';
const OUT = ROOT + '/work';

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const parts = [], texts = [], visible = [], nodesAcc = [], groupsAcc = [];
function V(id) { if (!visible.includes(id)) visible.push(id); return id; }
function T(id, value, region, fill, x, y, size, extra) {
  texts.push({ id, value, region, fill });
  V(id);
  return `<text id="${id}" data-content-id="${id}" x="${x}" y="${y}" font-size="${size}" fill="${fill}"${extra ? ' ' + extra : ''}>${esc(value)}</text>`;
}
function RG(id, bounds, inner) {
  V(id);
  return `<g id="${id}" data-region="${id}" data-bounds="${bounds}">${inner}</g>`;
}

const TITLE = '常用 AI Skill 索引 · 仓库架构';
const DESC = '仓库根目录的文件结构，以及 README 收录的 9 个 Skill 条目按来源分成三组；实线表示索引收录，虚线表示本仓库维护 Skill 的源码目录对应。使用环节为按需组合，不是自动编排。';

const rootCards = [
  { id: 'node-file-readme', name: 'README.md', desc: '中文索引', icon: 'icon-document', x: 84 },
  { id: 'node-file-readme-en', name: 'README.en.md', desc: 'English index', icon: 'icon-document', x: 438 },
  { id: 'node-file-license', name: 'LICENSE', desc: 'MIT', icon: 'icon-shield', x: 792 },
  { id: 'node-dir-req', name: 'requirement-clarifier/', desc: '本仓库维护', icon: 'icon-package', x: 1146 },
  { id: 'node-dir-svg', name: 'editable-diagram-svg/', desc: '本仓库维护', icon: 'icon-package', x: 1500 },
].map(c => ({ ...c, y: 260, w: 336, h: 74 }));

const localCards = [
  { id: 'node-01', name: '① requirement-clarifier', desc: '开工前：理清需求', icon: null, x: 84, y: 532, w: 502, h: 206 },
  { id: 'node-02', name: '② editable-diagram-svg', desc: '图示交付：可编辑 SVG', icon: 'icon-edit', x: 84, y: 758, w: 502, h: 206 },
];
const externalCards = [
  { id: 'node-03', name: '③ grill-me（RobMitt 版）', desc: '方案成形后：逐项追问', x: 654 },
  { id: 'node-04', name: '④ grill-me（zhudan930612 版）', desc: '方案 / 文档：压力测试', x: 654 },
  { id: 'node-05', name: '⑤ karpathy-guidelines', desc: '编码：约束实现', x: 654 },
  { id: 'node-06', name: '⑥ ponytail', desc: '编码：减少不必要代码', x: 654 },
  { id: 'node-07', name: '⑦ i-have-adhd', desc: '执行中：降低阅读负担', x: 654 },
  { id: 'node-08', name: '⑧ guizang-ppt-skill', desc: '演示交付：网页 PPT', x: 654 },
].map((c, i) => ({ ...c, icon: null, y: 532 + i * 72, w: 612, h: 67 }));
const collectionCards = [
  { id: 'node-09', name: '⑨ mattpocock/skills', desc: '按需工程步骤', icon: 'icon-layers', x: 1334, y: 645, w: 502, h: 206 },
];

const GROUPS = [
  { id: 'group-root', x: 60, y: 180, w: 1800, h: 170, title: '仓库根 · 索引与源码', titleFill: '#12306b', grad: 'gradient-root', stops: ['#e8eef8', '#cfd9ea'], border: '#cfe0fb', accent: '#46618f', cards: rootCards, reason: '蓝灰低饱和次级区域表示仓库根基础设施，与三组主分组拉开层级' },
  { id: 'group-local', x: 60, y: 440, w: 550, h: 540, title: '组 1 本仓库维护 · 2', titleFill: '#ffffff', grad: 'gradient-blue', stops: ['#3b8bff', '#1b57e0'], border: '#cfe0fb', accent: '#2468ee', cards: localCards, reason: '蓝色为既定基准主色，标出本仓库自己维护的两个 Skill' },
  { id: 'group-external', x: 630, y: 440, w: 660, h: 540, title: '组 2 外部单项 · 6', titleFill: '#ffffff', grad: 'gradient-teal', stops: ['#17b9a5', '#0b8f86'], border: '#8fe0d5', accent: '#12a898', cards: externalCards, headerIcon: 'icon-cloud', reason: '青绿与蓝、橙同属既定饱和基准，用于区分外部单项，不引入新增主色' },
  { id: 'group-collection', x: 1310, y: 440, w: 550, h: 540, title: '组 3 外部合集 · 1', titleFill: '#ffffff', grad: 'gradient-orange', stops: ['#ffb324', '#f08a00'], border: '#ffd27a', accent: '#f29200', cards: collectionCards, reason: '橙色为既定基准，用于第三类外部合集' },
];

function buildCard(g, c) {
  const small = c.h < 100;
  const nameY = small ? c.y + 28 : c.y + 90;
  const descY = small ? c.y + 52 : c.y + 128;
  const nameSize = small ? 21 : 26;
  const descSize = small ? 18 : 22;
  const nameId = 'text-name-' + c.id;
  const descId = 'text-desc-' + c.id;
  let inner = `<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="18" fill="#ffffff" stroke="${g.border}" stroke-width="1.5" data-paint-role="card"/>`;
  inner += `<rect x="${c.x + 14}" y="${c.y + 10}" width="5" height="${c.h - 20}" rx="2" fill="${g.accent}" data-paint-role="accent"/>`;
  if (c.icon) {
    const uid = 'use-icon-' + c.id;
    V(uid);
    inner += `<use id="${uid}" href="#${c.icon}" x="${c.x + 28}" y="${small ? c.y + 18 : c.y + 70}" width="${small ? 30 : 40}" height="${small ? 30 : 40}" color="${g.accent}"/>`;
  }
  inner += T(nameId, c.name, c.id, '#12306b', c.x + 72, nameY, nameSize, 'font-weight="600"');
  inner += T(descId, c.desc, c.id, '#46618f', c.x + 72, descY, descSize, '');
  V(c.id);
  nodesAcc.push({ id: c.id, group: g.id, title_text: nameId });
  return `<g id="${c.id}" data-group-id="${g.id}" data-region="${c.id}" data-bounds="${c.x},${c.y},${c.w},${c.h}">${inner}</g>`;
}

function buildGroup(g) {
  const frameId = 'frame-' + g.id.replace('group-', '');
  const titleId = 'text-title-' + frameId;
  let inner = `<rect x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="28" fill="#ffffff" stroke="${g.border}" stroke-width="2" filter="url(#shadow)" data-paint-role="card"/>`;
  inner += `<rect x="${g.x}" y="${g.y}" width="${g.w}" height="72" rx="28" fill="url(#${g.grad})" data-paint-role="header"/>`;
  inner += T(titleId, g.title, frameId, g.titleFill, g.x + 24, g.y + 46, 28, 'font-weight="700"');
  if (g.headerIcon) {
    const uid = 'use-header-' + g.id;
    V(uid);
    inner += `<use id="${uid}" href="#${g.headerIcon}" x="${g.x + g.w - 62}" y="${g.y + 20}" width="32" height="32" color="#ffffff"/>`;
  }
  for (const c of g.cards) inner += buildCard(g, c);
  V(frameId);
  nodesAcc.push({ id: frameId, group: g.id, title_text: titleId });
  const frame = `<g id="${frameId}" data-group-id="${g.id}" data-region="${frameId}" data-bounds="${g.x},${g.y},${g.w},${g.h}">${inner}</g>`;
  V(g.id);
  groupsAcc.push({
    id: g.id,
    members: [frameId, ...g.cards.map(c => c.id)],
    paint: {
      kind: 'gradient', fill: '#ffffff', stroke: g.border, accent: g.accent, foreground: '#12306b',
      header_gradient: { id: g.grad, direction: [0, 0, 1, 1], stops: [{ offset: 0, color: g.stops[0] }, { offset: 1, color: g.stops[1] }] }
    },
    reason: g.reason
  });
  return `<g id="${g.id}" data-group-id="${g.id}">${frame}</g>`;
}

const relations = [
  { id: 'rel-01', from: 'frame-root', to: 'frame-local', kind: 'contains', condition: '索引收录', line_style: 'style-contains', label_text: 'text-cond-1', d: 'M 335,350 L 335,440' },
  { id: 'rel-02', from: 'frame-root', to: 'frame-external', kind: 'contains', condition: '索引收录', line_style: 'style-contains', label_text: 'text-cond-2', d: 'M 960,350 L 960,440' },
  { id: 'rel-03', from: 'frame-root', to: 'frame-collection', kind: 'contains', condition: '索引收录', line_style: 'style-contains', label_text: 'text-cond-3', d: 'M 1585,350 L 1585,440' },
  { id: 'rel-04', from: 'node-01', to: 'node-dir-req', kind: 'source', condition: '源码在此', line_style: 'style-source', label_text: 'text-cond-4', d: 'M 586,635 L 620,635 L 620,398 L 1313,398 L 1313,334' },
  { id: 'rel-05', from: 'node-02', to: 'node-dir-svg', kind: 'source', condition: '源码在此', line_style: 'style-source', label_text: 'text-cond-5', d: 'M 586,861 L 624,861 L 624,428 L 1667,428 L 1667,334' },
];
const lineStyles = [
  { id: 'style-contains', stroke: '#46618f', dasharray: '', meaning: '索引收录', legend_text: 'text-legend-1', marker: 'marker-contains' },
  { id: 'style-source', stroke: '#7f8fab', dasharray: '8 6', meaning: '源码在此', legend_text: 'text-legend-2', marker: 'marker-source' },
];

// ---- SVG body ----
parts.push(`<svg xmlns="http://www.w3.org/2000/svg" id="diagram-main" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-labelledby="diagram-title diagram-description" fill="#ffffff" stroke="none" color="#1c2b4a" data-topology="nested" data-detail-level="medium">`);
parts.push(`<title id="diagram-title">${esc(TITLE)}</title>`);
parts.push(`<desc id="diagram-description">${esc(DESC)}</desc>`);

const iconsSrc = fs.readFileSync(ROOT + '/assets/icons.svg', 'utf8');
const wanted = ['icon-document', 'icon-shield', 'icon-package', 'icon-edit', 'icon-layers', 'icon-cloud'];
let symbols = '';
for (const id of wanted) {
  const m = iconsSrc.match(new RegExp('<symbol id="' + id + '"[\\s\\S]*?</symbol>'));
  if (!m) throw new Error('missing icon ' + id);
  symbols += m[0] + '\n';
}
const grad = (id, x1, y1, x2, y2, a, b) => `<linearGradient id="${id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>`;
parts.push('<defs>');
parts.push('<style>text{font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC","Source Han Sans SC",Arial,sans-serif}</style>');
parts.push(grad('gradient-bg', 0, 0, 0, 1, '#f4f9ff', '#e9f2ff'));
for (const g of GROUPS) parts.push(grad(g.grad, 0, 0, 1, 1, g.stops[0], g.stops[1]));
parts.push('<filter id="shadow" x="-20%" y="-20%" width="140%" height="145%"><feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#2864dc" flood-opacity="0.12"/></filter>');
for (const s of lineStyles) parts.push(`<marker id="${s.marker}" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M1,1 L10,6 L1,11 Z" fill="${s.stroke}" stroke="none"/></marker>`);
parts.push(symbols);
parts.push('</defs>');

V('diagram-background');
parts.push('<rect id="diagram-background" x="0" y="0" width="1920" height="1080" fill="url(#gradient-bg)"/>');

let titleInner = T('text-title', TITLE, 'region-title', '#12306b', 60, 108, 46, 'font-weight="700"');
titleInner += T('text-subtitle', '9 个条目 · 2 本仓库维护 / 6 外部单项 / 1 外部合集', 'region-title', '#46618f', 60, 148, 22, '');
parts.push(RG('region-title', '60,48,1800,120', titleInner));

for (const g of GROUPS) parts.push(buildGroup(g));

// relations (drawn above group backgrounds, below labels)
for (const r of relations) {
  V(r.id);
  const dash = r.line_style === 'style-source' ? ' stroke-dasharray="8 6"' : '';
  const stroke = r.line_style === 'style-source' ? '#7f8fab' : '#46618f';
  const marker = r.line_style === 'style-source' ? 'marker-source' : 'marker-contains';
  parts.push(`<path id="${r.id}" data-from="${r.from}" data-to="${r.to}" data-kind="${r.kind}" data-condition="${r.condition}" data-line-style="${r.line_style}" d="${r.d}" fill="none" stroke="${stroke}" stroke-width="2.5"${dash} marker-end="url(#${marker})"/>`);
}

let relInner = '';
relInner += T('text-cond-1', '索引收录', 'region-relations', '#1c2b4a', 345, 386, 18, '');
relInner += T('text-cond-2', '索引收录', 'region-relations', '#1c2b4a', 970, 386, 18, '');
relInner += T('text-cond-3', '索引收录', 'region-relations', '#1c2b4a', 1595, 386, 18, '');
relInner += T('text-cond-4', '源码在此', 'region-relations', '#1c2b4a', 660, 392, 18, '');
relInner += T('text-cond-5', '源码在此', 'region-relations', '#1c2b4a', 1100, 422, 18, '');
parts.push(RG('region-relations', '60,350,1800,90', relInner));

let legend = '<line x1="60" y1="1006" x2="104" y2="1006" stroke="#46618f" stroke-width="2.5" marker-end="url(#marker-contains)"/>';
legend += T('text-legend-1', '实线＝索引收录（包含）', 'region-legend', '#1c2b4a', 116, 1012, 20, '');
legend += '<line x1="760" y1="1006" x2="804" y2="1006" stroke="#7f8fab" stroke-width="2.5" stroke-dasharray="8 6" marker-end="url(#marker-source)"/>';
legend += T('text-legend-2', '虚线＝源码在此（对应）', 'region-legend', '#1c2b4a', 816, 1012, 20, '');
legend += T('text-note-1', '外部条目仅保留作者 / 维护者链接，不在本仓库存源码', 'region-legend', '#46618f', 60, 1046, 18, '');
legend += T('text-note-2', '环节为按需组合，不是自动编排', 'region-legend', '#46618f', 1000, 1046, 18, '');
parts.push(RG('region-legend', '60,990,1800,70', legend));

parts.push('</svg>');

const svg = parts.join('\n') + '\n';
fs.writeFileSync(OUT + '/candidate.svg', svg, 'utf8');

const acceptance = {
  schema_version: 1,
  confirmation: { status: 'approved', evidence: '用户于 2026-11-05 回复「确认」，批准本轮完整提纲（含推荐项 A：补装 Python 运行时）' },
  diagram: {
    id: 'diagram-main', filename: 'repo-architecture.svg', title: TITLE, description: DESC,
    topology: 'nested', detail_level: 'medium', viewBox: [0, 0, 1920, 1080], width: 1920, height: 1080, display_width: 1600,
    background: { id: 'diagram-background', gradient: { id: 'gradient-bg', direction: [0, 0, 0, 1], stops: [{ offset: 0, color: '#f4f9ff' }, { offset: 1, color: '#e9f2ff' }] } },
    defaults: { fill: '#ffffff', stroke: 'none', color: '#1c2b4a' }
  },
  texts, nodes: nodesAcc, groups: groupsAcc, relations, line_styles: lineStyles,
  visible_elements: visible,
  assumptions: [
    '使用环节取自 README 目录表第二列，为已有事实，不是推断的执行顺序',
    '外部条目仅保留作者 / 维护者链接，不在本仓库存源码',
    'image/ 为本次新增目录，只写进 README 图注，不画成节点',
    '未读外部仓库源码，不补版本信息与上游内部实现',
    '不画执行顺序箭头、并行拆分 / 汇合或反馈回路'
  ],
  fallback: { allowed: true, description: '若单图同一可读性问题连续三次修订仍不通过，按已批准拆图方案拆为 image/repo-architecture-overview.svg 与 image/repo-architecture-skills.svg 两张，编号 ①–⑨ 与三组配色保持一致，冻结总内容不减' }
};
fs.writeFileSync(OUT + '/acceptance.json', JSON.stringify(acceptance, null, 2) + '\n', 'utf8');
console.log('SVG bytes:', Buffer.byteLength(svg, 'utf8'));
console.log('texts:', texts.length, 'nodes:', nodesAcc.length, 'groups:', groupsAcc.length, 'visible:', visible.length, 'relations:', relations.length);
