"""Backup-first female named deity fixture for the one isolated test character.

No production acquisition/growth rule is claimed. World36 application remains
an explicit isolated Application hook; this tool never patches a live process.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import struct

from tools.skills.qualify_shunying_female_deity import qualify, ROOT

FIXTURE = ROOT / 'artifacts/playtests/private-shunying-manual-20260930-01'
DATABASE = FIXTURE / 'diagnostic-accounts.db'
SOURCE = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
EVIDENCE = 'CUSTOM-0058/female-named-deity-native102-20260930'


def records():
    declaration = bytearray(19)
    declaration[:6] = b'\x30\x66test'
    status = bytearray(29)
    status[:3] = b'\x31\x66\x32'
    # Explicit display-test numbers only; no recovered growth/derived formula.
    struct.pack_into('<5H', status, 3, 666, 666, 666, 666, 666)
    struct.pack_into('<4H', status, 17, 666, 666, 666, 666)
    return bytes(declaration), bytes(status), b'\x34\x66\x00\x08'


def check_owner(db):
    row = db.execute('select account_id,name_bytes from recovered_characters where id=6').fetchone()
    if row != (6, b'test'):
        raise ValueError('Only isolated character6/account6/test may be configured')


def configure(database, apply=False):
    database = Path(database).resolve(strict=True)
    if database != DATABASE.resolve(strict=True):
        raise ValueError('Not the exact named isolated manual fixture')
    proof = qualify()
    declaration, status, skills = records()
    desired = (6, 102, declaration, status, skills, 1, SOURCE, 'CUSTOM_TEST_NOT_NATIVE', EVIDENCE)
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        check_owner(db)
        owned = db.execute('select * from character_deities where character_id=6 order by row_key').fetchall()
        selected = db.execute('select * from character_deity_selection where character_id=6').fetchall()
        if owned and (owned != [desired] or selected != [(6, 102, 1)]):
            raise ValueError('Existing owned deity differs; refusing replacement')
        result = dict(status='READY', apply=apply, idempotent=bool(owned), key=102,
                      native_qualification=proof, declaration_hex=declaration.hex(), status_hex=status.hex(),
                      persisted_skill_hex=skills.hex(), world_appearance_hex='3601010100660006000000',
                      limitations='Custom test ownership/stats. World36 resource/render and battle appearance still require client acceptance.')
        if not apply or owned:
            return result
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = FIXTURE / ('diagnostic-accounts.before-female-deity-' + stamp + '.db')
        with backup.open('xb'):
            pass
        with closing(sqlite3.connect(backup)) as target:
            db.backup(target)
        result['backup'] = str(backup)
        result['backup_sha256'] = hashlib.sha256(backup.read_bytes()).hexdigest()
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on')
        db.execute('begin immediate')
        try:
            check_owner(db)
            if db.execute('select 1 from character_deities where character_id=6').fetchone():
                raise ValueError('Deity ownership changed after backup')
            others = db.execute('select * from character_deities where character_id<>6 order by character_id,row_key').fetchall()
            other_selection = db.execute('select * from character_deity_selection where character_id<>6 order by character_id').fetchall()
            db.execute('insert into character_deities values(?,?,?,?,?,?,?,?,?)', desired)
            db.execute('insert into character_deity_selection values(6,102,1)')
            if db.execute('select * from character_deities where character_id=6').fetchall() != [desired]:
                raise AssertionError('Owned deity readback differs')
            if db.execute('select * from character_deities where character_id<>6 order by character_id,row_key').fetchall() != others:
                raise AssertionError('Other owner changed')
            if db.execute('select * from character_deity_selection where character_id<>6 order by character_id').fetchall() != other_selection:
                raise AssertionError('Other selection changed')
            if db.execute('pragma foreign_key_check').fetchall():
                raise AssertionError('Foreign key check failed')
            db.commit()
        except BaseException:
            db.rollback()
            raise
    result['status'] = 'APPLIED'
    manifest = FIXTURE / ('female-deity-' + stamp + '.json')
    with manifest.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=True, indent=2)
    result['manifest'] = str(manifest)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=DATABASE)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(configure(args.database, args.apply), ensure_ascii=True, indent=2))
