"""Bounded static source capture only: file/hash/PE/Capstone/table, no native execution."""
from pathlib import Path
import hashlib
import json
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BASE = Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
INPUT = BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
OUT = BASE/'tw-native-petegg-selection-source-329'
SERVER = Path('C:/Users/risei/Desktop/God2/God2-Server')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    target = OUT/'native'
    target.mkdir(exist_ok=False)
    image = (INPUT/'native-image.bin').read_bytes()
    original = (INPUT/'originalPE.bin').read_bytes()
    assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
    pe=pefile.PE(data=original)
    md=Cs(CS_ARCH_X86,CS_MODE_32)
    cuts=[]
    def cut(name, va, end, scope, code=True):
        rva=va-0x400000
        raw=image[rva:end-0x400000]
        offset=pe.get_offset_from_rva(rva)
        assert original[offset:offset+len(raw)]==raw
        (target/(name+'.bin')).write_bytes(raw)
        rows=list(md.disasm(raw,va)) if code else []
        if code:
            assert sum(i.size for i in rows)==len(raw)
            (target/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
                f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8')
        cuts.append(dict(name=name,va=f'{va:08X}',end_exclusive=f'{end:08X}',bytes=len(raw),
                         sha256=sha(raw),original_pe_offset=offset,original_pe_equal=True,
                         code=code,instruction_sites=len(rows),scope=scope))
    cut('initializer-complete',0x4d4b80,0x4d4d7e,'Complete actual method; direct literal45 U8 and scalar reset. Resource cache children remain opaque.')
    cut('guarded-reset-complete',0x4d71f0,0x4d7230,'Complete actual flags/WORD guard then initializer then conditional close; final child state opaque.')
    cut('close-complete',0x4d5910,0x4d5968,'Historical actual complete close method; direct BYTE50=0 and opaque children; no direct U8 assignment.')
    cut('action-complete',0x4d6940,0x4d6b72,'Complete actual action method with all exits and direct producer calls; UI descendants opaque.')
    cut('action-table',0x4d6b74,0x4d6b9c,'Actual ten-entry control15..24 jump table',False)
    cut('b1-producer-complete',0x4d6ba0,0x4d6bc2,'Complete actual opcodeB1 body1 producer; preserves arg BYTE; queue4132E0 previously known.')
    cut('action-eligibility-leaf',0x4d68c0,0x4d68c8,'Complete actual leaf ignores arg and returns1; RET4.')
    cut('action-state-leaf',0x4d7df0,0x4d7e12,'Complete signed WORD52 predicate; FFFF or30..32 returns0, others1.')
    cut('primary-setup-complete',0x4817c0,0x481bd9,'Historical primary setup recaptured complete; ECX=U; actual initializer at481A2A; later children opaque.')
    cut('primary-action-dispatch-complete',0x4820a0,0x48314f,'Complete actual primary UI dispatch; only needed PetEgg branch qualified, all other callees opaque.')
    cut('primary-action-main-prefix',0x466b00,0x466ba1,'Actual Main method entry through needed invocation, selected prefix NOT complete method; EDI=Main+A7F2F6C.')
    cut('retained-queue-context-setter',0x496170,0x496199,'Prior251 complete actual G setter at U86874; historical no novelty.')
    cut('retained-primary-setup-invocation',0x465274,0x465328,'Prior251 selected caller span; NOT complete method; actual U=Main+A7F2F6C setup argument/context provenance.')
    cut('boundary-initializer-before',0x4d4b70,0x4d4b80,'Boundary evidence only, not a method.')
    cut('boundary-initializer-after',0x4d4d7e,0x4d4d90,'Boundary raw bytes only, not code/method.',False)
    cut('boundary-action-before',0x4d6936,0x4d6940,'Boundary evidence only, not a method.')
    cut('boundary-dispatch-before',0x482098,0x4820a0,'Padding before actual method.',False)
    table=struct.unpack('<10I',image[0xd6b74:0xd6b9c])
    (target/'action-targets.tsv').write_text('index\tcontrol_decimal\ttarget_va\n'+''.join(
        f'{n}\t{n+15}\t{v:08X}\n' for n,v in enumerate(table)),encoding='utf8')
    refs=[dict(path=str(INPUT/n),sha256=sha(b),bytes=len(b),copied=False)
          for n,b in [('native-image.bin',image),('originalPE.bin',original)]]
    (target/'input-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8')
    (target/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8')
    sources=[]
    for rel in ['docs/research/current-weapon-mapping-fields-20260926.md',
                'docs/research/tw-native-world-roster-initial-source-20261010.md',
                'docs/research/tw-native-e6-petegg-input-source-20261012.md',
                'docs/research/tw-native-e5-family-source-20261012.md',
                'docs/GOAL_ACCEPTANCE.md']:
        raw=(SERVER/rel).read_bytes()
        p=OUT/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        sources.append(dict(path=str(SERVER/rel),sha256=sha(raw),bytes=len(raw),retained='source/'+rel))
    ledger=SERVER/'artifacts/integration/packet-connections-20261006/packet-route-ledger.json'
    raw=ledger.read_bytes()
    sources.append(dict(path=str(ledger),sha256=sha(raw),bytes=len(raw),copied=False,
                        scope='Hash reference only; no full ledger copy.'))
    (OUT/'source-references.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),
                         data_bytes=sum(c['bytes'] for c in cuts if not c['code']),new_routes=0)))

if __name__=='__main__':
    main()
