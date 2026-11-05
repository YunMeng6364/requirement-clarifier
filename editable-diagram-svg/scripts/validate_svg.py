#!/usr/bin/env python3
"""Stdlib checks for the skill's closed, editable SVG subset.

0: required static checks pass; 1: SVG/check failure; 2: configuration/manifest
error; 3: environment blocked. An ok structural-only report is not production
acceptance. Rendering, actual relation geometry and visual review are separate.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET

SVG_NS = 'http://www.w3.org/2000/svg'
NUMBER = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
DIMENSION = re.compile(rf'^\s*({NUMBER})(?:px|pt|pc|mm|cm|in)?\s*$')
HEX = re.compile(r'#[0-9a-fA-F]{6}\Z')
URL = re.compile(r'''url\(\s*(?:"(#[A-Za-z_][\w.:-]*)"|'(#[A-Za-z_][\w.:-]*)'|(#[A-Za-z_][\w.:-]*))\s*\)\Z''')
PAINTS = {'fill', 'stroke', 'color', 'stop-color', 'flood-color', 'lighting-color'}
OPACITIES = {'opacity', 'fill-opacity', 'stroke-opacity', 'stop-opacity', 'flood-opacity'}
FONT_CSS = {'font-family', 'font-size', 'font-weight', 'font-style'}
INLINE_CSS = FONT_CSS | PAINTS | OPACITIES | {
    'display', 'visibility', 'stroke-width', 'stroke-dasharray', 'stroke-dashoffset',
    'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'text-anchor',
    'dominant-baseline', 'letter-spacing', 'word-spacing', 'fill-rule',
    'clip-rule', 'clip-path', 'mask', 'filter', 'marker-start', 'marker-mid', 'marker-end'}
RESOURCE_URL_ATTRIBUTES = PAINTS | {'style', 'filter', 'clip-path', 'mask', 'marker-start', 'marker-mid', 'marker-end', 'cursor'}
NON_DISPLAY = {'defs', 'title', 'desc', 'metadata', 'style', 'symbol', 'clipPath', 'mask', 'marker', 'pattern'}
DRAWABLE = {'rect', 'circle', 'ellipse', 'path', 'line', 'polyline', 'polygon', 'text', 'tspan', 'use'}
FORBIDDEN = {'script', 'foreignobject', 'image', 'animate', 'animatecolor', 'animatemotion', 'animatetransform', 'set', 'discard'}
TOPOLOGIES = {'nested', 'left-to-right', 'hub-and-spoke', 'timeline', 'grid', 'tree', 'funnel', 'comparison'}
DETAILS = {'high-level', 'medium', 'detailed'}
# Digest of the exact 47-value set, rather than a second editable palette.
PALETTE_SET_DIGEST = '08dcf5a06064bfe0bb3a1f4572f693ec126b1a7da9101429fe8437cfc29862cc'
PALETTE_PATH = Path(__file__).resolve().parents[1] / 'references' / 'palette.json'


def local_name(name):
    return name.rsplit('}', 1)[-1]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def finite(value, positive=False):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and (not positive or value > 0)


def same_paint(actual, expected):
    if isinstance(actual, str) and isinstance(expected, str) and HEX.fullmatch(actual) and HEX.fullmatch(expected):
        return actual.lower() == expected.lower()
    return actual == expected


def read_json(value):
    if isinstance(value, dict):
        data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return value, sha256(data)
    data = Path(value).read_bytes()
    return json.loads(data.decode('utf-8-sig')), sha256(data)


def load_palette():
    data = PALETTE_PATH.read_bytes()
    values = json.loads(data.decode('utf-8-sig'))
    if not isinstance(values, list) or len(values) != 47 or any(not isinstance(v, str) or not HEX.fullmatch(v) for v in values):
        raise ValueError('palette.json must contain exactly 47 six-digit hex values.')
    normalized = [v.lower() for v in values]
    if len(set(normalized)) != 47 or sha256('\n'.join(sorted(normalized)).encode('ascii')) != PALETTE_SET_DIGEST:
        raise ValueError('palette.json differs from the approved 47-value set.')
    return set(normalized), sha256(data)


def declarations(raw, allowed):
    """Parse a closed CSS declaration list, preserving quoted font families."""
    raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.S)
    if any(token in raw for token in ('\\', '@', '!', '{', '}', 'var(')):
        raise ValueError('Unsupported CSS escape, at-rule, important, variable or block.')
    pieces, part, quote, depth = [], [], None, 0
    for char in raw:
        if quote:
            part.append(char)
            if char == quote:
                quote = None
        elif char in '\"\'':
            quote = char
            part.append(char)
        elif char == '(':
            depth += 1
            part.append(char)
        elif char == ')':
            depth -= 1
            if depth < 0:
                raise ValueError('Unbalanced CSS parentheses.')
            part.append(char)
        elif char == ';' and depth == 0:
            pieces.append(''.join(part).strip())
            part = []
        else:
            part.append(char)
    if quote or depth:
        raise ValueError('Unclosed CSS quote or parentheses.')
    pieces.append(''.join(part).strip())
    result = {}
    for item in pieces:
        if not item:
            continue
        if ':' not in item:
            raise ValueError('CSS declaration needs a colon.')
        name, value = [p.strip() for p in item.split(':', 1)]
        name = name.lower()
        if name not in allowed or not value or name in result:
            raise ValueError(f'Unsupported, empty or duplicate CSS declaration: {name}')
        result[name] = value
    return result


def stylesheet(raw):
    raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.S).strip()
    if re.search(r'url\s*\(', raw, re.I):
        raise ValueError('Stylesheet font rules cannot contain resource URLs.')
    if any(token in raw for token in ('@', '\\', '!', ':', 'var(')):
        # Colons inside declarations are required; reject selector pseudos below.
        if any(token in raw for token in ('@', '\\', '!', 'var(')):
            raise ValueError('Unsupported stylesheet construct.')
    while raw:
        match = re.match(r'([^{}]+)\{([^{}]*)\}', raw, re.S)
        if not match:
            raise ValueError('Unsupported or malformed stylesheet block.')
        selectors = [s.strip() for s in match[1].split(',')]
        if any(not re.fullmatch(r'(?:\*|(?:text|tspan)?(?:[.#][A-Za-z_][\w-]*)?|text|tspan)', s) or not s for s in selectors):
            raise ValueError('Only plain text/tspan/id/class font selectors are supported.')
        declarations(match[2], FONT_CSS)
        raw = raw[match.end():].strip()


def text_value(element):
    spans = [child for child in element if local_name(child.tag) == 'tspan']
    if spans:
        # Ignore only indentation between tspans; actual span characters stay exact.
        if element.text and element.text.strip():
            raise ValueError('Text with tspans cannot mix direct content and spans.')
        if any(child.tail and child.tail.strip() for child in spans):
            raise ValueError('Text after tspans must be inside a span.')
        return unicodedata.normalize('NFC', ''.join(''.join(child.itertext()) for child in spans))
    return unicodedata.normalize('NFC', element.text or '')


class Report:
    def __init__(self, source, svg_path):
        self.value = {'schema_version': 1, 'stage': 'static', 'status': '未执行', 'ok': False,
                      'svg_path': str(Path(svg_path).resolve()), 'svg_sha256': sha256(source.encode('utf-8')),
                      'acceptance_sha256': None, 'palette_sha256': None, 'checks': {}, 'results': [],
                      'errors': [], 'limitations': ['Static checks do not prove glyphs, overlap, actual arrow targets, content truth or visual quality.'],
                      'production_ready': False, 'exit_code': 0}

    def add(self, key, passed, reason='', evidence=None, code=1, required=True, status=None):
        status = status or ('通过' if passed else '失败')
        self.value['results'].append({'key': key, 'status': status, 'reason': reason, 'evidence': evidence or [], 'required': required})
        if status in {'通过', '失败'}:
            self.value['checks'][key] = bool(passed)
        if status == '失败':
            self.value['errors'].append({'check': key, 'message': reason})
            self.value['exit_code'] = max(self.value['exit_code'], code if code != 3 else 1)
        elif status == '环境受阻' and self.value['exit_code'] == 0:
            self.value['exit_code'] = 3

    def finish(self):
        required = [r for r in self.value['results'] if r['required']]
        statuses = {r['status'] for r in required}
        self.value['status'] = '失败' if '失败' in statuses else '环境受阻' if '环境受阻' in statuses else '未执行' if '未执行' in statuses else '通过'
        self.value['ok'] = self.value['status'] == '通过'
        self.value['production_ready'] = self.value['ok'] and self.value['checks'].get('frozen_acceptance', False)
        return self.value


def validate_source(source, expected=(), acceptance=None, example_mode=False, svg_path='memory.svg'):
    report = Report(source, svg_path)
    if not isinstance(expected, (list, tuple)) or any(not isinstance(word, str) or not word.strip() for word in expected):
        report.add('expected_configuration', False, 'Expected strings must be nonempty.', code=2)
        return report.finish()
    try:
        palette, palette_hash = load_palette()
        report.value['palette_sha256'] = palette_hash
        report.add('palette_config', True)
    except PermissionError as error:
        report.add('palette_config', False, str(error), status='环境受阻')
        return report.finish()
    except (OSError, UnicodeError, ValueError) as error:
        report.add('palette_config', False, str(error), code=2)
        return report.finish()
    manifest = None
    if acceptance is not None:
        try:
            manifest, acceptance_hash = read_json(acceptance)
            report.value['acceptance_sha256'] = acceptance_hash
            manifest_schema(manifest, palette, example_mode)
            report.add('acceptance_schema', True)
        except PermissionError as error:
            report.add('acceptance_schema', False, str(error), status='环境受阻')
            return report.finish()
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as error:
            report.add('acceptance_schema', False, str(error), code=2)
            return report.finish()
    else:
        report.add('frozen_acceptance', False, 'No acceptance manifest: only structural/legacy checks requested.', status='未执行', required=False)
    no_dtd = not re.search(r'<!\s*(?:DOCTYPE|ENTITY)\b', source, re.I)
    report.add('no_dtd_entities', no_dtd, 'DTD/entity declarations are forbidden.' if not no_dtd else '')
    report.add('no_stylesheet_processing_instruction', not re.search(r'<\?xml-stylesheet\b', source, re.I), 'Stylesheet processing instructions are forbidden.')
    if not no_dtd:
        return report.finish()
    try:
        root = ET.fromstring(source)
    except (ET.ParseError, ValueError) as error:
        report.add('parseable_xml', False, str(error))
        return report.finish()
    report.add('parseable_xml', True)
    report.add('svg_root', root.tag == f'{{{SVG_NS}}}svg', 'Root must be SVG in the SVG namespace.')
    report.add('svg_elements_only', all(n.tag.startswith('{' + SVG_NS + '}') for n in root.iter()), 'Foreign namespace elements are outside the editable SVG subset.')
    for key in ('width', 'height'):
        match = DIMENSION.fullmatch(root.get(key, ''))
        report.add(key, bool(match) and math.isfinite(float(match[1])) and float(match[1]) > 0, f'{key} must be an explicit positive length.')
    try:
        vb = [float(n) for n in re.split(r'[\s,]+', root.get('viewBox', '').strip())]
        valid_vb = len(vb) == 4 and all(math.isfinite(n) for n in vb) and vb[2] > 0 and vb[3] > 0
    except ValueError:
        vb, valid_vb = [], False
    report.add('viewBox', valid_vb, 'viewBox requires four finite numbers and positive area.')
    parents = {child: node for node in root.iter() for child in node}
    ids, duplicate, refs, external, forbidden, css_errors = {}, [], [], [], [], []
    inline = {}
    for node in root.iter():
        tag = local_name(node.tag)
        identifier = node.get('id')
        if identifier is not None:
            if not identifier or identifier in ids:
                duplicate.append(identifier)
            ids[identifier] = node
        if tag.lower() in FORBIDDEN:
            forbidden.append(tag)
        try:
            inline[node] = declarations(node.get('style', ''), INLINE_CSS)
            if tag == 'style':
                stylesheet(''.join(node.itertext()))
        except ValueError as error:
            css_errors.append(f'{identifier or tag}: {error}')
            inline[node] = {}
        for name, value in node.attrib.items():
            attr = local_name(name)
            if attr.lower().startswith('on'):
                forbidden.append(f'{tag}@{attr}')
            if attr in {'href', 'src'}:
                if re.fullmatch(r'#[A-Za-z_][\w.:-]*', value):
                    refs.append(value[1:])
                else:
                    external.append(value)
            if name == '{http://www.w3.org/XML/1998/namespace}base':
                external.append(value)
            if attr in {'aria-labelledby', 'aria-describedby'}:
                refs.extend(value.split())
            if attr in RESOURCE_URL_ATTRIBUTES and 'url' in value.lower():
                urls = list(re.finditer(r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*))\s*\)''', value, re.I))
                if len(re.findall(r'url\s*\(', value, re.I)) != len(urls):
                    external.append(f'Malformed url: {value}')
                for match in urls:
                    target = next(v for v in match.groups() if v is not None).strip()
                    (refs if re.fullmatch(r'#[A-Za-z_][\w.:-]*', target) else external).append(target[1:] if target.startswith('#') else target)
    report.add('unique_ids', not duplicate, f'Empty/duplicate IDs: {duplicate}')
    report.add('internal_references', not (set(refs) - ids.keys()), f'Missing IDs: {sorted(set(refs) - ids.keys())}')
    report.add('self_contained_resources', not external, f'External or malformed resources: {external}')
    report.add('no_active_or_foreign_content', not forbidden, f'Forbidden SVG content: {forbidden}')
    report.add('vector_only', not any(local_name(n.tag).lower() == 'image' for n in root.iter()), 'All image elements are forbidden.')
    report.add('css_subset', not css_errors, '; '.join(css_errors))
    titles = [n for n in root if local_name(n.tag) == 'title']
    descs = [n for n in root if local_name(n.tag) == 'desc']
    report.add('accessible_description', len(titles) == 1 and len(descs) == 1 and bool(''.join(titles[0].itertext()).strip()) and bool(''.join(descs[0].itertext()).strip()) and bool(root.get('aria-labelledby')), 'One nonempty title/desc and aria-labelledby are required.')

    def inherited(node, key):
        while node is not None:
            if key in inline[node]:
                return inline[node][key]
            if key in node.attrib:
                return node.get(key)
            node = parents.get(node)
        return None

    def ancestor(node, tags):
        while node is not None:
            if local_name(node.tag) in tags:
                return node
            node = parents.get(node)
        return None

    def hidden(node):
        current = node
        while current is not None:
            attrs = {**current.attrib, **inline[current]}
            if attrs.get('display', '').lower() == 'none' or attrs.get('visibility', '').lower() in {'hidden', 'collapse'}:
                return True
            for key in ('opacity', 'fill-opacity'):
                try:
                    if key in attrs and float(attrs[key]) == 0:
                        return True
                except ValueError:
                    return True
            current = parents.get(current)
        return False

    paint_errors, opacity_errors = [], []
    for node in root.iter():
        tag = local_name(node.tag)
        attrs = {**{local_name(k): v for k, v in node.attrib.items()}, **inline[node]}
        for key in OPACITIES:
            if key in attrs:
                try:
                    value = float(attrs[key])
                    if not math.isfinite(value) or not 0 <= value <= 1:
                        raise ValueError()
                except ValueError:
                    opacity_errors.append(f'{node.get("id", tag)}@{key}')
        for key in PAINTS:
            if key not in attrs:
                continue
            value = attrs[key]
            if HEX.fullmatch(value) and value.lower() in palette:
                continue
            if value == 'none' and key in {'fill', 'stroke'}:
                continue
            symbol = ancestor(node, {'symbol'})
            if value == 'currentColor' and key in {'fill', 'stroke'} and symbol is not None and (symbol.get('id') or '').startswith('icon-'):
                continue
            url = URL.fullmatch(value) if key in {'fill', 'stroke'} else None
            target = next((v[1:] for v in url.groups() if v), '') if url else ''
            if url and target in ids and local_name(ids[target].tag) in {'linearGradient', 'radialGradient'}:
                continue
            paint_errors.append(f'{node.get("id", tag)}@{key}={value}')
        if tag in {'stop', 'feDropShadow', 'feFlood', 'feDiffuseLighting', 'feSpecularLighting'}:
            required = 'stop-color' if tag == 'stop' else 'lighting-color' if 'Lighting' in tag else 'flood-color'
            value = inherited(node, required)
            if not value or not HEX.fullmatch(value) or value.lower() not in palette:
                paint_errors.append(f'{node.get("id", tag)} missing explicit {required}')
        if tag in DRAWABLE and tag not in {'use', 'tspan'}:
            for key in ('fill', 'stroke'):
                value = inherited(node, key)
                if value is None and key == 'stroke':
                    # SVG's stroke default is no drawing, not an uncontrolled color.
                    continue
                if value is None:
                    paint_errors.append(f'{node.get("id", tag)} missing effective {key}')
        if tag == 'use':
            target = node.get('href', node.get('{http://www.w3.org/1999/xlink}href', ''))
            if target.startswith('#') and target[1:] in ids and local_name(ids[target[1:]].tag) == 'symbol':
                value = inline[node].get('color', node.get('color', ''))
                if not HEX.fullmatch(value) or value.lower() not in palette:
                    paint_errors.append(f'{node.get("id", "use")} needs explicit whitelisted color')
            else:
                paint_errors.append(f'{node.get("id", "use")} must reference an internal icon symbol')
    report.add('palette_colors', not paint_errors, '; '.join(paint_errors))
    report.add('opacity_values', not opacity_errors, f'Invalid opacity: {opacity_errors}')
    text_nodes = [n for n in root.iter() if local_name(n.tag) == 'text' and ancestor(n, NON_DISPLAY) is None]
    values, displayed_values = [], []
    text_errors = []
    for node in text_nodes:
        try:
            value = text_value(node)
            values.append(value)
            if not hidden(node) and not any(hidden(n) for n in node.iter()):
                displayed_values.append(value)
        except ValueError as error:
            text_errors.append(str(error))
    report.add('editable_text', bool(displayed_values) and any(v.strip() for v in displayed_values) and not text_errors, '; '.join(text_errors) or 'Nonempty visible editable text is required.')
    missing = [word for word in expected if not any(unicodedata.normalize('NFC', word) in value for value in displayed_values)]
    report.add('expected_text', not missing, f'Missing expected text: {missing}')
    report.value['visible_text_count'] = len(text_nodes)
    report.value['expected_text_count'] = len(expected)
    if manifest is not None and not duplicate:
        errors = check_manifest(root, manifest, ids, parents, inline, inherited, hidden, text_nodes, palette)
        for key, messages in errors.items():
            report.add(key, not messages, '; '.join(messages))
        report.add('frozen_acceptance', not any(errors.values()), 'All frozen object/text/paint/relationship checks must pass.')
    elif manifest is not None:
        report.add('frozen_acceptance', False, 'Cannot match a manifest against duplicate IDs.')
    report.add('visual_review', False, 'Actual rendering and human/agent visual review are separate required delivery stages.', status='未执行', required=False)
    return report.finish()


def manifest_schema(data, palette, example_mode):
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    def string(value):
        return isinstance(value, str) and bool(value.strip())
    def color(value):
        return isinstance(value, str) and bool(HEX.fullmatch(value)) and value.lower() in palette
    require(isinstance(data, dict) and data.get('schema_version') == 1, 'Acceptance schema_version must be 1.')
    confirmation = data.get('confirmation', {})
    require(isinstance(confirmation, dict) and confirmation.get('status') in ({'approved', 'simulated'} if example_mode else {'approved'}) and string(confirmation.get('evidence')), 'Actual approved confirmation evidence is required; simulated only with --example-mode.')
    diagram = data.get('diagram', {})
    require(isinstance(diagram, dict), 'diagram must be an object.')
    for key in ('id', 'filename', 'title', 'description'):
        require(string(diagram.get(key)), f'diagram.{key} must be nonempty.')
    require(diagram['filename'].endswith('.svg') and Path(diagram['filename']).name == diagram['filename'], 'diagram.filename must be an SVG basename.')
    require(diagram.get('topology') in TOPOLOGIES and diagram.get('detail_level') in DETAILS, 'Unknown topology/detail level.')
    vb = diagram.get('viewBox')
    require(isinstance(vb, list) and len(vb) == 4 and all(finite(v) for v in vb) and vb[2] > 0 and vb[3] > 0, 'Invalid acceptance viewBox.')
    for key in ('width', 'height', 'display_width'):
        require(finite(diagram.get(key), True), f'Invalid diagram.{key}.')
    require('background' in diagram and 'defaults' in diagram, 'diagram.background/defaults must be explicit, possibly null.')
    defaults = diagram['defaults']
    require(defaults is None or isinstance(defaults, dict) and set(defaults) == {'fill', 'stroke', 'color'} and color(defaults['fill']) and (defaults['stroke'] == 'none' or color(defaults['stroke'])) and color(defaults['color']), 'Invalid diagram.defaults.')
    background = diagram['background']
    if background is not None:
        require(isinstance(background, dict) and string(background.get('id')), 'Invalid background ID.')
        require(('fill' in background) != ('gradient' in background), 'Background must have exactly fill or gradient.')
        if 'fill' in background:
            require(color(background['fill']), 'Invalid background fill.')
        else:
            gradient_schema(background['gradient'], palette)
    tables = {}
    for key in ('texts', 'nodes', 'groups', 'relations', 'line_styles'):
        items = data.get(key)
        require(isinstance(items, list) and all(isinstance(item, dict) and string(item.get('id')) for item in items), f'{key} must be a list of identified objects.')
        require(len({item['id'] for item in items}) == len(items), f'Duplicate {key} IDs.')
        tables[key] = {item['id']: item for item in items}
    semantic_ids = [item['id'] for key in ('texts', 'nodes', 'groups', 'relations') for item in data[key]]
    require(len(set(semantic_ids)) == len(semantic_ids), 'Text/node/group/relation SVG IDs must be distinct across tables.')
    require(bool(tables['texts']), 'texts must be nonempty.')
    for item in tables['texts'].values():
        require(string(item.get('value')) and string(item.get('region')) and color(item.get('fill')), 'Each text requires value/region/whitelisted fill.')
    for item in tables['groups'].values():
        members, paint = item.get('members'), item.get('paint', {})
        require(isinstance(members, list) and all(v in tables['nodes'] for v in members) and len(set(members)) == len(members), 'Invalid group members.')
        require(isinstance(paint, dict) and paint.get('kind') in {'solid', 'gradient'} and all(color(paint.get(k)) for k in ('fill', 'stroke', 'accent', 'foreground')) and string(item.get('reason')), 'Group paint/reason must be explicit.')
        if paint['kind'] == 'gradient':
            gradient_schema(paint.get('header_gradient'), palette)
        else:
            require('header_gradient' not in paint, 'Solid group cannot contain header_gradient.')
    for item in tables['nodes'].values():
        require(item.get('group') in tables['groups'] and item.get('title_text') in tables['texts'], 'Invalid node group/title reference.')
        require(item['id'] in tables['groups'][item['group']]['members'], 'Node missing from its group membership.')
    for item in tables['line_styles'].values():
        require(color(item.get('stroke')) and isinstance(item.get('dasharray'), str) and string(item.get('meaning')) and item.get('legend_text') in tables['texts'] and string(item.get('marker')), 'Invalid line style or legend reference.')
        if item['dasharray']:
            numbers = re.split(r'[\s,]+', item['dasharray'].strip())
            require(bool(numbers) and all(re.fullmatch(NUMBER, n) and math.isfinite(float(n)) and float(n) >= 0 for n in numbers) and any(float(n) > 0 for n in numbers), 'Invalid dasharray.')
    for item in tables['relations'].values():
        require(item.get('from') in tables['nodes'] and item.get('to') in tables['nodes'] and string(item.get('kind')) and isinstance(item.get('condition'), str) and item.get('line_style') in tables['line_styles'], 'Invalid relation reference/condition.')
        require(item.get('label_text') in tables['texts'] or item.get('label_text') is None and item['condition'] == '', 'Nonempty conditions require a visible label; unconditional relations may use null label_text.')
    visible = data.get('visible_elements')
    require(isinstance(visible, list) and all(string(v) for v in visible) and len(set(visible)) == len(visible), 'visible_elements must contain unique SVG IDs.')
    require(diagram['id'] not in visible, 'The SVG root cannot exempt all visible content.')
    require(isinstance(data.get('assumptions'), list) and all(isinstance(v, str) for v in data['assumptions']), 'assumptions must be a string array.')
    fallback = data.get('fallback')
    require(isinstance(fallback, dict) and isinstance(fallback.get('allowed'), bool) and string(fallback.get('description')), 'Explicit fallback contract required.')


def gradient_schema(data, palette):
    if not isinstance(data, dict) or not isinstance(data.get('id'), str) or not data['id']:
        raise ValueError('Gradient needs an ID.')
    direction, stops = data.get('direction'), data.get('stops')
    if not isinstance(direction, list) or len(direction) != 4 or not all(finite(v) for v in direction):
        raise ValueError('Gradient direction needs four finite numbers.')
    if not isinstance(stops, list) or len(stops) < 2:
        raise ValueError('Gradient needs >=2 stops.')
    for stop in stops:
        if not isinstance(stop, dict) or not finite(stop.get('offset')) or not 0 <= stop['offset'] <= 1 or not isinstance(stop.get('color'), str) or not HEX.fullmatch(stop['color']) or stop['color'].lower() not in palette:
            raise ValueError('Invalid gradient stop.')
    offsets = [s['offset'] for s in stops]
    if offsets != sorted(offsets) or offsets[0] != 0 or offsets[-1] != 1:
        raise ValueError('Gradient offsets must span 0..1 in order.')


def check_manifest(root, data, ids, parents, inline, inherited, hidden, text_nodes, palette):
    errors = {key: [] for key in ('frozen_diagram', 'frozen_text', 'text_regions', 'visible_registration', 'frozen_objects', 'frozen_relations', 'approved_paint_mapping')}
    def test(key, ok, message):
        if not ok:
            errors[key].append(message)
    def is_definition(node):
        while node is not None:
            if local_name(node.tag) in NON_DISPLAY:
                return True
            node = parents.get(node)
        return False
    def region(node):
        while node is not None and node.get('data-region') is None:
            node = parents.get(node)
        return node
    def belongs(node, owner):
        while node is not None:
            if node is owner:
                return True
            node = parents.get(node)
        return False
    diagram = data['diagram']
    test('frozen_diagram', root.get('id') == diagram['id'] and root.get('data-topology') == diagram['topology'] and root.get('data-detail-level') == diagram['detail_level'], 'Root ID/topology/detail differs from acceptance.')
    try:
        actual_vb = [float(n) for n in re.split(r'[\s,]+', root.get('viewBox', '').strip())]
        dimensions = [float(DIMENSION.fullmatch(root.get(k, ''))[1]) for k in ('width', 'height')]
        test('frozen_diagram', actual_vb == diagram['viewBox'] and dimensions == [diagram['width'], diagram['height']], 'Canvas differs from acceptance.')
    except (ValueError, TypeError):
        test('frozen_diagram', False, 'Invalid canvas for manifest matching.')
    for tag, key in (('title', 'title'), ('desc', 'description')):
        nodes = [n for n in root if local_name(n.tag) == tag]
        test('frozen_diagram', len(nodes) == 1 and ''.join(nodes[0].itertext()) == diagram[key], f'{tag} differs from acceptance.')
    if diagram['defaults'] is not None:
        for key, value in diagram['defaults'].items():
            test('approved_paint_mapping', same_paint(inherited(root, key), value), f'Root {key} differs.')
    tables = {name: {item['id']: item for item in data[name]} for name in ('texts', 'nodes', 'groups', 'relations', 'line_styles')}
    actual_text_ids = [node.get('id') for node in text_nodes]
    test('frozen_text', set(actual_text_ids) == tables['texts'].keys() and len(actual_text_ids) == len(tables['texts']), 'Visible text set differs from acceptance.')
    for identifier, item in tables['texts'].items():
        node = ids.get(identifier)
        if node is None or local_name(node.tag) != 'text' or node not in text_nodes:
            test('frozen_text', False, f'Missing visible text {identifier}.')
            continue
        try:
            test('frozen_text', node.get('data-content-id') == identifier and text_value(node) == unicodedata.normalize('NFC', item['value']), f'{identifier} ID or exact text differs.')
        except ValueError as error:
            test('frozen_text', False, f'{identifier}: {error}')
        test('frozen_text', not hidden(node) and not any(hidden(n) for n in node.iter()), f'{identifier} is explicitly hidden.')
        test('approved_paint_mapping', (inherited(node, 'fill') or '').lower() == item['fill'].lower(), f'{identifier} text color differs.')
        owner = region(node)
        test('text_regions', owner is not None and owner.get('data-region') == item['region'], f'{identifier} region missing/different.')
        if owner is not None:
            try:
                bounds = [float(n) for n in owner.get('data-bounds', '').split(',')]
                test('text_regions', len(bounds) == 4 and all(math.isfinite(n) for n in bounds) and bounds[2] > 0 and bounds[3] > 0, f'{identifier} bounds invalid.')
            except ValueError:
                test('text_regions', False, f'{identifier} bounds invalid.')
            current = node
            while current is not None:
                test('text_regions', 'transform' not in current.attrib, f'{identifier} has unsupported transformed text bounds.')
                test('text_regions', current is root or local_name(current.tag) != 'svg', f'{identifier} has an unsupported nested SVG viewport.')
                current = parents.get(current)
    # Identified non-definition elements must be exactly registered. Unidentified
    # plain shapes may belong to a registered container; semantics may not hide there.
    actual_visible = {n.get('id') for n in root.iter() if n is not root and n.get('id') and not is_definition(n)}
    test('visible_registration', actual_visible == set(data['visible_elements']), 'Registered visible ID set differs.')
    for node in root.iter():
        if node is root or is_definition(node) or local_name(node.tag) not in DRAWABLE or local_name(node.tag) == 'tspan':
            continue
        if not node.get('id'):
            current = parents.get(node)
            covered = False
            while current is not None and current is not root:
                if current.get('id') in data['visible_elements']:
                    covered = True
                current = parents.get(current)
            semantic = local_name(node.tag) in {'text', 'use'} or node.get('data-from') is not None
            test('visible_registration', covered and not semantic, 'Unregistered visible shape or semantic instance.')
    actual_nodes = {n.get('id') for n in root.iter() if n.get('data-group-id') and n.get('id') not in tables['groups']}
    test('frozen_objects', actual_nodes == tables['nodes'].keys(), 'Node set differs from acceptance.')
    for identifier, item in tables['groups'].items():
        owner = ids.get(identifier)
        test('frozen_objects', owner is not None and owner.get('data-group-id') == identifier, f'Group {identifier} missing/wrong.')
        declared_members = {n['id'] for n in data['nodes'] if n['group'] == identifier}
        test('frozen_objects', declared_members == set(item['members']), f'Group {identifier} membership differs.')
    for identifier, item in tables['nodes'].items():
        node = ids.get(identifier)
        owner = ids.get(item['group'])
        title = ids.get(item['title_text'])
        test('frozen_objects', node is not None and node.get('data-group-id') == item['group'] and owner is not None and belongs(node, owner), f'Node {identifier} missing/wrong group.')
        test('frozen_objects', node is not None and title is not None and belongs(title, node), f'Node {identifier} title not within node.')
        if node is None:
            continue
        cards = [n for n in node.iter() if n.get('data-paint-role') == 'card']
        paint = tables['groups'][item['group']]['paint']
        test('approved_paint_mapping', bool(cards), f'Node {identifier} lacks card paint role.')
        for card in cards:
            test('approved_paint_mapping', same_paint(inherited(card, 'fill'), paint['fill']) and same_paint(inherited(card, 'stroke'), paint['stroke']), f'Node {identifier} card paint differs.')
    for node in root.iter():
        role = node.get('data-paint-role')
        if not role:
            continue
        if role not in {'card', 'accent', 'foreground', 'header'}:
            test('approved_paint_mapping', False, f'Unknown paint role {role}.')
            continue
        owner = node
        while owner is not None and owner.get('data-group-id') not in tables['groups']:
            owner = parents.get(owner)
        if owner is None:
            test('approved_paint_mapping', False, 'Paint role outside an approved group.')
            continue
        paint = tables['groups'][owner.get('data-group-id')]['paint']
        if role == 'card':
            test('approved_paint_mapping', same_paint(inherited(node, 'fill'), paint['fill']) and same_paint(inherited(node, 'stroke'), paint['stroke']), 'Card/container paint differs from the approved group.')
        elif role in {'accent', 'foreground'}:
            test('approved_paint_mapping', same_paint(inherited(node, 'fill'), paint[role]) or local_name(node.tag) == 'use' and same_paint(inherited(node, 'color'), paint[role]), f'{role} paint differs.')
        elif role == 'header':
            gradient = paint.get('header_gradient')
            test('approved_paint_mapping', gradient is not None and inherited(node, 'fill') == 'url(#' + gradient['id'] + ')', 'Header gradient differs.')
    def match_gradient(spec):
        node = ids.get(spec['id'])
        if node is None or local_name(node.tag) != 'linearGradient':
            return False
        try:
            direction = [float(node.get(k, 'nan')) for k in ('x1', 'y1', 'x2', 'y2')]
            stops = [{'offset': float(n.get('offset', 'nan')), 'color': inherited(n, 'stop-color')} for n in node if local_name(n.tag) == 'stop']
            return direction == spec['direction'] and len(stops) == len(spec['stops']) and all(a['offset'] == b['offset'] and same_paint(a['color'], b['color']) for a, b in zip(stops, spec['stops']))
        except ValueError:
            return False
    if diagram['background'] is not None:
        background = diagram['background']
        node = ids.get(background['id'])
        if 'gradient' in background:
            spec = background['gradient']
            test('approved_paint_mapping', node is not None and inherited(node, 'fill') == 'url(#' + spec['id'] + ')' and match_gradient(spec), 'Background gradient differs.')
        else:
            test('approved_paint_mapping', node is not None and same_paint(inherited(node, 'fill'), background['fill']), 'Background fill differs.')
    for item in tables['groups'].values():
        if item['paint']['kind'] == 'gradient':
            test('approved_paint_mapping', match_gradient(item['paint']['header_gradient']), 'Approved header gradient differs.')
    actual_relations = {n.get('id') for n in root.iter() if n.get('data-from') is not None}
    test('frozen_relations', actual_relations == tables['relations'].keys(), 'Relationship set differs.')
    for identifier, item in tables['relations'].items():
        node = ids.get(identifier)
        if node is None:
            test('frozen_relations', False, f'Missing relation {identifier}.')
            continue
        for key in ('from', 'to', 'kind', 'condition', 'line_style'):
            test('frozen_relations', node.get('data-' + key.replace('_', '-')) == item[key], f'{identifier} {key} differs.')
        if item['label_text'] is not None:
            label = ids.get(item['label_text'])
            test('frozen_relations', label is not None and item['condition'] in (text_value(label) if local_name(label.tag) == 'text' else ''), f'{identifier} condition label missing/different.')
        style = tables['line_styles'][item['line_style']]
        test('approved_paint_mapping', same_paint(inherited(node, 'stroke'), style['stroke']) and (inherited(node, 'stroke-dasharray') or '') == style['dasharray'] and inherited(node, 'marker-end') == 'url(#' + style['marker'] + ')', f'{identifier} line paint/style differs.')
    for item in tables['line_styles'].values():
        marker = ids.get(item['marker'])
        legend = ids.get(item['legend_text'])
        test('frozen_relations', marker is not None and local_name(marker.tag) == 'marker' and legend is not None and item['meaning'] in text_value(legend), 'Marker/legend missing or meaning differs.')
        if marker is not None:
            shapes = [n for n in marker.iter() if local_name(n.tag) in DRAWABLE]
            drawn = [inherited(n, key) for n in shapes for key in ('fill', 'stroke') if inherited(n, key) not in {None, 'none'}]
            test('approved_paint_mapping', bool(drawn) and all(same_paint(value, item['stroke']) for value in drawn), 'Marker color differs from line.')
    return errors


def validate(path, expected=(), acceptance=None, example_mode=False):
    try:
        raw = Path(path).read_bytes()
        source = raw.decode('utf-8-sig')
    except PermissionError as error:
        report = Report('', path)
        report.value['svg_sha256'] = None
        report.add('readable_utf8', False, str(error), status='环境受阻')
        return report.finish()
    except (OSError, UnicodeError) as error:
        report = Report('', path)
        report.value['svg_sha256'] = None
        report.add('readable_utf8', False, str(error), code=2 if isinstance(error, OSError) else 1)
        return report.finish()
    result = validate_source(source, expected, acceptance, example_mode, str(Path(path).resolve()))
    result['svg_sha256'] = sha256(raw)
    result['file'] = str(path)
    return result


class ArgumentError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentError(message)


def safe_report_destination(output, inputs):
    target = Path(output).resolve()
    key = str(target).casefold()
    if any(str(Path(item).resolve()).casefold() == key for item in inputs if item is not None):
        raise ArgumentError('Report destination must not overwrite SVG, acceptance, expected-file, palette or validator source.')
    return target


def atomic_report(path, result):
    """Only replace a complete report; never leave a partial destination file."""
    payload = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = Parser(description=__doc__)
    parser.add_argument('svg', type=Path)
    parser.add_argument('--acceptance', type=Path)
    parser.add_argument('--example-mode', action='store_true')
    parser.add_argument('--expect', action='append', default=[])
    parser.add_argument('--expected-file', type=Path)
    parser.add_argument('--report', type=Path)
    try:
        for flag in ('--acceptance', '--example-mode', '--expected-file', '--report'):
            if sum(arg == flag or arg.startswith(flag + '=') for arg in argv) > 1:
                raise ArgumentError(f'Duplicate parameter {flag}')
        args = parser.parse_args(argv)
        report_target = safe_report_destination(args.report, (args.svg, args.acceptance, args.expected_file, PALETTE_PATH, __file__)) if args.report else None
        expected = list(args.expect)
        if args.expected_file:
            words = json.loads(args.expected_file.read_text(encoding='utf-8-sig'))
            if not isinstance(words, list) or not words or not all(isinstance(w, str) and w.strip() for w in words):
                raise ValueError('Expected-file must be a nonempty array of strings.')
            expected.extend(words)
        result = validate(args.svg, expected, args.acceptance, args.example_mode)
        if report_target:
            try:
                atomic_report(report_target, result)
            except OSError as error:
                failed = Report('', args.svg)
                failed.value.update({key: result[key] for key in ('svg_sha256', 'acceptance_sha256', 'palette_sha256')})
                failed.add('report_write', False, str(error), status='环境受阻')
                result = failed.finish()
    except PermissionError as error:
        report = Report('', 'memory.svg')
        report.add('environment', False, str(error), status='环境受阻')
        result = report.finish()
    except (ArgumentError, OSError, UnicodeError, ValueError, TypeError) as error:
        report = Report('', 'memory.svg')
        report.add('configuration', False, str(error), code=2)
        result = report.finish()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result['exit_code']


if __name__ == '__main__':
    sys.exit(main())
