"""Observe controlled startup and API boundaries without guessing wire replies."""
import json
import re
from pathlib import Path

APIS = [('ws2_32', n) for n in ('WSAStartup','socket','connect','send','recv','WSASend','WSARecv','gethostbyname','getaddrinfo','inet_addr')]
APIS += [('kernel32','ExitProcess'),('ntdll32','NtTerminateProcess'),('user32','MessageBoxA'),('user32','MessageBoxW')]
APIS += [('kernel32','CreateFileA'),('kernel32','CreateFileW')]
ARG_COUNTS={'WSAStartup':2,'socket':3,'connect':3,'send':4,'recv':4,'WSASend':7,
            'WSARecv':7,'gethostbyname':1,'getaddrinfo':4,'inet_addr':1,'CreateFileA':7,'CreateFileW':7}


def return_matches(entry, returned):
    return (entry['pid']==returned['pid'] and entry['tid']==returned['tid']
        and entry['ret']==returned['pc'] and returned['time']>=entry['time']
        and returned['sp']==entry['sp']+4*(1+ARG_COUNTS[entry['api']]))


def marker(text):
    found = re.search(r'P2_STOP ([^\n]+)', text)
    if not found:
        raise ValueError('Missing stop context')
    return {k:int(v,16) for k,v in re.findall(r'(\w+)=([0-9a-f]+)',found[1])}


def collect(driver, result, name):
    from trace_qualification.interactive import OUT
    events=[]
    result.update(session_id='GOD2-NATIVE-MASTER-CAPTURE-02',
        arguments=['127.0.0.1','127.0.0.1','6001','0' if name.endswith('02d') else '1'], api_events=events,
        scope='Controlled startup/network observation, not gate certification')
    for index,(module,api) in enumerate(APIS,20):
        driver.command(f'bu{index} {module}!{api}')
    driver.command('bp1 /1 00531e28')
    if name.endswith(('02c','02d')):
        for index,pc in enumerate((0x45b7a4,0x45b786,0x45b791,0x45b79c),2):
            driver.command(f'bp{index} /1 {pc:x}')
    if name.endswith('02e'):
        driver.command('bp6 /1 0045b665')
    driver.command('sxe av')
    pending=None
    resume='g'
    try:
        for sequence in range(100):
            stop=driver.command(resume)
            resume='g'
            mode=driver.command('.effmach #')
            if 'x64' in mode:
                event={'sequence':sequence,'kind':'NATIVE_EXCEPTION_STOP','effective_machine':'amd64',
                       'native_stop':stop,'registers':driver.command('r'),'exception':driver.command('.exr -1'),
                       'call_stack':driver.command('k')}
                events.append(event)
                result['result']='NATIVE_STARTUP_BLOCKER'
                break
            raw=driver.command('.printf "P2_STOP pid=%x tid=%x pc=%p sp=%p ret=%p a0=%p a1=%p a2=%p a3=%p eax=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, poi(@esp), poi(@esp+4), poi(@esp+8), poi(@esp+c), poi(@esp+10), @eax, @$dbgtime')
            event=marker(raw)
            event.update(sequence=sequence, native_stop=stop, registers=driver.command('r'), stack=driver.command('dd @esp L10'))
            events.append(event)
            event['effective_machine']='x86'
            bp=re.search(r'Breakpoint (\d+) hit',stop)
            index=int(bp[1]) if bp else None
            if index==1:
                event['kind']='ARGUMENT_CHECK_PASSED'
                result['argument_check_passed']=True
                driver.command(f'.writemem ..\\output\\{name}-args.bin 400000 L307000')
                continue
            if index==6:
                event['kind']='RUNTIME_API_BYTE_CHECK'
                event['target_identity']=driver.command('ln poi(5707bc)')
                event['target_bytes']=driver.command('db poi(5707bc) L10')
                event['branch_step']=driver.command('t')
                event['branch_result']=driver.command('r')
                result['result']='API_BYTE_CHECK_MISMATCH'
                break
            if index in (2,3,4,5):
                event['kind']='VALIDATION_CHECKPOINT'
                event['state_count']=driver.command('dw @ebp+b2c64 L1')
                event['state_table']=driver.command('dd @ebp+b2c60 L1')
                if index==2:
                    event['call_stack']=driver.command('k')
                    result['result']='VALIDATION_FAILURE_BEFORE_NULL_FORMAT'
                    break
                continue
            if index==90 and pending:
                event.update(kind='API_RETURN',api=pending['api'],entry_sequence=pending['sequence'])
                if not return_matches(pending,event):
                    raise ValueError('API return context mismatch')
                if pending['api']=='recv' and 0<event['eax']<=pending['a2']<=4096:
                    event['rx_dump']=driver.command(f'db {pending["a1"]:x} L{event["eax"]:x}')
                if pending['api']=='connect':
                    result['connect_return']=event['eax']
                    event['wsa_error']='NOT_OBSERVED'
                    result['result']='CONNECT_OBSERVED'
                    break
                pending=None
                continue
            if index is None or not 20<=index<20+len(APIS):
                event['kind']='UNEXPECTED_STOP'
                event['call_stack']=driver.command('k')
                event['exception']=driver.command('.exr -1')
                if 'Access violation' in stop and '(first chance)' in stop:
                    event['kind']='FIRST_CHANCE_AV_DELIVERED_TO_CLIENT'
                    resume='gn'
                    continue
                result['result']='STARTUP_BLOCKER'
                break
            module,api=APIS[index-20]
            event.update(kind='API_ENTRY',api=api,module=module)
            event['call_stack']=driver.command('k')
            if api in ('MessageBoxA','MessageBoxW'):
                event['message']=driver.command(('da ' if api.endswith('A') else 'du ')+f'{event["a1"]:x}')
                result['result']='MESSAGE_BOX_BLOCKER'
                break
            if api in ('ExitProcess','NtTerminateProcess'):
                result['result']='EARLY_EXIT_OBSERVED'
                break
            if api=='connect':
                event['sockaddr_dump']=driver.command(f'db {event["a1"]:x} L10')
            if api in ('inet_addr','gethostbyname'):
                event['name_dump']=driver.command(f'da {event["a0"]:x}')
            if api in ('CreateFileA','CreateFileW'):
                event['path_dump']=driver.command(('da ' if api.endswith('A') else 'du ')+f'{event["a0"]:x}')
            if api=='send' and 0<event['a2']<=4096:
                event['tx_dump']=driver.command(f'db {event["a1"]:x} L{event["a2"]:x}')
            if pending:
                event['return_coverage']='Nested API call; earlier return no longer independently watched'
            pending=event
            driver.command(f'bp90 /1 {event["ret"]:x}')
        else:
            result['result']='EVENT_BUDGET_END'
        result['contexts'].append({'command':'lmv','output':driver.command('lmv')})
        driver.command(f'.writemem ..\\output\\{name}-end.bin 400000 L307000')
    finally:
        (OUT/f'{name}-api-events.json').write_text(json.dumps(events,indent=2))
