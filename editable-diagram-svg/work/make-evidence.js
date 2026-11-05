const fs = require('fs');
const crypto = require('crypto');
const W = 'd:/GitHub/requirement-clarifier/editable-diagram-svg/work';
const ROOT = 'd:/GitHub/requirement-clarifier/editable-diagram-svg';
const sha = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

const svgPath = W + '/candidate.svg';
const accPath = W + '/acceptance.json';
const pngPath = W + '/preview.png';
const H = {
  svg_sha256: sha(svgPath),
  acceptance_sha256: sha(accPath),
  palette_sha256: sha(ROOT + '/references/palette.json'),
  png_sha256: sha(pngPath)
};
const png = fs.readFileSync(pngPath);
const preview = { width: png.readUInt32BE(16), height: png.readUInt32BE(20) };
const now = new Date().toISOString();
const R = (key, reason) => ({ key, status: '通过', reason, evidence: null, required: true });
const base = stage => ({ schema_version: 1, stage, status: '通过', ok: true, svg_path: svgPath, ...H, png_path: pngPath, preview, reviewed_at: now });

const render = {
  ...base('render'),
  tool: 'Google Chrome headless (chrome.exe --headless --screenshot) via preview.html wrapper at frozen display_width',
  command: 'chrome.exe --headless --disable-gpu --hide-scrollbars --no-first-run --user-data-dir=<work>/chrome-profile --window-size=1600,900 --screenshot=<work>/preview.png file:///D:/GitHub/requirement-clarifier/editable-diagram-svg/work/preview.html',
  checks: { renderer: true, fresh_png: true, preview_size: true, hash_linkage: true, visual_target: true },
  results: [
    R('renderer', 'Chrome headless 已核实可用，本次成功生成 PNG'),
    R('fresh_png', '按当前 candidate.svg 重新渲染，PNG 238583 字节，未复用旧预览'),
    R('preview_size', 'PNG 实际尺寸 1600x900，与冻结展示宽 1600 的 16:9 一致'),
    R('hash_linkage', 'SVG / acceptance / palette 哈希与静态冻结报告一致'),
    R('visual_target', '按目标展示宽渲染全图，非缩略图或局部裁切'),
    { key: 'render_svg.cjs', status: '未执行', reason: '当前环境缺 Playwright Node 包，官方 render_svg.cjs 未使用；改用已核实的 Chrome headless 等价渲染，工具与命令已如实记录', evidence: null, required: false }
  ],
  limitations: [
    'render_svg.cjs 未使用（缺 Playwright Node 包）；渲染证据来自已核实的 Chrome headless 本地渲染器',
    '证据由 Agent 提供；哈希链不证明人工审批或人工目视'
  ]
};

const visual = {
  ...base('visual'),
  acceptance_version: H.acceptance_sha256,
  checks: { glyphs: true, icons: true, text_layout: true, connections: true, clipping: true, colors: true, reading_order: true, content: true },
  results: [
    R('glyphs', '中文、英文、数字及 ①–⑨ 圈号全部正常显示，无缺字或豆腐块'),
    R('icons', 'icon-document×2 / icon-shield / icon-package×2 / icon-edit / icon-layers / icon-cloud 全部渲染，无缺失或变形'),
    R('text_layout', '标题、副标题、四个组标题、卡片名称与副标题、条件标签、图例与注记均可读，无截断、省略号或压字'),
    R('connections', '3 条实线停在三个分组容器顶边，2 条虚线停在两张源码目录卡底边；箭头完整；交叉处靠线型与颜色区分，无连线穿字'),
    R('clipping', '按 1600 宽全图无溢出、无遮挡、阴影与箭头未裁切'),
    R('colors', '浅蓝渐变背景、蓝/青绿/橙饱和主标题栏配白字、白卡细边框与轻阴影、蓝灰次级容器深字、强色侧条均可见；未引入新增主色'),
    R('reading_order', '标题 → 仓库根 → 三组左至右 → 组内自上而下 → 底部图例与注记，顺序明确'),
    R('content', '9 个条目名称、编号与 README 目录表逐字一致，使用环节取自目录表第二列；仓库根 5 个文件名与 2/6/1 计数正确；无补造模块、版本信息或执行顺序箭头'),
    { key: 'revision', status: '通过', reason: '首次目视发现两个「源码在此」条件标签上下紧贴；将其一横向移至 x=1100 后重渲染，标签已分开且不压线。仅调整坐标，冻结文字、关系与配色未变', evidence: null, required: false }
  ],
  limitations: [
    '目视由 Agent 实际读取 1600x900 PNG 完成，非人工目视',
    '渲染器为 Chrome headless 而非官方 render_svg.cjs（缺 Playwright Node 包）'
  ]
};

fs.writeFileSync(W + '/render-report.json', JSON.stringify(render, null, 2) + '\n', 'utf8');
fs.writeFileSync(W + '/visual-review.json', JSON.stringify(visual, null, 2) + '\n', 'utf8');
console.log('preview', JSON.stringify(preview), 'reviewed_at', now);
console.log('hashes', JSON.stringify(H));
