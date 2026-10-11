"""Bounded hardware-gate qualification; no master launch before qualification."""
import argparse
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(HOME / 'tools/research'))
from mode_trace_review import markers
from trace_qualification.frame_stack import TransitionFrameStack

OUT = HOME / 'artifacts/capture_work/host-20260918-1430/output'


def prepare(run):
    old = (OUT / 'capture-frame-a.txt').read_text()
    header = old[:old.index('r @$t3 =')].replace('frame-a-', run+'-')
    header += 'r @$t3 = poi(ntdll!Wow64Transition)\nba e 1 @$t3\n'
    header += 'bp (@$t0+14ed7a)\nsxe av\n.echo STACK_WINDOW_BEGIN\nt 0n20000\n'
    block = f'''
.if (@eip == (@$t0+14ed7a)) {{ .echo STACK_CLIENT_RECONNECTED; r; .writemem ..\\output\\{run}-end.bin @$t0 L307000; bc *; t; t 0n32; .printf "STACK_LIVE pid=%x tid=%x pc=%p sp=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, @$dbgtime; r; q }}
.if (@eip == @$t3) {{ .printf "STACK_ENTRY pid=%x tid=%x pc=%p sp=%p expected=%p caller=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, poi(@esp), poi(@esp+4), @$dbgtime; dd @esp L8; bp poi(@esp) ".printf \\"STACK_RETURN pid=%x tid=%x pc=%p sp=%p caller=%p time=%I64x\\\\n\\", @$tpid, @$tid, @eip, @esp, poi(@esp), @$dbgtime; r; dd @esp L8"; g }} .else {{ t 0n20000 }}
'''
    if run == 'stack-b':
        entry = '.printf "STACK_ENTRY pid=%x tid=%x pc=%p sp=%p expected=%p caller=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, poi(@esp), poi(@esp+4), @$dbgtime; dd @esp L8; bp poi(@esp); g'
        returned = '.printf "STACK_RETURN pid=%x tid=%x pc=%p sp=%p caller=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, poi(@esp), @$dbgtime; r; dd @esp L8; t 0n20000'
        block = block[:block.index('.if (@eip == @$t3)')]
        block += '.if (@eip == @$t3) { '+entry+' } .else { '+returned+' }\n'
    with (OUT / f'capture-{run}.txt').open('x', encoding='ascii') as stream:
        stream.write(header + block*24 + '.echo STACK_EVENT_BUDGET_END\nq\n')


def review(run):
    native = (OUT / f'{run}-stdout.log').read_text(encoding='ascii')
    stack = TransitionFrameStack()
    events = [(v, 'entry') for v in markers(native, 'STACK_ENTRY')]
    events += [(v, 'return') for v in markers(native, 'STACK_RETURN')]
    for event, kind in sorted(events, key=lambda item:item[0]['native_line']):
        (stack.enter if kind == 'entry' else stack.returned)(event)
    result = stack.finish()
    result['client_reconnected'] = '\nSTACK_CLIENT_RECONNECTED\n' in native
    result['liveness'] = markers(native, 'STACK_LIVE')
    result['result'] = 'PARTIALLY_QUALIFIED' if result['all_returned'] else 'FAILED'
    wrapper = json.loads((OUT / f'{run}-result.json').read_text())
    result['wrapper'] = wrapper
    if 'Syntax error' in native or wrapper['timed_out'] or wrapper['exit_code'] != 0:
        result['result'] = 'TOOL_ERROR'
    result['scope'] = 'Hardware entry remains enabled; nested survival requires observed nested events and two repetitions'
    with (OUT / f'{run}-frames.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({k:v for k,v in result.items() if k != 'frames'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','review'))
    parser.add_argument('run', choices=('stack-a','stack-b'))
    args = parser.parse_args()
    (prepare if args.action == 'prepare' else review)(args.run)
