"""Retained toolbar -> packet-written vitals -> original pre-HUD guarded return.

At this initializer boundary +232E50 is -1. The HUD is constructed later;
this stage cannot certify clamp/display calls that the original guard skips.
"""
import struct
import unittest
import json
import test_current_battle_owner_toolbar as toolbar
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerVitalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = toolbar.CurrentBattleOwnerToolbarTests
        fixture.setUpClass()
        fixture().test_native_resource_controls_and_pending_character_call()
        fixture().test_exact_writes_and_source_retention()
        cls.b, cls.n = b, n = fixture.b, fixture.n
        pending = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                   bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2400)))
        maxima = bytearray(b'\x22' + bytes(24))
        struct.pack_into('<II', maxima, 17, 100, 50)
        current = b'\x2b' + struct.pack('<IIIIHH', 120, 0, 60, 0, 4321, 0)
        b.prepare_character_vitals(bytes(maxima), current)
        cls().assertEqual(pending, (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                                   bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2400))))
        cls.before = {base: bytes(n.vm.mem_read(base, size)) for base, size in (
            (boot.OWNER, boot.OWNER_SIZE), (boot.MOUSE, boot.MOUSE_SIZE),
            (boot.DISPLAY, boot.DISPLAY_STATE_SIZE), (boot.RENDERER, 0x291000),
            (boot.CHARACTER_ROOT, len(b.character_prepared)))}
        cls.calls = b.continue_owner_vitals()
        diagnostic = boot.ROOT / 'artifacts/verification/full-suite-followup-20260927/vitals-observer.json'
        diagnostic.parent.mkdir(parents=True, exist_ok=True)
        diagnostic.write_text(json.dumps({'calls': {hex(k): v for k, v in cls.calls.items()},
            'refresh_index': int.from_bytes(n.vm.mem_read(boot.OWNER + 0x232e50, 2), 'little', signed=True),
            'source_pointer': hex(n.u32(boot.OWNER + 0x86888)),
            'callee_bytes': {hex(rva): bytes(n.vm.mem_read(boot.BASE+rva, 16)).hex()
                for rva in (0xe72d0, 0xac070, 0x1060f0, 0x105680)}} , indent=2), encoding='utf-8')

    def test_original_pre_hud_guard_and_retained_return(self):
        self.assertEqual(self.calls[0xe72d0], 1)
        self.assertEqual(self.calls[0xac070], 1)
        self.assertEqual(int.from_bytes(self.n.vm.mem_read(boot.OWNER + 0x232e50, 2), 'little', signed=True), -1)
        self.assertEqual(self.calls[0xac095], 1)  # Original signed HUD-index guard.
        self.assertEqual(self.calls[0xac09c], 1)
        self.assertEqual(self.calls[0xac2ad], 1)  # Its unchanged early-return target.
        for skipped in (0xac0a2, 0xac0a7, 0xac0af, 0x1060f0, 0x105680):
            self.assertNotIn(skipped, self.calls)
        self.assertEqual(struct.unpack('<4I', self.n.vm.mem_read(boot.CHARACTER_ROOT + 0xec, 16)),
                         (120, 100, 60, 50))
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xb129a)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x7c)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)

    def test_exact_writes_unchanged_sources_and_single_use(self):
        for base, before in self.before.items():
            expected = bytearray(before)
            for _, at, size, value in self.b.owner_vitals_writes:
                if base <= at < base + len(expected):
                    expected[at - base:at - base + size] = value.to_bytes(size, 'little')
            self.assertEqual(bytes(self.n.vm.mem_read(base, len(expected))), bytes(expected))
        self.b.owner_map_metadata._verify_records(bound=True)
        with self.assertRaises(ValueError):
            self.b.continue_owner_vitals()


if __name__ == '__main__':
    unittest.main()
