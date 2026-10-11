"""Bounded native WPN field differential; no source/client/DB mutation.

Mutated rows are isolated VM inputs, never native-authoritative item records.
This checks definition retention, not a whole-client absence proof.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from .current_equipment_20260926 import EquipmentOracle, PIN, require
from .current_item_metadata import NativeItemMetadata, growth


def audit():
    current = EquipmentOracle()
    native = NativeItemMetadata()
    for low, high in native.CODE:
        require(current.image[low:high] == native.image[low:high],
                f'Current PE/native-image code mismatch {low:x}')
    catalogs = []
    vectors = []
    for family, count in (('WPN', 630), ('TWP', 629)):
        rows = native.sections[family]['records']
        require(len(rows) == count, 'Source count changed')
        fields = [growth.fields(row) for row in rows]
        require(all(len(row) == 32 for row in fields), 'Source width changed')
        require(all(row[30:32] == [b'0', b'0'] for row in fields),
                'Previously unused trailing source fields changed')
        catalogs.append(dict(family=family, count=count, column_count=32,
            distributions={str(c):dict(Counter(r[c].decode('ascii') for r in fields))
                           for c in (1, 26, 27, 28, 29, 30, 31)},
            column1_examples=[dict(source_line=rows[i]['source_line'],
                column1_decimal=int(value), key=int(fields[i][0]),
                fields_hex=[f.hex() for f in fields[i]],
                fields_cp950=[f.decode('cp950') for f in fields[i]])
                for value in sorted({r[1] for r in fields},key=int)
                for i in [next(i for i,r in enumerate(fields) if r[1]==value)]]))
        original = rows[0]
        baseline = native.item_row(family, 0)
        # One field at a time; parser receives original source except this value.
        for column, value, offset in ((1,b'99',None),(2,b'Probe_Tag',None),
                (30,b'17',None),(31,b'18',None), (26,b'19',0x11c),
                (27,b'20',0x11d),(28,b'777',0x11e),(29,b'9',0x120)):
            values = growth.fields(original)
            values[column] = value
            rows[0] = growth.record(b','.join(values)+b'\n',
                                   original['source_line'], 0)
            try:
                observed = native.item_row(family, 0)
            finally:
                rows[0] = original
            expected = bytearray(baseline['record'])
            if offset is not None:
                width = 2 if column == 28 else 1
                expected[offset:offset+width] = int(value).to_bytes(width,'little')
            require(observed['record'] == bytes(expected),
                    f'Unexpected retained field mutation {family} column {column}')
            accessed = sorted(set(observed['columns']))
            require((column in accessed) == (offset is not None),
                    'Native field access differed from retention')
            vectors.append(dict(family=family, key=baseline['key'],
                source_line=original['source_line'], mutated_column=column,
                synthetic_value=value.decode(), native_accessed_columns=accessed,
                changed_metadata_offsets=[hex(i) for i,(a,b) in
                    enumerate(zip(baseline['record'], observed['record'])) if a!=b],
                metadata_equal=(baseline['record']==observed['record'])))
    return dict(schema='current-weapon-mapping-fields-20260926', status='PASS',
        exe_sha256=PIN, source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
        native_image_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763',
        catalogs=catalogs, differential_vectors=vectors,
        scope='Native 59420 complete parser return + 59A60 lookup. WPN1/TWP19001 in-memory synthetic differentials; full396 metadata compared. No DA mapping, full tooltip, gameplay formula or client graphical acceptance claimed.')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: 16 current-code field differentials; 1259 current source rows; '+str(args.output))


if __name__ == '__main__':
    main()
