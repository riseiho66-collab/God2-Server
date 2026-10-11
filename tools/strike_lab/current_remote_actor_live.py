"""Bounded read-only remote actor pool observation; no visibility claim."""
import hashlib
import struct
from copy import deepcopy
from pathlib import Path


def configure_probe(settings,run,language):
    """Fresh isolated diagnostic settings; no source database is rewritten."""
    if type(language) is not int or language not in (0,1):
        raise ValueError('Remote probe requires explicit language bit')
    settings=deepcopy(settings)
    dev=settings['development']
    if not all(dev.get(key) is True for key in ('recovered_movement','recovered_world_entry',
            'recovered_account_auth','recovered_dual_connection','recovered_character_creation')):
        raise ValueError('Remote probe requires complete recovered movement configuration')
    if dev.get('mock_login') is not False or settings['server']['host']!='127.0.0.1':
        raise ValueError('Remote probe requires authenticated IPv4 loopback')
    for key,value in list(dev.items()):
        if key.startswith('diagnostic_'):
            if value is True or isinstance(value,(dict,list)):
                raise ValueError('Remote probe cannot replace another enabled diagnostic')
            del dev[key]
    target=Path(run).resolve()/'remote-actor-diagnostic.db'
    if target.exists():
        raise ValueError('Remote probe database must be fresh')
    settings['database']['path']=str(target)
    dev['diagnostic_remote_actor']=True
    dev['diagnostic_remote_actor_language']=language
    return settings


def snapshot(driver,world,include_status=False):
    from pagefile_capacity_compat import memory
    manager=world+0x15383410
    display_pointer=memory(driver,manager+8,4)
    if len(display_pointer)!=4:raise ValueError('Remote display pointer short read')
    display_pool=int.from_bytes(display_pointer,'little')
    # Original64D02 /65408 /FABB0 binds a distinct remote display pool.
    if display_pool!=world+0xaba32e0:raise ValueError('Remote display pool binding differs')
    controls=memory(driver,manager+0x13418,12)
    def components(raw):
        return [dict(handle=struct.unpack_from('<h',raw,4+6*i)[0],variant=raw[8+6*i])
                for i in range(4)]
    local_components=components(memory(driver,world+0xa7e04d0,32))
    records=bytearray()
    entries=[]
    for first in range(0,128,8):
        block=memory(driver,manager+0x18+first*0x268,8*0x268)
        if len(block)!=8*0x268:raise ValueError('Remote pool short read')
        records.extend(block)
        for relative in range(8):
            record=block[relative*0x268:(relative+1)*0x268]
            identity=struct.unpack_from('<I',record)[0]
            if identity==0xffffffff:continue
            render_handle=struct.unpack_from('<h',record,0x48)[0]
            text_fields=[record[offset:offset+16].split(b'\0',1)[0].hex() for offset in (4,20,36)]
            display_texts=[]
            if 0<=render_handle<4096:
                label_block=memory(driver,display_pool+render_handle*0xa7e0+0x70,51)
                if len(label_block)!=51:raise ValueError('Remote display text short read')
                display_texts=[label_block[offset:offset+17].split(b'\0',1)[0].hex() for offset in (0,17,34)]
            entries.append(dict(slot=first+relative,identity=identity,
                x=struct.unpack_from('<i',record,0x64)[0],
                y=struct.unpack_from('<i',record,0x68)[0],
                queue_read=record[0xa9],queue_write=record[0xaa],
                movement_state=struct.unpack_from('<H',record,0x38)[0],
                screen_x=struct.unpack_from('<h',record,0x74)[0],
                screen_y=struct.unpack_from('<h',record,0x76)[0],
                remaining_x=struct.unpack_from('<i',record,0x90)[0],
                remaining_y=struct.unpack_from('<i',record,0x94)[0],
                components=components(record[0x224:0x244]),
                render_handle=render_handle,text_fields=text_fields,display_texts=display_texts,
                record_sha256=hashlib.sha256(record).hexdigest()))
            if include_status and 0<=render_handle<4096:
                address=display_pool+render_handle*0xa7e0+0x1c
                raw=memory(driver,address+0x2a,4)
                icon,flags=struct.unpack('<hH',raw)
                status=dict(value=struct.unpack_from('<H',record,0x60)[0],flags=flags,handle=icon)
                if 0<=icon<4096:
                    bank=int.from_bytes(memory(driver,display_pool+4,4),'little')
                    graphic=memory(driver,bank+0x10+icon*0x290,0x18)
                    status.update(graphic_state=graphic[0],action=graphic[1],resource=struct.unpack_from('<H',graphic,0x16)[0],
                                  expected_resource=int.from_bytes(memory(driver,display_pool+0x18,4),'little'))
                entries[-1]['status']=status
                title_handle=int.from_bytes(memory(driver,address+0x88,4),'little',signed=True)
                title=dict(handle=title_handle)
                if 0<=title_handle<4096:
                    bank=int.from_bytes(memory(driver,display_pool+4,4),'little')
                    graphic=memory(driver,bank+0x10+title_handle*0x290,0x18)
                    title.update(graphic_state=graphic[0],action=graphic[1],
                        resource=struct.unpack_from('<H',graphic,0x16)[0],
                        expected_resource=int.from_bytes(memory(driver,display_pool+0x10,4),'little'))
                entries[-1]['title']=title
    clear_mode,display_mode,extra_mode=struct.unpack('<III',controls)
    return dict(manager=manager,capacity=128,stride=0x268,clear_mode=clear_mode,
        display_pool=display_pool,
        display_mode=display_mode,extra_mode=extra_mode,entries=entries,
        records_sha256=hashlib.sha256(records).hexdigest(),
        local_components=local_components,
        scope='READ_ONLY_POOL_STATE_NOT_MULTIPLAYER_VISIBILITY_ACCEPTANCE')


