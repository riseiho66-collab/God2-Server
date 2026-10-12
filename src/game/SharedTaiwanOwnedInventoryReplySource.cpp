#include "game/SharedTaiwanOwnedInventoryReplySource.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <stdexcept>

namespace god2 {
namespace {
using Source=SharedTaiwanOwnedInventoryReplySource;
using State=SqliteOwnedEquipmentTransaction::State;
bool shape(const State& state) {
    return NativeEquipmentSnapshot::same_root(state.inventory.root,state.equipment.root) &&
        state.equipment.client_sha256==NativeEquipmentSnapshot::client_pin &&
        state.equipment.record_kind==NativeEquipmentSnapshot::kind &&
        state.equipment.record.size()==NativeEquipmentSnapshot::record_bytes;
}
// Match an already authoritative common alias to the supplied native row.
// This is equality, not a native key/raw20 -> common instance ID conversion.
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
               alias.revision!=item.revision ||
               alias.native_key!=key || alias.record.size()!=20 ||
               !std::equal(alias.record.begin(),alias.record.end(),bytes.begin()+at+4))return false;
            ++found;
        }
    }
    return count?key && found==1:!key && found==0;
}
std::vector<std::uint8_t> prepare_bytes(const State& before,const State& after,
    const std::vector<Source::Operation>& operations,Source::Budgets budgets) {
    if(!budgets.max_records || !budgets.max_logical_bytes ||
       budgets.max_logical_bytes>RecoveredWorldFrame::max_logical_size || operations.empty() ||
       operations.size()>budgets.max_records)throw std::invalid_argument("TW inventory component lacks actual bounded operations");
    std::array<bool,50> touched{},has_item{},final_absolute{};
    std::array<RecoveredTaiwanInventoryItemRecord::Instance,50> instances{};
    std::array<RecoveredInventory::SlotUpdate,50> absolute{};
    std::vector<std::uint8_t> logical;logical.reserve(budgets.max_logical_bytes);
    const auto append=[&](const auto& record) {
        if(record.size()>budgets.max_logical_bytes-logical.size())
            throw std::invalid_argument("TW inventory component logical budget exceeded");
        logical.insert(logical.end(),record.begin(),record.end());
    };
    for(const auto& operation:operations) {
        if(operation.valueless_by_exception())throw std::invalid_argument("TW inventory component has no actual record");
        if(const auto* item=std::get_if<RecoveredTaiwanInventoryItemRecord::Fields>(&operation)) {
            const auto encoded=RecoveredTaiwanInventoryItemRecord::encode(*item);
            if(!encoded)throw std::invalid_argument("TW inventory3B native slot rejected");
            // A component is a bounded before -> next material projection,
            // not a sequence of transient grants. One exact full20 per slot.
            const auto at=std::size_t(item->slot)*24;
            const auto& next=after.equipment.record;
            const auto& actual=next[at]?next:before.equipment.record;
            if(has_item[item->slot] || !actual[at] ||
               !std::equal(item->instance.begin(),item->instance.end(),actual.begin()+at+4))
                throw std::invalid_argument("TW inventory3B requires an exact actual owned before/next instance");
            append(*encoded);touched[item->slot]=has_item[item->slot]=true;
            final_absolute[item->slot]=false;instances[item->slot]=item->instance;
        }else {
            const auto& update=std::get<RecoveredInventory::SlotUpdate>(operation);
            const auto encoded=RecoveredInventory::encode_slot_update(update);
            if(!encoded)throw std::invalid_argument("TW inventory41 native slot rejected");
            const auto at=std::size_t(update.slot)*24;
            const auto matches=[&](const State& actual) {
                const auto& row=actual.equipment.record;
                return row[at] && update.raw_count==row[at] &&
                    update.client_item_id==row[at+4]+256u*row[at+5];
            };
            if(update.raw_count>0 && update.raw_count<128 && !matches(before) && !matches(after))
                throw std::invalid_argument("TW inventory41 requires an exact actual owned before/next count and key");
            append(*encoded);touched[update.slot]=final_absolute[update.slot]=true;absolute[update.slot]=update;
        }
    }
    for(std::size_t slot=0;slot<50;++slot) {
        const auto at=slot*24;const auto& old=before.equipment.record;const auto& next=after.equipment.record;
        const bool changed=!std::equal(old.begin()+at,old.begin()+at+24,next.begin()+at);
        if(!touched[slot]) {
            if(changed)throw std::invalid_argument("TW inventory component omits changed native row");
            continue;
        }
        if(!final_absolute[slot] || !alias_row(before,slot) || !alias_row(after,slot) ||
           !std::equal(old.begin()+at+1,old.begin()+at+4,next.begin()+at+1))
            throw std::invalid_argument("TW inventory component lacks exact before/after alias or final count; opaque prefix must be retained");
        const auto& update=absolute[slot];const bool occupied=update.raw_count>0 && update.raw_count<128;
        const auto count=occupied?update.raw_count:0;
        const auto key=occupied?update.client_item_id:0;
        if(count!=next[at] || key!=next[at+4]+256u*next[at+5])
            throw std::invalid_argument("TW inventory final absolute41 differs from supplied next row");
        // Only data-prefix field effects. Opaque UI helpers/pending/stat and
        // whole native after-cache acceptance are not certified by this check.
        if(has_item[slot]) {
            if(!std::equal(instances[slot].begin()+2,instances[slot].end(),next.begin()+at+6))
                throw std::invalid_argument("TW inventory full20 tail differs from supplied next row");
            if(occupied && (instances[slot][0]!=next[at+4] || instances[slot][1]!=next[at+5]))
                throw std::invalid_argument("TW inventory occupied3B must match the actual committed alias");
        }else if(!std::equal(old.begin()+at+6,old.begin()+at+24,next.begin()+at+6))
            throw std::invalid_argument("TW inventory41 alone cannot replace the other18 instance bytes");
    }
    return RecoveredWorldFrame::encode(logical);
}
}
SharedTaiwanOwnedInventoryReplySource::SharedTaiwanOwnedInventoryReplySource(
    std::shared_ptr<SqliteOwnedEquipmentTransaction> transaction,
    std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> reader,Session& session,
    const Session::NativeWorldSelectionInput& input,const SharedTaiwanOwnedItemSelectionSource::Selection& selection,
    State after,std::vector<std::uint8_t> wire)
    :transaction_(std::move(transaction)),reader_(std::move(reader)),selection_(selection),
     connection_(session.shared_from_this()),input_(input),lease_(selection.lease()),
     battle_(selection.battle_generation()),after_(std::move(after)),wire_(std::move(wire)) {}
