"""Two live observers rendezvous on native remote-role records, not pixels."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def observe(server,peer,run_id,client_pid,sample):
    document=server.document
    peers=document['peers']
    if peers[str(peer)]!=run_id:raise ValueError('Shared observer run identity mismatch')
    from current_login_command import lab_identity
    with closing(sqlite3.connect(server.database.as_uri()+'?mode=ro',uri=True)) as db:
        rows=db.execute('select id,name_bytes from recovered_characters').fetchall()
    identities={bytes(name):identity for identity,name in rows}
    own_name=lab_identity(peer)[1]
    other_name=lab_identity(1-peer)[1]
    if own_name not in identities or other_name not in identities:return False,None
    if (sample['capacity'],sample['stride'],sample['clear_mode'],sample['display_mode'],sample['extra_mode'])!=(128,0x268,1,1,1):
        raise ValueError('Shared native role pool configuration differs')
    if sample.get('display_pool')!=sample['manager']-0x15383410+0xaba32e0:
        raise ValueError('Shared observer requires the native remote display pool')
    entries=sample['entries']
    if not entries:
        folder=server.manifest.parent
        visible=folder/f'peer-{peer}-visible.json'
        release=folder/'release-visible.json'
        if document.get('observe_departure') and peer==0 and visible.exists() and release.exists():
            if json.loads(release.read_text())!={'peers':peers}:
                raise ValueError('Shared visibility release mismatch')
            prior=json.loads(visible.read_text())
            if prior['run_id']!=run_id or prior['client_pid']!=client_pid:
                raise ValueError('Departure observer generation mismatch')
            evidence=dict(prior,departure_sample=sample,phase='REMOTE_DEPARTURE_OBSERVED')
            target=folder/'peer-0-departed.json'
            if not target.exists():
                temporary=target.with_suffix('.tmp')
                temporary.write_text(json.dumps(evidence),encoding='utf-8');temporary.replace(target)
            return not document.get('held_reconnect',False),evidence
        return False,None
    if len(entries)!=1:raise ValueError('Shared probe requires exactly one other player')
    actor=entries[0]
    folder=server.manifest.parent
    released=(folder/'release-visible.json').exists()
    moving=(document.get('observe_movement') and released) or (document.get('post_battle_movement') and peer==1 and (folder/'peer-1-fight-cleared.json').exists())
    restored=document.get('restored_source')
    expected=(18,12) if restored else (17,13)
    if restored and (sample.get('local_position_hex')!='120000000c000000' or sample.get('local_ring_hex')!='010001'):
        raise ValueError('Restored local position or reset movement ring differs')
    if (actor['identity']!=identities[other_name] or actor['text_fields'][0]!=other_name.hex() or
            actor['display_texts'][0]!=(b' '*max(0,(14-len(other_name))//2)+other_name).hex() or
            (actor['x'],actor['y']) not in (((17,13),(18,12)) if moving else (expected,)) or
            not 0<=actor['render_handle']<4096):
        raise ValueError('Shared native peer identity/name/position rejected')
    if len(actor['components'])!=4 or any(item['handle']<0 for item in actor['components']):
        raise ValueError('Shared native peer resources missing')
    evidence=dict(run_id=run_id,peer=peer,client_pid=client_pid,local_identity=identities[own_name],sample=sample,
                  scope='TWO_NATIVE_ROLE_POOLS_NOT_PIXEL_RENDERING_OR_FULL_GAMEPLAY')
    path=server.manifest.parent/f'peer-{peer}-visible.json'
    if not path.exists():
        temporary=path.with_suffix('.tmp')
        temporary.write_text(json.dumps(evidence),encoding='utf-8')
        temporary.replace(path)
    release=server.manifest.parent/'release-visible.json'
    if not release.exists():return False,evidence
    if json.loads(release.read_text())!={'peers':peers}:
        raise ValueError('Shared visibility release mismatch')
    if document.get('observe_battle'):
        if peer==0:return False,evidence
        status=actor['status'];title=actor['title']
        if status['value'] not in (0,1):raise ValueError('Unexpected shared battle status')
        marked=folder/'peer-1-fight.json'
        if status['value']==1:
            if not (0<=title['handle']<4096 and title['graphic_state']==2 and
                    title['action']==1 and title['resource']==title['expected_resource']):
                raise ValueError('Shared Fight graphic mismatch')
            if not marked.exists():
                temporary=marked.with_suffix('.tmp')
                temporary.write_text(json.dumps(evidence),encoding='utf-8');temporary.replace(marked)
        elif marked.exists():
            prior=json.loads(marked.read_text())
            if prior['client_pid']!=client_pid or prior['run_id']!=run_id:
                raise ValueError('Shared battle observer generation changed')
            prior_title=prior['sample']['entries'][0]['title']
            if not (title['handle']==prior_title['handle'] and title['graphic_state']==1 and
                    title['resource']==title['expected_resource']==prior_title['resource']):
                raise ValueError('Shared Fight graphic did not clear')
            evidence['phase']='REMOTE_BATTLE_TITLE_CLEARED'
            target=folder/'peer-1-fight-cleared.json'
            if not target.exists():
                temporary=target.with_suffix('.tmp')
                temporary.write_text(json.dumps(evidence),encoding='utf-8');temporary.replace(target)
            returned=folder/'peer-0-battle-returned.json'
            if not returned.exists():return False,evidence
            completion=json.loads(returned.read_text())
            combatant=json.loads((folder/'peer-0-battle-started.json').read_text())
            if (completion['run_id']!=peers['0'] or completion['client_pid']!=combatant['client_pid'] or
                    completion['client_pid']==client_pid):
                raise ValueError('Shared battle completion generation mismatch')
            if document.get('post_battle_movement'):
                finished=folder/'peer-0-path-completed.json'
                if not finished.exists():return False,evidence
                path=json.loads(finished.read_text())
                if path['run_id']!=peers['0'] or len(path['steps'])!=3:
                    raise ValueError('Post-battle producer path mismatch')
                before=prior['sample']['entries'][0]
                if not ((actor['x'],actor['y'])==(18,12) and actor['movement_state']==0 and
                    actor['remaining_x']==actor['remaining_y']==0 and actor['queue_read']==actor['queue_write'] and
                    (actor['screen_x'],actor['screen_y'])==(before['screen_x'],before['screen_y']-40)):
                    return False,evidence
                evidence['phase']='REMOTE_BATTLE_MOVEMENT_OBSERVED'
                target=folder/'peer-1-moved.json';temporary=target.with_suffix('.tmp')
                temporary.write_text(json.dumps(evidence),encoding='utf-8');temporary.replace(target)
            return True,evidence
        return False,evidence
    if document.get('held_reconnect') and peer==0 and (folder/'peer-0-departed.json').exists():
        evidence['phase']='REMOTE_REJOIN_OBSERVED'
        target=folder/'peer-0-rejoined.json'
        temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(evidence),encoding='utf-8');temporary.replace(target)
        return (folder/'release-rejoined.json').exists(),evidence
    if document.get('observe_movement'):
        simultaneous=document.get('simultaneous_movement',False)
        own_completed=folder/f'peer-{peer}-path-completed.json'
        if (simultaneous and not own_completed.exists()) or (peer==1 and not simultaneous):
            return False,dict(evidence,phase='MOVEMENT_REQUEST')
        before=json.loads(path.read_text())['sample']['entries'][0]
        completed=folder/f'peer-{1-peer}-path-completed.json'
        if not completed.exists():return False,evidence
        completion=json.loads(completed.read_text())
        if completion['run_id']!=peers[str(1-peer)] or len(completion['steps'])!=3:
            raise ValueError('Shared movement producer completion mismatch')
        if ((actor['x'],actor['y'])==(18,12) and actor['movement_state']==0 and
                actor['remaining_x']==actor['remaining_y']==0 and actor['queue_read']==actor['queue_write'] and
                (actor['screen_x'],actor['screen_y'])==(before['screen_x'],before['screen_y']-40)):
            evidence['phase']='REMOTE_MOVEMENT_OBSERVED'
            target=folder/f'peer-{peer}-moved.json'
            temporary=target.with_suffix('.tmp')
            temporary.write_text(json.dumps(evidence),encoding='utf-8')
            temporary.replace(target)
            return True,evidence
        return False,evidence
    return not (document.get('observe_departure') and peer==0),evidence
