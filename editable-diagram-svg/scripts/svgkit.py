"""Explicit, transactional SVG geometry. No business inference or auto approval.

Canvas receives a frozen acceptance dict. It can write a validated *candidate*;
save delegates verified final/draft writing to publish_svg.py.
"""
from copy import deepcopy
from html import escape
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FONT = '"Microsoft YaHei","PingFang SC","Noto Sans CJK SC","Source Han Sans SC",Arial,sans-serif'


def units(value):
    return sum(1 if unicodedata.east_asian_width(c) in 'WF' else .68 if c.isupper() else .56 for c in value)


def wrap(value, width, size):
    """Preserve every character, including meaningful spaces, in soft line cuts."""
    finite(width, size)
    if width <= 0 or size <= 0:
        raise ValueError('Positive text width/size required')
    lines, line = [], ''
    for token in re.findall(r'[A-Za-z0-9_./-]+|[^A-Za-z0-9_./-]', str(value)):
        pieces = list(token) if units(token) * size > width else [token]
        for piece in pieces:
            if line and (piece == '\n' or units(line + piece) * size > width):
                if piece == '\n':
                    lines.append(line + piece)
                    line = ''
                    continue
                lines.append(line)
                line = ''
            line += piece
    lines.append(line)
    assert ''.join(lines) == str(value), 'Wrapping must preserve frozen text'
    return lines


def finite(*values):
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values):
        raise ValueError('Finite numeric geometry required')


def attr(value):
    return escape(str(value), quote=True)


