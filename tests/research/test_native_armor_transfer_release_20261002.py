"""Pure release gates: no service, UI, port, formal DB or configuration writes."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.operations import native_armor_transfer_release_20261002 as release


class ArmorTransferReleaseGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run01=release.read(release.RUN01)
        cls.bank=release.read(release.RUN02)

    def rejected(self,fn,*args):
        with self.assertRaises((RuntimeError,KeyError,ValueError)):
            fn(*args)

    def test_config_only_one_enable_key(self):
        old={'world':{'chat':{'enabled':True},'owned_armor_transfers':{'enabled':False}},
             'database':{'path':'saved.db'},'unknown':{'leave':[1,2,3]}}
        unchanged=copy.deepcopy(old);new=release.config_after(old)
        self.assertEqual(old,unchanged)
        release.config_gate(old,new)
        new['database']['path']='other.db'
        self.rejected(release.config_gate,old,new)
        old['world']['owned_armor_transfers']['enabled']=0
        self.rejected(release.config_after,old)

    def test_schema_preserves_old_objects_rows_history_and_pragmas(self):
        old={'history':[[i,'old','oldsql','oldtime'] for i in range(1,42)],
             'pragmas':{'encoding':'UTF-8','application_id':0,'user_version':0},
             'schema':[['table','old_table','old_table','oldsql']],
             'tables':{'old_table':{'rows':1,'sha256':'original'},'schema_migrations':{'rows':41,'sha256':'history'}}}
        new=copy.deepcopy(old)
        new['history'].append([42,'owned_armor_instances','fixtureSQL','newtime'])
        new['tables']['schema_migrations']={'rows':42,'sha256':'newhistory'}
        new['tables'][release.TABLE]={'rows':0,'sha256':hashlib.sha256(b'').hexdigest()}
        new['schema']+=([['table',release.TABLE,release.TABLE,'newsql'],
                         ['index','sqlite_autoindex_'+release.TABLE+'_1',release.TABLE,None]]+
                        [['trigger',name,'old_table','sql'] for name in sorted(release.TRIGGERS)])
        with patch.object(release,'new_schema_sql',return_value='fixtureSQL'):
            release.schema_gate(old,new)
            changes=[('old row',lambda x:x['tables']['old_table'].update(sha256='changed')),
                     ('grant',lambda x:x['tables'][release.TABLE].update(rows=1)),
                     ('old history',lambda x:x['history'][0].__setitem__(1,'changed')),
                     ('pragma',lambda x:x['pragmas'].update(user_version=42)),
                     ('old schema',lambda x:x['schema'][0].__setitem__(3,'changed')),
                     ('missing guard',lambda x:x['schema'].pop())]
            for name,mutate in changes:
                with self.subTest(name=name):
                    bad=copy.deepcopy(new);mutate(bad)
                    self.rejected(release.schema_gate,old,bad)

    def test_ctest_actual_stdout_and_no_false_positive_summary(self):
        names=release.ctest_gate(release.RELATED_LOG,16,release.REQUIRED_RELATED)
        self.assertEqual(set(names),release.REQUIRED_RELATED)
        self.assertEqual(release.ctest_gate(release.PRODUCTION_LOG,1,{'sqlite_armor_production_adapter'}),
                         ['sqlite_armor_production_adapter'])
        text=release.RELATED_LOG.read_text('utf-8')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ctest.log'
            for bad in (text.replace('Passed','***Failed',1),
                        text.replace('bank_items_repository','armor_slots'),
                        text.replace('100% tests passed','99% tests passed'),
                        text.replace('1/16 Test','1/15 Test',1)):
                path.write_text(bad,'utf-8')
                self.rejected(release.ctest_gate,path,16,release.REQUIRED_RELATED)

    def test_run01_actual_omitted_refusal_key_and_exact_full20(self):
        release.run01_gate(self.run01)
        self.assertTrue(any('refusal' not in e for e in self.run01['ui']['events']))
        for change in ('missing_refusal','wrong_owner','mutated_metadata','changed_revision'):
            bad=copy.deepcopy(self.run01)
            if change=='missing_refusal':bad['ui']['events']=[e for e in bad['ui']['events'] if not e.get('refusal')]
            elif change=='wrong_owner':bad['ui']['events'][0]['identity']=999
            elif change=='changed_revision':bad['ui']['relogin'][0]['durable_revisions_unchanged']=False
            else:
                entry=bad['ui']['relogin'][0]
                slot=next(k for k,row in entry['saved'].items() if row['count'])
                entry['native'][slot]=entry['native'][slot][:-2]+'ff'
            with self.subTest(change=change):self.rejected(release.run01_gate,bad)

    def test_native_empty_slot_opaque_tail_is_not_fabricated_zero(self):
        native={'0':(bytes(6)+b'\x44'*18).hex()};saved={'0':{'count':0}}
        self.assertTrue(release.native_saved_matches(native,saved))
        native['0']=(bytes(4)+b'\x01'+bytes(19)).hex()
        self.assertFalse(release.native_saved_matches(native,saved))

    def test_bank_actual_native_and_owner_instances(self):
        release.run02_gate(self.bank)
        self.assertEqual(self.bank['ui']['initial']['instances'],self.bank['ui']['final_instances'])

    def test_bank_rejects_lost_foreign_metadata_or_revision(self):
        for table in ('character_armor_slot_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata'):
            with self.subTest(table=table):
                bad=copy.deepcopy(self.bank)
                bad['ui']['final_instances'][0]['tables'][table][0][3]+=1
                self.rejected(release.run02_gate,bad)

    def test_bank_rejects_missing_native_direction_and_durable_receipt(self):
        for mode in ('missing_65','missing_armor_rejection','wrong_receipt','peer_change','native_scalar_loss'):
            bad=copy.deepcopy(self.bank);events=bad['ui']['events']
            if mode=='missing_65':events.remove(next(e for e in events if e['operation']=='0x65'))
            elif mode=='missing_armor_rejection':events.remove(next(e for e in events if e['operation']=='armor63_rejected'))
            elif mode=='wrong_receipt':bad['ui']['final']['db']['receipts'][0][7]+=1
            elif mode=='peer_change':next(e for e in events if e['operation']=='0x63')['after']['db']['bag'][-1][4]+=1
            else:next(e for e in events if e['operation']=='0x63')['after']['native']['bag'][0]['raw']='00'*24
            with self.subTest(mode=mode):self.rejected(release.run02_gate,bad)

    def test_cleanup_is_mandatory_for_both_receipts(self):
        for fn,receipt in ((release.run01_gate,self.run01),(release.run02_gate,self.bank)):
            for mode in ('candidate','foreground','live_owned_pid'):
                bad=copy.deepcopy(receipt)
                if mode=='candidate':bad['candidate_sha256']='0'*64
                elif mode=='foreground':bad['desktop_owner_unchanged']=False
                else:next(iter(bad['owned_pid_terminal'].values()))['pid_exists']=True
                with self.subTest(fn=fn.__name__,mode=mode):self.rejected(fn,bad)

    def test_missing_final_support_receipt_blocks_qualification(self):
        verification=release.read(release.VERIFICATION)
        verification.pop('support_source_sha256',None)
        self.rejected(release.verification_gate,verification,release.read(release.CONTRACT))

    def test_support_paths_cannot_escape_archive(self):
        for path in ('../outside','C:/outside','src/../../../outside'):
            with self.subTest(path=path):self.rejected(release.checked_path,path)

    def test_formal_startup_only_new_application_log_bytes(self):
        proof=(b'OWNED_ARMOR_TRANSFERS_ENABLED CUSTOM-0066 instance_only no_grants no_formula no_appearance\n'
               b'NATIVE_ARMOR_DEFINITIONS equ=692 teq=662 authority=NATIVE_PARSED_DEFINITION_ONLY no_instances no_combat_formula\n')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'formal.log';path.write_bytes(proof)
            self.rejected(release.startup_log_gate,path,proof)
            path.write_bytes(proof+proof)
            result=release.startup_log_gate(path,proof)
            self.assertEqual(result['byte_offset'],len(proof))
            self.assertEqual(result['appended_bytes'],len(proof))
            path.write_bytes(proof[:40]+proof)
            self.rejected(release.startup_log_gate,path,proof)

    def test_formal_pid_must_use_exact_active_exe_and_config(self):
        info={'pid':123,'path':str(release.managed.ACTIVE),'command_line':'recorded'}
        args=[str(release.managed.ACTIVE),'--config',str(release.managed.CONFIG)]
        release.process_config_gate(info,args,123)
        for wrong in (args[:-1]+['wrong.json'],args+['--config','other.json'],args[1:]):
            self.rejected(release.process_config_gate,info,wrong,123)
        self.rejected(release.process_config_gate,info,args,999)


if __name__=='__main__':unittest.main()
