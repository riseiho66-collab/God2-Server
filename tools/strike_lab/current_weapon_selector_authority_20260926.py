"""Native icon identity and HeroDoll selector evidence, without an item->doll guess."""
import hashlib
import gc
import json
import struct
from collections import Counter
from .current_equipment_20260926 import EquipmentOracle, PIN, require
from .current_appearance_resources import AppearanceResources, source_rows
from .current_world_role_resources import NativeWorldRoleResources, COMPONENT_MANAGER, CWD
from .current_role_doll_resources import BANK, STRIDE, ROOT, DIRECTORY
from .current_indoor_resources import SCRATCH
from .current_item_metadata import NativeItemMetadata
from .omega_assets import decode_csvz

class SelectorResources(NativeWorldRoleResources):
 def allocate(self,length):
  # These source ROMs contain zero-byte ACTBLOCK chunks. Standard malloc(0)
  # may return a unique freeable pointer; model that CRT behavior explicitly.
  try:
   return super().allocate(1 if length==0 else length)
  except AssertionError as error:
   raise AssertionError(f'{error}; request={length:#x} heap={self.heap:#x} '
                        f'limit={self.heap_limit:#x} asset={getattr(self,"active_name",None)}') from error

ASSETS={
 'data2/itmimg/wpn01.romz':('caa72d4dccafacd44a27346f3a8db2e15319960bf003966b835416ed6c189499','eef95acad680643cdf07f570f124a273f7dfe112061596ef074736732ff9395f'),
 DIRECTORY+'r01w000.romz':('e1b3ffeab4430ab92867094f4dd4a3a0f20942130cf704a5de5d94c0dd81e1ef','ccdbcc326a026a8412bb4cf6fc20a3df385ce6a9cba900a5414f055ce7aa6e6a'),
 DIRECTORY+'r01w001.romz':('55a5a82b3095e1b3db1ac3f74b3d818befaea5eec5a043293ed8a0eabb523631','0da2b1ea8875d7ac688c76e1f37bb43ee362eb2d5cd4203baca4aa1a4eea9c88'),
 DIRECTORY+'r02w000.romz':('258e8757582e1f8a7a6373691e1ab3751914c8777c3e7fe6d36ba69314384a45','9b722989c404529007a6269e07d742ea2288eb5c896827bacea44bd54c13795d'),
 DIRECTORY+'r02w001.romz':('ff79ed937e1d0d85158a1485892b1470274c96d9cd00ad50f10da0d91edc16f7','009fc6d8acd191323312184ce398fd914f8340b57b558c063cb76b1facba2fb6'),
}
def sha(data):return hashlib.sha256(data).hexdigest()
def chunks(data):
 require(data[:12]==b'IGSROM02\0\0\0\0','ROM signature')
 at=12
 while at<len(data):
  require(at+12<=len(data),'ROM truncated header');tag=data[at:at+8];size=struct.unpack_from('<I',data,at+8)[0];at+=12
  require(at+size<=len(data),'ROM truncated body');yield tag,data[at:at+size];at+=size
 require(at==len(data),'ROM trailing bytes')

