from pathlib import Path
import hashlib,json,subprocess

ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round346-owned-mutation-receipt-implementation')
BASE='f5ab47fa8e55ff8c7438284caa23f61c26ca0efe'
BAGH='src/game/SharedTaiwanOwnedBagMoveSource.h'
BAGCPP='src/game/SharedTaiwanOwnedBagMoveSource.cpp'
MOVEH='src/handlers/RecoveredMovementService.h'
MOVECPP='src/handlers/RecoveredMovementService.cpp'
names=[BAGH,BAGCPP,MOVEH,MOVECPP]
sha=lambda data:hashlib.sha256(data).hexdigest()
norm=lambda data:data.replace(b'\r\n',b'\n')
def crlf(text):return text.replace('\n','\r\n').encode()
def lf(text):return text.encode()
def replace_one(data,old,new):
    assert data.count(old)==1, (old[:140], data.count(old))
    return data.replace(old,new,1)
old={name:(ROOT/name).read_bytes() for name in names}
for name in names:
    assert norm(old[name])==norm(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
    (OUT/('before-'+Path(name).name)).write_bytes(old[name])
changes=[]
def swap(name,before,after):
    changes.append({'path':name,'before_hex':before.hex(),'after_hex':after.hex()})
    final[name]=replace_one(final[name],before,after)
final=dict(old)

bag_api=lf('''    // Passive transport of this actual normal-entry C24 mutation receipt and
    // its ORIGINAL already-framed response. No acquisition, initial replay,
    // native timing/final-cache authority or caller-minted source is implied.
    class MutationResult final {
    public:
        MutationResult(const MutationResult&)=delete;
        MutationResult& operator=(const MutationResult&)=delete;
        MutationResult(MutationResult&&) noexcept=default;
        MutationResult& operator=(MutationResult&&) noexcept=default;
        const SqliteOwnedEquipmentTransaction::Committed& committed() const noexcept{return committed_;}
        const std::vector<std::uint8_t>& wire() const noexcept{return wire_;}
        bool native_no_reply() const noexcept{return no_reply_;}
        std::vector<std::uint8_t> take_wire() && noexcept{return std::move(wire_);}
    private:
        friend class SharedTaiwanOwnedBagMoveSource;
        MutationResult(bool no_reply,std::vector<std::uint8_t> wire,
            SqliteOwnedEquipmentTransaction::Committed committed) noexcept
            :no_reply_(no_reply),wire_(std::move(wire)),committed_(std::move(committed)) {}
        bool no_reply_;
        std::vector<std::uint8_t> wire_;
        SqliteOwnedEquipmentTransaction::Committed committed_;
    };
    struct MutationBinding {
        std::function<std::optional<MutationResult>(Session&,const RecoveredInventoryMoveRequest::Request&)> dispatch;
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
    };
    // Same concrete CUSTOM-0094 operation/owner; only the return carrier differs.
    // Output storage is allocated before its one joint COMMIT. Receipt/wire
    // move afterwards; no re-observation, decoding, repacking or mint callback.
    static MutationBinding create_for_normal_entry_with_item_material_and_receipt(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,RecoveredMovementService&);
''')
swap(BAGH,b'};\n}\n',bag_api+b'};\n}\n')

normal_start=final[BAGCPP].index(b'class NormalEntryOwner final {')
normal_end=final[BAGCPP].index(b'\n};',normal_start)+len(b'\n};')
normal_original=final[BAGCPP][normal_start:normal_end]
normal=normal_original
dispatch_old=lf('''    std::optional<Reply> dispatch(Session& session,Request request) {
''')
dispatch_new=lf('''    struct Outcome {
        Reply reply;
        std::vector<std::uint8_t> wire;
        Transaction::Committed committed;
    };
    std::optional<Reply> dispatch(Session& session,Request request) {
        auto result=dispatch_with_receipt(session,request,false);
        if(!result)return std::nullopt;
        return std::move(result->reply);
    }
    std::optional<Outcome> dispatch_with_receipt(Session& session,Request request,bool retain_wire) {
''')
normal=replace_one(normal,dispatch_old,dispatch_new)
reply_old=lf('''        auto reply=prepare_reply(*next,request,true);
''')
reply_new=reply_old+lf('''        // Generic Reply exposes a const wire view. Only this typed opt-in
        // copies those exact bytes, BEFORE COMMIT; the old adapter copies none.
        std::vector<std::uint8_t> response_wire;
        if(retain_wire)response_wire=reply.bytes();
''')
normal=replace_one(normal,reply_old,reply_new)
normal=replace_one(normal,lf('''        return reply;
'''),lf('''        return Outcome{std::move(reply),std::move(response_wire),*committed};
'''))
swap(BAGCPP,normal_original,normal)

new_factory=lf('''SharedTaiwanOwnedBagMoveSource::MutationBinding SharedTaiwanOwnedBagMoveSource::create_for_normal_entry_with_item_material_and_receipt(
    std::shared_ptr<Transaction> transaction,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,RecoveredMovementService& movement) {
    if(!transaction || !transaction->owns_sources(accounts,characters) ||
       !movement.owns_repository(characters))throw std::invalid_argument("TW normal-entry bag move requires actual same common sources and movement");
    auto owner=std::make_shared<NormalEntryOwner>(std::move(transaction),movement);
    return {[owner](Session& session,const Request& request)->std::optional<MutationResult> {
            auto result=owner->dispatch_with_receipt(session,request,true);
            if(!result)return std::nullopt;
            // The lexical source factory alone can construct this carrier.
            // This is the actual private token returned by the SAME mutation.
            return MutationResult(result->reply.native_no_reply(),std::move(result->wire),result->committed);
        },[owner](Session& session){owner->release(session);},[owner]{owner->invalidate();}};
}
''')
assert final[BAGCPP].endswith(b'}\n')
factory_end=lf('''    auto owner=std::make_shared<NormalEntryOwner>(std::move(transaction),movement);
    return {[owner](Session& session,const Request& request){return owner->dispatch(session,request);},
        [owner](Session& session){owner->release(session);},[owner]{owner->invalidate();}};
}
}
''')
swap(BAGCPP,factory_end,factory_end[:-2]+new_factory+b'}\n')

move_include=b'#include "db/SqliteOwnedEquipmentTransaction.h"\r\n'
swap(MOVEH,b'#pragma once\r\n',b'#pragma once\r\n'+move_include)
move_carrier=crlf('''    // Actual CUSTOM-0095 mutation receipt plus the ORIGINAL batch ACKs/path.
    // Passive proof transport, not native5D issuer or socket/client acceptance.
    class OwnedCommittedMove final {
    public:
        OwnedCommittedMove(const OwnedCommittedMove&)=delete;
        OwnedCommittedMove& operator=(const OwnedCommittedMove&)=delete;
        OwnedCommittedMove(OwnedCommittedMove&&) noexcept=default;
        OwnedCommittedMove& operator=(OwnedCommittedMove&&) noexcept=default;
        const SqliteOwnedEquipmentTransaction::Committed& committed() const noexcept{return committed_;}
        const CommittedMove& movement() const noexcept{return movement_;}
        CommittedMove take_movement() && noexcept{return std::move(movement_);}
    private:
        friend class RecoveredMovementService;
        OwnedCommittedMove(CommittedMove movement,SqliteOwnedEquipmentTransaction::Committed committed) noexcept
            :movement_(std::move(movement)),committed_(std::move(committed)) {}
        CommittedMove movement_;
        SqliteOwnedEquipmentTransaction::Committed committed_;
    };
''')
swap(MOVEH,b'    struct MovePreview {\r\n',move_carrier+b'    struct MovePreview {\r\n')
api_old=crlf('''    CommittedMove move_committed_with_owned_material(Session&,SqliteOwnedEquipmentTransaction&,
        std::span<const RecoveredMovement::Request> requests);
''')
api_new=api_old+crlf('''    // Same actual owner, batch recipe, one joint COMMIT and publication checks;
    // return its private durable receipt without a later observe_committed read.
    OwnedCommittedMove move_committed_with_owned_material_and_receipt(Session&,SqliteOwnedEquipmentTransaction&,
        std::span<const RecoveredMovement::Request> requests);
''')
swap(MOVEH,api_old,api_new)

method_old=crlf('''RecoveredMovementService::CommittedMove RecoveredMovementService::move_committed_with_owned_material(
    Session& session,SqliteOwnedEquipmentTransaction& custody,
    std::span<const RecoveredMovement::Request> requests) {
''')
method_new=method_old+crlf('''    return std::move(move_committed_with_owned_material_and_receipt(session,custody,requests)).take_movement();
}
RecoveredMovementService::OwnedCommittedMove RecoveredMovementService::move_committed_with_owned_material_and_receipt(
    Session& session,SqliteOwnedEquipmentTransaction& custody,
    std::span<const RecoveredMovement::Request> requests) {
''')
swap(MOVECPP,method_old,method_new)
return_old=crlf('''    return {std::move(prepared.response),old.saved,*prepared.next.saved,prepared.displaced_steps,std::move(prepared.path)};
''')
return_new=crlf('''    return OwnedCommittedMove({std::move(prepared.response),old.saved,*prepared.next.saved,
        prepared.displaced_steps,std::move(prepared.path)},*committed);
''')
swap(MOVECPP,return_old,return_new)

# Inverse textual source custody, without target execution or C++ compilation.
inverse=dict(final)
for row in reversed(changes):
    inverse[row['path']]=replace_one(inverse[row['path']],bytes.fromhex(row['after_hex']),bytes.fromhex(row['before_hex']))
for name in names:
    assert inverse[name]==old[name], name
    assert (ROOT/name).read_bytes()==old[name], 'Concurrent scoped mutation '+name
for name in names:
    (ROOT/name).write_bytes(final[name])
    (OUT/('final-'+Path(name).name)).write_bytes(final[name])
manifest={'baseline_revision':BASE,'scoped_source_paths':names,'target_execution':0,
          'inverse_equals_original_raw_bytes':True,'inverse_replacements':changes,
          'sources':[{'path':name,'before_bytes':len(old[name]),'before_sha256':sha(old[name]),
                      'after_bytes':len(final[name]),'after_sha256':sha(final[name])} for name in names]}
(OUT/'implementation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'sources':manifest['sources'],'inverse_equals_original_raw_bytes':True}))
