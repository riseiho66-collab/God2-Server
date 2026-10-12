from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
BASE='1b9bccaf29915afb37d7ee3379f5261b141eba2c'
H='src/handlers/RecoveredMovementService.h'
CPP='src/handlers/RecoveredMovementService.cpp'
sha=lambda value:hashlib.sha256(value).hexdigest()
old={}
for name in (H,CPP):
 old[name]=(ROOT/name).read_bytes()
 pinned=subprocess.check_output(['git','-C',str(ROOT),'show',f'{BASE}:{name}'])
 assert old[name].replace(b'\r\n',b'\n')==pinned.replace(b'\r\n',b'\n'),name
 (OUT/('before-'+Path(name).name)).write_bytes(old[name])

def block(text):return text.replace('\n','\r\n').encode()
def replace_one(body,prior,next):
 assert body.count(prior)==1,(prior[:100],body.count(prior))
 return body.replace(prior,next,1)

h=old[H]
h_include=block('#include <thread>\n')
h=replace_one(h,block('#include <memory>\n'),block('#include <memory>\n')+h_include)
forward=block('class Session;\nclass SqliteOwnedEquipmentTransaction;\n')
h=replace_one(h,block('namespace god2 {\n'),block('namespace god2 {\n')+forward)
api=block('''    // CUSTOM-0095: actual normal-entry callback only, one atomic whole-batch
    // saved-pose/native-witness update. Complete current banks are mandatory;
    // no fallback, grant, stale-witness rebase or recovered native5D claim.
    CommittedMove move_committed_with_owned_material(Session&,SqliteOwnedEquipmentTransaction&,
        std::span<const RecoveredMovement::Request> requests);
''')
h=replace_one(h,block('    std::vector<std::uint8_t> move(std::uint64_t session'),api+block('    std::vector<std::uint8_t> move(std::uint64_t session'))
position_equality=block('        bool operator==(const Position&) const = default;\n')
h=replace_one(h,block('        std::optional<RecoveredPosition> saved;\n'),block('        std::optional<RecoveredPosition> saved;\n')+position_equality)
private_api=block('''    struct PreparedMove {
        Position next;
        std::vector<std::uint8_t> response;
        std::vector<CommittedMove::Step> path;
        std::size_t displaced_steps{};
    };
    PreparedMove prepare_move_batch(const Position&,std::span<const RecoveredMovement::Request>) const;
    void reject_owned_movement_mutation() const;
    const std::thread::id owned_movement_thread_=std::this_thread::get_id();
    mutable bool owned_movement_busy_=false,owned_movement_invalid_=false;
''')
h=replace_one(h,block('    RecoveredCharacterRepository& characters_;\n'),private_api+block('    RecoveredCharacterRepository& characters_;\n'))

body=old[CPP]
includes=block('#include "db/SqliteOwnedEquipmentTransaction.h"\n#include "net/Session.h"\n')
body=replace_one(body,block('#include "handlers/RecoveredMovementService.h"\n'),block('#include "handlers/RecoveredMovementService.h"\n')+includes)

# Lift exact original batch validation and ACK/path prebuild once.
start=body.index(block('    auto next=it->second;\n    const auto before=next.saved;\n    std::size_t displaced_steps=0;\n'))
end=body.index(block('    // Validate the entire batch, then commit before publishing state or ACKs.\n'),start)
batch=body[start:end]
default_call=block('''    auto prepared=prepare_move_batch(it->second,requests);
    auto& next=prepared.next;
    const auto before=next.saved;
    auto& response=prepared.response;
    auto& path=prepared.path;
    const auto displaced_steps=prepared.displaced_steps;
''')
body=body[:start]+default_call+body[end:]
helper=block('''void RecoveredMovementService::reject_owned_movement_mutation() const {
    if(owned_movement_busy_) {
        owned_movement_invalid_=true;
        throw std::logic_error("Owned normal-entry movement reentered by a mutation");
    }
}
RecoveredMovementService::PreparedMove RecoveredMovementService::prepare_move_batch(
    const Position& position,std::span<const RecoveredMovement::Request> requests) const {
''')
helper+=batch.replace(block('    auto next=it->second;\n'),block('    auto next=position;\n'),1).replace(block('    const auto before=next.saved;\n'),b'',1)
helper+=block('    return {std::move(next),std::move(response),std::move(path),displaced_steps};\n}\n')
old_method=block('RecoveredMovementService::CommittedMove RecoveredMovementService::move_committed(\n')
body=replace_one(body,old_method,helper+old_method)

