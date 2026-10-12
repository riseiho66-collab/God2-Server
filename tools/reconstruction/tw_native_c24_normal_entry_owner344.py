from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent
BASE = 'dd7524e842479f4ca534f1f0a5291d93c3412c34'
H = 'src/game/SharedTaiwanOwnedBagMoveSource.h'
CPP = 'src/game/SharedTaiwanOwnedBagMoveSource.cpp'
sha = lambda value: hashlib.sha256(value).hexdigest()
original = {}
for name in (H, CPP):
    original[name] = (ROOT / name).read_bytes()
    pinned = subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{BASE}:{name}'])
    # Git stores LF; the working source can use CRLF. Preserve its exact bytes.
    assert original[name].replace(b'\r\n', b'\n') == pinned.replace(b'\r\n', b'\n'), name
    (OUT / ('before-' + Path(name).name)).write_bytes(original[name])

def lines(text, body):
    return text.replace('\n', '\r\n' if b'\r\n' in body else '\n').encode()

header = original[H]
forward = lines('class RecoveredMovementService;\n', header)
header = header.replace(lines('namespace god2 {\n', header), lines('namespace god2 {\n', header) + forward, 1)
addition = '''    // CUSTOM-0094 full25 only: actual legacy world-records callback and
    // private normal-entry receipt, never a fabricated common ready lease.
    // Requires both genuine complete saved banks at the exact live durable
    // pose. No initialization, grant, stale-witness rebase or scalar promotion.
    // Actual movement/common sources must outlive this game-owned binding.
    static SharedTaiwanWorldRecordSource::InventoryMoveBinding create_for_normal_entry_with_item_material(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,RecoveredMovementService&);
'''
assert header.count(b'};') == 1
header = header.replace(b'};', lines(addition, header) + b'};', 1)

body = original[CPP]
include_anchor = b'#include "protocol/RecoveredWorldFrame.h"'
includes = lines('#include "handlers/RecoveredMovementService.h"\n#include "protocol/RecoveredWorldEntryView.h"\n', body)
assert body.count(include_anchor) == 1
body = body.replace(include_anchor, includes + include_anchor, 1)

# Extract the exact existing reply generation once; keep every operation/order.
start_marker = lines('        // Allocate and encode the complete native result before any storage write.\n', body)
end_marker = lines('        if(!local() || !transaction_->before_current(*before) || !local())return std::nullopt;\n', body)
start = body.index(start_marker)
end = body.index(end_marker, start)
reply_block = body[start:end]
reply_text = reply_block.decode().replace('\r\n', '\n')
reply_lines = reply_text.splitlines(True)
helper_text = 'Reply prepare_reply(const State& next,Request request,bool material_mode) {\n'
helper_text += ''.join(line[4:] for line in reply_lines).replace('material_mode_', 'material_mode').replace('next->', 'next.')
helper_text += '    return reply;\n}\n'
reply_helper = lines(helper_text, body)
body = body[:start] + lines('        auto reply=prepare_reply(*next,request,material_mode_);\n', body) + body[end:]
anchor = lines('class Owner final {\n', body)
assert body.count(anchor) == 1
body = body.replace(anchor, reply_helper + anchor, 1)

