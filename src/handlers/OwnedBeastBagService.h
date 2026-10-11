#pragma once
#include "protocol/RecoveredWorldRecords.h"
namespace god2 {
// CUSTOM-0085 exact whole-frame native24 admission; ownership/custody belongs
// to the managed repository, not to slot numbers supplied by the client.
struct OwnedBeastBagService {
    static std::optional<RecoveredInventoryMoveRequest::Request> request(std::span<const RecoveredWorldRecords::Record> records){
        std::optional<RecoveredInventoryMoveRequest::Request> use;
        for(std::size_t i=0;i<records.size();++i){
            if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&records[i])){
                if(use||move->source_slot>=30||move->destination_slot>=30)return {};use=*move;
            } else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!use||i+1!=records.size()||!std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return {};
        }
        return use;
    }
};
}
