"""Release risk tests. Temp SQLite/files only; no servers, UI, or managed saves."""
from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.operations import owned_guild_release_v02_20261004 as release


def fixture(path):
    with closing(sqlite3.connect(path)) as db:
        db.executescript('''
CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY,name TEXT,sql_text TEXT,applied_at TEXT,unknown_history BLOB);
CREATE TABLE accounts(id INTEGER PRIMARY KEY AUTOINCREMENT,unknown_account TEXT);
CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY,account_id INTEGER REFERENCES accounts(id));
CREATE TABLE owned_guilds(id INTEGER PRIMARY KEY,name_utf8 TEXT);
CREATE TABLE unknown_save(id INTEGER PRIMARY KEY,cell,blob BLOB,extra TEXT);
CREATE INDEX unknown_save_index ON unknown_save(extra);
INSERT INTO accounts(id,unknown_account) VALUES(1,'existing玩家');
INSERT INTO recovered_characters VALUES(1,1);
INSERT INTO unknown_save VALUES(1,17,X'00FF','int');
INSERT INTO unknown_save VALUES(2,'17',X'00FF','text');
INSERT INTO unknown_save VALUES(3,17.5,X'0001','float');
INSERT INTO unknown_save VALUES(4,NULL,X'','null');
INSERT INTO unknown_save VALUES(5,X'3137',NULL,'blob');
PRAGMA user_version=7;
PRAGMA application_id=271828;
''')
        db.executemany('INSERT INTO schema_migrations VALUES(?,?,?,?,?)',
                       [(i, 'migration-' + str(i), 'exact SQL ' + str(i), 'unchanged-time', bytes([i])) for i in range(1,49)])
        db.commit()


def migrate_fixture(path, sql, inject_failure=False):
    # Real SQLite DDL/history atomicity, explicit transaction; no binary execution.
    with closing(sqlite3.connect(path)) as db:
        try:
            db.executescript('BEGIN IMMEDIATE;\n' + sql)
            db.execute('INSERT INTO schema_migrations(version,name,sql_text,applied_at) VALUES(49,?,?,?)',
                       (release.MIGRATION_NAME, sql, 'new-time'))
            if inject_failure:
                db.execute('INSERT INTO nonexistent_release_failure VALUES(1)')
            db.commit()
        except BaseException:
            db.rollback()
            raise


class MigrationRiskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='guild-release-risk-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'clone.db'
        fixture(self.path)
        self.sql = release.migration_sql()
        self.before = release.capture(self.path)

    def migrate(self):
        migrate_fixture(self.path, self.sql)
        return release.capture(self.path)

    def test_exact_addition_preserves_every_storage_type_unknown_schema_and_history(self):
        after = self.migrate()
        release.require49(self.before, after, self.sql)
        self.assertEqual(after['history48_typed'], self.before['history48_typed'])
        self.assertEqual(after['tables']['unknown_save'], self.before['tables']['unknown_save'])

    def test_real_ddl_and_history_failure_roll_back_without_backup_restore(self):
        with self.assertRaises(sqlite3.OperationalError):
            migrate_fixture(self.path, self.sql, inject_failure=True)
        self.assertEqual(release.capture(self.path), self.before)

    def test_modified_player_row_is_rejected(self):
        self.migrate()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE accounts SET unknown_account='lost save' WHERE id=1")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'Saved typed rows changed: accounts'):
            release.require49(self.before, release.capture(self.path), self.sql)

    def test_integer_to_text_is_not_treated_as_same_value(self):
        self.migrate()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE unknown_save SET cell='17' WHERE id=1")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'Saved typed rows changed: unknown_save'):
            release.require49(self.before, release.capture(self.path), self.sql)

    def test_unchanged_known_history_cannot_hide_unknown_history_column_change(self):
        self.migrate()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE schema_migrations SET unknown_history=X'FFFF' WHERE version=1")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'Old typed migration rows'):
            release.require49(self.before, release.capture(self.path), self.sql)

    def test_additional_index_is_rejected(self):
        self.migrate()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('CREATE INDEX unexpected ON owned_guild_governance_0078(owner_account)')
            db.commit()
        with self.assertRaisesRegex(ValueError, 'DDL/index differs'):
            release.require49(self.before, release.capture(self.path), self.sql)

    def test_modified_migration_sql_history_is_rejected(self):
        self.migrate()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE schema_migrations SET sql_text=sql_text||' ' WHERE version=49")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'identity/SQL differs'):
            release.require49(self.before, release.capture(self.path), self.sql)

    def test_install_uses_fresh_baseline_not_early_stage_save(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE accounts SET unknown_account='new player save after stage' WHERE id=1")
            db.commit()
        fresh = release.capture(self.path)
        after = self.migrate()
        release.require49(fresh, after, self.sql)
        with self.assertRaisesRegex(ValueError, 'Saved typed rows changed: accounts'):
            release.require49(self.before, after, self.sql)

    def test_nonempty49_never_qualifies_as_empty_install_or48_downgrade(self):
        self.migrate()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO owned_guilds VALUES(1,'existing guild')")
            db.execute('INSERT INTO owned_guild_governance_0078 VALUES(1,1,1,1,50000,20,?,?,?)',
                       ('CUSTOM_DESIGNED','CUSTOM-0078','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'))
            db.commit()
        with self.assertRaises(ValueError):
            release.require48(release.capture(self.path))
        with self.assertRaises(ValueError):
            release.require49(self.before, release.capture(self.path), self.sql)

    def test_backup_is_new_file_and_rejects_overwrite_or_self_target(self):
        new = self.path.with_name('fresh-backup.db')
        release.backup_new(self.path, new)
        self.assertEqual(release.capture(new), self.before)
        for target in (new,self.path):
            with self.assertRaises(ValueError):
                release.backup_new(self.path,target)


class ResourceAndCodeRiskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='guild-release-files-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.items = []
        for index in range(2):
            target, source = self.root / f'working-{index}', self.root / f'qualified-{index}'
            target.write_bytes(b'original-language-' + bytes([index]))
            source.write_bytes(b'new-language-' + bytes([index]))
            self.items.append((target,source,release.sha(target),release.sha(source)))

    def test_second_resource_replace_failure_restores_both_originals(self):
        calls = []
        def fault(source,target):
            calls.append(target)
            if len(calls) == 2:
                raise OSError('simulated second language sharing violation')
            Path(source).replace(target)
        with self.assertRaisesRegex(OSError, 'sharing violation'):
            release.install_pair(self.items, replace=fault)
        self.assertEqual(len(calls),2)
        self.assertTrue(all(release.sha(target)==old for target,_,old,_ in self.items))
        self.assertFalse(list(self.root.glob('owned-guild-*')))

    def test_wrong_source_pin_rejects_before_first_resource_change(self):
        self.items[1][1].write_bytes(b'changed source')
        with self.assertRaisesRegex(ValueError, 'pin differs'):
            release.install_pair(self.items)
        self.assertTrue(all(release.sha(target)==old for target,_,old,_ in self.items))

    def test_success_installs_both_exact_hashes(self):
        release.install_pair(self.items)
        self.assertTrue(all(release.sha(target)==new for target,_,_,new in self.items))

    def test_changed_candidate_rejected_even_with_accepted_design(self):
        binary=self.root/'candidate.exe';binary.write_bytes(b'candidate-v1')
        contract=self.root/'contract.json'
        contract.write_text(json.dumps({'design':'CUSTOM-0078','candidate_path':str(binary),
                                       'candidate_sha256':release.sha(binary)}))
        binary.write_bytes(b'candidate-v2')
        with self.assertRaisesRegex(ValueError, 'Candidate code differs'):
            release.validate_contract(contract,binary)

    def test_lab_receipt_cannot_qualify_formal_release(self):
        receipt = release.read(release.ROOT/'artifacts/playtests/ge-20261004-02/run-result.json')
        contract = release.read(release.ROOT/'artifacts/research/native-guild-membership-0078/general-entry-live-v01/contract-v02.json')
        with self.assertRaisesRegex(ValueError, 'formal_config'):
            release.validate_receipt(receipt,contract,receipt['contract_sha256'])

    def test_formal_receipt_cannot_bind_different_contract(self):
        receipt={'accepted':True,'formal_config':True,'env_lab_false':True,
                 'candidate_unchanged':True,'protected_files_unchanged':True,'protected_DB_exact':True,
                 'frozen_unchanged':True,'protected_processes_exact':True,'desktop_unchanged':True,
                 'foreground_unchanged':True,'contract_sha256':'one'}
        with self.assertRaisesRegex(ValueError, 'contract binding differs'):
            release.validate_receipt(receipt,{},'different')

    def test_disabled_config_preserves_all_existing_settings(self):
        original={'world':{'existing':{'nested':9}},'database':{'path':'save'},'unknown':[1,2]}
        after=release.entry_config(original,False)
        self.assertEqual(original,{'world':{'existing':{'nested':9}},'database':{'path':'save'},'unknown':[1,2]})
        self.assertEqual(after['world']['existing'],original['world']['existing'])
        self.assertEqual(after['world']['owned_guild_membership'],{'enabled':False,'entry_resource_bundle':release.BUNDLE})


class FormalReceiptRiskTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='guild-receipt-risk-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config_path=self.root/'formal.json'
        self.source={'server':{'host':'127.0.0.1','port':2592,'character_port':0},
            'database':{'type':'sqlite','path':'original-save.db'},'logging':{'file':'original.log'},
            'development':{'diagnostic_remote_actor_language':0,'battle':True},
            'world':{'mock':False,'unknown':{'flag':True}}}
        self.config_path.write_text(json.dumps(self.source),encoding='utf-8')
        self.contract={'source_sha256':{'formal.json':release.sha(self.config_path)}}
        self.receipt={key:True for key in ('accepted','formal_config','env_lab_false','candidate_unchanged',
            'protected_files_unchanged','protected_DB_exact','frozen_unchanged','protected_processes_exact',
            'desktop_unchanged','foreground_unchanged')}
        self.receipt.update(contract_sha256='contract',sources_before=self.contract['source_sha256'],
            sources_after=self.contract['source_sha256'],cases=[])
        for before,after in (('files_before','files_after'),('frozen_before','frozen_after'),
            ('protected_DB_before','protected_DB_after'),('protected_processes_before','protected_processes_after')):
            self.receipt[before]={'preserved':'exact'};self.receipt[after]={'preserved':'exact'}
        for locale in (950,936):
            private=self.root/str(locale)/'server-config.json'
            actual=deepcopy(self.source)
            actual['database']['path']=str(private.with_name('town-diagnostic-accounts.db'))
            actual['logging']['file']=str(private.with_name('server.log'))
            actual['server'].update(host='127.0.0.1',port=2598,character_port=0)
            actual['development']['diagnostic_remote_actor_language']=int(locale==936)
            actual['world']['owned_guild_membership']={'enabled':True,'entry_resource_bundle':release.BUNDLE}
            proof={'accepted':True,'all_other_gameplay_flags_preserved':True,'source_path':str(self.config_path),
                'source_sha256':release.sha(self.config_path),'private_path':str(private),
                'source':deepcopy(self.source),'actual':actual}
            ui={key:True for key in ('accepted','env_lab_false','ordinary_paired_entry_accepted',
                'desktop_unchanged','all_clients_closed','all_loaders_closed')}
            ui.update(locale=locale,formal_config_proof=deepcopy(proof),ordinary_menu_events=[{}],
                native_loaded_resource_proof={'original2995_all_rows_byte_exact':True,'VM_READ_only':True,
                    'count':2996,'locale':locale,'new2996_rows':{'rows_hex':['a','b','c','d']}})
            for name in ('real_create','real_pending_application','real_native_71_approve','real_native_72_reject'):
                ui[name]={'accepted':True}
            ui['ordinary_member_leave_events']=[{key:True for key in ('accepted','cancel_SQL_exact',
                'owner_only_membership_deleted','pending6_exact','governance_exact','all_unrelated_tables_exact',
                'native_2D_name_empty','all_panels_closed')}]
            case={key:True for key in ('accepted','formal_config','env_lab_false','private_files_unchanged',
                'all_private_images_closed','all_owned_processes_closed','exclusive_2598_released')}
            case.update(locale=locale,runner_exit=0,ui=ui,formal_config_proof=proof,
                runtime_configured_log='OWNED_GUILD_RUNTIME enabled=true ordinary_entry=true lab=false schema=49 CUSTOM-0078',
                environment_proof={name:{key:None for key in release.LAB_ENV}
                    for name in ('launch_lab_values','observed_server_lab_values')})
            self.receipt['cases'].append(case)

    def validate(self,receipt):
        with patch.object(release,'ROOT',self.root),patch.object(release.managed,'CONFIG',self.config_path):
            return release.validate_receipt(receipt,self.contract,'contract')

    def test_exact_formal_receipt_accepts_both_locales(self):
        self.assertIs(self.validate(self.receipt),self.receipt)

    def test_each_formal_case_requires_real_config_runtime_and_environment_evidence(self):
        mutations={
            'case_formal_flag':lambda c:c.update(formal_config=1),
            'case_env_flag':lambda c:c.update(env_lab_false=False),
            'ui_env_flag':lambda c:c['ui'].update(env_lab_false=1),
            'runtime_lab':lambda c:c.update(runtime_configured_log='OWNED_GUILD_RUNTIME enabled=true ordinary_entry=true lab=true schema=49 CUSTOM-0078'),
            'runtime_schema':lambda c:c.update(runtime_configured_log='OWNED_GUILD_RUNTIME enabled=true ordinary_entry=true lab=false schema=48 CUSTOM-0078'),
            'proof_acceptance':lambda c:c['formal_config_proof'].update(accepted=1),
            'proof_preservation':lambda c:c['formal_config_proof'].update(all_other_gameplay_flags_preserved=False),
            'source_pin':lambda c:c['formal_config_proof'].update(source_sha256='changed'),
            'source_object':lambda c:c['formal_config_proof']['source']['development'].update(battle=False),
            'gameplay_change':lambda c:c['formal_config_proof']['actual']['development'].update(battle=False),
            'gameplay_type':lambda c:c['formal_config_proof']['actual']['development'].update(battle=1),
            'wrong_bundle':lambda c:c['formal_config_proof']['actual']['world']['owned_guild_membership'].update(entry_resource_bundle='wrong'),
            'enabled_integer':lambda c:c['formal_config_proof']['actual']['world']['owned_guild_membership'].update(enabled=1),
            'unknown_node':lambda c:c['formal_config_proof']['actual']['world']['owned_guild_membership'].update(extra=True),
            'wrong_locale':lambda c:c['formal_config_proof']['actual']['development'].update(diagnostic_remote_actor_language=2),
            'wrong_private_DB':lambda c:c['formal_config_proof']['actual']['database'].update(path='foreign.db'),
            'missing_launch_key':lambda c:c['environment_proof']['launch_lab_values'].pop(release.LAB_ENV[0]),
            'lab_launch_value':lambda c:c['environment_proof']['launch_lab_values'].update({release.LAB_ENV[1]:'0'}),
            'lab_observed_value':lambda c:c['environment_proof']['observed_server_lab_values'].update({release.LAB_ENV[2]:'1'}),
            'different_UI_proof':lambda c:c['ui']['formal_config_proof']['actual']['world'].update(mock=True),
        }
        for index in (0,1):
            for name,mutate in mutations.items():
                with self.subTest(locale=self.receipt['cases'][index]['locale'],mutation=name):
                    receipt=deepcopy(self.receipt);mutate(receipt['cases'][index])
                    with self.assertRaises(ValueError):self.validate(receipt)


class ApplyRecoveryRiskTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='guild-apply-risk-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.directory=self.root/'release';self.directory.mkdir()
        self.active=self.root/'active.exe';self.active.write_bytes(b'original48')
        self.candidate=self.directory/'god2-server.candidate.exe';self.candidate.write_bytes(b'qualified49')
        self.client=self.root/'client.exe';self.client.write_bytes(b'unchanged client')
        self.database=self.root/'save.db';fixture(self.database);self.before=release.capture(self.database)
        self.config={'server':{'host':'127.0.0.1','port':2592,'character_port':0},
            'database':{'type':'sqlite','path':str(self.database)},'world':{'existing':True},
            'logging':{'file':str(self.root/'server.log')}}
        self.config_path=self.root/'server-config.json';self.config_path.write_text(json.dumps(self.config),encoding='utf-8')
        self.info={'old_server_sha256':release.sha(self.active),'candidate_sha256':release.sha(self.candidate),
            'config_sha256':release.sha(self.config_path),'database':str(self.database.resolve()),
            'resources':[],'client_sha256':release.sha(self.client),'frozen_chat':{},'contract_sha256':'contract'}
        self.args=SimpleNamespace(execute=True,release=str(self.directory),receipt=str(self.root/'unused-receipt.json'))
        for obj,name,value in ((release.managed,'ACTIVE',self.active),(release.managed,'CONFIG',self.config_path),
            (release.managed,'CLIENT',self.client)):
            p=patch.object(obj,name,value);p.start();self.addCleanup(p.stop)
        mocks=((release,'qualify_stage'),(release,'assert_formal_environment'),(release,'assert_clients_closed'),
            (release.managed_links,'managed_listener'),(release.managed_links,'stop_idle'),
            (release.managed_links,'process_guard_script'),(release.managed_links,'wait_listener'),
            (release.managed,'powershell'),(release.managed,'start'),(release,'install_pair'),(release,'freeze_gate'))
        self.mocks={}
        for obj,name in mocks:
            p=patch.object(obj,name);self.mocks[name]=p.start();self.addCleanup(p.stop)
        self.mocks['qualify_stage'].return_value=(self.info,self.config,self.database,{}, {})
        self.mocks['managed_listener'].return_value=17
        self.mocks['process_guard_script'].return_value='TEST_ONLY_NO_PROCESS_OPERATIONS;'
        self.mocks['wait_listener'].return_value=23
        self.mocks['freeze_gate'].return_value={}
        p=patch.object(release.managed_links,'install_binary',side_effect=lambda source,expected:self.active.write_bytes(Path(source).read_bytes()))
        p.start();self.addCleanup(p.stop)

    def failed(self):
        return release.read(self.directory/'apply-failed.json')

    def test_prestart_failure_changed_candidate_never_restarts(self):
        def fault(*args):
            self.active.write_bytes(b'unqualified replacement');raise OSError('migration failure')
        with patch.object(release,'migrate',side_effect=fault),self.assertRaisesRegex(OSError,'migration failure'):
            release.apply(self.args)
        self.mocks['start'].assert_not_called()
        self.assertIn('executable pin differs',self.failed()['recovery_error'])
        self.assertFalse(self.failed()['service_restarted'])
        self.assertTrue(self.failed()['manual_forward_repair_required'])
        self.assertEqual(release.capture(self.database),self.before)

    def test_prestart_failure_exact_candidate_and_disabled_config_can_restore_availability(self):
        with patch.object(release,'migrate',side_effect=OSError('migration failure')),self.assertRaises(OSError):
            release.apply(self.args)
        self.mocks['start'].assert_called_once()
        self.assertTrue(self.failed()['entry_disabled_runtime'])
        self.assertTrue(self.failed()['service_restarted'])
        self.assertEqual(release.read(self.config_path),release.entry_config(self.config,False))
        self.assertEqual(release.capture(self.database),self.before)

    def test_recovery_config_drift_and_changed_save_path_never_restart(self):
        # Separate apply attempts are required by the irreversible attempt marker.
        original_atomic=release.atomic_config
        for variant in ('unrelated_flag','save_path'):
            with self.subTest(variant=variant):
                attempt=self.root/variant;attempt.mkdir();self.args.release=str(attempt)
                (attempt/'god2-server.candidate.exe').write_bytes(b'qualified49')
                self.active.write_bytes(b'original48');self.config_path.write_text(json.dumps(self.config),encoding='utf-8')
                calls=[]
                def drift(path,value):
                    calls.append(path);changed=deepcopy(value)
                    if len(calls)==2:
                        if variant=='unrelated_flag':changed['world']['existing']=False
                        else:
                            other=self.root/'foreign.db'
                            if not other.exists():fixture(other)
                            changed['database']['path']=str(other)
                    original_atomic(path,changed)
                with patch.object(release,'migrate',side_effect=OSError('migration failure')),\
                    patch.object(release,'atomic_config',side_effect=drift),self.assertRaises(OSError):
                    release.apply(self.args)
                self.mocks['start'].assert_not_called()
                failure=release.read(attempt/'apply-failed.json')
                self.assertIn('config differs',failure['recovery_error'])
                self.assertFalse(failure['service_restarted'])
                self.assertEqual(release.capture(self.database),self.before)

    def test_stop_then_preinstall_failure_can_restart_only_unchanged48(self):
        with patch.object(release,'backup_new',side_effect=OSError('fresh backup failure')),self.assertRaises(OSError):
            release.apply(self.args)
        self.mocks['start'].assert_called_once()
        self.assertFalse(self.failed()['candidate_retained'])
        self.assertTrue(self.failed()['service_restarted'])
        self.assertEqual(release.sha(self.active),self.info['old_server_sha256'])
        self.assertEqual(release.capture(self.database),self.before)

    def test_poststart_failure_without_owned_listener_rechecks_candidate_before_second_start(self):
        sql=release.migration_sql()
        template_db=self.root/'template.db';fixture(template_db);migrate_fixture(template_db,sql)
        template=release.capture(template_db)
        self.mocks['qualify_stage'].return_value=(self.info,self.config,self.database,template,{})
        self.mocks['managed_listener'].side_effect=[17,ValueError('no owned listener')]
        def listener_failure():
            self.active.write_bytes(b'unqualified after start');raise ValueError('startup failure')
        self.mocks['wait_listener'].side_effect=listener_failure
        with patch.object(release,'migrate',side_effect=lambda *args:migrate_fixture(self.database,sql)),\
            self.assertRaisesRegex(ValueError,'startup failure'):
            release.apply(self.args)
        self.mocks['start'].assert_called_once() # first launch only; no unqualified recovery launch
        self.assertIn('executable pin differs',self.failed()['recovery_error'])
        self.assertFalse(self.failed()['service_restarted'])
        release.require49(self.before,release.capture(self.database),sql)


class StageConfigCompatibilityRiskTests(unittest.TestCase):
    def test_stage_required_basename_preserves_formal_flags_and_binds_v02_tool(self):
        with tempfile.TemporaryDirectory(prefix='guild-stage-v02-risk-') as temporary:
            directory=Path(temporary);database=directory/'formal-save.db';fixture(database)
            original={'server':{'host':'127.0.0.1','port':2592,'character_port':0},
                'database':{'type':'sqlite','path':str(database)},'logging':{'file':'original.log'},
                'development':{'diagnostic_town':True,'diagnostic_town_battle_after_quest':True,
                    'diagnostic_clock':True},'world':{'unchanged':'flag'}}
            config=directory/'formal.json';config.write_text(json.dumps(original),encoding='utf-8')
            active=directory/'active.exe';active.write_bytes(b'original48')
            candidate=directory/'candidate.exe';candidate.write_bytes(b'qualified49')
            client=directory/'client.exe';client.write_bytes(b'protected client')
            contract=directory/'contract.json';contract.write_text('{}',encoding='utf-8')
            items=[]
            for index in (0,1):
                target=directory/f'language{index}';target.write_bytes(b'original'+bytes([index]))
                replacement=directory/f'newlanguage{index}';replacement.write_bytes(b'qualified'+bytes([index]))
                items.append((target,replacement,release.sha(target),release.sha(replacement)))
            output=directory/'stage'
            args=SimpleNamespace(candidate=str(candidate),contract=str(contract),receipt=None,release=str(output))
            migration_configs=[]
            def migrate_only(binary,path,log):
                actual=release.read(path);migration_configs.append(actual)
                clone=Path(actual['database']['path'])
                self.assertEqual(clone,output/'town-diagnostic-accounts.db')
                expected=release.entry_config(original,False)
                expected['database']['path']=str(clone)
                expected['logging']['file']=str(output/'stage-server.log')
                self.assertTrue(release.exact_json(actual,expected))
                # Exercise actual SQLite migration and repeat preservation;
                # this fixture does not claim a real Config::load or binary launch.
                if len(release.capture(clone)['history'])==48:migrate_fixture(clone,release.migration_sql())
            with patch.object(release.managed,'ACTIVE',active),patch.object(release.managed,'CONFIG',config),\
                patch.object(release.managed,'CLIENT',client),\
                patch.object(release,'qualify_inputs',return_value=(candidate,contract,{},None)),\
                patch.object(release,'configured_database',return_value=(original,database)),\
                patch.object(release,'freeze_gate',return_value={'unchanged':True}),\
                patch.object(release,'resource_items',return_value=items),\
                patch.object(release,'migrate',side_effect=migrate_only):
                manifest=release.stage(args)
                self.assertEqual(len(migration_configs),2)
                self.assertFalse((output/'stage-migration.db').exists())
                self.assertEqual(manifest['release_tool_path'],str(Path(release.__file__).resolve()))
                self.assertEqual(manifest['release_tool_sha256'],release.sha(release.__file__))
                release.qualify_stage(args)
                for field in ('release_tool_path','release_tool_sha256'):
                    with self.subTest(manifest_field=field):
                        tampered=deepcopy(manifest);tampered[field]='unqualified'
                        (output/'manifest.json').write_text(json.dumps(tampered),encoding='utf-8')
                        with self.assertRaisesRegex(ValueError,'release tool identity changed'):
                            release.qualify_stage(args)
                self.assertEqual(release.capture(database)['history48_typed'],
                    release.capture(output/'stage-before.db')['history48_typed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
