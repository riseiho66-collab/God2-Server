"""Bounded current-PE weapon tooltip unpack and S2C22 side-effect oracle.

Synthetic actor/UI backing; executes native code without patched instructions or
stubbed calls. Not a server stat formula or rendered client acceptance.
"""
import argparse, json, random, struct
from pathlib import Path
from .current_dialogue_mode4_native_20260926 import Native, require, sha, ROOT, UI, RESOURCE, TABLE, STRINGS, PACKET, RETURN, pefile, SHA
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE

ACTOR, GOD = 0x61000000, 0x62000000

class Probe(Native):
    def __init__(self, pe):
        super().__init__(pe, [b''])
        self.vm.mem_map(ACTOR, 4096); self.vm.mem_map(GOD, 4096)
        self.write(UI+0x86888, 'I', ACTOR)
        self.write(ACTOR+0xd0, 'I', GOD)
        self.vm.mem_write(GOD, b'\x6b'*4096)
        self.write(GOD+0x2c, 'II', 333, 444)
        self.write(UI+0x232dda, 'h', -1)
        self.write(UI+0x232e50, 'h', 0)
        self.write(UI+0x232e52, 'h', 1)
        # Empty native widget records. Group FFFF avoids graphics-object lookup.
        self.write(UI+0xe2170+0x818+0x2a08+4, 'H', 65535)
        self.write(RESOURCE+0xb2c6c, 'h', 0)
        self.observed=[]; self.actor_writes=[]; self.god_writes=[]
        self.vm.hook_add(UC_HOOK_CODE, self.observe)
        self.vm.hook_add(UC_HOOK_MEM_WRITE, self.wrote)
    def observe(self, vm, a, size, context):
        if a in (0x5060f0,0x505680,0x505110,0x5077c0,0x507850):
            sp=self.reg('ESP')
            self.observed.append(dict(va=hex(a),args=[self.read(sp+4+i*4,'I') for i in range(5)]))
    def wrote(self, vm, access, a, size, value, context):
        if ACTOR<=a<ACTOR+4096:self.actor_writes.append(dict(offset=hex(a-ACTOR),size=size,value=value))
        if GOD<=a<GOD+4096:self.god_writes.append(dict(offset=hex(a-GOD),size=size,value=value))

