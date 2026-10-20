#pragma once
#include "db/SqliteTeleportGemRepository.h"
#include "game/RecoveredPosition.h"
#include "protocol/RecoveredWorldRecords.h"
#include <chrono>
#include <limits>
#include <unordered_map>

namespace god2 {
// CUSTOM-0057: owned16055 menu/selection lifecycle, serialized game executor.
// Native25/26,6D,99,86 contracts do not establish this server-side association.
// This class neither grants an item nor changes its charge or saved position.
class OwnedTeleportGemOffer {
public:
    using Clock=std::chrono::steady_clock;
    using Time=Clock::time_point;
    static constexpr std::uint16_t context=16055;
    static constexpr std::uint16_t message_id=280; // current SystemMessage row355
    static constexpr auto lifetime=std::chrono::seconds(60);
    struct Owner {
        std::uint64_t session_id{},account_id{},character_id{};
        bool ready{},in_battle{},transfer_pending{};
        std::optional<RecoveredPosition> position;
    };
    enum class Kind { Open,Select,Cancel };
    struct Operation {
        Kind kind{};
        std::uint8_t opcode{},slot{},destination{};
        std::uint16_t target{},context{};
        std::uint16_t raw_close_high_word{}; // Retained pointer residue, never authority.
    };
    struct Prepared {
        std::uint64_t token{};
        StoredTeleportGemSlot expected_item;
        RecoveredPosition expected_position;
    };

    // One operation and idle ticks only. The ordinary25 event has a native
    // trailing control dispatch; permit at most one1F00 after that25, not26.
    // Mixed mutations reject before open/select/cancel touches transient state.
    static std::optional<Operation> preflight(std::span<const RecoveredWorldRecords::Record> records) {
        if(records.empty() || records.size()>8192)return std::nullopt;
        std::optional<Operation> operation;
        bool control=false;
        for(const auto& record:records) {
            if(std::holds_alternative<RecoveredWorldRecords::Tick>(record))continue;
            if(std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(record)) {
                if(!operation || operation->kind!=Kind::Open || operation->opcode!=0x25 || control)
                    return std::nullopt;
                control=true;continue;
            }
            if(operation)return std::nullopt;
            if(const auto* request=std::get_if<RecoveredInventoryItemRequest::Request>(&record)) {
                if(request->client_item_id!=context || request->raw_slot>=30)return std::nullopt;
                operation=Operation{Kind::Open,0x25,request->raw_slot,0,0,context};
            } else if(const auto* targeted=std::get_if<RecoveredTargetItemRequest::Request>(&record)) {
                if(targeted->client_item_id!=context || targeted->raw_slot>=30)return std::nullopt;
                operation=Operation{Kind::Open,0x26,targeted->raw_slot,0,targeted->raw_target,context};
            } else if(const auto* selection=std::get_if<RecoveredTeleport::Selection>(&record)) {
                if(selection->opcode!=0x99 || selection->context!=context || selection->destination!=5)
                    return std::nullopt;
                operation=Operation{Kind::Select,0x99,0,selection->destination,0,selection->context};
            } else if(const auto* close=std::get_if<RecoveredQuestClose::Request>(&record)) {
                // Neither native word proves an actor identity. Preserve both;
                // CUSTOM-0057 cancellation only revokes this owner's offer.
                operation=Operation{Kind::Cancel,0x86,0,0,close->source_low_word,0,close->this_high_word};
            } else return std::nullopt;
        }
        return operation;
    }

    // Use this before generic world routing;86 belongs here only with an offer.
    bool claims(std::uint64_t session,std::span<const RecoveredWorldRecords::Record> records) const {
        for(const auto& record:records) {
            if(const auto* item=std::get_if<RecoveredInventoryItemRequest::Request>(&record);
               item && item->client_item_id==context)return true;
            if(const auto* item=std::get_if<RecoveredTargetItemRequest::Request>(&record);
               item && item->client_item_id==context)return true;
            if(const auto* selection=std::get_if<RecoveredTeleport::Selection>(&record);
               selection && selection->context==context)return true;
            if(pending_.contains(session) && std::holds_alternative<RecoveredQuestClose::Request>(record))return true;
        }
        return false;
    }

