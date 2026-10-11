"""Audit native four-button allocation and fresh-client owned-save restoration."""
from contextlib import closing
import json
import re
import sqlite3
import struct
from .run_private_scene_actor_route import ROOT,sha
from .current_attribute_allocation_20260927 import audit

CANDIDATE='fee579ab029aba362d7d333daf9bcc6e3a382f76ba9d644cbb7c515652ad6a7c'
RAPID_CANDIDATE='59591afb03b4bb0aadfe5063c636557ccb127a6c925221d954e78358346f50d6'
EVIDENCE=ROOT/'artifacts/research/character-growth-native-20260927'

def require(value,reason):
    if not value:raise ValueError(reason)

def role(path):
    with closing(sqlite3.connect((path/'diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('pragma quick_check').fetchone()==('ok',),'Database integrity failed')
        row=db.execute('select logical,revision from character_role_snapshots where character_id=4').fetchone()
        require(db.execute('select total from character_experience where character_id=4').fetchone()==(250,),'Allocation changed XP')
        return row

def main():
    require(sha(EVIDENCE/'attribute-allocation.accepted-server.exe')==CANDIDATE,'Archived accepted server pin changed')
    binding=audit();require(len(binding['cases'])==4,'Native allocation binding incomplete')
    root=ROOT/'artifacts/playtests'
    allocated=root/'private-native-blackbox-attribute-allocation-20260927-09'
    restored=root/'private-native-blackbox-attribute-allocation-restore-20260927-01'
    result=json.loads((allocated/'run-result.json').read_text('utf-8'));ui=result['ui']
    require(result['accepted'] and result['server_sha256']==CANDIDATE,'Allocation receipt failed')
    expected=[12,10,12,12]
    initial=bytes.fromhex(ui['saved_role']['logical_hex'])
    for step,(stage,native) in enumerate(zip(ui['allocation_stages'],binding['cases'],strict=True),1):
        require(stage['control']==native['control'] and stage['selector']==native['selector'],'Button/selector mapping changed')
        expected[native['stat_index']]+=1
        logical=bytearray(initial);struct.pack_into('<H',logical,3,4-step);struct.pack_into('<4H',logical,5,*expected)
        require(stage['logical_hex']==logical.hex() and stage['revision']==2+step,'Saved allocation bytes/revision differ')
        require(stage['native']=={'level':2,'points':4-step,'stats':expected},'Native allocation differs')
    require(ui['empty_budget_unchanged'],'Empty-budget client guard not verified')
    require(result['resources_before']==[100,120,50,80,4] and result['resources_after']==[100,120,50,80,8],
        'Allocation changed HP/MP values or incorrect transaction count')
    require(set(result['changed_tables'])=={'character_resources','character_role_snapshots'},'Allocation changed unrelated tables')
    log=(allocated/'server.log').read_text('utf-8',errors='replace')
    require([int(x) for x in re.findall(r'OWNED_ATTRIBUTE_ALLOCATION_HANDLED.*?selector=(\d+)',log)]==[2,3,1,4],
        'Four original requests not handled in order')
    saved,revision=role(allocated)
    require(saved.hex()==ui['allocated_role']['logical_hex'] and revision==6,'Actual allocation row mismatch')
    restored_result=json.loads((restored/'run-result.json').read_text('utf-8'))
    require(restored_result['accepted'] and restored_result['server_sha256']==CANDIDATE,'Fresh-client restoration failed')
    require(restored_result['ui']['native_role']=={'level':2,'points':0,'stats':[13,11,13,13]},'Restored native attributes differ')
    require(role(restored)==(saved,revision),'Restored save changed')
    for receipt in (result,restored_result):
        require(all(receipt[key] for key in ('source_database_unchanged','live_database_unchanged',
            'live_client_unchanged','private_client_unchanged')),'External state changed')
    require(restored_result['durable_state_unchanged'],'Fresh login modified any durable table')
    for path in (allocated,restored):
        cfg=json.loads((path/'server-config.json').read_text('utf-8'))
        require(not cfg['development']['diagnostic_character_growth'] and not cfg['development']['diagnostic_battle_transition'],
            'Allocation/restoration reseeded growth or battle')
    require(sha(EVIDENCE/'attribute-allocation-batched.accepted-server.exe')==RAPID_CANDIDATE,'Latest accepted server pin changed')
    rapid=root/'private-native-blackbox-attribute-allocation-rapid-20260927-02'
    rapid_restore=root/'private-native-blackbox-attribute-allocation-rapid-restore-20260927-01'
    for path in (rapid,rapid_restore):
        receipt=json.loads((path/'run-result.json').read_text('utf-8'))
        require(receipt['accepted'] and receipt['server_sha256']==RAPID_CANDIDATE,'Rapid/fresh-client receipt failed')
        require(all(receipt[key] for key in ('source_database_unchanged','live_database_unchanged',
            'live_client_unchanged','private_client_unchanged')),'Rapid test changed external state')
        saved_rapid,revision_rapid=role(path)
        require(list(struct.unpack_from('<4H',saved_rapid,5))==[14,10,13,13] and
            saved_rapid[3:5]==bytes(2) and revision_rapid==6,'Rapid allocation row mismatch')
        cfg=json.loads((path/'server-config.json').read_text('utf-8'))
        require(not cfg['development']['diagnostic_character_growth'] and not cfg['development']['diagnostic_battle_transition'],
            'Rapid test reseeded growth/battle')
        if path==rapid:
            require(receipt['ui']['allocated_role']['native']=={'level':2,'points':0,'stats':[14,10,13,13]} and
                receipt['ui']['empty_budget_unchanged'] and receipt['resource_values_unchanged'],'Rapid native/HP/MP mismatch')
            require([int(x) for x in re.findall(r'OWNED_ATTRIBUTE_ALLOCATION_HANDLED.*?selector=(\d+)',
                (path/'server.log').read_text('utf-8',errors='replace'))]==[2,2,1,4],'Repeated selector lost')
        else:
            require(receipt['durable_state_unchanged'] and not cfg['world']['owned_attribute_allocation']['enabled'],
                'Rapid restoration changed save/enabled allocation')
            require(receipt['ui']['native_role']=={'level':2,'points':0,'stats':[14,10,13,13]},'Rapid restored native mismatch')
    report={'candidate_sha256':CANDIDATE,'native_buttons_accepted':4,'fresh_client_restore':'PASS',
        'empty_budget_guard':'PASS','allocation_receipt':str(allocated/'run-result.json'),
        'restore_receipt':str(restored/'run-result.json'),'production_enabled':False,
        'allocation_rule_origin':'NATIVE_VERIFIED','baseline_and_xp_origin':'CUSTOM-0013',
        'derived_attack_defense_hp_mp_growth_formulas_recovered':False,
        'latest_candidate_sha256':RAPID_CANDIDATE,'rapid_repeated_selector_live':'PASS',
        'rapid_fresh_client_restore':'PASS','rapid_restore_receipt':str(rapid_restore/'run-result.json'),
        'actual_multi_request_client_frame_observed':False}
    (EVIDENCE/'allocation-acceptance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
