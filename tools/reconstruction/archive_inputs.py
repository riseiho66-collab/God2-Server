"""Read selected retained native evidence without restoring historical trees."""
import hashlib
import os
import sqlite3
import zlib
from pathlib import Path

SERVER = Path(__file__).resolve().parents[2]
PROJECT = SERVER.parent
ARCHIVE = PROJECT / 'artifacts/歷史精簡封存_20261006'

class ArchivedInputs:
    def __init__(self):
        self.db = sqlite3.connect((ARCHIVE / 'manifest.sqlite').as_uri() + '?mode=ro', uri=True)
        self.db.execute('PRAGMA query_only=ON')
        if self.db.execute("SELECT value FROM metadata WHERE key='verified'").fetchone() != ('true',):
            raise RuntimeError('Native evidence archive is not finalized')

    def close(self):
        self.db.close()

    def read(self, server_relative, *, limit=32_000_000):
        rel = Path(server_relative)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Server-relative evidence path required')
        target = (SERVER / rel).resolve()
        if not target.is_relative_to(SERVER):
            raise ValueError('Evidence path escapes server')
        if target.is_file():
            if target.stat().st_size > limit:
                raise ValueError('Evidence exceeds bounded reader size')
            return target.read_bytes()
        key = str(Path(SERVER.name) / rel)
        row = self.db.execute('SELECT size,mtime,sha FROM files WHERE path=?', (key,)).fetchone()
        if row is None:
            raise FileNotFoundError(server_relative)
        size, mtime, pin = row
        if size > limit:
            raise ValueError('Archived evidence exceeds bounded reader size')
        blob = self.db.execute('SELECT pack,offset,length,size FROM blobs WHERE sha=?', (pin,)).fetchone()
        pack, offset, length, expected = blob
        packpath = (ARCHIVE / pack).resolve()
        if not packpath.is_relative_to(ARCHIVE):
            raise ValueError('Invalid evidence pack path')
        with packpath.open('rb') as source:
            source.seek(offset)
            raw = zlib.decompress(source.read(length))
        if len(raw) != size or size != expected or hashlib.sha256(raw).hexdigest() != pin:
            raise ValueError('Archived evidence content differs')
        return raw

    def materialize(self, names, *, byte_limit=32_000_000):
        selected = []
        for name in names:
            rel = Path(name)
            target = (SERVER / rel).resolve()
            if not target.is_relative_to(SERVER / 'artifacts'):
                raise ValueError('Only archived artifact inputs may be restored')
            if target.exists():
                continue
            raw = self.read(name)
            selected.append((target, raw))
        if sum(len(raw) for _, raw in selected) > byte_limit:
            raise ValueError('Selective recovery exceeds its byte budget')
        for target, raw in selected:
            for parent in target.parents:
                if parent.exists() and (parent.is_symlink() or getattr(parent.stat(), 'st_file_attributes', 0) & 0x400):
                    raise ValueError('Recovery destination contains a reparse point')
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(raw)
        return {'files': len(selected), 'bytes': sum(len(raw) for _, raw in selected)}
