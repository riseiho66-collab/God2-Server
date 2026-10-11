"""Only loader prerequisites, focus callback and preidentified network entries."""
import json
import re
import time
from capture import Observer as BaseObserver, parse_marker

NETWORK=('WSAStartup','socket','connect','send','recv','WSASend','WSARecv')
SITES={
    4:(0x456130,'TABLE_FILE_LOADER_ENTRY'),5:(0x456682,'SYSTEMMESSAGE_DISPATCH_CALL'),
    6:(0x458ff0,'S4_SYSTEMMESSAGE_INITIALIZER'),7:(0x459012,'TABLE_POINTER_STORE_BEFORE'),
    8:(0x459112,'TABLE_COUNT_STORE_BEFORE'),9:(0x45b7a4,'S6_FAILURE_BEFORE_NULL_FORMAT'),
    10:(0x40dbd0,'SUBSYSTEM_INIT_CALL'),11:(0x40dbd5,'SUBSYSTEM_INIT_RETURN'),
    12:(0x40dbf3,'STARTUP_TABLES_CALL'),13:(0x40e3b0,'WINDOW_MESSAGE_ENTRY'),
    14:(0x40e42c,'FOCUS_MESSAGE_CASE'),15:(0x45b630,'VALIDATION_ENTRY'),
    16:(0x53c25f,'COOPERATIVE_LEVEL_CALL'),17:(0x53c262,'COOPERATIVE_LEVEL_RETURN'),
    18:(0x45b665,'API_BYTE_CHECK_BRANCH'),
}


class Observer(BaseObserver):
    def arm(self,driver,result,name):
        driver.deadline=time.monotonic()+120
        driver.command(f'.load "{self.dll.as_posix()}"')
        driver.command('.effmach #')
        self.snapshot(driver,'S0_PROCESS_DEBUG_STOP')
        driver.command('.effmach x86')
        for index,api in enumerate(NETWORK,100):
            driver.command(f'bu{index} ws2_32!{api} ".printf \\"LAB_EARLY api={api} pid=%x tid=%x pc=%p\\\\n\\", @$tpid, @$tid, @eip; gc"')

    def collect(self,driver,result,name):
        outcome='EVENT_BUDGET_END'
        result['api_events']=self.events
        try:
            self.previous=self.snapshot(driver,'RESTORED_CANDIDATE')
            for index,(pc,label) in SITES.items(): driver.command(f'bp{index} {pc:x}')
            for index,api in enumerate(NETWORK,100):
                driver.command(f'bc {index}'); driver.command(f'bu{index} ws2_32!{api}')
            driver.command('bu110 kernel32!ExitProcess')
            roots=json.loads((self.run.parents[2]/'artifacts/reports/strike-lab-final-20260919/network-root-candidates.json').read_text())['references']
            for index,root in enumerate(roots,120): driver.command(f'bp{index} {int(root["va"],16):x}')
            result['lab_breakpoint_inventory']=driver.command('bl')
            driver.command('sxe av')
            for seq in range(120):
                stopped=driver.command('g')
                mode=driver.command('.effmach #')
                if 'x64' in mode:
                    outcome='NATIVE_STOP'; self.events.append({'event_type':outcome,'native_stop':stopped,'registers':driver.command('r')}); break
                raw=driver.command('.printf "LAB_STOP pid=%x tid=%x pc=%p sp=%p ret=%p a0=%p a1=%p a2=%p eax=%p ecx=%p ebp=%p esi=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, poi(@esp), poi(@esp+4), poi(@esp+8), poi(@esp+c), @eax, @ecx, @ebp, @esi, @$dbgtime')
                event=parse_marker(raw); event.update(sequence=seq,run_id=name,timestamp=time.time(),native_stop=stopped)
                self.events.append(event)
                match=re.search(r'Breakpoint (\d+) hit',stopped); index=int(match[1]) if match else None
                if index in SITES:
                    event.update(event_type=SITES[index][1],snapshot=self.snapshot(driver,SITES[index][1]),
                                 raw_stack=driver.command('dd @esp L18'),registers=driver.command('r'))
                    if index==4: event['requested_path']=driver.command('da poi(@esp+4) L100')
                    if index in (7,8):
                        event['instruction']=driver.command('u @eip L1')
                        driver.command('t'); event['after_store']=self.snapshot(driver,'FIELD_STORE_AFTER')
                    if index==13:
                        event['message_id']=event['a1']
                        event['hwnd']=event['a0']
                    if index==15:
                        event['direct_caller']=hex(event['ret'])
                    if index==16:
                        event['vtable_target']=driver.command('ln poi(@ecx+50)')
                    if index==18:
                        event['api_target']=driver.command('ln poi(5707bc)')
                        event['api_bytes']=driver.command('db poi(5707bc) L10')
                        event['branch_step']=driver.command('t')
                        event['branch_result']=driver.command('r')
                    if index==9:
                        outcome='VALIDATION_FAILURE_BEFORE_NULL_FORMAT'; break
                elif index is not None and 100<=index<107:
                    api=NETWORK[index-100]; event.update(event_type='API_ENTRY',api=api)
                    self.network.append(api)
                    if api=='connect':
                        event['sockaddr_dump']=driver.command(f'db {event["a1"]:x} L10')
                        event['sockaddr_marker']=driver.command(f'.printf "LAB_CONNECT af=%x port=%x ip=%x\\n", wo({event["a1"]:x}), wo({event["a1"]+2:x}), dwo({event["a1"]+4:x})')
                        outcome='CONNECT_ENTRY_OBSERVED'; break
                    if api=='send' and 0<event['a2']<=4096:
                        event['tx_dump']=driver.command(f'db {event["a1"]:x} L{event["a2"]:x}')
                elif index is not None and 120<=index<120+len(roots):
                    event.update(event_type='STATIC_NETWORK_CANDIDATE_HIT',candidate=roots[index-120])
                elif index==110:
                    event['event_type']='EXIT_PROCESS'; outcome='EXIT_PROCESS'; break
                else:
                    event['event_type']='UNEXPECTED_STOP'; outcome='UNEXPECTED_STOP'; break
            result['result']=outcome
        finally:
            self.persist(driver,result,outcome)

    def persist(self,driver,result,outcome):
        super().persist(driver,result,outcome)
        path=self.run/'summary.json'
        summary=json.loads(path.read_text())
        summary.update(write_count=None,write_scope='OMEGA observes explicit store sites only; no hardware write watches armed',
                       write_watch_enabled=False)
        summary.pop('window_observation',None)
        # Finalize this new run before lab.py binds its evidence; never edit prior runs.
        path.write_text(json.dumps(summary,indent=2))
