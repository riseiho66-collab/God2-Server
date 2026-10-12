"""One-shot manual source findings and individually verified custody seal; no target execution."""
from pathlib import Path
import hashlib
import json
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def emit(name,value):
    path=OUT/name
    if path.exists():
        raise RuntimeError('Refusing overwrite: '+name)
    path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())

if (OUT/'SEAL.json').exists():
    raise RuntimeError('Already sealed; do not rerun')
refs=json.loads((OUT/'source-references.json').read_bytes())
for source in refs['sources']:
    data=(ROOT/source['path']).read_bytes()
    if len(data)!=source['bytes'] or sha(data)!=source['sha256']:
        raise RuntimeError('Audited current source changed: '+source['path'])
for cut in refs['cuts']:
    raw=(OUT/cut['raw_member']).read_bytes()
    annotated=(OUT/cut['annotated_member']).read_bytes()
    if len(raw)!=cut['bytes'] or sha(raw)!=cut['sha256'] or sha(annotated)!=cut['annotated_sha256']:
        raise RuntimeError('Retained cut changed')

findings={
 'scope':'Current hosted TW37/85 diagnostic town acquisition and common owned storage seams only; not a global absence search.',
 'snapshot_head':refs['snapshot_head'],
 'source_designs':{'town_stage':'CUSTOM-0021','scalar_reward':'CUSTOM-0022','common_storage':'CUSTOM-0092','normal_full25_move':'CUSTOM-0094'},
 'task_wording_correction':'143 denotes source line143, not CUSTOM0143. No CUSTOM0143 authority is claimed.',
 'hosted_route':[
  {'source':'src/core/Application.cpp:5551-5556','fact':'Diagnostic flags, no existing quest journal, single record or configured85then37 batch, CharacterSelected/InWorld.'},
  {'source':'src/core/Application.cpp:5576-5601','fact':'Actual movement/saved position near selected diagnostic NPC; saved stage plus Lua plan; reward needs explicitly empty scalar slot0 with selected source hash; original dialogue prebuilt before open.'},
  {'source':'src/core/Application.cpp:5607-5664','fact':'Pending plan copied, actual movement position rechecked, conversation identity confirmed, quest/scalar41 original frame prebuilt before complete_town_guide; pending/followup updated only after callback returns.'},
  {'source':'src/core/Application.cpp:5665-5689','fact':'Same-frame followup validates actual saved state and opens next request word; response may append original followup dialogue. This is not an initial common material issuer.'}],
 'town_atomic_authority':{
  'source':'src/db/SqliteRecoveredCharacterRepository.cpp:200-232',
  'preconditions':'Stage2/journal2, exact current empty scalar slot0, positive revisions, source SHA, no pending battle.',
  'writes':'One existing transaction CASes diagnostic stage3/journal0 and item5569/count1 scalar slot, inserts diagnostic_town_guide_reward CUSTOM-0022 and reads back before COMMIT.',
  'return':'Public TownGuideRewardCommit{progress,slot} at header51-54; does not contain private writer identity or genuine common/native paired material.'},
 'common_writer':{
  'source':'src/db/SqliteOwnedInventoryRepository.cpp:120-197',
  'required':'Already-proposed complete next owner population and actual issuer; positive common definition/id/revisions/acquisition tuple with genuine aliases where required.',
  'mint':'Line143 inserts already-supplied id/definition_key/stackable/acquisition_sha256/acquisition_record. Line144 binds those fields. Registry uniqueness is replay/theft prevention, not an acquisition or definition supplier.',
  'guard':'Autocommit entry, guarded private stage, issuer phase callbacks cannot write/change transaction/reenter; total_changes64 is checked. Private Committed allocated before the single COMMIT.',
  'schema':'owned_item_instances definition_key is a positive integer constraint; this schema does not supply a native-to-common definition mapping.'},
 'composition_obstruction':[
  'Common replace inside the existing town transaction fails its autocommit precondition (inventory172; joint44).',
  'Town completion inside a common Issuer would perform writes and transaction operations prohibited by the issuer contract and checked at inventory187/joint74. Nested BEGIN is not an authorized storage composition.',
  'Two sequential operations have two COMMIT boundaries: town scalar grant could persist even if later common issuance fails. No two-call adapter preserves the existing atomic grant.',
  'A public town return, durable observe_committed, or definition observation cannot be minted into fresh acquisition authority or an actual mutation receipt.'
 ],
 'definition_limits':{'source':'src/db/NativeItemDefinitionObservation.h:1-44; SqliteOwnedInventoryRepository.cpp:214-245; NativeMapItemCatalog.h:1-43',
  'fact':'Historical TWP/WPN/EQU/TEQ definition observation has no current bank, common-ID or acquisition authority; token0 native key and token5 metadataDWORD0 differ. SPI5569 display source is source-display-only. No native key5569 lookup outcome was executed or inferred.'},
 'native_custody_limits':{'source':'src/game/TaiwanOwnedBagItemMaterial.h:1-40; SharedTaiwanOwnedBagMoveSource.cpp:206-288',
  'fact':'Normal-entry C24 owns a real private initialization receipt, current saved position, actor handle and complete before bank. It only moves/swaps existing instances. Full25 and item20 aliases must share genuine source/slot/key/revision; raw count is not automatically common quantity. Shape validation and passive actual-commit wire carriers do not supply acquisition.'},
 'lifetime_seam':{'source':'src/core/Application.cpp:630-641,941-951,1232-1240,2323-2332; src/handlers/DiagnosticQuestConversation.h:93-104',
  'fact':'Actual game-thread repository and session-keyed pending/conversation state are retained; disconnect erases both. consume_after_commit keeps a bound-map reference across a synchronous non-reentrant callback. Future storage composition must preserve this lifetime and not add arbitrary callbacks/reader reentry.'},
 'earliest_missing_supplier':[
  'A source-qualified common definition mapping for the scalar native reward key; neither literal5569 nor metadata token5 proves a common definition identity.',
  'A genuine globally unused instance ID plus acquisition-event provenance/entitlement supplier before stage_replace line143, and a complete current owner population/destination permission.',
  'For actual normal-entry full25/native1215 custody: paired genuine item20/full25 material and complete native bank/actor/pose source; no guessed opaque fields, zero fill, formatter1/30 rights or initial replay.'
 ],
 'next_atomic_owner_seam':'Only after a genuine supplier is qualified, add one same-connection typed atomic operation internally staging the existing town CAS/receipt and common registry/cells/full native bank under one owner transaction and one COMMIT; prepare original reply/private actual receipts before COMMIT. Existing private stage APIs do not currently expose this composition. This is a necessary dependency description, not an implementation proposal or new grant policy.',
 'decision':'OPEN exact hosted supplier and atomic-owner seam. No source implementation is justified with the current contracts alone.',
 'credits':{'new_native_opcode':0,'new_format':0,'whole_route':0,'native_acceptance':0},
 'execution':'Source/hash/git custody only. No tracked edits, target/API/SQL/native/codec/compiler/build/test execution.'
}
emit('manual-source-findings.json',findings)
emit('capture-success-receipt.json',{'helper':'capture_common_acquisition_source350.py','exit_code':0,
 'stdout':{'head':refs['snapshot_head'],'source_count':14,'cut_count':23,'prior347_members':70},
 'invocation':'Python312 python.exe -B capture_common_acquisition_source350.py; source-only helper executed once.',
 'same_current_source_readback':True})
