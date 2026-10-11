"""Original remote insertion with real resource/display pools, offline only."""
import json
import hashlib
from pathlib import Path
import struct
import unittest

from tools.strike_lab.current_world_display import NativeWorldDisplay, DISPLAY_POOL, SCENE_BRIDGE
from tools.strike_lab.current_world_viewport import ROLE_POOL
from tools.strike_lab.current_world_actor import WORLD, PETDRV
from tools.strike_lab.current_world_role_resources import WORLD_COMPONENTS
from tools.strike_lab.current_battle_character_binding import NativeBattleCharacterBinding
from tools.strike_lab.current_indoor_resources import SCRATCH, SP
from unicorn.x86_const import UC_X86_REG_ESI, UC_X86_REG_EBX, UC_X86_REG_EBP, UC_X86_REG_ESP

ROOT=Path(__file__).resolve().parents[2]


class RemoteActorFullTests(unittest.TestCase):
    def test_resource_backed_insert_and_remove(self):
        folder=ROOT/'artifacts/runs/native-remote-pool-baseline-20260921-01/crypto-private'
        bodies=[]
        for path in folder.glob('*.json'):
            meta=json.loads(path.read_text())
            plain=(folder/meta['plain_file']).read_bytes()
            if meta['direction']=='S2C' and plain[2]==0x2a:
                self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
                self.assertTrue(meta['checksum_valid'])
                bodies.append(plain[3:39])
        self.assertEqual(len(bodies),1)
        body=bytearray(bodies[0])
        # Explicit laboratory scene override to the qualified offline indoor map.
        struct.pack_into('<H',body,24,2|(15<<6))
        struct.pack_into('<I',body,28,2|(17<<2)|(13<<17))
        native=NativeWorldDisplay()
        native.bind_title_resources()
        native.enter_scene(bytes(body))
        from tools.strike_lab.current_world_startup_assets import pinned_assets,ASSETS
        from tools.strike_lab.current_world_resource_banks import CWD
        resource=next(a for a in ASSETS if a.record==3)
        raw,plain=pinned_assets()[3]
        relative=resource.asset.lower();name=relative.rsplit('/',1)[-1]
        native.files[relative]=raw;native.decoded[name]=plain
        native.asset_names[relative]=native.asset_names[relative[:-1]]=name
        native.vm.mem_write(SCRATCH,CWD+resource.literal_path.encode('ascii')+b'\0')
        status_slot=native.call(0x60a90,SCRATCH,this=native.manager)
        self.assertGreaterEqual(status_slot,0)
        # Original local-pool binding consumes the actual loader return in EAX.
        native.vm.reg_write(UC_X86_REG_EBP,WORLD)
        native._slice(0x64f58,0x64f5e)
        self.assertEqual(native.u32(DISPLAY_POOL+0x18),status_slot)
        binding=NativeBattleCharacterBinding(native.vm,root=native.actor_address,
            ui=WORLD+0xa7f2f6c,sp=SCRATCH+0x6000,packet=SCRATCH+0x6200)
        binding.bind_packet_source()
        self.assertEqual(native.u32(binding.source+0x3f98),0)
        native.call(0xfabb0,SCENE_BRIDGE,native.renderer_address,DISPLAY_POOL,
                    native.title_slot,0,this=ROLE_POOL)
        # Original643FC selects the native driver, then64552 binds this pointer.
        native.vm.reg_write(UC_X86_REG_ESI,WORLD)
        native.vm.reg_write(UC_X86_REG_EBX,PETDRV)
        native._slice(0x64552,0x64558)
        block=bytes([1,0,1,0,1,0,0x81,0])
        native.vm.mem_write(SCRATCH+0x5000,block)
        native.call(0x61270,0,0,SCRATCH+0x5000,SCRATCH+0x5100,this=native.manager)
        handles=struct.unpack('<6H',native.vm.mem_read(SCRATCH+0x5100,12))
        self.assertTrue(all(value!=0xffff for value in handles[:4]))
        remote=bytearray(80)
        struct.pack_into('<I',remote,0,7)
        struct.pack_into('<I',remote,12,(18<<2)|(12<<17)|2)
        remote[20:28]=block
        remote[28:39]=b'RemoteHero\0'
        # Dispatch the full original6F branch, including resource selection.
        language=native.call(0x131c10)
        self.assertIn(language,(0,1))
        struct.pack_into('<I',remote,0,7|(language<<25))
        def dispatch(opcode,payload,start):
            native.vm.mem_write(SCRATCH+0x5200,bytes([opcode])+bytes(payload))
            native.vm.reg_write(UC_X86_REG_ESP,SP)
            native.vm.reg_write(UC_X86_REG_EBP,WORLD)
            native.vm.reg_write(UC_X86_REG_EBX,SCRATCH+0x5200)
            native._slice(start,0x6b517)
            self.assertEqual(native.vm.reg_read(UC_X86_REG_ESP),SP)
        def display_texts(record):
            handle=struct.unpack('<h',native.vm.mem_read(record+0x48,2))[0]
            self.assertGreaterEqual(handle,0)
            self.assertLess(handle,4096)
            return tuple(bytes(native.vm.mem_read(DISPLAY_POOL+handle*0xa7e0+offset,17)).split(b'\0',1)[0]
                         for offset in (0x70,0x81,0x92))
        def assert_display_texts(record,values):
            self.assertEqual(display_texts(record),
                             tuple(b' '*max(0,(14-len(value))//2)+value for value in values))
        dispatch(0x6f,remote,0x695c8)
        actor=ROLE_POOL+0x18
        self.assertEqual(native.u32(actor),7)
        self.assertEqual(bytes(native.vm.mem_read(actor+4,11)),b'RemoteHero\0')
        self.assertEqual(struct.unpack('<II',native.vm.mem_read(actor+0x64,8)),(18,12))
        render=struct.unpack('<h',native.vm.mem_read(actor+0x48,2))[0]
        self.assertGreaterEqual(render,0)
        self.assertLess(render,4096)
        assert_display_texts(actor,(b'RemoteHero',b'',b''))
        # A second real actor must remain untouched while the first is updated/replaced.
        other=bytearray(remote)
        struct.pack_into('<I',other,0,8|(language<<25))
        other[28:44]=b'OtherHero\0'+bytes(6)
        dispatch(0x6f,other,0x695c8)
        neighbor=actor+0x268
        self.assertEqual(native.u32(neighbor),8)
        assert_display_texts(neighbor,(b'OtherHero',b'',b''))
        neighbor_texts=display_texts(neighbor)
        neighbor_before=bytes(native.vm.mem_read(neighbor,0x268))
        # Original5E must build/clear StateEft action1 (sleep), not a Fight title.
        display_object=DISPLAY_POOL+render*0xa7e0+0x1c
        for status in (0x0200,0x0200,0,0x0200,0):
            dispatch(0x5e,struct.pack('<III',7,status,18|(12<<11)),0x69a60)
            self.assertEqual(struct.unpack('<H',native.vm.mem_read(actor+0x60,2))[0],status)
            self.assertEqual(struct.unpack('<H',native.vm.mem_read(display_object+0x2c,2))[0],status>>8)
            if status:
                icon=struct.unpack('<h',native.vm.mem_read(display_object+0x2a,2))[0]
                self.assertTrue(0<=icon<4096)
                graphic=native.renderer_address+0x10+icon*0x290
                self.assertEqual(native.vm.mem_read(graphic+1,1)[0],1)
            self.assertEqual(bytes(native.vm.mem_read(neighbor,0x268)),neighbor_before)
            self.assertEqual(display_texts(neighbor),neighbor_texts)
            assert_display_texts(actor,(b'RemoteHero',b'',b''))
        # Clear the queued stationary updates through the original replacement path.
        dispatch(0x6f,remote,0x695c8)
        self.assertEqual(bytes(native.vm.mem_read(actor+0xa9,2)),b'\0\0')
        state=struct.unpack('<H',native.vm.mem_read(actor+0x60,2))[0]
        dispatch(0x5e,struct.pack('<III',7,state,19|(12<<11)),0x69a60)
        self.assertEqual(bytes(native.vm.mem_read(actor+0xa9,2)),b'\0\1')
        self.assertEqual(struct.unpack('<II',native.vm.mem_read(actor+0xac,8)),(19,12))
        self.assertEqual(bytes(native.vm.mem_read(neighbor,0x268)),neighbor_before)
        # Follow the native per-frame callees; logical coordinates publish at start.
        point=SCRATCH+0x5400
        screen_before=struct.unpack('<hh',native.vm.mem_read(actor+0x74,4))
        self.assertEqual(native.call(0xfcc70,actor+0xa8,this=ROLE_POOL),0)
        native.call(0xfcd00,actor+0xa8,point,this=ROLE_POOL)
        self.assertEqual(struct.unpack('<ii',native.vm.mem_read(point,8)),(19,12))
        self.assertEqual(native.call(0xfcc70,actor+0xa8,this=ROLE_POOL),1)
        native.call(0xfb080,actor,point,this=ROLE_POOL)
        self.assertEqual(struct.unpack('<II',native.vm.mem_read(actor+0x64,8)),(19,12))
        self.assertEqual(struct.unpack('<H',native.vm.mem_read(actor+0x38,2))[0],8)
        remaining=struct.unpack('<ii',native.vm.mem_read(actor+0x90,8))
        self.assertNotEqual(remaining,(0,0))
        for tick in range(1000):
            if native.call(0xfb0d0,actor,16,this=ROLE_POOL):
                break
        else:
            self.fail('Native remote interpolation did not finish within 1000 ticks')
        self.assertEqual(struct.unpack('<ii',native.vm.mem_read(actor+0x90,8)),(0,0))
        screen_after=struct.unpack('<hh',native.vm.mem_read(actor+0x74,4))
        self.assertEqual(screen_after,tuple(a+b for a,b in zip(screen_before,remaining)))
        self.assertNotEqual(screen_after,screen_before)
        native.call(0xfb060,actor,this=ROLE_POOL)
        self.assertEqual(struct.unpack('<H',native.vm.mem_read(actor+0x38,2))[0],0)
        self.assertEqual(bytes(native.vm.mem_read(neighbor,0x268)),neighbor_before)
        dispatch(0x6f,remote,0x695c8)
        self.assertEqual(native.u32(actor),7)
        self.assertEqual(bytes(native.vm.mem_read(actor+0xa9,2)),b'\0\0')
        self.assertEqual(bytes(native.vm.mem_read(neighbor,0x268)),neighbor_before)
        assert_display_texts(actor,(b'RemoteHero',b'',b''))
        # Full branch replacement must update its text buffers without touching a peer.
        replacement=bytearray(remote)
        labels=(b'ABCDEFGHIJKLMNO',b'GroupLabelABCD',bytes.fromhex('a4a4a4e5'))
        for offset,value in zip((28,44,60),labels):
            replacement[offset:offset+16]=value+b'\0'*(16-len(value))
        dispatch(0x6f,replacement,0x695c8)
        assert_display_texts(actor,labels)
        self.assertEqual(display_texts(neighbor),neighbor_texts)
        self.assertEqual(bytes(native.vm.mem_read(neighbor,0x268)),neighbor_before)
        # Shorter replacement clears displayed old names instead of retaining a suffix.
        dispatch(0x6f,remote,0x695c8)
        assert_display_texts(actor,(b'RemoteHero',b'',b''))
        self.assertEqual(display_texts(neighbor),neighbor_texts)
        dispatch(0x73,struct.pack('<I',7),0x69a28)
        self.assertEqual(native.u32(actor),0xffffffff)
        self.assertEqual(struct.unpack('<h',native.vm.mem_read(actor+0x48,2))[0],-1)
        self.assertEqual(bytes(native.vm.mem_read(neighbor,0x268)),neighbor_before)
        # Repeated removal must not damage the remaining resource-backed actor.
        dispatch(0x73,struct.pack('<I',7),0x69a28)
        self.assertEqual(native.u32(actor),0xffffffff)
        self.assertEqual(bytes(native.vm.mem_read(neighbor,0x268)),neighbor_before)
        dispatch(0x73,struct.pack('<I',8),0x69a28)
        self.assertEqual(native.u32(neighbor),0xffffffff)
        self.assertEqual(struct.unpack('<h',native.vm.mem_read(neighbor+0x48,2))[0],-1)
        # Original684CD and69941 share61270 with different selector bit positions.
        # Test projection of this captured bootstrap, not a general appearance builder.
        projected=bytearray(remote)
        selector=(struct.unpack_from('<I',body)[0]>>16)&0x7f
        struct.pack_into('<I',projected,0,9|(selector<<14)|(language<<25))
        projected[5]=body[6]&0x7f
        projected[20:28]=body[12:20]
        dispatch(0x6f,projected,0x695c8)
        self.assertEqual(native.u32(actor),9)
        for index in range(4):
            local=WORLD_COMPONENTS+4+6*index
            remote_component=actor+0x224+4+6*index
            self.assertEqual(bytes(native.vm.mem_read(remote_component,2)),
                             bytes(native.vm.mem_read(local,2)),f'component handle{index}')
            self.assertEqual(bytes(native.vm.mem_read(remote_component+4,1)),
                             bytes(native.vm.mem_read(local+4,1)),f'component variant{index}')
        dispatch(0x73,struct.pack('<I',9),0x69a28)
        self.assertEqual(native.u32(actor),0xffffffff)
        for first in range(7):
            for second in range(7):
                with self.subTest(first=first,second=second):
                    local_body=bytearray(body)
                    local_body[13]=(local_body[13]&0x1f)|(first<<5)
                    local_body[15]=(local_body[15]&0x1f)|(second<<5)
                    self.assertEqual(local_body[32:34],b'\0\0')
                    self.assertLess(local_body[6],128)
                    # Original local copy, normal resource selection and variant setters.
                    native.vm.mem_write(SP+0x28,bytes(local_body))
                    native.vm.reg_write(UC_X86_REG_ESP,SP)
                    native.vm.reg_write(UC_X86_REG_EBP,native.actor_address)
                    native.vm.reg_write(UC_X86_REG_EBX,WORLD)
                    native.vm.reg_write(UC_X86_REG_ESI,native.manager)
                    native._slice(0x68315,0x68558)
                    self.assertEqual(native.vm.reg_read(UC_X86_REG_ESP),SP)
                    projected[20:28]=local_body[12:20]
                    dispatch(0x6f,projected,0x695c8)
                    self.assertEqual(native.u32(actor),9)
                    for index in range(4):
                        local=WORLD_COMPONENTS+4+6*index
                        component=actor+0x224+4+6*index
                        self.assertNotEqual(bytes(native.vm.mem_read(component,2)),b'\xff\xff')
                        for offset,width in ((0,2),(4,1)):
                            self.assertEqual(bytes(native.vm.mem_read(component+offset,width)),
                                             bytes(native.vm.mem_read(local+offset,width)))
                    self.assertEqual(native.vm.mem_read(actor+0x22c,1)[0],first)
                    self.assertEqual(native.vm.mem_read(actor+0x232,1)[0],second)
                    dispatch(0x73,struct.pack('<I',9),0x69a28)
                    self.assertEqual(native.u32(actor),0xffffffff)


if __name__=='__main__':
    unittest.main()
