"""Read-only current NPC resource/pool observation in the guarded child."""
import struct


def snapshot(driver,world):
    from pagefile_capacity_compat import memory,number
    manager=world+0xaa364b8
    bank=number(driver,f'poi({manager+0x16ce18:x})')
    if bank>7:raise ValueError('NPC diagnostic resource bank outside bounded observation')
    table=manager+bank*0xad610+0x3d5d4
    count=number(driver,f'poi({table+0x244e0:x})')
    if not 0<count<=1024:raise ValueError('NPC resource table unavailable or out of observation bounds')
    resources=[]
    catalog=memory(driver,table+0x244e4,count*76)
    for ordinal in range(count):
        record=catalog[ordinal*76:(ordinal+1)*76]
        loaded=struct.unpack_from('<h',record,64)[0]
        if loaded<0 and ordinal not in (19,20,81,87,237,318):continue
        resources.append(dict(ordinal=ordinal,path=record[:64].split(b'\0',1)[0].decode('ascii'),
            loaded_slot=loaded,action_count=record[66],palette=record[67]))
    catalog_owner=number(driver,f'poi({world+0xaa36480:x})')
    if not catalog_owner:raise ValueError('Native NPC appearance catalog owner unavailable')
    maximum=int.from_bytes(memory(driver,catalog_owner+0x121e8,2),'little',signed=True)
    templates=[]
    for selector in (531,3557,1606,1607):
        if not 0<selector<=maximum:raise ValueError('Selected current NPC template outside catalog')
        record=memory(driver,catalog_owner+0x121ea+94*selector,94)
        templates.append(dict(selector=selector,record_hex=record.hex(),
                              flags=struct.unpack_from('<H',record,0x10)[0],
                              appearance_code=struct.unpack_from('<H',record,0x12)[0]))
    pools=[]
    for offset in (0x1539aed8,0x153b8758):
        pool=world+offset
        # Fixed native capacity and stride; no pointers from untrusted records followed.
        entries=[]
        for first in range(0,256,16):
            block=memory(driver,pool+0x70+first*0x1d8,16*0x1d8)
            for i in range(16):
                identity=struct.unpack_from('<I',block,i*0x1d8)[0]
                if identity!=0xffffffff:
                    x,y=struct.unpack_from('<ii',block,i*0x1d8+0x10)
                    entries.append(dict(slot=first+i,identity=identity,x=x,y=y))
        pools.append(dict(offset=offset,address=pool,capacity=256,entries=entries))
    return dict(manager=manager,bank=bank,table=table,count=count,resources=resources,pools=pools,
                appearance_catalog_owner=catalog_owner,appearance_maximum=maximum,templates=templates,
                scope='READ_ONLY_RESOURCE_AND_POOL_STATE_NOT_VISIBLE_NPC_ACCEPTANCE')


def render_slots(driver, observed):
    """Read bounded native actor, renderer and command slots without driving input."""
    from pagefile_capacity_compat import memory
    result=[]
    for pool in observed['pools']:
        renderer=struct.unpack('<I',memory(driver,pool['address']+4,4))[0]
        if not renderer:raise ValueError('NPC renderer pointer unavailable')
        surface=struct.unpack('<I',memory(driver,renderer+4,4))[0]
        if not surface:raise ValueError('NPC surface pointer unavailable')
        for entry in pool['entries']:
            actor=pool['address']+0x70+entry['slot']*0x1d8
            raw=memory(driver,actor,0x40)
            identity=struct.unpack_from('<I',raw,0)[0]
            if identity!=entry['identity']:
                raise ValueError('NPC actor changed during render-slot observation')
            sprite_handle,hit_handle=struct.unpack_from('<hh',raw,0xa)
            coordinates=struct.unpack_from('<ii',raw,0x10)
            if coordinates!=(entry['x'],entry['y']):
                raise ValueError('NPC coordinates changed during render-slot observation')
            if not 0<=sprite_handle<4096:raise ValueError('NPC sprite handle outside native pool')
            node=memory(driver,renderer+0x10+0x290*sprite_handle,0x48)
            command_slot=struct.unpack_from('<h',node,0xe)[0]
            if not 0<=command_slot<4096:raise ValueError('NPC surface command slot outside native pool')
            command_type=memory(driver,surface+0x1258+200*command_slot,1)[0]
            primary=dict(handle=sprite_handle,node_type=node[0],command_slot=command_slot,
                         command_type=command_type,resource_slot=struct.unpack_from('<h',node,0x16)[0])
            if primary['node_type']!=2 or primary['command_type']!=2:
                raise ValueError('NPC primary render object or command is inactive')
            if primary['resource_slot']!=struct.unpack_from('<h',raw,4)[0]:
                raise ValueError('NPC primary render object resource differs from actor')
            result.append(dict(identity=identity,pool_offset=pool['offset'],slot=entry['slot'],
                               sprite_handle=sprite_handle,hit_handle=hit_handle,
                               projected_float_hex=raw[0x18:0x20].hex(),
                               primary_renderer_node=primary,actor_header_hex=raw.hex()))
    return dict(entries=result,scope='READ_ONLY_NATIVE_SPRITE_AND_HIT_HANDLES_NOT_DEVICE_PIXELS_OR_CLICK_ACCEPTANCE')
