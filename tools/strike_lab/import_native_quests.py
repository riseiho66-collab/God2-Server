"""Pinned Mission_data display catalog only; no quest conditions or rewards."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import uuid

from .recover_quests import build_catalog
from .import_native_catalog import configured_database

ROOT = Path(__file__).resolve().parents[2]
DATASET = 'current-quest-descriptions-v1'
SOURCE_SHA = '659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716'
DECODED_SHA = 'f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCE_ROW = (DATASET, 'Data2/Patch/Comm/Mission_data.csvZ', SOURCE_SHA,
              DECODED_SHA, IMAGE_SHA, 'Mission_data', '0x584ae', '0xc9581', 418)


def pinned_records(client):
    catalog = build_catalog(Path(client))
    table = catalog['tables']['missions']
    if (table['source_sha256'], table['decoded_sha256']) != (SOURCE_SHA, DECODED_SHA):
        raise ValueError('Mission_data source changed')
    if catalog['validation']['structural_issues'] or len(catalog['quests']) != 418:
        raise ValueError('Invalid mission structure')
    lines = {row['source_line']: row for row in table['records']}
    rows = []
    for index, mission in enumerate(catalog['quests'], 1):
        texts = mission['objectives_text']
        if mission['id'] != index or not 1 <= len(texts) <= 32767 or mission['step_field'] != len(texts):
            raise ValueError('Mission display index/count mismatch')
        for description, text in enumerate(texts):
            if text['step'] != description + 1:
                raise ValueError('Mission description order changed')
            source = lines[text['source_line']]
            raw = b','.join(bytes.fromhex(field) for field in source['raw_fields_hex'])
            digest = hashlib.sha256(raw).hexdigest()
            if digest != source['source_record_sha256']:
                raise ValueError('Mission source row hash mismatch')
            rows.append((DATASET,index,description,len(texts),text['source_line'],digest,raw))
    if len(rows) != 2014:
        raise ValueError('Mission description count changed')
    return rows


def import_catalog(db, client):
    rows = pinned_records(client)
    if db.in_transaction:
        raise ValueError('Quest import requires its own transaction')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute('SELECT name FROM schema_migrations WHERE version=14').fetchall() != [('native_quest_descriptions',)]:
            raise ValueError('Apply native quest migration first')
        source = db.execute('SELECT * FROM native_data_sources WHERE dataset_id=?',(DATASET,)).fetchall()
        stored = db.execute('SELECT * FROM native_quest_descriptions WHERE dataset_id=? ORDER BY mission_index,description_index',(DATASET,)).fetchall()
        if source:
            if source != [SOURCE_ROW] or stored != rows:
                raise ValueError('Conflicting quest catalog; refusing overwrite')
        else:
            if stored:
                raise ValueError('Orphaned quest catalog')
            db.execute('INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)',SOURCE_ROW)
            db.executemany('INSERT INTO native_quest_descriptions VALUES(?,?,?,?,?,?,?)',rows)
        if db.execute('SELECT * FROM native_quest_descriptions WHERE dataset_id=? ORDER BY mission_index,description_index',(DATASET,)).fetchall() != rows:
            raise ValueError('Quest import readback mismatch')
        if db.execute('PRAGMA foreign_key_check').fetchone() or db.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise ValueError('Database integrity check failed')
        db.commit()
        return dict(dataset=DATASET,missions=418,descriptions=len(rows),inserted=0 if source else len(rows))
    except BaseException:
        db.rollback()
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'config/server.json')
    parser.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    parser.add_argument('--server-exe',type=Path,default=ROOT/'build/Release/god2-server.exe')
    parser.add_argument('--include-requirement-display',action='store_true')
    args=parser.parse_args()
    client=args.client.resolve()
    pinned_records(client)
    if args.include_requirement_display:
        from . import import_native_quest_requirements as requirements
        requirements.native.evidence(client=client)
    database=configured_database(args.config)
    if database.is_relative_to(client) or not database.is_file():
        raise ValueError('Refusing client-tree or nonexistent database')
    backup=ROOT/'artifacts/db-backups'/('native-quests-'+uuid.uuid4().hex+'.sqlite')
    backup.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(database.as_uri()+'?mode=rw',uri=True)) as source:
        with closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
    subprocess.run([str(args.server_exe.resolve()),'--config',str(args.config.resolve()),'--migrate-only'],cwd=ROOT,check=True)
    with closing(sqlite3.connect(database.as_uri()+'?mode=rw',uri=True)) as db:
        result=import_catalog(db,client)
        if args.include_requirement_display:
            result['requirement_display']=requirements.import_catalog(db,client)
    print(json.dumps(dict(result,database=str(database),backup=str(backup))))


if __name__=='__main__':
    main()
