import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from post_six_snapshot import REGISTERS, WIRE, capture_post_six


class Driver:
    def __init__(self, malformed=False, short=False, root_valid=True, changed=False):
        self.commands = []
        self.malformed, self.short = malformed, short
        self.root_valid, self.changed = root_valid, changed

    def command(self, command):
        self.commands.append(command)
        if command.startswith('.printf'):
            if self.malformed:
                return 'debugger command failed'
            regs = dict.fromkeys(REGISTERS, 0)
            regs.update(eax=6, esi=0x200758, edi=0x200104,
                        esp=0x300000, eip=0x412506 + self.changed, efl=0x202)
            return 'POST6_REGS ' + ' '.join(f'{k}={regs[k]:08x}' for k in REGISTERS)
        match = re.fullmatch(r'\.writemem "([^"]+)" ([0-9a-f]+) L([0-9a-f]+)', command)
        assert match, command
        path, address, size = match.groups()
        data = bytearray(int(size, 16) - self.short)
        if Path(path).name == 'stack.bin':
            data[:4] = (0x200000 if self.root_valid else 0).to_bytes(4, 'little')
            data[8:12] = (0x4133b3).to_bytes(4, 'little')
        Path(path).write_bytes(data)
        return 'written'


class PostSixSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.event = dict(api='send', matched=True, pc=0x412506, sp=0x300000,
                          eax=6, pid=123, tid=456, sequence=147, entry=146)
        self.pending = dict(api='send', ret=0x412506, sp=0x300000-20,
                            a2=6, pid=123, tid=456)

    def capture(self, driver):
        result = capture_post_six(driver, self.run, self.event, self.pending, WIRE)
        return result, json.loads((self.run / result['file']).read_text())

    def test_private_bounded_capture_never_promotes(self):
        driver = Driver()
        result, report = self.capture(driver)
        self.assertEqual(result['captured_regions'], 5)
        self.assertEqual(report['status'], 'CAPSULE_INCOMPLETE')
        self.assertFalse(report['replay_ready'])
        self.assertIsNone(report['protocol_state_fingerprint'])
        self.assertEqual(report['next_direction'], 'UNKNOWN')
        self.assertEqual(report['protocol_root'], 0x200000)
        self.assertEqual(report['errors'], [])
        self.assertLess(sum(r['size'] for r in report['regions']), 40000)
        self.assertNotIn('registers', result)
        for region in report['regions']:
            raw = (self.run / result['file']).parent.joinpath(region['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), region['sha256'])
        self.assertTrue(all(c.startswith(('.printf', '.writemem')) for c in driver.commands))

    def test_boundary_mismatch_rejected_before_io(self):
        for key, value in [('matched', False), ('pc', 0x412507), ('eax', 5),
                           ('pid', 999), ('tid', 999), ('sp', 0x300004)]:
            with self.subTest(key=key):
                event = dict(self.event, **{key: value})
                driver = Driver()
                with self.assertRaises(ValueError):
                    capture_post_six(driver, self.run, event, self.pending, WIRE)
                self.assertFalse(driver.commands)
                self.assertFalse((self.run / 'protocol-private').exists())

    def test_unknown_wire_rejected(self):
        with self.assertRaises(ValueError):
            capture_post_six(Driver(), self.run, self.event, self.pending, b'123456')

    def test_bad_register_reply_stops_memory_capture(self):
        driver = Driver(malformed=True)
        result, report = self.capture(driver)
        self.assertEqual(len(driver.commands), 1)
        self.assertEqual(result['error_count'], 1)
        self.assertFalse(report['replay_ready'])

    def test_context_change_stops_memory_capture(self):
        driver = Driver(changed=True)
        result, _ = self.capture(driver)
        self.assertEqual(len(driver.commands), 1)
        self.assertEqual(result['captured_regions'], 0)

    def test_short_reads_not_accepted_or_followed(self):
        result, report = self.capture(Driver(short=True))
        self.assertEqual(result['captured_regions'], 0)
        self.assertEqual(result['error_count'], 4)
        self.assertNotIn('protocol_root', report)

    def test_unconfirmed_root_not_followed(self):
        result, report = self.capture(Driver(root_valid=False))
        self.assertEqual(result['captured_regions'], 4)
        self.assertNotIn('protocol_root', report)
        self.assertEqual(result['error_count'], 1)

    def test_existing_capture_not_overwritten(self):
        result, _ = self.capture(Driver())
        before = (self.run / result['file']).read_bytes()
        with self.assertRaises(FileExistsError):
            self.capture(Driver())
        self.assertEqual((self.run / result['file']).read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
