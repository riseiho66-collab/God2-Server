"""Native pet2 category names only; no growth grade, numeric base or grants."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
from . import recover_companion_growth as g

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'NewCombatPet_Category'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
CLIENT = ROOT.parent / 'God2'
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
DATASET = 'de6cada4b90996515a0e371eb8d503a39718b45a9103b9259c1f7f483b569772'


def fingerprint(rows):
    data = bytearray()
    for group, index, line, raw, label in rows:
        data.extend(struct.pack('<BBII', group, index, line, len(raw)))
        data.extend(raw)
        data.extend(bytes((len(label),)))
        data.extend(label)
    return hashlib.sha256(data).hexdigest()


def extract():
    image = IMAGE.read_bytes()
    raw = (CLIENT / g.source_path(SOURCE)).read_bytes()
    plain = g.decode_csvz(raw)
    if (g.digest(image) != g.IMAGE_SHA or
            (g.digest(raw), g.digest(plain)) != g.SOURCE_HASHES[SOURCE]):
        raise ValueError('Unqualified current native category source')
    rows = g.parse_auxiliary(SOURCE, plain)['records']
    native = g._NativeRows(image)
    native.vm.mem_write(native.OUTPUT, b'\xa5' * 0x4000)
    native.vm.mem_write(native.TABLE + 0xfc2c4, struct.pack('<I', native.OUTPUT))
    native.vm.mem_write(native.TABLE + 0xfc2c8, bytes(2))
    output = []
    for row in rows:
        values = g.fields(row)
        group, index = map(g.decimal, values[:2])
        label = values[2]
        address = native.OUTPUT + ((group - 1) * 16 + index) * 22
        native.tokenize(row, 12)
        native.reg('EBP', native.TABLE)
        native.reg('EBX', 0)
        native.vm.mem_write(native.SP, bytes(0x80))
        native.row(0x5c6a6, 0x5c9b5, range(9),
                   ((address, address + 22), (native.TABLE + 0xfc2c8, native.TABLE + 0xfc2ca)))
        if bytes(native.vm.mem_read(address, len(label) + 1)) != label + b'\0':
            raise ValueError('Original category name loader differs')
        output.append((group, index, row['source_line'], bytes.fromhex(row['raw_record_hex']), label))
    if len(output) != 464 or [(r[0], r[1]) for r in output] != [
            (group, index) for group in range(1, 30) for index in range(16)]:
        raise ValueError('Incomplete native category keys')
    # Exercise the actual FB selectors, gate and copied category-name getter.
    native.vm.mem_map(0x3500000, 0x1000, native.uc.UC_PROT_READ | native.uc.UC_PROT_WRITE)
    native.vm.mem_map(0x3600000, 0x1000, native.uc.UC_PROT_READ | native.uc.UC_PROT_WRITE)
    native.vm.mem_map(0x3700000, 0x100000, native.uc.UC_PROT_READ | native.uc.UC_PROT_WRITE)
    native.vm.mem_write(0x3500000 + 0xdc, struct.pack('<I', 0x3700000))
    native.vm.mem_write(0x3700000 + 0xcff70, struct.pack('<I', native.TABLE))
    for group, index, _, _, label in output:
        # Unrelated high nibble and nonzero upper register bits must not change
        # which category row is selected by the original low-byte getters.
        body = bytearray(72)
        body[0x2c], body[0x3c] = 0xf0 | index, group
        native.vm.mem_write(0x3600000, bytes(body))
        native.reg('EBP', 0x3500000)
        native.reg('EBX', 0x3600000)
        native.reg('EAX', 0xa5a5a5a5)
        native.reg('ECX', 0xa5a5a5a5)
        native.reg('ESP', native.SP - 0x50)
        native.allowed = ((native.STACK, native.STACK + 0x10000),)
        native.run(0xa4525, 0xa4543)
        if native.vm.reg_read(native.x86.UC_X86_REG_EAX) & 255 != 1:
            raise ValueError('Native category gate rejected source row')
        native.run(0xa4543, 0xa4567)
        got = bytes(native.vm.mem_read(native.SP + 0x7c, 22))
        if got[:len(label) + 1] != label + b'\0':
            raise ValueError('FB caller selected the wrong native category')
    return output


def cache(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    result = dict(source_sha256=g.SOURCE_HASHES[SOURCE][0],
                  decoded_sha256=g.SOURCE_HASHES[SOURCE][1], image_sha256=g.IMAGE_SHA,
                  dataset_sha256=fingerprint(rows), authority='NATIVE_PARSED_DISPLAY_ONLY',
                  native_selected_rows=464, flags_or_growth_formulas_verified=False,
                  rows=[[group,index,line,raw.hex(),label.hex()] for group,index,line,raw,label in rows])
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def cached(path):
    result = json.loads(path.read_text('utf-8'))
    rows = [(a,b,c,bytes.fromhex(d),bytes.fromhex(e)) for a,b,c,d,e in result['rows']]
    if (result['source_sha256'] != g.SOURCE_HASHES[SOURCE][0] or
            result['decoded_sha256'] != g.SOURCE_HASHES[SOURCE][1] or
            result['image_sha256'] != g.IMAGE_SHA or len(rows) != 464 or
            fingerprint(rows) != result['dataset_sha256'] or result['dataset_sha256'] != DATASET):
        raise ValueError('Category cache source or dataset differs')
    return rows


def install(db, rows):
    wanted = DATASET
    if len(rows) != 464 or fingerprint(rows) != wanted:
        raise ValueError('Unqualified category import')
    source = (1, g.SOURCE_HASHES[SOURCE][0], g.SOURCE_HASHES[SOURCE][1],
              g.IMAGE_SHA, CLIENT_SHA, wanted, 'NATIVE_PARSED_DISPLAY_ONLY')
    db.execute('BEGIN IMMEDIATE')
    try:
        old = db.execute('SELECT * FROM native_pet2_category_source').fetchall()
        old_rows = db.execute('SELECT * FROM native_pet2_category_rows ORDER BY group_id,category_index').fetchall()
        if old or old_rows:
            if old != [source] or old_rows != rows:
                raise ValueError('Existing native category catalog differs')
        else:
            db.execute('INSERT INTO native_pet2_category_source VALUES(?,?,?,?,?,?,?)', source)
            db.executemany('INSERT INTO native_pet2_category_rows VALUES(?,?,?,?,?)', rows)
        if db.execute('SELECT * FROM native_pet2_category_rows ORDER BY group_id,category_index').fetchall() != rows:
            raise ValueError('Category catalog readback differs')
        db.commit()
    except BaseException:
        db.rollback()
        raise
    return dict(rows=464, idempotent=bool(old), dataset_sha256=wanted,
                authority='NATIVE_PARSED_DISPLAY_ONLY', growth_rule_activated=False)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache', type=Path)
    ap.add_argument('--database', type=Path)
    args = ap.parse_args()
    rows = extract()
    if args.cache:
        print(json.dumps({k:v for k,v in cache(rows,args.cache).items() if k != 'rows'}))
    if args.database:
        with closing(sqlite3.connect(args.database.resolve(strict=True))) as db:
            print(json.dumps(install(db, rows)))
