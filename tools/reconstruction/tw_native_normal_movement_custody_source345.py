from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
REV='dd7524e842479f4ca534f1f0a5291d93c3412c34'
SPEC={
 'src/handlers/RecoveredMovementService.h':[(17,21),(38,68),(108,154)],
 'src/handlers/RecoveredMovementService.cpp':[(203,234),(289,332),(384,428),(467,522)],
 'src/db/RecoveredCharacterRepository.h':[(55,64)],
 'src/db/SqliteRecoveredCharacterRepository.cpp':[(958,996)],
 'src/game/RecoveredPosition.h':[(1,14)],
 'src/protocol/RecoveredMovement.h':[(10,27),(73,104)],
 'src/protocol/RecoveredNativeMovement.h':[(5,33)],
 'src/db/SqliteOwnedEquipmentTransaction.h':[(87,89),(104,129)],
 'src/db/SqliteOwnedEquipmentTransaction.cpp':[(7,24),(91,190),(192,217),(244,265)],
 'src/db/SqliteNativeEquipmentSnapshotRepository.cpp':[(25,35),(92,119)],
 'src/db/NativeEquipmentSnapshotRepository.h':[(11,40)],
 'src/net/Session.h':[(108,129),(338,348),(421,434)],
 'src/net/Session.cpp':[(61,68),(116,150),(1534,1568),(1585,1628),(1958,1968),(2184,2208),(2318,2359),(3185,3200)],
 'src/protocol/RecoveredWorldEntryView.h':[(62,81)],
 'src/game/SharedTaiwanMovement.cpp':[(65,120),(122,149)],
 'src/core/Application.cpp':[(843,851),(1198,1212),(2231,2256),(2354,2381),(2391,2429),(2478,2506),(6441,6453),(6495,6507)],
}
sha=lambda value:hashlib.sha256(value).hexdigest()
run=lambda *args:subprocess.check_output(['git','-C',str(ROOT),*args])
head=run('rev-parse','HEAD').decode().strip()
refs=[]
cuts=[]
file_end_adjustments=[]
parts=[]
for name,ranges in SPEC.items():
 body=run('show',f'{REV}:{name}')
 text=body.decode('utf-8-sig').splitlines()
 for low,high in ranges:
  if high>len(text):
   file_end_adjustments.append({'path':name,'requested_end':high,'actual_end':len(text)})
   high=len(text)
  assert 1<=low<=high<=len(text),(name,low,high,len(text))
  cut=''.join(f'{name}:{i}: {text[i-1]}\n' for i in range(low,high+1)).encode()
  parts.append(cut)
  cuts.append({'path':name,'first_line':low,'last_line':high,'bytes':len(cut),'sha256':sha(cut)})
 refs.append({'path':name,'snapshot_revision':REV,'source_bytes':len(body),'source_sha256':sha(body)})
(OUT/'source-cuts.txt').write_bytes(b'\n'.join(parts))
(OUT/'source-references.json').write_text(json.dumps({'snapshot_revision':REV,'head_at_capture_start':head,
 'head_at_capture_end':run('rev-parse','HEAD').decode().strip(),'file_end_adjustments':file_end_adjustments,'sources':refs},indent=2)+'\n',encoding='utf-8',newline='\n')
(OUT/'cut-manifest.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'sources':len(refs),'cuts':len(cuts),'scope':'immutable source/hash only; no source execution'}))
