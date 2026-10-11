"""Import complete native daily316 display rows after migration30.

Runs the pinned native parser/lookup afresh before every import. No progression,
eligibility enforcement, completion, reward or player-state rules are created.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile

from . import current_daily_quest_source_20260927 as native

CATALOG_SHA='df0bc3a96425c3440cd2fefc867840aa10e3ad35c4a3be32e332c6204f30236a'
AUTHORITY='NATIVE_PARSED_DISPLAY_ONLY'
COLUMNS=('ordinal','source_line','pair_index','pair_branch','logical','source_record_sha256',
         'client_sha256','source_sha256','decoded_sha256','catalog_sha256','authority')
SQL_COLUMNS=','.join(COLUMNS)


def pinned_records(client):
    result=native.audit(Path(client))
    native.require(result['parsed_catalog_sha256']==CATALOG_SHA,'Native parsed catalog fingerprint changed')
    rows=[]
    source=[]
    for row in result['rows']:
        raw=b','.join(bytes.fromhex(field) for field in row['raw_fields_hex'])
        logical=bytes.fromhex(row['parsed316_hex'])
        native.require(len(logical)==316 and native.sha(raw)==row['source_record_sha256'],'Native source binding mismatch')
        rows.append((row['ordinal'],row['source_line'],logical[0],logical[1],logical,
            row['source_record_sha256'],native.CLIENT_SHA,native.SOURCE_SHA,native.DECODED_SHA,CATALOG_SHA,AUTHORITY))
        source.append((row['ordinal'],native.SOURCE,native.SOURCE_SHA,native.DECODED_SHA,
            row['source_line'],row['source_record_sha256'],raw,len(row['raw_fields_hex']),'SOURCE_FIELDS_ONLY'))
    native.require(len(rows)==85,'Incomplete native catalog')
    return rows,source


def import_catalog(db,client):
    native.require(not db.in_transaction,'Daily parsed import requires its own transaction')
    rows,source=pinned_records(client)
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('BEGIN IMMEDIATE')
    try:
        read_source=lambda:db.execute('SELECT record_index,source_path,source_sha256,decoded_sha256,source_line,'
            'record_sha256,raw_record,field_count,authority FROM native_daily_quest_source ORDER BY record_index').fetchall()
        native.require(read_source()==source,'Missing, partial or conflicting raw daily source; import source catalog first')
        read=lambda:db.execute('SELECT '+SQL_COLUMNS+' FROM native_daily_quest_parsed ORDER BY ordinal').fetchall()
        before=read()
        native.require(not before or before==rows,'Partial or conflicting parsed daily catalog; refusing overwrite')
        if not before:
            db.executemany('INSERT INTO native_daily_quest_parsed ('+SQL_COLUMNS+') VALUES ('+','.join('?' for _ in COLUMNS)+')',rows)
        native.require(read()==rows,'Daily parsed readback mismatch')
        native.require(read_source()==source,'Raw daily source changed during import')
        native.require(db.execute('PRAGMA quick_check').fetchall()==[('ok',)] and
            not db.execute('PRAGMA foreign_key_check').fetchall(),'Daily parsed database integrity failed')
        db.commit()
        return dict(rows=85,inserted=0 if before else 85,authority=AUTHORITY,catalog_sha256=CATALOG_SHA,
                    executable_quest_rules=0,player_states_created=0)
    except BaseException:
        db.rollback()
        raise


def self_test(client):
    """Disposable memory DB only; actual85 raw and native parsed source rows."""
    rows,source=pinned_records(client)
    # Test schemas model the required column/foreign-key contract; importer does
    # not create or alter production schemas and requires migration30 to exist.
    source_ddl='''CREATE TABLE native_daily_quest_source(
        record_index INTEGER PRIMARY KEY,source_path TEXT,source_sha256 TEXT,decoded_sha256 TEXT,
        source_line INTEGER,record_sha256 TEXT,raw_record BLOB,field_count INTEGER,authority TEXT)'''
    parsed_ddl='''CREATE TABLE native_daily_quest_parsed(
        ordinal INTEGER PRIMARY KEY REFERENCES native_daily_quest_source(record_index),
        source_line INTEGER,pair_index INTEGER,pair_branch INTEGER,logical BLOB CHECK(length(logical)=316),
        source_record_sha256 TEXT,client_sha256 TEXT,source_sha256 TEXT,decoded_sha256 TEXT,
        catalog_sha256 TEXT,authority TEXT)'''
    def fixture():
        db=sqlite3.connect(':memory:')
        db.execute(source_ddl);db.execute(parsed_ddl)
        db.executemany('INSERT INTO native_daily_quest_source VALUES(?,?,?,?,?,?,?,?,?)',source);db.commit()
        return db
    def snapshot(db):return list(db.iterdump())
    def rejects(db):
        before=snapshot(db)
        try:import_catalog(db,client)
        except (ValueError,sqlite3.DatabaseError):pass
        else:raise ValueError('Negative import unexpectedly succeeded')
        native.require(snapshot(db)==before,'Failed import changed database')
    cases=[]
    with closing(fixture()) as db:
        native.require(import_catalog(db,client)['inserted']==85,'Fresh import failed')
        native.require(import_catalog(db,client)['inserted']==0,'Repeat import not idempotent')
        native.require(db.execute('SELECT '+SQL_COLUMNS+' FROM native_daily_quest_parsed ORDER BY ordinal').fetchall()==rows,'Test readback mismatch')
        cases.extend(['fresh85','idempotent85','exact_readback'])
        db.execute('DELETE FROM native_daily_quest_parsed WHERE ordinal=84');db.commit();rejects(db);cases.append('partial_rejected_unchanged')
    for name,sql in (
        ('raw_source_corruption',"UPDATE native_daily_quest_source SET raw_record=X'30' WHERE record_index=0"),
        ('raw_source_missing','DELETE FROM native_daily_quest_source WHERE record_index=84'),
        ('raw_authority',"UPDATE native_daily_quest_source SET authority='OTHER' WHERE record_index=0"),
        ('encoder_readback_trigger',"CREATE TRIGGER corrupt AFTER INSERT ON native_daily_quest_parsed BEGIN UPDATE native_daily_quest_parsed SET pair_index=255 WHERE ordinal=NEW.ordinal; END"),
        ('abort_trigger',"CREATE TRIGGER deny BEFORE INSERT ON native_daily_quest_parsed WHEN NEW.ordinal=84 BEGIN SELECT RAISE(ABORT,'test'); END")):
        with closing(fixture()) as db:
            db.execute(sql);db.commit();rejects(db);cases.append(name+'_rejected_unchanged')
    with closing(fixture()) as db:
        db.executemany('INSERT INTO native_daily_quest_parsed VALUES('+','.join('?' for _ in COLUMNS)+')',rows)
        db.execute("UPDATE native_daily_quest_parsed SET logical=zeroblob(316) WHERE ordinal=0")
        db.commit();rejects(db);cases.append('parsed_conflict_rejected_unchanged')
    with closing(fixture()) as db, tempfile.TemporaryDirectory(prefix='god2-daily-identity-') as directory:
        wrong=Path(directory);(wrong/'God2.exe').write_bytes(b'not-the-current-client')
        before=snapshot(db)
        try:import_catalog(db,wrong)
        except ValueError:pass
        else:raise ValueError('Wrong client identity unexpectedly accepted')
        native.require(snapshot(db)==before and not db.in_transaction,'Wrong identity changed database')
        cases.append('wrong_client_rejected_before_transaction')
    with closing(fixture()) as db:
        db.execute('PRAGMA query_only=ON');rejects(db);cases.append('read_only_rejected')
    with closing(fixture()) as db:
        db.execute('BEGIN');before=snapshot(db)
        try:import_catalog(db,client)
        except ValueError:pass
        else:raise ValueError('Borrowed transaction unexpectedly accepted')
        native.require(db.in_transaction and snapshot(db)==before,'Caller transaction changed')
        db.rollback();cases.append('caller_transaction_preserved')
    return dict(status='PASS',cases=cases,catalog_sha256=CATALOG_SHA)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',type=Path,default=native.ROOT.parent/'God2')
    parser.add_argument('--database',type=Path)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        native.require(args.database is None,'Self-test never accepts a database path')
        print(json.dumps(self_test(args.client)));return
    native.require(args.database is not None,'--database or --self-test required')
    path=args.database.resolve()
    native.require(path.is_file() and not path.is_relative_to(args.client.resolve()),'Expected existing database outside client tree')
    with closing(sqlite3.connect(path.as_uri()+'?mode=rw',uri=True)) as db:
        print(json.dumps(import_catalog(db,args.client)))


if __name__=='__main__':main()
