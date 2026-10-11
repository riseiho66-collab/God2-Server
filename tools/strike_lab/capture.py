"""Targeted startup observer on the already qualified native CDB driver."""
import json
import re
import socket
import time

WS = {'WSAStartup':2,'socket':3,'connect':3,'send':4,'recv':4,'WSASend':7,'WSARecv':7,
      'select':5,'closesocket':1,'gethostbyname':1,'getaddrinfo':4,'inet_addr':1}
KERNEL = {'GetCommandLineA':0,'GetCommandLineW':0,'GetCurrentDirectoryA':2,'GetCurrentDirectoryW':2,
    'SetCurrentDirectoryA':1,'SetCurrentDirectoryW':1,'GetModuleFileNameA':3,'GetModuleFileNameW':3,
    'GetEnvironmentVariableA':3,'GetEnvironmentVariableW':3,'CreateFileA':7,'CreateFileW':7,
    'ReadFile':5,'GetFileSize':2,'SetFilePointer':4,'CloseHandle':1,
    'FindResourceA':3,'FindResourceW':3,'LoadResource':2,'LockResource':1,'SizeofResource':2}
REG = {'RegOpenKeyExA':5,'RegOpenKeyExW':5,'RegQueryValueExA':6,'RegQueryValueExW':6,'RegCloseKey':1}
APIS = [(module, api, count) for module, values in (('ws2_32',WS),('kernel32',KERNEL),('advapi32',REG))
        for api,count in values.items()]
APIS += [('kernel32','ExitProcess',1),('ntdll32','NtTerminateProcess',2),('user32','MessageBoxA',4),('user32','MessageBoxW',4)]


def parse_marker(raw):
    line = re.search(r'LAB_STOP ([^\r\n]+)', raw)
    if not line:
        raise ValueError('Missing x86 marker')
    return {k:int(v,16) for k,v in re.findall(r'(\w+)=([0-9a-f]+)',line[1])}


