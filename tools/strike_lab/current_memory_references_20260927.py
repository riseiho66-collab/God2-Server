"""Read live loaded catalog references, without dumping unrelated process data."""
import array
import json
import struct
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.strike_lab import current_live_memory_catalog_20260927 as native

original_static=native.static_catalogs

def references(handle,scan_result):
    result=original_static(handle,scan_result)
    owner=int(result['owner'],16)
    npc_start=owner+0x121ea
    npc_keys={r['key'] for r in result['npc_records']}
    enemy_start=int(result['enemy_arena'],16)
    quest_start=int(scan_result['quest_catalogs'][0]['base'],16)
    ranges=[('npc_template',npc_start,npc_start+94*(result['npc_highwater']+1),94),
            ('enemy_display',enemy_start,enemy_start+26*len(result['enemy_records']),26),
            ('quest_display',quest_start,quest_start+40*418,40)]
    hits={kind:[] for kind,_,_,_ in ranges};counts={kind:0 for kind in hits}
    scanned=0
    for start,end,kind,protect in native.regions(handle):
        # Only private heap/data. Numeric coincidences are retained as candidates,
        # never promoted into a spawn, reward or combat-stat interpretation.
        if kind!=0x20000:continue
        at=(start+3)&~3
        while at<end:
            length=min(1<<20,end-at)&~3
            if not length:break
            native.require(scanned+length<=800*(1<<20),'REFERENCE_SCAN_LIMIT')
            raw=native.read(handle,at,length)
            if raw and len(raw)==length:
                scanned+=length;values=array.array('I');values.frombytes(raw)
                for index,value in enumerate(values):
                    for label,lo,hi,stride in ranges:
                        if lo<=value<hi and (value-lo)%stride==0:
                            key=(value-lo)//stride
                            if label=='npc_template' and key not in npc_keys:continue
                            counts[label]+=1
                            if len(hits[label])<512:
                                hits[label].append({'reference_address':hex(at+4*index),
                                    'target_address':hex(value),'catalog_index':key,
                                    'authority':'LIVE_ALIGNED_POINTER_CANDIDATE_NOT_SPAWN_OR_RULE'})
            at+=length
    qualified_groups={int(g['descriptor_address'],16)+8:g for g in result['enemy_groups']}
    for h in hits['enemy_display']:
        group=qualified_groups.get(int(h['reference_address'],16))
        if group and h['target_address']==group['record_pointer']:
            h['authority']='LIVE_SOURCE_ENEMY_GROUP_DESCRIPTOR_NOT_SPAWN'
            h['area']=group['area'];h['scene']=group['scene'];h['count']=group['count']
    for h in hits['npc_template']:
        address=int(h['reference_address'],16)
        nearby=native.read(handle,max(0x10000,address-16),48)
        if nearby and len(nearby)==48:
            words=struct.unpack('<24H',nearby)
            printable=sum(w==0 or 32<=w<=126 or 0x3000<=w<=0x9fff for w in words)
            h['nearby_utf16_text_likelihood']=round(printable/len(words),3)
            # Classification only. No unrelated strings or raw neighboring data
            # are retained; numerical pointer matches are never authority.
            h['neighboring_catalog_pointer_fields']=sum(any(lo<=w<hi and (w-lo)%stride==0 for _,lo,hi,stride in ranges) for w in struct.unpack('<12I',nearby))
    result['live_heap_references']={'heap_bytes_read':scanned,'counts':counts,'candidates':hits,
        'scope':'ReadProcessMemory only; next step is qualify each reference owner and native writer before semantic use.'}
    result['all_npc_memory_fields']=[{'key':r['key'],'address':r['address'],
        'source_prefix28_hex':r['record94_hex'][:56],
        'server_cache_nonzero':any(bytes.fromhex(r['record94_hex'])[28:]),
        'flags_word':r['flags_word'],'appearance_code':r['appearance_code']}
        for r in result['npc_records']]
    result['all_catalog_coverage']={'npc_loaded_records':len(result['npc_records']),
        'npc_highest_selector':result['npc_highwater'],
        'monster_arena_records':len(result['enemy_records']),
        'monster_lookup_groups':len(result['enemy_groups']),
        'monster_lookup_visible':sum(r['count'] for r in result['enemy_groups']),
        'native_spawns_confirmed':0,'original_combat_stats_confirmed':0}
    return result

if __name__=='__main__':
    native.static_catalogs=references
    # Preserve the established hidden-desktop process owner and cleanup code,
    # while its child executes this additional read-only memory qualification.
    native.__file__=str(Path(__file__).resolve())
    raise SystemExit(native.main())
