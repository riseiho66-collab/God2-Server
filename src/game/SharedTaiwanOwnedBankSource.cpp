#include "game/SharedTaiwanOwnedBankSource.h"
#include "game/TaiwanOwnedBankItemMaterial.h"
#include "game/TaiwanOwnedBagItemMaterial.h"
#include "handlers/RecoveredMovementService.h"
#include "net/Session.h"
#include "protocol/RecoveredInventory.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <limits>
#include <map>
#include <set>
#include <thread>

namespace god2 {
namespace {
using Material=TaiwanOwnedBankItemMaterial;
using Transaction=SqliteOwnedEquipmentTransaction;
using State=Transaction::State;
using Request=RecoveredBankItems::Request;
using Kind=RecoveredBankItems::Kind;
constexpr std::string_view marker=";CUSTOM-0160:whole-bank-full25-single-custody";
bool advances(std::uint64_t value) {
    return value && value<static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
}
bool tag(std::string& text) {
    if(text.find(marker)!=std::string::npos)return true;
    if(text.size()>2048-marker.size())return false;
    text.append(marker);return true;
}
const OwnedInventoryCell* cell_at(const State& state,std::string_view kind,std::uint32_t index) {
    const auto found=std::find_if(state.inventory.cells.begin(),state.inventory.cells.end(),
        [&](const auto& cell){return cell.location_kind==kind && cell.location_index==index;});
    return found==state.inventory.cells.end()?nullptr:&*found;
}
OwnedInventoryCell* cell_at(State& state,std::string_view kind,std::uint32_t index) {
    return const_cast<OwnedInventoryCell*>(cell_at(std::as_const(state),kind,index));
}
bool reserved(const std::vector<std::uint8_t>& raw) {
    if(raw.size()!=20)return true;
    const auto type=raw[2]&0x3fu;
    return type==0x0d || type==0x20 || type==0x22;
}
bool bag_rows(const State& state) {
    for(const auto& cell:state.inventory.cells)if(cell.instance)
        for(const auto& alias:cell.instance->aliases)if(alias.client_sha256==NativeEquipmentSnapshot::client_pin &&
            alias.profile==SharedTaiwanOwnedItemSelectionSource::alias_profile) {
            if(alias.native_slot>=50 || alias.record.size()!=20 || alias.revision!=cell.instance->revision ||
               !alias.native_key || (alias.native_slot<30 &&
                (cell.location_kind!="bag" || cell.location_index!=alias.native_slot)))return false;
        }
    for(std::size_t slot=0;slot<50;++slot) {
        const auto at=slot*24;const auto& bytes=state.equipment.record;
        const auto count=bytes[at];const auto key=std::uint16_t(bytes[at+4]+256u*bytes[at+5]);
        std::size_t found=0;
        for(const auto& cell:state.inventory.cells)if(cell.instance)for(const auto& alias:cell.instance->aliases) {
            if(alias.client_sha256!=NativeEquipmentSnapshot::client_pin ||
               alias.profile!=SharedTaiwanOwnedItemSelectionSource::alias_profile || alias.native_slot!=slot)continue;
            if(!count || count>99 || !key || alias.native_key!=key || cell.instance->quantity!=count ||
               (!cell.instance->stackable && count!=1) ||
               !std::equal(alias.record.begin(),alias.record.end(),bytes.begin()+at+4))return false;
            ++found;
        }
        if(count?(!key || found!=1):(key || found))return false;
    }
    return true;
}
template<class T>void append(std::vector<std::uint8_t>& to,const T& bytes){to.insert(to.end(),bytes.begin(),bytes.end());}
std::array<std::uint8_t,29> bank_record(const State& state,std::uint8_t page,std::uint8_t local) {
    const auto* cell=cell_at(state,"bank",std::uint32_t(page)*50+local);
    if(!cell)throw std::logic_error("Whole bank projection has absent source cell");
    RecoveredInventoryProjection::Metadata raw{};std::uint8_t quantity=0;
    if(cell->instance) {
        std::copy(cell->instance->aliases.front().record.begin(),cell->instance->aliases.front().record.end(),raw.begin());
        quantity=static_cast<std::uint8_t>(cell->instance->quantity);
    }
    const auto result=RecoveredBankItems::slot(page,local,quantity,raw);
    if(!result)throw std::logic_error("Whole bank S48 projection rejected");
    return *result;
}
bool retarget(OwnedInventoryInstance& item,bool bank,std::uint8_t page,std::uint8_t slot) {
    if(!advances(item.revision))return false;
    ++item.revision;
    item.aliases[0].profile=bank?Material::identity_profile(page):SharedTaiwanOwnedItemSelectionSource::alias_profile;
    item.aliases[1].profile=bank?Material::material_profile(page):TaiwanOwnedBagItemMaterial::profile;
    for(auto& alias:item.aliases) {
        alias.native_slot=slot;alias.revision=item.revision;
        if(!tag(alias.source_record))return false;
    }
    // Only withdrawal changes the known slot field of retained bag material.
    // Bank movement preserves its complete incoming25 bytes, including opaque.
    if(!bank)item.aliases[1].record[2]=slot;
    return true;
}
void bag_project(State& state,const OwnedInventoryCell& cell,std::uint8_t slot) {
    const auto at=std::size_t(slot)*24;
    state.equipment.record[at]=cell.instance?static_cast<std::uint8_t>(cell.instance->quantity):0;
    if(cell.instance)std::copy(cell.instance->aliases[0].record.begin(),cell.instance->aliases[0].record.end(),
        state.equipment.record.begin()+at+4);
    else state.equipment.record[at+4]=state.equipment.record[at+5]=0; // Native41 retains the other18 bytes.
}
}
std::string Material::identity_profile(std::uint8_t page) {
    if(page>=6)throw std::invalid_argument("Whole bank page outside native namespace");
    return "tw149c-bank"+std::to_string(page)+"-item20";
}
std::string Material::material_profile(std::uint8_t page) {
    if(page>=6)throw std::invalid_argument("Whole bank page outside native namespace");
    return "tw149c-bank"+std::to_string(page)+"-item3b25-material";
}
std::optional<RecoveredTaiwanInventoryItemRecord::Fields> Material::observe(
    const OwnedInventoryInstance& item,std::uint8_t page,std::uint8_t local) {
    if(page>=6 || local>=50 || item.aliases.size()!=2 || !item.id || !item.definition_key ||
       !item.revision || item.quantity==0 || item.quantity>99 || (!item.stackable && item.quantity!=1))return {};
    const auto& identity=item.aliases[0];const auto& material=item.aliases[1];
    if(identity.client_sha256!=NativeEquipmentSnapshot::client_pin || material.client_sha256!=identity.client_sha256 ||
       identity.profile!=identity_profile(page) || material.profile!=material_profile(page) ||
       identity.native_slot!=local || material.native_slot!=local || identity.native_key==0 ||
       material.native_key!=identity.native_key || identity.revision!=item.revision || material.revision!=item.revision ||
       identity.source_sha256!=material.source_sha256 || identity.source_record!=material.source_record ||
       identity.record.size()!=20)return {};
    const auto parsed=RecoveredInstanceUpdate::parse_logical(material.record);
    if(!parsed)return {};
    const auto raw=RecoveredInstanceUpdate::encode_logical(*parsed);
    if(raw[1]==0 || raw[1]>99 || raw[2]>=30 || parsed->low_word_lookup_key()!=identity.native_key ||
       !std::equal(identity.record.begin(),identity.record.end(),raw.begin()+5))return {};
    RecoveredTaiwanInventoryItemRecord::Instance instance;
    std::copy(raw.begin()+5,raw.end(),instance.begin());
    return RecoveredTaiwanInventoryItemRecord::Fields(raw[1],raw[2],
        std::uint16_t(raw[3]+256u*raw[4]),instance);
}
bool Material::qualified(const State& state) {
    if(!NativeEquipmentSnapshot::same_root(state.inventory.root,state.equipment.root) ||
       state.equipment.client_sha256!=NativeEquipmentSnapshot::client_pin ||
       state.equipment.record_kind!=NativeEquipmentSnapshot::kind ||
       state.equipment.record.size()!=NativeEquipmentSnapshot::record_bytes ||
       state.equipment.actor_handle>0x3fff || !state.equipment.appearance() ||
       state.equipment.appearance()->actor_identity()!=state.equipment.actor_handle ||
       !state.inventory.revision || !state.equipment.revision || state.inventory.cells.size()>4096)return false;
    std::set<std::uint64_t> ids;std::size_t banks=0;
    const OwnedInventoryCell* previous=nullptr;
    for(const auto& cell:state.inventory.cells) {
        if(previous && std::pair{previous->location_kind,previous->location_index}>=
            std::pair{cell.location_kind,cell.location_index})return false;
        previous=&cell;
        if(cell.instance && !ids.insert(cell.instance->id).second)return false;
        if(cell.location_kind=="bank") {
            if(cell.location_index>=300)return false;
            ++banks;
            if(cell.instance) {
                const auto page=static_cast<std::uint8_t>(cell.location_index/50),local=static_cast<std::uint8_t>(cell.location_index%50);
                if(!observe(*cell.instance,page,local) || reserved(cell.instance->aliases[0].record)!=(local<2))return false;
            }
        } else if(cell.instance)for(const auto& alias:cell.instance->aliases) {
            if(alias.client_sha256==NativeEquipmentSnapshot::client_pin && alias.profile.starts_with("tw149c-bank"))return false;
        }
    }
    return banks==300 && bag_rows(state);
}
std::optional<State> Material::plan(const Transaction::Before& before,const Request& request) {
    if(!before.inventory || !before.equipment || request.page>=3 || !request.target)return {};
    State next{*before.inventory,*before.equipment};
    if(!qualified(next) || !advances(next.inventory.revision) || !advances(next.equipment.revision))return {};
    const bool deposit=request.kind==Kind::Deposit,withdraw=request.kind==Kind::Withdraw,move=request.kind==Kind::Move;
    if(!deposit && !withdraw && !move)return {};
    if(deposit?(request.source>=30 || request.destination<2 || request.destination>=50):
       withdraw?(request.source<2 || request.source>=50 || request.destination>=30):
       (request.source<2 || request.source>=50 || request.destination<2 || request.destination>=50 ||
        request.source==request.destination || request.quantity!=1))return {};
    auto* source=cell_at(next,deposit?"bag":"bank",deposit?request.source:std::uint32_t(request.page)*50+request.source);
    auto* destination=cell_at(next,withdraw?"bag":"bank",withdraw?request.destination:std::uint32_t(request.page)*50+request.destination);
    if(!source || !destination || !source->instance || (!move && destination->instance))return {};
    if(deposit) {
        if(!TaiwanOwnedBagItemMaterial::observe(*source->instance,request.source) || reserved(source->instance->aliases[0].record))return {};
    }
    // Quantity equality permits the original whole instance only. No new ID,
    // acquisition receipt, splitting, combining or inferred stack limit.
    if(!move && request.quantity!=source->instance->quantity)return {};
    std::swap(source->instance,destination->instance);
    if(destination->instance && !retarget(*destination->instance,!withdraw,request.page,request.destination))return {};
    if(source->instance && !retarget(*source->instance,true,request.page,request.source))return {};
    if(deposit)bag_project(next,*source,request.source);
    if(withdraw)bag_project(next,*destination,request.destination);
    if(!tag(next.inventory.source_record) || !tag(next.equipment.source_record))return {};
    ++next.inventory.revision;++next.equipment.revision;
    return qualified(next)?std::optional<State>{std::move(next)}:std::nullopt;
}
std::vector<std::uint8_t> Material::opening_wire(const State& state) {
    if(!qualified(state))throw std::invalid_argument("Whole bank opening lacks complete source population");
    std::vector<std::uint8_t> wire,logical;
    wire.reserve(9000);logical.reserve(RecoveredWorldFrame::max_logical_size);
    for(std::uint8_t page=0;page<6;++page)for(std::uint8_t local=0;local<50;++local) {
        if(logical.size()+29>RecoveredWorldFrame::max_logical_size) {
            append(wire,RecoveredWorldFrame::encode(logical));logical.clear();
        }
        append(logical,bank_record(state,page,local));
    }
    if(!logical.empty())append(wire,RecoveredWorldFrame::encode(logical));
    return wire;
}
std::vector<std::uint8_t> Material::mutation_wire(const State& state,const Request& request) {
    if(!qualified(state))throw std::invalid_argument("Whole bank mutation projection lacks qualified population");
    std::vector<std::uint8_t> logical;
    if(request.kind==Kind::Deposit) {
        const auto clear=RecoveredInventory::clear_slot(request.source);
        if(!clear)throw std::logic_error("Whole bank deposit bag clear rejected");
        append(logical,*clear);append(logical,bank_record(state,request.page,request.destination));
    } else if(request.kind==Kind::Withdraw) {
        append(logical,bank_record(state,request.page,request.source));
        const auto clear=RecoveredInventory::clear_slot(request.destination);
        const auto* cell=cell_at(state,"bag",request.destination);
        const auto material=cell && cell->instance?TaiwanOwnedBagItemMaterial::observe(*cell->instance,request.destination):std::nullopt;
        if(!clear || !material)throw std::logic_error("Whole bank withdrawal lost original full25");
        const auto record=RecoveredTaiwanInventoryItemRecord::encode(*material);
        const auto count=RecoveredInventory::encode_slot_update({cell->instance->aliases[0].native_key,
            request.destination,static_cast<std::uint8_t>(cell->instance->quantity)});
        if(!record || !count)throw std::logic_error("Whole bank withdrawal native projection rejected");
        append(logical,*clear);append(logical,*record);append(logical,*count);
    } else if(request.kind==Kind::Move) {
        append(logical,bank_record(state,request.page,request.source));
        append(logical,bank_record(state,request.page,request.destination));
    } else throw std::invalid_argument("Whole bank projection opcode rejected");
    return RecoveredWorldFrame::encode(logical);
}

struct SharedTaiwanOwnedBankSource::Impl {
    struct Context {
        std::weak_ptr<Session> connection;
        Session::NormalWorldInitialization initialization;
        RecoveredBankService::LeaseSource source;
        std::uint16_t target;
        std::optional<RecoveredPosition> position;
        std::uint64_t battle;
        SessionState phase;
        std::optional<RecoveredMovementService::WorldLocationObservation> movement_binding;
    };
    struct Outcome {Transaction::Committed committed;std::vector<std::uint8_t> wire;bool mutated,current;};
    Impl(std::shared_ptr<Transaction> transaction,RecoveredMovementService& movement,RecoveredBankService& money,std::size_t capacity)
        :transaction(std::move(transaction)),movement(movement),money(money),capacity(capacity) {}
    ~Impl(){if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {if(thread!=std::this_thread::get_id())throw std::logic_error("Whole bank wrong game owner");}
    void invalidate(){owner();if(busy)invalid=true;}
    void release(Session& session) {
        owner();if(active==&session)invalidate();
        const auto found=contexts.find(session.id());
        if(found!=contexts.end() && found->second.connection.lock().get()==&session)contexts.erase(found);
    }
    void stop(){owner();invalidate();stopped=true;contexts.clear();}
    bool current(Session& session) const {
        owner();if(stopped || invalid)return false;
        const auto found=contexts.find(session.id());if(found==contexts.end())return false;
        const auto& context=found->second;
        return context.position && context.movement_binding && movement.world_location_current(*context.movement_binding) &&
            context.connection.lock().get()==&session && !session.closing() &&
            session.recovered_world_ready() && session.state()==context.phase &&
            (context.phase==SessionState::CharacterSelected || context.phase==SessionState::InWorld) &&
            context.battle==session.battle_generation() &&
            context.source.owns(session.id(),session.account_id,session.character_id,context.target) &&
            context.initialization.entry_written() && session.normal_world_initialization_current_on_game(context.initialization) &&
            movement.current_world_location(session.id(),session.account_id,session.character_id)==context.position;
    }
    std::optional<Outcome> run(Session& session,std::uint16_t target,std::optional<Request> request) {
        owner();if(busy){invalid=true;throw std::logic_error("Whole bank reentered");}
        if(stopped)return {};
        busy=true;invalid=false;active=&session;
        struct End {Impl& self;~End(){self.active=nullptr;self.busy=false;self.invalid=false;}} end{*this};
        const auto id=session.id(),account=session.account_id,character=session.character_id;
        const auto phase=session.state();const auto battle=session.battle_generation();
        // Copy every retained source before any observer can close/reopen it.
        std::optional<Context> held;
        if(request) {
            const auto found=contexts.find(id);if(found==contexts.end())return {};
            held=found->second;
        } else {
            contexts.erase(id); // An unsuccessful reopen retires its predecessor.
            const auto initialization=session.normal_world_initialization();
            if(!initialization || contexts.size()>=capacity)return {};
            held.emplace(Context{session.shared_from_this(),*initialization,
                money.capture_lease(id,target,RecoveredBankService::Clock::now()),target,{},battle,phase,
                movement.observe_world_location(id,account,character)});
        }
        const auto connection=held->connection.lock();
        std::optional<RecoveredPosition> position;
        const auto local=[&] {
            return held->movement_binding&&movement.world_location_current(*held->movement_binding)&&
                !invalid && !stopped && connection.get()==&session && id && account && character &&
                target==held->target && held->source.owns(id,account,character,target) &&
                session.normal_world_initialization_current_on_game(held->initialization) && held->initialization.entry_written() &&
                !session.closing() && session.recovered_world_ready() && session.id()==id &&
                session.account_id==account && session.character_id==character && session.state()==phase &&
                (phase==SessionState::CharacterSelected || phase==SessionState::InWorld) && session.battle_generation()==battle &&
                held->battle==battle && held->phase==phase &&
                (!position || movement.current_world_location(id,account,character)==position);
        };
        if(!local())return {};
        const auto entry=RecoveredWorldEntryView::read(held->initialization.entry_frame());
        position=movement.current_location(id,account,character);
        if(!entry || !position || !position->revision || !local())return {};
        if(held->position && held->position!=position)return {};
        held->position=position;
        const auto pose=[&] {return local() && movement.current_location(id,account,character)==position && local();};
        // Full money/NPC access observers run OUTSIDE the joint issuer. The
        // captured opaque source, pure normal INIT and pure movement snapshot
        // are the lifetime dependencies inside it; none invoke SQL/providers.
        if(!money.permits_items(id,target,RecoveredBankService::Clock::now()) || !pose())return {};
        if(!request) {
            auto committed=transaction->observe_committed(account,character);
            if(!committed || committed->equipment().snapshot().actor_handle!=entry->actor_handle ||
               committed->equipment().snapshot().position!=*position || !pose())return {};
            const State state{committed->inventory().snapshot(),committed->equipment().snapshot()};
            if(!Material::qualified(state))return {};
            auto wire=Material::opening_wire(state);
            contexts.insert_or_assign(id,*held); // Allocate before final qualification.
            if(!transaction->committed_current(*committed) || !pose()) {contexts.erase(id);return {};}
            money.renew_items(id,RecoveredBankService::Clock::now());
            if(!local()){contexts.erase(id);return {};}
            return Outcome{std::move(*committed),std::move(wire),false,true};
        }
        const auto before=transaction->observe_before(account,character);
        if(!before || !before->equipment || before->equipment->actor_handle!=entry->actor_handle ||
           before->equipment->position!=*position || !pose())return {};
        const auto next=Material::plan(*before,*request);if(!next)return {};
        auto wire=Material::mutation_wire(*next,*request);
        if(!money.permits_items(id,target,RecoveredBankService::Clock::now()) ||
           !transaction->before_current(*before) || !pose())return {};
        auto committed=transaction->replace_from_issuer(*before,*next,
            [&](const Transaction::Before&,const State& proposed,Transaction::Check)->std::optional<State> {
                if(!local())return {};
                const auto qualified=Material::plan(*before,*request);
                return qualified && *qualified==proposed?qualified:std::nullopt;
            },local);
        if(!committed)return {};
        // COMMIT truth survives every postcommit failure. Never lose this
        // receipt through a catch/re-observation/retry or claim rollback.
        bool current=false;
        try {
            current=local() && committed->inventory().snapshot()==next->inventory &&
                committed->equipment().snapshot()==next->equipment && transaction->committed_current(*committed) && pose();
            if(current) {money.renew_items(id,RecoveredBankService::Clock::now());current=local();}
        } catch(...) {current=false;}
        if(!current)contexts.erase(id);
        return Outcome{std::move(*committed),std::move(wire),true,current};
    }
    const std::thread::id thread=std::this_thread::get_id();
    std::shared_ptr<Transaction> transaction;
    RecoveredMovementService& movement;
    RecoveredBankService& money;
    const std::size_t capacity;
    std::map<std::uint64_t,Context> contexts;
    Session* active=nullptr;
    bool busy=false,invalid=false,stopped=false;
};
SharedTaiwanOwnedBankSource::SharedTaiwanOwnedBankSource(std::unique_ptr<Impl> impl):impl_(std::move(impl)){}
SharedTaiwanOwnedBankSource::~SharedTaiwanOwnedBankSource()=default;
std::shared_ptr<SharedTaiwanOwnedBankSource> SharedTaiwanOwnedBankSource::create(
    std::shared_ptr<Transaction> transaction,AccountRepository& accounts,RecoveredCharacterRepository& characters,
    RecoveredMovementService& movement,RecoveredBankService& money,std::size_t max_sessions) {
    if(!transaction || !max_sessions || !transaction->owns_sources(accounts,characters) || !movement.owns_repository(characters))
        throw std::invalid_argument("Whole bank requires same actual inventory/equipment/common/movement owners");
    return std::shared_ptr<SharedTaiwanOwnedBankSource>(new SharedTaiwanOwnedBankSource(
        std::make_unique<Impl>(std::move(transaction),movement,money,max_sessions)));
}
std::optional<SharedTaiwanOwnedBankSource::Result> SharedTaiwanOwnedBankSource::open(Session& session,std::uint16_t target) {
    try {
        auto out=impl_->run(session,target,{});if(!out)return {};
        return Result(std::move(out->committed),std::move(out->wire),out->mutated,out->current);
    } catch(...) {impl_->release(session);throw;}
}
std::optional<SharedTaiwanOwnedBankSource::Result> SharedTaiwanOwnedBankSource::dispatch(Session& session,const Request& input) {
    // Caller may hold input in mutable callback storage. Retain the full value
    // before the first provider; never consult its address/contents afterwards.
    const Request request=input;
    try {
        auto out=impl_->run(session,request.target,request);
        if(!out){impl_->release(session);return {};}
        return Result(std::move(out->committed),std::move(out->wire),out->mutated,out->current);
    } catch(...) {impl_->release(session);throw;}
}
void SharedTaiwanOwnedBankSource::release(Session& session){impl_->release(session);}
void SharedTaiwanOwnedBankSource::invalidate_active(){impl_->invalidate();}
void SharedTaiwanOwnedBankSource::stop(){impl_->stop();}
bool SharedTaiwanOwnedBankSource::current(Session& session) const{return impl_->current(session);}
}
