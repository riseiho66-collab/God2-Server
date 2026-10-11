"""Own-server current-client test on an explicitly hidden God2Lab desktop.

No screenshots, code injection, process-memory writes or desktop switching.
Only read-only native state checks and window-local mouse/keyboard messages.
"""
import argparse
import ctypes as c
import hashlib
from ctypes import wintypes as w
import json
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
import time
import psutil
from private_potion_ui import click,drag,game_window,type_ascii,user
from private_inventory_memory import kernel,read,Region
from private_inventory_move_ui import desktop_names,wait_until,require

def saved(db):
    with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as connection:
        return {'resources':connection.execute('select hp,max_hp,mp,max_mp,revision from character_resources where character_id=4').fetchone(),
                'selection':connection.execute('select row_key,revision from character_deity_selection where character_id=4').fetchone(),
                'deity_keys':[row[0] for row in connection.execute('select row_key from character_deities where character_id=4 order by row_key')],
                'pets':[(slot,metadata.hex(),stats.hex(),revision) for slot,metadata,stats,revision in connection.execute(
                    'select slot,metadata,stats,revision from character_pet2_slots where character_id=4 order by slot')]}

def native_world_records(handle,ui):
    source=int.from_bytes(read(handle,ui+0x86888,4),'little');world=source-0x90-0x1539683c
    require(world>0x10000,'INVALID_WORLD_OWNER')
    found={}
    for name,offset,count,identity in (('npc',0x1539aed8,256,3793),('monster',0x153b8758,256,123)):
        pool=world+offset
        for index in range(count):
            address=pool+0x70+index*0x1d8;raw=read(handle,address,0x1d8)
            if raw and int.from_bytes(raw[:4],'little')==identity:
                require(name not in found,'DUPLICATE_NATIVE_INSTANCE')
                sprite_handle=int.from_bytes(raw[10:12],'little',signed=True)
                renderer=int.from_bytes(read(handle,pool+4,4),'little')
                require(renderer>0x10000 and 0<=sprite_handle<4096,'NATIVE_WORLD_SPRITE_UNAVAILABLE')
                node=read(handle,renderer+0x10+sprite_handle*0x290,0x48)
                surface=int.from_bytes(read(handle,renderer+4,4),'little')
                command=int.from_bytes(node[14:16],'little',signed=True)
                require(surface>0x10000 and 0<=command<4096,'NATIVE_WORLD_RENDER_COMMAND_MISSING')
                command_type=read(handle,surface+0x1258+200*command,1)[0]
                require(node[0]==2 and command_type==2,'NATIVE_WORLD_RENDER_COMMAND_INACTIVE')
                require(node[22:24]==raw[4:6],'NATIVE_WORLD_RENDER_RESOURCE_MISMATCH')
                found[name]={'address':hex(address),'identity':identity,
                    'facing':int.from_bytes(raw[8:10],'little'),'x':int.from_bytes(raw[16:20],'little'),
                    'y':int.from_bytes(raw[20:24],'little'),'screen':list(struct.unpack_from('<2f',raw,24)),
                    'name_handle':int.from_bytes(raw[12:14],'little'),'level_cache':raw[0x17b],
                    'sprite_handle':sprite_handle,'renderer_active':True,'resource':int.from_bytes(raw[4:6],'little',signed=True)}
    return found

def check_native_world_records(value):
    require(set(value)=={'npc','monster'},'NATIVE_WORLD_INSTANCES_MISSING')
    for name,expected in (('npc',(124,126,5)),('monster',(128,126,6))):
        row=value[name]
        require((row['x'],row['y'],row['facing'])==expected,'NATIVE_WORLD_POSITION_FACING_MISMATCH')
        require(all(abs(x)<100000 for x in row['screen']),'NATIVE_WORLD_SCREEN_COORDINATES_INVALID')
    require(value['monster']['level_cache']==27,'NATIVE78_MONSTER_LEVEL_NOT_APPLIED')

def saved_role_auxiliary(db):
    with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as connection:
        row=connection.execute('select logical,revision,origin,provenance,client_sha256,design_id '
            'from character_role_auxiliary_snapshots where character_id=4').fetchone()
    require(row is not None,'OWNED_ROLE_AUXILIARY_ROW_MISSING')
    return {'logical_hex':row[0].hex(),'revision':row[1],'origin':row[2],'provenance':row[3],
            'client_sha256':row[4],'design_id':row[5]}

def check_role_auxiliary(value,owned,resources):
    expected=bytearray(61);expected[0]=0x2c
    for offset,number in ((1,2),(5,3),(9,4),(13,5),(45,56),(49,77),(53,88),(57,99)):
        struct.pack_into('<I',expected,offset,number)
    require(owned=={'logical_hex':expected.hex(),'revision':1,'origin':'CUSTOM_TEST_NOT_NATIVE',
        'provenance':'hidden-fixture/client6bf/CUSTOM-0045',
        'client_sha256':'6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98',
        'design_id':'CUSTOM-0045'},'OWNED_ROLE_AUXILIARY_FIXTURE_MISMATCH')
    require(value['role_auxiliary']=={'modifiers':[2,3,4,5],
        'physical_attack':77,'physical_defense':56,'magical_attack':99,'magical_defense':88,
        'received_values':[0,0,0,0,0],'positive_mask':0,'negative_mask':0},
        'NATIVE_ROLE_AUXILIARY_RESTORE_MISMATCH')
    require(value['role_resources']==list(resources[:4]),'ROLE_AUXILIARY_VITALS_CHANGED')
    require(value['deity_count']==0 and value['deity_selected_key'] is None,'ROLE_AUXILIARY_NO_GOD_FIXTURE_REQUIRED')

def saved_weapons(db):
    with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as connection:
        rows=connection.execute('SELECT s.slot,s.item_id,s.count,s.revision,s.source_sha256,'
            'm.logical20,m.revision,m.origin,m.provenance,m.source_sha256,m.client_sha256,m.design_id '
            'FROM diagnostic_inventory_slots s LEFT JOIN character_weapon_slot_metadata m '
            'ON m.character_id=s.character_id AND m.slot=s.slot '
            'WHERE s.character_id=4 AND (s.slot BETWEEN 0 AND 29 OR s.slot=34) ORDER BY s.slot').fetchall()
    require([r[0] for r in rows]==list(range(30))+[34],'EXPLICIT_WEAPON_SLOT_SET_MISSING')
    return {str(r[0]):{'item':r[1],'count':r[2],'revision':r[3],'scalar_source':r[4],
        'metadata':r[5].hex() if r[5] is not None else bytes(20).hex(),
        'metadata_revision':r[6],'origin':r[7],'provenance':r[8],
        'source':r[9],'client':r[10],'design':r[11]} for r in rows}

def saved_weapon_appearance(db):
    with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as connection:
        row=connection.execute('select logical,base_components,revision,origin,provenance,client_sha256,design_id '
            'from character_player_appearance_snapshots where character_id=4').fetchone()
    require(row is not None,'OWNED_WEAPON_APPEARANCE_SNAPSHOT_MISSING')
    require(len(row[0])==15 and row[0][0]==0xda and len(row[1])==8,'OWNED_WEAPON_APPEARANCE_FRAMING_MISMATCH')
    require(row[3]=='CUSTOM_TEST_NOT_NATIVE' and row[5]=='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98' and row[6]=='CUSTOM-0047','OWNED_WEAPON_APPEARANCE_AUTHORITY_MISMATCH')
    return {'logical_hex':row[0].hex(),'base_components':row[1].hex(),'revision':row[2],
        'origin':row[3],'provenance':row[4],'client_sha256':row[5],'design_id':row[6]}

