"""Validate portable package resources; does not read external history or render automatically."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'scripts'))

def main():
    from validate_svg import validate
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    results=[]
    def record(key,passed,reason):
        results.append({'key':key,'status':'通过' if passed else '失败','reason':reason})
    palette=json.loads((ROOT/'references/palette.json').read_text(encoding='utf-8'))
    record('palette',len(palette)==47 and len(set(palette))==47 and all(re.fullmatch(r'#[0-9a-f]{6}',v) for v in palette),'47 unique exact source colors')
    for path in sorted(ROOT.rglob('*.md')):
        content=path.read_text(encoding='utf-8-sig')
        missing=[]
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',content):
            target=target.strip('<> ').split('#',1)[0]
            if not target or re.match(r'^[a-z]+:',target,re.I):continue
            referenced=(path.parent/target).resolve()
            if ROOT.resolve() not in referenced.parents and referenced != ROOT.resolve():
                missing.append('outside package: '+target)
            elif not referenced.exists():missing.append(target)
        record('links:'+str(path.relative_to(ROOT)),not missing,'Missing links: '+str(missing) if missing else 'All local links resolve inside package')
    svg_reports=[]
    for path in sorted(list((ROOT/'assets').rglob('*.svg'))+list((ROOT/'examples').glob('*.svg'))+list((ROOT/'verification/forward-test').glob('*.svg'))):
        acceptance=path.with_suffix('.acceptance.json')
        if path.name=='cold-chain.svg':acceptance=path.parent/'acceptance.json'
        if not acceptance.is_file():
            record('acceptance:'+str(path.relative_to(ROOT)),False,'Missing complete simulated acceptance')
            continue
        expected=[]
        legacy=path.with_suffix('.expected.json')
        if path.name=='cold-chain.svg':legacy=path.parent/'expected.json'
        if legacy.is_file():expected=json.loads(legacy.read_text(encoding='utf-8-sig'))
        report=validate(path,expected=expected,acceptance=acceptance,example_mode=True)
        svg_reports.append(report)
        record('svg:'+str(path.relative_to(ROOT)),report['ok'],str(report.get('errors',[])))
    fixture=json.loads((ROOT/'verification/forward-test/acceptance.json').read_text(encoding='utf-8'))
    record('forward-fixture',len(fixture['nodes'])==8 and not fixture['relations'],'Eight confirmed fictional modules, no execution arrows')
    failed=any(item['status']=='失败' for item in results)
    payload={'status':'失败' if failed else '通过','ok':not failed,'results':results,'svg_reports':svg_reports,'not_run':['Actual rendering and visual inspection','Official skill-creator quick_validate','Independent fresh-input forward test','Receiver fonts and projection devices'],'scope':'Current package static resources and links only; old evidence is not used.'}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':payload['status'],'checks':len(results),'svg_count':len(svg_reports),'failures':[r for r in results if r['status']=='失败'],'not_run':payload['not_run']},ensure_ascii=False,indent=2))
    return 1 if failed else 0

if __name__=='__main__':
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    raise SystemExit(main())
