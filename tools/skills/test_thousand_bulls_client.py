"""Preservation and native action resolution checks for skill150 DATA candidate."""
import struct
import tempfile
import unittest
from pathlib import Path
from tools.skills import build_thousand_bulls_client as build


class CandidateChecks(unittest.TestCase):
    def test_existing_definition_bytes_and_native_mp(self):
        original = build.decode_definitions((build.CLIENT/build.CATALOG).read_bytes())
        new = build.decode_definitions((build.OUTPUT/build.CATALOG).read_bytes())
        self.assertEqual(len(original), 453)
        for key, record in original.items():
            self.assertEqual(new[key].raw, record.raw)
        self.assertEqual(new[0,150].raw[68:70], b"\x05\x05")
        self.assertEqual(struct.unpack_from("<H",new[0,150].raw,66)[0],100)
        for identity in range(127,150):
            self.assertEqual(new[0,identity].raw[32:], bytes(78))

    def test_native_action_pool_resolves_new_bitmap(self):
        parts = list(build.chunks(build.decode_csvz((build.OUTPUT/build.ICONS).read_bytes())))
        images = [d for t,d,_ in parts if t.endswith(b"_RWIF")]
        current = None
        for tag,data,_ in parts:
            if tag == b"ACT_DATA":
                current = struct.unpack_from("<i",data)[0]
            if current == 21150 and tag == b"ACT_POOL":
                x,y,fx,fy,index,flags = struct.unpack("<hhBBHH",data)
                self.assertEqual((x,y,fx,fy,index,flags),(0,0,0,0,120,0x030d))
                self.assertEqual(struct.unpack_from("<II",images[index]),(40,40))
                self.assertTrue(any(v>>12 for v in struct.unpack_from("<1600H",images[index],8)))
                return
        self.fail("21150 ACT_POOL missing")

    def test_existing_icon_action_and_bitmap_chunks_preserved(self):
        old=list(build.chunks(build.decode_csvz((build.CLIENT/build.ICONS).read_bytes())))
        new=list(build.chunks(build.decode_csvz((build.OUTPUT/build.ICONS).read_bytes())))
        insertion=next(i for i,p in enumerate(old) if p[0]==b"ACT_DATA")
        restored=new[:insertion]+new[insertion+1:len(old)]+[new[-1]]
        self.assertEqual([p[2] for p in old],[p[2] for p in restored])

    def test_f1_alias_both_encodings(self):
        for relative,codec,name in [(build.DISPLAY_ITEMS,'cp950','牛轉仙界踏'),(build.DISPLAY_ITEMS_GB,'cp936','牛转仙界踏')]:
            rows=[r.split(b',') for r in build.decode_csvz((build.OUTPUT/relative).read_bytes()).splitlines()]
            row=next(r for r in rows if r[0]==b'6898')
            self.assertEqual((row[3],row[26]),(b'21150',b'SpcA150'))
            self.assertEqual(row[4].decode(codec),name)
            self.assertEqual(sum(len(r)>26 and r[26]==b'SpcA150' for r in rows),1)
            self.assertTrue(any(r[0]==b'6897' and r[26]==b'SpcA126' for r in rows if len(r)>26))

    def test_unqualified_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for rel in build.FILES:
                target=root/rel
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((build.CLIENT/rel).read_bytes())
            target=root/build.CATALOG
            data=bytearray(target.read_bytes());data[0]^=1;target.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'pin mismatch'):
                build.build(client=root)

    def test_cannot_write_live_client(self):
        with self.assertRaisesRegex(ValueError,'isolated'):
            build.build(output=build.CLIENT)


if __name__=='__main__':
    unittest.main()
