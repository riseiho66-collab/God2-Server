"""Guarded live-client offline-entry experiment, without desktop automation.

Only the existing original-hash, program-firewalled working copy may run.
Transport breakpoints stop before connection/data APIs. No listener or packet
fixture is created. The initial mode stops before the normal login/world call.
"""
import argparse
import ctypes
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import struct
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lab import HOME, CLIENT, PROFILES, profile_context, sha, write_json
from capture import parse_marker
from trace_qualification import native, interactive
from network_driver import NetworkDriver
from pagefile_capacity_compat import CapacityAdapter, memory, number

BASE = 0x400000
IMAGE = HOME / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
TRANSPORT_APIS = ('connect', 'WSAConnect', 'send', 'recv', 'sendto', 'recvfrom',
                  'WSASend', 'WSARecv', 'WSASendTo', 'WSARecvFrom')
STARTUP_CALL = 0x131fe2
WORLD_STAGES = {294: (0xeee0, 'ALTERNATE_WORLD_ENTRY'),
                295: (0x643b0, 'WORLD_CONSTRUCTOR'),
                296: (0x64910, 'WORLD_INITIALIZER'),
                297: (0x68160, 'INITIAL_ACTOR_DISPATCH'),
                298: (0x688d0, 'LOCAL_NULL_INPUT_BRANCH'),
                299: (0x131fe7, 'EXPERIMENT_CALL_RETURN'),
                320: (0x100180, 'SCENE_ENTRY'),
                321: (0x6543a, 'SCENE_RETURN_TO_WORLD_INITIALIZER')}


def install_loop_page(driver, application):
    """One bounded RX thunk in the already guarded child, never a remote thread."""
    from current_offline_entry_bridge import loop_trampoline, pinned_image
    pinned_image()
    code = loop_trampoline(application)
    if application != 0x5e00f8 or not 1 <= len(code) <= 256:
        raise ValueError('Pinned application and bounded thunk required')
    return install_owned_page(driver, lambda address: (code, len(code) - 3))


