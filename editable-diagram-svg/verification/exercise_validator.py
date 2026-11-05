#!/usr/bin/env python3
"""Independent positive/negative SVG contracts; stdlib, isolated temporary files."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PACKAGE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('editable_svg_validator', PACKAGE / 'scripts' / 'validate_svg.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def fixture():
    source = '''<svg xmlns="http://www.w3.org/2000/svg" id="demo" width="600" height="300" viewBox="0 0 600 300" role="img" aria-labelledby="title description" fill="#26406e" stroke="none" color="#26406e" data-topology="left-to-right" data-detail-level="medium">
<title id="title">演示流程</title><desc id="description">虚构：审核通过后交付。</desc>
<defs><style>text{font-family:"Microsoft YaHei",Arial,sans-serif}</style><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4f9ff"/><stop offset="1" stop-color="#e9f2ff"/></linearGradient><marker id="arrow" markerWidth="10" markerHeight="10"><path d="M0 0 L9 5 L0 10Z" fill="#46618f"/></marker></defs>
<rect id="background" width="600" height="300" fill="url(#bg)"/>
<g id="review-group" data-group-id="review-group"><g id="review" data-group-id="review-group"><rect data-paint-role="card" x="30" y="70" width="180" height="100" rx="16" fill="#fafcff" stroke="#8db8ff"/><g data-region="review-region" data-bounds="40,80,160,80"><text id="review-text" data-content-id="review-text" data-paint-role="foreground" x="50" y="125" fill="#12306b">01 审核</text></g></g></g>
<g id="delivery-group" data-group-id="delivery-group"><g id="delivery" data-group-id="delivery-group"><rect data-paint-role="card" x="390" y="70" width="180" height="100" rx="16" fill="#fafcff" stroke="#8fe0d5"/><g data-region="delivery-region" data-bounds="400,80,160,80"><text id="delivery-text" data-content-id="delivery-text" data-paint-role="foreground" x="410" y="125" fill="#12306b">02 交付</text></g></g></g>
<path id="advance" d="M210 120 L390 120" fill="none" stroke="#46618f" marker-end="url(#arrow)" data-from="review" data-to="delivery" data-kind="data-flow" data-condition="通过" data-line-style="flow"/>
<g data-region="labels" data-bounds="225,65,140,45"><text id="condition-text" data-content-id="condition-text" x="260" y="95" fill="#26406e">通过</text></g>
<g data-region="legend-region" data-bounds="20,220,560,50"><text id="legend-text" data-content-id="legend-text" x="30" y="250" fill="#46618f">实线：资料流转</text></g>
</svg>'''
    paint_blue = {'kind': 'solid', 'fill': '#fafcff', 'stroke': '#8db8ff', 'accent': '#2468ee', 'foreground': '#12306b'}
    paint_teal = {**paint_blue, 'stroke': '#8fe0d5', 'accent': '#0b8f86'}
    data = {
        'schema_version': 1,
        'confirmation': {'status': 'simulated', 'evidence': 'Explicit isolated test fixture; never actual user authorization.'},
        'diagram': {'id': 'demo', 'filename': 'demo.svg', 'title': '演示流程', 'description': '虚构：审核通过后交付。', 'topology': 'left-to-right', 'detail_level': 'medium', 'viewBox': [0, 0, 600, 300], 'width': 600, 'height': 300, 'display_width': 600,
                    'background': {'id': 'background', 'gradient': {'id': 'bg', 'stops': [{'offset': 0, 'color': '#f4f9ff'}, {'offset': 1, 'color': '#e9f2ff'}], 'direction': [0, 0, 0, 1]}}, 'defaults': {'fill': '#26406e', 'stroke': 'none', 'color': '#26406e'}},
        'texts': [{'id': 'review-text', 'value': '01 审核', 'region': 'review-region', 'fill': '#12306b'}, {'id': 'delivery-text', 'value': '02 交付', 'region': 'delivery-region', 'fill': '#12306b'}, {'id': 'condition-text', 'value': '通过', 'region': 'labels', 'fill': '#26406e'}, {'id': 'legend-text', 'value': '实线：资料流转', 'region': 'legend-region', 'fill': '#46618f'}],
        'nodes': [{'id': 'review', 'group': 'review-group', 'title_text': 'review-text'}, {'id': 'delivery', 'group': 'delivery-group', 'title_text': 'delivery-text'}],
        'groups': [{'id': 'review-group', 'members': ['review'], 'paint': paint_blue, 'reason': '本图审核选蓝，不绑定治理橙色'}, {'id': 'delivery-group', 'members': ['delivery'], 'paint': paint_teal, 'reason': '本图交付选青绿，不绑定消费蓝色'}],
        'relations': [{'id': 'advance', 'from': 'review', 'to': 'delivery', 'kind': 'data-flow', 'condition': '通过', 'line_style': 'flow', 'label_text': 'condition-text'}],
        'line_styles': [{'id': 'flow', 'stroke': '#46618f', 'dasharray': '', 'meaning': '资料流转', 'legend_text': 'legend-text', 'marker': 'arrow'}],
        'visible_elements': ['background', 'review-group', 'review', 'review-text', 'delivery-group', 'delivery', 'delivery-text', 'advance', 'condition-text', 'legend-text'],
        'assumptions': ['虚构测试'], 'fallback': {'allowed': False, 'description': '不改变测试范围'}}
    return source, data


def replace(source, data, before, after):
    assert before in source, f'Mutation source missing: {before}'
    return source.replace(before, after, 1), data


def add_icon(source, data, explicit_color=True):
    symbol = '<symbol id="icon-dot" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="currentColor"/></symbol>'
    color = ' color="#2468ee"' if explicit_color else ''
    source = source.replace('</defs>', symbol + '</defs>')
    source = source.replace('<g id="review" data-group-id="review-group">', '<g id="review" data-group-id="review-group"><use id="review-icon" href="#icon-dot" data-paint-role="accent" x="170" y="80" width="24" height="24"' + color + '/>')
    data['visible_elements'].append('review-icon')
    return source, data


def add_header(source, data):
    source = source.replace('</defs>', '<linearGradient id="header-gradient" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3b8bff"/><stop offset="1" stop-color="#1b57e0"/></linearGradient></defs>')
    source = source.replace('<g id="review" data-group-id="review-group">', '<g id="review" data-group-id="review-group"><rect data-paint-role="header" x="30" y="70" width="180" height="30" fill="url(#header-gradient)"/>')
    data['groups'][0]['paint']['kind'] = 'gradient'
    data['groups'][0]['paint']['header_gradient'] = {'id': 'header-gradient', 'stops': [{'offset': 0, 'color': '#3b8bff'}, {'offset': 1, 'color': '#1b57e0'}], 'direction': [0, 0, 1, 1]}
    return source, data


def url_literal_condition(source, data):
    literal = '请使用url(api)'
    source = source.replace('data-condition="通过"', 'data-condition="' + literal + '"', 1)
    source = source.replace('>通过</text>', '>' + literal + '</text>', 1)
    data['relations'][0]['condition'] = literal
    data['texts'][2]['value'] = literal
    return source, data


def add_group_card(source, data, wrong=False):
    stroke = '#b7bfff' if wrong else '#8db8ff'
    card = '<rect id="review-banner" data-paint-role="card" x="30" y="40" width="180" height="20" fill="#fafcff" stroke="' + stroke + '"/>'
    source = source.replace('<g id="review-group" data-group-id="review-group">', '<g id="review-group" data-group-id="review-group">' + card, 1)
    data['visible_elements'].append('review-banner')
    return source, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    source, data = fixture()
    cases = []
    def case(name, mutate=None, expected_check=None, expected_exit=1, expected_ok=False, manifest=True, example=True):
        svg, acceptance = source, copy.deepcopy(data)
        if mutate:
            svg, acceptance = mutate(svg, acceptance)
        result = validator.validate_source(svg, acceptance=acceptance if manifest else None, example_mode=example)
        check_failed = expected_check is None or result['checks'].get(expected_check) is False
        passed = result['ok'] is expected_ok and result['exit_code'] == expected_exit and check_failed
        cases.append({'name': name, 'passed': passed, 'expected_exit': expected_exit, 'actual_exit': result['exit_code'], 'expected_check': expected_check, 'actual_errors': result['errors']})
        return result
    case('approved-semantic-free-palette', expected_exit=0, expected_ok=True)
    case('exact-whitelist-with-opacity', lambda s, d: replace(s, d, '<rect id="background"', '<rect fill-opacity="0.12" id="background"'), expected_exit=0, expected_ok=True)
    case('case-normalization-is-not-approximation', lambda s, d: replace(s, d, 'fill="#fafcff"', 'fill="#FAFCFF"'), expected_exit=0, expected_ok=True)
    case('business-url-literal-is-not-a-resource', url_literal_condition, expected_exit=0, expected_ok=True)
    case('non-node-group-card-approved-paint', add_group_card, expected_exit=0, expected_ok=True)
    case('non-node-group-card-wrong-legal-paint', lambda s, d: add_group_card(s, d, True), 'approved_paint_mapping')
    case('controlled-symbol-current-color', add_icon, expected_exit=0, expected_ok=True)
    case('icon-with-uncontrolled-default-color', lambda s, d: add_icon(s, d, False), 'palette_colors')
    case('frozen-gradient-header-keeps-card-pure', add_header, expected_exit=0, expected_ok=True)
    def wrong_header(s, d):
        s, d = add_header(s, d)
        return s.replace('stop-color="#3b8bff"', 'stop-color="#17b9a5"'), d
    case('legal-color-but-wrong-gradient-stop', wrong_header, 'approved_paint_mapping')
    case('xml-damaged', lambda s, d: (s[:-6], d), 'parseable_xml')
    case('duplicate-id', lambda s, d: replace(s, d, 'id="delivery"', 'id="review"'), 'unique_ids')
    case('dangling-ref', lambda s, d: replace(s, d, 'url(#bg)', 'url(#missing)'), 'internal_references')
    case('external-resource', lambda s, d: replace(s, d, 'url(#bg)', 'url(https://example.invalid/x.svg)'), 'self_contained_resources')
    case('raster-image', lambda s, d: replace(s, d, '</svg>', '<image href="data:image/png;base64,AA"/></svg>'), 'vector_only')
    case('script', lambda s, d: replace(s, d, '</svg>', '<script>alert(1)</script></svg>'), 'no_active_or_foreign_content')
    case('smil-discard', lambda s, d: replace(s, d, '</svg>', '<discard href="#review" begin="0s"/></svg>'), 'no_active_or_foreign_content')
    case('empty-title', lambda s, d: replace(s, d, '>演示流程</title>', '></title>'), 'accessible_description')
    case('invalid-canvas', lambda s, d: replace(s, d, 'width="600"', 'width="0"'), 'width')
    case('missing-editable-text', lambda s, d: (re_remove_text(s), d), 'editable_text')
    for token in ('#3b8bfe', '#fff', '#ffffff80', 'red', 'rgb(255,255,255)', 'rgba(255,255,255,.5)', 'hsl(0,0%,100%)', 'var(--color)', 'transparent'):
        case('illegal-paint-' + token, lambda s, d, token=token: replace(s, d, 'fill="#fafcff"', 'fill="' + token + '"'), 'palette_colors')
    case('illegal-unused-def', lambda s, d: replace(s, d, '</defs>', '<linearGradient id="unused"><stop offset="0" stop-color="#112233"/></linearGradient></defs>'), 'palette_colors')
    case('style-paint-bypass', lambda s, d: replace(s, d, 'text{font-family:', 'text{fill:#ffffff;font-family:'), 'css_subset')
    case('style-hidden-bypass', lambda s, d: replace(s, d, 'text{font-family:', 'text{display:none;font-family:'), 'css_subset')
    case('css-important', lambda s, d: replace(s, d, 'font-family:"Microsoft', 'font-weight:700!important;font-family:"Microsoft'), 'css_subset')
    case('implicit-black', lambda s, d: (s.replace('fill="#26406e" stroke="none" color="#26406e"', 'stroke="none" color="#26406e"', 1).replace('fill="#fafcff"', '', 1), d), 'palette_colors')
    case('explicit-hidden-text', lambda s, d: replace(s, d, 'id="review-text"', 'opacity="0" id="review-text"'), 'frozen_text')
    case('zero-text-fill-opacity', lambda s, d: replace(s, d, 'id="review-text"', 'fill-opacity="0" id="review-text"'), 'frozen_text')
    case('wrong-text-object', lambda s, d: replace(s, d, '>01 审核</text>', '>03 缺失</text>'), 'frozen_text')
    case('wrong-approved-color', lambda s, d: replace(s, d, 'stroke="#8db8ff"', 'stroke="#b7bfff"'), 'approved_paint_mapping')
    case('nan-region', lambda s, d: replace(s, d, 'data-bounds="40,80,160,80"', 'data-bounds="NaN,80,160,80"'), 'text_regions')
    case('missing-region', lambda s, d: replace(s, d, 'data-region="review-region"', 'data-omitted="review-region"'), 'text_regions')
    case('transformed-text-region', lambda s, d: replace(s, d, 'id="review-text"', 'transform="translate(0 0)" id="review-text"'), 'text_regions')
    case('nested-svg-text-viewport', lambda s, d: (s.replace('<text id="review-text"', '<svg><text id="review-text"', 1).replace('>01 审核</text>', '>01 审核</text></svg>', 1), d), 'text_regions')
    case('new-visible-element', lambda s, d: replace(s, d, '</svg>', '<rect id="extra" width="10" height="10" fill="#ffffff"/></svg>'), 'visible_registration')
    case('unregistered-icon-instance', lambda s, d: replace(s, d, '</svg>', '<use href="#notfound" color="#2468ee"/></svg>'), 'visible_registration')
    case('wrong-condition', lambda s, d: replace(s, d, 'data-condition="通过"', 'data-condition="拒绝"'), 'frozen_relations')
    case('wrong-marker-color', lambda s, d: replace(s, d, 'd="M0 0 L9 5 L0 10Z" fill="#46618f"', 'd="M0 0 L9 5 L0 10Z" fill="#26406e"'), 'approved_paint_mapping')
    case('simulation-not-real-approval', expected_check='acceptance_schema', expected_exit=2, example=False)
    case('empty-manifest-texts', lambda s, d: (s, {**d, 'texts': []}), 'acceptance_schema', 2)
    case('legacy-mode-is-not-production', expected_exit=0, expected_ok=True, manifest=False)
    legacy = validator.validate_source(source, expected=('不存在',))
    cases.append({'name': 'legacy-keyword-not-found', 'passed': not legacy['ok'] and not legacy['checks']['expected_text'] and not legacy['production_ready'], 'actual_exit': legacy['exit_code']})
    legacy_hidden = validator.validate_source(source.replace('id="review-text"', 'display="none" id="review-text"', 1), expected=('01 审核',))
    cases.append({'name': 'legacy-hidden-keyword-cannot-pass', 'passed': not legacy_hidden['ok'] and not legacy_hidden['checks']['expected_text'], 'actual_exit': legacy_hidden['exit_code']})
    legacy_concat = validator.validate_source(source, expected=('01 审核02 交付',))
    cases.append({'name': 'legacy-texts-cannot-concatenate', 'passed': not legacy_concat['ok'] and not legacy_concat['checks']['expected_text'], 'actual_exit': legacy_concat['exit_code']})
    empty_expected = validator.validate_source(source, expected=('',))
    cases.append({'name': 'empty-keyword-configuration-rejected', 'passed': not empty_expected['ok'] and empty_expected['exit_code'] == 2 and not empty_expected['checks']['expected_configuration'], 'actual_exit': empty_expected['exit_code']})
    with tempfile.TemporaryDirectory(prefix='editable-svg-check-') as temp:
        temp = Path(temp)
        svg = temp / 'demo.svg'
        ac = temp / 'acceptance.json'
        svg.write_text(source, encoding='utf-8')
        ac.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        cmd = [sys.executable, str(PACKAGE / 'scripts' / 'validate_svg.py'), str(svg), '--acceptance', str(ac), '--example-mode']
        run = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        payload = json.loads(run.stdout)
        cases.append({'name': 'cli-current-file-hashes', 'passed': run.returncode == 0 and payload['production_ready'] and payload['svg_sha256'] == validator.sha256(svg.read_bytes()) and payload['acceptance_sha256'] == validator.sha256(ac.read_bytes()), 'actual_exit': run.returncode})
        invalid = subprocess.run(cmd + ['--unknown'], capture_output=True, text=True, encoding='utf-8')
        cases.append({'name': 'cli-unknown-arg', 'passed': invalid.returncode == 2 and json.loads(invalid.stdout)['status'] == '失败', 'actual_exit': invalid.returncode})
        duplicate = subprocess.run(cmd + ['--acceptance', str(ac)], capture_output=True, text=True, encoding='utf-8')
        cases.append({'name': 'cli-duplicate-arg', 'passed': duplicate.returncode == 2, 'actual_exit': duplicate.returncode})
        before_svg, before_acceptance = svg.read_bytes(), ac.read_bytes()
        collision = subprocess.run(cmd + ['--report', str(svg)], capture_output=True, text=True, encoding='utf-8')
        cases.append({'name': 'report-cannot-overwrite-svg', 'passed': collision.returncode == 2 and svg.read_bytes() == before_svg, 'actual_exit': collision.returncode})
        collision = subprocess.run(cmd + ['--report', str(ac)], capture_output=True, text=True, encoding='utf-8')
        cases.append({'name': 'report-cannot-overwrite-acceptance', 'passed': collision.returncode == 2 and ac.read_bytes() == before_acceptance, 'actual_exit': collision.returncode})
        report_path = temp / 'static.json'
        saved = subprocess.run(cmd + ['--report', str(report_path)], capture_output=True, text=True, encoding='utf-8')
        cases.append({'name': 'report-complete-atomic-write', 'passed': saved.returncode == 0 and json.loads(report_path.read_text(encoding='utf-8'))['ok'] and not list(temp.glob('.static.json.*.tmp')), 'actual_exit': saved.returncode})
        keyword = temp / 'expected.json'
        keyword.write_text('["01 审核"]', encoding='utf-8')
        old = subprocess.run([sys.executable, str(PACKAGE / 'scripts' / 'validate_svg.py'), str(svg), '--expected-file', str(keyword)], capture_output=True, text=True, encoding='utf-8')
        payload = json.loads(old.stdout)
        cases.append({'name': 'cli-legacy-explicitly-not-ready', 'passed': old.returncode == 0 and not payload['production_ready'] and any(r['key'] == 'frozen_acceptance' and r['status'] == '未执行' for r in payload['results']), 'actual_exit': old.returncode})
    result = {'scope': 'Isolated current validator behavior; not a rendering/visual-quality proof', 'ok': all(c['passed'] for c in cases), 'case_count': len(cases), 'cases': cases, 'temporary_files_cleaned': True}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': result['ok'], 'case_count': len(cases), 'failed_cases': [c for c in cases if not c['passed']], 'temporary_files_cleaned': True}, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


def re_remove_text(source):
    root = ET.fromstring(source)
    parents = {child: node for node in root.iter() for child in node}
    for node in list(root.iter()):
        if node.tag == '{' + NS + '}text':
            parents[node].remove(node)
    return ET.tostring(root, encoding='unicode')


if __name__ == '__main__':
    sys.exit(main())
