"""Pin the current client's native C2S35/action2 timeout producer.

This establishes a producer path, not the missing server-side defense effect.
"""

from hashlib import sha256
from pathlib import Path
import unittest

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile


ROOT = Path(__file__).resolve().parents[2]
MAPPED = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
CLIENT = ROOT.parent / 'God2/God2.exe'
MAPPED_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'


def instructions(raw, start, end):
    return {i.address: (i.mnemonic, i.op_str)
            for i in Cs(CS_ARCH_X86, CS_MODE_32).disasm(raw[start:end], start)}


class CurrentAction2Timeout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapped = MAPPED.read_bytes()
        cls.client = CLIENT.read_bytes()
        assert sha256(cls.mapped).hexdigest() == MAPPED_SHA
        assert sha256(cls.client).hexdigest() == CLIENT_SHA
        cls.pe = pefile.PE(data=cls.client, fast_load=True)

    def test_current_exe_retains_timeout_and_grant_functions(self):
        for start, end in ((0x112c37, 0x112e88),
                           (0x1117c1, 0x111804),
                           (0x117590, 0x1177b5)):
            offset = self.pe.get_offset_from_rva(start)
            self.assertEqual(self.mapped[start:end], self.client[offset:offset + end - start])

    def test_negative_remaining_time_reaches_action2_producer(self):
        code = instructions(self.mapped, 0x112c37, 0x112e88)
        self.assertEqual(code[0x112c37], ('test', 'eax, eax'))
        self.assertEqual(code[0x112c39], ('jl', '0x112d89'))
        self.assertEqual(code[0x112d8f], ('mov', 'dword ptr [esi + 0xa9e9c18], 0'))
        self.assertEqual(code[0x112da1], ('mov', 'eax, dword ptr [esi + 0xa9e9c54]'))
        self.assertEqual(code[0x112dc3], ('mov', 'byte ptr [edi], 0xe'))
        for push, call in ((0x112e26, 0x112e2a), (0x112e72, 0x112e76)):
            self.assertEqual(code[push], ('push', '2'))
            self.assertEqual(code[call], ('call', '0x118e50'))
        self.assertEqual(code[0x112e7b], ('mov', 'dword ptr [esi + 0xa9e9c54], 1'))

    def test_entry_context_supplies_initial_window(self):
        code = instructions(self.mapped, 0x1117c1, 0x111804)
        self.assertEqual(code[0x1117c4], ('xor', 'edx, edx'))
        self.assertEqual(code[0x1117c6], ('mov', 'dl, byte ptr [ebp + 0x41]'))
        self.assertEqual(code[0x1117fe], ('mov', 'dword ptr [ebp + 0xa9e9c70], edx'))
        grant = instructions(self.mapped, 0x117590, 0x1175b2)
        self.assertEqual(grant[0x1175a6], ('mov', 'eax, dword ptr [esi + 0xa9e9c70]'))
        self.assertEqual(grant[0x1175ac], ('mov', 'dword ptr [esi + 0xa9e9c18], eax'))


if __name__ == '__main__':
    unittest.main()