SharedTaiwanOwnedInventoryReplySource::~SharedTaiwanOwnedInventoryReplySource() {
    if(thread_!=std::this_thread::get_id())std::terminate();
}
void SharedTaiwanOwnedInventoryReplySource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW inventory component game owner mismatch");
}
bool SharedTaiwanOwnedInventoryReplySource::local(Session& session) const {
    return !invalidated_ && connection_.lock().get()==&session && !session.closing() &&
        session.state()==SessionState::InWorld && session.id()==lease_.session &&
        session.account_id==lease_.account && session.character_id==lease_.character &&
        session.battle_generation()==battle_ && session.world_selection_input_current(input_) &&
        session.recovered_world_ready() && session.common_world_delivery_current(lease_.account,lease_.character,lease_.generation) &&
        !session.common_world_entry_current(lease_.account,lease_.character,lease_.generation);
}
std::shared_ptr<SharedTaiwanOwnedInventoryReplySource> SharedTaiwanOwnedInventoryReplySource::prepare(
    std::shared_ptr<SqliteOwnedEquipmentTransaction> transaction,std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> reader,
    Session& session,const Session::NativeWorldSelectionInput& input,
    const SharedTaiwanOwnedItemSelectionSource::Selection& selection,SqliteOwnedEquipmentTransaction::Before before,
    State after,std::vector<Operation> operations,Budgets budgets) {
    if(!transaction || !reader || !reader->owns_repository(transaction->inventory_writer()) ||
       !before.inventory || !before.equipment || *before.inventory!=selection.snapshot() || !shape(after) ||
       !NativeEquipmentSnapshot::same_root(selection.snapshot().root,after.inventory.root) ||
       after.equipment.position!=selection.saved_position() || !session.world_selection_input_current(input) ||
       input.request().client_item_id!=selection.request().client_item_id || input.request().raw_slot!=selection.request().raw_slot ||
       !reader->current(session,selection) || !transaction->before_current(before) ||
       !reader->current(session,selection))throw std::invalid_argument("TW inventory component requires actual current C28 before and full next state");
    const State old{*before.inventory,*before.equipment};
    if(!shape(old) || old.equipment.position!=selection.saved_position() ||
       !NativeEquipmentSnapshot::same_root(old.inventory.root,after.inventory.root) ||
       selection.alias().native_slot!=selection.request().raw_slot || !alias_row(old,selection.request().raw_slot))
        throw std::invalid_argument("TW inventory component before material is not the actual common owner");
    auto wire=prepare_bytes(old,after,operations,budgets);
    auto result=std::shared_ptr<SharedTaiwanOwnedInventoryReplySource>(new SharedTaiwanOwnedInventoryReplySource(
        std::move(transaction),reader,session,input,selection,std::move(after),std::move(wire)));
    if(!reader->current(session,selection) || !result->transaction_->before_current(before) ||
       !reader->current(session,selection) || !result->local(session))
        throw std::invalid_argument("TW inventory component before source changed during preparation");
    return result;
}
void SharedTaiwanOwnedInventoryReplySource::invalidate() {owner();invalidated_=true;}
std::optional<SharedTaiwanOwnedInventoryReplySource::Component> SharedTaiwanOwnedInventoryReplySource::take(
    Session& session,const SqliteOwnedEquipmentTransaction::Committed& committed) {
    owner();
    if(consumed_) {invalidated_=true;return std::nullopt;}
    consumed_=true;
    if(!local(session) || !reader_->ready_current(session,selection_) || !local(session) ||
       committed.inventory().snapshot()!=after_.inventory || committed.equipment().snapshot()!=after_.equipment ||
       !transaction_->committed_current(committed) || !local(session) ||
       !reader_->ready_current(session,selection_) || !local(session)) {invalidated_=true;return std::nullopt;}
    return Component(std::move(wire_));
}
bool SharedTaiwanOwnedInventoryReplySource::entry_current(
    Session& session,const SqliteOwnedEquipmentTransaction::EntryCommitted& committed) {
    owner();
    // Retain every owner/token BEFORE a virtual ready observer. An observer
    // may release the caller's last source/component/receipt reference.
    const auto self=shared_from_this();
    const auto receipt=committed;
    const auto connection=connection_.lock();
    if(!connection || connection.get()!=&session) {invalidated_=true;return false;}
    if(observing_entry_) {invalidated_=true;return false;}
    observing_entry_=true;
    struct Leave {bool& active;~Leave(){active=false;}} leave{observing_entry_};
    try {
        const auto& material=receipt.material();
        const bool valid=consumed_ && local(session) && reader_->ready_current(session,selection_) && local(session) &&
            material.inventory().snapshot()==after_.inventory && material.equipment().snapshot()==after_.equipment &&
            transaction_->committed_current(receipt) && local(session) &&
            reader_->ready_current(session,selection_) && local(session) &&
            // Recheck ALL three tuples after the last ready observer. The
            // material() access above only compares the prepared projection;
            // durable Current always selects the complete receipt overload.
            transaction_->committed_current(receipt) && local(session);
        if(!valid)invalidated_=true;
        return valid;
    }catch(...) {invalidated_=true;throw;}
}
std::optional<SharedTaiwanOwnedInventoryReplySource::EntryComponent> SharedTaiwanOwnedInventoryReplySource::take(
    Session& session,const SqliteOwnedEquipmentTransaction::EntryCommitted& committed) {
    owner();
    const auto self=shared_from_this();
    const auto receipt=committed;
    if(consumed_) {invalidated_=true;return std::nullopt;}
    consumed_=true;
    if(!entry_current(session,receipt))return std::nullopt;
    // The source and wire were allocated by prepare(), before COMMIT. Receipt
    // copies keep their immutable shared snapshots, including the full entry.
    return EntryComponent(std::move(wire_),self,receipt);
}
bool SharedTaiwanOwnedInventoryReplySource::EntryComponent::current(Session& session) const {
    return source_ && source_->entry_current(session,committed_);
}
}
