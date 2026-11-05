#!/usr/bin/env node
'use strict';
// Preview only. Uses an existing Playwright/Chromium; never installs dependencies.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const PASSED = '通过', FAILED = '失败', SKIPPED = '未执行', BLOCKED = '环境受阻';
const VALUE_OPTIONS = new Set(['input', 'output', 'acceptance', 'static-report', 'width', 'audit', 'module-dir', 'browser']);
class ToolError extends Error {
  constructor(message, code = 1, check = 'execution') { super(message); this.code = code; this.check = check; }
}
function parse(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith('--')) throw new ToolError(`Unexpected argument: ${token}`, 2, 'arguments');
    const key = token.slice(2);
    if (Object.hasOwn(args, key)) throw new ToolError(`Duplicate option: --${key}`, 2, 'arguments');
    if (key === 'example-mode' || key === 'help') { args[key] = true; continue; }
    if (!VALUE_OPTIONS.has(key)) throw new ToolError(`Unknown option: --${key}`, 2, 'arguments');
    const value = argv[++i];
    if (!value || value.startsWith('--')) throw new ToolError(`Missing value for --${key}`, 2, 'arguments');
    args[key] = value;
  }
  if (args.help) return args;
  for (const key of ['input', 'output', 'acceptance', 'static-report']) {
    if (!args[key]) throw new ToolError(`Required option: --${key}`, 2, 'arguments');
  }
  const width = Number(args.width || 1600);
  if (!Number.isInteger(width) || width < 320 || width > 8192) throw new ToolError('Preview width must be an integer 320..8192', 2, 'arguments');
  args.width = width;
  for (const key of ['input', 'output', 'acceptance', 'static-report', 'audit', 'module-dir', 'browser']) {
    if (args[key]) args[key] = path.resolve(args[key]);
  }
  if (!/\.png$/i.test(args.output)) throw new ToolError('--output must end in .png', 2, 'arguments');
  args.audit ||= args.output.replace(/\.png$/i, '') + '.render.json';
  const inputs = [args.input, args.acceptance, args['static-report'], path.resolve(__dirname, '../references/palette.json')];
  const normalize = p => process.platform === 'win32' ? p.toLowerCase() : p;
  if (normalize(args.output) === normalize(args.audit) || [args.output, args.audit].some(p => inputs.some(q => normalize(p) === normalize(q)))) {
    throw new ToolError('Preview/audit paths must be distinct from each other and input files', 2, 'arguments');
  }
  return args;
}
const digest = data => crypto.createHash('sha256').update(data).digest('hex');
const fileHash = file => digest(fs.readFileSync(file));
function readJson(file, label) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); }
  catch (e) { throw new ToolError(`${label}: ${e.message}`, e.code === 'EACCES' || e.code === 'EPERM' ? 3 : 2, label); }
}
function atomicJson(file, value) {
  fs.mkdirSync(path.dirname(file), {recursive: true});
  const temp = path.join(path.dirname(file), '.' + path.basename(file) + '.' + crypto.randomUUID() + '.tmp');
  try {
    fs.writeFileSync(temp, JSON.stringify(value, null, 2) + '\n', {encoding: 'utf8', flag: 'wx'});
    fs.renameSync(temp, file);
  } finally { if (fs.existsSync(temp)) fs.unlinkSync(temp); }
}
function result(report, key, status, reason = '', evidence = null, required = true) {
  report.results.push({key, status, reason, evidence, required});
  if (required) report.checks[key] = status === PASSED;
}
function summarize(report) {
  const mandatory = report.results.filter(item => item.required !== false);
  report.status = mandatory.some(item => item.status === FAILED) ? FAILED
    : mandatory.some(item => item.status === BLOCKED) ? BLOCKED
    : mandatory.some(item => item.status === SKIPPED) || !mandatory.length ? SKIPPED : PASSED;
  report.ok = report.status === PASSED;
  return report;
}
function checkEvidence(report, expected) {
  if (!report || report.schema_version !== 1 || report.stage !== 'static' || report.status !== PASSED || report.ok !== true || report.production_ready !== true) {
    throw new ToolError('A current passing static report is required', 1, 'static_precheck');
  }
  if (!Array.isArray(report.results) || !report.results.length || !report.checks || !Object.keys(report.checks).length) {
    throw new ToolError('Static report has no check evidence', 1, 'static_precheck');
  }
  if (Object.values(report.checks).some(value => value !== true) || report.results.some(item => item.required !== false && item.status !== PASSED)) {
    throw new ToolError('Static report contains incomplete or failed required checks', 1, 'static_precheck');
  }
  for (const key of ['svg_sha256', 'acceptance_sha256', 'palette_sha256']) {
    if (report[key] !== expected[key]) throw new ToolError(`Stale static report: ${key}`, 1, 'static_precheck');
  }
}
function inspectPng(file, width, height) {
  const data = fs.readFileSync(file);
  if (data.length < 24 || !data.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
    throw new ToolError('Screenshot is not a valid PNG', 1, 'png_valid');
  }
  if (data.readUInt32BE(16) !== width || data.readUInt32BE(20) !== height) {
    throw new ToolError('PNG dimensions differ from the requested preview', 1, 'png_valid');
  }
  return digest(data);
}
async function run(argv) {
  let args, browser, temporaryPng;
  const palettePath = path.resolve(__dirname, '../references/palette.json');
  const report = {
    schema_version: 1, stage: 'render', status: SKIPPED, ok: false,
    svg_path: null, svg_sha256: null, acceptance_sha256: null, palette_sha256: null,
    checks: {}, results: [], limitations: [
      'Geometry checks do not establish glyph coverage, visual occlusion, arrow targets, clipping or business correctness; view the actual PNG.',
      'Font lookup is a browser hint, not proof of installed font files or complete glyph coverage.',
      'Text regions use root viewBox coordinates; transformed text/region ancestors are unsupported.'
    ], png_path: null, png_sha256: null, preview: null, exit_code: 1
  };
  let exitCode = 0;
  try {
    args = parse(argv);
    if (args.help) {
      process.stdout.write('Usage: node render_svg.cjs --input SVG --output PNG --acceptance JSON --static-report JSON [--width 1600] [--audit JSON] [--module-dir PATH] [--browser PATH] [--example-mode]\n');
      return 0;
    }
    report.svg_path = args.input;
    let source;
    try {
      source = fs.readFileSync(args.input);
      report.svg_sha256 = digest(source);
      report.acceptance_sha256 = fileHash(args.acceptance);
      report.palette_sha256 = fileHash(palettePath);
    } catch (e) { throw new ToolError(`Cannot read required input: ${e.message}`, e.code === 'ENOENT' ? 2 : 3, 'input_files'); }
    const acceptance = readJson(args.acceptance, 'acceptance');
    const mode = args['example-mode'] ? 'simulated' : 'approved';
    if (acceptance.schema_version !== 1 || acceptance.confirmation?.status !== mode || !acceptance.confirmation?.evidence?.trim()) {
      throw new ToolError(`Confirmation must be ${mode} with evidence`, 2, 'confirmation');
    }
    result(report, 'confirmation', PASSED, `Mode: ${mode}`);
    checkEvidence(readJson(args['static-report'], 'static_report'), report);
    result(report, 'static_precheck', PASSED, 'Current SVG, acceptance and palette hashes match passing static checks', args['static-report']);
    if (acceptance.diagram?.display_width !== args.width) throw new ToolError('Preview width differs from the frozen display_width', 1, 'target_size');
    let playwright;
    try { playwright = require(require.resolve('playwright', {paths: args['module-dir'] ? [args['module-dir']] : [__dirname, process.cwd()]})); }
    catch (e) { throw new ToolError(`Existing Playwright is unavailable: ${e.message}`, 3, 'renderer_available'); }
    if (args.browser && !fs.existsSync(args.browser)) throw new ToolError(`Existing browser path does not exist: ${args.browser}`, 3, 'browser_launch');
    result(report, 'renderer_available', PASSED, 'Existing Playwright loaded; no installation performed');
    try { browser = await playwright.chromium.launch({headless: true, ...(args.browser ? {executablePath: args.browser} : {})}); }
    catch (e) { throw new ToolError(`Existing Chromium cannot launch: ${e.message}`, 3, 'browser_launch'); }
    result(report, 'browser_launch', PASSED, 'Existing browser launched');
    report.renderer = 'Playwright Chromium'; report.browserVersion = browser.version();
    const page = await browser.newPage({viewport: {width: args.width, height: 1000}, deviceScaleFactor: 1});
    await page.route('**/*', route => route.abort());
    await page.setContent('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:white}body>svg{display:block}</style></head><body>' + source.toString('utf8').replace(/^\uFEFF/, '') + '</body></html>');
    const dimensions = await page.evaluate(() => {
      const svg = document.querySelector('body > svg');
      if (!svg) throw Error('No SVG root');
      const box = svg.viewBox.baseVal;
      if (![box.x, box.y, box.width, box.height].every(Number.isFinite) || box.width <= 0 || box.height <= 0) throw Error('Invalid viewBox');
      return {viewBox: [box.x, box.y, box.width, box.height], sourceWidth: svg.getAttribute('width'), sourceHeight: svg.getAttribute('height')};
    });
    if (JSON.stringify(dimensions.viewBox) !== JSON.stringify(acceptance.diagram.viewBox)) throw new ToolError('Rendered viewBox differs from acceptance', 1, 'target_size');
    const height = Math.ceil(args.width * dimensions.viewBox[3] / dimensions.viewBox[2]);
    if (height > 16384) throw new ToolError('Preview exceeds 16384px height; use the approved split/section plan', 1, 'target_size');
    report.preview = {width: args.width, height}; Object.assign(report, dimensions);
    await page.setViewportSize({width: args.width, height});
    await page.evaluate(({width, height}) => { const svg = document.querySelector('body > svg'); svg.setAttribute('width', width); svg.setAttribute('height', height); }, report.preview);
    await page.evaluate(async () => { await document.fonts.ready; });
    result(report, 'target_size', PASSED, 'Preview uses the frozen width and viewBox ratio', report.preview);
    const geometry = await page.evaluate(() => {
      const svg = document.querySelector('body > svg'), screen = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
      const sx = screen.width / vb.width, sy = screen.height / vb.height;
      const errors = [], regions = [], hidden = [], transformed = [];
      const texts = [...svg.querySelectorAll('text')].filter(element => !element.closest('defs')).map(element => {
        const owner = element.closest('[data-bounds]');
        let region = null, regionBounds = null, regionValid = false;
        if (owner) {
          region = owner.dataset.region || null;
          const values = owner.dataset.bounds.split(',').map(Number);
          regionValid = !!region && values.length === 4 && values.every(Number.isFinite) && values[2] > 0 && values[3] > 0;
          if (regionValid) regionBounds = {left: screen.left + (values[0] - vb.x) * sx, top: screen.top + (values[1] - vb.y) * sy, right: screen.left + (values[0] + values[2] - vb.x) * sx, bottom: screen.top + (values[1] + values[3] - vb.y) * sy};
        }
        if (!regionValid) regions.push({id: element.id, reason: 'Missing/invalid root-coordinate data-region/data-bounds'});
        let ancestor = element;
        while (ancestor && ancestor !== svg) {
          if (ancestor.hasAttribute('transform') && ancestor.getAttribute('transform').trim()) transformed.push({id: element.id, ancestor: ancestor.id || ancestor.tagName});
          const style = getComputedStyle(ancestor);
          if (style.display === 'none' || ['hidden', 'collapse'].includes(style.visibility) || Number(style.opacity) === 0) hidden.push({id: element.id, ancestor: ancestor.id || ancestor.tagName});
          ancestor = ancestor.parentElement;
        }
        const pieces = [element, ...element.querySelectorAll('tspan')];
        for (const piece of pieces) {
          const style = getComputedStyle(piece);
          if (style.display === 'none' || ['hidden', 'collapse'].includes(style.visibility) || Number(style.opacity) === 0 || Number(style.fillOpacity) === 0 || parseFloat(style.fontSize) <= 0) hidden.push({id: element.id, reason: 'Hidden/zero-size text or span'});
        }
        const rect = element.getBoundingClientRect(), bbox = element.getBBox(), style = getComputedStyle(element);
        const outsideCanvas = rect.left < screen.left - 1 || rect.top < screen.top - 1 || rect.right > screen.right + 1 || rect.bottom > screen.bottom + 1;
        const outsideRegion = regionValid && (rect.left < regionBounds.left - 1 || rect.top < regionBounds.top - 1 || rect.right > regionBounds.right + 1 || rect.bottom > regionBounds.bottom + 1);
        const item = {id: element.id, text: element.textContent, box: [bbox.x, bbox.y, bbox.width, bbox.height], screenBox: [rect.left - screen.left, rect.top - screen.top, rect.width, rect.height], screenFontSize: parseFloat(style.fontSize) * sx, fontFamily: style.fontFamily, region, outsideCanvas, outsideRegion};
        if (outsideCanvas || outsideRegion) errors.push(item);
        return item;
      });
      return {textCount: texts.length, iconUses: svg.querySelectorAll('use').length, texts, regionErrors: regions, hiddenErrors: hidden, transformedText: transformed, geometryErrors: errors, regionCoverage: texts.length ? (texts.length - regions.length) / texts.length : 0, availableKnownFonts: ['Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', 'Arial'].filter(font => document.fonts.check('20px "' + font + '"'))};
    });
    Object.assign(report, geometry);
    result(report, 'regions', geometry.regionErrors.length ? FAILED : PASSED, 'Every text needs a finite positive root-coordinate region', geometry.regionErrors);
    result(report, 'visible_text', geometry.hiddenErrors.length ? FAILED : PASSED, 'Explicit hidden/zero-size text is rejected', geometry.hiddenErrors);
    result(report, 'root_coordinates', geometry.transformedText.length ? FAILED : PASSED, 'Transformed text/region ancestors require an explicitly supported alternate check', geometry.transformedText);
    result(report, 'geometry', geometry.geometryErrors.length ? FAILED : PASSED, 'Canvas and region bounds use one display-pixel tolerance', geometry.geometryErrors);
    if (report.textCount !== acceptance.texts.length) result(report, 'text_coverage', FAILED, 'Rendered text count differs from the frozen manifest');
    else result(report, 'text_coverage', PASSED, 'All frozen text objects reached the renderer', report.textCount);
    fs.mkdirSync(path.dirname(args.output), {recursive: true});
    temporaryPng = path.join(path.dirname(args.output), '.' + path.basename(args.output) + '.' + crypto.randomUUID() + '.tmp.png');
    await page.screenshot({path: temporaryPng, type: 'png', fullPage: false});
    const pngHash = inspectPng(temporaryPng, args.width, height);
    result(report, 'rendered', PASSED, 'Current SVG actually rendered and a fresh valid PNG was produced');
    result(report, 'png_valid', PASSED, 'Fresh PNG signature and dimensions checked');
    for (const [file, key] of [[args.input, 'svg_sha256'], [args.acceptance, 'acceptance_sha256'], [palettePath, 'palette_sha256']]) {
      if (fileHash(file) !== report[key]) throw new ToolError(`Input changed during rendering: ${key}`, 1, 'current_input');
    }
    result(report, 'current_input', PASSED, 'Input hashes unchanged throughout rendering');
    fs.renameSync(temporaryPng, args.output); temporaryPng = null;
    report.png_path = args.output; report.png_sha256 = pngHash;
    result(report, 'visual_review', SKIPPED, 'The agent must open the actual PNG and record a separate visual report', null, false);
    result(report, 'receiving_machine', SKIPPED, 'Fonts and other renderers on the receiving machine were not tested', null, false);
    summarize(report);
    exitCode = report.ok ? 0 : 1;
  } catch (e) {
    exitCode = e instanceof ToolError ? e.code : (['EACCES', 'EPERM', 'ENOENT'].includes(e.code) ? 3 : 1);
    result(report, e.check || 'execution', exitCode === 3 ? BLOCKED : FAILED, e.message);
    result(report, 'visual_review', SKIPPED, 'No agent visual review was performed by this script', null, false);
    summarize(report);
  } finally {
    if (browser) { try { await browser.close(); } catch (e) { result(report, 'browser_cleanup', FAILED, e.message); exitCode = 1; } }
    if (temporaryPng && fs.existsSync(temporaryPng)) { try { fs.unlinkSync(temporaryPng); } catch (e) { result(report, 'temporary_cleanup', BLOCKED, e.message); exitCode = 3; } }
  }
  summarize(report); report.exit_code = exitCode;
  if (args?.audit) {
    try { atomicJson(args.audit, report); }
    catch (e) { result(report, 'audit_write', ['EACCES', 'EPERM'].includes(e.code) ? BLOCKED : FAILED, e.message); exitCode = ['EACCES', 'EPERM'].includes(e.code) ? 3 : 1; summarize(report); report.exit_code = exitCode; }
  }
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  return exitCode;
}
if (require.main === module) run(process.argv.slice(2)).then(code => { process.exitCode = code; }).catch(error => { process.stderr.write(error.message + '\n'); process.exitCode = 1; });
module.exports = {run, parse, inspectPng};
