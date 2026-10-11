"""Continue once past the frozen six-byte send; never synthesize responses."""
import time
import re
from ui_gate import atomic_json
from ui_gate_live import LongLivedRunContext
from post6b_native_events import NativePost6BEvents, matched_pair


class PostServerSelectObserver(LongLivedRunContext):
    boundary = None
    preserve_select_coverage = True

    def network_entry(self, event, driver):
        if self.boundary is None:
            return False
        if (event.get('api') == 'select' and event.get('a1')
                and event.get('a2') == 0 and event.get('a3') == 0):
            raw = driver.command('.printf "POST6B_SELECT count=%x timeout=%x\\n", '
                                 f'dwo({event["a1"]:x}), poi(@esp+14)')
            match = re.search(r'POST6B_SELECT count=([0-9a-fA-F]+) timeout=([0-9a-fA-F]+)', raw)
            if not match:
                raise ValueError('Select arguments unavailable; wait classification blocked')
            count, timeout = (int(value, 16) for value in match.groups())
            evidence = dict(source='NATIVE_SELECT_ARGUMENTS', raw=raw,
                            read_count=count, infinite=timeout == 0)
            if timeout:
                raw = driver.command('.printf "POST6B_TIMEOUT sec=%x usec=%x\\n", '
                                     f'dwo({timeout:x}), dwo({timeout+4:x})')
                match = re.search(r'POST6B_TIMEOUT sec=([0-9a-fA-F]+) usec=([0-9a-fA-F]+)', raw)
                if not match:
                    raise ValueError('Select timeout unavailable; wait classification blocked')
                evidence.update(seconds=int(match[1],16), microseconds=int(match[2],16), timeout_raw=raw)
            event['select_wait_evidence'] = evidence
        winner = self.post6b_events.consume(event)
        if winner:
            self.capture(winner['event_class'], event)
        return winner is not None

    def tick(self):
        if self.boundary is None:
            return super().tick()
        if (self.run/'cancel.request').exists():
            self.reason='OPERATOR_CANCEL';self.driver.deadline=time.monotonic()
        elif self.server.process.poll() is not None:
            self.reason='SERVER_EXIT';self.driver.deadline=time.monotonic()

    def network_return(self,event,pending,driver):
        if self.boundary is None:
            if event['api']=='send' and event['eax']==6 and (
                    event.get('matched') is not True or pending.get('a2')!=6 or
                    event.get('entry')!=pending.get('sequence') or
                    not pending.get('buffer_file')):
                return False
            if (event['api']=='send' and event.get('matched') is True and
                    event['eax']==6 and pending.get('a2')==6 and
                    event.get('entry')==pending.get('sequence') and
                    pending.get('buffer_file')):
                if not matched_pair(event, pending):
                    raise ValueError('T0 requires exact same-PID/TID native pair')
                packet=(self.run/pending['buffer_file']).read_bytes()[:6]
                golden=(self.home/'artifacts/golden/server-select/C2S_0001.bin').read_bytes()
                if packet!=golden:raise RuntimeError('Post-selection fixture regression')
                self.post6b_events = NativePost6BEvents(event,
                    lambda result: atomic_json(self.run/'post6b-first-event.json', result),
                    self.run.name, getattr(self, 'action_candidate', None),
                    getattr(self, 'action_result', None))
                from post_six_snapshot import capture_post_six
                event['protocol_capture_seed'] = capture_post_six(
                    driver, self.run, event, pending, packet)
                self.server.request_hold(False,wait=True)
                path=self.run/'C2S_AFTER_SERVER_SELECT_0001.bin';path.write_bytes(packet)
                event['accepted_buffer']=path.name
                self.boundary=dict(event)
                atomic_json(self.run/'post-six-boundary.json',dict(event,
                    registers=driver.command('r'),stack=driver.command('dd @esp L10')))
                from apex import APIS
                driver.command(f'bu{100+APIS.index("select")} ws2_32!select')
                # Only observation after the known send is bounded, never the UI wait.
                driver.deadline=time.monotonic()+30
                snapshot=self.control.snapshot()
                snapshot.update(state='POST_C2S_OBSERVATION',ui_gate_ready=False,
                                server_session_hold_active=False)
                atomic_json(self.run/'ui_gate.json',snapshot)
                atomic_json(self.home/'artifacts/strike/ui_gate.json',snapshot)
                return False
            return super().network_return(event,pending,driver)
        # Persist accepted bytes before the arbiter's write-ahead winner record.
        if event.get('api') == 'send' and matched_pair(event, pending) and 0 < event.get('eax', 0) < 0x80000000:
            source = pending.get('buffer_file')
            if not source or event['eax'] > pending.get('a2', 0):
                raise ValueError('Accepted send bytes unavailable')
            packet = (self.run/source).read_bytes()
            if len(packet) < event['eax']:
                raise ValueError('Accepted send capture truncated')
            path = self.run/'C2S_AFTER_6B_NEXT.bin'
            path.write_bytes(packet[:event['eax']])
            event['accepted_buffer'] = path.name
        winner = self.post6b_events.consume(event, pending)
        if winner:
            self.capture(winner['event_class'], event)
            return True
        api=event['api'];value=event['eax']
        if api=='recv':
            kind='RX_BYTES' if 0<value<0x80000000 else 'CLIENT_RX_EOF' if value==0 else 'CLIENT_RX_ERROR'
            if 0<value<=min(pending['a2'],4096):
                path=self.run/'s2c'/f'post-six-{event["sequence"]}.bin'
                event['capture']=driver.command(f'.writemem "{path.as_posix()}" {pending["a1"]:x} L{value:x}')
        elif api=='select':
            kind='RX_POLL' if pending['a1'] else 'SELECT_RETURN'
            self.poll_samples = getattr(self, 'poll_samples', 0) + 1
            if self.poll_samples <= 8:
                atomic_json(self.run/f'post-six-poll-{self.poll_samples}.json',
                            dict(event, classification=kind, next_direction='UNKNOWN'))
            # A nonblocking select result is not the next protocol edge.
            # Limit duplicate artifacts, not breakpoint coverage.
            return False
        elif api=='send':
            kind='NEW_CLIENT_TX' if 0<value<0x80000000 else 'CLIENT_TX_ERROR'
            if kind=='NEW_CLIENT_TX' and pending.get('buffer_file'):
                path=self.run/'C2S_AFTER_6B_NEXT.bin'
                path.write_bytes((self.run/pending['buffer_file']).read_bytes()[:value])
                event['accepted_buffer']=path.name
        elif api in ('socket','WSASocketA','WSASocketW'):
            kind='NEW_SOCKET' if value!=0xffffffff else 'SOCKET_ERROR'
        else:kind=api.upper()+'_RETURN'
        atomic_json(self.run/'post-six-next-event.json',dict(event,classification=kind,
                    qualification='Actual API return; RX_POLL does not assert a blocking wait or a packet handler'))
        self.capture(kind,event)
        return False
