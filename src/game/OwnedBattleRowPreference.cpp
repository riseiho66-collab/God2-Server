#include "game/OwnedBattleRowPreference.h"
#include "protocol/RecoveredBattleRowPreference.h"
#include "protocol/RecoveredWorldFrame.h"
#include <limits>
#include <stdexcept>
namespace god2 {
OwnedBattleRowPreference::OwnedBattleRowPreference(SqliteNativeWorldEntrySnapshotRepository& repository,
        AccountRepository& accounts,RecoveredCharacterRepository& characters,std::size_t capacity)
    :repository_(repository),characters_(characters),capacity_(capacity) {
    if(!capacity || !repository.owns_sources(accounts,characters))
        throw std::invalid_argument("Row preference requires actual common sources and capacity");
}
bool OwnedBattleRowPreference::begin() noexcept {
    if(stopped_)return false;
    if(busy_){poisoned_=true;return false;}
    busy_=true;poisoned_=false;return true;
}
void OwnedBattleRowPreference::ready(const Session& session) noexcept {
    // Actual ready runs BEFORE private INIT publication. Mark only through
    // changed INIT comparison on the next callback. No invented receipt here.
    if(busy_){poisoned_=true;return;}
    const auto at=state_->find(session.id());
    if(at==state_->end() || at->second.session.lock().get()!=&session)return;
    try {auto next=std::make_shared<State>(*state_);next->at(session.id()).pending=true;state_=std::move(next);}
    catch(...) { /* Changed actual INIT still forces replay; no fabricated receipt. */ }
}
void OwnedBattleRowPreference::disconnect(const Session& session) noexcept {
    if(busy_)poisoned_=true;
    // Defer erase while a callback retains a state witness. Exact incarnation
    // cleanup is retried at qualified synchronization; no iterator survives a callback.
    if(busy_)return;
    const auto at=state_->find(session.id());
    if(at==state_->end() || at->second.session.lock().get()!=&session)return;
    try {auto next=std::make_shared<State>(*state_);next->erase(session.id());state_=std::move(next);}
    catch(...) { /* Weak dead entries are swept before the next admission. */ }
}
void OwnedBattleRowPreference::defer_unavailable_replay(Session& session) {
    if(!current())return;
    const auto held=session.shared_from_this();
    const auto initialization=session.normal_world_initialization();
    if(!initialization || !initialization->entry_written() ||
       !session.normal_world_initialization_current_on_game(*initialization))return;
    if(const auto at=state_->find(session.id());at!=state_->end() &&
       (at->second.session.lock()!=held || at->second.account!=session.account_id ||
        at->second.character!=session.character_id))return;
    auto next=std::make_shared<State>(*state_);
    for(auto at=next->begin();at!=next->end();) {
        if(at->second.session.expired())at=next->erase(at);else ++at;
    }
    if(!next->contains(session.id()) && next->size()>=capacity_)return;
    next->insert_or_assign(session.id(),Entry{held,session.account_id,session.character_id,*initialization,false,true,{}});
    state_=std::move(next);
}
bool OwnedBattleRowPreference::synchronize(Session& session,std::optional<std::uint8_t> supplied,
        std::vector<std::uint8_t>& wire) {
    if(!current() || (supplied && *supplied>1))return false;
    const auto held=session.shared_from_this();
    const auto initialization=session.normal_world_initialization();
    if(!initialization || !initialization->entry_written() ||
       !session.normal_world_initialization_current_on_game(*initialization))return !supplied;
    const auto response=session.capture_normal_world_response(*initialization);
    if(!response)return !supplied;
    const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();
    const auto phase=session.state();
    const auto before=state_;
    const auto pure_current=[&] {
        return current() && state_==before && !session.closing() && session.recovered_world_ready() &&
            account && character && session.account_id==account && session.character_id==character &&
            session.battle_generation()==battle && session.state()==phase &&
            (phase==SessionState::CharacterSelected || phase==SessionState::InWorld) &&
            initialization->entry_written() && session.normal_world_initialization_current_on_game(*initialization) &&
            session.normal_world_response_callback_current(*response);
    };
    if(!pure_current())return false;
    const auto at=before->find(session.id());
    if(at!=before->end()) {
        const auto& previous=at->second;
        if(previous.session.lock()!=held || previous.account!=account || previous.character!=character)return false;
        if(previous.response) {
            const auto status=previous.response->status();
            if(status==Session::NormalWorldResponseStatus::Failed)return false;
            if(status==Session::NormalWorldResponseStatus::Pending &&
               (!(*previous.response==*response) || !session.normal_world_response_callback_current(*previous.response)))return false;
        }
        if(!supplied && !previous.pending && previous.initialization.same_initialization(*initialization))return true;
    }
    // Own all key inputs BEFORE SQL observers; historical root/position are
    // never borrowed as the present Session's authority.
    auto expected=repository_.load(account,character,client_pin,record_kind);
    if(!pure_current())return false;
    if(expected && (expected->source_sha256!=client_pin || expected->source_record!=source_record ||
       expected->record.size()!=2 || expected->record[0]!=0xe8 || expected->record[1]>1))return false;
    std::optional<std::uint8_t> row=supplied;
    if(!row && expected)row=expected->record[1];
    auto next_state=std::make_shared<State>(*before);
    for(auto entry=next_state->begin();entry!=next_state->end();) {
        if(entry->second.session.expired())entry=next_state->erase(entry);else ++entry;
    }
    if(!next_state->contains(session.id()) && next_state->size()>=capacity_)return false;
    next_state->insert_or_assign(session.id(),Entry{held,account,character,*initialization,false,false,
        row?response:std::optional<Session::NormalWorldResponseAttempt>{}});
    if(!row) {
        // Absence is cached for this INIT only. It is not a saved initial row.
        if(!pure_current())return false;
        state_=std::move(next_state);return true;
    }
    const auto logical=RecoveredBattleRowPreference::projection(*row);
    if(!logical)return false;
    const auto framed=RecoveredWorldFrame::encode(*logical);
    auto merged=wire;merged.insert(merged.end(),framed.begin(),framed.end());
    if(supplied && (!expected || expected->record[1]!=*row)) {
        auto roots=characters_.list_for_account(account);
        if(!pure_current())return false;
        std::optional<RecoveredCharacter> root;
        for(const auto& candidate:roots)if(candidate.id==character && candidate.account_id==account) {
            if(root)return false;root=candidate;
        }
        const auto position=characters_.load_position(account,character);
        if(!pure_current() || !root || !position)return false;
        const auto revision=expected?expected->revision:0;
        if(revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))return false;
        NativeWorldEntrySnapshot next{*root,*position,client_pin,record_kind,client_pin,source_record,
            std::vector<std::uint8_t>(logical->begin(),logical->end()),revision+1};
        const auto saved=repository_.replace_from_issuer(expected,next,
            [&](const auto& prior,const auto& staged,auto) {
                // Actual user bytes/full owner/root/position frozen above;
                // repository validates complete DB readset at every stage.
                return pure_current() && prior==expected && staged==next;
            },pure_current);
        // COMMIT may already be durable when a completion observer retires us.
        // Suppress stale E8. Never retry/claim rollback or publish old state.
        if(!saved || !pure_current())return false;
    }
    if(!pure_current())return false;
    session.expect_normal_world_response(*response,framed);
    if(!pure_current())return false;
    state_=std::move(next_state);
    wire.swap(merged);
    return true;
}
}
