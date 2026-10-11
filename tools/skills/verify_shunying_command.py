"""CUSTOM-0058: original x86 builder oracle for candidate one/two/three targets.

Run python -B -m tools.skills.verify_shunying_command after building the candidate.
Targets and count are explicit fixture input. This does not exercise mouse UI,
manual confirmation, native clones, animation or authoritative server balance.
"""
import hashlib
import json
import sys
import struct

from unicorn import UC_HOOK_CODE

from .build_shunying_client import ROOT, OUTPUT, CATALOG, decode_definitions

sys.path.insert(0, str(ROOT / "tests/research"))
from test_current_skill_command import CurrentSkillCommandTests
import test_current_battle_command as command_native
import test_current_skill_target_setup as setup_native
from test_current_skill_target_setup import CurrentSkillTargetSetupTests
from tools.strike_lab import current_skill_target_setup as targeting


class NativeSetupCommandTest(CurrentSkillCommandTests):
    """Feed the actual 11EAD0 outputs into the original command builder.

    The old fixture left B+468 zero even though catalog mode3 produces one.
    That bypassed the real combined-mask branch and hid a live parser rejection.
    """
    def vm(self):
        vm = super().vm()
        def install_setup(machine, address, width, data):
            if address == command_native.BASE + 0x118e50:
                count, combined = self.native_setup
                machine.mem_write(command_native.BATTLE + 0x45c, struct.pack('<I', count))
                machine.mem_write(command_native.BATTLE + 0x468, struct.pack('<I', combined))
        vm.hook_add(UC_HOOK_CODE, install_setup)
        return vm


def original_setup(setup, vm, mode):
    value = setup.target_invoke(vm, 0x11ead0, (mode, setup_native.FLAG),
        writes=((setup_native.FLAG, setup_native.FLAG + 4),))
    flag = struct.unpack('<I', vm.mem_read(setup_native.FLAG, 4))[0]
    assert (value, flag) == targeting.setup_parameters(mode)
    return value, flag


def main():
    raw_catalog = (OUTPUT / CATALOG).read_bytes()
    definition = decode_definitions(raw_catalog)[0, 126].raw
    CurrentSkillCommandTests.setUpClass()
    test = NativeSetupCommandTest()
    test.native_definition = definition
    rows = []
    target_rows = []
    try:
        # Execute the unchanged native target helper for all caster slots and
        # full/sparse enemy masks, with each occupancy pattern supplied explicitly.
        setup = CurrentSkillTargetSetupTests()
        setup.image = test.image
        fields = targeting.Fields.from_record(definition)
        assert (fields.reach_44, fields.mode_45) == (7, 16)
        vm = setup.target_machine()
        for actor in range(14):
            for enemy_mask in (0x3fff, 1, 0x2000, 0x2201, 0x480):
                state = targeting.TargetState((1 << actor, enemy_mask), (0, 0), (None,) * 28)
                result = setup.compare_masks(vm, fields, actor, state)
                assert result.masks[1] == enemy_mask
                target_rows.append(dict(actor=actor, enemy_mask=enemy_mask,
                    reachable_enemy_mask=result.masks[1], passed=True))
        test.native_setup = original_setup(setup, vm, fields.mode_45)
        assert test.native_setup == (3, 0)
        for count in (1, 2, 3):
            for modes in ((1, 0), (0, 1)):
                targets = tuple(range(14, 14 + count))
                raw, _, _, native_vm = test.builder(targets, action=3, skill=True,
                    skill_id=126, skill_kind=0, modes=modes)
                assert struct.unpack('<I', native_vm.mem_read(command_native.BATTLE + 0x468, 4))[0] == test.native_setup[1]
                decoded = test.decode_sequence(raw)
                assert len(decoded) == count and len(raw) == count * 17
                for i, result in enumerate(decoded):
                    assert result[-1] == 126
                    assert result[1] == int(i + 1 < count)
                    assert result[2] == int(modes == (0, 1))
                    assert result[4:6] == (0, 1 << i)
                rows.append(dict(count=count, modes=modes, targets=targets,
                    native_setup=test.native_setup,
                    wire_bytes=len(raw), wire_hex=raw.hex(), decoded=decoded, passed=True))
        # Prove the previous fixture regression remains visible: mode3 genuinely
        # emits one multi-bit-mask packet, which the one-target grammar rejects.
        bad_definition = bytearray(definition)
        bad_definition[0x45] = 3
        test.native_definition = bytes(bad_definition)
        test.native_setup = original_setup(setup, vm, 3)
        assert test.native_setup == (3, 1)
        combined, _, _, _ = test.builder((14, 20, 27), action=3, skill=True,
            skill_id=126, skill_kind=0)
        assert len(combined) == 17 and struct.unpack_from('<H', combined, 7)[0] == 0x2041
        assert test.decode_sequence(combined) is None
        regression = dict(mode=3, native_setup=test.native_setup,
            wire_hex=combined.hex(), parser_rejected=True)
        report = dict(custom_design_id="CUSTOM-0058", cases=rows, passed=6,
            native_setup_entry_rva="0x11ead0", native_setup_output_fields=["B+45C", "B+468"],
            actual_setup_output_fed_to_builder=True, previous_mode3_regression=regression,
            native_target_setup_cases=target_rows, native_target_setup_passed=len(target_rows),
            command="python -B -m tools.skills.verify_shunying_command",
            native_entry_rva="0x118e50", native_stop_rva="0x1191ee",
            native_image_sha256=hashlib.sha256(test.image).hexdigest(),
            candidate_catalog_sha256=hashlib.sha256(raw_catalog).hexdigest(),
            candidate_record_sha256=hashlib.sha256(definition).hexdigest(),
            native_builder_and_cpp_parser_verified=True,
            target_list_and_count_source="Explicit bounded test fixture, not UI interaction",
            native_ui_maximum_target_count_verified=False,
            fewer_remaining_enemies_confirmation_verified=False,
            optional_fewer_than_three_targets_confirmation_verified=False,
            actual_game_cast_verified=False)
        destination = ROOT / "artifacts/custom-skills/shunying/target-command-native.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"passed": 6, "output": str(destination), "ui_confirmation_verified": False}))
    finally:
        CurrentSkillCommandTests.doClassCleanups()


if __name__ == "__main__":
    main()