def native_weapon_appearance(handle,ui):
    source=int.from_bytes(read(handle,ui+0x86888,4),'little');root=source-0x90;world=root-0x1539683c
    require(world>0x10000,'WEAPON_APPEARANCE_WORLD_POINTER_INVALID')
    identity=int.from_bytes(read(handle,root,2),'little')
    components=read(handle,root+0x4584,8);scalars=read(handle,root+0x4695,4)
    live=read(handle,world+0xa7e04d0,32)
    require(components is not None and len(components)==8 and scalars is not None and len(scalars)==4 and live is not None and len(live)==32,'WEAPON_APPEARANCE_SHORT_READ')
    override=read(handle,world+0x1539ad70,1)[0]
    appearance_selectors=int.from_bytes(read(handle,root+0x44,4),'little')
    logical=b'\xda'+struct.pack('<HHBB',identity,int.from_bytes(scalars[1:3],'little'),scalars[0],scalars[3])+components
    result={'world':hex(world),'role_root':hex(root),'logical_hex':logical.hex(),'components':components.hex(),
        'identity':identity,'transform':int.from_bytes(scalars[1:3],'little'),'scalar5':scalars[0],'scalar6':scalars[3],
        'override_byte':override,'resource_selector':(appearance_selectors>>18)&255,
        'accessory_selector':(appearance_selectors>>10)&255,
        'live_components':[{'handle':struct.unpack_from('<h',live,4+6*i)[0],
            'variant':live[8+6*i],'entry_hex':live[4+6*i:10+6*i].hex()} for i in range(4)]}
    if result['resource_selector']==0:
        # Current 61270 -> 63DE0 -> 526C0: resolve this ordinary component's
        # source row, then compare its live cached handle. Handles may be reused.
        from omega_assets import decode_csvz
        source_path=Path(__file__).resolve().parents[3]/'God2/Data2/Patch/HeroDoll.csvZ'
        raw=source_path.read_bytes()
        require(hashlib.sha256(raw).hexdigest()=='df2fa65e0b159b18303b2e135cacc690e0e02e4ea12560cacda3f0d8e6ae1359','WEAPON_APPEARANCE_HERODOLL_SOURCE_CHANGED')
        lines=decode_csvz(raw).splitlines();start=int(lines[0].split(b',')[2]);count=int(lines[0].split(b',')[4])
        key=f'r{(components[6]&15)+1}w{components[6]>>4}{components[7]&31:02d}'
        matched=[(ordinal,row.split(b',')) for ordinal,row in enumerate(lines[start-1:]) if b''.join(row.split(b',')[:2]).decode('ascii')==key]
        require(len(matched)==1,'WEAPON_APPEARANCE_RESOURCE_KEY_MISSING')
        ordinal,fields=matched[0];manager=world+0xaa364b8
        bank_index=int.from_bytes(read(handle,manager+0x16ce18,4),'little')
        require(bank_index<2,'WEAPON_APPEARANCE_RESOURCE_BANK_OUTSIDE_SCOPE')
        bank=manager+bank_index*0xad610+0x682e0
        hero=bank+0x12d78  # Current 463E10 adds this before 4526C0 lookup.
        records=int.from_bytes(read(handle,hero+0x121ec,4),'little')
        loaded_count=int.from_bytes(read(handle,hero+0x121f0,4),'little')
        require(records>0x10000 and loaded_count==count,
            f'WEAPON_APPEARANCE_RESOURCE_TABLE_MISMATCH hero={hero:x} records={records:x} count={loaded_count} expected={count}')
        record=read(handle,records+ordinal*44,44)
        require(record is not None and len(record)==44,'WEAPON_APPEARANCE_RESOURCE_RECORD_SHORT')
        filename=record[:30].split(b'\0')[0];cached_handle=int.from_bytes(record[30:32],'little')
        require(filename==fields[3] and cached_handle==result['live_components'][3]['handle'],'WEAPON_APPEARANCE_NATIVE_RESOURCE_BINDING_MISMATCH')
        result['weapon_resource']={'key':key,'filename':filename.decode('ascii'),'source_line':start+ordinal,
            'source_description':fields[6].decode('cp950') if len(fields)>6 else '',
            'record':hex(records+ordinal*44),'cached_handle':cached_handle,'bank_index':bank_index}
    return result

def check_weapon_appearance(owned,current,baseline,initial_native,item,revision):
    base=bytes.fromhex(baseline['base_components']);expected=bytearray(bytes.fromhex(baseline['logical_hex']))
    expected[7:15]=base
    if item:
        require(item in (1,2),'WEAPON_APPEARANCE_FIXTURE_MAPPING_SCOPE')
        expected[13]=base[6]&15;expected[14]=item-1
    require(owned['base_components']==baseline['base_components'],'WEAPON_APPEARANCE_BASE_COMPONENTS_CHANGED')
    require(owned['revision']==revision and owned['logical_hex']==expected.hex(),'WEAPON_APPEARANCE_DB_AFTER_STATE_MISMATCH')
    require(current['logical_hex']==owned['logical_hex'],'WEAPON_APPEARANCE_NATIVE_AFTER_STATE_MISMATCH')
    require(current['identity']==4 and current['transform']==0 and not current['override_byte']&0x10,'WEAPON_APPEARANCE_NOT_NORMAL_UNMOUNTED')
    require(current['resource_selector']==0,'WEAPON_APPEARANCE_DRIVER_SELECTOR_NOT_ZERO')
    require(current['components'][:12]==baseline['base_components'][:12],'WEAPON_APPEARANCE_CHANGED_OTHER_COMPONENT_BYTES')
    for i,component in enumerate(current['live_components']):
        require(0<=component['handle']<512,'WEAPON_APPEARANCE_COMPONENT_HANDLE_UNAVAILABLE')
        require(component['variant']==expected[8+2*i]>>5,'WEAPON_APPEARANCE_COMPONENT_VARIANT_MISMATCH')
        if i<3:
            # Only handle and variant have a qualified stable meaning here.
            # Retain the other entry bytes as diagnostics, not a state gate.
            require(all(component[key]==initial_native['live_components'][i][key] for key in ('handle','variant')),
                'WEAPON_APPEARANCE_CHANGED_OTHER_LIVE_COMPONENTS')

def find_weapon_owner(handle, initial):
    """Bounded read-only scan for both complete synthetic slot records."""
    pattern=b''.join(struct.pack('<I',initial[str(i)]['count'])+bytes.fromhex(initial[str(i)]['metadata']) for i in (0,1))
    address=0x10000;scanned=0;matches={}
    while address<0x80000000 and scanned<800*1024*1024:
        region=Region()
        if not kernel.VirtualQueryEx(handle,address,c.byref(region),c.sizeof(region)):break
        base=region.BaseAddress or address;end=min(base+region.RegionSize,0x80000000)
        if region.State==0x1000 and not region.Protect&0x101:
            offset=base;tail=b''
            while offset<end:
                size=min(1024*1024,end-offset);raw=read(handle,offset,size)
                if raw:
                    scanned+=len(raw);combined=tail+raw;at=combined.find(pattern)
                    while at>=0:
                        ui=offset-len(tail)+at-0x8560c
                        index_raw=read(handle,ui+0x232dc8,2)
                        index=int.from_bytes(index_raw,'little',signed=True) if index_raw else -1
                        if 0<=index<128 and read(handle,ui+0x855f0,2)==b'\xff\xff':
                            mode=read(handle,ui+0xe2988+0x2a08*index,1)
                            if mode==b'\x23':matches[ui]={'ui':hex(ui),'inventory_source_index':index,'inventory_source_mode':'23','selected_inventory_slot':'ffff'}
                        at=combined.find(pattern,at+1)
                    tail=combined[-(len(pattern)-1):]
                else:tail=b''
                offset+=size
        address=end if end>address else address+0x1000
    require(len(matches)==1,'EXPECTED_ONE_WEAPON_INVENTORY_OWNER')
    return list(matches.values())

def native_weapon_slots(handle,ui):
    return {str(slot):read(handle,ui+0x8560c+slot*24,24).hex() for slot in [*range(30),34]}

def weapon_slots_agree(actual,owned):
    return all(actual[slot]==(struct.pack('<I',row['count'])+bytes.fromhex(row['metadata'])).hex()
        for slot,row in owned.items())

def weapon_after_state(prior,after,source,destination):
    source=str(source);destination=str(destination)
    if after[source]['revision']!=prior[source]['revision']+1 or after[destination]['revision']!=prior[destination]['revision']+1:return False
    for slot in prior:
        if slot not in (source,destination) and after[slot]!=prior[slot]:return False
    for slot,other in ((destination,source),(source,destination)):
        expected=prior[other]
        if expected['count']:
            if any(after[slot][key]!=expected[key] for key in ('item','count','metadata','origin','provenance','source','client','design')):return False
        else:
            if after[slot]['item'] or after[slot]['count']:return False
            if after[slot]['metadata']!='0000'+prior[slot]['metadata'][4:]:return False
            if after[slot]['origin']!='EMPTY_SLOT_POLICY':return False
        if after[slot]['metadata_revision']!=after[slot]['revision']:return False
        if after[slot]['scalar_source']!=prior[slot]['scalar_source']:return False
    return sum(row['count'] for row in after.values())==2

def weapon_icon_state(handle,ui,widget,slot,item):
    resource=int.from_bytes(read(handle,ui+0xcff70,4),'little')
    # B2D40 is the inline item-pointer array, not a pointer to another table.
    definition=int.from_bytes(read(handle,resource+0xb2d40+item*4,4),'little')
    require(definition>0x10000,'WEAPON_NATIVE_DEFINITION_MISSING')
    group,action=struct.unpack('<Hh',read(handle,definition+0x116,4))
    require(read(handle,definition+0x11a,1)[0]&4,'WEAPON_NATIVE_EQUIPPABLE_FLAG_MISSING')
    manager=ui+0xe2170
    graphics=int.from_bytes(read(handle,manager+8,4),'little')
    render=int.from_bytes(read(handle,manager+widget*0x2a08+0x81c,2),'little')
    require(graphics>0x10000 and render<4096,'WEAPON_NATIVE_ICON_RENDERER_MISSING')
    node=graphics+0x10+render*0x290
    actual_action=int.from_bytes(read(handle,node+0x180+slot*2,2),'little',signed=True)
    image_handle=int.from_bytes(read(handle,node+0xac+slot*2,2),'little')
    require(action>=0 and actual_action==action and image_handle<5000,'WEAPON_NATIVE_ICON_ACTION_MISMATCH')
    pool=int.from_bytes(read(handle,graphics+4,4),'little')
    image_pointer=int.from_bytes(read(handle,pool+image_handle*200+0x12e4,4),'little')
    image_resource=int.from_bytes(read(handle,pool+image_handle*200+0x12ec,4),'little')
    require(image_pointer>0x10000 and image_resource not in (0,0xcdcdcdcd),'WEAPON_NATIVE_ICON_RESOURCE_MISSING')
    name=read(handle,definition+8,38).split(b'\0')[0].decode('cp950')
    level=int.from_bytes(read(handle,definition+0x11e,2),'little')
    require((name,level)=={1:('菜刀',1),2:('砍刀',10)}[item],'WEAPON_NATIVE_SOURCE_NAME_OR_LEVEL_MISMATCH')
    return {'slot':slot,'key':item,'definition':hex(definition),'name':name,'definition_encoded_level':level,
        'group':group,'definition_action':action,'actual_action':actual_action,'render_handle':render,
        'image_handle':image_handle,'image_pointer':hex(image_pointer),'image_resource':hex(image_resource)}