class Observer:
    def __init__(self, run, dll):
        self.run = run
        self.dll = dll
        self.events = []
        self.snapshots = []
        self.previous = None
        self.writes = []
        self.paths = set()
        self.resources = set()
        self.network = []

    def snapshot(self, driver, stage):
        raw = driver.command('!God2Probe.snapshot')
        match = re.search(r'GOD2_PROBE (\{[^\r\n]+\})',raw)
        if not match:
            raise ValueError('Read-only extension did not produce snapshot: '+raw)
        state = json.loads(match[1])
        state.update(stage=stage, run_id=self.run.name)
        self.snapshots.append(state)
        return state

    def arm(self, driver, result, name):
        driver.deadline = time.monotonic()+300
        driver.command('.effmach #')
        loaded = driver.command(f'.load "{self.dll.as_posix()}"')
        if 'failed' in loaded.lower():
            raise ValueError(loaded)
        self.snapshot(driver, 'S0_PROCESS_DEBUG_STOP')
        driver.command('.effmach x86')
        for index,(module,api,_) in enumerate(APIS,100):
            driver.command(f'bu{index} {module}!{api} ".printf \\"LAB_EARLY api={api} pid=%x tid=%x pc=%p sp=%p caller=%p\\\\n\\", @$tpid, @$tid, @eip, @esp, poi(@esp); gc"')
        result['lab_scope'] = 'Debugger-host read-only extension; debugger breakpoints; no injection or API return changes'

    def collect(self, driver, result, name):
        pending = None
        resume = 'g'
        outcome = 'EVENT_BUDGET_END'
        result['api_events'] = self.events
        try:
            for index,(module,api,_) in enumerate(APIS,100):
                driver.command(f'bc {index}')
                condition = f' ".if ((poi(@esp) < 400000) | (poi(@esp) >= 707000)) {{ gc }} .else {{ .echo LAB_API {index} }}"' if api in ('ReadFile','GetFileSize','SetFilePointer','CloseHandle') else ''
                driver.command(f'bu{index} {module}!{api}{condition}')
            self.previous = self.snapshot(driver, 'S0_RESTORED_CANDIDATE')
            driver.command('ba2 w 2 6931a0')
            driver.command('ba3 w 4 69319c')
            for index,pc in ((4,0x531e28),(5,0x45b662),(6,0x45b665),(7,0x45b7a4),
                             (8,0x458ff0),(9,0x459141),(10,0x456130),(11,0x4561a7),(12,0x456682)):
                driver.command(f'bp{index} /1 {pc:x}')
            result['lab_breakpoint_inventory']=driver.command('bl')
            driver.command('sxe av')
            for sequence in range(800):
                stop = driver.command(resume)
                resume = 'g'
                mode = driver.command('.effmach #')
                if 'x64' in mode:
                    self.events.append({'event_type':'NATIVE_STOP','native_stop':stop,'registers':driver.command('r'),
                                        'exception':driver.command('.exr -1'),'run_id':name})
                    outcome = 'NATIVE_STARTUP_BLOCKER'
                    break
                raw = driver.command('.printf "LAB_STOP pid=%x tid=%x pc=%p sp=%p ret=%p a0=%p a1=%p a2=%p a3=%p eax=%p ebp=%p ecx=%p edx=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, poi(@esp), poi(@esp+4), poi(@esp+8), poi(@esp+c), poi(@esp+10), @eax, @ebp, @ecx, @edx, @$dbgtime')
                event = parse_marker(raw)
                event.update(sequence=sequence,run_id=name,timestamp=time.time(),native_stop=stop,
                             arguments=None,return_value=None,buffer_va=None,buffer_length=None,bytes=None)
                self.events.append(event)
                match = re.search(r'(?:Breakpoint |LAB_API )(\d+)',stop)
                index = int(match[1]) if match else None
                if index in (8,9,10,11,12):
                    labels={8:'S4_SYSTEMMESSAGE_INITIALIZER',9:'S5_SYSTEMMESSAGE_INITIALIZER_RETURN',
                            10:'TABLE_FILE_LOADER_ENTRY',11:'TABLE_HEADER_PARSED',12:'SYSTEMMESSAGE_DISPATCH_CALL'}
                    event.update(event_type=labels[index],snapshot=self.snapshot(driver,labels[index]),call_stack=driver.command('k'))
                    if index==10:
                        event['requested_path']=driver.command(f'da {event["a0"]:x} L100')
                    if index==11:
                        event['header']=driver.command('da @esp+18 L80')
                    continue
                if index in (2,3):
                    state = self.snapshot(driver,'STRING_TABLE_WRITE')
                    event.update(event_type='STRING_TABLE_WRITE',old=self.previous,new=state,
                                 stop_rva=event['pc']-0x400000,
                                 writer_instruction='UNKNOWN; data breakpoint PC is after the write',
                                 preceding_disassembly=driver.command('ub @eip L8'),call_stack=driver.command('k'))
                    self.writes.append(event)
                    self.previous=state
                    continue
                if index in (4,5,6,7):
                    stages={4:'S1_ARGUMENTS_PARSED',5:'S2_BEFORE_COMPATIBILITY',6:'S3_COMPATIBILITY_BRANCH',7:'S6_FAILURE_BEFORE_NULL_FORMAT'}
                    event.update(event_type=stages[index],snapshot=self.snapshot(driver,stages[index]))
                    if index==4:
                        result['argument_check_passed']=True
                    if index in (5,6):
                        event.update(api_target=driver.command('ln poi(5707bc)'),api_bytes=driver.command('db poi(5707bc) L10'),
                                     instruction=driver.command('u @eip L3'))
                    if index==6:
                        event['branch_step']=driver.command('t')
                        event['branch_after']=driver.command('r')
                    if index==7:
                        event.update(call_stack=driver.command('k'),object_matches=event['ebp']==0x5e053c)
                        outcome='VALIDATION_FAILURE_BEFORE_NULL_FORMAT'
                        break
                    continue
                if index==90 and pending:
                    api=pending['api']
                    matched=(event['pid']==pending['pid'] and event['tid']==pending['tid'] and event['pc']==pending['ret']
                        and event['sp']==pending['sp']+4*(1+pending['argument_count']) and event['time']>=pending['time'])
                    event.update(event_type='API_RETURN',api=api,entry_sequence=pending['sequence'],
                                 return_value=event['eax'],context_matched=matched)
                    if matched:
                        event['thread_last_error']='NOT_QUALIFIED_WITH_LOCAL_SYMBOLS'
                        if api=='ReadFile' and event['eax']:
                            event['bytes_read']=driver.command(f'dd {pending["a3"]:x} L1')
                        if api in ('GetCommandLineA','GetCommandLineW') and event['eax']:
                            event['value']=driver.command(('du ' if api.endswith('W') else 'da ')+f'{event["eax"]:x} L100')
                        if api in ('GetCurrentDirectoryA','GetCurrentDirectoryW') and event['eax']:
                            event['value']=driver.command(('du ' if api.endswith('W') else 'da ')+f'{pending["a1"]:x} L100')
                        if api=='recv' and 0<event['eax']<=pending['a2'] and event['eax']<=4096:
                            event['rx_dump']=driver.command(f'db {pending["a1"]:x} L{event["eax"]:x}')
                        if api=='connect':
                            outcome='CONNECT_OBSERVED'
                            break
                    pending=None
                    continue
                if index is None or not 100<=index<100+len(APIS):
                    event.update(event_type='UNEXPECTED_STOP',registers=driver.command('r'),exception=driver.command('.exr -1'))
                    if 'Access violation' in stop and '(first chance)' in stop:
                        self.snapshot(driver,'S6_FIRST_CHANCE_FAULT')
                        resume='gn'
                        continue
                    outcome='UNEXPECTED_STOP'
                    break
                module,api,argc=APIS[index-100]
                event.update(event_type='API_ENTRY',module=module,api=api,argument_count=argc,
                             arguments=[event[f'a{i}'] for i in range(min(4,argc))],
                             caller_va=event['ret'],caller_rva=event['ret']-0x400000 if 0x400000<=event['ret']<0x707000 else None,
                             call_stack=driver.command('k 6'))
                if api in WS:
                    self.network.append(api)
                    if len(self.network)==1:
                        self.snapshot(driver,'S7_FIRST_WINSOCK')
                if api.startswith(('CreateFile','SetCurrentDirectory','GetEnvironmentVariable')):
                    event['path_or_name']=driver.command(('du ' if api.endswith('W') else 'da ')+f'{event["a0"]:x} L100')
                    if api.startswith('CreateFile'):
                        self.paths.add(''.join(re.findall(r'"([^"\r\n]*)"',event['path_or_name'])))
                if api in ('FindResourceA','FindResourceW'):
                    self.resources.add(f'{api}:{event["a1"]:x}:{event["a2"]:x}')
                if api=='connect':
                    event['sockaddr_dump']=driver.command(f'db {event["a1"]:x} L10')
                    event['sockaddr_marker']=driver.command(f'.printf "LAB_CONNECT af=%x port=%x ip=%x\\n", wo({event["a1"]:x}), wo({event["a1"]+2:x}), dwo({event["a1"]+4:x})')
                if api=='send' and 0<event['a2']<=4096:
                    event.update(buffer_va=event['a1'],buffer_length=event['a2'],
                                 tx_dump=driver.command(f'db {event["a1"]:x} L{event["a2"]:x}'))
                if api in ('ExitProcess','NtTerminateProcess','MessageBoxA','MessageBoxW'):
                    outcome='EARLY_EXIT_OR_MESSAGE'
                    break
                if pending:
                    pending['return_coverage']='Replaced by nested API; unmatched return not interpreted'
                pending=event
                driver.command(f'bp90 /1 {event["ret"]:x}')
            result['result']=outcome
        finally:
            self.persist(driver, result, outcome)

    def persist(self, driver, result, outcome):
        modules=''
        try:
            modules=driver.command('lm')
            (self.run/'modules.txt').write_text(modules)
            driver.command(f'.writemem "{(self.run / "selected-object.bin").as_posix()}" 693180 L60')
        except Exception as error:
            result['lab_final_snapshot_error']=repr(error)
        final = self.snapshots[-1] if self.snapshots else {}
        summary={'outcome':outcome,'string_table_classification':'UNKNOWN',
            'write_count':len(self.writes),'write_scope':'Only restored candidate to final observed stop; not whole process lifetime',
            'io_scope':'ReadFile/GetFileSize/SetFilePointer/CloseHandle restricted to immediate callers in client image; other API entries unfiltered',
            'count':final.get('count'),'pointer':final.get('pointer'),
            'initializer_function':'UNKNOWN','string_table_source':'UNKNOWN','preconditions':'UNKNOWN','failure_reason':'UNKNOWN',
            'network_apis':self.network,'paths':sorted(self.paths),'resources':sorted(self.resources),
            'modules':sorted(re.findall(r'^[0-9a-f`]+\s+[0-9a-f`]+\s+(\S+)',modules,re.M)),
            'snapshots_unavailable':['S4_INITIALIZER_UNKNOWN','S5_INITIALIZER_UNKNOWN']}
        if outcome=='VALIDATION_FAILURE_BEFORE_NULL_FORMAT' and not any(e.get('event_type')=='S4_SYSTEMMESSAGE_INITIALIZER' for e in self.events):
            summary.update(string_table_classification='INITIALIZER_NOT_CALLED',
                initializer_function='0x458ff0 (static SystemMessage dispatcher target)',
                preconditions='0x456130 loader success; SystemMessage header dispatch; positive row count for rows',
                failure_reason='Compatibility failure occurs before observed initializer entry; source-file failure NOT established',
                snapshots_unavailable=['S4_INITIALIZER_NOT_REACHED','S5_INITIALIZER_NOT_REACHED'])
        if not self.writes:
            summary['window_observation']='NO_WRITE_OBSERVED_IN_MONITORED_WINDOW'
        elif final.get('pointer')==0 and any(e['new'].get('pointer') for e in self.writes):
            summary['string_table_classification']='WRITTEN_THEN_CLEARED'
        for name,value in (('events.json',self.events),('snapshots.json',self.snapshots),('summary.json',summary)):
            with (self.run/name).open('x',encoding='utf-8') as stream:
                json.dump(value,stream,indent=2)
