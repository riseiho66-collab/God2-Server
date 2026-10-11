import unittest
from pathlib import Path

from tools.strike_lab.recover_items import (
    LABELS, MAX_LINE, SOURCE, build_items, digest, parse_items, read_source, serialize,
)


def table(rows=None, count=None, type_rows=None):
    # Parser fixtures only; production output is always decoded from the client.
    rows = rows if rows is not None else [b'1,0,Wpn,1,Name,200,100,,,,,,,8400,' + b','.join([b'0'] * 11)]
    types = type_rows or [b'1,1000,WPN,Weapon']
    return b'\n'.join([b'RowDesc,1', b','.join(s.encode('cp950') for s in LABELS),
                       b'ItemType,' + str(len(types)).encode(), *types,
                       b'WPN,' + str(len(rows) if count is None else count).encode(), *rows])


class RecoverItemsTests(unittest.TestCase):
    def test_normalization_and_unknowns(self):
        result = parse_items(table())
        row = result['records'][0]
        self.assertEqual(row['definition_key'], 'WPN:1')
        self.assertEqual(row['client_visual_effect_id'], 8400)
        self.assertFalse(row['client_flags']['stackable'])
        for key in ('stack_limit', 'equipment_slot', 'equipment_restrictions', 'server_effect_handler'):
            self.assertIsNone(row[key])
        self.assertFalse(row['runtime_eligible'])
        self.assertEqual(bytes.fromhex(row['raw_fields_hex'][5]), b'200')
        self.assertEqual(serialize(result), serialize(parse_items(table())))

    def test_malformed_and_bounds(self):
        base = table()
        for bad in (base.replace(b'WPN,1\n', b'WPN,100001\n'),
                    base.replace(b'WPN,1\n', b'WPN,-1\n'),
                    base.replace(b'WPN,1\n', b'WPN,2\n'),
                    base.replace(b'1,0,Wpn', b'2147483648,0,Wpn'),
                    base.replace(b'1,0,Wpn', b'0,0,Wpn'),
                    base.replace(b'1,0,Wpn', b'x,0,Wpn'),
                    base.replace(b'Name', b'Na\0me'),
                    base.replace(b'Name', b'x' * (MAX_LINE + 1)),
                    base.replace(b'8400,0', b'8400,2'),
                    base.replace(b'ITEM_ID', b'UNPROVEN'),
                    table([b'1,0']), table(count=0)):
            with self.subTest(bad=bad[:40]), self.assertRaises(ValueError):
                parse_items(bad)

    def test_duplicates(self):
        row = table().split(b'\n')[-1]
        for bad in (table([row, row]), table() + b'\nWPN,0',
                    table(type_rows=[b'1,1000,WPN,A', b'1,1000,WPN,B'])):
            with self.assertRaises(ValueError):
                parse_items(bad)

    def test_range_discrepancy_preserved(self):
        result = parse_items(table().replace(b'1,0,Wpn', b'1001,0,Wpn'))
        self.assertFalse(result['records'][0]['within_declared_type_range'])

    def test_short_rows_and_overlapping_type_ranges(self):
        data = table(type_rows=[b'1,1000,WPN,W', b'2801,2899,GOD,G', b'2801,2899,MAP,M'])
        data += b'\nGOD,1\n2801,-1,God,1,Name,1791\nMAP,1\n2901,-1,Map,1,Place'
        rows = parse_items(data)['records']
        self.assertEqual(len(rows), 3)
        self.assertIsNone(rows[0]['client_flags']['stackable'])
        self.assertIsNone(rows[0]['client_visual_effect_id'])

    def test_invalid_display_bytes_preserved(self):
        row = parse_items(table().replace(b'Name', b'\xff'))['records'][0]
        self.assertIsNone(row['client_name'])
        self.assertEqual(row['raw_fields_hex'][4], 'ff')

    def test_current_client_byte_identity_and_artifact(self):
        repo = Path(__file__).resolve().parents[2]
        client = repo.parent / 'God2'
        if not (client / SOURCE).is_file():
            self.skipTest('Original current client is unavailable')
        decoded, source = read_source(client.resolve(), SOURCE)
        lines = [line.removesuffix(b'\r') for line in decoded.split(b'\n')]
        result = build_items(client)
        self.assertEqual(result['source'], source)
        declared_total = 0
        for kind in result['types']:
            headers = [line for line in lines if line.startswith(kind['section'].encode() + b',')]
            if headers:
                declared_total += int(headers[0].split(b',')[1])
        self.assertEqual(len(result['records']), declared_total)
        for row in [result['row_description'], *result['types'], *result['records']]:
            raw = b','.join(bytes.fromhex(value) for value in row['raw_fields_hex'])
            self.assertEqual(raw, lines[row['source_line'] - 1])
            self.assertEqual(digest(raw), row['source_record_sha256'])
        self.assertEqual(serialize(result), serialize(build_items(client)))
        artifact = repo / 'artifacts/world-atlas/items.json'
        self.assertEqual(artifact.read_bytes(), serialize(result).encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