def fresh_weapon_hover(hwnd,handle,ui,widget,owned,target):
    target=str(target);other=next((int(s) for s,r in owned.items() if r['count'] and s!=target),None)
    require(other is not None,'WEAPON_FRESH_HOVER_ALTERNATE_MISSING')
    def hover(slot):
        x,y=control_point(handle,ui,widget,slot);rect=w.RECT()
        require(user.GetClientRect(hwnd,c.byref(rect)) and rect.right>0 and rect.bottom>0,'WEAPON_CLIENT_RECT_MISSING')
        px=round(x*rect.right/800);py=round(y*rect.bottom/600)
        require(user.PostMessageW(hwnd,0x200,0,(py<<16)|px),'WEAPON_HOVER_MESSAGE_FAILED')
        expected=bytes.fromhex(owned[str(slot)]['metadata'])
        def tooltip_ready():
            panel=int.from_bytes(read(handle,ui+0x232e56,2),'little',signed=True)
            if not 0<=panel<128 or read(handle,0x5b7838,20)!=expected:return None
            node=ui+0xe2170+0x818+panel*0x2a08
            flags=int.from_bytes(read(handle,node,2),'little');renderer=int.from_bytes(read(handle,node+4,2),'little')
            if not flags&0x20 or renderer>=4096:return None
            return {'panel':panel,'flags':flags,'renderer':renderer}
        tooltip=wait_until(tooltip_ready,6,'WEAPON_FRESH_HOVER_CACHE_OR_PANEL_NOT_UPDATED')
        return {'slot':slot,'point':[x,y],'cache':read(handle,0x5b7838,20).hex(),
            'key':int.from_bytes(read(handle,0x5b7830,2),'little'),
            'type':int.from_bytes(read(handle,0x5926b0,2),'little'),
            'xy':list(struct.unpack('<2H',read(handle,0x5926b2,4))),'tooltip':tooltip}
    alternate=hover(other);before=read(handle,0x5b7838,20)
    require(before!=bytes.fromhex(owned[target]['metadata']),'WEAPON_HOVER_WOULD_BE_CACHE_HIT')
    result=hover(int(target))
    require(result['key']==owned[target]['item'],'WEAPON_HOVER_KEY_MISMATCH')
    require(result['type']==0x12,'WEAPON_HOVER_TYPE_MISMATCH')
    return {'alternate':alternate,'target':result,'fresh_cache_transition':True,
        'icon':weapon_icon_state(handle,ui,widget,int(target),owned[target]['item'])}

def native(handle,ui):
    actor=int.from_bytes(read(handle,ui+0x86888,4),'little')
    pet_manager=int.from_bytes(read(handle,ui+0x232ebc,4),'little')
    require(actor>0x10000 and pet_manager>0x10000,'NATIVE_OWNER_POINTERS_UNAVAILABLE')
    selected=int.from_bytes(read(handle,actor+0xd0,4),'little')
    # UI+86888 publishes root+90 (role source); map fields belong to root.
    root=actor-0x90
    return {'world_map':{'kind':int.from_bytes(read(handle,root+0x10,4),'little'),
                'scene':int.from_bytes(read(handle,root+0x14,4),'little'),'area':int.from_bytes(read(handle,root+0x18,2),'little')},
            'role_resources':list(struct.unpack('<4I',read(handle,actor+0x5c,16))),
            'role_auxiliary':{'modifiers':list(struct.unpack('<4h',read(handle,actor+0x88,8))),
                'physical_attack':int.from_bytes(read(handle,actor+0x94,4),'little'),
                'physical_defense':int.from_bytes(read(handle,actor+0x98,4),'little'),
                'magical_attack':int.from_bytes(read(handle,actor+0x9c,4),'little'),
                'magical_defense':int.from_bytes(read(handle,actor+0xa0,4),'little'),
                'received_values':list(struct.unpack('<5I',read(handle,actor+0xa4,20))),
                'positive_mask':int.from_bytes(read(handle,actor+0xb8,2),'little'),
                'negative_mask':int.from_bytes(read(handle,actor+0xba,2),'little')},
            'quest_journal':list(struct.unpack('<15I',read(handle,ui+0xc2104,60))),
            'world_clock':list(struct.unpack('<2I',read(handle,actor+0x44ac,8))),
            'deity_count':read(handle,actor+0xd4,1)[0],
            'deity_selected_key':int.from_bytes(read(handle,selected,2),'little') if selected else None,
            'deity_keys':[int.from_bytes(read(handle,actor+0xd8+i*0x3ec,2),'little') for i in range(read(handle,actor+0xd4,1)[0])],
            'deity_vitals':[read(handle,actor+0xd8+i*0x3ec+0x2c,8).hex() for i in range(read(handle,actor+0xd4,1)[0])],
            'pet_slots':{str(slot):read(handle,ui+0x8560c+slot*24,24).hex() for slot in range(42,45)},
            'pet_cache':{str(slot):read(handle,pet_manager+(slot-42)*72,72).hex() for slot in range(42,45)},
            'pet1_cache':{str(slot):read(handle,ui+0xa6d8+(slot-42)*52,52).hex() for slot in range(42,45)}}

