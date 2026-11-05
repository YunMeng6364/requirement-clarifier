#!/usr/bin/env python3
"""Local publisher boundary tests. Report fixtures are simulated test data, not actual rendering/review evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
from unittest.mock import patch
import zlib

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / 'scripts'))
import publish_svg as publisher


def fixture(directory):
    svg = '<svg xmlns="http://www.w3.org/2000/svg" id="diagram-main" width="400" height="240" viewBox="0 0 400 240" role="img" aria-labelledby="title desc" data-topology="grid" data-detail-level="medium" font-size="24" fill="#26406e" stroke="none" color="#26406e"><title id="title">Publisher test</title><desc id="desc">Simulated test fixture.</desc><rect id="background" width="400" height="240" fill="#ffffff"/><text id="text-hello" data-content-id="text-hello" data-region="hello" data-bounds="20,20,360,180" x="40" y="100" fill="#12306b">Hello</text></svg>\n'
    acceptance = {'schema_version': 1, 'confirmation': {'status': 'simulated', 'evidence': 'Publisher unit-test fixture; not user approval'},
                  'diagram': {'id': 'diagram-main', 'filename': 'final.svg', 'title': 'Publisher test', 'description': 'Simulated test fixture.', 'topology': 'grid', 'detail_level': 'medium', 'viewBox': [0, 0, 400, 240], 'width': 400, 'height': 240, 'display_width': 400, 'background': {'id': 'background', 'fill': '#ffffff'}, 'defaults': {'fill': '#26406e', 'stroke': 'none', 'color': '#26406e'}},
                  'texts': [{'id': 'text-hello', 'value': 'Hello', 'region': 'hello', 'fill': '#12306b'}], 'nodes': [], 'groups': [], 'relations': [], 'line_styles': [], 'visible_elements': ['background', 'text-hello'], 'assumptions': [], 'fallback': {'allowed': False, 'description': 'No content changes'}}
    candidate, approved = directory / 'candidate.svg', directory / 'acceptance.json'
    candidate.write_text(svg, encoding='utf-8')
    approved.write_text(json.dumps(acceptance, ensure_ascii=False, indent=2), encoding='utf-8')
    from validate_svg import validate
    static = validate(candidate, acceptance=approved, example_mode=True)
    if not static.get('ok') or not static.get('production_ready'):
        raise AssertionError('Fixture must pass complete static validation: ' + json.dumps(static, ensure_ascii=False))
    static_path = directory / 'static.json'
    static_path.write_text(json.dumps(static, ensure_ascii=False), encoding='utf-8')
    hashes = {key: static[key] for key in ('svg_sha256', 'acceptance_sha256', 'palette_sha256')}
    png_path = directory / 'fixture.png'
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    raw = b''.join(b'\x00' + b'\xff\xff\xff' * 400 for _ in range(240))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 400, 240, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
    png_path.write_bytes(png)
    base = {'schema_version': 1, 'status': '通过', 'ok': True, 'svg_path': str(candidate), **hashes, 'checks': {'fixture': True}, 'results': [{'key': 'fixture', 'status': '通过', 'reason': 'Simulated boundary-test evidence only', 'evidence': None, 'required': True}], 'limitations': ['Simulated publisher test evidence; no actual rendering or visual review is claimed.']}
    rendered = {**base, 'stage': 'render', 'png_path': str(png_path), 'png_sha256': hashlib.sha256(png).hexdigest(), 'preview': {'width': 400, 'height': 240}}
    visual_keys = ['glyphs', 'icons', 'text_layout', 'connections', 'clipping', 'colors', 'reading_order', 'content']
    visual = {**base, 'stage': 'visual', 'png_sha256': rendered['png_sha256'], 'preview': rendered['preview'], 'reviewed_at': '2026-11-05T00:00:00+00:00', 'acceptance_version': hashes['acceptance_sha256'], 'checks': {key: True for key in visual_keys}, 'results': [{'key': key, 'status': '通过', 'reason': 'Simulated unit-test record, not actual review', 'evidence': None, 'required': True} for key in visual_keys]}
    render_path, visual_path = directory / 'render.json', directory / 'visual.json'
    render_path.write_text(json.dumps(rendered), encoding='utf-8')
    visual_path.write_text(json.dumps(visual), encoding='utf-8')
    return candidate, approved, static_path, render_path, visual_path, rendered, visual


def run(report_path=None):
    records = []
    def case(name, operation):
        if operation() is False:
            return
        records.append({'key': name, 'status': '通过'})
    with tempfile.TemporaryDirectory(prefix='editable-svg-publish-') as temp:
        directory = Path(temp)
        def atomic_pass():
            target = directory / 'atomic.svg'; target.write_bytes(b'original')
            publisher.atomic_replace(target, b'complete', b'original')
            assert target.read_bytes() == b'complete'
        case('atomic_complete_replace', atomic_pass)
        def atomic_fail():
            target = directory / 'failure.svg'; target.write_bytes(b'original')
            with patch.object(publisher.os, 'replace', side_effect=PermissionError('simulated permission failure')):
                try: publisher.atomic_replace(target, b'complete', b'original')
                except PermissionError: pass
                else: raise AssertionError('Expected replace failure')
            assert target.read_bytes() == b'original' and not list(directory.glob('.failure.svg.*.tmp'))
        case('replace_failure_preserves_target_and_cleans_temp', atomic_fail)
        def concurrent():
            target = directory / 'concurrent.svg'; target.write_bytes(b'another writer')
            try: publisher.atomic_replace(target, b'ours', b'original')
            except publisher.CheckError as error: assert error.key == 'concurrent_output'
            else: raise AssertionError('Expected concurrent-write rejection')
            assert target.read_bytes() == b'another writer' and not list(directory.glob('.concurrent.svg.*.tmp'))
        case('concurrent_change_preserved', concurrent)
        old = b'<svg><rect fill="#3b8bff"/><text>Keep fill="#3b8bff" text unchanged</text></svg>'
        new = b'<svg><rect fill="#17b9a5"/><text>Keep fill="#3b8bff" text unchanged</text></svg>'
        contract = {'schema_version': 1, 'baseline_sha256': publisher.sha256(old), 'mappings': [{'old': '#3b8bff', 'new': '#17b9a5', 'count': 1}]}
        case('exact_paint_edit_keeps_text_bytes', lambda: publisher.apply_color_contract(old, new, contract, {'#17b9a5'}))
        def count_rejected():
            bad = copy.deepcopy(contract); bad['mappings'][0]['count'] = 2
            try: publisher.apply_color_contract(old, new, bad, {'#17b9a5'})
            except publisher.CheckError: pass
            else: raise AssertionError('Bad count should fail')
        case('mapping_count_assertion', count_rejected)
        def extra_rejected():
            try: publisher.apply_color_contract(old, new.replace(b'<rect ', b'<rect x="1" '), contract, {'#17b9a5'})
            except publisher.CheckError: pass
            else: raise AssertionError('Geometry change should fail')
        case('unapproved_geometry_change_rejected', extra_rejected)
        candidate, approved, static_path, render_path, visual_path, rendered, visual = fixture(directory)
        target = directory / 'final.svg'
        args = dict(candidate=candidate, output=target, acceptance=approved, static_report=static_path, render_report=render_path, review=visual_path, example_mode=True)
        def final_pass():
            output = publisher.publish(**args)
            assert output['exit_code'] == 0 and output['written'] and output['final_acceptance'], output
        case('complete_evidence_publishes', final_pass)
        def idempotent():
            modified_before = target.stat().st_mtime_ns
            output = publisher.publish(**args)
            assert output['exit_code'] == 0 and not output['written'] and target.stat().st_mtime_ns == modified_before, output
        case('same_bytes_not_rewritten', idempotent)
        def wrong_filename():
            unexpected = directory / 'unexpected.svg'
            output = publisher.publish(**{**args, 'output': unexpected})
            assert output['exit_code'] == 1 and not output['written'] and not unexpected.exists(), output
        case('frozen_final_filename_enforced', wrong_filename)
        def linked_output():
            linked = directory / 'linked.svg'
            before = target.read_bytes()
            try:
                linked.symlink_to(target)
            except (OSError, NotImplementedError) as error:
                records.append({'key': 'symbolic_link_output_preserves_target', 'status': '环境受阻', 'reason': str(error)})
                return False
            try:
                output = publisher.publish(**{**args, 'output': linked})
                assert output['exit_code'] == 2 and not output['written'] and target.read_bytes() == before and linked.is_symlink(), output
            finally:
                linked.unlink()
        case('symbolic_link_output_preserves_target', linked_output)
        def stale():
            bad = copy.deepcopy(rendered); bad['svg_sha256'] = '0' * 64
            render_path.write_text(json.dumps(bad), encoding='utf-8')
            before = target.read_bytes()
            output = publisher.publish(**args)
            assert output['exit_code'] == 1 and not output['written'] and target.read_bytes() == before, output
            render_path.write_text(json.dumps(rendered), encoding='utf-8')
        case('stale_report_preserves_target', stale)
        def incomplete_review():
            bad = copy.deepcopy(visual); bad['results'] = bad['results'][:1]
            visual_path.write_text(json.dumps(bad), encoding='utf-8')
            output = publisher.publish(**args)
            assert output['exit_code'] == 2 and not output['written'], output
            visual_path.write_text(json.dumps(visual), encoding='utf-8')
        case('incomplete_visual_evidence_rejected', incomplete_review)
        blocked = {**rendered, 'status': '环境受阻', 'ok': False, 'png_path': None, 'png_sha256': None, 'checks': {'browser_launch': False}, 'results': [{'key': 'browser_launch', 'status': '环境受阻', 'reason': 'Simulated missing browser fixture', 'evidence': None, 'required': True}]}
        render_path.write_text(json.dumps(blocked), encoding='utf-8')
        draft_args = {**args, 'review': None, 'output': directory / 'draft.svg', 'draft_reason': 'Simulated unavailable browser'}
        def draft():
            output = publisher.publish(**draft_args)
            assert output['exit_code'] == 3 and output['written'] and not output['final_acceptance'] and output['status'] == '环境受阻', output
        case('blocked_draft_written_but_not_final', draft)
        def failed_draft():
            bad = copy.deepcopy(blocked); bad['results'].append({'key': 'geometry', 'status': '失败', 'reason': 'Simulated geometry error', 'required': True})
            render_path.write_text(json.dumps(bad), encoding='utf-8')
            before = draft_args['output'].read_bytes()
            output = publisher.publish(**draft_args)
            assert output['exit_code'] == 1 and not output['written'] and draft_args['output'].read_bytes() == before, output
        case('failed_check_cannot_be_draft_bypass', failed_draft)
    result = {'scope': 'Publisher behavior tests; render/review records are simulated fixtures', 'ok': True, 'count': len(records), 'passed_count': sum(item['status'] == '通过' for item in records), 'blocked_count': sum(item['status'] == '环境受阻' for item in records), 'results': records, 'temporary_files_cleaned': True}
    if report_path:
        Path(report_path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    sys.exit(run(args.report))
