#include "game/OwnedBattleRowPreference.h"
#include "protocol/RecoveredBattleRowPreference.h"
#include "protocol/RecoveredWorldFrame.h"
#include <limits>
#include <stdexcept>
#include <algorithm>
namespace god2 {
OwnedBattleRowPreference::OwnedBattleRowPreference(SqliteNativeWorldEntrySnapshotRepository& repository,
        AccountRepository& accounts,RecoveredCharacterRepository& characters,std::size_t capacity)
    :repository_(repository),characters_(characters),capacity_(capacity) {
    if(!capacity || !repository.owns_sources(accounts,characters))
        throw std::invalid_argument("Row preference requires actual common sources and capacity");
}
OwnedBattleRowPreference::OwnedBattleRowPreference(SqliteNativeWorldEntrySnapshotRepository& repository,
        AccountRepository& accounts,RecoveredCharacterRepository& characters,SharedWorldPresence& presence,
        std::size_t capacity):OwnedBattleRowPreference(repository,accounts,characters,capacity) {
    if(!presence.owns_repository(characters))
        throw std::invalid_argument("Row preference requires its actual common presence repository");
    presence_=&presence;
}
bool OwnedBattleRowPreference::begin() noexcept {
    if(stopped_)return false;
    if(busy_){poisoned_=true;return false;}
    if(callback_==std::numeric_limits<std::uint64_t>::max()){stopped_=true;return false;}
    ++callback_;
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
    const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();
    const auto phase=session.state();
    const auto before=state_;
    const auto lease=presence_?presence_->ready_lease(session.id(),account,character):
        std::optional<SharedWorldPresence::Lease>{};
    if(!current() || state_!=before || session.closing() || !session.recovered_world_ready() ||
       !account || !character || session.account_id!=account || session.character_id!=character ||
       session.battle_generation()!=battle || session.state()!=phase ||
       (phase!=SessionState::CharacterSelected && phase!=SessionState::InWorld))return;
    if(presence_) {
        if(!lease || !presence_->retained_ready_current(*lease) ||
           !session.common_world_delivery_current(account,character,lease->generation))return;
    } else if(!initialization || !initialization->entry_written() ||
       !session.normal_world_initialization_current_on_game(*initialization))return;
    if(const auto at=state_->find(session.id());at!=state_->end() &&
       (at->second.session.lock()!=held || at->second.account!=session.account_id ||
        at->second.character!=session.character_id))return;
    if(const auto at=state_->find(session.id());at!=state_->end()) {
        const auto& previous=at->second;
        if(previous.unsealed || (previous.common_response &&
           previous.common_response->status()!=Session::WorldResponseWriteStatus::Written) ||
           (previous.response && previous.response->status()!=Session::NormalWorldResponseStatus::Queued))return;
    }
    auto next=std::make_shared<State>(*state_);
    for(auto at=next->begin();at!=next->end();) {
        if(at->second.session.expired())at=next->erase(at);else ++at;
    }
    if(!next->contains(session.id()) && next->size()>=capacity_)return;
    next->insert_or_assign(session.id(),Entry{held,account,character,presence_?std::nullopt:initialization,
        lease,battle,callback_,false,true,{},{},false,{}});
    state_=std::move(next);
}
bool OwnedBattleRowPreference::synchronize(Session& session,std::optional<std::uint8_t> supplied,
        std::vector<std::uint8_t>& wire) {
    if(!current() || (supplied && *supplied>1))return false;
    // An inner original return may already own the one complete wire capture.
    // Never append to its bytes or commit a choice which cannot be answered.
    // Replay stays uncached and waits for a genuine uncaptured idle callback.
    if(presence_ && session.current_world_response_capture_on_game())return !supplied;
    const auto held=session.shared_from_this();
    const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();
    const auto phase=session.state();
    const auto before=state_;
    const auto initialization=session.normal_world_initialization();
    if(!presence_ && (!initialization || !initialization->entry_written() ||
       !session.normal_world_initialization_current_on_game(*initialization)))return !supplied;
    const auto lease=presence_?presence_->ready_lease(session.id(),account,character):
        std::optional<SharedWorldPresence::Lease>{};
    if(presence_ && !lease) {
        // No actual ready common lease: absence cannot grant a B4 save, but
        // ordinary input must retain its original independent callback.
        return current() && state_==before && session.account_id==account && session.character_id==character &&
            session.battle_generation()==battle && session.state()==phase && !supplied;
    }
    const auto response=presence_?std::optional<Session::NormalWorldResponseAttempt>{}:
        session.capture_normal_world_response(*initialization);
    if(!presence_ && !response)return !supplied;
    const auto pure_current=[&] {
        return current() && state_==before && !session.closing() && session.recovered_world_ready() &&
            account && character && session.account_id==account && session.character_id==character &&
            session.battle_generation()==battle && session.state()==phase &&
            (phase==SessionState::CharacterSelected || phase==SessionState::InWorld) &&
            (presence_ ? lease && presence_->retained_ready_current(*lease) &&
                session.common_world_delivery_current(account,character,lease->generation) :
                initialization->entry_written() && session.normal_world_initialization_current_on_game(*initialization) &&
                session.normal_world_response_callback_current(*response));
    };
    if(!pure_current())return false;
    const auto at=before->find(session.id());
    if(at!=before->end()) {
        const auto& previous=at->second;
        if(previous.session.lock()!=held || previous.account!=account || previous.character!=character)return false;
        if(previous.unsealed && previous.callback!=callback_)return false;
        if(previous.common_response && previous.common_response->status()!=Session::WorldResponseWriteStatus::Written)
            return false; // Failed or still pending is never successful replay.
        if(previous.response) {
            const auto status=previous.response->status();
            if(status==Session::NormalWorldResponseStatus::Failed)return false;
            if(status==Session::NormalWorldResponseStatus::Pending &&
               (!(*previous.response==*response) || !session.normal_world_response_callback_current(*previous.response)))return false;
        }
        const bool same_entry=presence_ ? previous.lease==lease : previous.initialization &&
            previous.initialization->same_initialization(*initialization);
        if(!supplied && !previous.pending && previous.battle==battle && same_entry)return true;
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
    // Preserve unsealed output across ordered B4s in the same real callback.
    const bool already_unsealed=at!=before->end() && at->second.unsealed && at->second.callback==callback_;
    next_state->insert_or_assign(session.id(),Entry{held,account,character,presence_?std::nullopt:initialization,
        lease,battle,callback_,false,false,row?response:std::optional<Session::NormalWorldResponseAttempt>{},
        {},presence_ && (row.has_value() || already_unsealed),{}});
    if(presence_ && already_unsealed)next_state->at(session.id()).common_components=at->second.common_components;
    if(!row) {
        // Absence is cached for this INIT only. It is not a saved initial row.
        if(!pure_current())return false;
        state_=std::move(next_state);return true;
    }
    const auto logical=RecoveredBattleRowPreference::projection(*row);
    if(!logical)return false;
    const auto framed=RecoveredWorldFrame::encode(*logical);
    auto merged=wire;merged.insert(merged.end(),framed.begin(),framed.end());
    if(presence_) {
        auto& staged=next_state->at(session.id());
        // Same bounded component ceiling as actual normal response custody.
        if(staged.common_components.size()>=8192)return false;
        staged.common_components.push_back({wire.size(),framed});
    }
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
    if(!presence_)session.expect_normal_world_response(*response,framed);
    if(!pure_current())return false;
    state_=std::move(next_state);
    wire.swap(merged);
    return true;
}
bool OwnedBattleRowPreference::seal_common_response(Session& session,std::span<const std::uint8_t> final_wire,
        std::optional<Session::WorldResponseWrite> captured) {
    if(!current())return false;
    if(!presence_)return true;
    const auto before=state_;
    const auto at=before->find(session.id());
    if(at==before->end() || !at->second.unsealed)return true;
    const auto entry=at->second;
    const auto pure_current=[&] {
        return current() && state_==before && entry.callback==callback_ && entry.session.lock().get()==&session &&
            !session.closing() && session.recovered_world_ready() && session.account_id==entry.account &&
            session.character_id==entry.character && session.battle_generation()==entry.battle &&
            (session.state()==SessionState::CharacterSelected || session.state()==SessionState::InWorld) &&
            entry.lease && presence_->retained_ready_current(*entry.lease) &&
            session.common_world_delivery_current(entry.account,entry.character,entry.lease->generation);
    };
    if(!pure_current() || final_wire.empty())return false;
    // Exact append-site custody, not a byte search: an outer appender cannot
    // drop, replace, move or truncate an E8 staged for a saved explicit choice.
    for(const auto& component:entry.common_components) {
        if(component.offset>final_wire.size() || component.wire.size()>final_wire.size()-component.offset ||
           !std::equal(component.wire.begin(),component.wire.end(),final_wire.begin()+component.offset))return false;
    }
    auto next=std::make_shared<State>(*before); // Allocate before capturing or holding actual transport input.
    if(!captured)captured=session.observe_world_response(final_wire);
    if(!pure_current() || captured->status()!=Session::WorldResponseWriteStatus::Pending ||
       !session.world_response_write_current(*captured) || captured->wire().size()!=final_wire.size() ||
       !std::equal(final_wire.begin(),final_wire.end(),captured->wire().begin()))return false;
    // This exact private capture check also refuses another callback's token.
    session.hold_world_input_until_response_written(*captured);
    if(!pure_current())return false;
    auto& saved=next->at(session.id());saved.common_response=std::move(captured);saved.unsealed=false;
    saved.common_components.clear();
    state_=std::move(next);return true;
}
}
