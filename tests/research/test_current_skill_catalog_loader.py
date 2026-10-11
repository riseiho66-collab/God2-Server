"""Execute the original loader without preparing unrelated battle resources."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from tools.strike_lab import current_skill_catalog_loader as catalog
from tools.strike_lab.current_battle_bootstrap import BootstrapResources, MANAGER
from tools.strike_lab.current_indoor_resources import STACK
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_PROT_READ, UC_PROT_EXEC


class CurrentSkillCatalogLoaderTests(unittest.TestCase):
    def setUp(self):
        self.image = catalog.read_pinned(catalog.IMAGE, catalog.IMAGE_SHA)
        self.source = catalog.read_pinned(catalog.CLIENT / catalog.SOURCE, catalog.SOURCE_SHA256)
        self.n = n = BootstrapResources.__new__(BootstrapResources)
        n.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        n.vm.mem_map(catalog.BASE, (len(self.image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        n.vm.mem_write(catalog.BASE, self.image)
        n.vm.mem_map(STACK, 0x80000)
        self.dest = MANAGER + catalog.OFFSET
        first, end = (self.dest - 16) & ~4095, (self.dest + catalog.BODY_SIZE + 16 + 4095) & ~4095
        n.vm.mem_map(first, end - first)
        n.vm.mem_write(first, b'\xa5' * (end - first))
        n.files, n.handles, n.opens, n.calls = {}, {}, [], set()
        n.os_apis, n.find_first = {}, 0
        for rva in catalog.FILE_RVAS:
            n.vm.hook_add(UC_HOOK_CODE, n._service, begin=catalog.BASE + rva, end=catalog.BASE + rva)

    def test_original_full_loader_copies_all_four_banks_and_448_definitions(self):
        result = catalog.load_catalog(self.n, MANAGER)
        self.assertEqual(result['body'], self.source[4:])
        self.assertEqual(result['destination'], self.dest)
        self.assertEqual(result['definition_count'], 448)
        self.assertEqual(result['result'], 1)
        self.assertEqual(result['io'], [('open', catalog.SOURCE.lower()), ('read', 0, 4),
                                        ('read', 4, catalog.BODY_SIZE), ('close', catalog.FILE_SIZE)])
        for rva in (0x12d3b0, 0x155980, 0x12d417, 0x12d433):
            self.assertIn(rva, result['executed'])
        for definition in catalog.decode_definitions(self.source).values():
            self.assertEqual(bytes(self.n.vm.mem_read(self.dest + definition.source_offset - 4, 110)),
                             definition.raw)
        for address in (self.dest - 16, self.dest + catalog.BODY_SIZE):
            self.assertEqual(bytes(self.n.vm.mem_read(address, 16)), b'\xa5' * 16)
        self.assertEqual(bytes(self.n.vm.mem_read(catalog.BASE, len(self.image))), self.image)
        self.assertFalse(self.n.handles)
        self.assertFalse(self.n.skill_catalog_loading)
        with self.assertRaises(ValueError):
            catalog.load_catalog(self.n, MANAGER)

    def test_changed_code_and_source_hash_fail_before_execution(self):
        with patch.object(catalog, 'SOURCE_SHA256', '0' * 64):
            with self.assertRaises(ValueError):
                catalog.load_catalog(self.n, MANAGER)
        self.n.vm.mem_write(catalog.BASE + 0x12d3b0, b'\x90')
        with self.assertRaisesRegex(ValueError, 'executable'):
            catalog.load_catalog(self.n, MANAGER)
        self.assertFalse(self.n.files)
        self.assertFalse(self.n.calls)

    def test_changed_locale_rejected_without_guessing_crt_behavior(self):
        self.n.vm.mem_write(0x6f6ed4, b'\x01\0\0\0')
        with self.assertRaisesRegex(ValueError, 'locale'):
            catalog.load_catalog(self.n, MANAGER)
        self.assertFalse(self.n.calls)

    def test_short_virtual_stream_is_not_accepted_as_native_success(self):
        service = catalog.file_service

        def short_stream(n, vm, address, size, context):
            service(n, vm, address, size, context)
            if len(n.skill_catalog_io) == 1:
                handle = next(iter(n.handles.values()))
                handle[0] = handle[0][:-1]

        with patch.object(catalog, 'file_service', side_effect=short_stream):
            with self.assertRaisesRegex(AssertionError, 'stream length/position'):
                catalog.load_catalog(self.n, MANAGER)
        self.assertFalse(self.n.skill_catalog_loading)
        self.assertEqual(bytes(self.n.vm.mem_read(self.dest, catalog.BODY_SIZE)), b'\xa5' * catalog.BODY_SIZE)


if __name__ == '__main__':
    unittest.main()
