"""CUSTOM-0058 native display-name resolver regression; no live mutation."""
import json
import struct

from .build_shunying_client import (CLIENT, OUTPUT, DISPLAY_ITEMS, DISPLAY_ITEMS_GB,
                                    make_display_items, decode_csvz, sha)
from tools.strike_lab.current_item_metadata import NativeItemMetadata, growth


def resolve(n, skill_id):
    """Execute 004A8E10/459A60/strncmp; adapt only CRT sprintf."""
    vm, x = n.vm, n.x86
    def sprintf(vm, address, size, context):
        sp = vm.reg_read(x.UC_X86_REG_ESP)
        ret, dest, fmt, value = struct.unpack('<4I', vm.mem_read(sp, 16))
        assert ret == 0x4a8eb4
        template = bytes(vm.mem_read(fmt, 16)).split(b'\0')[0]
        assert template in (b'SpcA%3d', b'SpcA%02d')
        text = template % value
        vm.mem_write(dest, text + b'\0')
        vm.reg_write(x.UC_X86_REG_EAX, len(text))
        vm.reg_write(x.UC_X86_REG_ESP, sp + 4)
        vm.reg_write(x.UC_X86_REG_EIP, ret)
    hook = vm.hook_add(n.uc.UC_HOOK_CODE, sprintf, begin=0x547af7, end=0x547af7)
    try:
        vm.mem_write(n.OUTPUT, b'\xff\xff')
        vm.mem_write(n.SP, struct.pack('<4I', n.RETURN, 0, skill_id, n.OUTPUT))
        n.reg('ESP', n.SP)
        n.reg('ECX', n.OWNER)
        n.reg('EFLAGS', 2)
        vm.emu_start(0x4a8e10, n.RETURN, count=50000, timeout=1000000)
        assert vm.reg_read(x.UC_X86_REG_EIP) == n.RETURN
        assert vm.reg_read(x.UC_X86_REG_ESP) == n.SP + 16
        return vm.reg_read(x.UC_X86_REG_EAX), struct.unpack('<H', vm.mem_read(n.OUTPUT, 2))[0]
    finally:
        vm.hook_del(hook)


def verify():
    reports = []
    for relative, simplified in ((DISPLAY_ITEMS, False), (DISPLAY_ITEMS_GB, True)):
        encoded, info = make_display_items((CLIENT / relative).read_bytes(), simplified=simplified)
        n = NativeItemMetadata()
        original = n.item_row('SKB', 7, retain=True)
        assert original['key'] == 6508
        assert resolve(n, 8) == (n.RECORD + 16, 6508)
        # No alias row: native leaves the output ID untouched, explaining the
        # caller's uninitialized metadata/text usage; cbspec2 cannot fix this.
        assert resolve(n, 126) == (0, 65535)
        n.vm.mem_write(n.TABLE + 0xb2d40 + 6508 * 4, bytes(4))
        n.retained_key = None
        sections = growth.parse_sections(decode_csvz(encoded), ('SKB',))
        n.sections['SKB'] = sections['SKB']
        assert len(n.sections['SKB']['records']) == 382
        loaded = n.item_row('SKB', 381, retain=True)
        record = loaded['record']
        assert loaded['key'] == 6897 and loaded['group'] == 5
        assert struct.unpack_from('<H', record, 0x114)[0] == 21126
        assert record[0x11c:].split(b'\0')[0] == b'SpcA126'
        assert record[8:].split(b'\0')[0].hex() == info['name_hex']
        assert resolve(n, 126) == (n.RECORD + 16, 6897)
        # Only our new alias resolves; adjacent reserved skill remains missing.
        assert resolve(n, 125) == (0, 65535)
        destination = OUTPUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encoded)
        reports.append(dict(path=relative, sha256=sha(encoded), **info,
                            native_parser=True, native_resolver=True,
                            missing_alias_reproduced=True))
    report = dict(design='CUSTOM-0058', scope='native parser/resolver; graphical acceptance pending',
                  files=reports, visual_assets_changed=False)
    (OUTPUT / 'display-name-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    # Keep the candidate handoff complete without rebuilding frozen visuals.
    manifest_path = OUTPUT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for entry in reports:
        relative = entry['path']
        manifest['source_sha256'][relative] = sha((CLIENT / relative).read_bytes())
        manifest['output_sha256'][relative] = entry['sha256']
        manifest.setdefault('display_metadata', {})[relative] = entry
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