owner_text = '''// Concrete legacy owner. Receipt identity is the real normal-entry incarnation;
// it neither installs client item material nor supplies a common-world lease.
class NormalEntryOwner final {
public:
    NormalEntryOwner(std::shared_ptr<Transaction> transaction,RecoveredMovementService& movement)
        :transaction_(std::move(transaction)),movement_(movement) {}
    ~NormalEntryOwner(){if(thread_!=std::this_thread::get_id())std::terminate();}
    void owner() const {if(thread_!=std::this_thread::get_id())throw std::logic_error("TW normal-entry bag move game owner mismatch");}
    void invalidate(){owner();if(busy_)invalid_=true;}
    void release(Session& session){owner();if(active_==&session)invalidate();}
    std::optional<Reply> dispatch(Session& session,Request request) {
        owner();if(busy_){invalid_=true;throw std::logic_error("TW normal-entry bag move reentered");}
        busy_=true;invalid_=false;active_=&session;
        struct End {NormalEntryOwner& self;~End(){self.active_=nullptr;self.busy_=false;self.invalid_=false;}} end{*this};
        const auto connection=session.shared_from_this();
        // Getter is restricted to the actual synchronous world-records callback.
        const auto initialization=session.normal_world_initialization();
        if(!initialization || !initialization->entry_written() ||
           !session.normal_world_initialization_current_on_game(*initialization))return std::nullopt;
        const auto id=session.id(),account=session.account_id,character=session.character_id;
        const auto phase=session.state();const auto battle=session.battle_generation();
        if(!id || !account || !character ||
           (phase!=SessionState::CharacterSelected && phase!=SessionState::InWorld))return std::nullopt;
        // Pure identity/receipt checks only. Safe inside the joint issuer:
        // no movement/repository observer, callback, send, yield or SQL here.
        const auto local=[&] {
            return !invalid_ && connection.get()==&session &&
                session.normal_world_initialization_current_on_game(*initialization) && initialization->entry_written() &&
                !session.closing() && session.recovered_world_ready() && session.id()==id &&
                session.account_id==account && session.character_id==character &&
                session.state()==phase && session.battle_generation()==battle;
        };
        if(!local())return std::nullopt;
        const auto entry=RecoveredWorldEntryView::read(initialization->entry_frame());
        if(!entry || !local())return std::nullopt;
        const auto position=movement_.current_location(id,account,character);
        if(!position || !position->revision || !local())return std::nullopt;
        // This observer reads the actual saved baseline. Call only OUTSIDE the
        // joint issuer/transaction, whose own checks enforce the durable pose.
        const auto pose_current=[&] {
            return local() && movement_.current_location(id,account,character)==position && local();
        };
        const auto before=transaction_->observe_before(account,character);
        if(!before || !before->equipment || before->equipment->actor_handle!=entry->actor_handle ||
           before->equipment->position!=*position || !pose_current())return std::nullopt;
        // Full25 is mandatory on this path. Count-only41 cannot prove the
        // legacy client's previously retained18 bytes from a saved bank.
        const auto next=plan(*before,request,true);if(!next)return std::nullopt;
        auto reply=prepare_reply(*next,request,true);
        if(!pose_current() || !transaction_->before_current(*before) || !pose_current())return std::nullopt;
        const auto committed=transaction_->replace_from_issuer(*before,*next,
            [&](const Transaction::Before&,const State& proposed,Transaction::Check)->std::optional<State> {
                if(!local())return std::nullopt;
                const auto qualified=plan(*before,request,true);
                return qualified && *qualified==proposed?qualified:std::nullopt;
            });
        if(!committed)return std::nullopt;
        if(!pose_current() || committed->inventory().snapshot()!=next->inventory ||
           committed->equipment().snapshot()!=next->equipment || !transaction_->committed_current(*committed) ||
           !pose_current()) {
            invalid_=true;throw std::runtime_error("TW normal-entry bag move committed but delivery became stale");
        }
        return reply;
    }
private:
    const std::thread::id thread_=std::this_thread::get_id();
    std::shared_ptr<Transaction> transaction_;
    RecoveredMovementService& movement_;
    Session* active_=nullptr;
    bool busy_=false,invalid_=false;
};
'''
owner_block = lines(owner_text, body)
owner_end = lines('};\n}\nstatic SharedTaiwanWorldRecordSource::InventoryMoveBinding make_bag_binding(', body)
assert body.count(owner_end) == 1
body = body.replace(owner_end, lines('};\n', body) + owner_block + lines('}\nstatic SharedTaiwanWorldRecordSource::InventoryMoveBinding make_bag_binding(', body), 1)

factory_text = '''SharedTaiwanWorldRecordSource::InventoryMoveBinding SharedTaiwanOwnedBagMoveSource::create_for_normal_entry_with_item_material(
    std::shared_ptr<Transaction> transaction,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,RecoveredMovementService& movement) {
    if(!transaction || !transaction->owns_sources(accounts,characters) ||
       !movement.owns_repository(characters))throw std::invalid_argument("TW normal-entry bag move requires actual same common sources and movement");
    auto owner=std::make_shared<NormalEntryOwner>(std::move(transaction),movement);
    return {[owner](Session& session,const Request& request){return owner->dispatch(session,request);},
        [owner](Session& session){owner->release(session);},[owner]{owner->invalidate();}};
}
'''
factory_block = lines(factory_text, body)
assert body.endswith(lines('}\n}\n', body))
body = body[:-len(lines('}\n', body))] + factory_block + lines('}\n', body)

# Source-only inverse custody: no planner/common-owner/factory change except
# lifting the identical reply block into one shared pure function.
inverse = body.replace(includes, b'', 1).replace(reply_helper, b'', 1).replace(owner_block, b'', 1).replace(factory_block, b'', 1)
inverse = inverse.replace(lines('        auto reply=prepare_reply(*next,request,material_mode_);\n', body), reply_block, 1)
assert inverse == original[CPP]
inverse_h = header.replace(forward, b'', 1).replace(lines(addition, header), b'', 1)
assert inverse_h == original[H]

for name, result in ((H, header), (CPP, body)):
    assert (ROOT/name).read_bytes() == original[name], 'Concurrent scoped source modification'
    (ROOT/name).write_bytes(result)
    (OUT/('final-'+Path(name).name)).write_bytes(result)

manifest = {'baseline_revision':BASE, 'scope':[H,CPP], 'target_execution':False,
            'public_factory':'create_for_normal_entry_with_item_material(transaction,accounts,characters,movement)',
            'existing_cpp_inverse_equals_baseline':True,'existing_header_inverse_equals_baseline':True,
            'inverse_recipe':['remove two added includes','remove prepare_reply helper','remove NormalEntryOwner class',
                              'remove new public factory','replace common-owner prepare_reply call with retained original reply block',
                              'header remove movement forward declaration and new API/comment block'],
            'sources':[{'path':n,'before_bytes':len(original[n]),'before_sha256':sha(original[n]),
                        'after_bytes':len(v),'after_sha256':sha(v)} for n,v in ((H,header),(CPP,body))]}
(OUT/'implementation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
(OUT/'original-reply-block.txt').write_bytes(reply_block)
print(json.dumps(manifest))
