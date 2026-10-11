"""Copy an already qualified native catalog into a disposable test database."""
from contextlib import closing
import hashlib,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'artifacts/playtests/private-owned-supply-20260927-04/town-diagnostic-accounts.db'
def copy_catalog(target):
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with closing(sqlite3.connect(SOURCE.resolve().as_uri()+'?mode=ro',uri=True)) as source:
        sources=source.execute("SELECT * FROM native_data_sources WHERE dataset_id='current-med02-recovery-v1'").fetchall()
        rows=source.execute('SELECT * FROM native_med02_recovery_declarations ORDER BY source_record_index').fetchall()
    if len(sources)!=1 or len(rows)!=71:raise ValueError('Qualified fixture MED02 catalog absent')
    if target.in_transaction:raise ValueError('Fixture catalog requires fresh transaction')
    target.execute('BEGIN IMMEDIATE')
    try:
        target.execute("DELETE FROM native_med02_recovery_declarations WHERE dataset_id='current-med02-recovery-v1'")
        target.execute("DELETE FROM native_data_sources WHERE dataset_id='current-med02-recovery-v1'")
        target.executemany('INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)',sources)
        target.executemany('INSERT INTO native_med02_recovery_declarations VALUES(?,?,?,?,?,?,?,?,?,?,?)',rows)
        target.commit()
    except BaseException:target.rollback();raise
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=before:raise ValueError('Catalog fixture changed')
    # The candidate validates all 71 rows against its pinned full catalog digest.
    return {'source':str(SOURCE),'sha256':before,'rows':len(rows)}
