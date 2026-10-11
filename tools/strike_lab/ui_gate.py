"""Fail-closed rendezvous control plane. No UI input or protocol operations."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import tempfile
import time


REQUIRED_TRUE = (
    'client_alive', 'server_alive', 'socket_alive', 'observer_alive',
    'login', 'server_list_ready', 'no_regression', 'network_observers_armed',
    'ui_path_observers_armed', 'client_running', 'run_owned', 'unbounded_capable',
    'server_session_hold_active',
)
ORDER = ('BOOT', 'REPLAY_GOLDEN_PREFIX', 'SERVER_AUTO_SELECTED',
         'ARM_POST_GATE_OBSERVERS', 'UI_GATE_READY', 'WAIT_EXTERNAL_UI',
         'POST_GATE_EVENT', 'CAPTURE', 'CLEANUP')
UNAVAILABLE = ()


def readiness(health):
    missing = [key for key in REQUIRED_TRUE if health.get(key) is not True]
    for key, expected in (('server_count', 1), ('selected_entry_id', 0)):
        if type(health.get(key)) is not int or health[key] != expected:
            missing.append(key)
    if type(health.get('pid')) is not int or health['pid'] <= 0:
        missing.append('pid')
    return missing


def atomic_json(path, value):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.flush()
        # Windows readers can briefly deny delete-sharing during an atomic replace.
        for attempt in range(10):
            try:
                temporary.replace(path)
                break
            except PermissionError as error:
                if getattr(error, 'winerror', None) not in (5, 32) or attempt == 9:
                    raise
                time.sleep(0.01)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class Rendezvous:
    """Pure orchestration; health must come from a run-owned live adapter."""
    def __init__(self, run_id, max_wait=None):
        if max_wait is not None and (not math.isfinite(max_wait) or max_wait <= 0):
            raise ValueError('max wait must be finite and positive')
        self.run_id = run_id
        self.max_wait = max_wait
        self.state = 'BOOT'
        self.health = {}
        self.wait_started = None
        self.termination_reason = None
        self.events = []
        self.owned_processes = []

    def transition(self, target, now):
        if self.state == 'CLEANUP' or ORDER.index(target) != ORDER.index(self.state) + 1:
            raise ValueError('Illegal rendezvous transition')
        if target in ('UI_GATE_READY', 'WAIT_EXTERNAL_UI') and readiness(self.health):
            raise ValueError('Gate prerequisites missing')
        if target == 'POST_GATE_EVENT' and not self.events:
            raise ValueError('Runtime event required')
        self.state = target
        if target == 'WAIT_EXTERNAL_UI':
            self.wait_started = now

    def refresh(self, health, now):
        self.health = dict(health)
        if self.state in ('UI_GATE_READY', 'WAIT_EXTERNAL_UI'):
            failures = (('client_alive', 'CLIENT_EXIT'), ('server_alive', 'SERVER_EXIT'),
                        ('socket_alive', 'UI_GATE_SESSION_EXPIRED'),
                        ('observer_alive', 'FATAL_OBSERVER_FAILURE'))
            for key, reason in failures:
                if self.health.get(key) is not True:
                    self.cancel(reason)
                    return
            if readiness(self.health):
                self.cancel('GATE_PREREQUISITE_LOST')
                return
            if (self.state == 'WAIT_EXTERNAL_UI' and self.max_wait is not None
                    and now - self.wait_started >= self.max_wait):
                self.cancel('OPERATOR_MAX_WAIT')

    def observe(self, event, now):
        if self.state != 'WAIT_EXTERNAL_UI':
            return False
        if (event.get('run_id') != self.run_id or event.get('pid') != self.health.get('pid')
                or event.get('runtime_verified') is not True):
            return False
        kind = event.get('kind')
        if kind not in ('UI_PATH_A_HIT', 'UI_PATH_B_HIT', 'NEW_CLIENT_TX',
                        'NEW_SOCKET', 'NEW_CONNECT', 'CHARACTER_PHASE_REACHED',
                        'SERVER_SELECTION_CONFIRMED', 'CLIENT_EXIT'):
            return False
        self.events.append(dict(event, observed_monotonic=now))
        # A callback hit alone does not complete the wait or certify selection.
        if kind not in ('UI_PATH_A_HIT', 'UI_PATH_B_HIT'):
            self.transition('POST_GATE_EVENT', now)
        return True

    def snapshot(self):
        return dict(self.health, run_id=self.run_id, state=self.state,
                    ui_gate_ready=self.state in ('UI_GATE_READY', 'WAIT_EXTERNAL_UI')
                    and not readiness(self.health),
                    runner_heartbeat_utc=datetime.now(timezone.utc).isoformat(),
                    termination_reason=self.termination_reason)

    def cancel(self, reason='OPERATOR_CANCEL'):
        self.termination_reason = reason
        self.state = 'CLEANUP'

    def cleanup_owned(self):
        # Only retained process objects from this run, never names or global PID scans.
        errors = []
        for process in self.owned_processes:
            try:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=5)
            except Exception as error:
                errors.append(repr(error))
        return errors


def preflight(home, client):
    """Read-only qualification, plus a temporary output-writability probe."""
    home, client = Path(home), Path(client)
    failures = list(UNAVAILABLE)
    checks = {}
    for label, path in (
        ('server_executable', home/'build/Release/god2-server.exe'),
        ('runner_executable', home/'build-strike-lab/Release/god2-strike-runner.exe'),
        ('client_working_copy', client/'God2.exe'),
        ('server_config', home/'config/recovered-server-list.json'),
    ):
        checks[label] = path.is_file()
    import lab  # Establish the existing research module search path.
    from trace_qualification.native import CDB
    checks['observer_executable'] = CDB.is_file()
    checks['long_lived_adapter'] = (home/'tools/strike_lab/ui_gate_live.py').is_file()
    golden = home/'artifacts/golden/server-list/server-list-one-01'
    checks['golden_prefix'] = all((golden/name).is_file() for name in (
        'S2C_0001.bin', 'C2S_0001.bin', 'S2C_0002.bin', 'C2S_0002.bin',
        'S2C_0003.bin', 'S2C_SERVER_LIST_0001.bin', 'S2C_0004.bin'))
    try:
        checks['client_identity'] = hashlib.sha256((client/'God2.exe').read_bytes()).hexdigest() == (
            'fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1')
    except OSError:
        checks['client_identity'] = False
    try:
        state = json.loads((home/'artifacts/strike/state.json').read_text(encoding='utf-8'))
        checks['state_consistency'] = (
            state['last_accepted_state'] == 'SERVER_AUTO_SELECTED'
            and state['baseline'] == {'LOGIN': True, 'SERVER_LIST_READY': True,
                                      'SERVER_COUNT': 1, 'SELECTED_ENTRY_ID': 0}
            and state['observations']['SERVER_SELECTION_CONFIRMED'] is False
            and bool(state['evidence'])
            and all(hashlib.sha256((home/e['path']).read_bytes()).hexdigest() == e['sha256']
                    for e in state['evidence']))
    except (OSError, ValueError, KeyError, TypeError):
        checks['state_consistency'] = False
    try:
        config = json.loads((home/'config/recovered-server-list.json').read_text())
        checks['loopback_config'] = config['server']['host'] == '127.0.0.1'
    except (OSError, ValueError, KeyError, TypeError):
        checks['loopback_config'] = False
    try:
        with tempfile.TemporaryFile(dir=home/'artifacts/strike'):
            checks['output_writable'] = True
    except OSError:
        checks['output_writable'] = False
    failures.extend(key for key, valid in checks.items() if not valid)
    return {'ui_gate_ready': False, 'rendezvous_complete': False,
            'client_launched': False, 'checks': checks, 'blockers': failures}
