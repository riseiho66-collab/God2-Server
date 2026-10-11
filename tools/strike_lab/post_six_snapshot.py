"""Local-only POST_6B capture seed, not a complete replayable protocol snapshot."""
import hashlib
import json
import re
from pathlib import Path


WIRE = bytes.fromhex('0600a3a3fdd5')
REGISTERS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp', 'eip', 'efl')


def capture_post_six(driver, run, event, pending, wire):
    """Read only at the matched x86 send return; never resume or mutate client."""
    if not (wire == WIRE and event.get('matched') is True
            and event.get('api') == pending.get('api') == 'send'
            and event.get('pc') == pending.get('ret') == 0x412506
            and event.get('eax') == pending.get('a2') == 6
            and event.get('pid') == pending.get('pid')
            and event.get('tid') == pending.get('tid')
            and isinstance(pending.get('sp'), int)
            and event.get('sp') == pending['sp'] + 20):
        raise ValueError('POST_6B boundary is not a matched exact-fixture send return')
    root = Path(run) / 'protocol-private' / 'post-six'
    root.mkdir(parents=True, exist_ok=False)
    report = dict(format_version=1, kind='POST_6B_CAPTURE_SEED',
                  status='CAPSULE_INCOMPLETE', replay_ready=False,
                  protocol_state_fingerprint=None, next_direction='UNKNOWN',
                  image_base=0x400000,
                  boundary={key: event.get(key) for key in
                            ('pid', 'tid', 'sequence', 'entry', 'pc', 'sp', 'eax')},
                  wire_sha256=hashlib.sha256(wire).hexdigest(),
                  regions=[], errors=[],
                  missing=['dependency closure beyond initial codec/stack/code windows',
                           'dispatcher/session/UI object identity and relevant globals',
                           'canonical pointer relocation and protocol state definition',
                           'three original-code deterministic replays'])
    # Values and opaque memory stay in private lab artifacts, never normal logs.
    try:
        command = '.printf "POST6_REGS ' + ' '.join(
            name + '=%08x' for name in REGISTERS) + '\\n", ' + ', '.join(
            '@' + name for name in REGISTERS)
        raw = driver.command(command)
        lines = [line.strip() for line in raw.splitlines()
                 if line.strip().startswith('POST6_REGS ')]
        if len(lines) != 1:
            raise ValueError('Missing or ambiguous register response')
        pattern = 'POST6_REGS ' + ' '.join(name + r'=([0-9a-fA-F]{8})'
                                         for name in REGISTERS)
        match = re.fullmatch(pattern, lines[0])
        if not match:
            raise ValueError('Malformed register response')
        regs = dict(zip(REGISTERS, (int(value, 16) for value in match.groups())))
        if regs['eip'] != event['pc'] or regs['esp'] != event['sp'] or regs['eax'] != 6:
            raise ValueError('Debugger register context changed at boundary')
        report['registers'] = regs
        # ESI codec is established only for this exact wrapper. Other objects
        # are deliberately not guessed from stack pointers or register values.
        regions = [('codec', regs['esi'], 0x255c),
                   ('stack', regs['esp'], 0x1000),
                   ('send_continuation', 0x412000, 0x1000),
                   ('flush_continuation', 0x413000, 0x1000)]
        for name, address, size in regions:
            item = dict(name=name, address=address, size=size, captured=False)
            report['regions'].append(item)
            if address < 0x10000 or address + size > 0x100000000:
                report['errors'].append(name + ': invalid x86 address range')
                continue
            path = root / (name + '.bin')
            try:
                driver.command(f'.writemem "{path.as_posix()}" {address:x} L{size:x}')
                data = path.read_bytes()
                if len(data) != size:
                    raise ValueError('short memory capture')
                item.update(captured=True, file=path.name,
                            sha256=hashlib.sha256(data).hexdigest())
                if name == 'stack':
                    protocol = int.from_bytes(data[:4], 'little')
                    continuation = int.from_bytes(data[8:12], 'little')
                    if (protocol + 0x758 == regs['esi']
                            and protocol + 0x104 == regs['edi']
                            and continuation == 0x4133b3):
                        report['protocol_root'] = protocol
                        regions.append(('protocol_object', protocol, 0x40d8))
                    else:
                        report['errors'].append('protocol root relationship not confirmed')
            except (OSError, ValueError, RuntimeError) as exc:
                report['errors'].append(name + ': ' + type(exc).__name__)
    except (OSError, ValueError, RuntimeError) as exc:
        report['errors'].append('context: ' + type(exc).__name__)
    target = root / 'capture.json'
    with target.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return {'file': str(target.relative_to(run)), 'status': report['status'],
            'replay_ready': False, 'captured_regions': sum(
                item['captured'] for item in report['regions']),
            'error_count': len(report['errors'])}
