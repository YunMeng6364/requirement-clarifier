"""Export a frozen, simulated forward-test fixture to an explicit directory."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parents[1]
sys.path.insert(0, str(SKILL / 'examples'))
from build_examples import same_or_write

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    originals = [SKILL.parent / n for n in ('architecture-diagram-generator','diagram-creator','technical-report-svg')]
    if any(destination == p.resolve() or p.resolve() in destination.parents for p in originals):
        parser.error('Output must not be inside an original source skill.')
    jobs = [(ROOT / 'cold-chain.svg', destination / 'cold-chain.svg'), (ROOT / 'acceptance.json', destination / 'acceptance.json'), (ROOT / 'expected.json', destination / 'expected.json')]
    for source, target in jobs:
        if not source.is_file() or (target.exists() and target.read_bytes() != source.read_bytes()):
            raise ValueError(f'Invalid fixture or differing existing output: {target}')
    written = sum(same_or_write(source,target) for source,target in jobs)
    print(json.dumps({'status':'通过','written_files':written,'modules':8,'execution_arrows':0,'scope':'Fixture export; independent fresh-input use still requires a separate forward test.'},ensure_ascii=False,indent=2))
    return 0

if __name__ == '__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError) as error:
        print(str(error));raise SystemExit(1)