end_head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip()
emit('final-readback-custody.json',{'snapshot_head':refs['snapshot_head'],'seal_time_head':end_head,
 'all14_audited_source_hashes_unchanged':True,'all23_raw_and_annotated_cuts_verified':True,
 'scope':'Source audit only; snapshot HEAD label is not coerced to another round publication.'})
members=[]
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data=path.read_bytes()
        members.append({'name':path.relative_to(OUT).as_posix(),'bytes':len(data),'sha256':sha(data)})
emit('SEAL.json',{'schema':'individual-member-sha256-v1','head':refs['snapshot_head'],
 'member_count':len(members),'total_bytes':sum(m['bytes'] for m in members),'native_complete_routes':0,'members':members})
for m in members:
    data=(OUT/m['name']).read_bytes()
    if len(data)!=m['bytes'] or sha(data)!=m['sha256']:
        raise RuntimeError('Sealed member readback mismatch')
seal=(OUT/'SEAL.json').read_bytes()
print(json.dumps({'head':refs['snapshot_head'],'member_count':len(members),'total_bytes':sum(m['bytes'] for m in members),
 'seal_bytes':len(seal),'seal_sha256':sha(seal),
 'helpers':[{'name':n,'bytes':len((OUT/n).read_bytes()),'sha256':sha((OUT/n).read_bytes())}
            for n in ('capture_common_acquisition_source350.py','seal_common_acquisition_source350.py')]}))
