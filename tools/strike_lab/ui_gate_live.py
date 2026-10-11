"""Run-owned rendezvous lifecycle; never produces UI input or game traffic."""
import json
import msvcrt
import sys
import time
from datetime import datetime, timezone

import psutil

from ui_gate import Rendezvous, REQUIRED_TRUE, atomic_json


class RunLease:
    def __init__(self, root):
        self.stream = (root/'ui_gate.lock').open('a+b')
        self.stream.seek(0)
        try:msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            self.stream.close()
            raise RuntimeError('Another rendezvous owns the gate')

    def close(self):
        if not self.stream.closed:
            self.stream.seek(0)
            msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            self.stream.close()


def prefix_verified(home, run, events):
    golden = home/'artifacts/golden/server-list/server-list-one-01'
    rx = b''.join((run/'s2c'/f'recv-{e["sequence"]:04}.bin').read_bytes()
                  for e in events if e.get('api') == 'recv' and e.get('matched')
                  and 0 < e.get('eax', 0) <= 4096)
    tx = b''.join((run/e['accepted_buffer']).read_bytes()
                  for e in events if e.get('accepted_buffer'))
    expected_rx = b''.join((golden/name).read_bytes() for name in (
        'S2C_0001.bin', 'S2C_0002.bin', 'S2C_0003.bin',
        'S2C_SERVER_LIST_0001.bin', 'S2C_0004.bin'))
    expected_tx = b''.join((golden/name).read_bytes() for name in ('C2S_0001.bin', 'C2S_0002.bin'))
    state = any(e.get('event_type') == 'LOGIN_STATE_CHANGE_RETURN'
                and 'state=2 previous=f' in e.get('ui_state', '') for e in events)
    returned = any(e.get('event_type') == 'LOGIN_TERMINAL_RETURN'
                   and e.get('eax') == 0 for e in events)
    from server_list import qualifies, WIRE
    return rx == expected_rx and tx == expected_tx and state and returned and qualifies({'LOGIN': True}, events, WIRE)