    std::optional<RecoveredTeleport::MenuBytes> open(const Owner& owner,const Operation& operation,
            const StoredTeleportGemSlot& item,Time now=Clock::now()) {
        if(operation.kind!=Kind::Open || (operation.opcode!=0x25 && operation.opcode!=0x26) ||
           operation.context!=context || !eligible(owner) || !valid_item(item) || operation.slot!=item.slot ||
           (operation.opcode==0x26 && operation.target!=owner.character_id) ||
           next_token_==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
        // Single source-qualified label5. Costs/context and no-currency policy
        // are CUSTOM-0057. Display level10 selects numeric zero cost; this does
        // not assert the actor's role level or the official free-level cutoff.
        RecoveredTeleport::Menu menu{context,message_id,0x81,0,10,0};
        menu.destinations[0]={5,0,0};
        const auto logical=RecoveredTeleport::encode(menu);
        if(!logical)return std::nullopt;
        Offer next{owner.account_id,owner.character_id,++next_token_,item,*owner.position,now,now+lifetime};
        pending_.insert_or_assign(owner.session_id,std::move(next));
        return logical;
    }

    std::optional<std::uint8_t> pending_slot(std::uint64_t session) const {
        const auto it=pending_.find(session);
        if(it==pending_.end())return std::nullopt;
        return it->second.item.slot;
    }

    std::optional<Prepared> select(const Owner& owner,const Operation& operation,
            const StoredTeleportGemSlot& current,Time now=Clock::now()) {
        const auto it=pending_.find(owner.session_id);
        if(it==pending_.end() || !same_owner(owner,it->second))return std::nullopt;
        const auto& offer=it->second;
        if(now<offer.opened || now>=offer.expires || !eligible(owner) ||
           *owner.position!=offer.position || current!=offer.item || !valid_item(current)) {
            pending_.erase(it);return std::nullopt;
        }
        if(operation.kind!=Kind::Select || operation.opcode!=0x99 || operation.context!=context ||
           operation.destination!=5)return std::nullopt;
        return Prepared{offer.token,offer.item,offer.position};
    }

    // Call only after atomic item/position commit, on the same serialized executor.
    // A failed preparation/transaction leaves a valid offer available for retry.
    bool committed(std::uint64_t session,std::uint64_t token) {
        const auto it=pending_.find(session);
        if(it==pending_.end() || it->second.token!=token)return false;
        pending_.erase(it);return true;
    }
    // CUSTOM-0057: an authenticated owner may revoke only its own transient
    // offer. Native86 words are opaque context, not actor IDs or permission.
    // The caller admits Cancel only after whole-batch preflight; no item debit,
    // movement, new offer or selection authority can result from this method.
    bool cancel(const Owner& owner,const Operation& operation,Time now=Clock::now()) {
        const auto it=pending_.find(owner.session_id);
        if(it==pending_.end() || !same_owner(owner,it->second) || operation.kind!=Kind::Cancel ||
           operation.opcode!=0x86)return false;
        const bool valid=now>=it->second.opened && now<it->second.expires;
        pending_.erase(it);return valid;
    }
    void forget(std::uint64_t session) { pending_.erase(session); }

private:
    struct Offer {
        std::uint64_t account{},character{},token{};
        StoredTeleportGemSlot item;
        RecoveredPosition position;
        Time opened{},expires{};
    };
    static bool same_owner(const Owner& owner,const Offer& offer) {
        return owner.account_id==offer.account && owner.character_id==offer.character;
    }
    static bool eligible(const Owner& owner) {
        return owner.session_id && owner.account_id && owner.character_id && owner.character_id<=65535 &&
            owner.ready && !owner.in_battle && !owner.transfer_pending && owner.position &&
            owner.position->area==2 && owner.position->scene==0 && owner.position->revision;
    }
    static bool valid_item(const StoredTeleportGemSlot& item) {
        return item.slot<30 && item.item_id==context && item.count==1 && item.revision &&
            item.metadata_present && RecoveredTeleportGem::displayed_charges(item.metadata20).has_value();
    }
    std::unordered_map<std::uint64_t,Offer> pending_;
    std::uint64_t next_token_{};
};
}