class Canvas:
    def __init__(self, acceptance):
        self.acceptance = deepcopy(acceptance)
        self.diagram = self.acceptance['diagram']
        self.width, self.height = self.diagram['width'], self.diagram['height']
        finite(self.width, self.height)
        if self.width <= 0 or self.height <= 0:
            raise ValueError('Positive canvas dimensions required')
        self.palette = set(json.loads((ROOT / 'references/palette.json').read_text(encoding='utf-8')))
        self.texts = {item['id']: item for item in self.acceptance['texts']}
        self.groups = {item['id']: item for item in self.acceptance['groups']}
        self.relations = {item['id']: item for item in self.acceptance['relations']}
        self.line_styles = {item['id']: item for item in self.acceptance['line_styles']}
        self.parts, self.group_parts = [], {}
        self.serial = 0
        self.used_ids, self.used_icons, self.extra_defs = set(), set(), {}
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        symbols = ET.parse(ROOT / 'assets/icons.svg').getroot()
        self.symbols = {e.get('id'): ET.tostring(e, encoding='unicode') for e in symbols.iter() if e.tag.endswith('}symbol')}

    def _color(self, value, none=False):
        if value in self.palette or (none and value == 'none'):
            return value
        raise ValueError('Unapproved color: ' + str(value))

    def _commit(self, fragments, identifiers, group=None, icons=(), definitions=None):
        identifiers = list(identifiers)
        if len(set(identifiers)) != len(identifiers) or self.used_ids.intersection(identifiers):
            raise ValueError('Duplicate component IDs')
        if group is not None and group not in self.groups:
            raise ValueError('Unknown frozen group')
        if any(name not in self.symbols for name in icons):
            raise ValueError('Unknown vector icon')
        # All checks precede mutation; callers build local fragments only.
        destination = self.parts if group is None else self.group_parts.setdefault(group, [])
        destination.extend(fragments)
        self.used_ids.update(identifiers)
        self.used_icons.update(icons)
        self.extra_defs.update(definitions or {})
        self.serial += 1

    def _text(self, identifier, x, y, *, width=None, size=24, weight=400, anchor='start', role=None):
        spec = self.texts[identifier]
        finite(x, y, size)
        if size <= 0 or anchor not in {'start', 'middle', 'end'}:
            raise ValueError('Invalid text geometry/anchor')
        color = self._color(spec['fill'])
        lines = wrap(spec['value'], width, size) if width is not None else [spec['value']]
        spans = ''.join(f'<tspan x="{x}" y="{y + i * size * 1.4}">{escape(line)}</tspan>' for i, line in enumerate(lines))
        role_attr = f' data-paint-role="{attr(role)}"' if role else ''
        value = f'<text id="{attr(identifier)}" data-content-id="{attr(identifier)}"{role_attr} xml:space="preserve" x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{spans}</text>'
        return value, len(lines)

    def rect(self, identifier, x, y, width, height, *, fill='#ffffff', stroke='#cfe0fb', radius=24, opacity=1):
        finite(x, y, width, height, radius, opacity)
        if width <= 0 or height <= 0 or radius < 0 or not 0 <= opacity <= 1:
            raise ValueError('Invalid rectangle')
        self._color(fill, True)
        self._color(stroke, True)
        fragment = f'<rect id="{attr(identifier)}" x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}" fill-opacity="{opacity}"/>'
        self._commit([fragment], [identifier])

    def text(self, identifier, x, y, *, bounds, size=24, width=None, weight=400, anchor='start'):
        finite(*bounds)
        if len(bounds) != 4 or bounds[2] <= 0 or bounds[3] <= 0:
            raise ValueError('Positive root-coordinate text region required')
        fragment, _ = self._text(identifier, x, y, width=width, size=size, weight=weight, anchor=anchor)
        region = self.texts[identifier]['region']
        self._commit([f'<g data-region="{attr(region)}" data-bounds="{",".join(map(str, bounds))}">{fragment}</g>'], [identifier])

    def _icon(self, name, identifier, x, y, size, color):
        full_name = name if name.startswith('icon-') else 'icon-' + name
        finite(x, y, size)
        if size <= 0 or full_name not in self.symbols:
            raise ValueError('Invalid vector icon')
        self._color(color)
        fragment = f'<use id="{attr(identifier)}" href="#{attr(full_name)}" x="{x}" y="{y}" width="{size}" height="{size}" color="{color}"/>'
        return fragment, full_name

    def icon(self, name, identifier, x, y, *, size=36, color='#2468ee'):
        fragment, symbol = self._icon(name, identifier, x, y, size, color)
        self._commit([fragment], [identifier], icons=[symbol])

    def card(self, identifier, group, x, y, width, height, title_id, *, body_ids=(), icon=None, title_size=26, body_size=24):
        finite(x, y, width, height, title_size, body_size)
        if width <= 48 or height <= 48:
            raise ValueError('Card too small')
        paint = self.groups[group]['paint']
        for key in ('fill', 'stroke', 'accent', 'foreground'):
            self._color(paint[key])
        text_ids = [title_id, *body_ids]
        if any(self.texts[i]['region'] != identifier for i in text_ids):
            raise ValueError('Card text region must equal frozen node ID')
        if self.texts[title_id]['fill'] != paint['foreground']:
            raise ValueError('Frozen title foreground mismatch')
        fragments = [f'<g id="{attr(identifier)}" data-group-id="{attr(group)}"><rect data-paint-role="card" x="{x}" y="{y}" width="{width}" height="{height}" rx="20" fill="{paint["fill"]}" stroke="{paint["stroke"]}" stroke-width="1.5"/>', f'<g data-region="{attr(identifier)}" data-bounds="{x+24},{y+18},{width-48},{height-36}">']
        identifiers, symbols = [identifier], []
        title_x = x + 24
        if icon:
            name, icon_id = icon
            fragment, symbol = self._icon(name, icon_id, title_x, y + 23, 32, paint['accent'])
            fragments.append(fragment)
            identifiers.append(icon_id)
            symbols.append(symbol)
            title_x += 44
        heading, count = self._text(title_id, title_x, y + 49, width=x + width - 24 - title_x, size=title_size, weight=700, role='foreground')
        fragments.append(heading)
        identifiers.append(title_id)
        next_y = y + 49 + count * title_size * 1.4 + 14
        for text_id in body_ids:
            fragment, count = self._text(text_id, x + 24, next_y, width=width-48, size=body_size)
            if next_y + (count-1) * body_size * 1.4 + 6 > y + height - 22:
                raise ValueError('Card overflow: expand, rearrange or use approved split')
            fragments.append(fragment)
            identifiers.append(text_id)
            next_y += count * body_size * 1.4 + 6
        if y + 49 + (len(wrap(self.texts[title_id]['value'], x + width - 24 - title_x, title_size))-1)*title_size*1.4 + 6 > y + height - 22:
            raise ValueError('Card title overflow')
        fragments.append('</g></g>')
        self._commit(fragments, identifiers, group=group, icons=symbols)

    def band(self, identifier, group, x, y, width, height, title_id, *, header_height=80):
        finite(x, y, width, height, header_height)
        if identifier in self.groups:
            raise ValueError('Band ID must differ from the outer frozen group ID')
        if min(width, height, header_height) <= 0 or header_height > height:
            raise ValueError('Invalid group band geometry')
        paint = self.groups[group]['paint']
        if paint['kind'] != 'gradient':
            raise ValueError('Band needs an explicitly frozen header gradient')
        if units(self.texts[title_id]['value']) * 30 > width - 56:
            raise ValueError('Band title overflow: expand or wrap explicitly')
        for key in ('fill', 'stroke', 'accent', 'foreground'):
            self._color(paint[key])
        gradient = paint['header_gradient']
        definition = self._gradient(gradient)
        clip_id = identifier + '-clip'
        clip = f'<clipPath id="{attr(clip_id)}"><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="28"/></clipPath>'
        # Header text has its own frozen fill; card foreground can remain dark.
        heading, _ = self._text(title_id, x+28, y+51, size=30, weight=700)
        region = self.texts[title_id]['region']
        # A visible group container is not automatically a business node.
        node_group = f' data-group-id="{attr(group)}"' if any(node['id'] == identifier for node in self.acceptance['nodes']) else ''
        fragments = [f'<g id="{attr(identifier)}"{node_group}><rect data-paint-role="card" x="{x}" y="{y}" width="{width}" height="{height}" rx="28" fill="{paint["fill"]}" stroke="{paint["stroke"]}"/><g clip-path="url(#{attr(clip_id)})"><rect data-paint-role="header" x="{x}" y="{y}" width="{width}" height="{header_height}" fill="url(#{attr(gradient["id"])})"/></g><g data-region="{attr(region)}" data-bounds="{x+24},{y+12},{width-48},{header_height-20}">{heading}</g></g>']
        self._commit(fragments, [identifier, title_id], group=group, definitions={clip_id: clip, gradient['id']: definition})

    def arrow(self, identifier, points, *, label_pos=None, label_bounds=None):
        if len(points) < 2:
            raise ValueError('Arrow needs at least two points')
        for point in points:
            finite(*point)
            if len(point) != 2:
                raise ValueError('Arrow point needs x/y')
        relation = self.relations[identifier]
        style = self.line_styles[relation['line_style']]
        self._color(style['stroke'])
        label_id = relation.get('label_text')
        if label_id and (label_pos is None or label_bounds is None):
            raise ValueError('Explicit label position and region required')
        if label_pos is not None:
            finite(*label_pos)
        d = 'M' + ' L'.join(f'{x},{y}' for x, y in points)
        dash = f' stroke-dasharray="{attr(style["dasharray"])}"' if style['dasharray'] else ''
        metadata = ''.join(f' data-{key.replace("_", "-")}="{attr(relation[key])}"' for key in ('from', 'to', 'kind', 'condition', 'line_style'))
        fragments = [f'<path id="{attr(identifier)}"{metadata} d="{d}" fill="none" stroke="{style["stroke"]}" stroke-width="3" stroke-linejoin="round"{dash} marker-end="url(#{attr(style["marker"])})"/>']
        identifiers = [identifier]
        if label_id:
            finite(*label_bounds)
            if len(label_bounds) != 4 or label_bounds[2] <= 0 or label_bounds[3] <= 0:
                raise ValueError('Invalid arrow label region')
            fragment, _ = self._text(label_id, *label_pos, size=22, weight=600)
            fragments.append(f'<g data-region="{attr(self.texts[label_id]["region"])}" data-bounds="{",".join(map(str,label_bounds))}">{fragment}</g>')
            identifiers.append(label_id)
        marker = f'<marker id="{attr(style["marker"])}" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M1,1 L10,6 L1,11 Z" fill="{style["stroke"]}"/></marker>'
        self._commit(fragments, identifiers, definitions={style['marker']: marker})

    def heading(self, title_id, subtitle_id=None):
        fragments, identifiers = [], [title_id]
        title, _ = self._text(title_id, 60, 78, size=46, weight=700)
        fragments.append(f'<g data-region="{attr(self.texts[title_id]["region"])}" data-bounds="48,20,{self.width-96},84">{title}</g>')
        if subtitle_id:
            subtitle, _ = self._text(subtitle_id, 60, 130, size=24)
            fragments.append(f'<g data-region="{attr(self.texts[subtitle_id]["region"])}" data-bounds="48,98,{self.width-96},60">{subtitle}</g>')
            identifiers.append(subtitle_id)
        self._commit(fragments, identifiers)

    def access(self, identifier, group, x, y, width, height, title_id, **kwargs):
        """An explicit access card; never invents an input strip or default modules."""
        return self.card(identifier, group, x, y, width, height, title_id, **kwargs)

    def _gradient(self, spec):
        finite(*spec['direction'])
        if len(spec['direction']) != 4:
            raise ValueError('Gradient direction needs four numbers')
        stops = []
        for stop in spec['stops']:
            finite(stop['offset'])
            if not 0 <= stop['offset'] <= 1:
                raise ValueError('Gradient offset out of range')
            self._color(stop['color'])
            stops.append(f'<stop offset="{stop["offset"]}" stop-color="{stop["color"]}"/>')
        coords = ' '.join(f'{key}="{value}"' for key,value in zip(('x1','y1','x2','y2'),spec['direction']))
        return f'<linearGradient id="{attr(spec["id"])}" {coords}>' + ''.join(stops) + '</linearGradient>'

    def to_svg(self):
        d = self.diagram
        defs = dict(self.extra_defs)
        background = d.get('background')
        initial = []
        if background:
            if 'gradient' in background:
                spec = background['gradient']
                defs[spec['id']] = self._gradient(spec)
                fill = 'url(#' + spec['id'] + ')'
            else:
                fill = self._color(background['fill'])
            vx,vy,vw,vh = d['viewBox']
            initial.append(f'<rect id="{attr(background["id"])}" x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="{fill}"/>')
        defaults = d.get('defaults') or {}
        for key,value in defaults.items():
            self._color(value, key in {'fill','stroke'})
        svg_defaults = ' '.join(f'{key}="{value}"' for key,value in defaults.items())
        groups = [f'<g id="{attr(group)}" data-group-id="{attr(group)}">'+''.join(parts)+'</g>' for group,parts in self.group_parts.items()]
        return (f'<svg xmlns="http://www.w3.org/2000/svg" id="{attr(d["id"])}" width="{self.width}" height="{self.height}" viewBox="{" ".join(map(str,d["viewBox"]))}" role="img" aria-labelledby="diagram-title diagram-description" data-topology="{attr(d["topology"])}" data-detail-level="{attr(d["detail_level"])}" {svg_defaults}>\n'
                f'<title id="diagram-title">{escape(d["title"])}</title><desc id="diagram-description">{escape(d["description"])}</desc>\n'
                '<defs><style>text{font-family:'+FONT+'}</style>'+''.join(defs.values())+''.join(self.symbols[i] for i in sorted(self.used_icons))+'</defs>\n'
                +'\n'.join(initial+self.parts+groups)+'\n</svg>\n')

    def write_candidate(self, path, *, example_mode=False):
        """Complete static checks before writing a private workflow candidate."""
        from validate_svg import validate_source
        target = Path(path)
        source = self.to_svg()
        report = validate_source(source, acceptance=self.acceptance, example_mode=example_mode, svg_path=str(target.resolve()))
        if not report['ok']:
            raise ValueError(json.dumps(report, ensure_ascii=False))
        payload = source.encode('utf-8')
        if target.exists() and target.read_bytes() == payload:
            return report
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.'+target.name+'.', suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return report

    def save(self, output, *, candidate_file, acceptance_file, static_report, render_report, review=None, draft_reason=None, example_mode=False):
        """Delegate only verified candidate publishing; never write a final directly."""
        if Path(candidate_file).read_bytes() != self.to_svg().encode('utf-8'):
            raise ValueError('Candidate differs from current Canvas')
        command = [sys.executable, str(ROOT/'scripts/publish_svg.py'), '--candidate', str(candidate_file), '--output', str(output), '--acceptance', str(acceptance_file), '--static-report', str(static_report), '--render-report', str(render_report)]
        if review:
            command += ['--review', str(review)]
        if draft_reason:
            command += ['--draft-reason', str(draft_reason)]
        if example_mode:
            command += ['--example-mode']
        completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        if completed.returncode not in (0,3):
            raise ValueError(completed.stderr or completed.stdout)
        return json.loads(completed.stdout)
