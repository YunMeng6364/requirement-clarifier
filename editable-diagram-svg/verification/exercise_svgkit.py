"""Behavior tests for explicit geometry transaction and frozen candidate checks."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from svgkit import Canvas, wrap


def fixture():
    return {
        'schema_version': 1,
        'confirmation': {'status':'simulated','evidence':'Isolated helper behavior test'},
        'diagram': {'id':'diagram-test','filename':'candidate.svg','title':'几何助手演练','description':'演示设定，只有一个明确节点。','topology':'grid','detail_level':'medium','viewBox':[0,0,1920,1080],'width':1920,'height':1080,'display_width':1600,'background':{'id':'background-rect','fill':'#f4f9ff'},'defaults':{'fill':'#26406e','stroke':'none','color':'#26406e'}},
        'texts': [
            {'id':'text-title','value':'几何助手演练','region':'heading','fill':'#12306b'},
            {'id':'text-node','value':'01 既定模块','region':'node-one','fill':'#12306b'},
            {'id':'text-body','value':'API  v1 保留空格与内容','region':'node-one','fill':'#26406e'},
            {'id':'text-label','value':'已确认条件','region':'label','fill':'#26406e'},
            {'id':'text-legend','value':'实线表示本例关联','region':'legend','fill':'#46618f'}
        ],
        'groups':[{'id':'group-any','members':['node-one'],'paint':{'kind':'solid','fill':'#fafcff','stroke':'#8db8ff','accent':'#2468ee','foreground':'#12306b'},'reason':'本例任意分组，无职责绑定'}],
        'nodes':[{'id':'node-one','group':'group-any','title_text':'text-node'}],
        'relations':[{'id':'edge-one','from':'node-one','to':'node-one','kind':'feedback','condition':'已确认条件','line_style':'line','label_text':'text-label'}],
        'line_styles':[{'id':'line','stroke':'#46618f','dasharray':'','meaning':'本例关联','legend_text':'text-legend','marker':'arrow-line'}],
        'visible_elements':['background-rect','group-any','node-one','edge-one','text-title','text-node','text-body','text-label','text-legend'],
        'assumptions':['明确模拟测试'],
        'fallback':{'allowed':False,'description':'无拆图'}
    }


def snapshot(canvas):
    return deepcopy((canvas.parts, canvas.group_parts, canvas.serial, canvas.used_ids, canvas.used_icons, canvas.extra_defs))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    cases = []

    def run(name, fn):
        try:
            fn()
            cases.append({'key':name,'status':'通过'})
        except Exception as error:
            cases.append({'key':name,'status':'失败','reason':str(error)})

    def no_mutation(method):
        canvas = Canvas(fixture())
        before = snapshot(canvas)
        try:
            method(canvas)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError('Expected rejection')
        assert snapshot(canvas) == before, 'Assertion must not partially mutate Canvas'

    def preserved_wrap():
        for value in ['API  v1 保留 空格','LongTechnicalTermWithoutSpaces','中文\n换行保留','尾部空格  ']:
            assert ''.join(wrap(value,100,24)) == value

    run('wrapping_preserves_frozen_text', preserved_wrap)
    run('card_failure_no_partial_memory', lambda:no_mutation(lambda c:c.card('node-one','group-any',100,300,300,70,'text-node',body_ids=['text-body'])))
    run('arrow_failure_no_partial_memory', lambda:no_mutation(lambda c:c.arrow('edge-one',[(100,100),(200,100)])))
    run('heading_failure_no_partial_memory', lambda:no_mutation(lambda c:c.heading('text-title','missing-text')))
    run('color_rejection_no_partial_memory', lambda:no_mutation(lambda c:c.rect('bad',0,0,20,20,fill='#fff')))

    def band_failure():
        data = fixture()
        data['groups'][0]['paint'].update(kind='gradient',header_gradient={'id':'band-gradient','stops':[{'offset':0,'color':'#727bff'},{'offset':1,'color':'#5149e8'}],'direction':[0,0,1,1]})
        canvas = Canvas(data)
        before = snapshot(canvas)
        try:
            canvas.band('group-band','group-any',0,0,50,100,'text-title')
        except ValueError:
            pass
        else:
            raise AssertionError('Expected band overflow')
        assert snapshot(canvas) == before

    run('band_failure_no_partial_memory', band_failure)

    def non_node_group_band():
        from validate_svg import validate_source
        data = fixture()
        data['groups'][0]['paint'].update(kind='gradient',header_gradient={'id':'band-gradient','stops':[{'offset':0,'color':'#3b8bff'},{'offset':1,'color':'#1b57e0'}],'direction':[0,0,1,0]})
        data['texts'].append({'id':'text-band','value':'已确认分组容器','region':'band-heading','fill':'#ffffff'})
        data['visible_elements'].extend(['group-band','text-band'])
        canvas = Canvas(data)
        canvas.heading('text-title')
        canvas.band('group-band','group-any',200,180,900,500,'text-band')
        canvas.card('node-one','group-any',300,300,500,260,'text-node',body_ids=['text-body'])
        canvas.arrow('edge-one',[(800,440),(950,440),(950,570),(550,570),(550,560)],label_pos=(1100,410),label_bounds=(1080,370,450,100))
        canvas.text('text-legend',60,1000,bounds=(48,950,1800,100),size=20)
        source = canvas.to_svg()
        assert '<g id="group-band">' in source
        elements = {element.get('id'): element for element in ET.fromstring(source).iter() if element.get('id')}
        assert elements['text-band'].get('fill') == '#ffffff'
        assert elements['text-node'].get('fill') == '#12306b'
        report = validate_source(source,acceptance=data,example_mode=True)
        assert report['ok'], report
        assert report['production_ready']

    run('non_node_group_band_white_heading_dark_card', non_node_group_band)

    def valid_candidate():
        data = fixture()
        canvas = Canvas(data)
        canvas.heading('text-title')
        canvas.card('node-one','group-any',300,300,500,260,'text-node',body_ids=['text-body'])
        canvas.arrow('edge-one',[(800,440),(950,440),(950,570),(550,570),(550,560)],label_pos=(950,410),label_bounds=(930,370,450,100))
        canvas.text('text-legend',60,1000,bounds=(48,950,1800,100),size=20)
        with tempfile.TemporaryDirectory(prefix='svgkit-check-') as directory:
            path = Path(directory) / 'candidate.svg'
            report = canvas.write_candidate(path, example_mode=True)
            assert report['ok'], report
            original = path.read_bytes()
            mtime = path.stat().st_mtime_ns
            repeated = canvas.to_svg()
            assert repeated.encode('utf-8') == original
            canvas.write_candidate(path, example_mode=True)
            assert path.stat().st_mtime_ns == mtime, 'Same-byte rerun must not write'
            assert original.count(b'id="node-one"') == 1
            before = path.read_bytes()
            canvas.parts.append('<rect fill="#000000"/>')
            try:
                canvas.write_candidate(path, example_mode=True)
            except ValueError:
                pass
            else:
                raise AssertionError('Illegal candidate must fail')
            assert path.read_bytes() == before, 'Failed static check must preserve existing candidate'

    run('valid_candidate_and_idempotent_write', valid_candidate)
    result = {'stage':'helper-tests','ok':all(c['status']=='通过' for c in cases),'results':cases,'limitations':['Behavior tests do not replace rendering or real user confirmation.']}
    payload = json.dumps(result,ensure_ascii=False,indent=2)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(payload+'\n',encoding='utf-8')
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
