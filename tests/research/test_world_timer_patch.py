"""Emulate the pinned client's world-loop timeGetTime check, without a UI.

This is instruction-level evidence for the launcher branch patch, not a claim
that the rendered town has passed an interactive playtest.
"""

import hashlib
import struct
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin"
CLIENT = ROOT.parent / "God2/God2-run-ae997bbe726afaaee3a02ff9b718eff03f3d726002bc6aa36ce66a1964241f7f.exe"
NATIVE_SHA = "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"
CLIENT_SHA = "ae997bbe726afaaee3a02ff9b718eff03f3d726002bc6aa36ce66a1964241f7f"


def patch_byte(client: bytes) -> int:
    pe = struct.unpack_from("<I", client, 0x3c)[0]
    count = struct.unpack_from("<H", client, pe + 6)[0]
    table = pe + 24 + struct.unpack_from("<H", client, pe + 20)[0]
    sections = {}
    for index in range(count):
        header = table + 40 * index
        name = client[header:header + 8].rstrip(b"\0")
        size, _, _, offset = struct.unpack_from("<IIII", client, header + 8)
        sections[name] = client[offset:offset + size]
    code = sections[b".w10fix"]
    emission = bytes.fromhex("c6 80 96 b8 05 00")
    assert code.count(emission) == 1
    return code[code.index(emission) + len(emission)]


def run_check(image: bytes, first_byte: int, branch: int, initial_flag=0):
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    machine.mem_map(0x400000, 0x400000)
    machine.mem_write(0x400000, image)
    machine.mem_map(0x10000000, 0x100000)
    machine.mem_map(0x20000000, 0x10000)
    machine.mem_map(0x30000000, 0x1000)
    machine.mem_write(0x30000000, bytes((first_byte, 0x25)))
    machine.mem_write(0x5707bc, struct.pack("<I", 0x30000000))
    machine.mem_write(0x45b896, bytes((branch,)))
    # Stop at the diagnostic sender; the real network routine is outside the
    # isolated function contract. A RET preserves the function's own flow.
    machine.mem_write(0x402b10, b"\xc3")
    owner = 0x10000000
    machine.mem_write(owner + 0xfc270, struct.pack("<I", initial_flag))
    stack = 0x20008000 - 4
    machine.mem_write(stack, struct.pack("<I", 0x60000000))
    machine.reg_write(UC_X86_REG_ESP, stack)
    machine.reg_write(UC_X86_REG_ECX, owner)
    diagnostics = []

    def observe(_, address, __, ___):
        if address == 0x402b10:
            diagnostics.append(address)

    machine.hook_add(UC_HOOK_CODE, observe)
    machine.emu_start(0x45b880, 0x60000000, count=100)
    flag = struct.unpack("<I", machine.mem_read(owner + 0xfc270, 4))[0]
    return flag, len(diagnostics), machine.reg_read(UC_X86_REG_EAX)


class WorldTimerPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = NATIVE.read_bytes()
        client = CLIENT.read_bytes()
        assert hashlib.sha256(cls.image).hexdigest() == NATIVE_SHA
        assert hashlib.sha256(client).hexdigest() == CLIENT_SHA
        assert cls.image[0x5b896:0x5b898] == bytes.fromhex("74 21")
        cls.branch = patch_byte(client)
        assert cls.branch == 0xeb

    def test_original_unhooked_prologue_passes(self):
        self.assertEqual(run_check(self.image, 0x83, 0x74), (0, 0, 0))

    def test_original_hooked_prologue_reports_error(self):
        self.assertEqual(run_check(self.image, 0xff, 0x74), (1, 1, 1))

    def test_launcher_patch_prevents_new_timer_failure(self):
        self.assertEqual(run_check(self.image, 0xff, self.branch), (0, 0, 0))

    def test_launcher_patch_does_not_clear_prior_terminal_state(self):
        self.assertEqual(run_check(self.image, 0xff, self.branch, 1), (1, 0, 1))


if __name__ == "__main__":
    unittest.main()