def audit(client, compiled=None):
    raw=(client/'God2.exe').read_bytes(); require(sha(raw)==SHA,'Current PE pin mismatch')
    pe=pefile.PE(data=raw)
    snapshots=[]
    for hud in (-1,0):
        for maximum in (0,80,100,200):
            n=Probe(pe); n.write(UI+0x232e50,'h',hud)
            n.write(ACTOR+0x5c,'IIII',100,100,90,100)
            # Complete 24-byte payload with opaque padding preserved as sent.
            payload=struct.pack('<BBH4HHHII',9,0xA5,7,11,22,33,44,500,0xA55A,maximum,maximum)
            require(len(payload)==24,'payload size')
            n.vm.mem_write(PACKET,payload); god_before=bytes(n.vm.mem_read(GOD,4096))
            n.setup(PACKET); n.run(0x4e6b40,[RETURN])
            expected_hp=min(100,maximum) if hud>=0 and maximum else 100
            expected_mp=min(90,maximum) if hud>=0 and maximum else 90
            require(n.read(ACTOR+0x5c,'I')==expected_hp and n.read(ACTOR+0x64,'I')==expected_mp,'HP/MP clamp mismatch')
            require(n.read(ACTOR+0x60,'I')==maximum and n.read(ACTOR+0x68,'I')==maximum,'maxima mismatch')
            require([n.read(ACTOR+o,'I') for o in (0x78,0x7c,0x80,0x84)]==[11,22,33,44],'base stats mismatch')
            require(bytes(n.vm.mem_read(GOD,4096))==god_before and not n.god_writes,'S2C22 wrote God memory')
            expected_ui=bool(hud>=0 and maximum)
            god_frame=[c for c in n.observed if c['va']=='0x505110']
            require(bool(god_frame)==expected_ui,'God HUD branch mismatch')
            if expected_ui:
                require([a&65535 for a in god_frame[0]['args'][:3]]==[1,31,75],'God HUD clear frame mismatch')
                require(any(c['va']=='0x5060f0' and c['args'][0]&65535==1 and c['args'][1:4]==[4,0,0] for c in n.observed),'God HUD gauge clear missing')
            snapshots.append(dict(hud=hud,maxima=maximum,logical_hex='22'+payload.hex(),hp=expected_hp,mp=expected_mp,god_hp=n.read(GOD+0x2c,'I'),god_memory_unchanged=True,actor_writes=n.actor_writes,ui_calls=n.observed))
    # 2C is a separate complete attribute snapshot, not the 22 base/maxima record.
    length_va=struct.unpack('<I',pe.get_data(0x1324+4*0x2c,4))[0]
    length_probe=Probe(pe);length_probe.setup();length_probe.run(length_va,[RETURN])
    require(length_probe.reg('EAX')==61,'2C logical length changed')
    stat_snapshots=[]
    for sheet in (-1,0):
        for positive in range(16):
            for negative in range(16):
                n=Probe(pe);n.write(UI+0x232dda,'h',sheet)
                n.write(ACTOR+0x5c,'4I',123,456,78,901)
                before=bytes(n.vm.mem_read(ACTOR,4096));god_before=bytes(n.vm.mem_read(GOD,4096))
                values=[13,17,19,23,101,102,103,104,105,positive,negative,2001,2002,2003,2004]
                payload=struct.pack('<15I',*values);n.vm.mem_write(PACKET,payload)
                n.setup(PACKET);n.run(0x4e6600,[RETURN])
                expected=bytearray(before)
                for i,off in enumerate((0x88,0x8a,0x8c,0x8e)):
                    bit=(2,4,1,8)[i];sign=-1 if negative&bit and not positive&bit else 1
                    struct.pack_into('<h',expected,off,values[i]*sign)
                for i,off in enumerate((0xa4,0xa8,0xac,0xb0,0xb4)):struct.pack_into('<I',expected,off,values[i+4])
                struct.pack_into('<HH',expected,0xb8,positive,negative)
                for i,off in enumerate((0x98,0x94,0xa0,0x9c)):struct.pack_into('<I',expected,off,values[11+i])
                require(bytes(n.vm.mem_read(ACTOR,4096))==expected,'2C full actor after-state mismatch')
                require(bytes(n.vm.mem_read(GOD,4096))==god_before and not n.god_writes,'2C wrote God memory')
                require(not any(c['va'] in ('0x5060f0','0x505680','0x505110') for c in n.observed),'2C touched HUD refresh path')
                stat_snapshots.append(dict(sheet=sheet,positive_mask=positive,negative_mask=negative,logical_hex='2c'+payload.hex(),modifiers=[n.read(ACTOR+o,'h') for o in (0x88,0x8a,0x8c,0x8e)],attack_defense_display=[n.read(ACTOR+o,'I') for o in (0x94,0x98,0x9c,0xa0)],god_memory_unchanged=True,role_vitals_unchanged=True))
    compiled_result=None
    if compiled is not None:
        require(len(compiled)==61 and compiled[0]==0x2c,'Compiled codec packet must be exact2C61')
        n=Probe(pe);n.write(UI+0x232dda,'h',0);n.write(ACTOR+0x5c,'4I',123,456,78,901)
        before=bytes(n.vm.mem_read(ACTOR,4096));god_before=bytes(n.vm.mem_read(GOD,4096));expected=bytearray(before)
        payload=compiled[1:];positive=int.from_bytes(payload[36:38],'little');negative=int.from_bytes(payload[40:42],'little')
        for i,off in enumerate((0x88,0x8a,0x8c,0x8e)):
            value=int.from_bytes(payload[i*4:i*4+2],'little');bit=(2,4,1,8)[i]
            if negative&bit and not positive&bit:value=(-value)&65535
            struct.pack_into('<H',expected,off,value)
        for source,dest,size in [(16,0xa4,20),(36,0xb8,2),(40,0xba,2),(44,0x98,4),(48,0x94,4),(52,0xa0,4),(56,0x9c,4)]:expected[dest:dest+size]=payload[source:source+size]
        n.vm.mem_write(PACKET,payload);n.setup(PACKET);n.run(0x4e6600,[RETURN])
        require(bytes(n.vm.mem_read(ACTOR,4096))==expected,'Compiled packet actor mismatch')
        require(bytes(n.vm.mem_read(GOD,4096))==god_before and not n.god_writes,'Compiled packet changed God')
        compiled_result=dict(logical_hex=compiled.hex(),full_native_return=True,actor_exact=True,god_memory_unchanged=True,role_vitals_unchanged=True)
    # Execute current unpacker through the exact call boundary to text formatter.
    rng=random.Random(20260926); unpack=[]
    for i in range(258):
        data=bytes(20) if i==0 else bytes([255])*20 if i==1 else rng.randbytes(20)
        n=Probe(pe);n.vm.mem_write(PACKET,data);n.setup(PACKET,TABLE,STRINGS)
        n.run(0x4b45b0,[0x4b4200])
        sp=n.reg('ESP');values=n.read(sp+12,'I');labels=n.read(sp+16,'I')
        observed=list(struct.unpack('<6H',n.vm.mem_read(values,12)))
        ids=list(struct.unpack('<6H',n.vm.mem_read(labels,12)))
        b=data[19]
        expected=[data[7]|((b>>4)&3)<<8,data[12]|(b>>6)<<8]+[data[8+j]|((b>>j)&1)<<8 for j in range(4)]
        require(observed==expected and ids==[520,522,74,73,72,75],'native weapon unpack mismatch')
        unpack.append(dict(instance_hex=data.hex(),tooltip_values=observed,label_ids=ids))
    quality=[]
    for bits in range(8):
        n=Probe(pe);n.write(PACKET+12,'I',bits<<27);n.setup(PACKET,TABLE,TABLE+512,TABLE+1024,STRINGS)
        n.run(0x4b4200,[0x4b4237]);signed=bits if bits<4 else bits-8
        require(n.reg('EAX')==(signed&0xffffffff),'quality field signed extraction mismatch')
        quality.append(dict(raw_bits=bits,signed_quality=signed,prefix_pointer=hex(n.reg('ECX'))))
    level_display=[]
    adjustments=struct.unpack('<4h',pe.get_data(0x1926d4,8))
    require(adjustments==(0,1,3,5),'level display adjustment table changed')
    for grade in range(4):
        for base in (1,100,1001):
            n=Probe(pe);n.write(PACKET+12,'I',grade<<30);n.write(TABLE+0x11e,'H',base);n.setup()
            n.write(n.reg('ESP')+0x11a8,'I',TABLE);n.setreg('EDX',PACKET);n.setreg('EBP',UI)
            n.run(0x4b6020,[0x4b604a]);result=n.reg('EAX')&65535
            require(result==max(1,base-adjustments[grade]),'level display reduction mismatch')
            level_display.append(dict(base_encoded_level=base,grade_bits=grade,display_encoded_level=result))
    sources=[]
    for filename,selected in [('gamedata.csvZ',[3,4803,4804,15477,15478]),('message.csvZ',[])]:
        data=(client/'Data2/Patch/Comm'/filename).read_bytes()
        require(sha(data)=={'gamedata.csvZ':'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731','message.csvZ':'5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'}[filename],'source pin changed')
        decoded=decode_csvz(data);rows=decoded.splitlines()
        if filename=='message.csvZ':
            inside=False
            for line,row in enumerate(rows,1):
                if row.startswith(b'ProgramMsg,'):inside=True;continue
                if inside and row.split(b',')[0] in [str(k).encode() for k in (520,521,522,523,72,73,74,75,569,570,571,1066)]:selected.append(line)
        sources.append(dict(file=filename,sha256=sha(data),decoded_sha256=sha(decoded),rows=[dict(line=i,raw_hex=rows[i-1].hex(),text=rows[i-1].decode('cp950')) for i in selected]))
    spans=[(0x4e6b40,0x4e6bf0),(0x4e6600,0x4e6b40),(0x4ac070,0x4ac2c0),(0x4b45b0,0x4b4690),(0x4b4200,0x4b423c),(0x4b6020,0x4b604f),(0x459420,0x459960)]
    return dict(schema='current-weapon-attributes-20260926',exe_sha256=sha(raw),compiled_codec=compiled_result,snapshot_vectors=snapshots,attribute_snapshot_length=dict(entry=hex(length_va),length=61),attribute_snapshot_vectors=stat_snapshots,weapon_unpack_vectors=unpack,quality_vectors=quality,level_display_vectors=level_display,sources=sources,spans=[dict(start=hex(a),end_exclusive=hex(b),sha256=sha(pe.get_data(a-0x400000,b-a))) for a,b in spans],scope='Current PE22 consumer returns through real refresh callees with role sheet disabled and empty native HUD records. 2C returns through real role formatter with disabled/enabled sheet handle and empty records. Records actual requested God HUD updates, not rendered pixels. Weapon unpack stops before tooltip formatter; quality and level display slices use native instructions. No stat-generation formula, inventory equip, graphical acceptance, DB or live client operation.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--client',type=Path,default=ROOT.parent/'God2');p.add_argument('--output',type=Path,required=True);p.add_argument('--packet-hex',help='Exact logical2C61 from compiled codec');a=p.parse_args()
    result=audit(a.client,bytes.fromhex(a.packet_hex) if a.packet_hex else None);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS: 8 current-PE22 refresh, 512 complete2C, 258 weapon unpack, 20 quality/level vectors; compiled packet='+str(result['compiled_codec'] is not None)+'; '+str(a.output))
if __name__=='__main__':main()
