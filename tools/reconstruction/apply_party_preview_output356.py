from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
D=Path(__file__).resolve().parent
HEAD='6c2d3412e22316d1537323bc13e449f87ddfd03a'
def sha(b):return hashlib.sha256(b).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
names=['src/net/Session.h','src/net/Session.cpp','src/core/Application.cpp']
original={f:(R/f).read_bytes() for f in names}
prior=D.parent/'round356-party-preview-transport-proposal/complete-final/whole'
for f,b in original.items():assert (prior/f).read_bytes()==b,f
for f,b in original.items():
    p=D/'before'/f;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
data=dict(original);edits=[]
def replace(f,old,new):
    # Unique literal replacement preserves all bytes outside the exact span.
    b=data[f];o=old.encode('utf-8');n=new.encode('utf-8')
    if b.count(o)!=1:
        o=old.replace('\n','\r\n').encode('utf-8');n=new.replace('\n','\r\n').encode('utf-8')
    assert b.count(o)==1,(f,old[:90],b.count(o))
    data[f]=b.replace(o,n,1)
    edits.append({'source':f,'before_hex':o.hex(),'after_hex':n.hex(),'before_bytes':len(o),'after_bytes':len(n)})
replace('src/net/Session.h',
'''    std::optional<NormalWorldOutputHandle> capture_normal_world_output(const NormalWorldInitialization&);
''',
'''    std::optional<NormalWorldOutputHandle> capture_normal_world_output(const NormalWorldInitialization&);
    // Trusted SAME game owner, exact private Written INIT for this Session.
    // Recipient transport custody only; no callback permission/consent/ACK.
    // The own-callback capture above retains its actual TLS requirement.
    std::optional<NormalWorldOutputHandle> capture_normal_world_output_on_game(const NormalWorldInitialization&);
''')
replace('src/net/Session.cpp',
'''        throw std::logic_error("Normal output recipient requires its own actual world callback");
    if(!normal_world_initialization_current_on_game(initialization) || !initialization.entry_written())return std::nullopt;
''',
'''        throw std::logic_error("Normal output recipient requires its own actual world callback");
    return capture_normal_world_output_on_game(initialization);
}
std::optional<Session::NormalWorldOutputHandle> Session::capture_normal_world_output_on_game(
        const NormalWorldInitialization& initialization) {
    if(!normal_world_initialization_current_on_game(initialization) || !initialization.entry_written())return std::nullopt;
''')
replace('src/core/Application.cpp',
'''#include "handlers/OwnedPartyDirectoryService.h"
''',
'''#include "handlers/OwnedPartyDirectoryService.h"
#include "game/OwnedPartyPreviewTransport.h"
''')
replace('src/core/Application.cpp',
'''            std::map<std::uint64_t,std::weak_ptr<Session>> party_sessions;
''',
'''            std::map<std::uint64_t,std::weak_ptr<Session>> party_sessions;
            std::unique_ptr<OwnedPartyPreviewTransport> party_preview_transport;
            if(owned_party_directory)party_preview_transport=std::make_unique<OwnedPartyPreviewTransport>(config.max_sessions);
''')
replace('src/core/Application.cpp',
'''                                    if(!qualified || dispatch->reentered || !native_parties.same_state(*party_before) ||
                                       owned_party_directory->snapshot()!=before)continue;
                                    if(response) {
''',
'''                                    // Actual C91 peer output custody; no own-response ticket.
                                    // All source/bytes/registry allocations precede both commits.
                                    std::optional<OwnedPartyPreviewTransport::Prepared> preview;
                                    if(request.opcode()==0x91) {
                                        auto sources=members;
                                        if(std::none_of(sources.begin(),sources.end(),[&](const auto& actor){return actor.same_owner(*owner);}))sources.push_back(*owner);
                                        auto prepared=party_preview_transport->prepare(sources,recipients,projections);
                                        if(!prepared)continue;
                                        preview.emplace(std::move(*prepared));
                                    }
                                    if(!qualified || dispatch->reentered || !native_parties.same_state(*party_before) ||
                                       owned_party_directory->snapshot()!=before || (preview && !preview->current()))continue;
                                    if(response) {
''')
replace('src/core/Application.cpp',
'''                                    if(!owned_party_directory->publish(before,std::move(next_directory)))continue;
                                    if(next_party)native_parties=std::move(*next_party); // No callback between the two ephemeral commits.
                                    wire=std::move(merged);
                                    // Submission only: a transport failure cannot be called
                                    // consent or rolled back as if the pending prefix never existed.
                                    for(auto& [id,bytes]:projections)recipients.at(id)->send_world_records(std::move(bytes));
''',
'''                                    if(!owned_party_directory->publish(before,std::move(next_directory)))continue;
                                    if(preview)preview->mark_committed(); // No allocation, immediately after successful CAS.
                                    if(next_party)native_parties=std::move(*next_party); // No callback between the two ephemeral commits.
                                    wire=std::move(merged);
                                    // Actual peer FIFO custody only. Caller final rejection,
                                    // consent, Written/native ACK and all variants remain OPEN.
                                    // A postcommit exception retires/closes exact held peers;
                                    // committed state is never rolled back or retried.
                                    if(preview)preview->submit();
                                    else for(auto& [id,bytes]:projections)recipients.at(id)->send_world_records(std::move(bytes));
''')
replace('src/core/Application.cpp',
'''            auto scheduler=std::make_shared<Scheduler>(game.get_executor(),std::chrono::milliseconds(50),[&] {
                world.update(0.05f);
''',
'''            auto scheduler=std::make_shared<Scheduler>(game.get_executor(),std::chrono::milliseconds(50),[&] {
                if(party_preview_transport)party_preview_transport->settle(); // Pending has no native timeout.
                world.update(0.05f);
''')
replace('src/core/Application.cpp',
'''                if(stopping) return;
                guild_delivery_lifetime->store(false);
''',
'''                if(stopping) return;
                if(party_preview_transport)party_preview_transport->stop(); // Before scheduler/network and borrowed game teardown.
                guild_delivery_lifetime->store(false);
''')
for f,b in data.items():
    inverse=b
    for e in reversed(edits):
        if e['source']!=f:continue
        n=bytes.fromhex(e['after_hex']);o=bytes.fromhex(e['before_hex'])
        assert inverse.count(n)==1;inverse=inverse.replace(n,o,1)
    assert inverse==original[f],f
new='src/game/OwnedPartyPreviewTransport.h';newbytes=(D/'new-OwnedPartyPreviewTransport.h').read_bytes()
assert not (R/new).exists();assert b'\r' not in newbytes and not newbytes.startswith(b'\xef\xbb\xbf')
for f,b in data.items():assert (R/f).read_bytes()==original[f]
for f,b in data.items():(R/f).write_bytes(b)
(R/new).write_bytes(newbytes)
manifest=[]
for f in names+[new]:
    b=(R/f).read_bytes();p=D/'candidate'/f;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
    assert b==(newbytes if f==new else data[f])
    manifest.append({'source':f,'bytes':len(b),'sha256':sha(b),'new':f==new,'before_sha256':sha(original[f]) if f in original else None})
result={'head':HEAD,'scope':'Source only; three old whole files exact literal inverse, new header explicitly separate; no product execution','old_whole_inverse_equal':True,'edits':edits,'candidate':manifest}
(D/'apply-receipt.json').write_bytes((json.dumps(result,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'status':'applied','edits':len(edits),'candidate':manifest}))
