#include "game/SharedTaiwanOwnedBagMoveSource.h"
#include "game/SharedTaiwanOwnedItemSelectionSource.h"
#include "game/TaiwanOwnedBagItemMaterial.h"
#include "protocol/RecoveredInventory.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <thread>

namespace god2 {
namespace {
using Transaction=SqliteOwnedEquipmentTransaction;
using State=Transaction::State;
using Request=RecoveredInventoryMoveRequest::Request;
using Reply=SharedTaiwanWorldRecordSource::Reply;
constexpr auto max_revision=std::uint64_t(std::numeric_limits<std::int64_t>::max());
bool advances(std::uint64_t revision){return revision && revision<max_revision;}
bool alias_row(const State& state,std::size_t slot) {
    const auto at=slot*24;const auto& bytes=state.equipment.record;
    const auto count=bytes[at];const auto key=std::uint16_t(bytes[at+4]+256u*bytes[at+5]);
    std::size_t found=0;
    for(const auto& cell:state.inventory.cells)if(cell.instance) {
        const auto& item=*cell.instance;
        for(const auto& alias:item.aliases) {
            if(alias.client_sha256!=NativeEquipmentSnapshot::client_pin ||
               alias.profile!=SharedTaiwanOwnedItemSelectionSource::alias_profile || alias.native_slot!=slot)continue;
            if(!count || !key || count>99 || item.quantity!=count || (!item.stackable && count!=1) ||
               alias.revision!=item.revision || alias.native_key!=key || alias.record.size()!=20 ||
               !std::equal(alias.record.begin(),alias.record.end(),bytes.begin()+at+4))return false;
            ++found;
        }
    }
    return count?key && found==1:!key && found==0;
}
std::optional<State> plan(const Transaction::Before& before,Request request,bool material_mode) {
    if(!before.inventory || !before.equipment || request.source_slot>=30 ||
       request.destination_slot>=30 || request.source_slot==request.destination_slot)return std::nullopt;
    State next{*before.inventory,*before.equipment};
    if(!NativeEquipmentSnapshot::same_root(next.inventory.root,next.equipment.root) ||
       next.equipment.client_sha256!=NativeEquipmentSnapshot::client_pin ||
       next.equipment.record_kind!=NativeEquipmentSnapshot::kind ||
       next.equipment.record.size()!=NativeEquipmentSnapshot::record_bytes ||
       !advances(next.inventory.revision) || !advances(next.equipment.revision))return std::nullopt;
    for(std::size_t slot=0;slot<50;++slot)if(!alias_row(next,slot))return std::nullopt;
    // Explicit CUSTOM-0093 location mapping. Missing cells are not capacity.
    auto source=next.inventory.cells.end(),destination=source;
    for(auto it=next.inventory.cells.begin();it!=next.inventory.cells.end();++it)if(it->location_kind=="bag") {
        if(it->location_index==request.source_slot)source=it;
        if(it->location_index==request.destination_slot)destination=it;
    }
    if(source==next.inventory.cells.end() || destination==next.inventory.cells.end() || !source->instance)return std::nullopt;
    const auto eligible=[material_mode](const OwnedInventoryCell& cell,std::uint8_t slot) {
        if(!cell.instance)return true;
        const auto& item=*cell.instance;
        if(material_mode)return advances(item.revision) && TaiwanOwnedBagItemMaterial::observe(item,slot).has_value();
        // A second client's relocation semantics are unqualified. Preserve it
        // by refusing this subset, rather than deleting/updating that alias.
        return advances(item.revision) && item.aliases.size()==1 &&
            item.aliases.front().client_sha256==NativeEquipmentSnapshot::client_pin &&
            item.aliases.front().profile==SharedTaiwanOwnedItemSelectionSource::alias_profile &&
            item.aliases.front().native_slot==slot;
    };
    if(!eligible(*source,request.source_slot) || !eligible(*destination,request.destination_slot))return std::nullopt;
    const auto a=std::size_t(request.source_slot)*24,b=std::size_t(request.destination_slot)*24;
    // 41 leaves these bytes intact, including stale metadata in empty rows.
    if(!material_mode && !std::equal(next.equipment.record.begin()+a+6,next.equipment.record.begin()+a+24,
                   next.equipment.record.begin()+b+6))return std::nullopt;
    std::swap(source->instance,destination->instance);
    const auto project=[&](OwnedInventoryCell& cell,std::uint8_t slot) {
        const auto at=std::size_t(slot)*24;
        std::uint16_t key=0;std::uint8_t count=0;
        if(cell.instance) {
            auto& item=*cell.instance;++item.revision;
            auto& alias=item.aliases.front();alias.native_slot=slot;alias.revision=item.revision;
            key=alias.native_key;count=static_cast<std::uint8_t>(item.quantity);
            if(material_mode) {
                auto& material=item.aliases[1];material.native_slot=slot;material.revision=item.revision;
                material.record[2]=slot; // Only the qualified native slot field.
                std::copy(alias.record.begin(),alias.record.end(),next.equipment.record.begin()+at+4);
            }
        }
        next.equipment.record[at]=count;
        next.equipment.record[at+4]=static_cast<std::uint8_t>(key);
        next.equipment.record[at+5]=static_cast<std::uint8_t>(key>>8);
    };
    project(*source,request.source_slot);project(*destination,request.destination_slot);
    // Keep the full original material provenance and tag this derived policy
    // once. Repeated moves must not exhaust the source-record field by growing
    // an operation log; actual fulltuple/instance revisions advance each time.
    const auto tag=[material_mode](std::string& record) {
        const std::string_view marker=material_mode?";CUSTOM-0094:C24-full25-retention":";CUSTOM-0093:C24-whole-instance";
        if(record.ends_with(marker))return true;
        if(record.size()+marker.size()>2048)return false;
        record.append(marker);return true;
    };
    if(!tag(next.inventory.source_record) || !tag(next.equipment.source_record))return std::nullopt;
    if(material_mode)for(auto* cell:{&*source,&*destination})if(cell->instance)
        for(auto& alias:cell->instance->aliases)if(!tag(alias.source_record))return std::nullopt;
    ++next.inventory.revision;++next.equipment.revision;
    // Every full20 remains the original instance material. All50 aliases must
    // still agree with the full presentation witness after the two projections.
    for(std::size_t slot=0;slot<50;++slot)if(!alias_row(next,slot))return std::nullopt;
    return next;
}
class Owner final {
public:
    Owner(std::shared_ptr<Transaction> transaction,std::shared_ptr<SharedWorldPresence> presence,bool material_mode)
        :transaction_(std::move(transaction)),presence_(std::move(presence)),material_mode_(material_mode) {}
    ~Owner(){if(thread_!=std::this_thread::get_id())std::terminate();}
    void owner() const {if(thread_!=std::this_thread::get_id())throw std::logic_error("TW bag move game owner mismatch");}
    void invalidate(){owner();if(busy_)invalid_=true;}
    void release(Session& session){owner();if(active_==&session)invalidate();}
    std::optional<Reply> dispatch(Session& session,Request request) {
        owner();if(busy_){invalid_=true;throw std::logic_error("TW bag move reentered");}
        busy_=true;invalid_=false;active_=&session;
        struct End {Owner& self;~End(){self.active_=nullptr;self.busy_=false;self.invalid_=false;}} end{*this};
        auto connection=session.shared_from_this();
        const auto lease=presence_->ready_lease(session.id(),session.account_id,session.character_id);
        if(!lease)return std::nullopt;
        const auto battle=session.battle_generation();
        const auto local=[&] {
            return !invalid_ && connection.get()==&session && !session.closing() &&
                session.state()==SessionState::InWorld && session.id()==lease->session &&
                session.account_id==lease->account && session.character_id==lease->character &&
                session.battle_generation()==battle && session.recovered_world_ready() &&
                session.common_world_delivery_current(lease->account,lease->character,lease->generation) &&
                !session.common_world_entry_current(lease->account,lease->character,lease->generation);
        };
        if(!local())return std::nullopt;
        const auto before=transaction_->observe_before(lease->account,lease->character);
        if(!before || !before->equipment || before->equipment->actor_handle!=lease->actor_handle ||
           presence_->ready_lease(session.id(),session.account_id,session.character_id)!=lease ||
           presence_->saved_position(*lease)!=std::optional{before->equipment->position} || !local())return std::nullopt;
        const auto next=plan(*before,request,material_mode_);if(!next)return std::nullopt;
        // Allocate and encode the complete native result before any storage write.
        std::vector<std::uint8_t> logical;logical.reserve(material_mode_?70:10);
        if(material_mode_) {
            // CUSTOM-0094 ordered projection: clear both counters, replay each
            // moved instance's own full material, then set exact final counts.
            // No opaque from another item and no default/padded WORD.
            for(const auto slot:{request.source_slot,request.destination_slot}) {
                const auto clear=RecoveredInventory::clear_slot(slot);
                logical.insert(logical.end(),clear->begin(),clear->end());
            }
            for(const auto& cell:next->inventory.cells)if(cell.location_kind=="bag" && cell.instance &&
                (cell.location_index==request.source_slot || cell.location_index==request.destination_slot)) {
                const auto material=TaiwanOwnedBagItemMaterial::observe(*cell.instance,static_cast<std::uint8_t>(cell.location_index));
                if(!material)throw std::logic_error("TW bag move next full25 material rejected");
                const auto record=RecoveredTaiwanInventoryItemRecord::encode(*material);
                if(!record)throw std::logic_error("TW bag move full25 projection rejected");
                logical.insert(logical.end(),record->begin(),record->end());
            }
        }
        for(const auto slot:{request.source_slot,request.destination_slot}) {
            const auto at=std::size_t(slot)*24;const auto& bytes=next->equipment.record;
            const auto record=RecoveredInventory::encode_slot_update({
                std::uint16_t(bytes[at+4]+256u*bytes[at+5]),slot,bytes[at]});
            if(!record)throw std::logic_error("TW bag move projection rejected");
            logical.insert(logical.end(),record->begin(),record->end());
        }
        auto reply=Reply::wire(RecoveredWorldFrame::encode(logical));
        if(!local() || !transaction_->before_current(*before) || !local())return std::nullopt;
        // Concrete issuer is internal, not a callback placeholder. The joint
        // writer checks common root/position/battle/full population in all phases.
        // Do not reenter its readers from this synchronous issuer.
        const auto committed=transaction_->replace_from_issuer(*before,*next,
            [&](const Transaction::Before&,const State& proposed,Transaction::Check)->std::optional<State> {
                if(!local())return std::nullopt;
                const auto qualified=plan(*before,request,material_mode_);
                return qualified && *qualified==proposed?qualified:std::nullopt;
            });
        if(!committed)return std::nullopt;
        if(!local() || committed->inventory().snapshot()!=next->inventory ||
           committed->equipment().snapshot()!=next->equipment || !transaction_->committed_current(*committed) ||
           presence_->ready_lease(session.id(),session.account_id,session.character_id)!=lease ||
           presence_->saved_position(*lease)!=std::optional{next->equipment.position} || !local()) {
            invalid_=true;throw std::runtime_error("TW bag move committed but delivery became stale");
        }
        return reply;
    }
private:
    const std::thread::id thread_=std::this_thread::get_id();
    std::shared_ptr<Transaction> transaction_;
    std::shared_ptr<SharedWorldPresence> presence_;
    const bool material_mode_;
    Session* active_=nullptr;
    bool busy_=false,invalid_=false;
};
}
static SharedTaiwanWorldRecordSource::InventoryMoveBinding make_bag_binding(
    std::shared_ptr<Transaction> transaction,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,std::shared_ptr<SharedWorldPresence> presence,bool material_mode) {
    if(!transaction || !presence || !transaction->owns_sources(accounts,characters) ||
       !presence->owns_repository(characters))throw std::invalid_argument("TW bag move requires actual shared sources");
    auto owner=std::make_shared<Owner>(std::move(transaction),std::move(presence),material_mode);
    return {[owner](Session& session,const Request& request){return owner->dispatch(session,request);},
        [owner](Session& session){owner->release(session);},[owner]{owner->invalidate();}};
}
SharedTaiwanWorldRecordSource::InventoryMoveBinding SharedTaiwanOwnedBagMoveSource::create(
    std::shared_ptr<Transaction> transaction,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,std::shared_ptr<SharedWorldPresence> presence) {
    return make_bag_binding(std::move(transaction),accounts,characters,std::move(presence),false);
}
SharedTaiwanWorldRecordSource::InventoryMoveBinding SharedTaiwanOwnedBagMoveSource::create_with_item_material(
    std::shared_ptr<Transaction> transaction,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,std::shared_ptr<SharedWorldPresence> presence) {
    return make_bag_binding(std::move(transaction),accounts,characters,std::move(presence),true);
}
}
