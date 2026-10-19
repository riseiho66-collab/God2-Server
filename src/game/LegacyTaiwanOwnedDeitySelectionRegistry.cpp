#include "game/LegacyTaiwanOwnedDeitySelectionRegistry.h"
#include <map>
#include <stdexcept>
#include <thread>

namespace god2 {
struct LegacyTaiwanOwnedDeitySelectionRegistry::Data {
    const std::weak_ptr<Impl> origin;
    const std::weak_ptr<Session> session;
    const Session::NormalWorldInitialization initialization;
    const Session::WorldCallbackOutput output;
    const std::uint64_t id,account,character,battle;
    const SessionState phase;
    const std::vector<Session::WorldCallbackOutput::SelectionKey> keys;
    std::vector<RecoveredOwnedCompanions::SelectionPublication> results;
    std::vector<Session::WorldCallbackSelectionEmission> emissions;
    bool invalid=false,finished=false,eligible=false;
    Data(const std::shared_ptr<Impl>& owner,Session& peer,
        const Session::NormalWorldInitialization& init,const Session::WorldCallbackOutput& receipt)
        :origin(owner),session(peer.weak_from_this()),initialization(init),output(receipt),id(peer.id()),
         account(peer.account_id),character(peer.character_id),battle(peer.battle_generation()),phase(peer.state()),
         keys(receipt.selection_keys().begin(),receipt.selection_keys().end()) {
        results.reserve(keys.size());emissions.reserve(keys.size()); // Before any actual helper mutation.
    }
};
struct LegacyTaiwanOwnedDeitySelectionRegistry::Impl {
    const std::thread::id thread=std::this_thread::get_id();
    const std::size_t capacity;
    RecoveredOwnedCompanions& companions;
    std::map<std::uint64_t,std::shared_ptr<Data>> slots;
    std::shared_ptr<Data> active;
    bool reading=false,reentered=false;
    Impl(std::size_t count,RecoveredOwnedCompanions& helper):capacity(count),companions(helper){}
    struct Read {
        Impl& owner;
        explicit Read(Impl& value):owner(value) {
            if(owner.thread!=std::this_thread::get_id())throw std::logic_error("Legacy selection game owner mismatch");
            if(owner.reading){
                owner.reentered=true;if(owner.active)owner.active->invalid=true;
                throw std::logic_error("Legacy selection source reentered");
            }
            owner.reading=true;owner.reentered=false;
        }
        ~Read(){owner.reading=false;}
    };
    bool local(Session& peer,const std::shared_ptr<Data>& data) const {
        if(!data || data->origin.lock().get()!=this || data->invalid || reentered ||
           data->session.lock().get()!=&peer || peer.id()!=data->id || peer.account_id!=data->account ||
           peer.character_id!=data->character || peer.battle_generation()!=data->battle ||
           peer.state()!=data->phase || (data->phase!=SessionState::CharacterSelected&&data->phase!=SessionState::InWorld) ||
           peer.closing() || !peer.recovered_world_ready() || !data->initialization.entry_written() ||
           !peer.normal_world_initialization_current_on_game(data->initialization) ||
           !peer.world_callback_output_current_on_game(data->output))return false;
        const auto at=slots.find(data->id);
        return at!=slots.end() && at->second==data;
    }
    bool collecting(Session& peer,const std::shared_ptr<Data>& data) const {
        return active==data && data && !data->finished && !data->output.sealed() &&
            data->output.status()==Session::WorldCallbackOutputStatus::Pending && local(peer,data);
    }
    bool written(Session& peer,const std::shared_ptr<Data>& data) const {
        if(!local(peer,data) || !data->finished || !data->eligible ||
           data->output.status()!=Session::WorldCallbackOutputStatus::Written ||
           !data->output.sealed() || !data->output.callback_accepted() ||
           data->results.size()!=data->keys.size() || data->emissions.size()!=data->results.size())return false;
        std::optional<Session::WorldCallbackEmissionLocation> previous;
        for(std::size_t i=0;i<data->results.size();++i) {
            const auto& emission=data->emissions[i];
            if(emission.selection_ordinal()!=i || emission.expected_wire()!=data->results[i].wire() ||
               !peer.callback_output_emission_written(data->output,emission))return false;
            const auto location=peer.callback_output_emission_location(data->output,emission);
            if(!location || location->logical_record_offset!=0 || location->logical_record_size!=29)return false;
            if(previous && (location->component_ordinal<previous->component_ordinal ||
               (location->component_ordinal==previous->component_ordinal &&
                location->frame_wire_offset<=previous->frame_wire_offset)))return false;
            previous=location;
        }
        return local(peer,data);
    }
};
LegacyTaiwanOwnedDeitySelectionRegistry::LegacyTaiwanOwnedDeitySelectionRegistry(
        std::size_t capacity,RecoveredOwnedCompanions& helper) {
    if(!capacity)throw std::invalid_argument("Legacy selection requires actual Session capacity");
    state_=std::make_shared<Impl>(capacity,helper);
}
LegacyTaiwanOwnedDeitySelectionRegistry::Callback LegacyTaiwanOwnedDeitySelectionRegistry::begin(
        Session& peer,const Session::NormalWorldInitialization& initialization,const Session::WorldCallbackOutput& output) {
    const auto state=state_;Impl::Read read(*state);
    if(state->active){state->active->invalid=true;throw std::logic_error("Legacy selection callback reentered");}
    if(output.selection_keys().empty() || output.sealed() || output.status()!=Session::WorldCallbackOutputStatus::Pending ||
       !peer.normal_world_initialization_current(initialization) || !initialization.entry_written() ||
       !peer.world_callback_output_current_on_game(output))throw std::runtime_error("Legacy selection lacks actual callback custody");
    const auto prior=state->slots.find(peer.id());
    if(prior!=state->slots.end()) {
        if(prior->second->session.lock().get()!=&peer)throw std::logic_error("Legacy selection Session incarnation conflict");
        const auto status=prior->second->output.status();
        if(status!=Session::WorldCallbackOutputStatus::Written && status!=Session::WorldCallbackOutputStatus::NoOutput)
            throw std::runtime_error("Legacy selection crossed an incomplete original callback");
    }else if(state->slots.size()>=state->capacity)throw std::runtime_error("Legacy selection capacity exhausted");
    auto data=std::make_shared<Data>(state,peer,initialization,output);
    // Replace the old local source before any current callback can perform SQL.
    // No old source becomes Current again through equal values/idempotence.
    if(prior!=state->slots.end())prior->second->invalid=true;
    state->slots.insert_or_assign(peer.id(),data);state->active=data;
    if(!state->collecting(peer,data)){data->invalid=true;state->active.reset();throw std::runtime_error("Legacy selection admission retired");}
    return Callback(std::move(data));
}
std::optional<LegacyWorldReply> LegacyTaiwanOwnedDeitySelectionRegistry::select(
        Session& peer,const RecoveredDeitySelection::Request& request) {
    const auto state=state_;Impl::Read read(*state);const auto data=state->active;
    if(!state->collecting(peer,data))throw std::runtime_error("Legacy selection lacks its original active callback");
    const auto input=peer.claim_next_callback_selection(data->output,request);
    if(!input || input->selection_ordinal()!=data->results.size() || input->selection_ordinal()>=data->keys.size() ||
       input->record_index()!=data->keys[input->selection_ordinal()].record_index ||
       input->request().key!=data->keys[input->selection_ordinal()].key) {
        data->invalid=true;throw std::runtime_error("Legacy selection input occurrence changed");
    }
    // True helper invocation only; no API accepts a caller-provided publication.
    auto result=state->companions.select_deity_with_source(data->account,data->character,request);
    if(!result)return std::nullopt; // Original authority refusal; no fabricated S31.
    if(!state->collecting(peer,data) || !peer.callback_output_selection_current(data->output,*input)) {
        data->invalid=true;throw std::runtime_error("Committed legacy selection lost its owner");
    }
    const auto& publication=result->publication();const auto& committed=publication.committed();
    if(committed.account()!=data->account || committed.character()!=data->character ||
       committed.after().key!=request.key || result->wire()!=publication.wire() ||
       (!data->results.empty() && committed.before()!=std::optional{data->results.back().committed().after()})) {
        data->invalid=true;throw std::runtime_error("Legacy selection private commit chain changed");
    }
    const auto emission=peer.mint_callback_selection_emission(data->output,*input,publication.wire());
    if(!emission){data->invalid=true;throw std::runtime_error("Committed legacy selection could not retain its original emission");}
    data->results.push_back(publication);data->emissions.push_back(*emission);
    return LegacyWorldReply(*emission); // Private producer constructor, exact complete original frame.
}
void LegacyTaiwanOwnedDeitySelectionRegistry::finish(Session& peer,const Callback& callback,bool accepted) {
    const auto state=state_;Impl::Read read(*state);const auto data=callback.data_;
    if(!state->collecting(peer,data)){if(data)data->invalid=true;throw std::runtime_error("Legacy selection callback finish retired");}
    if(!accepted)data->invalid=true;
    else if(!data->results.empty() && (data->results.size()!=data->keys.size() || data->emissions.size()!=data->results.size())) {
        data->invalid=true;throw std::runtime_error("Legacy selection has an incomplete durable prefix");
    }
    data->eligible=accepted&&!data->results.empty()&&!data->invalid;
    data->finished=true;state->active.reset(); // Session still owns actual final-return acceptance and sealing.
}
void LegacyTaiwanOwnedDeitySelectionRegistry::abandon(const Callback& callback) noexcept {
    const auto state=state_;const auto data=callback.data_;
    if(state->thread!=std::this_thread::get_id())std::terminate();
    if(!data || data->origin.lock()!=state)return;
    if(!data->finished)data->invalid=true;
    if(state->active==data)state->active.reset();
}
std::optional<LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource>
LegacyTaiwanOwnedDeitySelectionRegistry::observe(Session& peer) {
    const auto state=state_;Impl::Read read(*state);
    const auto at=state->slots.find(peer.id());
    if(at==state->slots.end() || !state->written(peer,at->second))return {};
    return WrittenSelectionSource(at->second);
}
void LegacyTaiwanOwnedDeitySelectionRegistry::release(Session& peer) {
    const auto state=state_;Impl::Read read(*state);const auto at=state->slots.find(peer.id());
    if(at==state->slots.end() || at->second->session.lock().get()!=&peer)return;
    at->second->invalid=true;if(state->active==at->second)state->active.reset();state->slots.erase(at);
}
std::span<const RecoveredOwnedCompanions::SelectionPublication>
LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource::publications() const noexcept{return data_->results;}
const Session::NormalWorldInitialization&
LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource::initialization() const noexcept{return data_->initialization;}
const Session::WorldCallbackOutput&
LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource::output() const noexcept{return data_->output;}
bool LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource::current(Session& peer) const {
    const auto state=data_->origin.lock();
    return state && state->thread==std::this_thread::get_id() && !state->reading && state->written(peer,data_);
}
}