def control_point(handle,ui,widget_index,control):
    require(0<=widget_index<128,'INVALID_WIDGET_ID')
    base=ui+0xe2170+0x818+widget_index*0x2a08
    bounds=read(handle,base+0xa0+control*100+0x10,16)
    require(bounds is not None,'NATIVE_CONTROL_RECT_UNAVAILABLE')
    left,top,right,bottom=struct.unpack('<4i',bounds)
    require(0<=left<right<=800 and 0<=top<bottom<=600,'NATIVE_CONTROL_RECT_OUTSIDE_CLIENT')
    return ((left+right)//2,(top+bottom)//2)

def agrees(native_value,db):
    if native_value['role_resources']!=list(db['resources'][:4]):return False
    selection=db['selection'][0] if db['selection'] else None
    if native_value['deity_selected_key']!=selection or native_value['deity_keys']!=db['deity_keys']:return False
    for slot,metadata,stats,_ in db['pets']:
        actual_slot=bytes.fromhex(native_value['pet_slots'][str(slot)])
        if metadata:
            if actual_slot!=bytes([1,0,0,0])+bytes.fromhex(metadata):return False
        else:
            # Native 4991E0 clears quantity and key but deliberately retains
            # other metadata, including type34 required by A2C90 cache clear.
            # Empty is quantity0/key0, not a memset of all24 inventory bytes.
            if actual_slot[:6]!=bytes(6):return False
        pet1=bool(stats and stats[:2]=='e3')
        if stats:
            cache=native_value['pet1_cache' if pet1 else 'pet_cache'][str(slot)]
            if cache!=stats[2:]:return False
        else:
            retained_type=actual_slot[6]&63
            if retained_type==34 and native_value['pet_cache'][str(slot)]!=bytes(72).hex():return False
            if retained_type in (13,32) and native_value['pet1_cache'][str(slot)]!=bytes(52).hex():return False
    return True

def pet_icon_state(handle,ui,widget,slot,metadata):
    """Read the native live binder/action and actual inventory sprite, no writes."""
    key=int.from_bytes(bytes.fromhex(metadata)[:2],'little')
    table=int.from_bytes(read(handle,ui+0xcff70,4),'little')
    definition=int.from_bytes(read(handle,table+0xb2d40+key*4,4),'little')
    require(definition>0x10000,'PET_ICON_NATIVE_METADATA_MISSING')
    icon_id,bank,action=struct.unpack('<HHh',read(handle,definition+0x114,6))
    require(0<=bank<512 and action>=0,'PET_ICON_NATIVE_ACTION_UNBOUND')
    manager=ui+0xe2170;graphics=int.from_bytes(read(handle,manager+8,4),'little')
    renderer=int.from_bytes(read(handle,manager+widget*0x2a08+0x81c,2),'little')
    require(graphics>0x10000 and renderer<4096,'PET_ICON_NATIVE_RENDERER_MISSING')
    node=graphics+0x10+renderer*0x290
    actual_action=int.from_bytes(read(handle,node+0x180+slot*2,2),'little',signed=True)
    image_handle=int.from_bytes(read(handle,node+0xac+slot*2,2),'little')
    require(actual_action==action and image_handle<5000,'PET_ICON_CONTROL_ACTION_MISMATCH')
    banks=int.from_bytes(read(handle,graphics+0xc,4),'little');bank_pointer=banks+bank*0x1514
    count=int.from_bytes(read(handle,bank_pointer+0x108c,4),'little')
    require(action<count,'PET_ICON_ACTION_OUTSIDE_ORIGINAL_BANK')
    header=int.from_bytes(read(handle,bank_pointer+0x1090+action*4,4),'little')
    require(header>0x10000,'PET_ICON_ACTION_HEADER_MISSING')
    original_id=int.from_bytes(read(handle,header,4),'little')
    require(original_id==icon_id,'PET_ICON_NATIVE_BINDER_SELECTED_DIFFERENT_ID')
    pool=int.from_bytes(read(handle,graphics+4,4),'little');sprite=pool+image_handle*200
    image_pointer=int.from_bytes(read(handle,sprite+0x12e4,4),'little')
    image_resource=int.from_bytes(read(handle,sprite+0x12ec,4),'little')
    require(image_pointer>0x10000 and image_resource not in (0,0xcdcdcdcd),'PET_ICON_IMAGE_RESOURCE_MISSING')
    return dict(slot=slot,key=key,icon_id=icon_id,bank=bank,action=action,original_action_id=original_id,
        renderer=renderer,image_handle=image_handle,image_pointer=hex(image_pointer),image_resource=hex(image_resource))

def native_deity_metadata(handle,ui,database,expected_count=2):
    table=int.from_bytes(read(handle,ui+0xcff70,4),'little')
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
        rows=db.execute("select metadata_key,parsed_record from native_companion_metadata where family='GOD' order by metadata_key").fetchall()
    require([r[0] for r in rows]==list(range(2801,2835)),'GOD_NATIVE_CATALOG_INCOMPLETE')
    definitions=[]
    for key,expected in rows:
        pointer=int.from_bytes(read(handle,table+0xb2d40+key*4,4),'little')
        require(pointer>0x10000,'GOD_NATIVE_METADATA_MISSING')
        actual=read(handle,pointer,396);normalized=bytearray(actual)
        normalized[0x116:0x11a]=expected[0x116:0x11a]
        require(bytes(normalized)==expected,'GOD_NATIVE_PARSED_METADATA_MISMATCH')
        icon,bank,action=struct.unpack_from('<HHh',actual,0x114)
        require((icon,bank,action)==(1,65,0),'GOD_NATIVE_PRELOAD_BINDING_MISMATCH')
        name=actual[8:46].split(b'\0',1)[0].decode('cp950')
        definitions.append(dict(key=key,name=name,live_record_hex=actual.hex(),bank=bank,action=action))
    actor=int.from_bytes(read(handle,ui+0x86888,4),'little')
    owned=[]
    for ordinal in range(read(handle,actor+0xd4,1)[0]):
        row=actor+0xd8+ordinal*0x3ec;key=int.from_bytes(read(handle,row,2),'little')
        name=read(handle,row+3,16).split(b'\0',1)[0].decode('cp950')
        require(name==definitions[key-1]['name'],'GOD_NATIVE_DECLARATION_NAME_NOT_FROM_METADATA')
        owned.append(dict(key=key,name=name))
    require([r['key'] for r in owned]==list(range(1,expected_count+1)),'GOD_NATIVE_OWNED_KEYS_MISMATCH')
    return dict(definitions=definitions,owned=owned,definition_count=34,
                ignored_packet_names=True,instance_stats_authority='CUSTOM_TEST_NOT_NATIVE')

def native_skill_icon_audit(handle,ui,client_root):
    from owned_deity_skill_fixture import catalog
    definitions=catalog.pinned_records(client_root)
    manager=ui+0xe2170;graphics=int.from_bytes(read(handle,manager+8,4),'little')
    banks=int.from_bytes(read(handle,graphics+0xc,4),'little')
    offsets=struct.unpack('<4I',read(handle,0x5b6f70,16))
    mappings=struct.unpack('<4I',read(handle,0x5b6f80,16))
    rows=[]
    for definition in definitions:
        kind,identity=definition[5:7];bank=mappings[kind];action=offsets[kind]+identity-1
        require(bank<512,'SKILL_ICON_BANK_OUTSIDE_BOUND')
        owner=banks+bank*0x1514;count=int.from_bytes(read(handle,owner+0x108c,4),'little')
        header=int.from_bytes(read(handle,owner+0x1090+action*4,4),'little') if action<count else 0
        animation=int.from_bytes(read(handle,header+0x30,4),'little') if header else 0
        terminal=None
        if animation:
            for ordinal in range(512):
                frame=read(handle,animation+ordinal*10,10)
                if frame[0]==0:
                    terminal=frame[3];break
            require(terminal is not None,'SKILL_ICON_ANIMATION_UNTERMINATED')
        rows.append(dict(kind=kind,id=identity,bank=bank,action=action,bank_count=count,
            header_present=bool(header),animation_present=bool(animation),terminal_sprite=terminal,
            display_eligible=bool(animation and terminal is not None)))
    return dict(rows=rows,total=448,display_eligible=sum(r['display_eligible'] for r in rows),
        authority='CURRENT_CLIENT_READONLY_RESOURCE_OBSERVATION',casting_verified=False)


def native_deity_skills(handle,ui,database,client_root):
    from owned_deity_skill_fixture import verified_catalog,assignments
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
        definitions=verified_catalog(db,client_root)
        owned=db.execute('select row_key,skills from character_deities where character_id=4 order by row_key').fetchall()
    require(dict(owned)==assignments(definitions),'GOD_SKILL_FIXTURE_OWNERSHIP_MISMATCH')
    records={(row[5],row[6]):row[4] for row in definitions}
    actor=int.from_bytes(read(handle,ui+0x86888,4),'little')
    require(read(handle,actor+0xd4,1)[0]==16,'GOD_SKILL_NATIVE_ROW_CAPACITY_MISMATCH')
    observed=set();rows=[]
    for ordinal,(key,skills) in enumerate(owned):
        row=actor+0xd8+ordinal*0x3ec
        require(int.from_bytes(read(handle,row,2),'little')==key,'GOD_SKILL_NATIVE_OWNER_MISMATCH')
        require(read(handle,row+0x1f0,1)[0]==100,'GOD_SKILL_NATIVE_LEARNED_COUNT_MISMATCH')
        pointers=struct.unpack('<100I',read(handle,row+0x258,400));identities=[]
        for index,pointer in enumerate(pointers):
            require(pointer>0x10000,'GOD_SKILL_NATIVE_POINTER_MISSING')
            identity=tuple(skills[index*4+2:index*4+4]);actual=read(handle,pointer,110)
            require(actual==records[identity],'GOD_SKILL_NATIVE_DEFINITION_MISMATCH')
            identities.append(list(identity));observed.add(identity)
        rows.append(dict(key=key,count=100,identities=identities,
            page=read(handle,row+0x3e8,1)[0],page_count=read(handle,row+0x3e9,1)[0]))
    expected={tuple(blob[i+2:i+4]) for blob in assignments(definitions).values() for i in range(0,len(blob),4)}
    require(observed==expected,'GOD_SKILL_NATIVE_CATALOG_COVERAGE_MISMATCH')
    return dict(rows=rows,owned_rows=16,learned_instances=1600,distinct_definitions=len(observed),
                bank_counts=[sum(kind==i for kind,_ in observed) for i in range(4)],
                full_records_match_source=True,ownership_authority='CUSTOM_TEST_NOT_NATIVE',casting_verified=False)

def deity_portrait_state(handle,ui,key):
    require(1<=key<=34 or 101<=key<=108,'UNQUALIFIED_DEITY_PORTRAIT')
    widget=int.from_bytes(read(handle,ui+0x232e52,2),'little',signed=True)
    require(0<widget<128,'DEITY_HUD_WIDGET_MISSING')
    manager=ui+0xe2170;graphics=int.from_bytes(read(handle,manager+8,4),'little')
    renderer=int.from_bytes(read(handle,manager+widget*0x2a08+0x81c,2),'little')
    require(graphics>0x10000 and renderer<4096,'DEITY_HUD_RENDERER_MISSING')
    node=graphics+0x10+renderer*0x290
    action=int.from_bytes(read(handle,node+0x180,2),'little',signed=True)
    image_handle=int.from_bytes(read(handle,node+0xac,2),'little')
    require(action==(key-1 if key<=100 else key-67) and image_handle<5000,
            f'DEITY_HUD_ACTION_MISMATCH key={key} action={action} image={image_handle} widget={widget} renderer={renderer}')
    banks=int.from_bytes(read(handle,graphics+0xc,4),'little');bank=banks+5*0x1514
    count=int.from_bytes(read(handle,bank+0x108c,4),'little')
    require(count==42 and action<count,'DEITY_HUD_ORIGINAL_BANK_BOUND')
    header=int.from_bytes(read(handle,bank+0x1090+action*4,4),'little')
    require(header>0x10000,'DEITY_HUD_ACTION_HEADER_MISSING')
    original_id=int.from_bytes(read(handle,header,4),'little')
    require(original_id==1000+key,'DEITY_HUD_ACT_ID_MISMATCH')
    pool=int.from_bytes(read(handle,graphics+4,4),'little');sprite=pool+image_handle*200
    image_pointer=int.from_bytes(read(handle,sprite+0x12e4,4),'little')
    image_resource=int.from_bytes(read(handle,sprite+0x12ec,4),'little')
    require(image_pointer>0x10000 and image_resource not in (0,0xcdcdcdcd),'DEITY_HUD_IMAGE_RESOURCE_MISSING')
    return dict(key=key,bank=5,action=action,bank_action_count=count,original_action_id=original_id,
        widget=widget,renderer=renderer,image_handle=image_handle,image_pointer=hex(image_pointer),image_resource=hex(image_resource))

def toggle_deity_mode(hwnd,handle,ui,expected):
    require(user.PostMessageW(hwnd,0x100,0x7a,0x00570001),'DEITY_F11_DOWN_FAILED')
    time.sleep(.2)
    require(user.PostMessageW(hwnd,0x101,0x7a,0xc0570001),'DEITY_F11_UP_FAILED')
    wait_until(lambda:int.from_bytes(read(handle,ui+0xa3d08,4),'little')==expected,5,'DEITY_NATIVE_F11_MODE_SWITCH_FAILED')
    time.sleep(.2)
    require(int.from_bytes(read(handle,ui+0xa3d08,4),'little')==expected,'DEITY_NATIVE_F11_MODE_NOT_STABLE')

def select_native_deities(hwnd,handle,ui,database,server_log,receipt,steps=((41,2),(40,1))):
    """Original004A8AA0 controls41/40 ->004962E0 C2S67, no injection."""
    widget=int.from_bytes(read(handle,ui+0x232ddc,2),'little',signed=True)
    require(0<widget<128,'DEITY_PANEL_WIDGET_MISSING')
    base=ui+0xe2170+widget*0x2a08
    # Original005048BC..00504934 accepts input only for widget flag20h.
    # Flag10h is not an input-enabled panel. F11 mode1 invokes004A87C0
    # ->00507B20 and opens the panel; mode0 invokes004A8990 and closes it.
    visible=lambda:bool(read(handle,base+0x818,1)[0]&0x20)
    require(int.from_bytes(read(handle,ui+0xa3d08,4),'little')==1,'DEITY_NATIVE_PANEL_EXPECTED_DEITY_MODE')
    wait_until(visible,5,'DEITY_NATIVE_PANEL_NOT_OPENED')
    baseline=saved(database);stages=[]
    require(1<=baseline['selection'][0]<=34,'DEITY_NATIVE_INITIAL_SELECTION_MISMATCH')
    for control,key in steps:
        require(visible(),'DEITY_NATIVE_PANEL_CLOSED')
        entry=base+0x8b8+control*100
        hit=int.from_bytes(read(handle,entry+8,2),'little',signed=True)
        manager=int.from_bytes(read(handle,ui+0xe2174,4),'little')
        require(manager>0x10000 and 0<=hit<0xc00,'DEITY_NATIVE_BUTTON_HIT_MISSING')
        active,left,top,right,bottom=struct.unpack('<5i',read(handle,manager+hit*24,20))
        require(active!=0 and 0<=left<right<=800 and 0<=top<bottom<=600,'DEITY_NATIVE_BUTTON_RECT_INVALID')
        point=((left+right)//2,(top+bottom)//2)
        order=[];visited=set()
        node=int.from_bytes(read(handle,ui+0xe2170+0x14,4),'little')
        while node:
            require(node>0x10000 and node not in visited and len(order)<128,'DEITY_NATIVE_WIDGET_ORDER_INVALID')
            visited.add(node);row=read(handle,node,16)
            other=int.from_bytes(row[:2],'little',signed=True)
            require(0<=other<128,'DEITY_NATIVE_WIDGET_ORDER_ID_INVALID')
            order.append(other);node=int.from_bytes(row[12:16],'little')
        require(widget in order,'DEITY_NATIVE_PANEL_NOT_IN_INPUT_ORDER')
        receipt['input_order']=order
        overlaps=[]
        # 005048BC visits this list in order. Only preceding widgets can
        # consume a click before the deity panel; panels behind cannot mask it.
        for other in order[:order.index(widget)]:
            block=read(handle,ui+0xe2170+other*0x2a08+0x818,0x21f0)
            if not (block[0]&0x20):continue
            for index in range(84):
                cell=block[0xa0+index*100:0xa0+(index+1)*100]
                if cell[0]==0:continue
                other_hit=int.from_bytes(cell[8:10],'little',signed=True)
                if not 0<=other_hit<4096:continue
                enabled,x1,y1,x2,y2=struct.unpack('<5i',read(handle,manager+other_hit*24,20))
                if enabled and x1<right and x2>left and y1<bottom and y2>top:
                    overlaps.append(dict(widget=other,control=index,kind=cell[0],hit=other_hit,rect=[x1,y1,x2,y2],header=block[:16].hex()))
        receipt['occlusion']=dict(control=control,rect=[left,top,right,bottom],overlaps=overlaps)
        # Only input-enabled widgets qualify as blockers. Bit80h on a control
        # affects native drawing and must not be treated as visibility.
        blockers=[x['rect'] for x in overlaps if x['widget']!=widget]
        candidates=[(x,y) for y in range(top+1,bottom-1) for x in range(left+1,right-1)
            if not any(a<=x<b and c<=y<d for a,c,b,d in blockers)]
        require(candidates,'DEITY_NATIVE_BUTTON_FULLY_OCCLUDED')
        point=min(candidates,key=lambda p:(p[0]-(left+right)//2)**2+(p[1]-(top+bottom)//2)**2)
        receipt.setdefault('attempts',[]).append(dict(control=control,hit=hit,active=active,point=point,
            overlaps=overlaps,
            local_point=control_point(handle,ui,widget,control),widget=widget,
            widget_header=read(handle,base+0x818,16).hex(),control_record=read(handle,entry,100).hex(),
            native_before=native(handle,ui),db_before=saved(database)))
        click(hwnd,*point)
        revision=baseline['selection'][1]+len(stages)+1
        def applied():
            state=saved(database)
            return state['selection']==(key,revision) and native(handle,ui)['deity_selected_key']==key
        wait_until(applied,5,'DEITY_NATIVE_BUTTON_SELECTION_NOT_COMMITTED')
        state=saved(database);actual=native(handle,ui)
        require(agrees(actual,state),'DEITY_NATIVE_SELECTION_CACHE_MISMATCH')
        require(all(state[k]==baseline[k] for k in ('resources','deity_keys','pets')),'DEITY_SELECTION_CHANGED_UNRELATED_STATE')
        portrait=deity_portrait_state(handle,ui,key)
        require(f'key={key} CUSTOM-0039' in server_log.read_text('utf-8',errors='replace'),'DEITY_NATIVE_SELECTION_LOG_MISSING')
        stages.append(dict(control=control,hit=hit,point=point,selection=state['selection'],portrait=portrait))
    return dict(stages=stages,opcode='0x67',producer='004962E0',unrelated_state_unchanged=True)


def native_skill_pages(hwnd,handle,ui,database,server_log):
    """Actual controls43/42 paginate25 icons; no gameplay choice is sent."""
    widget=int.from_bytes(read(handle,ui+0x232ddc,2),'little',signed=True)
    manager=ui+0xe2170;base=manager+widget*0x2a08
    graphics=int.from_bytes(read(handle,manager+8,4),'little')
    renderer=int.from_bytes(read(handle,base+0x81c,2),'little')
    node=graphics+0x10+renderer*0x290;pool=int.from_bytes(read(handle,graphics+4,4),'little')
    hit_manager=int.from_bytes(read(handle,manager+4,4),'little')
    pages=[];transitions=[];reverse_pages=[];observed=set()
    for key in range(1,6):
        if key>1:
            receipt={};receipt.update(select_native_deities(hwnd,handle,ui,database,server_log,receipt,((41,key),)))
            transitions.append(receipt)
        actor=int.from_bytes(read(handle,ui+0x86888,4),'little')
        row=int.from_bytes(read(handle,actor+0xd0,4),'little')
        require(int.from_bytes(read(handle,row,2),'little')==key,'SKILL_PAGE_WRONG_OWNER')
        require(read(handle,row+0x3e9,1)==b'\x04','SKILL_PAGE_COUNT_NOT_FOUR')
        for page in (0,1,2,3):
            require(read(handle,row+0x3e8,1)==bytes((page,)),'SKILL_PAGE_INDEX_MISMATCH')
            identities=[]
            for control in range(25):
                pointer=int.from_bytes(read(handle,row+0x258+(page*25+control)*4,4),'little')
                identity,kind=read(handle,pointer,2)
                action=int.from_bytes(read(handle,node+0x180+control*2,2),'little',signed=True)
                image=int.from_bytes(read(handle,node+0xac+control*2,2),'little')
                require(action==identity-1 and image<5000,'SKILL_PAGE_NATIVE_ICON_ACTION_MISMATCH')
                sprite=pool+image*200
                require(int.from_bytes(read(handle,sprite+0x12e4,4),'little')>0x10000 and
                    int.from_bytes(read(handle,sprite+0x12ec,4),'little') not in (0,0xcdcdcdcd),
                    'SKILL_PAGE_NATIVE_IMAGE_UNAVAILABLE')
                identities.append([kind,identity]);observed.add((kind,identity))
            pages.append(dict(key=key,page=page,identities=identities))
            baseline=saved(database);hit=int.from_bytes(read(handle,base+0x8b8+43*100+8,2),'little',signed=True)
            require(0<=hit<0xc00,'SKILL_PAGE_BUTTON_HIT_INVALID')
            active,left,top,right,bottom=struct.unpack('<5i',read(handle,hit_manager+hit*24,20))
            require(active==1 and 0<=left<right<=800 and 0<=top<bottom<=600,'SKILL_PAGE_BUTTON_RECT_INVALID')
            click(hwnd,(left+right)//2,(top+bottom)//2)
            wait_until(lambda:read(handle,row+0x3e8,1)==bytes(((page+1)%4,)),5,'SKILL_PAGE_NEXT_FAILED')
            require(saved(database)==baseline,'SKILL_PAGE_CHANGED_SAVED_STATE')
        for control,expected in ((42,3),(43,0)):
            baseline=saved(database);hit=int.from_bytes(read(handle,base+0x8b8+control*100+8,2),'little',signed=True)
            require(0<=hit<0xc00,'SKILL_PAGE_REVERSE_HIT_INVALID')
            active,left,top,right,bottom=struct.unpack('<5i',read(handle,hit_manager+hit*24,20))
            require(active==1 and 0<=left<right<=800 and 0<=top<bottom<=600,'SKILL_PAGE_REVERSE_RECT_INVALID')
            click(hwnd,(left+right)//2,(top+bottom)//2)
            wait_until(lambda:read(handle,row+0x3e8,1)==bytes((expected,)),5,'SKILL_PAGE_REVERSE_FAILED')
            require(saved(database)==baseline,'SKILL_PAGE_REVERSE_CHANGED_SAVED_STATE')
            reverse_pages.append(dict(key=key,control=control,page=expected))
    receipt={};receipt.update(select_native_deities(hwnd,handle,ui,database,server_log,receipt,tuple((40,key) for key in (4,3,2,1))))
    transitions.append(receipt)
    require(len(observed)==409,'SKILL_PAGE_FULL_DISPLAY_COVERAGE_MISSING')
    return dict(pages=pages,transitions=transitions,reverse_pages=reverse_pages,distinct_definitions=409,icons_checked=500,
        page_controls=[42,43],casting_verified=False,ownership_authority='CUSTOM_TEST_NOT_NATIVE')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('db',type=Path);ap.add_argument('server_log',type=Path)
    ap.add_argument('--client-exe',type=Path,required=True);ap.add_argument('--expect-kunlun',action='store_true')
    ap.add_argument('--expect-quest-journal',action='store_true')
    ap.add_argument('--expect-world-clock',action='store_true')
    ap.add_argument('--expect-native-world-records',action='store_true')
    ap.add_argument('--expect-map-view',action='store_true')
    ap.add_argument('--expect-role-auxiliary',action='store_true')
    ap.add_argument('--expect-weapon-transfers',action='store_true')
    ap.add_argument('--expect-weapon-appearance',action='store_true')
    ap.add_argument('--expect-pet1-mixed',action='store_true')
    ap.add_argument('--expect-pet-native-icons',action='store_true')
    ap.add_argument('--expect-deity-native-icons',action='store_true')
    ap.add_argument('--expect-deity-templates',action='store_true')
    ap.add_argument('--expect-deity-skill-catalog',action='store_true')
    ap.add_argument('--expect-knowledge-menu',action='store_true')
    ap.add_argument('--knowledge-choice',type=int,choices=range(7),default=0);args=ap.parse_args()
    if args.expect_role_auxiliary and not args.expect_kunlun:ap.error('--expect-role-auxiliary requires --expect-kunlun')
    if args.expect_weapon_transfers and (args.expect_map_view or args.expect_knowledge_menu):ap.error('Weapon acceptance excludes map/menu fixture conflicts')
    if args.expect_weapon_appearance and (not args.expect_weapon_transfers or not args.expect_kunlun or args.expect_role_auxiliary or args.expect_map_view or args.expect_knowledge_menu):
        ap.error('Weapon appearance requires transfers/Kunlun and excludes role auxiliary/map/menu')
    result={'accepted':False,'stages':[]};hwnd=process=handle=None
    try:
        desktop=desktop_names();result['desktop_before']=desktop
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'PRIVATE_DESKTOP_REQUIRED')
        require(args.client_exe.name.lower()!='god2.exe','DISPOSABLE_CLIENT_REQUIRED')
        def find():
            window,pid=game_window()
            if not window:return None
            target=psutil.Process(pid);require(Path(target.exe()).resolve()==args.client_exe.resolve(),'WRONG_CLIENT')
            return window,target
        hwnd,process=wait_until(find,35,'GAME_WINDOW_UNAVAILABLE');result['pid']=process.pid
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow');click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370)
        wait_until(lambda:'OWNED_WORLD_SNAPSHOT_RESTORED' in args.server_log.read_text('utf-8',errors='replace'),20,'OWNED_RESTORE_NOT_SENT')
        time.sleep(3)
        if not args.expect_knowledge_menu:click(hwnd,708,584);time.sleep(2)
        handle=kernel.OpenProcess(0x1010,False,process.pid);require(handle,'READONLY_OPEN_FAILED')
        if args.expect_weapon_transfers:
            weapon_initial=saved_weapons(args.db)
            scan={'matches':find_weapon_owner(handle,weapon_initial)}
        else:
            scanner=Path(__file__).with_name('private_inventory_memory.py')
            scan=json.loads(subprocess.check_output([sys.executable,'-B',str(scanner),str(process.pid),'5576' if args.expect_map_view else '5569'],timeout=20))
        if args.expect_knowledge_menu:
            matches=[row for row in scan['matches'] if read(handle,int(row['ui'],16)+0xccc1c,4)==struct.pack('<HH',4,1434)]
        else:
            matches=[row for row in scan['matches'] if row.get('inventory_source_mode')=='23' and row.get('selected_inventory_slot')=='ffff']
        require(len(matches)==1,'EXPECTED_ONE_INVENTORY_OWNER');ui=int(matches[0]['ui'],16)
        result['ui']=hex(ui)
        if args.expect_native_world_records:
            result['world_records']=native_world_records(handle,ui)
            check_native_world_records(result['world_records'])
        if args.expect_knowledge_menu:
            flags=struct.unpack('<II',read(handle,ui+0xaff00,8))
            pages=struct.unpack('<II',read(handle,0x5b7bf0,8))
            require(flags[0]!=0 and pages==(0,2),'NATIVE_KNOWLEDGE_MENU_NOT_OPEN')
            manager=int.from_bytes(read(handle,ui+0xcc9d4,4),'little')
            require(manager>0x10000,'NATIVE_KNOWLEDGE_INPUT_MANAGER_MISSING')
            def hit_point(hit):
                require(0<=hit<8192,'INVALID_KNOWLEDGE_HIT_ID')
                active,left,top,right,bottom=struct.unpack('<5i',read(handle,manager+hit*0x18,20))
                require(active!=0 and 0<=left<=right<800 and 0<=top<=bottom<600,'KNOWLEDGE_HIT_RECT_OUTSIDE_CLIENT')
                return ((left+right)//2,(top+bottom)//2)
            if args.knowledge_choice>=3:
                widget=int.from_bytes(read(handle,ui+0x232dee,2),'little',signed=True)
                require(0<=widget<128,'INVALID_KNOWLEDGE_WIDGET_ID')
                def button(control):
                    address=ui+0xe2170+widget*0x2a08+0x8b8+control*100+8
                    return hit_point(int.from_bytes(read(handle,address,2),'little',signed=True))
                for control,page in ((3,1),(2,0),(3,1)):
                    click(hwnd,*button(control))
                    wait_until(lambda:int.from_bytes(read(handle,0x5b7bf0,4),'little')==page,5,'KNOWLEDGE_PAGE_BUTTON_FAILED')
                require('KNOWLEDGE_MENU_CHOICE' not in args.server_log.read_text('utf-8',errors='replace'),'KNOWLEDGE_PAGING_SENT_GAMEPLAY_CHOICE')
            row=args.knowledge_choice+2 if args.knowledge_choice<3 else args.knowledge_choice-3
            require(int.from_bytes(read(handle,ui+0xcc9d4+0x148+4*row,4),'little')!=0,'KNOWLEDGE_CHOICE_ROW_DISABLED')
            hit=int.from_bytes(read(handle,ui+0xcc9d4+0x1c+2*row,2),'little',signed=True)
            point=hit_point(hit);result['knowledge_menu']={'flags':list(flags),'pages':list(struct.unpack('<II',read(handle,0x5b7bf0,8))),'row':row,'choice':args.knowledge_choice,'hit':hit,'point':point}
            click(hwnd,*point)
            wait_until(lambda:'KNOWLEDGE_MENU_CHOICE' in args.server_log.read_text('utf-8',errors='replace'),12,'KNOWLEDGE_NATIVE_85_NOT_RECEIVED')
            require(f'choice={args.knowledge_choice} request=0 context=68' in args.server_log.read_text('utf-8',errors='replace'),'KNOWLEDGE_NATIVE_CHOICE_FIELDS_MISMATCH')
            wait_until(lambda:int.from_bytes(read(handle,ui+0xaff00,4),'little')==0,5,'KNOWLEDGE_MENU_DID_NOT_CLOSE')
            result['knowledge_menu']['native_closed']=True
        before=saved(args.db);actual=native(handle,ui);result['before']={'db':before,'native':actual}
        if args.expect_deity_templates:
            result['deity_native_metadata']=native_deity_metadata(handle,ui,args.db,16 if args.expect_deity_skill_catalog else 2)
            result['skill_icon_audit']=native_skill_icon_audit(handle,ui,args.client_exe.parent)
        if args.expect_deity_skill_catalog:
            result['deity_native_skills']=native_deity_skills(handle,ui,args.db,args.client_exe.parent)
        if args.expect_pet1_mixed:
            table=int.from_bytes(read(handle,ui+0xcff70,4),'little');definitions={}
            for _,metadata,_,_ in before['pets']:
                if not metadata:continue
                key=int.from_bytes(bytes.fromhex(metadata)[:2],'little')
                pointer=int.from_bytes(read(handle,table+0xb2d40+key*4,4),'little')
                require(pointer>0x10000,'MIXED_PET_NATIVE_METADATA_MISSING')
                definitions[str(key)]=read(handle,pointer,396).hex()
            result['mixed_pet_native_definitions']=definitions
        if args.expect_role_auxiliary:
            require('OWNED_ROLE_AUXILIARY_RESTORED' in args.server_log.read_text('utf-8',errors='replace'),'OWNED_ROLE_AUXILIARY_RESTORE_NOT_SENT')
            auxiliary_before=saved_role_auxiliary(args.db)
            check_role_auxiliary(actual,auxiliary_before,before['resources'])
            result['role_auxiliary_restore']={'db':auxiliary_before,'native':actual['role_auxiliary'],
                'resources_match_owned_fixture':True,'no_god_fixture':True,
                'actual_god_preservation_tested':False,'authority':'CUSTOM_TEST_NOT_NATIVE'}
        if args.expect_kunlun:require(actual['world_map']=={'kind':0,'scene':3,'area':4},'NATIVE_CLIENT_NOT_IN_KUNLUN')
        if args.expect_quest_journal:
            with sqlite3.connect(args.db) as db:
                blob,revision=db.execute('select values_blob,revision from character_quest_journals where character_id=4').fetchone()
            expected=list(struct.unpack('<15I',blob))
            require(actual['quest_journal']==expected,'NATIVE_QUEST_JOURNAL_RESTORE_MISMATCH')
            result['journal_restore']={'values':expected,'revision':revision,'authority':'CUSTOM_TEST_NOT_NATIVE'}
        if not args.expect_kunlun and not args.expect_weapon_transfers:
            require(agrees(actual,before),'OWNED_WORLD_NATIVE_STATE_MISMATCH')
            widget=matches[0]['inventory_source_index']
            points={slot:control_point(handle,ui,widget,slot) for slot in (42,43,44)};result['control_points']=points
            if args.expect_pet_native_icons or args.expect_deity_native_icons:
                result['pet_native_icons']={'before':[pet_icon_state(handle,ui,widget,slot,metadata)
                    for slot,metadata,_,_ in before['pets'] if metadata],'stages':[],'no_deity_control':args.expect_pet_native_icons}
            moves=((42,44),(43,44),(44,42))
            if args.expect_pet1_mixed:moves+=((43,44),(44,43))
            for index,(source,destination) in enumerate(moves,1):
                prior=saved(args.db);key=int.from_bytes(bytes.fromhex(next(row[1] for row in prior['pets'] if row[0]==source))[:2],'little')
                drag(hwnd,points[source],points[destination])
                def observed():
                    db=saved(args.db);value=native(handle,ui)
                    result['last_observed']={'db':db,'native':value}
                    if db==prior or not agrees(value,db):return None
                    destination_metadata=next(row[1] for row in db['pets'] if row[0]==destination)
                    if not destination_metadata or int.from_bytes(bytes.fromhex(destination_metadata)[:2],'little')!=key:return None
                    return {'move':index,'source':source,'destination':destination,'db':db,'native':value}
                result['stages'].append(wait_until(observed,12,f'PET_MOVE_{index}_NOT_ACCEPTED'))
                if args.expect_pet_native_icons or args.expect_deity_native_icons:
                    result['pet_native_icons']['stages'].append([pet_icon_state(handle,ui,widget,slot,metadata)
                        for slot,metadata,_,_ in saved(args.db)['pets'] if metadata])
            if args.expect_pet1_mixed:
                # Every occupied generation's opposite cache, and both empty
                # caches, must be cleared after transitions, not just hidden.
                final=native(handle,ui);db=saved(args.db)
                for slot,_,stats,_ in db['pets']:
                    if not stats or stats[:2]=='fb':require(final['pet1_cache'][str(slot)]==bytes(52).hex(),'STALE_E3_CACHE_AFTER_MIXED_TRANSFER')
                    if not stats or stats[:2]=='e3':require(final['pet_cache'][str(slot)]==bytes(72).hex(),'STALE_FB_CACHE_AFTER_MIXED_TRANSFER')
                result['mixed_pet_generations']={'accepted':True,'shared_capacity':3,'transfers':len(moves),'opposite_caches_cleared':True}
        if args.expect_weapon_transfers:
            from private_map_item_current_ui import double_click_message
            initial_slots=native_weapon_slots(handle,ui)
            require(weapon_slots_agree(initial_slots,weapon_initial),'INITIAL_WEAPON_NATIVE_SNAPSHOT_MISMATCH')
            require([weapon_initial[str(i)]['item'] for i in (0,1,34)]==[1,2,0],'INITIAL_WEAPON_FIXTURE_KEYS_MISMATCH')
            stable_keys=('role_resources','role_auxiliary','deity_count','deity_selected_key','deity_keys','deity_vitals','pet_slots','pet_cache')
            stable={key:actual[key] for key in stable_keys}
            result['weapon_transfers']={'authority':'CUSTOM_TEST_NOT_NATIVE','before':weapon_initial,'stages':[],
                'actual_god_preservation_tested':bool(actual['deity_count'])}
            widget=matches[0]['inventory_source_index']
            if args.expect_weapon_appearance:
                require(actual['deity_count']==0 and actual['deity_selected_key'] is None,'WEAPON_APPEARANCE_REQUIRES_NO_GOD_FIXTURE')
                appearance_baseline=saved_weapon_appearance(args.db);appearance_initial=native_weapon_appearance(handle,ui)
                check_weapon_appearance(appearance_baseline,appearance_initial,appearance_baseline,appearance_initial,0,1)
                result['weapon_appearance']={'authority':'CUSTOM_TEST_NOT_NATIVE','mapping':'CUSTOM-0047 fixture-only WPN1/2 to category0 ordinal0/1',
                    'baseline_db':appearance_baseline,'baseline_native':appearance_initial,'stages':[],
                    'actual_god_preservation_tested':False,'remote_or_rendered_pixels_tested':False}
            for step,source in enumerate((0,1,34,1) if args.expect_weapon_appearance else (0,1,34,0),1):
                prior=saved_weapons(args.db)
                destination=34 if source!=34 else next((i for i in range(30) if prior[str(i)]['count']==0),None)
                require(destination is not None,'WEAPON_UNEQUIP_EXPECTED_EMPTY_BAG')
                if step==3:require(destination==0,'WEAPON_FIXTURE_LOWEST_EMPTY_CHANGED')
                point=control_point(handle,ui,widget,source)
                double_click_message(hwnd,*point)
                def weapon_observed():
                    after=saved_weapons(args.db);slots=native_weapon_slots(handle,ui)
                    result['weapon_transfers']['last_observed']={'db':after,'slots':slots}
                    if not weapon_after_state(prior,after,source,destination) or not weapon_slots_agree(slots,after):return None
                    state=native(handle,ui)
                    require(all(state[key]==stable[key] for key in stable_keys),'WEAPON_TRANSFER_CHANGED_UNRELATED_NATIVE_STATE')
                    require(saved(args.db)==before,'WEAPON_TRANSFER_CHANGED_UNRELATED_OWNED_STATE')
                    return {'step':step,'source':source,'destination':destination,'point':point,
                        'db':after,'slots':slots,'pending':read(handle,ui+0x85608,4).hex(),
                        'unrelated_native_state_unchanged':True}
                observed=wait_until(weapon_observed,12,f'WEAPON_TRANSFER_{step}_NOT_ACCEPTED')
                if args.expect_weapon_appearance:
                    item=observed['db']['34']['item']
                    def appearance_observed():
                        owned=saved_weapon_appearance(args.db);current=native_weapon_appearance(handle,ui)
                        result['weapon_appearance']['last_observed']={'db':owned,'native':current,'step':step}
                        if owned['revision']!=step+1 or current['logical_hex']!=owned['logical_hex']:return None
                        check_weapon_appearance(owned,current,appearance_baseline,appearance_initial,item,step+1)
                        return {'step':step,'equipped_item':item,'db':owned,'native':current,'other_components_preserved':True}
                    result['weapon_appearance']['stages'].append(wait_until(appearance_observed,8,f'WEAPON_APPEARANCE_{step}_NOT_PROJECTED'))
                observed['fresh_hover']=fresh_weapon_hover(hwnd,handle,ui,widget,observed['db'],destination)
                result['weapon_transfers']['stages'].append(observed)
        if args.expect_map_view:
            from private_map_item_current_ui import double_click_message
            inventory_widget=matches[0]['inventory_source_index']
            item_point=control_point(handle,ui,inventory_widget,0)
            with sqlite3.connect(args.db) as db:
                original_bag=db.execute('select * from diagnostic_inventory_slots where character_id=4 order by slot').fetchall()
            def map_state():
                index=int.from_bytes(read(handle,ui+0x232da8,2),'little',signed=True)
                require(0<=index<128,'MAP_PANEL_INDEX_INVALID')
                node=ui+0xe2988+index*0x2a08
                scene=int.from_bytes(read(handle,ui+0x8aa4c,4),'little')
                require(scene>0x10000,'MAP_SCENE_POINTER_UNAVAILABLE')
                meta=int.from_bytes(read(handle,scene+0x1a0,4),'little')
                require(meta>0x10000,'MAP_METADATA_POINTER_UNAVAILABLE')
                return {'index':index,'flags':int.from_bytes(read(handle,node,2),'little'),'render_handle':int.from_bytes(read(handle,node+4,2),'little'),
                        'resource':list(struct.unpack('<3H',read(handle,meta+0x20,6)))}
            result['map_views']=[]
            for attempt in (1,2):
                double_click_message(hwnd,*item_point)
                opened=wait_until(lambda:map_state() if map_state()['flags']&0x20 else None,10,'MAP_PANEL_DID_NOT_OPEN')
                require(opened['resource']==[47,7,8],'MAP_NOT_KUNLUN_RESOURCE')
                click(hwnd,*control_point(handle,ui,opened['index'],0))
                closed=wait_until(lambda:map_state() if not map_state()['flags']&0x20 else None,5,'MAP_PANEL_DID_NOT_CLOSE')
                result['map_views'].append({'attempt':attempt,'opened':opened,'closed':closed})
            with sqlite3.connect(args.db) as db:
                require(db.execute('select * from diagnostic_inventory_slots where character_id=4 order by slot').fetchall()==original_bag,'MAP_USE_CHANGED_OWNED_INVENTORY')
                require(db.execute('select count(*) from diagnostic_town_guide_progress where character_id=4').fetchone()==(0,),'MAP_USE_GRANTED_QUEST')
            require(args.server_log.read_text('utf-8',errors='replace').count('OWNED_MAP_VIEW_OPEN')>=2,'MAP_NOT_REPEATABLE_SERVER_ROUTE')
        if args.expect_kunlun:
            if not args.expect_knowledge_menu:click(hwnd,708,584);time.sleep(1)
            with sqlite3.connect(args.db) as db:
                movement_before=db.execute('select area,scene,x,y,revision from recovered_positions where character_id=4').fetchone()
            click(hwnd,460,340)
            def moved_in_kunlun():
                with sqlite3.connect(args.db) as db:
                    row=db.execute('select area,scene,x,y,revision from recovered_positions where character_id=4').fetchone()
                if row and movement_before and row[:2]==(4,3) and row[2:4]!=movement_before[2:4] and row[4]>movement_before[4]:return list(row)
                return None
            result['kunlun_movement']=wait_until(moved_in_kunlun,12,'KUNLUN_NATIVE_MOVEMENT_NOT_SAVED')
        if args.expect_world_clock:
            prior=native(handle,ui)['world_clock'];require(prior[0]!=0,'WORLD_CLOCK_UNINITIALIZED')
            def clock_resynchronized():
                value=native(handle,ui)['world_clock'];now=int(time.time())%14400
                if value[0]==prior[0]:return None
                require(value[1]%6==0 and 0<=value[1]<86400,'WORLD_CLOCK_BASE_OUTSIDE_POLICY')
                require((now-value[1]//6)%14400<=7,'WORLD_CLOCK_NOT_SERVER_ALIGNED')
                return value
            result['clock_resynchronization']={'before':prior,'after':wait_until(clock_resynchronized,10,'WORLD_CLOCK_PERIODIC_SYNC_MISSING')}
        result['client_alive']=process.is_running();require(result['client_alive'],'CLIENT_EXITED')
        if args.expect_quest_journal:
            require(native(handle,ui)['quest_journal']==expected,'NATIVE_QUEST_JOURNAL_OVERWRITTEN_AFTER_MOVEMENT')
        if args.expect_role_auxiliary:
            final_auxiliary=saved_role_auxiliary(args.db);final_native=native(handle,ui)
            require(final_auxiliary==auxiliary_before,'OWNED_ROLE_AUXILIARY_SNAPSHOT_MUTATED')
            require(saved(args.db)['resources']==before['resources'],'OWNED_ROLE_AUXILIARY_RESOURCES_MUTATED')
            check_role_auxiliary(final_native,final_auxiliary,before['resources'])
            result['role_auxiliary_restore'].update(after_actions=final_native['role_auxiliary'],
                resources_after_actions=final_native['role_resources'],persisted_snapshot_unchanged=True)
        if args.expect_weapon_transfers:
            final_weapons=saved_weapons(args.db);final_slots=native_weapon_slots(handle,ui);final_state=native(handle,ui)
            require(final_weapons==result['weapon_transfers']['stages'][-1]['db'],'WEAPON_SNAPSHOT_CHANGED_AFTER_ACTIONS')
            require(weapon_slots_agree(final_slots,final_weapons),'WEAPON_NATIVE_SNAPSHOT_CHANGED_AFTER_ACTIONS')
            require(all(final_state[key]==stable[key] for key in stable_keys),'WEAPON_UNRELATED_NATIVE_STATE_CHANGED_AFTER_ACTIONS')
            require(saved(args.db)==before,'WEAPON_UNRELATED_OWNED_STATE_CHANGED_AFTER_ACTIONS')
            result['weapon_transfers'].update(final_db=final_weapons,final_slots=final_slots,
                final_resources=final_state['role_resources'],unrelated_state_unchanged_after_actions=True)
        if args.expect_weapon_appearance:
            appearance_final=saved_weapon_appearance(args.db);native_final=native_weapon_appearance(handle,ui)
            check_weapon_appearance(appearance_final,native_final,appearance_baseline,appearance_initial,1,5)
            require(appearance_final==result['weapon_appearance']['stages'][-1]['db'],'WEAPON_APPEARANCE_CHANGED_AFTER_MOVEMENT_CLOCK')
            result['weapon_appearance'].update(final_db=appearance_final,final_native=native_final,
                unchanged_after_movement_clock=True)
        result['desktop_after']=desktop_names();require(result['desktop_after']==desktop,'DESKTOP_CHANGED')
        if args.expect_deity_native_icons:
            # Complete real bag drags before switching native UI contexts.
            # Original004AB5AD/VK_F11 invokes004AD800; no memory writes.
            require(int.from_bytes(read(handle,ui+0xa3d08,4),'little')==0,'DEITY_ACCEPTANCE_EXPECTED_INITIAL_ROLE_MODE')
            toggle_deity_mode(hwnd,handle,ui,1)
            actor=int.from_bytes(read(handle,ui+0x86888,4),'little')
            widget=int.from_bytes(read(handle,ui+0x232e52,2),'little')
            result['deity_hud_diagnostic']=dict(mode=int.from_bytes(read(handle,ui+0xa3d08,4),'little'),
                selected_pointer=hex(int.from_bytes(read(handle,actor+0xd0,4),'little')),
                widget_header=read(handle,ui+0xe2170+widget*0x2a08+0x818,16).hex(),
                control0=read(handle,ui+0xe2170+widget*0x2a08+0x8b8,100).hex(),
                hud_code=read(handle,0x4ae150,0x62).hex())
            result['deity_native_portrait']=deity_portrait_state(handle,ui,native(handle,ui)['deity_selected_key'])
            toggle_deity_mode(hwnd,handle,ui,0)
            toggle_deity_mode(hwnd,handle,ui,1)
            result['deity_native_portrait_after']=deity_portrait_state(handle,ui,native(handle,ui)['deity_selected_key'])
            require(all(result['deity_native_portrait_after'][k]==result['deity_native_portrait'][k]
                        for k in ('key','bank','action','bank_action_count','original_action_id','image_pointer')),
                    'DEITY_PORTRAIT_CHANGED_BY_PET_TRANSFER')
            if args.expect_deity_templates:
                result['deity_native_selection']={}
                result['deity_native_selection'].update(select_native_deities(hwnd,handle,ui,args.db,args.server_log,result['deity_native_selection']))
            if args.expect_deity_skill_catalog:
                result['deity_native_skill_pages']=native_skill_pages(hwnd,handle,ui,args.db,args.server_log)
                result['deity_native_skills_after']=native_deity_skills(handle,ui,args.db,args.client_exe.parent)
                require(result['deity_native_skills']==result['deity_native_skills_after'],'GOD_SKILLS_CHANGED_AFTER_UI_TRANSFERS')
            require('NATIVE_CLIENT_DIAGNOSTIC' not in args.server_log.read_text('utf-8',errors='replace'),'NATIVE_CLIENT_DIAGNOSTIC_DURING_COMPANION_ACCEPTANCE')
        if args.expect_native_world_records:
            result['world_records_after_movement']=native_world_records(handle,ui)
            check_native_world_records(result['world_records_after_movement'])
        result['accepted']=True
    except Exception as error:result['error']=f'{type(error).__name__}: {error}'
    finally:
        if handle:
            kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle(handle)
        if hwnd and process:
            try:
                if process.is_running() and Path(process.exe()).resolve()==args.client_exe.resolve():
                    user.PostMessageW(hwnd,0x10,0,0)
                    try:process.wait(timeout=4)
                    except psutil.TimeoutExpired:process.terminate()
            except psutil.NoSuchProcess:pass
        result['desktop_final']=desktop_names();args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return 0 if result['accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
