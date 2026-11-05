#!/usr/bin/env node
'use strict';
// Actual local renderer tests plus explicitly fault-injected boundary reports.
const fs = require('node:fs'), path = require('node:path'), os = require('node:os'), crypto = require('node:crypto');
const {spawnSync} = require('node:child_process');
const PACKAGE = path.resolve(__dirname, '..');
function options(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 2) {
    if (!['--python', '--module-dir', '--browser', '--report'].includes(argv[i]) || !argv[i + 1]) throw Error('Use --python PATH --module-dir PATH --browser PATH [--report JSON]');
    out[argv[i].slice(2)] = argv[i + 1];
  }
  if (!out.python || !out['module-dir'] || !out.browser) throw Error('Existing Python, Playwright module directory and browser are required');
  return out;
}
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
function run(args) {
  const tempRoot = path.resolve(os.tmpdir()), temp = fs.mkdtempSync(path.join(tempRoot, 'editable-svg-render-'));
  const results = [];
  function check(condition, message) { if (!condition) throw Error(message); }
  function record(key, action) { action(); results.push({key, status: '通过'}); }
  try {
    const setup = spawnSync(args.python, ['-X', 'utf8', '-c', 'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from exercise_publish import fixture; fixture(Path(sys.argv[2]))', path.join(PACKAGE, 'verification'), temp], {encoding: 'utf8', windowsHide: true});
    check(setup.status === 0, 'Fixture setup failed: ' + setup.stderr);
    const svgPath = path.join(temp, 'candidate.svg'), staticPath = path.join(temp, 'static.json');
    const originalSvg = fs.readFileSync(svgPath), originalStatic = JSON.parse(fs.readFileSync(staticPath, 'utf8'));
    const png = path.join(temp, 'actual-preview.png'), audit = path.join(temp, 'actual-render.json');
    const command = ['--input', svgPath, '--output', png, '--acceptance', path.join(temp, 'acceptance.json'), '--static-report', staticPath, '--width', '400', '--audit', audit, '--module-dir', args['module-dir'], '--browser', args.browser, '--example-mode'];
    function invoke(extra = [], replace = null) {
      const effective = replace || [...command, ...extra];
      const processResult = spawnSync(process.execPath, [path.join(PACKAGE, 'scripts/render_svg.cjs'), ...effective], {encoding: 'utf8', windowsHide: true, maxBuffer: 4 * 1024 * 1024});
      check(!processResult.error, 'Renderer process failed: ' + processResult.error);
      let report;
      try { report = JSON.parse(processResult.stdout); } catch { throw Error('Renderer did not return JSON: ' + processResult.stderr + processResult.stdout); }
      return {code: processResult.status, report};
    }
    record('actual_renderer_png_and_geometry', () => {
      const value = invoke();
      check(value.code === 0 && value.report.status === '通过' && value.report.regionCoverage === 1 && value.report.geometryErrors.length === 0, JSON.stringify(value));
      check(value.report.preview.width === 400 && value.report.preview.height === 240 && fs.existsSync(png), 'Actual preview missing');
      check(value.report.results.some(item => item.key === 'visual_review' && item.status === '未执行'), 'Renderer must not claim agent visual review');
    });
    const currentPng = fs.readFileSync(png);
    record('stale_static_report_preserves_old_png', () => {
      fs.writeFileSync(staticPath, JSON.stringify({...originalStatic, svg_sha256: '0'.repeat(64)}));
      const value = invoke();
      check(value.code === 1 && value.report.status === '失败' && value.report.png_sha256 === null && hash(fs.readFileSync(png)) === hash(currentPng), JSON.stringify(value));
      fs.writeFileSync(staticPath, JSON.stringify(originalStatic));
    });
    record('missing_browser_is_blocked_not_old_preview_success', () => {
      const altered = [...command]; altered[altered.indexOf('--browser') + 1] = path.join(temp, 'not-installed-browser.exe');
      const value = invoke([], altered);
      check(value.code === 3 && value.report.status === '环境受阻' && value.report.png_path === null && value.report.png_sha256 === null && value.report.svg_sha256 === originalStatic.svg_sha256, JSON.stringify(value));
      check(hash(fs.readFileSync(png)) === hash(currentPng), 'Blocked renderer must not mutate old preview');
    });
    record('nan_region_rejected_with_fault_injected_precheck', () => {
      const broken = originalSvg.toString('utf8').replace('20,20,360,180', 'NaN,20,360,180');
      fs.writeFileSync(svgPath, broken);
      // Deliberately corrupt the prior passing record to test renderer defense in depth.
      fs.writeFileSync(staticPath, JSON.stringify({...originalStatic, svg_sha256: hash(Buffer.from(broken))}));
      const value = invoke();
      check(value.code === 1 && value.report.status === '失败' && value.report.regionErrors.length === 1 && value.report.checks.regions === false, JSON.stringify(value));
      fs.writeFileSync(svgPath, originalSvg); fs.writeFileSync(staticPath, JSON.stringify(originalStatic));
    });
    record('geometry_failure_is_separate_from_successful_screenshot', () => {
      const broken = originalSvg.toString('utf8').replace('y="100"', 'y="220"');
      fs.writeFileSync(svgPath, broken);
      fs.writeFileSync(staticPath, JSON.stringify({...originalStatic, svg_sha256: hash(Buffer.from(broken))}));
      const value = invoke();
      check(value.code === 1 && value.report.checks.rendered === true && value.report.checks.geometry === false && value.report.geometryErrors.length === 1, JSON.stringify(value));
      fs.writeFileSync(svgPath, originalSvg); fs.writeFileSync(staticPath, JSON.stringify(originalStatic));
    });
    record('duplicate_argument_is_configuration_error', () => { const value = invoke(['--width', '400']); check(value.code === 2 && value.report.status === '失败', JSON.stringify(value)); });
    record('unknown_argument_is_configuration_error', () => { const value = invoke(['--skip-colors', 'yes']); check(value.code === 2 && value.report.status === '失败', JSON.stringify(value)); });
    record('invalid_width_is_configuration_error', () => { const altered = [...command]; altered[altered.indexOf('--width') + 1] = 'NaN'; const value = invoke([], altered); check(value.code === 2 && value.report.status === '失败', JSON.stringify(value)); });
    const report = {scope: 'Actual local renderer behavior; NaN/geometry cases explicitly fault-inject static-report fixtures. No actual agent visual review is claimed by these tests.', ok: true, count: results.length, results, renderer: 'Playwright Chromium', temporary_files_cleaned: true};
    if (args.report) fs.writeFileSync(path.resolve(args.report), JSON.stringify(report, null, 2) + '\n');
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
    return 0;
  } finally {
    const checked = path.resolve(temp);
    if (path.dirname(checked) !== tempRoot || !path.basename(checked).startsWith('editable-svg-render-')) throw Error('Unsafe temporary cleanup target');
    fs.rmSync(checked, {recursive: true, force: true});
  }
}
try { process.exitCode = run(options(process.argv.slice(2))); }
catch (error) { process.stderr.write(error.message + '\n'); process.exitCode = 1; }