class LongLivedRunContext:
    def __init__(self, home, run, server, driver, max_wait):
        self.home, self.run, self.server, self.driver = home, run, server, driver
        self.control = Rendezvous(run.name, max_wait)
        self.client = None
        self.active = False
        self.prepared = False
        self.reason = None
        self.next_tick = 0
        self.result = None
        self.paths = []
        self.records = {
            'server': self.record(psutil.Process(server.process.pid)),
            'debugger': self.record(psutil.Process(driver.p.pid)),
        }

    @staticmethod
    def record(process):
        return {'pid': process.pid, 'launch_timestamp': process.create_time(),
                'owned_by_run': True, 'alive': process.is_running()}

    def prepare(self, events, event):
        if not prefix_verified(self.home, self.run, events):
            raise RuntimeError('Rendezvous golden prefix regression')
        client = psutil.Process(event['pid'])
        from lab import CLIENT
        if client.exe().casefold() != str(CLIENT/'God2.exe').casefold():
            raise RuntimeError('Client identity mismatch')
        if self.driver.p.pid not in [p.pid for p in client.parents()]:
            raise RuntimeError('Client is not owned by this debugger')
        self.client = client
        self.records['client'] = self.record(client)
        for index in range(4,17):self.driver.command(f'bc {index}')
        from apex import APIS
        quiet = {'send','WSASend','recv','WSARecv','socket','WSASocketA',
                 'WSASocketW','connect','WSAConnect','closesocket','shutdown'}
        if getattr(self,'preserve_select_coverage',False):
            quiet.add('select')
            self.driver.command(f'bu{100+APIS.index("select")} ws2_32!select')
        for index, api in enumerate(APIS,100):
            if api not in quiet:self.driver.command(f'bc {index}')
        self.driver.command('bc 244')
        self.driver.command('bp249 407040 ".if (by(@esp+8)&1) {.if (wo(@esp+4)==6) {.echo Breakpoint 249 hit} .else {gc}} .else {gc}"')
        self.driver.command('bp250 4070b0 ".if ((by(@esp+8)&4)!=0) {.echo Breakpoint 250 hit} .else {gc}"')
        armed = self.driver.command('bl')
        (self.run/'ui-gate-armed.txt').write_text(armed, encoding='utf-8')
        for marker in ('00407040', '004070b0', '!send', '!recv', '!connect',
                       '!socket', '!closesocket', '!shutdown', '!WSASend',
                       '!WSARecv', '!WSAConnect', '!WSASocketA', '!WSASocketW'):
            if marker.casefold() not in armed.casefold():
                raise RuntimeError('Required breakpoint not verified: '+marker)
        for target in ('REPLAY_GOLDEN_PREFIX', 'SERVER_AUTO_SELECTED', 'ARM_POST_GATE_OBSERVERS'):
            self.control.transition(target, time.monotonic())
        self.server.request_hold(True,wait=True)
        self.prepared = True

    def health(self):
        alive = self.client is not None and self.client.is_running()
        connected = False
        if alive:
            connected = any(c.status == psutil.CONN_ESTABLISHED and c.raddr
                            and c.raddr.ip == '127.0.0.1' and c.raddr.port == 2592
                            for c in self.client.net_connections(kind='tcp'))
        health = dict.fromkeys(REQUIRED_TRUE, self.prepared)
        health.update(pid=self.client.pid if self.client else 0,
                      client_alive=alive, server_alive=self.server.process.poll() is None,
                      observer_alive=self.driver.p.poll() is None and self.driver.reader.is_alive(),
                      socket_alive=connected, session_alive=connected,
                      client_running=bool(getattr(self.driver,'executing_target',False)),
                      server_count=1, selected_entry_id=0)
        status=self.server.hold_status()
        health['server_session_hold_active']=status.get('ui_gate_hold_active') is True
        health['server_timeout_telemetry']=status
        return health

    def tick(self):
        now = time.monotonic()
        if now < self.next_tick:return
        self.next_tick = now + 2
        if (self.run/'cancel.request').exists():
            self.reason='OPERATOR_CANCEL'
            self.driver.deadline=now
            self.control.cancel(self.reason)
            return
        if not self.prepared:
            if self.server.process.poll() is not None:
                self.reason = 'SERVER_EXIT'
                self.driver.deadline = now
            return
        self.server.request_hold(True)
        health = self.health()
        self.control.refresh(health, now)
        if not self.active and not self.reason:
            self.control.transition('UI_GATE_READY', now)
            self.control.transition('WAIT_EXTERNAL_UI', now)
            self.active = True
            print('UI_GATE_READY\n\nGOD2 is alive and waiting at the selected server.\n\n'
                  'Perform one normal visible server-selection confirmation.\n\n'
                  'Do not close GOD2.\nDo not restart the server.', file=sys.__stdout__, flush=True)
        if self.control.termination_reason:
            self.reason = self.control.termination_reason
            self.driver.deadline = now
        snapshot = self.control.snapshot()
        snapshot['processes'] = self.records
        snapshot['wait_duration'] = now-self.control.wait_started if self.control.wait_started is not None else 0
        atomic_json(self.run/'ui_gate.json', snapshot)
        atomic_json(self.home/'artifacts/strike/ui_gate.json', snapshot)

    def path(self, event):
        self.paths.append(event)
        atomic_json(self.run/'ui-path-events.json', self.paths)

    def network_return(self, event, pending, driver):
        api, value = event['api'], event['eax']
        if api == 'send' and 0 < value <= pending['a2'] and pending.get('buffer_file'):
            packet = (self.run/pending['buffer_file']).read_bytes()[:value]
            path = self.run/'C2S_SERVER_SELECT_0001.bin'
            path.write_bytes(packet)
            event['accepted_buffer'] = path.name
            self.capture('NEW_CLIENT_TX', event)
            return True
        if api in ('socket', 'WSASocketA', 'WSASocketW') and value != 0xffffffff:
            self.capture('NEW_SOCKET', event)
            return True
        if (api in ('closesocket', 'shutdown') and value == 0) or (api == 'recv' and value == 0):
            self.reason = 'UI_GATE_SESSION_EXPIRED'
            self.capture(self.reason, event)
            return True
        return False

    def capture(self, kind, event):
        self.server.request_hold(False,wait=True)
        atomic_json(self.run/'first-post-gate-event.json', dict(event, classification=kind))
        self.control.events.append(event)
        self.control.transition('POST_GATE_EVENT', time.monotonic())
        self.control.transition('CAPTURE', time.monotonic())
        self.result = {
            'last_accepted_state': 'SERVER_AUTO_SELECTED',
            'ui_action_window': {'gate_ready_monotonic': self.control.wait_started,
                                 'event_utc': datetime.now(timezone.utc).isoformat()},
            'selection_path_hit': [e['event_type'] for e in self.paths],
            'new_client_tx': kind == 'NEW_CLIENT_TX', 'new_socket': kind == 'NEW_SOCKET',
            'new_connect': kind == 'NEW_CONNECT', 'server_selection_confirmed': False,
            'client_alive': bool(self.client and self.client.is_running()),
            'next_blocker': {'NEW_CLIENT_TX':'SERVER_SELECT_C2S_UNKNOWN',
                             'NEW_CONNECT':'SECOND_CONNECTION_HANDOFF'}.get(kind,kind),
        }

    def finish(self, outcome):
        if self.server.process.poll() is None:self.server.request_hold(False,wait=True)
        reason = self.reason or outcome
        self.control.cancel(reason)
        self.active = False
        snapshot = self.control.snapshot()
        snapshot['ui_gate_ready'] = False
        snapshot['client_alive'] = bool(self.client and self.client.is_running())
        snapshot['server_alive'] = self.server.process.poll() is None
        snapshot['observer_alive'] = self.driver.p.poll() is None
        atomic_json(self.run/'ui_gate.json', snapshot)
        atomic_json(self.home/'artifacts/strike/ui_gate.json', snapshot)
        result = self.result or {'last_accepted_state':'SERVER_AUTO_SELECTED' if self.prepared else None,
            'ui_action_window': None, 'selection_path_hit':[e['event_type'] for e in self.paths],
            'new_client_tx':False, 'new_socket':False, 'new_connect':False,
            'server_selection_confirmed':False, 'client_alive':bool(self.client and self.client.is_running()),
            'next_blocker':reason}
        atomic_json(self.run/'ui_gate_result.json', result)
        atomic_json(self.home/'artifacts/strike/ui_gate_result.json', result)