# Guard every service mutation before it can observe/change active or storage.
names=['prepare','prepare_native','prepare_native_scene','bind','resume_after_battle',
 'begin_town_transfer','begin_indoor_transfer','begin_initial_indoor_transfer','begin_outdoor_return',
 'begin_island_transfer','begin_island_return','begin_transfer','begin_registered_door_transfer',
 'begin_registered_parent_transfer','finish_town_transfer','move_committed']
guards=[]
for name in names:
 marker=('RecoveredMovementService::'+name+'(').encode()
 matches=[p for p in range(len(body)) if body.startswith(marker,p)]
 assert len(matches)==1,(name,len(matches))
 brace=body.index(b'{',matches[0])
 newline=b'\r\n' if body[brace+1:brace+3]==b'\r\n' else b'\n'
 point=brace+1+len(newline)
 inserted=b'    reject_owned_movement_mutation();'+newline
 body=body[:point]+inserted+body[point:]
 guards.append({'method':name,'inserted_hex':inserted.hex()})

# noexcept cleanup must still remove, while noexcept publication cannot mutate
# the OLD active state during an opted operation.
noexcept_guard=block('    if(owned_movement_busy_){owned_movement_invalid_=true;return;}\n')
commit_marker=b'RecoveredMovementService::commit_owned_island_return('
brace=body.index(b'{',body.index(commit_marker))
newline=b'\r\n' if body[brace+1:brace+3]==b'\r\n' else b'\n'
point=brace+1+len(newline)
noexcept_guard=noexcept_guard.replace(b'\r\n',newline)
body=body[:point]+noexcept_guard+body[point:]
remove_old=b'void RecoveredMovementService::remove(std::uint64_t session) noexcept { active_.erase(session); }'
remove_new=b'void RecoveredMovementService::remove(std::uint64_t session) noexcept { if(owned_movement_busy_)owned_movement_invalid_=true;active_.erase(session); }'
body=replace_one(body,remove_old,remove_new)

# During opted reads copy the value BEFORE calling the repository; remove may
# erase the map node on a reentrant observer. Default read body remains intact.
safe_read_text='''    if(owned_movement_busy_) {
        const auto snapshot=[&]()->std::optional<Position> {
            const auto found=active_.find(session);
            if(found==active_.end())return std::nullopt;
            return found->second;
        }();
        if(owned_movement_invalid_ || !snapshot || !snapshot->ready || snapshot->transfer_pending ||
           snapshot->account!=account || snapshot->character!=character)return std::nullopt;
        const auto saved=characters_.load_position(account,character);
        const auto now=active_.find(session);
        if(owned_movement_invalid_ || now==active_.end() || now->second!=*snapshot || saved!=snapshot->saved)
            return std::nullopt;
        return RecoveredPosition{snapshot->area,snapshot->scene,
            static_cast<std::uint16_t>(snapshot->x),static_cast<std::uint16_t>(snapshot->y),
            snapshot->saved?snapshot->saved->revision:0};
    }
'''
brace=body.index(b'{',body.index(b'RecoveredMovementService::current_location('))
newline=b'\r\n' if body[brace+1:brace+3]==b'\r\n' else b'\n'
point=brace+1+len(newline)
safe_read=block(safe_read_text).replace(b'\r\n',newline)
body=body[:point]+safe_read+body[point:]

