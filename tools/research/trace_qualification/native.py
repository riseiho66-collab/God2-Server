"""Short native x64 CDB qualification; preserve legacy x86 captures."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time

HOME = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(HOME/'tools/research'))
from trace_qualification.interactive import Driver, ROOT, OUT
from host_capture import digest, powershell, firewall_query, firewall_ready, ARTIFACT
from tool_inventory import metadata

CDB = Path('C:/Program Files/WindowsApps/Microsoft.WinDbg_1.2606.22001.0_x64__8wekyb3d8bbwe/amd64/cdb.exe')


class NativeDriver(Driver):
    def stop(self):
        data = b''
        while True:
            remaining = self.deadline-time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Native capture deadline')
            item = self.q.get(timeout=min(remaining, 20))
            if item is None:
                raise RuntimeError('Debugger exited before prompt')
            data += item
            if re.search(rb'\d+:\d+(?::x86)?>\s*$', data):
                return data.decode('ascii', errors='replace')


def run(name, lab=None):
    if any(OUT.glob(name+'-*')):
        raise ValueError('Outputs exist')
    tool = metadata(CDB)
    if tool['architecture'] != 'x64' or tool['signature_status'] != 'Valid' or 'O=Microsoft Corporation' not in tool['signer']:
        raise ValueError('Require signed Microsoft native CDB')
    request = json.loads((ROOT/'host-request.json').read_text())
    if powershell('([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) | ConvertTo-Json'):
        raise ValueError('Non-elevated capture required')
    state = powershell('$v=& { '+firewall_query(request)+' }; $v | ConvertTo-Json -Depth 8')
    if not firewall_ready(state, request['programs']):
        raise ValueError('Work-copy firewall not ready')
    if digest(ROOT/'client/God2.exe') != ARTIFACT or digest(request['original']) != ARTIFACT:
        raise ValueError('Client identity mismatch')
    probe = name == 'native-probe'
    master = name in ('native-master-01','native-master-02','native-master-02b','native-master-02c','native-master-02d','native-master-02e')
    if master:
        from trace_qualification.native_review import review
        review('native-f')
        review('native-g')
    if not probe and json.loads((ROOT/'output/native-probe-result.json').read_text())['result'] != 'PROBE_PASS':
        raise ValueError('Benign native probe required')
    (OUT/f'{name}-firewall.json').write_text(json.dumps(state,indent=2))
    result = {'result':'FAILED', 'tool':tool, 'contexts':[],
              'scope':'Short mode qualification, not a formal G02/G03 capture',
              'network_scope':'Existing work-copy program blocks retained; native debugger not firewalled; explicit local symbol path'}
    driver = None
    try:
        target = [str(Path(os.environ['WINDIR'])/'SysWOW64/cmd.exe'),'/c','exit'] if probe else [str(ROOT/'client/God2.exe')]
        if lab or name in ('native-args-check','native-master-02','native-master-02b','native-master-02c','native-master-02d','native-master-02e'):
            target += ['127.0.0.1','127.0.0.1','6001','0' if not lab and name.endswith('02d') else '1']
        command = [str(CDB), '-y', str(ROOT/'debugger'), *target]
        if os.environ.get('GOD2_PRIVATE_DESKTOP') == '1':
            wrapper = HOME/'build-strike-lab/Release/God2PrivateDesktop.exe'
            if not wrapper.is_file():
                raise FileNotFoundError('Private desktop runner has not been built')
            command.insert(0, str(wrapper))
        driver = NativeDriver(command, name)
        driver.stop()
        if lab:
            result['scope'] = 'Targeted STRIKE LAB startup observation, not gate certification'
            lab.arm(driver, result, name)
        for cmd in ('.effmach', '.effmach x86', 'r', '.effmach amd64', 'r', '.effmach #', '.load wow64exts', '!wow64exts.info'):
            result['contexts'].append({'command':cmd, 'output':driver.command(cmd)})
        if probe:
            result['result'] = 'PROBE_PASS' if all('Syntax error' not in c['output'] for c in result['contexts']) else 'TOOL_ERROR'
            return
        driver.command('.effmach x86')
        driver.command('bp 00702001')
        for attempt in range(3):
            stopped = driver.command('g')
            driver.command('.effmach x86')
            if 'eip=00702001' in driver.command('r'):
                break
            if 'WOW64 breakpoint' not in stopped:
                raise ValueError('Unexpected stop before packed entry')
        else:
            raise ValueError('Packed entry not reached')
        if master:
            for cmd in ('r','dd @esp L8','!vprot @eip',
                        '.printf "MASTER_PACKED pid=%x tid=%x eip=%p esp=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, @$dbgtime',
                        f'.writemem ..\\output\\{name}-before.bin 400000 L307000'):
                result['contexts'].append({'command':cmd,'output':driver.command(cmd)})
        driver.command('bc 0' if lab else 'bc *')
        driver.command('ba e 1 007023bf')
        driver.command('g')
        driver.command('.effmach x86')
        if 'eip=007023bf' not in driver.command('r'):
            raise ValueError('Unpack transfer not reached')
        if master:
            for cmd in ('r','dd @esp L8', '.printf "MASTER_TRANSFER pid=%x tid=%x eip=%p esp=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, @$dbgtime'):
                result['contexts'].append({'command':cmd,'output':driver.command(cmd)})
        driver.command('bc 0' if lab else 'bc *')
        driver.command('t')
        driver.command('.effmach x86')
        if 'eip=0054a3e8' not in driver.command('r'):
            raise ValueError('Candidate mismatch')
        if lab:
            lab.collect(driver, result, name)
            return
        if name == 'native-args-check':
            for cmd in ('bp 00531e16','g','bc *','.effmach x86','r','da @esi','t 0n2','r'):
                result['contexts'].append({'command':cmd,'output':driver.command(cmd)})
            result['result']='OBSERVED_PENDING_REVIEW'
            return
        if name == 'native-launch-check':
            for cmd in ('bp 00531dc5','g','bc *','.effmach x86','r','da @esi','db @esi L20','t 0n4','r'):
                result['contexts'].append({'command':cmd,'output':driver.command(cmd)})
            result['result']='OBSERVED_PENDING_REVIEW'
            return
        if master:
            for cmd in ('db 54a3e8 L20','!vprot 54a3e8',
                        '.printf "MASTER_CANDIDATE pid=%x tid=%x eip=%p esp=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, @$dbgtime',
                        f'.writemem ..\\output\\{name}-after.bin 400000 L307000'):
                result['contexts'].append({'command':cmd,'output':driver.command(cmd)})
            if name in ('native-master-02','native-master-02b','native-master-02c','native-master-02d','native-master-02e'):
                from trace_qualification.phase2 import collect
                collect(driver,result,name)
                return
            for api in ('connect','send','recv','WSASend','WSARecv'):
                driver.command('bu ws2_32!'+api)
            for pc in (0x54a40e,0x54a414,0x54a441,0x54f12a,0x54a446,0x54a453,0x54df7c,0x54a458,0x54a469,0x54ebbf):
                driver.command(f'bp /1 {pc:x}')
                driver.command('g')
                driver.command('.effmach x86')
                registers = driver.command('r')
                result['contexts'].append({'command':f'checkpoint {pc:x}','output':registers})
                if f'eip={pc:08x}' not in registers:
                    raise ValueError('Unexpected master checkpoint; inspect native output')
                driver.command('dd @esp L8')
                driver.command('!vprot @eip')
        driver.command('bp 005479bd')
        driver.command('g')
        driver.command('bc *')
        lookup = driver.command('x ntdll32!Wow64Transition')
        addresses = re.findall(r'^([0-9a-f`]+)\s+\S*!Wow64Transition', lookup, re.M)
        if len(addresses) != 1:
            raise ValueError('Ambiguous WOW64 transition symbol: '+lookup)
        driver.command('r @$t3 = poi('+addresses[0]+')')
        driver.command('bp @$t3')
        driver.command('g')
        driver.command('bc *')
        for cmd in ('.effmach x86', 'r', 'dd @esp L8', 'r @$t1 = poi(@esp)',
                    'r @$t2 = @esp', '.printf "NATIVE_X86_ENTRY pid=%x tid=%x eip=%p esp=%p expected=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, @$t1, @$dbgtime',
                    '.effmach amd64', 'r', 'u @rip L4', 't', '.effmach #', 'r',
                    '.printf "NATIVE_EXEC pid=%x tid=%x rip=%p rsp=%p time=%I64x\\n", @$tpid, @$tid, @rip, @rsp, @$dbgtime'):
            result['contexts'].append({'command':cmd, 'output':driver.command(cmd)})
        code = driver.command('u wow64cpu!TurboDispatchJumpAddressEnd-200 L100')
        result['contexts'].append({'command':'native return candidate disassembly','output':code})
        sites = re.findall(r'^([0-9a-f`]+)\s+[0-9a-f]+\s+(?:jmp\s+fword ptr \[r14\]|iretq)', code, re.M)
        if not sites:
            raise ValueError('No observed native return candidates')
        for site in sites:
            driver.command('bp '+site)
        driver.command('g')
        for cmd in ('.effmach #','r','dq @r14 L4',
                    '.printf "NATIVE_RETURN pid=%x tid=%x rip=%p rsp=%p time=%I64x\\n", @$tpid, @$tid, @rip, @rsp, @$dbgtime',
                    'bc *','t','.effmach #','r',
                    '.printf "NATIVE_X86_RETURN pid=%x tid=%x eip=%p esp=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, @$dbgtime'):
            result['contexts'].append({'command':cmd,'output':driver.command(cmd)})
        if master:
            for pc in (0x54ed7a,0x54a46e):
                driver.command(f'bp /1 {pc:x}')
                driver.command('g')
                driver.command('.effmach x86')
                registers = driver.command('r')
                result['contexts'].append({'command':f'checkpoint {pc:x}','output':registers})
                if f'eip={pc:08x}' not in registers:
                    raise ValueError('Unexpected final checkpoint')
                driver.command('dd @esp L8')
            driver.command('t 0n32')
            for cmd in ('r','!vprot 54a3e8','lmv',
                        f'.writemem ..\\output\\{name}-stable.bin 400000 L307000'):
                result['contexts'].append({'command':cmd,'output':driver.command(cmd)})
            for api in ('connect','send','recv','WSASend','WSARecv'):
                driver.command('bu ws2_32!'+api)
            driver.command('bu kernel32!ExitProcess')
            driver.command('bu ntdll32!NtTerminateProcess')
            result['startup_collected'] = True
            driver.command('g')
            for cmd in ('.effmach #','r','k','dd @esp L10','lmv',
                        f'.writemem ..\\output\\{name}-next-stop.bin 400000 L307000'):
                result['contexts'].append({'command':cmd,'output':driver.command(cmd)})
        result['result'] = 'OBSERVED_PENDING_REVIEW'
    except Exception as error:
        result['error'] = repr(error)
        result['result'] = 'TOOL_ERROR'
    finally:
        if driver:
            driver.close()
            result['native_sha256'] = digest(OUT/f'{name}-native.log')
        (OUT/f'{name}-result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:v for k,v in result.items() if k not in ('contexts','tool','api_events')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', choices=('native-probe','native-a','native-b','native-c','native-d','native-e','native-f','native-g','native-master-01','native-master-02','native-master-02b','native-master-02c','native-master-02d','native-master-02e','native-launch-check','native-args-check'))
    run(parser.parse_args().name)