class RemoteActorStatusLifecycle:
    def __init__(self,targets=(0x200,0)):
        if not targets or any(t not in (0,1,0x100,0x200,0x400,0x800,0x1000) for t in targets) or targets[-1]!=0:
            raise ValueError('Explicit qualified status sequence ending clear required')
        self.targets=tuple(targets);self.cursor=0
        self.base=RemoteActorLifecycle(require_components=True,require_text=True)
        self.stage='spawn';self.evidence=[]

    def observe(self,sample):
        if self.stage=='spawn':
            self.base.observe(sample)
            if self.base.stage=='move':
                self.evidence.append(deepcopy(sample));self.stage='status'
            return False
        if self.stage=='status':
            if len(sample['entries'])!=1 or sample['entries'][0]['identity']!=7:
                raise ValueError('Remote actor disappeared during status qualification')
            actor=sample['entries'][0];status=actor['status']
            if (actor['x'],actor['y'])!=(18,12):raise ValueError('Remote actor moved before status acceptance')
            target=self.targets[self.cursor]
            if status['value']!=target:return False
            if status['flags']!=target>>8 or not 0<=status['handle']<4096:
                raise ValueError('Native status display binding rejected')
            if target>=0x100 and (status['graphic_state']!=2 or status['action']!=target.bit_length()-9 or status['resource']!=status['expected_resource']):
                raise ValueError('Native status graphic resource/action mismatch')
            if target==1 or (self.cursor and self.targets[self.cursor-1]==1):
                title=actor['title']
                if not 0<=title['handle']<4096:raise ValueError('Native title handle invalid')
                if target==1 and (title['graphic_state']!=2 or title['action']!=1 or title['resource']!=title['expected_resource']):
                    raise ValueError('Native Fight title resource/action mismatch')
                if target==0 and title['graphic_state']!=1:
                    raise ValueError('Native Fight title did not clear')
            expected_variants=[7]*4 if target==0x1000 else [c['variant'] for c in sample['local_components']]
            if [c['variant'] for c in actor['components']]!=expected_variants:
                raise ValueError('Native status component actions differ')
            if target<0x100 and status['graphic_state']!=1:raise ValueError('Native status graphic did not clear')
            self.evidence.append(deepcopy(sample))
            self.cursor+=1
            self.stage='move' if self.cursor==len(self.targets) else 'status'
            return False
        done=self.base.observe(sample)
        self.stage=self.base.stage
        if done:self.evidence.extend(self.base.evidence[1:])
        return done


class RemoteActorLifecycle:
    """CUSTOM-0026 observation gate; callers must separately prove socket frames."""
    def __init__(self,require_components=False,require_text=False):
        self.stage='spawn'
        self.require_components=require_components
        self.require_text=require_text
        self.spawn_text=None
        self.spawn_screen=None
        self.evidence=[]

    def observe(self, sample):
        if self.stage=='complete':
            raise ValueError('Remote lifecycle already complete')
        if (sample['capacity'],sample['stride'],sample['clear_mode'],
                sample['display_mode'],sample['extra_mode'])!=(128,0x268,1,1,1):
            raise ValueError('Unexpected remote pool configuration')
        entries=sample['entries']
        if len(entries)>1 or any(entry['identity']!=7 for entry in entries):
            raise ValueError('Unexpected actor in isolated remote probe')
        if not entries:
            if self.stage=='remove':
                self.evidence.append(deepcopy(sample))
                self.stage='complete'
                return True
            if self.stage=='move':
                raise ValueError('Actor disappeared before observed movement completion')
            return False
        actor=entries[0]
        if self.require_text:
            if sample.get('display_pool')!=sample['manager']-0x15383410+0xaba32e0:
                raise ValueError('Remote text evidence lacks the qualified display pool')
            fields=[bytes.fromhex(value) for value in actor['text_fields']]
            if len(fields)!=3 or not fields[0] or any(len(value)>15 or b'\0' in value for value in fields):
                raise ValueError('Remote text fields outside bounded name contract')
            expected=[(b' '*max(0,(14-len(value))//2)+value).hex() for value in fields]
            if actor['display_texts']!=expected:
                raise ValueError('Remote display text differs from native centering contract')
            if self.spawn_text is None:self.spawn_text=list(actor['text_fields'])
            elif actor['text_fields']!=self.spawn_text:
                raise ValueError('Remote text changed during movement')
        if self.require_components:
            local=sample['local_components']
            if len(local)!=4 or any(item['handle']<0 for item in local) or actor['components']!=local:
                raise ValueError('Remote appearance does not match local native components')
        if not 0<=actor['render_handle']<4096:
            raise ValueError('Remote actor has no valid render handle')
        if not (0<=actor['queue_read']<40 and 0<=actor['queue_write']<40):
            raise ValueError('Remote movement queue index outside bounds')
        point=(actor['x'],actor['y'])
        if self.stage=='spawn':
            if point!=(18,12):
                raise ValueError('Missed qualified spawn position')
            self.spawn_screen=(actor['screen_x'],actor['screen_y'])
            self.evidence.append(deepcopy(sample))
            self.stage='move'
        elif self.stage=='move':
            if point not in ((18,12),(19,12)):
                raise ValueError('Unexpected remote destination')
            if (point==(19,12) and actor['queue_read']==actor['queue_write'] and
                    actor['movement_state']==0 and
                    (actor['remaining_x'],actor['remaining_y'])==(0,0) and
                    (actor['screen_x'],actor['screen_y'])!=self.spawn_screen):
                self.evidence.append(deepcopy(sample))
                self.stage='remove'
        elif point!=(19,12):
            raise ValueError('Remote actor changed after qualified movement')
        return False