new_method=block('''RecoveredMovementService::CommittedMove RecoveredMovementService::move_committed_with_owned_material(
    Session& session,SqliteOwnedEquipmentTransaction& custody,
    std::span<const RecoveredMovement::Request> requests) {
    if(owned_movement_thread_!=std::this_thread::get_id())
        throw std::logic_error("Owned normal-entry movement requires its game owner");
    reject_owned_movement_mutation();
    owned_movement_busy_=true;owned_movement_invalid_=false;
    struct End {RecoveredMovementService& self;~End(){self.owned_movement_busy_=self.owned_movement_invalid_=false;}} end{*this};
    if(&custody.characters_repository()!=&characters_)
        throw std::invalid_argument("Owned movement requires the exact common character repository");
    const auto connection=session.shared_from_this();
    const auto initialization=session.normal_world_initialization();
    if(!initialization || !initialization->entry_written() ||
       !session.normal_world_initialization_current_on_game(*initialization))
        throw std::invalid_argument("Owned movement requires actual current normal initialization");
    const auto id=session.id(),account=session.account_id,character=session.character_id;
    const auto phase=session.state();const auto battle=session.battle_generation();
    if(!id || !account || !character || requests.empty() ||
       (phase!=SessionState::CharacterSelected && phase!=SessionState::InWorld))
        throw std::invalid_argument("Owned movement normal owner/batch rejected");
    const auto local=[&] {
        return owned_movement_busy_ && !owned_movement_invalid_ && connection.get()==&session &&
            session.normal_world_initialization_current_on_game(*initialization) && initialization->entry_written() &&
            !session.closing() && session.recovered_world_ready() && session.id()==id &&
            session.account_id==account && session.character_id==character &&
            session.state()==phase && session.battle_generation()==battle;
    };
    const auto old=[&] {
        const auto found=active_.find(id);
        if(found==active_.end() || !found->second.ready || found->second.transfer_pending ||
           found->second.account!=account || found->second.character!=character)
            throw std::invalid_argument("Unbound owned movement rejected");
        return found->second;
    }();
    // Pure in-memory owner check, including exact queue/geometry/saved state.
    // No iterator is retained across a repository or Session observation.
    const auto active_current=[&](const Position& wanted) {
        if(!local())return false;
        const auto found=active_.find(id);
        return found!=active_.end() && found->second==wanted && local();
    };
    if(!old.saved || !old.saved->revision || old.area!=old.saved->area || old.scene!=old.saved->scene ||
       old.x!=old.saved->x || old.y!=old.saved->y || !active_current(old))
        throw std::invalid_argument("Owned movement lacks exact positive saved active pose");
    const auto pose_current=[&](const Position& wanted) {
        return active_current(wanted) && current_location(id,account,character)==wanted.saved && active_current(wanted);
    };
    const auto entry=RecoveredWorldEntryView::read(initialization->entry_frame());
    if(!entry || !pose_current(old))throw std::invalid_argument("Owned movement entry/current pose rejected");
    const auto before=custody.observe_before(account,character);
    if(!before || !before->inventory || !before->equipment ||
       before->inventory->root.account_id!=account || before->inventory->root.id!=character ||
       !NativeEquipmentSnapshot::same_root(before->inventory->root,before->equipment->root) ||
       before->equipment->actor_handle!=entry->actor_handle || before->equipment->position!=*old.saved || !pose_current(old))
        throw std::invalid_argument("Owned movement requires both genuine current complete banks");
    // Reuse the entire legacy batch recipe. All allocation/ACK/path generation
    // completes while live queue and both persisted populations are still OLD.
    auto prepared=prepare_move_batch(old,requests);
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    if(old.saved->revision>=limit || !before->equipment->revision || before->equipment->revision>=limit)
        throw std::invalid_argument("Owned movement revision overflow");
    auto expected_equipment=*before->equipment;
    expected_equipment.position.x=static_cast<std::uint16_t>(prepared.next.x);
    expected_equipment.position.y=static_cast<std::uint16_t>(prepared.next.y);
    ++expected_equipment.position.revision;++expected_equipment.revision;
    constexpr std::string_view marker=";CUSTOM-0095:ordinary-move-preserves-material";
    if(expected_equipment.source_record.find(marker)==std::string::npos) {
        if(expected_equipment.source_record.size()>2048-marker.size())
            throw std::invalid_argument("Owned movement provenance exceeds bounded storage");
        expected_equipment.source_record.append(marker);
    }
    if(!pose_current(old))throw std::invalid_argument("Owned movement before pose became stale");
    // Only this pure OLD owner predicate runs inside the joint transaction.
    // No current_location, repository reader, callback, send or SQL reentry.
    const auto committed=custody.move_position_from_current(*before,entry->actor_handle,
        expected_equipment.position.x,expected_equipment.position.y,[&]{return active_current(old);});
    if(!committed)throw std::runtime_error("Owned movement authority rejected before commit");
    if(!active_current(old) || committed->inventory().snapshot()!=*before->inventory ||
       committed->equipment().snapshot()!=expected_equipment || !custody.committed_current(*committed) || !active_current(old))
        throw std::runtime_error("Owned movement committed but old local publication became stale");
    // Storage is now NEW. Publishing this trivially copied Position allocates
    // nothing; old current_location would reject until saved becomes NEW too.
    prepared.next.saved=committed->equipment().snapshot().position;
    {
        const auto found=active_.find(id);
        if(found==active_.end() || found->second!=old || !local())
            throw std::runtime_error("Owned movement committed but active incarnation was retired");
        found->second=prepared.next;
    }
    if(!pose_current(prepared.next) || !custody.committed_current(*committed) || !pose_current(prepared.next))
        throw std::runtime_error("Owned movement committed but ACK delivery became stale");
    return {std::move(prepared.response),old.saved,*prepared.next.saved,prepared.displaced_steps,std::move(prepared.path)};
}
''')
remove_signature=b'void RecoveredMovementService::remove(std::uint64_t session) noexcept'
body=replace_one(body,remove_signature,new_method+remove_signature)

