"""Evidence-only acceptance of the bounded effective-capacity experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from pagefile_capacity_compat import live_state


def summarize(run):
    report = json.loads((run/'pagefile-capacity-policy.json').read_text())
    events = [json.loads(line) for line in (run/'compat-events.jsonl').read_text().splitlines()]
    events.extend(json.loads(line) for line in (run/'network-events.jsonl').read_text().splitlines())
    events.sort(key=lambda e:e.get('global_sequence',-1))
    run_result = json.loads((run/'run.json').read_text())
    by_pc = {e.get('pc'): e for e in events}
    after = live_state()
    report['host_after'] = after
    unchanged = all(after[k] == report['host_before'][k] for k in ('raw','existing','automatic','settings'))
    report.update(host_modified=not unchanged, fresh_client_started=True,
                  message_905_reached=0x40f24c in by_pc,
                  message_916_reached=0x40f1f5 in by_pc,
                  winsock_reached=any(e.get('api')=='WSAStartup' and e.get('event_type')=='API_RETURN'
                                     and e.get('matched') and e.get('eax')==0 for e in events))
    parser = by_pc.get(0x40f12f, {})
    values = re.findall(r'^[0-9a-f]{8}\s+([0-9a-f]{8})\s*$',
                        parser.get('warning_input',{}).get('parsed_numbers',''),re.M|re.I)
    report['parser_conversion_count'] = parser.get('eax')
    report['parsed_P'] = int(values[0],16) if len(values)==2 else None
    report['second_numeric'] = int(values[1],16) if len(values)==2 else None
    disk = by_pc.get(0x40f16b,{})
    match = re.search(r'^[0-9a-f]{8}\s+([0-9a-f]{8})\s+([0-9a-f]{8})\s+([0-9a-f]{8})\s+([0-9a-f]{8})',
                      disk.get('warning_input',{}).get('outputs_after',''),re.M|re.I)
    if match:
        free,b,s,total = [int(v,16) for v in match.groups()]
        report['real_disk_query'] = dict(success=disk['eax']!=0, S=s,B=b,F=free,total=total,
            address=by_pc[0x40f165].get('real_api_address'),
            root=by_pc[0x40f165]['warning_input']['root_path'])
        q = ((((s*b)&0xffffffff)>>10)*free)&0xffffffff
        report['Q'] = q
        report['T'] = (q + report['parsed_P']) & 0xffffffff if report['parsed_P'] is not None else None
    q_matches = report.get('Q') == by_pc.get(0x40f180,{}).get('eax')
    t_matches = report.get('T') == by_pc.get(0x40f246,{}).get('eax')
    taken = all('[br=1]' in by_pc.get(pc,{}).get('native_stop','') for pc in (0x40f186,0x40f246))
    ordered = [e for e in events if e.get('pc') in (0x40f0d6,0x40f0db,0x40f12f,0x40f165,0x40f16b,0x40f180,0x40f186,0x40f246,0x40f2d0)]
    expected = [0x40f0d6,0x40f0db,0x40f12f,0x40f165,0x40f16b,0x40f180,0x40f186,0x40f246,0x40f2d0]
    continuity = [e['pc'] for e in ordered]==expected and len({(e['pid'],e['tid']) for e in ordered})==1
    native_log = next(run.glob('*-native.log')).read_text(errors='replace')
    # Older captures did not persist the restoration flag, but logged readback.
    wrapper = re.search(r'ds:002b:0057040c=([0-9a-f]{8})',
                        by_pc.get(0x40f165,{}).get('native_stop',''),re.I)
    return_log = native_log.split('Breakpoint 273 hit',1)[-1].split('Breakpoint 274 hit',1)[0]
    restored = report.get('disk_slot_restored',False) or bool(wrapper and
        re.search(r'PFVALUE='+wrapper[1]+r'\b',return_log,re.I))
    checks = dict(host_unchanged=unchanged, single_ordered_thread=continuity,
        graphics_returned=run_result.get('milestones',{}).get('GRAPHICS_RETURNED',False),
        string_table_ready=run_result.get('milestones',{}).get('STRING_TABLE_INITIALIZED',False),
        parser_two_fields=report['parser_conversion_count']==2,
        capacity_matches=report['parsed_P']==report['effective_capacity']['value_mb'],
        untouched_second=report['second_numeric']==0, natural_branches=taken,
        arithmetic_matches=q_matches and t_matches,
        disk_success=report.get('real_disk_query',{}).get('success',False),
        no_warnings=not report['message_905_reached'] and not report['message_916_reached'],
        winsock=report['winsock_reached'], disk_binding_restored=restored,
        single_translation=sum(e.get('event_type')=='PAGEFILE_EFFECTIVE_VIEW' for e in events)==1)
    passed = all(checks.values())
    report.update(checks=checks, runtime_acceptance='PASS' if passed else 'FAIL',
        verdict='CODEX_VERIFIED' if passed else 'NOT_VERIFIED',
        qualification='AUTO_MANAGED_PAGEFILE_COMPAT_VERIFIED' if passed else 'UNVERIFIED',
        PREFIX_WARNING_COMPATIBLE=passed,
        scope='Lab compatibility policy for this observed startup; not recovered InitialSize or full prefix acceptance',
        same_process_continued=report['winsock_reached'],
        next_blocker=('NO_CONNECT_OBSERVED_BEFORE_TIMEOUT'
                      if run_result.get('result')=='HARD_TIMEOUT' and not run_result.get('milestones',{}).get('CONNECTED')
                      else run_result.get('next_blocker',run_result.get('result','UNKNOWN'))),
        server_auto_selected=run_result.get('server_list',{}).get('SERVER_SELECTION_CONFIRMED',False), run_id=run.name,
        interventions=['Existing timeGetTime bridge','One scoped registry-result buffer translation',
                      'One GetDiskFreeSpaceA call bound to KERNELBASE export then restored'],
        evidence=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                  for p in (run/'compat-events.jsonl',run/'network-events.jsonl',run/'run.json')])
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = summarize(args.run)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('runtime_acceptance','checks','next_blocker')}))
