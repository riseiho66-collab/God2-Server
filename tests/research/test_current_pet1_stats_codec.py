import struct
import subprocess
import tempfile
from pathlib import Path
import unittest
from tests.research.test_current_instance_update import build_fixture,ROOT
from tools.strike_lab.current_pet1_stat_labels import audit,NativePet1,diagnostic_body,FIELDS

class Pet1StatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='god2-pet1-codec-');cls.addClassCleanup(cls.temp.cleanup)
        cls.exe=build_fixture(Path(cls.temp.name),source=ROOT/'tests/test_recovered_pet1_stats.cpp')
    def decode(self,packets):
        r=subprocess.run([str(self.exe)],input=''.join(p.hex()+'\n' for p in packets),text=True,capture_output=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr)
        rows=r.stdout.splitlines();self.assertEqual(len(rows),len(packets))
        return [None if row=='reject' else (bytes.fromhex(row.split()[0]),list(map(int,row.split()[1:]))) for row in rows]
    def test_full_original_receiver_and_all_25_numeric_fields(self):
        evidence=audit();self.assertEqual(len(evidence['fields']),25)
        native=NativePet1();packets=[];expected=[]
        boundaries=(0,1,0x3ff,0x400,0xfff,0x1000,0x3fffff,0x400000,0xffffff,0x1000000,0xffffffff)
        for level in range(256):
            slot=42+level%3;body=bytearray(diagnostic_body(slot));body[0x23]=level
            for index,offset in enumerate((8,12,16,20,24)):
                struct.pack_into('<I',body,offset,boundaries[(level+index)%len(boundaries)])
            r=native.receive(bytes(body));self.assertIn(0xa2bc7,r['trace']['pcs'])
            values=native.numeric_fields(r['record_address'])
            expected.append([values[f[0]] for f in FIELDS]);packets.append(b'\xe3'+body)
            raw=(struct.unpack_from('<I',body,24)[0]>>10)&0x3fff
            scale=struct.unpack('<f',struct.pack('<f',.01))[0]
            self.assertEqual(native.progress(r['record_address']),struct.unpack('<f',struct.pack('<f',raw*scale))[0])
        for packet,wanted,decoded in zip(packets,expected,self.decode(packets)):
            self.assertEqual(decoded[0],packet);self.assertEqual(decoded[1][:2],[24001,packet[0x27]])
            self.assertEqual(decoded[1][2:27],wanted)
            self.assertEqual(decoded[1][27],(struct.unpack_from('<I',packet,25)[0]>>10)&0x3fff)
            self.assertEqual(decoded[1][28],struct.unpack_from('<I',packet,49)[0])
    def test_bounds_and_lossless_opaque_storage(self):
        good=b'\xe3'+diagnostic_body();packets=[];wanted=[]
        for length in range(55):packets.append((good+b'\xcc')[:length]);wanted.append(length==53)
        for slot in range(256):
            p=bytearray(good);p[0x27]=slot;packets.append(bytes(p));wanted.append(42<=slot<=44)
        for key in (0,0x3390,0x3391,0x3778,0x3779,0x5dc0,0x5dc1,0x6d60,0x6d61,65535):
            p=bytearray(good);struct.pack_into('<H',p,0x1d,key);packets.append(bytes(p))
            wanted.append(0x3391<=key<=0x3778 or 0x5dc1<=key<=0x6d60)
        for offset in range(1,53):
            if offset in (0x1d,0x1e,0x27):continue
            for bit in range(8):
                p=bytearray(good);p[offset]^=1<<bit;packets.append(bytes(p));wanted.append(True)
        p=bytearray(good);p[0]=0xe2;packets.append(bytes(p));wanted.append(False)
        for raw,accepted,row in zip(packets,wanted,self.decode(packets)):
            self.assertEqual(row is not None,accepted)
            if row:self.assertEqual(row[0],raw)
    def test_zero_key_and_outside_integer_ranges_are_not_instances(self):
        native=NativePet1()
        for key in (0,0x3390,0x3779,0x6d61):
            body=bytearray(diagnostic_body());struct.pack_into('<H',body,0x1c,key)
            self.assertNotIn(0xa2bc7,native.receive(bytes(body))['trace']['pcs'])

if __name__=='__main__':unittest.main()
