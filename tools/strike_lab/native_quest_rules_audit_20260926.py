"""Read-only current quest authority audit; never imports catalogs into a DB."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .recover_quests import build_catalog
from .omega_assets import decode_csvz

ROOT=Path(__file__).resolve().parents[2]
CURRENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
NATIVE_SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
PINS={
    'missions':'659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716',
    'requirements':'e1e35ee689d12ef265be8620b21f856709976896a46edeb9f31c15622041accf',
    'daily':'4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54',
}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(value,message):
    if not value:raise ValueError(message)

def audit(client):
    catalog=build_catalog(client)
    require(not catalog['validation']['structural_issues'],'Invalid quest source structure')
    for name,pin in PINS.items():require(catalog['tables'][name]['source_sha256']==pin,'Source pin mismatch: '+name)
    tables={name:{key:table[key] for key in ('source_file','source_sha256','decoded_sha256',
            'declared_records','header_fields','field_columns')} for name,table in catalog['tables'].items()}
    daily=catalog['tables']['daily']['records']
    missing=Counter(key for row in daily for key,value in row['fields'].items() if value is None)
    messages=[];all_keys=[]
    for stem in [f'NPCMission{i:02}' for i in range(1,16)]+['DailyMission01']:
        path=client/'Data2/Patch/Comm'/f'{stem}.csvZ'
        raw=path.read_bytes();decoded=decode_csvz(raw)
        lines=decoded.split(b'\n');lines=[line.rstrip(b'\r') for line in lines if line.rstrip(b'\r')]
        header=lines[1].split(b',');declared=int(header[1])
        rows=[line.split(b',',1) for line in lines[2:]]
        require(all(len(row) in (1,2) and row[0].isdigit() for row in rows),'Unexpected message record shape: '+stem)
        keys=[int(row[0]) for row in rows]
        require(len(rows)==declared and len(set(keys))==len(keys),'Message count/key mismatch: '+stem)
        if stem!='DailyMission01':all_keys.extend(keys)
        messages.append(dict(source_file=path.relative_to(client).as_posix(),source_sha256=sha(raw),
            decoded_sha256=sha(decoded),declared=declared,rows=len(rows),key_min=min(keys),key_max=max(keys),
            missing_text_rows=sum(len(row)==1 for row in rows),
            schema='key[,text bytes]; id-only rows retained',authority='PRESENTATION_TEXT_ONLY'))
    require(len(all_keys)==len(set(all_keys)),'NPC mission message keys overlap')
    image=(client/'God2.exe').read_bytes()
    original=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    require(sha(image)==CURRENT_SHA and sha(original)==NATIVE_SHA,'Native identity changed')
    import pefile
    pe=pefile.PE(data=image)
    spans=[]
    for label,start,stop in (
        ('Mission_data description lookup',0xc9581,0xc95db),
        ('Quest journal slot writer',0xc9670,0xc9770),
        ('ACTMIS row parser',0x587c4,0x588e1),
        ('ACTMIS category20 display consumer',0xb9f8d,0xba060),
        ('C2S85 producer',0x97dc0,0x97e00),
        ('S2C7A receiver header',0xc7f10,0xc8240)):
        current=pe.get_data(start,stop-start);prior=original[start:stop]
        require(len(current)==stop-start,'Truncated native span')
        spans.append(dict(label=label,rva_start=hex(start),rva_end_exclusive=hex(stop),
                          current_sha256=sha(current),prior_sha256=sha(prior),equal=current==prior))
    gaps=('prerequisites','rewards','conditions','transitions','npc_references','monster_references')
    return dict(schema='native-quest-rules-audit-20260926-v1',
        qualification='CURRENT_SOURCE_AND_CODE_IDENTITY_AUDIT_NOT_GAMEPLAY_COMPLETION',
        current_client_sha256=sha(image),prior_native_sha256=sha(original),source_tables=tables,
        counts=catalog['counts'],daily_missing_field_counts=dict(sorted(missing.items())),
        daily_incomplete_rows=[dict(source_line=row['source_line'],index=row['fields']['index'],
            branch=row['fields']['branch'],missing=[key for key,value in row['fields'].items() if value is None])
            for row in daily if any(value is None for value in row['fields'].values())],
        message_tables=messages,npc_mission_message_rows=len(all_keys),
        native_code_comparison=spans,
        mission_rule_gaps={field:sum(q[field]=='UNKNOWN' for q in catalog['quests']) for field in gaps},
        mission_audit=[dict(id=q['id'],name=q['name'],source_line=q['source_line'],
            description_rows=len(q['objectives_text']),**{field:q[field] for field in gaps}) for q in catalog['quests']],
        important_count_boundary='counts.executable_transition_rules=0 describes rules recovered from these three source tables; '
            'counts.server_integrated=0 is the extractor scope, not current server runtime coverage. '
            'Custom town quest and native display imports exist separately.',
        namespaces='No Mission_data/ACTMIS/daily/message-ID join is established merely by equal numeric IDs.',
        retired_inputs_read=False,database_opened=False,client_executed=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();client=args.client.resolve();output=args.output.resolve()
    require(not output.is_relative_to(client),'Output must not enter client directory')
    result=audit(client)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('counts','npc_mission_message_rows','daily_missing_field_counts','mission_rule_gaps')},ensure_ascii=False))
    require(all(span['equal'] for span in result['native_code_comparison']),'Selected current code differs from original proof')
    return 0

if __name__=='__main__':raise SystemExit(main())
