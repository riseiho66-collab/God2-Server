"""PHASE1 static E6/egg-input capture; only file/hash/PE/Capstone/table work."""
from pathlib import Path
import hashlib
import json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

ROOT = Path.home() / '.codex/artifact-archives/god2-server/20261012'
INPUT = ROOT / 'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT = ROOT / 'tw-native-e5-egg-input-source-328/native'
SERVER = Path('C:/Users/risei/Desktop/God2/God2-Server')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    image = (INPUT / 'native-image.bin').read_bytes()
    original = (INPUT / 'originalPE.bin').read_bytes()
    if sha(image) != '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':
        raise ValueError('Mapped identity differs')
    if sha(original) != '5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':
        raise ValueError('Original PE identity differs')
    pe = pefile.PE(data=original)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    cuts = []
    def write(name, value):
        (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    def cut(name, va, end, scope, code=True):
        rva=va-0x400000;raw=image[rva:end-0x400000];offset=pe.get_offset_from_rva(rva)
        if original[offset:offset+len(raw)]!=raw:
            raise ValueError('Original PE cut differs: '+name)
        (OUT/(name+'.bin')).write_bytes(raw)
        rows=list(md.disasm(raw,va)) if code else []
        if code and sum(i.size for i in rows)!=len(raw):
            raise ValueError('Incomplete static decode: '+name)
        if code:
            (OUT/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
                f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8')
        cuts.append(dict(name=name,va=f'{va:08X}',end_exclusive=f'{end:08X}',bytes=len(raw),sites=len(rows),
                         sha256=sha(raw),original_pe_offset=offset,original_pe_equal=True,scope=scope,code=code))
    cut('e6-complete-receiver',0x4d6d20,0x4d6da8,'Complete actual incoming12B -> primary context44/48/4C; all direct guards retained')
    cut('e6-world-case',0x4691eb,0x4691fd,'Actual primary WORLD E6 case; same U=Main+A7F2F6C')
    cut('e6-world-table-cell',0x46b96c,0x46b970,'Actual original E6 table cell',False)
    cut('e6-length-leaf',0x401246,0x40124c,'Complete actual MOV EAX,13/RET length leaf')
    cut('e6-length-table-cell',0x4016bc,0x4016c0,'Actual original E6 length table cell',False)
    cut('known-egg-open-complete',0x4d53f0,0x4d58f1,'Historical20260926 method recaptured; only needed input/body/E6 boundary newly qualified')
    cut('known-egg-open-selector-table',0x4d58f4,0x4d5910,'Seven actual3A-to3E selector table cells; not growth transformation authority',False)
    cut('known-egg-slot-guard',0x4d6c40,0x4d6c7a,'Historical complete actual guard; unsigned slot0..29 or45')
    cut('known-egg-key-guard',0x4d6c80,0x4d6d1e,'Historical complete actual slot/key+real metadata lookup guard')
    cut('known-3b-complete-receiver',0x498dd0,0x498fc2,'Historical complete actual full20 incoming retention and selected45->egg-open call')
    cut('known-3b-world-case',0x46a029,0x46a03b,'Historical actual primary3B case; same U=Main+A7F2F6C')
    cut('known-3b-world-table-cell',0x46b6c0,0x46b6c4,'Actual original3B table cell',False)
    cut('retained-e5-world-case',0x4691d9,0x4691eb,'Prior326 E5 source explicitly qualifies primary U context')
    cut('retained-e5-selected-caller',0x4d7030,0x4d7049,'Prior327 actual family1 S32 direct44 write then egg-open invocation; selected span not method entry')
    cut('retained-control-bridge',0x4d7e40,0x4d7e64,'Prior327 complete actual bridge;507150 opaque')
    for name,va in [('egg-open-declaration',0x5951ac),('egg-native-source-path',0x5951ec),
                    ('egg-slot-assertion',0x59527c),('egg-key-assertion',0x5952ac)]:
        end=image.index(0,va-0x400000)+0x400001
        cut(name,va,end,'Exact native NUL-terminated declaration only',False)
    refs=[dict(path=str(INPUT/name),sha256=sha(raw),bytes=len(raw),copied=False)
          for name,raw in [('native-image.bin',image),('originalPE.bin',original)]]
    sources=[]
    for rel in ['docs/research/current-weapon-mapping-fields-20260926.md',
                'docs/research/tw-native-e5-family-source-20261012.md',
                'src/protocol/RecoveredE5Update.h','src/game/TaiwanOwnedBagItemMaterial.h',
                'src/game/SharedTaiwanOwnedItemSelectionSource.h','docs/GOAL_ACCEPTANCE.md']:
        raw=(SERVER/rel).read_bytes();target=OUT/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        sources.append(dict(path=str(SERVER/rel),sha256=sha(raw),bytes=len(raw),retained='source/'+rel))
    write('cuts.json',cuts);write('input-references.json',refs);write('source-references.json',sources)
    write('declared-clock-import.json',[dict(iat_va=f'{i.address:08X}',dll=e.dll.decode('ascii'),name=i.name.decode('ascii'),scope='PE declaration only; never called')
        for e in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]) for i in e.imports if i.address==0x5707bc and i.name])
    print(json.dumps(dict(output=str(OUT),cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),
                         data_bytes=sum(c['bytes'] for c in cuts if not c['code']),new_gameplay_routes=0)))

if __name__=='__main__':
    main()
