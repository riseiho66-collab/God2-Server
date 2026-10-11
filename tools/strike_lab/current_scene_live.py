"""Read-only scene61 runtime evidence, not physical UI or resurrection proof."""
import struct
from pagefile_capacity_compat import memory


def scene_snapshot(driver, world):
    ui = world + 0xa7f2f6c
    return dict(world=world,
                ring_hex=memory(driver,world+0x234,3).hex(),
                x=struct.unpack('<I',memory(driver,world+0x224,4))[0],
                y=struct.unpack('<I',memory(driver,world+0x228,4))[0],
                area=struct.unpack('<H',memory(driver,world+0x15396854,2))[0],
                scene=struct.unpack('<I',memory(driver,world+0x15396850,4))[0],
                kind=memory(driver,world+0x1539684c,1)[0],
                slot0_hex=memory(driver,ui+0x8560c,24).hex())


def outdoor_scene_snapshot(driver, world):
    state=scene_snapshot(driver,world)
    pointer=struct.unpack('<I',memory(driver,world+0xa7f2f6c+0x8aa4c,4))[0]
    if not pointer:raise ValueError('Outdoor scene object is null')
    metadata=struct.unpack('<I',memory(driver,pointer+0x1a0,4))[0]
    if not metadata:raise ValueError('Outdoor metadata is null')
    state.update(scene_object=pointer,metadata_pointer=metadata,
                 loaded_scene_id=struct.unpack('<H',memory(driver,pointer+0xf0,2))[0],
                 metadata_hex=memory(driver,metadata,40).hex())
    return state


def loaded_scene_snapshot(driver, world):
    state=scene_snapshot(driver,world)
    pointer=struct.unpack('<I',memory(driver,world+0xa7f2f6c+0x8aa4c,4))[0]
    if not pointer and (state['area'],state['scene'],state['kind'])!=(2,15,2):
        raise ValueError('Loaded scene pointer is null outside qualified indoor scene')
    state['scene_object']=pointer
    state['loaded_scene_id']=struct.unpack('<H',memory(driver,pointer+0xf0,2))[0] if pointer else None
    metadata=struct.unpack('<I',memory(driver,pointer+0x1a0,4))[0] if pointer else 0
    if pointer and not metadata:raise ValueError('Loaded scene metadata is null')
    state['metadata_pointer']=metadata
    state['metadata_hex']=memory(driver,metadata,40).hex() if metadata else None
    bridge=struct.unpack('<I',memory(driver,world+0xa7e05dc,4))[0]
    if not bridge:raise ValueError('Scene bridge is null')
    manager=struct.unpack('<I',memory(driver,bridge+0xbc,4))[0]
    if not manager:raise ValueError('Map manager is null')
    indoor=struct.unpack('<I',memory(driver,manager+0x1030,4))[0]
    if not indoor:raise ValueError('Indoor object is null')
    grid,width,height=struct.unpack('<III',memory(driver,indoor+0x8c,12))
    if not grid or not (1<=width<=64 and 1<=height<=64):
        raise ValueError('Indoor live grid outside bounded probe')
    state.update(map_manager=manager,indoor=indoor,grid_width=width,grid_height=height,
                 grid_hex=memory(driver,grid,width*height).hex())
    return state
