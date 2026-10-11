"""Current bytes -> original reader -> seven startup arguments; no fake slots."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_world_startup_assets import (
    ASSETS, HANDLE_STORES, CONSUMERS, NativeStartupAssets, BASE, CWD, STRIDE)
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_REG


class CurrentWorldStartupAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NativeStartupAssets()
        disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
        disassembler.detail = True
        cls.code = {i.address-BASE: i for i in disassembler.disasm(
            bytes(cls.native.vm.mem_read(BASE+0x64cb6, 0x64fe2-0x64cb6)),
            BASE+0x64cb6)}

    def instruction(self, rva, text):
        instruction = self.code[rva]
        self.assertEqual(instruction.mnemonic+' '+instruction.op_str, text)

    def call_target(self, rva, target):
        code = bytes(self.native.vm.mem_read(BASE+rva, 5))
        self.assertEqual(code[0], 0xe8)
        self.assertEqual(rva+5+struct.unpack('<i', code[1:])[0], target)

    def test_all_source_rows_native_inline_fields_and_asset_identity(self):
        n = self.native
        self.assertEqual(n.reader_result, 1)
        self.assertEqual([a.record for a in ASSETS], [2, 3, 10, 12, 8, 9, 46])
        for asset in ASSETS:
            with self.subTest(record=asset.record):
                offset = asset.record*STRIDE+4
                self.assertEqual(asset.inline_offset, offset)
                self.assertEqual(n.u32(n.records+offset-4), asset.record)
                self.assertEqual(n.rows[asset.record][1], asset.literal_path)
                self.assertEqual(n.string(n.records+offset), asset.literal_path.encode())
                self.assertEqual(n.path_copies[asset.record], (1, n.records+offset))
                self.assertEqual(n.plain_csv.splitlines()[asset.record+4].split(b',')[1],
                                 asset.literal_path.encode())
                raw, plain = n.assets[asset.record]
                self.assertEqual((len(raw), len(plain)), (asset.raw_size, asset.decoded_size))
                self.assertTrue(plain.startswith(b'IGSROM02\0\0\0\0ACTINDEX'))

    def test_original_decompression_of_every_asset(self):
        self.assertEqual(self.native.verify_native_decodes(),
                         {a.record: a.decoded_sha256 for a in ASSETS})
        self.assertFalse(self.native.handles)

    def test_original_startup_and_rom_first_open_arguments(self):
        for asset in ASSETS:
            with self.subTest(record=asset.record):
                self.instruction(asset.start_rva, 'mov eax, dword ptr [ebp + 0xa8d50d0]')
                self.instruction(asset.start_rva+6, f'add eax, {asset.inline_offset:#x}')
                self.call_target(asset.start_rva+12, 0x12f550)
                self.call_target(asset.start_rva+28, 0x147af7)
                self.call_target(asset.load_call_rva, 0x60a90)
                expected = CWD + asset.literal_path.encode()
                self.assertEqual(self.native.argument(asset), expected)
                self.assertEqual(self.native.argument(asset), expected)
                self.assertEqual(self.native.argument(asset, first_open=True),
                                 CWD+b'\\'+asset.asset.replace('/', '\\').encode())
        self.assertEqual(self.native.u32(0), 0xffffffff)

    def test_conditional_owner_and_postload_finalization(self):
        self.instruction(0x64e60, 'mov eax, dword ptr [ebp + 0x398]')
        self.instruction(0x64e69, 'test eax, eax')
        self.instruction(0x64e6b, 'jne 0x464ec5')
        self.instruction(0x64e6d, 'push 0xc')
        self.call_target(0x64e6f, 0x15b406)
        self.call_target(0x64e8c, 0x10fa30)
        self.instruction(0x64e95, 'mov dword ptr [ebp + 0x398], eax')
        self.instruction(0x64eb2, 'mov ecx, dword ptr [ebp + 0xaa36484]')
        self.instruction(0x64eb8, 'push eax')
        self.instruction(0x64eb9, 'push ecx')
        self.instruction(0x64eba, 'mov ecx, dword ptr [ebp + 0x398]')
        self.call_target(0x64ec0, 0x10fa50)
        self.call_target(0x64f21, 0x60b10)
        for rva, expected in (
                (0x64fbd, 'mov eax, dword ptr [ebp + 0xaba32dc]'),
                (0x64fc3, 'push edx'), (0x64fc4, 'lea ecx, [ebp + 0xaa36488]'),
                (0x64fca, 'push eax'),
                (0x64fd0, 'mov ecx, dword ptr [ebp + 0xaba32dc]'),
                (0x64fd6, 'push ecx'), (0x64fd7, 'lea ecx, [ebp + 0xa7e04d0]')):
            self.instruction(rva, expected)
        self.call_target(0x64fcb, 0x10dc70)
        self.call_target(0x64fdd, 0xff3c0)

    def test_handle_store_provenance_from_original_mov_dataflow(self):
        # Static symbolic provenance, NOT native execution with fabricated
        # handles. Calls yield labels; no label is ever written into the VM.
        registers, memory, found = {}, {}, []
        aliases = {'ax': 'eax', 'si': 'esi', 'dx': 'edx'}
        bases = {'ebp': 'world', 'esp': 'stack', 'ebx': 'secondary', 'edi': 'primary'}
        loaders = {a.load_call_rva: ('return', a.record) for a in ASSETS}
        for rva, instruction in self.code.items():
            if rva in (0x64d01, 0x64f3f):
                self.assertEqual(registers['esi'], ('return', 2))
            elif rva == 0x64eb8:
                self.assertEqual(registers['eax'], ('return', 9))
            elif rva == 0x64fc3:
                self.assertEqual(registers['edx'], ('return', 8))
            if instruction.mnemonic == 'call':
                registers['eax'] = loaders.get(rva)
                registers['ecx'] = registers['edx'] = None
                continue
            if instruction.mnemonic != 'mov':
                continue
            destination, source = instruction.operands
            value = None
            if source.type == X86_OP_REG:
                name = instruction.reg_name(source.reg)
                value = registers.get(aliases.get(name, name))
            elif source.type == X86_OP_MEM:
                base = bases.get(instruction.reg_name(source.mem.base))
                value = memory.get((base, source.mem.disp))
            if destination.type == X86_OP_REG:
                name = instruction.reg_name(destination.reg)
                registers[aliases.get(name, name)] = value
            elif destination.type == X86_OP_MEM:
                base = bases.get(instruction.reg_name(destination.mem.base))
                key = (base, destination.mem.disp)
                memory[key] = value
                if value is not None:
                    found.append((rva, value[1], base, destination.mem.disp, destination.size))
        self.assertEqual(tuple(found), HANDLE_STORES)
        self.instruction(0x64d02, 'lea ebx, [ebp + 0xaba32e0]')
        self.instruction(0x64f40, 'lea edi, [ebp + 0x39c]')
        self.instruction(0x64cf2, 'mov esi, eax')
        self.instruction(0x64d01, 'push esi')
        self.instruction(0x64f3f, 'push esi')
        self.call_target(0x64d0d, 0x1081c0)
        self.call_target(0x64f4b, 0x1081c0)
        # Record 8 survives in EDX to the 10DC70 second argument.
        self.instruction(0x64f54, 'mov edx, dword ptr [esp + 0x1c]')
        self.instruction(0x64fc3, 'push edx')

    def test_effect_manager_binding_is_gcall_not_title(self):
        binding = next(c for c in CONSUMERS if c['call_rva'] == 0x64fcb)
        self.assertEqual(binding['this'], 'world+0xaa36488')
        self.assertEqual(binding['arguments'],
                         ['[world+0xaba32dc]', 'return(60A90, record=8)'])
        asset = next(a for a in ASSETS if a.record == 8)
        self.assertEqual(asset.inline_offset, 0x844)
        self.assertEqual(asset.literal_path, r'\Data3\Flow\gcall.ROM')
        self.assertEqual(self.native.argument(asset, first_open=True),
                         CWD+rb'\Data3\Flow\gcall.ROMZ')
        # Verify the original callee stores and reset; no constructed manager.
        d = Cs(CS_ARCH_X86, CS_MODE_32)
        instructions = list(d.disasm(bytes(self.native.vm.mem_read(BASE+0x10dc70, 0x17)),
                                    BASE+0x10dc70))
        self.assertEqual([i.mnemonic+' '+i.op_str for i in instructions], [
            'mov eax, dword ptr [esp + 4]', 'mov dx, word ptr [esp + 8]',
            'mov dword ptr [ecx], eax', 'mov word ptr [ecx + 0x2c], dx',
            'call 0x50dc90', 'ret 8'])
        instructions = list(d.disasm(bytes(self.native.vm.mem_read(BASE+0x10dc90, 0x24)),
                                    BASE+0x10dc90))
        self.assertEqual([i.mnemonic+' '+i.op_str for i in instructions], [
            'or eax, 0xffffffff', 'xor edx, edx',
            'mov word ptr [ecx + 4], ax', 'mov word ptr [ecx + 0x22], ax',
            'mov dword ptr [ecx + 0x24], edx', 'mov dword ptr [ecx + 0x28], edx',
            'mov word ptr [ecx + 6], ax', 'mov word ptr [ecx + 8], ax',
            'mov word ptr [ecx + 0xa], ax', 'mov word ptr [ecx + 0xc], ax', 'ret '])


if __name__ == '__main__':
    unittest.main()
