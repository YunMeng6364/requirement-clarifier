"""Export frozen fictional fixtures to an explicit output directory; never approve new input."""
import argparse
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def same_or_write(source, target):
    data = source.read_bytes()
    if target.exists():
        if target.read_bytes() == data:
            return False
        raise ValueError(f'Refusing to overwrite different existing file: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix='.' + target.name + '.', suffix='.tmp', dir=target.parent)
    try:
        with os.fdopen(handle, 'wb') as output:
            output.write(data); output.flush(); os.fsync(output.fileno())
        if target.exists():
            raise ValueError(f'Target appeared during export: {target}')
        os.replace(temporary, target)
    finally:
        if Path(temporary).exists(): Path(temporary).unlink()
    return True

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--regenerate-templates', action='store_true', help='Also export the three frozen template fixtures beneath output-dir/assets/templates.')
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    source_roots = [ROOT.parent / name for name in ('architecture-diagram-generator', 'diagram-creator', 'technical-report-svg')]
    if any(destination == path.resolve() or path.resolve() in destination.parents for path in source_roots):
        parser.error('Output must not be inside an original source skill.')
    filenames = [f'{name}.{ending}' for name in ('architecture', 'lifecycle') for ending in ('svg', 'acceptance.json', 'expected.json')]
    jobs = [(ROOT / 'examples' / name, destination / name) for name in filenames]
    if args.regenerate_templates:
        for name in ('overview-detail', 'layers', 'flow'):
            for ending in ('svg', 'acceptance.json'):
                rel = Path('assets/templates') / f'{name}.{ending}'
                jobs.append((ROOT / rel, destination / rel))
    # Preflight content assertions before writing; every individual output is atomic.
    for source, target in jobs:
        if not source.is_file(): raise ValueError(f'Missing canonical fixture: {source}')
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise ValueError(f'Refusing different existing output: {target}')
    writes = sum(same_or_write(source, target) for source, target in jobs)
    print(json.dumps({'status': '通过', 'written_files': writes, 'output_dir': str(destination), 'scope': 'Frozen fictional fixture export only; confirmations remain simulated.'}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(str(error))
        raise SystemExit(1)
