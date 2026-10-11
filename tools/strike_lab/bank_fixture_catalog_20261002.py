"""Verified NPC display catalog copy for disposable bank fixtures only.

The live language overlay may differ from the original pinned csvZ. Preserve
that source gate; use the already qualified release backup, opened read-only.
Display prefixes do not establish an NPC's role or original coordinates.
"""
from contextlib import closing
import hashlib,sqlite3
from . import import_native_npc_display as native

SOURCE=native.ROOT/'artifacts/releases/native-trade-20261002/deployment/accounts.before.db'

def copy_npc_catalog(target):
    before=native.sha(SOURCE.read_bytes())
    with closing(sqlite3.connect(SOURCE.resolve().as_uri()+'?mode=ro',uri=True)) as source:
        sources=source.execute('SELECT * FROM native_npc_display_sources ORDER BY id').fetchall()
        rows=source.execute('SELECT * FROM native_npc_display_rows ORDER BY npc_key').fetchall()
    native.require(sources==[native.source_row()],'NPC fixture source identity')
    native.require(len(rows)==len({r[0] for r in rows})==4043,'NPC fixture count/keys')
    native.require(native.sha(native.canonical(rows))==native.DATASET_SHA,'NPC fixture dataset pin')
    for key,line,offset,digest,raw,prefix in rows:
        native.require(0<key<7000 and line>0 and offset>=0,'NPC fixture row bounds')
        native.require(native.sha(raw)==digest and native.project(raw.split(b','))==prefix,'NPC fixture row/prefix pin')
    native.require(not target.in_transaction,'NPC fixture requires fresh transaction')
    target.execute('BEGIN IMMEDIATE')
    try:
        for sql in native.SCHEMA:target.execute(sql.replace('CREATE TABLE ','CREATE TABLE IF NOT EXISTS ',1))
        stored_sources=target.execute('SELECT * FROM native_npc_display_sources ORDER BY id').fetchall()
        stored_rows=target.execute('SELECT * FROM native_npc_display_rows ORDER BY npc_key').fetchall()
        if not stored_sources and not stored_rows:
            target.executemany('INSERT INTO native_npc_display_sources VALUES(?,?,?,?,?,?,?,?,?,?,?)',sources)
            target.executemany('INSERT INTO native_npc_display_rows VALUES(?,?,?,?,?,?)',rows)
        native.require(target.execute('SELECT * FROM native_npc_display_sources ORDER BY id').fetchall()==sources,'NPC fixture source conflict')
        native.require(target.execute('SELECT * FROM native_npc_display_rows ORDER BY npc_key').fetchall()==rows,'NPC fixture rows conflict')
        native.require(native.sha(SOURCE.read_bytes())==before,'NPC fixture source changed')
        target.commit()
    except BaseException:target.rollback();raise
    return {'source':str(SOURCE),'sha256':before,'rows':4043,'dataset_sha256':native.DATASET_SHA,
            'authority':'SOURCE_DISPLAY_ONLY','player_rows_written':0}
