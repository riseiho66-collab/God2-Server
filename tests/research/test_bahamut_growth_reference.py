"""Check source row spans and generation layouts, including unknown/late bands."""
import unittest
import json
import sqlite3
import tempfile
import shutil
from contextlib import closing
from unittest.mock import patch
from pathlib import Path
from tools.strike_lab.import_bahamut_growth_reference import Tables, growth, profiles, checkpoint_check, main, PAGES


class WikiGrowthTests(unittest.TestCase):
    def test_fullwidth_and_unknown(self):
        self.assertEqual(growth('２體 ３智\n１速'),[2,0,3,1])
        self.assertIsNone(growth('未知'))
        self.assertIsNone(growth('體力+2'))
        self.assertIsNone(growth(''))
        with self.assertRaises(ValueError):growth('2體3體')

    def test_rowspan_preserves_checkpoint_and_blank(self):
        p=Tables();p.feed('<h3>二代鴨族</h3><table><tr><td rowspan="2">體力 A</td><td>LV1</td><td></td></tr><tr><td>LV99</td><td>100</td></tr></table>')
        self.assertEqual(p.tables[0][1],['LV99','100'])
        self.assertEqual(p.expanded_tables[0],[['體力 A','LV1',''],['體力 A','LV99','100']])
        self.assertEqual(p.contexts,['二代鴨族'])

    def test_second_generation_keeps_literal_overlap(self):
        rows=[['戰寵型態','等級','體力','力量','智力','速度'],
              ['體力 Ａ','ＬＶ１','101','52','51','101'],
              ['體力 Ａ','ＬＶ９９','279','248','199','249'],
              ['１～１９級','２０～４９級','５０～９９級','１００～１２４','１２５～１３９','１３９～１５９'],
              ['１體２力１智１速','２體２力１智１速','２體２力２智２速','６體４力３速','','未知']]
        value=profiles(rows,rows,'二代鴨族')[0]
        self.assertEqual(value[0],'二代鴨族')
        self.assertEqual(value[3][-2:],['125~139','139~159'])
        self.assertEqual(value[4][-2:],[None,None])
        self.assertEqual(value[5]['1'],[101,52,51,101])
        self.assertEqual(value[5]['99'],[279,248,199,249])

    def test_special_pet_notes_do_not_become_wild_monster_stats(self):
        rows=[['戰寵類別','備註','１～１９級配點','２０～４９級','５０～９９級','體','力','智','速'],
              ['鑫雀','必破頂\nHP+200','２智２速','１體３智４速','１體５智４速','190','50','508','478']]
        value=profiles(rows,rows)[0]
        self.assertEqual(value[1],'破頂')
        self.assertEqual(value[2],'必破頂\nHP+200')
        self.assertEqual(value[4][0],[0,0,2,2])
        self.assertEqual(value[5],{'99':[190,50,508,478]})

    def test_saved_catalog_preserves_generation_and_unknown(self):
        path=Path(__file__).resolve().parents[2]/'artifacts/research/bahamut-growth-20260927/growth-reference.db'
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchone(),('ok',))
            self.assertEqual(db.execute('select count(*) from sources').fetchone(),(7,))
            self.assertEqual(db.execute('select count(*) from pet_growth_profiles').fetchone(),(62,))
            values=db.execute('select p.family,p.stages,s.generation,p.runtime_eligible from pet_growth_profiles p join sources s on s.key=p.source_key').fetchall()
            self.assertTrue(all(eligible==0 for _,_,_,eligible in values))
            second=[r for r in values if r[2]=='SECOND_GENERATION']
            self.assertEqual(len(second),35)
            self.assertTrue(all(r[0] for r in second))
            self.assertTrue(any(None in json.loads(r[1]) for r in second))

    def test_checkpoint_disagreement_is_reported_not_overwritten(self):
        profile=['鴨族','體力 A','',['1~19級','20~49級','50~99級'],
                 [[1,2,1,1],[2,2,1,1],[2,2,2,2]],
                 {'1':[101,52,51,101],'99':[279,248,199,249]}]
        self.assertTrue(checkpoint_check(profile)['matches'])
        profile[5]['99'][0]=280
        report=checkpoint_check(profile)
        self.assertFalse(report['matches'])
        self.assertEqual(report['calculated_level99'][0],279)
        self.assertEqual(profile[5]['99'][0],280)

    def test_cached_import_is_idempotent_without_network(self):
        source=Path(__file__).resolve().parents[2]/'artifacts/research/bahamut-growth-20260927'
        with tempfile.TemporaryDirectory(prefix='god2-wiki-growth-') as folder:
            output=Path(folder)
            for key in PAGES:shutil.copy2(source/(key+'.html'),output/(key+'.html'))
            with patch('sys.argv',['importer','--output',folder]),patch('builtins.print'),patch('tools.strike_lab.import_bahamut_growth_reference.urlopen',side_effect=AssertionError('Network not allowed')):
                main()
                with closing(sqlite3.connect(output/'growth-reference.db')) as db:first=list(db.iterdump())
                main()
                with closing(sqlite3.connect(output/'growth-reference.db')) as db:
                    self.assertEqual(first,list(db.iterdump()))
                    self.assertEqual(db.execute('pragma integrity_check').fetchone(),('ok',))


if __name__=='__main__':unittest.main()
