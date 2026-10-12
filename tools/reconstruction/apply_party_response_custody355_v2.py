from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round355-party-detail-response-implementation'
HEAD='b934e539e9d0cb279e2d6b58678afdb7b555dcf9';sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,indent=2)+'\n').encode())
paths=['src/core/Application.cpp','src/game/OwnedPartyDirectory.h','src/handlers/OwnedPartyDirectoryService.h'];old={p:(S/p).read_bytes() for p in paths};new=dict(old);edits=[]
for p,b in old.items():
 assert b==subprocess.check_output(['git','show',HEAD+':'+p],cwd=S)
 write(D/'before-v2'/p,b)
def replace(p,a,b):
 # Preserve the original file's actual newline bytes in every literal edit.
 alternatives=[]
 for newline in ['\n','\r\n']:
  before=a.replace('\n',newline).encode();after=b.replace('\n',newline).encode()
  if new[p].count(before)==1 and not any(before==x[0] for x in alternatives):alternatives.append((before,after))
 assert len(alternatives)==1,(p,'unique literal newline',len(alternatives))
 a,b=alternatives[0]
 new[p]=new[p].replace(a,b);edits.append(dict(path=p,before=a.decode(),after=b.decode()))
H=paths[1];T=paths[2];P=paths[0]
replace(H,'#include <memory>\n','#include <memory>\n#include <optional>\n')
replace(H,'        std::vector<std::uint8_t> raw_request; // Full C90, including opaque highWORD.\n','        std::vector<std::uint8_t> raw_request; // Full C90, including opaque highWORD.\n        // Exact original AB response; only current Queued may grant C91.\n        std::optional<Session::NormalWorldResponseAttempt> response;\n')
replace(H,'        std::size_t party_size;\n','        std::size_t party_size;\n        // Provisional native presentation, never C91 authority by itself.\n        std::optional<Session::NormalWorldResponseAttempt> response;\n')
replace(T,'    static bool description_valid(const std::array<std::uint8_t,24>& raw) {\n','    static bool retained_response_current(const OwnedPartyDirectory::Actor& actor,\n        const std::optional<Session::NormalWorldResponseAttempt>& response) {\n        const auto peer=actor.session.lock();\n        return peer && response && response->status()!=Session::NormalWorldResponseStatus::Failed &&\n            peer->normal_world_response_current_on_game(*response);\n    }\n    static bool detail_response_queued(const OwnedPartyDirectory::Detail& detail) {\n        return detail.response && detail.response->status()==Session::NormalWorldResponseStatus::Queued &&\n            retained_response_current(detail.owner,detail.response) &&\n            detail.response->status()==Session::NormalWorldResponseStatus::Queued;\n    }\n    static bool description_valid(const std::array<std::uint8_t,24>& raw) {\n')
replace(T,'                invalid_detail=!captured_entry_current(p.owner) || !captured_entry_current(p.target) ||\n','                invalid_detail=!retained_response_current(p.owner,p.response) ||\n                    !captured_entry_current(p.owner) || !captured_entry_current(p.target) ||\n')
replace(T,'                invalid_detail=invalid_detail || !d.party || !captured_entry_current(d.owner) || !captured_entry_current(d.target) ||\n','                invalid_detail=invalid_detail || !d.party || !retained_response_current(d.owner,d.response) ||\n                    !captured_entry_current(d.owner) || !captured_entry_current(d.target) ||\n')
replace(P,'                            if(!OwnedPartyDirectoryService::captured_entry_current(p.owner) ||\n','                            if(!OwnedPartyDirectoryService::retained_response_current(p.owner,p.response) ||\n                               !OwnedPartyDirectoryService::captured_entry_current(p.owner) ||\n')
replace(P,'                                    auto next_directory=std::make_shared<OwnedPartyDirectory::State>(*before);\n','                                    std::optional<Session::NormalWorldResponseAttempt> response;\n                                    if(request.opcode()==0x90) {\n                                        response=session.capture_normal_world_response(owner->initialization);\n                                        if(!response)continue; // Actual own callback, never copied facade/IDs.\n                                    }\n                                    auto next_directory=std::make_shared<OwnedPartyDirectory::State>(*before);\n')
replace(P,'                                            *owner,*target,members,party_before,request.logical});\n','                                            *owner,*target,members,party_before,request.logical,*response});\n')
replace(P,'                                            *owner,*target,members,participants,party_before->party_size(target->session_id)});\n','                                            *owner,*target,members,participants,party_before->party_size(target->session_id),*response});\n')
replace(P,'                                        if(!detail || !detail->party || !OwnedPartyDirectoryService::captured_entry_current(detail->owner) ||\n','                                        if(!detail || !detail->party || !OwnedPartyDirectoryService::detail_response_queued(*detail) ||\n                                           !OwnedPartyDirectoryService::captured_entry_current(detail->owner) ||\n')
replace(P,'                                        if(!OwnedPartyDirectoryService::captured_entry_current(d.owner) ||\n','                                        if(!OwnedPartyDirectoryService::detail_response_queued(d) ||\n                                           !OwnedPartyDirectoryService::captured_entry_current(d.owner) ||\n')
replace(P,'                                    if(!qualified || dispatch->reentered || !native_parties.same_state(*party_before) ||\n                                       !owned_party_directory->publish(before,std::move(next_directory)))continue;\n','                                    if(!qualified || dispatch->reentered || !native_parties.same_state(*party_before) ||\n                                       owned_party_directory->snapshot()!=before)continue;\n                                    if(response) {\n                                        if(!session.normal_world_response_callback_current(*response) ||\n                                           !OwnedPartyDirectoryService::captured_entry_current(*owner))continue;\n                                        // Full state/frame/merged bytes precede registration.\n                                        // Registration may allocate; an omitted armed AB fails closed.\n                                        session.expect_normal_world_response(*response,framed);\n                                        if(dispatch->reentered || !session.normal_world_response_callback_current(*response) ||\n                                           !OwnedPartyDirectoryService::captured_entry_current(*owner) ||\n                                           !native_parties.same_state(*party_before) || owned_party_directory->snapshot()!=before)continue;\n                                    }\n                                    if(!owned_party_directory->publish(before,std::move(next_directory)))continue;\n')
for p in paths:
 inverse=new[p]
 for e in reversed(edits):
  if e['path']==p:
   a=e['before'].encode();b=e['after'].encode();assert inverse.count(b)==1
   inverse=inverse.replace(b,a)
 assert inverse==old[p]
js(D/'literal-edits-and-inverse.json',dict(head=HEAD,edits=edits,exact_inverse=True,modified_paths=paths))
for p in paths:(S/p).write_bytes(new[p])
js(D/'initial-final-pins.json',[dict(path=p,before_bytes=len(old[p]),before_sha256=sha(old[p]),bytes=len(new[p]),sha256=sha(new[p])) for p in paths])
write(D/'helpers'/'apply_party_response_custody355_v2.py',Path(__file__).read_bytes())
print(json.dumps(dict(modified=paths,edits=len(edits),inverse_exact=True)))
