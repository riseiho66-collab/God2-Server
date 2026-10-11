#pragma once
#include "protocol/RecoveredWorldRecords.h"
namespace god2 {
// CUSTOM-0050: one owned self-player non-revival supply action per frame.
// Amounts come from pinned MED02 declarations; caps/debit remain CUSTOM-0016.
struct RecoveredOwnedSupply {
    static std::optional<RecoveredTargetItemRequest::Request> request(std::span<const RecoveredWorldRecords::Record> records) {
        std::optional<RecoveredTargetItemRequest::Request> value;
        for(std::size_t i=0;i<records.size();++i) {
            if(const auto* use=std::get_if<RecoveredTargetItemRequest::Request>(&records[i])) {
                if(value || use->raw_slot>=30)return std::nullopt;value=*use;
            } else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!value || i+1!=records.size() || !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return std::nullopt;
        }
        return value;
    }
};
}