def verify():
 image=EquipmentOracle().image
 appearance=AppearanceResources();native=SelectorResources(appearance)
 for lo,hi in ((0x1ae70,0x1aec0),(0x52260,0x522b0),(0x52460,0x52550),(0x61270,0x614a0),(0x63de0,0x63ed2)):
  require(bytes(native.vm.mem_read(0x400000+lo,hi-lo))==image[lo:hi],'Current PE/native code mismatch')
 _,rows=source_rows();row_by_key={r[0]+r[1]:(26+i,r) for i,r in enumerate(rows)}
 source_report={}
 for path,(raw_sha,plain_sha) in ASSETS.items():
  raw=(ROOT.parent/'God2'/path).read_bytes();plain=decode_csvz(raw,limit=2*1024*1024)
  require(sha(raw)==raw_sha and sha(plain)==plain_sha,'Pinned art source changed')
  name=path.rsplit('/',1)[1];native.files[path]=raw;native.decoded[name]=plain;native.asset_names[path]=name
  parts=list(chunks(plain));actions=[(struct.unpack_from('<I',b)[0],b[24:48].split(b'\0')[0].decode('cp950',errors='replace')) for t,b in parts if t==b'ACT_DATA']
  source_report[path]={'raw_sha256':raw_sha,'decoded_sha256':plain_sha,'actindex':struct.unpack('<H',next(b for t,b in parts if t==b'ACTINDEX'))[0],'action_count':len(actions),'first_actions':actions[:2],'action_ids_sha256':sha(b''.join(struct.pack('<I',a[0]) for a in actions)),'has_wpn_source_tag':any(tag in plain.lower() for tag in (b'wpn01001',b'wpn01002'))}
 # Real item-art ROM: original loader and action-ID search, no reconstructed action table.
 icon='data2/itmimg/wpn01.romz';native.active_name='wpn01.romz'
 native.vm.mem_write(SCRATCH,CWD+b'\\'+icon.replace('/','\\').encode()+b'\0')
 icon_result=native.call(0x29820,SCRATCH,65,this=BANK)
 require(icon_result==6549,'Unexpected item ROM ACTINDEX')
 native.vm.mem_write(SCRATCH+0x4000,b'\0'*16);native.vm.mem_write(SCRATCH+0x400c,struct.pack('<I',BANK))
 metadata=NativeItemMetadata();icons=[]
 for ordinal in (0,1):
  item=metadata.item_row('WPN',ordinal);record=item['record'];identifier=struct.unpack_from('<H',record,0x114)[0];group=struct.unpack_from('<H',record,0x116)[0]
  require(group==0,'WPN icon group')
  action=native.call(0x1ae70,group+0x41,identifier,this=SCRATCH+0x4000)
  require(action==ordinal,'Original icon action lookup differs')
  action_ptr=native.u32(BANK+65*STRIDE+0x1090+4*action)
  require(native.u32(action_ptr)==identifier,'Native icon ID mismatch')
  name=native.string(action_ptr+24)
  require(name==record[8:46].split(b'\0')[0],'Native icon label differs from item definition')
  icons.append({'item_id':item['key'],'source_line':item['source_line'],'item_and_icon_name':name.decode('cp950'),'icon_id':identifier,'rom_slot':65,'native_action_index':action})
 # UI icon and world HeroDoll use independent fixture banks.
 del native
 gc.collect()
 # Four source-labelled world knife variants. These are NOT asserted to be WPN1/2.
 selectors=[]
 for binary in (0,1):
  for ordinal in (0,1):
   # Independent uncached cases retain the original bounded heap size. The CRT
   # adapter is monotonic (freed pages are not reused); keeping all four cases
   # in one VM exhausted its fixture heap on the third case, not the ROM parser.
   native=SelectorResources(appearance)
   for path,(raw_sha,plain_sha) in ASSETS.items():
    if not path.startswith(DIRECTORY):continue
    raw=(ROOT.parent/'God2'/path).read_bytes();plain=decode_csvz(raw,limit=2*1024*1024)
    require(sha(raw)==raw_sha and sha(plain)==plain_sha,'Pinned world source changed')
    name=path.rsplit('/',1)[1];native.files[path]=raw;native.decoded[name]=plain;native.asset_names[path]=name
   native._prepare_component_manager()
   key=f'r{binary+1}w0{ordinal:02d}';line,row=row_by_key[key]
   ptr=appearance.lookup(binary,3,0,ordinal,0)
   require(ptr==appearance.by_key[key],'Original key conversion/hash lookup')
   block=bytes((binary,0,binary,0,binary,0,binary,ordinal))
   native.vm.mem_write(SCRATCH+0x2000,b'\xa5'*8+block+b'\xa5'*8)
   native.vm.mem_write(SCRATCH+0x3000,b'\xa5'*28)
   native.call(0x61270,0,0,SCRATCH+0x2008,SCRATCH+0x3008,this=COMPONENT_MANAGER)
   handles=struct.unpack('<6H',native.vm.mem_read(SCRATCH+0x3008,12))
   require(handles[3]==native.cache(key) and handles[3]!=65535,'Complete resolver selected wrong weapon')
   require(bytes(native.vm.mem_read(SCRATCH+0x2000,24))==b'\xa5'*8+block+b'\xa5'*8,'Component input/canary changed')
   require(bytes(native.vm.mem_read(SCRATCH+0x3000,8))==b'\xa5'*8 and bytes(native.vm.mem_read(SCRATCH+0x3014,8))==b'\xa5'*8,'Output bounds')
   filename=row[3].lower().replace('\\','/')
   require(DIRECTORY+filename in native.opens,'Native requested filename not loaded')
   selectors.append({'source_key':key,'source_line':line,'source_label':row[6].encode('latin1').decode('cp950'),'component_pair_hex':block[6:8].hex(),'full_unmounted_fixture_block':block.hex(),'native_handle':handles[3],'filename':filename,'heap_used':native.heap-native.heap_start_address,'heap_limit':native.heap_limit,'item_mapping':'UNVERIFIED'})
   del native
   gc.collect()
 require(source_report[DIRECTORY+'r01w000.romz']['actindex']==source_report[DIRECTORY+'r01w001.romz']['actindex']==4201,'Expected ACTINDEX collision')
 return {'status':'PASS','current_exe_sha256':PIN,'icon_records':icons,'native_hero_selectors':selectors,'assets':source_report,'scope':'Actual native ROM loader, icon action lookup, full unmounted 61270 including cache/path/decompress/ROMs. No item-to-HeroDoll mapping, full DA refresh, renderer or server formula claim.'}
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))

