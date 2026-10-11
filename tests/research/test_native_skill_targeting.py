"""Unchanged x86 target selection versus the formal C++ rule implementation."""
from pathlib import Path
import random
import struct
import subprocess

import test_current_skill_target_setup as native
from tools.strike_lab import current_skill_target_setup as model


class FormalTargetingTests(native.CurrentSkillTargetSetupTests):
    def test_formal_cpp_against_original_helper(self):
        root = Path(__file__).resolve().parents[2]
        executable = root / 'build/tests/Release/native-skill-targeting.exe'
        self.assertTrue(executable.is_file(), 'Build the formal native-skill-targeting target first')
        vm = self.target_machine()
        cases = []
        for mode in range(256):
            for actor in (0, 4, 9, 13):
                for reach in (0, 7, 255):
                    cases.append((model.Fields(1, 0, 0, reach, mode), actor,
                                  self.state((0x80003fff, 0x40000000))))
        for definition in native.native.identity.decode_definitions(self.source).values():
            for actor in (0, 13):
                cases.append((model.Fields.from_record(definition.raw), actor, self.state()))
        rng = random.Random(913)
        for _ in range(512):
            fields = model.Fields(rng.randrange(7, 12), 3, 0, rng.randrange(256), rng.randrange(18))
            words = tuple(rng.choice((None, -32768, -1, 0, 32767)) for _ in range(28))
            cases.append((fields, rng.randrange(14), self.state((rng.getrandbits(32), rng.getrandbits(32)), words)))
        lines, expected = [], []
        for fields, actor, state in cases:
            self.compare_masks(vm, fields, actor, state)
            masks = struct.unpack('<2I', vm.mem_read(native.OUTPUT, 8))
            saved_mode = struct.unpack('<3I', vm.mem_read(native.CONTEXT + 0x2fc, 12))
            if 1 <= fields.mode_45 <= 17:
                value = self.target_invoke(vm, 0x11ead0, (fields.mode_45, native.FLAG),
                    writes=((native.FLAG, native.FLAG + 4),))
                flag = struct.unpack('<I', vm.mem_read(native.FLAG, 4))[0]
            else:
                value, flag = -1, -1
            expected.append((*masks, *saved_mode, value, flag, int(fields.passes_kind_gate)))
            values = (fields.identifier, fields.kind, fields.word_3e, fields.reach_44,
                      fields.mode_45, actor, *state.masks, *state.saved_masks,
                      *(32768 if word is None else word for word in state.entity_words))
            lines.append(' '.join(map(str, values)))
        result = subprocess.run([str(executable), '--batch'], input='\n'.join(lines) + '\n',
                                capture_output=True, text=True, timeout=30, check=True)
        actual = [tuple(map(int, line.split())) for line in result.stdout.splitlines()]
        self.assertEqual(len(actual), len(expected))
        for index, (observed, wanted) in enumerate(zip(actual, expected)):
            self.assertEqual(observed, wanted, cases[index])


if __name__ == '__main__':
    import unittest
    unittest.main()
