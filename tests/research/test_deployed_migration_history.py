"""Keep already-deployed SQLite migrations byte-for-byte compatible.

The baseline digest comes from the persistent 2592 database after migrations
1..21 were applied on 2026-09-26. New migrations must be appended, never edit
these entries (including SQL whitespace).
"""
import hashlib
from pathlib import Path
import re
import unittest


SOURCE = Path(__file__).resolve().parents[2] / 'src/db/Migration.cpp'
DEPLOYED_COUNT = 21
DEPLOYED_SHA256 = 'c6176666d8862cfcb8a3fd26c13153de5ef4b5247a850ffd16fd29d6c6847b79'


class DeployedMigrationHistoryTests(unittest.TestCase):
    def test_applied_sql_and_names_remain_exact(self):
        source = SOURCE.read_text(encoding='utf-8')
        records = re.findall(r'\{(\d+), "([^"]+)", R"SQL\((.*?)\)SQL"\}', source, re.S)
        self.assertGreaterEqual(len(records), DEPLOYED_COUNT)
        digest = hashlib.sha256()
        for expected, (version, name, sql) in enumerate(records[:DEPLOYED_COUNT], 1):
            self.assertEqual(int(version), expected)
            for value in (version, name, sql):
                digest.update(value.encode('utf-8'))
                digest.update(b'\0')
        self.assertEqual(digest.hexdigest(), DEPLOYED_SHA256)


if __name__ == '__main__':
    unittest.main()
