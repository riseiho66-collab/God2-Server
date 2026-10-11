"""Preserve loaded priority-module disk files and runtime pointer candidates."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import pefile
HOME=Path(__file__).resolve().parents[3]
OUT=HOME/'artifacts/capture_work/host-20260918-1430/output'


def main():
    dest=HOME/'artifacts/reports/native-wow64-20260919/modules'
    dest.mkdir(exist_ok=False)
    text=(OUT/'native-master-01-native.log').read_text(encoding='ascii')
    priority={'kernel32','kernelbase','ntdll','ntdll32','user32','ddraw','ws2_32','wininet'}
    modules={}
    current=None
    for line in text.splitlines():
        m=re.match(r'^([0-9a-f`]+) ([0-9a-f`]+)\s+(\w+)\s',line)
        if m:
            current=(m[3].lower(),int(m[1].replace('`',''),16),int(m[2].replace('`',''),16))
        elif current and line.strip().startswith('Image path:') and current[0] in priority:
            path=Path(line.split('Image path:',1)[1].strip())
            if path.is_file():
                modules[(current[0],current[1])]=(path,current[2])
    records=[]
    exports={}
    for (name,base),(path,end) in modules.items():
        data=path.read_bytes(); sha=hashlib.sha256(data).hexdigest()
        target=dest/(sha+'.dll')
        if not target.exists():
            shutil.copy2(path,target)
        pe=pefile.PE(data=data)
        table=[]
        for symbol in getattr(getattr(pe,'DIRECTORY_ENTRY_EXPORT',None),'symbols',[]):
            entry={'name':symbol.name.decode('ascii',errors='replace') if symbol.name else None,
                   'ordinal':symbol.ordinal,'rva':symbol.address,
                   'forwarder':symbol.forwarder.decode('ascii') if symbol.forwarder else None}
            table.append(entry)
            if not symbol.forwarder:
                exports.setdefault(base+symbol.address,[]).append(dict(entry,module=name,module_base=base,module_sha256=sha))
        records.append({'module':name,'base':base,'end':end,'disk_path':str(path),'sha256':sha,
                        'timestamp':pe.FILE_HEADER.TimeDateStamp,'exports':table,
                        'limitation':'Disk file copied after capture; not byte-equivalence proof of all mapped module pages'})
    image=(OUT/'native-master-01-stable.bin').read_bytes()
    candidates=[]
    for rva in range(0x170000,0x171000,4):
        target=struct.unpack_from('<I',image,rva)[0]
        if target in exports:
            candidates.append({'iat_rva_candidate':rva,'slot_va':0x400000+rva,'runtime_target':target,
                               'export_matches':exports[target],'status':'OBSERVED_POINTER_NOT_REPAIRED_IAT'})
    (dest/'module-index.json').write_text(json.dumps(records,indent=2))
    (dest/'runtime-import-candidates.json').write_text(json.dumps(candidates,indent=2))
    print(json.dumps({'modules':len(records),'pointer_candidates':len(candidates),'g04_verified':False}))


if __name__=='__main__':
    main()
