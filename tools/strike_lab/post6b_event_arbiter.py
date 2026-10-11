"""First-event latch for a serialized, globally sequenced observer stream.

The producer must classify/qualify events and deliver them in native order.
This module does not infer blocking waits, API success, or capture completeness.
"""
from copy import deepcopy
from threading import Lock


class Post6BEventArbiter:
    DIRECTIONS = {
        'CLIENT_TX': 'CLIENT_FIRST',
        'RX_WAIT': 'SERVER_FIRST',
        'CONNECTION_TRANSITION': 'CONNECTION_TRANSITION',
        'LOCAL_PROTOCOL_TRANSITION': 'LOCAL_STATE_TRANSITION',
        'CLIENT_EXIT': 'UNKNOWN',
    }

    def __init__(self, t0, persist):
        for key in ('sequence', 'pid', 'tid'):
            if type(t0.get(key)) is not int or t0[key] < 0:
                raise ValueError('Invalid T0 identity/sequence')
        self.t0 = deepcopy(t0)
        self._last = t0['sequence']
        self._persist = persist
        self._first = None
        self._lock = Lock()

    @property
    def first(self):
        with self._lock:
            return deepcopy(self._first)

    def consume(self, event):
        with self._lock:
            sequence = event.get('sequence')
            if type(sequence) is not int:
                raise ValueError('Global sequence required')
            if sequence <= self.t0['sequence']:
                return None
            if event.get('pid') != self.t0['pid']:
                raise ValueError('Process transition: PID differs from T0')
            if type(event.get('tid')) is not int or event['tid'] < 0:
                raise ValueError('Event TID required')
            if sequence <= self._last:
                raise ValueError('Native stream is duplicated or out of order')
            if self._first is not None:
                self._last = sequence
                return deepcopy(self._first)
            kind = event.get('event_class')
            if kind not in self.DIRECTIONS:
                self._last = sequence
                return None
            # Unknown relevant events block proof; never skip to a later winner.
            if event.get('qualified') is not True:
                raise ValueError('Relevant event is not qualified')
            if kind == 'LOCAL_PROTOCOL_TRANSITION' and not event.get('state_evidence'):
                raise ValueError('Certified state evidence required')
            result = {
                't0_sequence': self.t0['sequence'], 't0_tid': self.t0['tid'],
                'client_pid': self.t0['pid'], 'first_event_sequence': sequence,
                'first_event_tid': event['tid'], 'event_class': kind,
                'api': event.get('api'), 'rva': event.get('caller_rva'),
                'timestamp': event.get('timestamp'),
                'direction': self.DIRECTIONS[kind], 'event': deepcopy(event),
                'qualification': 'Producer-qualified event; coverage certification is separate',
            }
            # Persistence failure propagates; caller must not clean up as success.
            self._persist(deepcopy(result))
            self._first = result
            self._last = sequence
            return deepcopy(result)