# Inverse custody proves old public/default method contents survive exactly.
inverse=body.replace(includes,b'',1).replace(helper,b'',1).replace(new_method,b'',1).replace(safe_read,b'',1).replace(noexcept_guard,b'',1)
inverse=replace_one(inverse,remove_new,remove_old)
inverse=replace_one(inverse,default_call,batch)
for guard in guards:
 inserted=bytes.fromhex(guard['inserted_hex'])
 # Remove one insertion at the named original method boundary only.
 marker=('RecoveredMovementService::'+guard['method']+'(').encode()
 brace=inverse.index(b'{',inverse.index(marker))
 newline=b'\r\n' if inverse[brace+1:brace+3]==b'\r\n' else b'\n'
 point=brace+1+len(newline)
 assert inverse[point:point+len(inserted)]==inserted
 inverse=inverse[:point]+inverse[point+len(inserted):]
assert inverse==old[CPP]
inverse_h=h.replace(h_include,b'',1).replace(forward,b'',1).replace(api,b'',1).replace(position_equality,b'',1).replace(private_api,b'',1)
assert inverse_h==old[H]
for name,result in ((H,h),(CPP,body)):
 assert (ROOT/name).read_bytes()==old[name], 'Concurrent scoped source mutation'
 (ROOT/name).write_bytes(result)
 (OUT/('final-'+Path(name).name)).write_bytes(result)
(OUT/'original-batch-block.txt').write_bytes(batch)
manifest={'baseline_revision':BASE,'source_scope':[H,CPP],'target_execution':False,
 'public_api':'CommittedMove move_committed_with_owned_material(Session&,SqliteOwnedEquipmentTransaction&,span<Request>)',
 'old_cpp_inverse_equals_baseline':True,'old_header_inverse_equals_baseline':True,'guard_insertions':guards,
 'inverse_recipe':['remove added includes/API/private members/equality','remove shared batch/guard helper/new typed method',
  'remove opted safe current_location branch/noexcept island guard','restore original remove and original batch block',
  'remove exact method-entry guard insertions'],
 'sources':[{'path':name,'before_bytes':len(old[name]),'before_sha256':sha(old[name]),'after_bytes':len(result),'after_sha256':sha(result)} for name,result in ((H,h),(CPP,body))]}
(OUT/'implementation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(manifest))
