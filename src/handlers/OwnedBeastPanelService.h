#pragma once
#include "db/NativeBeastSourceCatalog.h"
#include "protocol/RecoveredWorldRecords.h"
#include "protocol/RecoveredBeastInventoryProjection.h"
namespace god2 {
// CUSTOM-0085: presentation of separately acquired, exact owned PET snapshots.
// Native963C0 forces25 for quotient53/55; the separate9A330 same-slot
// release route (9AA07) also sends25 for PET quotients52/53/54. Source PET
// membership remains mandatory: this never claims all SPI55xx are beasts.
// CUSTOM selection is persisted by the repository; no activity authority is
// inferred from it. This policy never interprets opaque25 tail as quantity or privilege and
// never treats panel opening as ride/food/teleport/exploration authorization.
struct OwnedBeastPanelService {
    static bool supported(std::uint16_t key) noexcept {
        const auto group=key/100;
        return (group==52||group==53||group==54||group==55)&&NativeBeastSourceCatalog::lookup(key);
    }
    static bool handles(std::span<const RecoveredWorldRecords::Record> records) {
        for(const auto& record:records)
            if(const auto* use=std::get_if<RecoveredInventoryItemRequest::Request>(&record))
                if(supported(use->client_item_id))return true;
        return false;
    }
    // Entire original frame before callbacks: exactly one use, ticks and an
    // optional final1F. No mixed mutation/prefix can establish new authority.
    static std::optional<RecoveredInventoryItemRequest::Request> request(
        std::span<const RecoveredWorldRecords::Record> records) {
        std::optional<RecoveredInventoryItemRequest::Request> selected;
        for(std::size_t i=0;i<records.size();++i){
            if(const auto* use=std::get_if<RecoveredInventoryItemRequest::Request>(&records[i])){
                if(selected||!supported(use->client_item_id)||!RecoveredBeastInventoryProjection::domain(use->raw_slot))return {};
                selected=*use;
            } else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!selected||i+1!=records.size()||
                !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return {};
        }
        return selected;
    }
};
}
