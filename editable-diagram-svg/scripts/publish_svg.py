#!/usr/bin/env python3
"""Atomically save a checked local SVG; this does not upload or deploy anything.

Exit 0: final SVG verified (written or already identical).
Exit 1: check failure; 2: invalid argument/configuration; 3: environment blocked.
A statically valid draft may be written with exit 3 and final_acceptance=false.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

PASSED, FAILED, SKIPPED, BLOCKED = '通过', '失败', '未执行', '环境受阻'
PALETTE = Path(__file__).resolve().parents[1] / 'references' / 'palette.json'
PAINT = {'fill', 'stroke', 'color', 'stop-color', 'flood-color', 'lighting-color'}


class CheckError(Exception):
    def __init__(self, message, code=1, key='publish_checks'):
        super().__init__(message)
        self.code, self.key = code, key


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise CheckError(f'Invalid JSON {path}: {error}', 2, 'report_format') from error


def add(report, key, status, reason='', evidence=None, required=True):
    report['results'].append({'key': key, 'status': status, 'reason': reason, 'evidence': evidence, 'required': required})
    if required:
        report['checks'][key] = status == PASSED


def finish(report, code):
    statuses = [item['status'] for item in report['results'] if item.get('required', True)]
    report['status'] = FAILED if FAILED in statuses else BLOCKED if BLOCKED in statuses else SKIPPED if SKIPPED in statuses or not statuses else PASSED
    report['ok'] = report['status'] == PASSED
    report['exit_code'] = code
    return report


def match_hashes(evidence, current, stage, passing=True):
    if not isinstance(evidence, dict) or evidence.get('schema_version') != 1 or evidence.get('stage') != stage:
        raise CheckError(f'Expected schema 1 {stage} report', 2, 'report_format')
    for key in ('svg_sha256', 'acceptance_sha256', 'palette_sha256'):
        if evidence.get(key) != current[key]:
            raise CheckError(f'Stale {stage} evidence: {key}', 1, 'current_evidence')
    checks, results = evidence.get('checks'), evidence.get('results')
    if not isinstance(checks, dict) or not checks or not isinstance(results, list) or not results:
        raise CheckError(f'{stage} report has no check evidence', 2, 'report_format')
    if passing:
        if evidence.get('status') != PASSED or evidence.get('ok') is not True or any(value is not True for value in checks.values()):
            raise CheckError(f'{stage} stage has not passed', 1, 'required_evidence')
        if any(item.get('required', True) and item.get('status') != PASSED for item in results):
            raise CheckError(f'{stage} required checks have not passed', 1, 'required_evidence')
    return evidence


def read_png(path, expected_hash, preview):
    png = Path(path).read_bytes()
    if sha256(png) != expected_hash:
        raise CheckError('Preview PNG does not match rendering/visual evidence', 1, 'current_png')
    if len(png) < 24 or png[:8] != bytes([137, 80, 78, 71, 13, 10, 26, 10]):
        raise CheckError('Preview evidence is not PNG', 1, 'current_png')
    dimensions = (int.from_bytes(png[16:20], 'big'), int.from_bytes(png[20:24], 'big'))
    if not isinstance(preview, dict) or dimensions != (preview.get('width'), preview.get('height')):
        raise CheckError('PNG size does not match frozen rendering evidence', 1, 'current_png')


def apply_color_contract(baseline, candidate, contract, palette):
    """Exact edits in paint attributes and inline declarations; other bytes stay identical."""
    if contract.get('schema_version') != 1 or not isinstance(contract.get('mappings'), list) or not contract['mappings']:
        raise CheckError('change-contract needs schema_version 1 and nonempty mappings', 2, 'change_contract')
    if contract.get('baseline_sha256') != sha256(baseline):
        raise CheckError('Change contract baseline hash does not match', 1, 'change_contract')
    try:
        original, actual = baseline.decode('utf-8'), candidate.decode('utf-8')
    except UnicodeError as error:
        raise CheckError('Pure recoloring requires UTF-8 baseline/candidate', 2, 'change_contract') from error
    mappings, expected = {}, {}
    for item in contract['mappings']:
        if not isinstance(item, dict):
            raise CheckError('Invalid change mapping', 2, 'change_contract')
        old, new, count = item.get('old'), item.get('new'), item.get('count')
        if not isinstance(old, str) or not re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', old) or new not in palette or type(count) is not int or count <= 0 or old in mappings or old == new:
            raise CheckError('Mappings need unique exact old color, allowed new color and positive count', 2, 'change_contract')
        mappings[old], expected[old] = new, count
    occurrences = {old: 0 for old in mappings}
    after_counts = {new: 0 for new in mappings.values()}
    attribute = re.compile(r'([\w:-]+)(\s*=\s*)([\"\'])(.*?)(\3)', re.S)
    declaration = re.compile(r'([\w-]+)(\s*:\s*)([^;]*)(;|$)')

    def color(value):
        if value in mappings:
            occurrences[value] += 1
            return mappings[value]
        if value in after_counts:
            after_counts[value] += 1
        return value

    def declaration_replace(match):
        prop, separator, value, end = match.groups()
        if prop in PAINT:
            leading = value[:len(value) - len(value.lstrip())]
            trailing = value[len(value.rstrip()):]
            return prop + separator + leading + color(value.strip()) + trailing + end
        return match.group(0)

    def attribute_replace(match):
        prop, separator, quote, value, close = match.groups()
        if prop in PAINT:
            value = color(value)
        elif prop == 'style':
            value = declaration.sub(declaration_replace, value)
        return prop + separator + quote + value + close

    def tag_replace(match):
        token = match.group(0)
        return token if token.startswith('<!--') or token.startswith('<?') or token.startswith('</') else attribute.sub(attribute_replace, token)

    modified = re.sub(r'<!--.*?-->|<\?.*?\?>|<[^>]+>', tag_replace, original, flags=re.S)
    if all(count == 0 for count in occurrences.values()):
        expected_new = {}
        for old, new in mappings.items():
            expected_new[new] = expected_new.get(new, 0) + expected[old]
        if original != actual or any(after_counts.get(new, 0) < count for new, count in expected_new.items()):
            raise CheckError('Old colors absent but the complete approved target mapping is not present', 1, 'change_contract')
        return 'already_mapped'
    if occurrences != expected:
        raise CheckError(f'Color occurrence assertions failed: expected {expected}, found {occurrences}', 1, 'change_contract')
    if modified != actual:
        raise CheckError('Candidate changes bytes outside the exact approved paint mapping', 1, 'change_contract')
    return 'mapped_exactly'


def atomic_replace(target, data, expected_target):
    """No target mutation before complete temp write, fsync and concurrent-state assertion."""
    target = Path(target)
    if target.is_symlink():
        raise CheckError('Refusing to replace a symbolic-link output', 2, 'output_path')
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', prefix='.' + target.name + '.', suffix='.tmp', dir=target.parent, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        current = target.read_bytes() if target.exists() else None
        if current != expected_target:
            raise CheckError('Output changed concurrently; target preserved', 1, 'concurrent_output')
        os.replace(temp, target)
        temp = None
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def publish(candidate, output, acceptance, static_report, render_report, review=None, draft_reason=None, baseline=None, change_contract=None, example_mode=False):
    raw_output = Path(output)
    output_is_link = raw_output.is_symlink()
    candidate, output = Path(candidate).resolve(), Path(output).resolve()
    acceptance, static_report, render_report = Path(acceptance).resolve(), Path(static_report).resolve(), Path(render_report).resolve()
    report = {'schema_version': 1, 'stage': 'publish', 'status': SKIPPED, 'ok': False,
              'svg_path': str(candidate), 'svg_sha256': None, 'acceptance_sha256': None, 'palette_sha256': None,
              'checks': {}, 'results': [], 'limitations': ['Evidence is agent-provided; hash linkage does not authenticate a human approval or visual review.'],
              'output_path': str(output), 'written': False, 'final_acceptance': False}
    try:
        if output_is_link:
            raise CheckError('Output is a symbolic link; target preserved', 2, 'output_path')
        data = candidate.read_bytes()
        target_before = output.read_bytes() if output.exists() else None
        manifest_bytes, palette_bytes = acceptance.read_bytes(), PALETTE.read_bytes()
        report.update(svg_sha256=sha256(data), acceptance_sha256=sha256(manifest_bytes), palette_sha256=sha256(palette_bytes))
        if output in {acceptance, static_report, render_report, PALETTE.resolve()} or (review and output == Path(review).resolve()):
            raise CheckError('Output must not overwrite evidence or configuration files', 2, 'output_path')
        manifest = read_json(acceptance)
        mode = 'simulated' if example_mode else 'approved'
        if manifest.get('schema_version') != 1 or manifest.get('confirmation', {}).get('status') != mode or not str(manifest.get('confirmation', {}).get('evidence', '')).strip():
            raise CheckError(f'Confirmation must be {mode} with evidence', 2, 'confirmation')
        frozen_name = manifest.get('diagram', {}).get('filename')
        if not isinstance(frozen_name, str) or Path(frozen_name).name != frozen_name:
            raise CheckError('Frozen diagram.filename must be a plain SVG filename', 2, 'output_path')
        if not draft_reason and output.name != frozen_name:
            raise CheckError('Final output filename differs from the frozen diagram.filename', 1, 'output_path')
        add(report, 'confirmation', PASSED, f'Mode: {mode}')
        evidence = match_hashes(read_json(static_report), report, 'static')
        if evidence.get('production_ready') is not True:
            raise CheckError('Full frozen acceptance checks are required; keyword compatibility is insufficient', 1, 'frozen_acceptance')
        # Recheck current source rather than trusting an old or edited passing report.
        from validate_svg import validate
        fresh = validate(candidate, acceptance=acceptance, example_mode=example_mode)
        if fresh.get('ok') is not True or fresh.get('production_ready') is not True:
            raise CheckError('Current candidate does not pass the full SVG contract', 1, 'candidate_recheck')
        add(report, 'candidate_recheck', PASSED, 'Current complete candidate validated in memory')
        add(report, 'static_evidence', PASSED, 'Current static evidence hashes match')
        render = match_hashes(read_json(render_report), report, 'render', passing=not bool(draft_reason))
        if draft_reason:
            if not isinstance(draft_reason, str) or not draft_reason.strip() or review is not None:
                raise CheckError('Draft needs a nonempty reason and no claimed final visual review', 2, 'draft_evidence')
            if render.get('status') != BLOCKED or render.get('ok') is not False or render.get('png_sha256') is not None or render.get('png_path') is not None:
                raise CheckError('Draft requires a current render environment-blocked report', 1, 'draft_evidence')
            if not any(item.get('status') == BLOCKED and item.get('reason') for item in render['results']) or any(item.get('status') == FAILED for item in render['results']):
                raise CheckError('Draft evidence must explain a real block and contain no failed checks', 1, 'draft_evidence')
            add(report, 'render_acceptance', BLOCKED, draft_reason.strip(), str(render_report))
            add(report, 'visual_review', SKIPPED, 'Draft has not completed actual render/visual acceptance', required=False)
        else:
            if review is None:
                raise CheckError('A separate actual visual review report is required for final SVG', 2, 'visual_review')
            visual = match_hashes(read_json(review), report, 'visual')
            required_visual = {'glyphs', 'icons', 'text_layout', 'connections', 'clipping', 'colors', 'reading_order', 'content'}
            reviewed_keys = {item.get('key') for item in visual['results'] if item.get('status') == PASSED}
            if not required_visual.issubset(reviewed_keys):
                raise CheckError('Visual review is missing required glyph/icon/layout/connection/clipping/color/order/content checks', 2, 'visual_review')
            if visual.get('acceptance_version') != report['acceptance_sha256'] or not visual.get('reviewed_at'):
                raise CheckError('Visual review must identify the exact acceptance version and actual review time', 2, 'visual_review')
            try:
                datetime.fromisoformat(visual['reviewed_at'].replace('Z', '+00:00'))
            except (TypeError, ValueError) as error:
                raise CheckError('Visual review time must be ISO 8601', 2, 'visual_review') from error
            if visual.get('png_sha256') != render.get('png_sha256') or visual.get('preview') != render.get('preview'):
                raise CheckError('Visual review is not for the current PNG and display size', 1, 'visual_review')
            if render.get('preview', {}).get('width') != manifest.get('diagram', {}).get('display_width'):
                raise CheckError('Render width differs from frozen display_width', 1, 'render_acceptance')
            read_png(render.get('png_path'), render.get('png_sha256'), render.get('preview'))
            add(report, 'render_acceptance', PASSED, 'Actual fresh PNG, size and render evidence checked', str(render_report))
            add(report, 'visual_review', PASSED, 'Separate actual agent review matches the current PNG', str(Path(review).resolve()))
        if bool(baseline) != bool(change_contract):
            raise CheckError('--baseline and --change-contract must be used together', 2, 'change_contract')
        if baseline:
            state = apply_color_contract(Path(baseline).read_bytes(), data, read_json(change_contract), set(json.loads(palette_bytes)))
            add(report, 'change_contract', PASSED, state)
        if candidate.read_bytes() != data or acceptance.read_bytes() != manifest_bytes or PALETTE.read_bytes() != palette_bytes:
            raise CheckError('Candidate, acceptance or palette changed during verification', 1, 'current_inputs')
        add(report, 'current_inputs', PASSED, 'Inputs unchanged throughout verification')
        if target_before == data:
            add(report, 'atomic_write', PASSED, 'Already identical; no file rewrite')
        else:
            atomic_replace(output, data, target_before)
            report['written'] = True
            add(report, 'atomic_write', PASSED, 'Complete candidate saved with same-directory fsync and atomic replace')
        report['final_acceptance'] = not bool(draft_reason)
        return finish(report, 3 if draft_reason else 0)
    except CheckError as error:
        add(report, error.key, BLOCKED if error.code == 3 else FAILED, str(error))
        return finish(report, error.code)
    except (PermissionError, FileNotFoundError, OSError) as error:
        add(report, 'filesystem', BLOCKED, str(error))
        return finish(report, 3)
    except (ValueError, TypeError, KeyError, ImportError) as error:
        add(report, 'configuration', FAILED, str(error))
        return finish(report, 2)
    except Exception as error:
        add(report, 'execution', FAILED, str(error))
        return finish(report, 1)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CheckError(message, 2, 'arguments')


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = Parser(description=__doc__)
    for option in ('candidate', 'output', 'acceptance', 'static-report', 'render-report'):
        parser.add_argument('--' + option, required=True, type=Path)
    for option in ('review', 'baseline', 'change-contract', 'report'):
        parser.add_argument('--' + option, type=Path)
    parser.add_argument('--draft-reason')
    parser.add_argument('--example-mode', action='store_true')
    try:
        raw = list(sys.argv[1:] if argv is None else argv)
        flags = [token.split('=', 1)[0] for token in raw if token.startswith('--')]
        if len(flags) != len(set(flags)):
            raise CheckError('Duplicate options are not allowed', 2, 'arguments')
        args = parser.parse_args(raw)
        if args.report:
            evidence_paths = {Path(item).resolve() for item in (args.candidate, args.output, args.acceptance, args.static_report, args.render_report, args.review, args.baseline, args.change_contract) if item}
            if args.report.resolve() in evidence_paths or args.report.resolve() == PALETTE.resolve():
                raise CheckError('--report must not overwrite SVG inputs, output or evidence', 2, 'arguments')
        report = publish(args.candidate, args.output, args.acceptance, args.static_report, args.render_report,
                         args.review, args.draft_reason, args.baseline, args.change_contract, args.example_mode)
        if args.report:
            before = args.report.read_bytes() if args.report.exists() else None
            atomic_replace(args.report.resolve(), (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8'), before)
    except CheckError as error:
        if 'report' in locals():
            add(report, error.key, BLOCKED if error.code == 3 else FAILED, str(error))
            report = finish(report, error.code)
        else:
            report = {'schema_version': 1, 'stage': 'publish', 'status': FAILED, 'ok': False, 'checks': {error.key: False},
                      'results': [{'key': error.key, 'status': FAILED, 'reason': str(error), 'evidence': None, 'required': True}],
                      'svg_path': None, 'svg_sha256': None, 'acceptance_sha256': None, 'palette_sha256': None,
                      'limitations': [], 'written': False, 'final_acceptance': False, 'exit_code': error.code}
    except OSError as error:
        if 'report' in locals():
            add(report, 'report_write', BLOCKED, str(error))
            report = finish(report, 3)
        else:
            report = {'schema_version': 1, 'stage': 'publish', 'status': BLOCKED, 'ok': False, 'checks': {'report_write': False},
                      'results': [{'key': 'report_write', 'status': BLOCKED, 'reason': str(error), 'evidence': None, 'required': True}],
                      'svg_path': None, 'svg_sha256': None, 'acceptance_sha256': None, 'palette_sha256': None,
                      'limitations': [], 'written': False, 'final_acceptance': False, 'exit_code': 3}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report['exit_code']


if __name__ == '__main__':
    sys.exit(main())
