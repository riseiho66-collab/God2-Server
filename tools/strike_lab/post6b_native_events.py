"""Conservative adapter for producer-ordered native stops, not coverage proof."""
from copy import deepcopy
import math

from post6b_event_arbiter import Post6BEventArbiter


def native_identity(event):
    result = deepcopy(event)
    sequence = event.get('global_sequence')
    if type(sequence) is not int or sequence < 0 or sequence != event.get('sequence'):
        raise ValueError('Producer global sequence required')
    for key in ('pid', 'tid'):
        if type(event.get(key)) is not int or event[key] < 0:
            raise ValueError('Native PID/TID required')
    if type(event.get('native_timestamp')) is not int:
        raise ValueError('Native timestamp required')
    result.update(sequence=sequence, event_class='UNCLASSIFIED', qualified=False)
    return result


def matched_pair(event, pending):
    return (pending is not None and event.get('event_type') == 'API_RETURN'
            and pending.get('event_type') == 'API_ENTRY'
            and event.get('matched') is True
            and event.get('api') == pending.get('api')
            and event.get('entry') == pending.get('sequence')
            and event.get('pid') == pending.get('pid')
            and event.get('tid') == pending.get('tid'))


def normalize(event, pending=None):
    result = native_identity(event)
    api = event.get('api')
    if event.get('event_type') == 'API_ENTRY' and api == 'select':
        evidence = event.get('select_wait_evidence', {})
        if (evidence.get('source') == 'NATIVE_SELECT_ARGUMENTS'
                and event.get('a2') == 0 and event.get('a3') == 0):
            count = evidence.get('read_count')
            seconds, micros = evidence.get('seconds'), evidence.get('microseconds')
            timed = (type(seconds) is int and type(micros) is int
                     and 0 <= seconds < 0x80000000 and 0 <= micros < 1000000
                     and (seconds > 0 or micros > 0))
            if type(count) is int and 0 < count <= 64 and (evidence.get('infinite') is True or timed):
                result.update(event_class='RX_WAIT', qualified=True)
    elif event.get('event_type') == 'API_ENTRY' and api in ('connect', 'WSAConnect'):
        if event.get('destination'):
            result.update(event_class='CONNECTION_TRANSITION', qualified=True,
                          transition='CONNECT_ATTEMPT')
    elif event.get('event_type') == 'API_RETURN':
        value = event.get('eax')
        if not matched_pair(event, pending):
            raise ValueError('Exact native entry/return pair required')
        if type(value) is not int:
            raise ValueError('Native return value required')
        if api == 'send' and 0 < value < 0x80000000:
            if type(pending.get('a2')) is not int or value > pending['a2']:
                raise ValueError('Send return exceeds captured request')
            result.update(event_class='CLIENT_TX', qualified=True)
        elif ((api in ('socket', 'WSASocketA', 'WSASocketW') and 0 <= value < 0xffffffff)
              or (api in ('connect', 'WSAConnect', 'closesocket', 'shutdown') and value == 0)
              or (api == 'recv' and value == 0 and pending.get('a2', 0) > 0)):
            result.update(event_class='CONNECTION_TRANSITION', qualified=True)
    # No currently certified local-state or process-exit producer is installed.
    if event.get('event_class') in ('LOCAL_PROTOCOL_TRANSITION', 'CLIENT_EXIT'):
        raise ValueError('No certified native source for this event class')
    return result


class NativePost6BEvents:
    def __init__(self, t0, persist, run_id, action_candidate=None, action_result=None):
        self.t0 = native_identity(t0)
        self.persist = persist
        self.run_id = run_id
        self.action_candidate = action_candidate
        self.action_result = action_result
        self.arbiter = Post6BEventArbiter(self.t0, self._persist)

    def _persist(self, result):
        event = result['event']
        start, end = self.t0.get('timestamp'), event.get('timestamp')
        elapsed = ((end - start) * 1000 if all(type(v) in (int, float)
                   and math.isfinite(v) for v in (start, end)) and end >= start else None)
        observed_direction = result['direction']
        result.update(run_id=self.run_id, action_candidate=self.action_candidate,
                      action_result=self.action_result, first_event_type=result['event_class'],
                      first_event_api_or_rva=result['api'] or result['rva'],
                      elapsed_from_t0_ms=elapsed, elapsed_clock='HOST_OBSERVER',
                      observed_candidate_direction=observed_direction,
                      direction='UNKNOWN', next_direction='UNKNOWN', capture_complete=False,
                      coverage_limitations=['WSASend/WSARecv completion unsupported',
                          'recv blocking mode unverified', 'return breakpoints not thread-scoped',
                          'no certified local-state or process-exit source'])
        self.persist(result)

    def consume(self, event, pending=None):
        identity = native_identity(event)
        if identity['sequence'] <= self.t0['sequence']:
            return None
        if identity['pid'] != self.t0['pid']:
            raise ValueError('PROCESS_TRANSITION: PID differs from T0')
        return self.arbiter.consume(normalize(event, pending))