def install_owned_page(driver, build):
    """Install a bounded immutable lab page in the already verified child."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    pointer, size, dword, boolean = ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_int
    signatures = {
        'OpenProcess': ([dword, boolean, dword], pointer),
        'CloseHandle': ([pointer], boolean),
        'QueryFullProcessImageNameW': ([pointer, dword, ctypes.c_wchar_p, ctypes.POINTER(dword)], boolean),
        'VirtualAllocEx': ([pointer, pointer, size, dword, dword], pointer),
        'VirtualFreeEx': ([pointer, pointer, size, dword], boolean),
        'WriteProcessMemory': ([pointer, pointer, pointer, size, ctypes.POINTER(size)], boolean),
        'VirtualProtectEx': ([pointer, pointer, size, dword, ctypes.POINTER(dword)], boolean),
        'FlushInstructionCache': ([pointer, pointer, size], boolean),
    }
    for name, (arguments, result) in signatures.items():
        getattr(kernel, name).argtypes, getattr(kernel, name).restype = arguments, result
    handle = kernel.OpenProcess(0x438, False, driver.client_pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    allocation, complete = None, False
    try:
        path = ctypes.create_unicode_buffer(32768)
        length = dword(len(path))
        if not kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        if path.value.casefold() != str(CLIENT / 'God2.exe').casefold():
            raise ValueError('Debugger child executable changed')
        allocation = kernel.VirtualAllocEx(handle, None, 4096, 0x3000, 4)
        if not allocation or allocation > 0xfffff000:
            raise ValueError('Could not allocate bounded32-bit trampoline page')
        code, trap = build(allocation)
        if (not isinstance(code, bytes) or not 3 <= len(code) <= 4096 or
                not 0 <= trap <= len(code) - 3 or code[trap:trap + 3] != b'\xcc\x0f\x0b'):
            raise ValueError('Bounded page with explicit INT3/UD2 return required')
        buffer = ctypes.create_string_buffer(code)
        written, previous = size(), dword()
        if not kernel.WriteProcessMemory(handle, allocation, buffer, len(code), ctypes.byref(written)) or written.value != len(code):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.VirtualProtectEx(handle, allocation, 4096, 0x20, ctypes.byref(previous)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.FlushInstructionCache(handle, allocation, len(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        if memory(driver, allocation, len(code)) != code:
            raise ValueError('Installed loop thunk bytes differ')
        complete = True
        return {'address': allocation, 'hex': code.hex(), 'return_trap': allocation + trap,
                'protection': 'PAGE_EXECUTE_READ', 'lifetime': 'Owned child process; released at exit'}
    finally:
        if allocation and not complete:
            kernel.VirtualFreeEx(handle, allocation, 0, 0x8000)
        kernel.CloseHandle(handle)


class OfflineObserver:
    def __init__(self, run, timeout, enter_local_world=False, run_world_loop=False, monster_side=None, probe_phase=False, probe_vitals=False, probe_battle_init=False, probe_battle_loop=False, probe_battle_actors=False, probe_battle_grant=False):
        if sha(IMAGE) != IMAGE_SHA:
            raise ValueError('Current native image identity changed')
        self.image = IMAGE.read_bytes()
        self.run, self.timeout = run, timeout
        self.events = []
        self.capacity = CapacityAdapter(CLIENT, run)
        self.installed = False
        self.enter_local_world = enter_local_world
        self.entry_patch = False
        self.application = None
        self.run_world_loop = run_world_loop
        self.loop_frame_returns = 0
        self.presentation_returns = 0
        self.presentation_calls = 0
        self.monster = None
        self.battle_init = None
        if probe_battle_init:
            from current_offline_battle_init import LiveBattleInitProbe
            self.battle_init = LiveBattleInitProbe(run, probe_vitals, probe_battle_loop, probe_battle_actors, probe_battle_grant)
        if monster_side is not None:
            from current_offline_monster_live import LiveMonsterProbe
            self.monster = LiveMonsterProbe(run, monster_side, probe_phase, probe_vitals)

    def arm(self, driver, result, name):
        driver.deadline = time.monotonic() + self.timeout
        driver.client_pid = number(driver, '@$tpid')
        # There is intentionally no window snapshot, input callback or listener.
        for index, api in enumerate(TRANSPORT_APIS, 300):
            driver.command(f'bu{index} ws2_32!{api}')
        result.update(network_policy='STOP_BEFORE_TRANSPORT_API', desktop_automation=False,
                      client_pid=driver.client_pid, offline_world_entered=False)

    def collect(self, driver, result, name):
        outcome = 'EVENT_LIMIT'
        try:
            library = HOME / 'build-strike-lab/Release/God2Compat.dll'
            if not library.is_file():
                raise ValueError('Existing timer compatibility extension missing')
            driver.command(f'.load "{library.as_posix()}"')
            installation = driver.command('!God2Compat.install')
            if 'GOD2_COMPAT installed' not in installation:
                raise ValueError('Timer compatibility installation refused')
            self.installed = True
            result['timer_compatibility'] = installation
            if memory(driver, BASE + STARTUP_CALL, 5) != self.image[STARTUP_CALL:STARTUP_CALL + 5]:
                raise ValueError('Original startup call bytes differ')
            driver.command(f'bp290 {BASE + STARTUP_CALL:x}')
            for index, api in ((291, 'kernel32!ExitProcess'),
                               (292, 'user32!MessageBoxA'), (293, 'user32!MessageBoxW')):
                driver.command(f'bu{index} {api}')
            for index, address in ((272, 0x40f165), (273, 0x40f16b)):
                driver.command(f'bp{index} {address:x}')
            self.capacity.arm(driver)
            driver.command('sxe av')
            result['armed'] = driver.command('bl')
            for sequence in range(128 if self.monster else 64):
                stop = driver.command('g')
                if driver.interrupted:
                    result['timeout_stop'] = stop
                    result['timeout_stack'] = driver.command('~* k')
                    outcome = 'TIMEOUT'
                    break
                driver.command('.effmach x86')
                raw = driver.command(
                    '.printf "LAB_STOP pid=%x tid=%x pc=%p sp=%p ret=%p '
                    'a0=%p a1=%p a2=%p a3=%p eax=%p time=%I64x\\n", '
                    '@$tpid, @$tid, @eip, @esp, poi(@esp), poi(@esp+4), '
                    'poi(@esp+8), poi(@esp+c), poi(@esp+10), @eax, @$dbgtime')
                event = parse_marker(raw)
                event.update(sequence=sequence, native_stop=stop)
                self.events.append(event)
                found = re.search(r'Breakpoint (\d+) hit', stop)
                index = int(found[1]) if found else None
                if index in range(300, 300 + len(TRANSPORT_APIS)):
                    event['transport_api'] = TRANSPORT_APIS[index - 300]
                    outcome = 'TRANSPORT_ATTEMPT_STOPPED_BEFORE_EXECUTION'
                    break
                if self.capacity.handle(index, event, driver):
                    continue
                if index in (272, 273):
                    continue
                if self.battle_init and self.battle_init.handles(index):
                    init_result = self.battle_init.handle(index, event, driver, result)
                    if init_result:
                        outcome = init_result
                        break
                    continue
                if self.monster and self.monster.handles(index):
                    monster_result = self.monster.handle(index, event, driver, result)
                    if monster_result:
                        outcome = monster_result
                        break
                    continue
                if index in range(345, 353):
                    event['stage'] = {
                        345: 'WORLD_LOOP_ENTRY', 346: 'WORLD_DISPATCH_ENTRY',
                        347: 'WORLD_FRAME_HEAD', 348: 'WORLD_FRAME_RETURN',
                        349: 'PRESENTATION_RETURN', 350: 'WORLD_LOOP_RETURN',
                        351: 'PRESENTATION_COM_CALL', 352: 'PRESENTATION_WRAPPER_CALL'}[index]
                    if index in (345, 346):
                        driver.command(f'bc {index}')
                    elif index == 348:
                        self.loop_frame_returns += 1
                    elif index in (351, 352):
                        self.presentation_calls += 1
                    elif index == 349:
                        self.presentation_returns += 1
                        if min(self.loop_frame_returns, self.presentation_calls, self.presentation_returns) >= 3:
                            outcome = 'THREE_NATIVE_FRAME_PRESENTATION_RETURNS'
                            break
                    elif index == 350:
                        result['world_loop_result'] = event['eax']
                        outcome = 'WORLD_LOOP_RETURNED'
                        break
                    continue
                if index == 290:
                    if event['pc'] != BASE + STARTUP_CALL:
                        raise ValueError('Startup checkpoint PC mismatch')
                    app = number(driver, '@ecx')
                    result['startup_entry'] = {
                        'pc': event['pc'], 'application': app,
                        'application_owner_bytes_hex': memory(driver, app + 0x430, 0x20).hex(),
                        'registers': driver.command('r'), 'stack': driver.command('dd @esp L10'),
                        'next_instructions': driver.command('u @eip L8')}
                    if not self.enter_local_world:
                        outcome = 'BEFORE_LOGIN_WORLD_CALL'
                        break
                    self.application = app
                    result['events_start_sp'] = event['sp']
                    owners = [number(driver, f'poi({app + offset:x})') for offset in (0x434, 0x438)]
                    if (app != 0x5e00f8 or not all(owners) or
                            number(driver, f'poi({app + 0x440:x})') != 0 or
                            number(driver, f'poi({app + 0xa4:x})') != 0 or
                            any(memory(driver, pointer + 0x2cb8, 1) != b'\0' for pointer in owners)):
                        raise ValueError('Fresh application/inactive network owners required')
                    result['offline_prerequisites'] = {'application': app, 'network_owners': owners,
                                                       'connected_flags': [0, 0], 'prior_world': 0}
                    driver.command('bc 290')
                    patch = b'\xe8' + struct.pack('<i', 0xeee0 - STARTUP_CALL - 5)
                    driver.command(f'eb {BASE + STARTUP_CALL:x} ' + patch.hex(' '))
                    self.entry_patch = True
                    if memory(driver, BASE + STARTUP_CALL, 5) != patch:
                        raise ValueError('Experimental entry patch verification failed')
                    result['entry_intervention'] = {
                        'address': BASE + STARTUP_CALL,
                        'original_hex': self.image[STARTUP_CALL:STARTUP_CALL + 5].hex(),
                        'experimental_hex': patch.hex(), 'target': BASE + 0xeee0,
                        'scope': 'Process-local alternate call; NOT an original startup observation',
                        'stack_contract': 'EEE0 returns without popping originalDE80 argument; stop before caller resumes'}
                    for stage_index, (rva, _) in WORLD_STAGES.items():
                        driver.command(f'bp{stage_index} {BASE + rva:x}')
                    continue
                if index in WORLD_STAGES:
                    rva, label = WORLD_STAGES[index]
                    if event['pc'] != BASE + rva:
                        raise ValueError('World-stage breakpoint mismatch')
                    event.update(stage=label, ecx=number(driver, '@ecx'),
                                 stack=driver.command('dd @esp L10'))
                    driver.command(f'bc {index}')
                    if index == 297:
                        event['initializer_first_argument'] = number(driver, 'poi(@esp+4)')
                    if index == 299:
                        world = number(driver, f'poi({self.application + 0x440:x})')
                        result['local_world_return'] = {'world': world, 'eax': event['eax'],
                                                        'esp': event['sp'], 'registers': driver.command('r')}
                        if event['sp'] != result['events_start_sp']:
                            raise ValueError('AlternateRET0 stack differs from expected pending argument')
                        if world:
                            actor = world + 0x1539683c
                            result['local_actor_prefix_hex'] = memory(driver, actor, 0x40).hex()
                            result['world_owner_bindings_hex'] = memory(driver, world + 0xa7e05c4, 0x30).hex()
                            result['game_data_owner'] = number(driver, f'poi({world + 0xaa36480:x})')
                            for filename, pointer, length in (
                                    ('local-actor.bin', actor, 0x4594),
                                    ('gamedata-headers.bin', result['game_data_owner'] + 0xd2a00, 0x500)):
                                path = self.run / filename
                                event.setdefault('memory_files', []).append({
                                    'path': str(path), 'address': pointer, 'length': length,
                                    'debugger_output': driver.command(f'.writemem "{path.as_posix()}" {pointer:x} L{length:x}')})
                                if not path.is_file() or path.stat().st_size != length:
                                    raise ValueError('Runtime memory evidence write incomplete')
                                event['memory_files'][-1]['sha256'] = sha(path)
                            labels = {item.get('stage') for item in self.events}
                            result['native_scene_call_returned'] = {
                                'SCENE_ENTRY', 'SCENE_RETURN_TO_WORLD_INITIALIZER'} <= labels
                        if self.battle_init:
                            if not world or event['eax'] != 1 or not result.get('native_scene_call_returned'):
                                raise ValueError('Native scene prerequisites incomplete')
                            self.battle_init.arm(driver, result, world)
                            continue
                        if self.monster:
                            if not world or event['eax'] != 1 or not result.get('native_scene_call_returned'):
                                raise ValueError('Native local scene prerequisites incomplete')
                            monster_result = self.monster.arm(driver, result, world)
                            if monster_result:
                                outcome = monster_result
                                break
                            continue
                        if not self.run_world_loop:
                            outcome = 'ALTERNATE_WORLD_CALL_RETURNED'
                            break
                        labels = {item.get('stage') for item in self.events}
                        if (not world or event['eax'] != 1 or not result.get('native_scene_call_returned') or
                                not {'WORLD_CONSTRUCTOR', 'WORLD_INITIALIZER', 'INITIAL_ACTOR_DISPATCH',
                                     'LOCAL_NULL_INPUT_BRANCH'} <= labels):
                            raise ValueError('Native local scene prerequisites incomplete')
                        page = install_loop_page(driver, self.application)
                        result['loop_intervention'] = page
                        for loop_index, address in ((345, BASE + 0x655e0), (346, BASE + 0x67860),
                                (347, BASE + 0x6791d), (348, BASE + 0x67a68),
                                (349, BASE + 0x67bca), (350, page['return_trap']),
                                (351, BASE + 0x32a70), (352, BASE + 0x32a85)):
                            driver.command(f'bp{loop_index} {address:x}')
                        driver.command(f'r @eip = {page["address"]:x}')
                        result['loop_intervention']['execution_scope'] = 'Owner thread redirected into explicit lab thunk; no input events'
                        continue
                    continue
                if index in (291, 292, 293):
                    outcome = 'PROCESS_EXIT' if index == 291 else 'DIALOG_BOUNDARY_NO_INTERACTION'
                    result['boundary_stack'] = driver.command('k')
                    break
                result['unexpected_stop'] = stop
                result['unexpected_registers'] = driver.command('r')
                result['unexpected_stack'] = driver.command('k')
                outcome = 'UNEXPECTED_STOP'
                break
        finally:
            if self.entry_patch:
                original = self.image[STARTUP_CALL:STARTUP_CALL + 5]
                driver.command(f'eb {BASE + STARTUP_CALL:x} ' + original.hex(' '))
                result['entry_patch_restored'] = memory(driver, BASE + STARTUP_CALL, 5) == original
                if not result['entry_patch_restored']:
                    raise ValueError('Experimental entry patch restore failed')
            self.capacity.restore(driver)
            if self.installed:
                result['timer_restore'] = driver.command('!God2Compat.restore')
            result.update(result=outcome, events=self.events,
                          transport_calls_executed_by_observer=0,
                          native_frame_returns=self.loop_frame_returns,
                          native_presentation_calls=self.presentation_calls,
                          native_presentation_returns=self.presentation_returns,
                          original_monster_values_recovered=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', default='offline-entry-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))
    parser.add_argument('--timeout', type=int, default=90)
    parser.add_argument('--enter-local-world', action='store_true',
                        help='Experimental in-memory alternate call; stop before caller resumes')
    parser.add_argument('--run-world-loop', action='store_true',
                        help='After native local scene return, run bounded original event-loop frames')
    parser.add_argument('--probe-native-monster', type=int, choices=(0, 1),
                        help='Diagnostic identity-only native constructor probe on side0 or1; no stat packet')
    parser.add_argument('--probe-native-phase', action='store_true',
                        help='After diagnostic constructor, call native phase0 scanner including its OS clock')
    parser.add_argument('--probe-native-vitals', action='store_true',
                        help='After phase probe, invoke original88 receiver with explicit test HP/MP')
    parser.add_argument('--probe-native-battle-init', action='store_true',
                        help='Exclusive original session initializer with zero diagnostic event')
    parser.add_argument('--probe-native-battle-loop', action='store_true',
                        help='Queue diagnostic88 natively and enter original battle loop through first dispatch return')
    parser.add_argument('--probe-native-battle-actors', action='store_true',
                        help='Prepend two diagnostic1C participants before88 in the original queue')
    parser.add_argument('--probe-native-battle-grant', action='store_true',
                        help='After participants and scalar vitals, dispatch diagnostic86/5 first control')
    parser.add_argument('--probe-native-battle-action', action='store_true',
                        help='After grant, diagnostic native basic attack call on disconnected transport')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', args.run_id) or not 15 <= args.timeout <= 180:
        raise ValueError('Bounded run name and15..180 second timeout required')
    if args.run_world_loop and not args.enter_local_world:
        raise ValueError('World loop requires explicit experimental entry')
    if args.probe_native_monster is not None and (not args.enter_local_world or args.run_world_loop):
        raise ValueError('Monster probe requires alternate entry and an exclusive bounded call')
    if args.probe_native_phase and args.probe_native_monster is None:
        raise ValueError('Phase probe requires the explicit diagnostic constructor')
    if args.probe_native_vitals and not (args.probe_native_phase or args.probe_native_battle_init):
        raise ValueError('Vitals probe requires native phase or complete battle initialization')
    if args.probe_native_battle_init and (not args.enter_local_world or args.run_world_loop or args.probe_native_monster is not None):
        raise ValueError('Battle initializer requires exclusive local-world entry')
    if args.probe_native_battle_loop and not (args.probe_native_battle_init and args.probe_native_vitals):
        raise ValueError('Battle loop probe requires explicit initializer and vitals modes')
    if args.probe_native_battle_actors and not args.probe_native_battle_loop:
        raise ValueError('Participant probe requires the native battle loop')
    if args.probe_native_battle_grant and not args.probe_native_battle_actors:
        raise ValueError('Grant probe requires diagnostic participants')
    if args.probe_native_battle_action and not args.probe_native_battle_grant:
        raise ValueError('Action probe requires completed native grant')
    run = HOME / 'artifacts/runs' / args.run_id
    run.mkdir(parents=True, exist_ok=False)
    original_hash = sha(CLIENT / 'God2.exe')
    observer = OfflineObserver(run, args.timeout, args.enter_local_world, args.run_world_loop,
                               args.probe_native_monster, args.probe_native_phase, args.probe_native_vitals,
                               args.probe_native_battle_init, args.probe_native_battle_loop, args.probe_native_battle_actors,
                               args.probe_native_battle_grant)
    if args.probe_native_battle_action:
        observer.battle_init.vitals.action_enabled = True
    native.NativeDriver = NetworkDriver
    native.OUT = interactive.OUT = run
    with (run / 'stdout.log').open('x') as out, (run / 'stderr.log').open('x') as err:
        with redirect_stdout(out), redirect_stderr(err):
            with profile_context(PROFILES[2], CLIENT, run):
                native.run(args.run_id, lab=observer)
    result = json.loads((run / f'{args.run_id}-result.json').read_text())
    if sha(CLIENT / 'God2.exe') != original_hash:
        raise AssertionError('Working-copy executable disk bytes changed')
    result.update(report=str(run / 'offline-result.json'), executable_disk_unchanged=True,
                  source_hashes={str(path.relative_to(HOME)): sha(path) for path in
                                 (Path(__file__), Path(native.__file__),
                                  HERE / 'pagefile_capacity_compat.py',
                                  HERE / 'current_offline_entry_bridge.py',
                                  HERE / 'current_offline_monster_live.py',
                                  HERE / 'current_offline_vitals_live.py',
                                  HERE / 'current_offline_battle_init.py')})
    write_json(run / 'offline-result.json', result)
    print(json.dumps({key: result.get(key) for key in
                      ('result', 'report', 'client_pid', 'offline_world_entered', 'error')}))
    return 0 if result['result'] in ('BEFORE_LOGIN_WORLD_CALL', 'ALTERNATE_WORLD_CALL_RETURNED',
                                   'THREE_NATIVE_FRAME_PRESENTATION_RETURNS', 'WORLD_LOOP_RETURNED',
                                   'NATIVE_MONSTER_CONSTRUCTOR_RETURNED', 'NATIVE_PHASE_CLOCK_RETURNED',
                                   'NATIVE_VITALS_RECEIVER_RETURNED', 'NATIVE_BATTLE_INITIALIZER_RETURNED',
                                   'NATIVE_BATTLE_DISPATCH_RETURNED', 'NATIVE_DISCONNECTED_ACTION_RETURNED') else 1


if __name__ == '__main__':
    raise SystemExit(main())
