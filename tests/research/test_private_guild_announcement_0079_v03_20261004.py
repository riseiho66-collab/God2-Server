"""Static-only announcement QA risk checks; never import Windows launch code."""
import ast
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
NEW = ROOT / 'tools/strike_lab/private_guild_announcement_0079_v03_20261004.py'
OLD = ROOT / 'tools/strike_lab/private_guild_formal_entry_0078_v04_20261004.py'


def require(value, error):
    if not value:
        raise ValueError(error)


def functions(path):
    return {node.name: node for node in ast.parse(path.read_text('utf-8')).body
            if isinstance(node, ast.FunctionDef)}


class AnnouncementHarnessRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = functions(NEW)
        cls.ns = {'require': require, 're': re}
        pure = [cls.tree[name] for name in
                ('announcement_cache', 'announcement_physical_rows', 'announcement_marker')]
        exec(compile(ast.Module(body=pure, type_ignores=[]), str(NEW), 'exec'), cls.ns)

    def test_cache_size_nul_and_max_boundary(self):
        decode = self.ns['announcement_cache']
        self.assertEqual(decode(4, b'\0'), b'')
        self.assertEqual(decode(1044, b'a' * 1040 + b'\0'), b'a' * 1040)
        for size, raw in ((3, b'\0'), (1045, b'a' * 1041 + b'\0'),
                          (5, b'\0a'), (6, b'a\0\0'), (7, b'a\0')):
            with self.assertRaises(ValueError):
                decode(size, raw)

    def test_physical_rows_do_not_invent_newlines(self):
        join = self.ns['announcement_physical_rows']
        self.assertEqual(join([b'A\0' + bytes(255), b'B\0' + bytes(255)]), b'AB')
        self.assertEqual(join([b'x' * 256 + b'\0']), b'x' * 256)
        self.assertEqual(join([b'CancelNotice0079\0' + bytes(241)] + [bytes(257)] * 17), b'CancelNotice0079')
        self.assertEqual(join([b'A\0' + bytes(255)] + [bytes(257)] * 62 + [b'B\0' + bytes(255)]), b'AB')
        for rows in ([], [b'x' * 256 + b'\0'] * 5, [bytes(257)] * 65, [b'x' * 257], [b'a\0']):
            with self.assertRaises(ValueError):
                join(rows)

    def test_marker_requires_exact_identity_authority_and_unique_event(self):
        match = self.ns['announcement_marker']
        line = ('OWNED_GUILD_ANNOUNCEMENT_PUBLISHED session_id=12 character_id=4 '
                'guild_id=1 revision=0 published=true write_authorized=true '
                'entry=native_help_CUSTOM CUSTOM-0078')
        req = {'published': 'true', 'write_authorized': 'true'}
        self.assertIsNotNone(match([line], 'OWNED_GUILD_ANNOUNCEMENT_PUBLISHED', 4, 1, req))
        self.assertIsNone(match([line], 'OWNED_GUILD_ANNOUNCEMENT_PUBLISHED', 5, 1, req))
        self.assertIsNone(match([line], 'OWNED_GUILD_ANNOUNCEMENT_PUBLISHED', 4, 2, req))
        self.assertIsNone(match([line.replace('true', 'false')],
                                'OWNED_GUILD_ANNOUNCEMENT_PUBLISHED', 4, 1, req))
        with self.assertRaises(ValueError):
            match([line, line], 'OWNED_GUILD_ANNOUNCEMENT_PUBLISHED', 4, 1, req)

    def test_previous_phase_parsers_and_guard_ownership_preserved(self):
        old = functions(OLD)
        for name in ('native_login_phase', 'native_login_frontend', 'protected', 'guard_sources'):
            self.assertEqual(ast.dump(self.tree[name], include_attributes=False),
                             ast.dump(old[name], include_attributes=False), name)
        source = NEW.read_text('utf-8')
        self.assertIn('BOOTSTRAP49_HISTORY_REQUIRED', source)
        self.assertIn('ANNOUNCEMENT_SCHEMA50_REQUIRED', source)
        self.assertIn('POSTPROMOTION_RESOURCE_NOT_BYTE_EXACT', source)
        self.assertNotIn('shutil.copyfile(artifact,target)', source)
        worker = self.tree['worker']
        nested = {n.name: n for n in worker.body if isinstance(n, ast.FunctionDef)}
        oldnested = {n.name: n for n in old['worker'].body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(ast.dump(nested['launch'], include_attributes=False),
                         ast.dump(oldnested['launch'], include_attributes=False))
        operations = ast.unparse(nested['announcement_exercise'])
        self.assertIn('control(c, main, 30)', operations)
        self.assertIn('control(c, main, 26)', operations)
        self.assertIn('control(c, main, 28)', operations)
        self.assertNotIn('sqlite3.connect', operations)


if __name__ == '__main__':
    unittest.main()
