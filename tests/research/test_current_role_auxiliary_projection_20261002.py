"""Compiled raw2C field updates into actual current native consumer/formatter.

Only CRT sprintf is adapted by StatProbe. Values are deliberate differential
test inputs; this does not qualify a gameplay formula or a live server release.
"""
from pathlib import Path
import hashlib
import struct
import subprocess
import tempfile
import unittest

from test_current_battle_command import build_fixture
from tools.strike_lab.current_armor_equipped_attributes_20261002 import (
    StatProbe, LIVE, PIN, qualified_image, pefile, UI, ACTOR, PACKET,
)


class AuxiliaryProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='god2-auxiliary-projection-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.exe=build_fixture(Path(cls.temp.name),'companion/role_auxiliary_projection_probe.cpp')
        current=LIVE.read_bytes()
        if hashlib.sha256(current).hexdigest()!=PIN:
            raise AssertionError('Current client differs')
        cls.pe=pefile.PE(data=current)
        cls.original=qualified_image()

    @staticmethod
    def seed():
        raw=bytearray([0xa5]*61);raw[0]=0x2c
        struct.pack_into('<5I',raw,17,101,0x7fffffff,0x80000000,0xffffffff,105)
        struct.pack_into('<4I',raw,45,2001,2002,2003,2004)
        return raw

    def cpp(self,lines):
        result=subprocess.run([str(self.exe)],input='\n'.join(lines)+'\n',text=True,
                              capture_output=True,check=True,timeout=30)
        return result.stdout.splitlines()

    def native(self,raw):
        n=StatProbe(self.pe,self.original)
        n.write(UI+0x232dda,'h',0);n.write(UI+0x232e50,'h',-1)
        n.write(ACTOR+0x58,'H',0);n.write(ACTOR+0x78,'4I',111,222,333,444)
        n.vm.mem_write(PACKET,raw[1:])
        n.call(0x4e6600,PACKET,phase='fresh2C')
        n.call(0x4e6db0,ACTOR,phase='base_sheet')
        self.assertEqual(bytes(n.vm.mem_read(PACKET,60)),raw[1:])
        self.assertFalse(n.inventory_accesses)
        formats={x['control']:x['value_raw'] for x in n.status_formats if x['phase']=='base_sheet'}
        self.assertEqual([formats[i] for i in range(14,18)],[111,222,333,444])
        return n,tuple(struct.unpack('<4h',n.vm.mem_read(ACTOR+0x88,8)))

    def test_signed_updates_against_fresh_native_and_preserved_fields(self):
        tuples=[(0,0,0,0),(1,-2,3,-4),(32767,-32768,-1,0),(-32768,32767,0,-1)]
        for value in (-32768,-32767,-2044,-1,0,1,2044,32766,32767):
            for dimension in range(4):
                item=[0]*4;item[dimension]=value;tuples.append(tuple(item))
        seed=self.seed()
        outputs=self.cpp([seed.hex()+' modifiers '+' '.join(map(str,v)) for v in tuples])
        self.assertEqual(len(outputs),len(tuples))
        mutable=set(range(37,39))|set(range(41,43))
        for i in range(4):mutable.update((1+4*i,2+4*i))
        for values,line in zip(tuples,outputs):
            with self.subTest(values=values):
                fields=line.split();encoded=bytes.fromhex(fields[0]);cpp=tuple(map(int,fields[1:5]))
                self.assertEqual(cpp,values)
                self.assertEqual([encoded[i] for i in range(61) if i not in mutable],
                                 [seed[i] for i in range(61) if i not in mutable])
                for offset in (37,41):
                    self.assertEqual(struct.unpack_from('<H',encoded,offset)[0]&0xfff0,
                                     struct.unpack_from('<H',seed,offset)[0]&0xfff0)
                n,native=self.native(encoded);self.assertEqual(native,values)
                formats={x['control']:x for x in n.status_formats if x['phase']=='base_sheet'}
                for i,value in enumerate(values):
                    formatted=formats[18+i]
                    if value==0:
                        # Native uses an empty format, so its unused vararg is
                        # stack residue rather than a numeric zero argument.
                        self.assertEqual(formatted['format_hex'],'')
                    else:
                        self.assertEqual(formatted['format_hex'],'2b2564' if value>0 else '2564')
                        self.assertEqual(formatted['value_raw'],value&0xffffffff)
                # Re-project an unchanged authoritative total: byte-stable, no accumulation.
                repeated=self.cpp([encoded.hex()+' modifiers '+' '.join(map(str,values))])[0]
                self.assertEqual(bytes.fromhex(repeated.split()[0]),encoded)

    def test_original_raw_mask_precedence_and_word_edges(self):
        cases=[]
        for magnitude in (13,0x7fff,0x8000,0xffff):
            for positive,negative in ((0,0),(15,0),(0,15),(15,15)):
                raw=self.seed()
                for offset in (1,5,9,13):struct.pack_into('<I',raw,offset,0xcafe0000|magnitude)
                struct.pack_into('<I',raw,37,0x12340000|positive)
                struct.pack_into('<I',raw,41,0x56780000|negative)
                cases.append(bytes(raw))
        outputs=self.cpp([raw.hex()+' read' for raw in cases])
        for raw,line in zip(cases,outputs):
            fields=line.split();self.assertEqual(bytes.fromhex(fields[0]),raw)
            _,native=self.native(raw)
            self.assertEqual(tuple(map(int,fields[1:5])),native)

    def test_combat_order_full_dwords_and_signed_display_domain(self):
        totals=[(2002,2001,2004,2003),(0,0,0,0),(0x7fffffff,123,456,789),
                (0x80000000,0xffffffff,0x80000001,0x7fffffff)]
        seed=self.seed()
        outputs=self.cpp([seed.hex()+' combat '+' '.join(map(str,v)) for v in totals])
        for values,line in zip(totals,outputs):
            fields=line.split();raw=bytes.fromhex(fields[0])
            self.assertEqual(raw[:45],seed[:45])
            self.assertEqual(tuple(map(int,fields[5:9])),values)
            self.assertEqual(tuple(map(int,fields[9:14])),(101,0x7fffffff,0x80000000,0xffffffff,105))
            self.assertEqual(int(fields[14]),int(all(x<0x80000000 for x in values)))
            n,_=self.native(raw)
            self.assertEqual(tuple(struct.unpack('<4I',n.vm.mem_read(ACTOR+0x94,16))),values)
            self.assertEqual(bytes(n.vm.mem_read(ACTOR+0xa4,20)),raw[17:37])

    def test_malformed_wire_rejected(self):
        raw=self.seed();wrong=raw.copy();wrong[0]=0x22
        cases=[wrong,raw+b'\0']+[raw[:size] for size in range(1,61)]
        self.assertEqual(self.cpp([bytes(x).hex()+' read' for x in cases]),['reject']*len(cases))


if __name__=='__main__':
    unittest.main()
