"""Original skill bytes through formal migration, importer, C++ and Lua."""
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from tools.strike_lab import import_native_skills as catalog
from tools.strike_lab import current_skill_target_setup as targeting


class NativeSkillApplicationTests(unittest.TestCase):
    def test_all_original_records_through_recovered_application(self):
        with tempfile.TemporaryDirectory(prefix='god2-skill-application-') as folder:
            root = Path(folder)
            database = root / 'test.sqlite'
            config_path = root / 'server.json'
            executable = catalog.ROOT / 'build/Release/god2-server.exe'
            config = json.loads((catalog.ROOT / 'config/recovered-world-entry.json').read_text())
            config['database']['path'] = str(database)
            config['server'].update(port=0, character_port=0, worker_threads=1)
            config['logging']['file'] = str(root / 'server.log')
            config['protocol']['packet_dump'] = False
            config_path.write_text(json.dumps(config), encoding='utf-8')
            subprocess.run([str(executable), '--config', str(config_path), '--migrate-only'],
                           cwd=catalog.ROOT, check=True, capture_output=True, timeout=30)
            db = sqlite3.connect(database)
            try:
                db.execute("INSERT INTO accounts(username,password_hash) VALUES('test-only','not-a-login')")
                db.commit()
                accounts = db.execute('SELECT * FROM accounts').fetchall()
                catalog.import_catalog(db, catalog.ROOT.parent / 'God2')
                rows = catalog.pinned_records(catalog.ROOT.parent / 'God2')
                self.assertEqual(len(rows), 448)
                scripts = root / 'scripts'
                scripts.mkdir()
                checks = ['assert(GOD2_FIXTURE_MODE == false)']
                checks.append('local state={masks={0x3fff,0x3fff},saved_masks={0xabcdef01,0x12345678},entity_words={}}; '
                              'for i=1,28 do state.entity_words[i]=false end')
                fields = catalog.SOURCE_COLUMNS.split(',')
                provenance = ' '.join(
                    'assert(r.source.%s==%s);' % (field, json.dumps(value))
                    for field, value in zip(fields, catalog.SOURCE_ROW))
                for _, index, offset, digest, raw, kind, identity in rows:
                    literal = ''.join('\\%03d' % value for value in raw)
                    checks.append(
                        'do local r=native_skill_catalog(%d,%d); assert(r); '
                        'assert(r.kind==%d and r.definition_id==%d); '
                        'assert(r.source_record_index==%d and r.source_offset==%d); '
                        'assert(r.record_sha256=="%s" and r.raw_record=="%s"); '
                        'assert(r.client_mp_threshold==%d); '
                        'assert(r.damage==nil and r.multiplier==nil and r.mp_cost==nil); %s end'
                        % (kind, identity, kind, identity, index, offset, digest, literal,
                           int.from_bytes(raw[0x42:0x44], 'little'), provenance))
                    fields = targeting.Fields.from_record(raw)
                    input_state = targeting.TargetState((0x3fff, 0x3fff), (0xabcdef01, 0x12345678), (None,) * 28)
                    for actor in (0, 13):
                        expected = targeting.target_masks(fields, actor, input_state)
                        setup = (targeting.setup_parameters(fields.mode_45)
                                 if 1 <= fields.mode_45 <= 17 else None)
                        checks.append(
                            'do local r=native_skill_target_setup(%d,%d,%d,state); assert(r); '
                            'assert(r.masks[1]==%d and r.masks[2]==%d); '
                            'assert(r.saved_masks[1]==%d and r.saved_masks[2]==%d); '
                            'assert(r.stored_mode==%d and r.passes_kind_gate==%s); '
                            'assert(r.setup_valid==%s and r.setup_value==%s and r.setup_flag==%s); '
                            'assert(r.record_sha256=="%s" and r.damage==nil and r.cast_allowed==nil); %s end'
                            % (kind, identity, actor, *expected.masks, *expected.saved_masks,
                               expected.stored_mode, str(fields.passes_kind_gate).lower(),
                               str(setup is not None).lower(), str(setup[0]) if setup else 'nil',
                               str(setup[1]) if setup else 'nil', digest, provenance))
                for kind, count in enumerate(catalog.KIND_COUNTS):
                    checks.append('assert(native_skill_catalog(%d,%d)==nil)' % (kind, count + 1))
                checks.append('log("NATIVE_SKILL_ALL_448_VERIFIED")')
                checks.append('assert(state.masks[1]==0x3fff and state.saved_masks[1]==0xabcdef01); '
                              'log("NATIVE_SKILL_TARGET_SETUP_ALL_448_VERIFIED")')
                bootstrap = scripts / 'bootstrap.lua'
                bootstrap.write_text('\n'.join(checks), encoding='ascii')
                config['lua'].update(bootstrap=str(bootstrap), script_root=str(scripts), hot_reload=False)
                config_path.write_text(json.dumps(config), encoding='utf-8')
                result = subprocess.run([str(executable), '--config', str(config_path), '--run-for', '1'],
                                        cwd=catalog.ROOT, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('NATIVE_SKILL_ALL_448_VERIFIED', (root / 'server.log').read_text())
                self.assertIn('NATIVE_SKILL_TARGET_SETUP_ALL_448_VERIFIED', (root / 'server.log').read_text())
                self.assertEqual(db.execute('SELECT * FROM accounts').fetchall(), accounts)
                self.assertEqual(db.execute('SELECT %s FROM native_skill_catalog ORDER BY source_record_index'
                                            % catalog.RECORD_COLUMNS).fetchall(), rows)
                self.assertEqual(db.execute('PRAGMA quick_check').fetchall(), [('ok',)])
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
            finally:
                db.close()


if __name__ == '__main__':
    unittest.main()
