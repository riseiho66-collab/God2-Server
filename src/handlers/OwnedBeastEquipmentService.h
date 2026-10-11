#pragma once
#include "db/SqliteBeastBagRepository.h"
#include "handlers/OwnedBagProjectionService.h"
#include "protocol/RecoveredWorldRecords.h"
#include "protocol/RecoveredBeastInventoryProjection.h"
#include "scripting/LuaEngine.h"
namespace god2 {
// CUSTOM-0085: actual owned28 -> Lua placement -> full-instance bag/37
// transaction ->3B/41. Does not claim original riding/stat/appearance effects.
class OwnedBeastEquipmentService {
public:
    OwnedBeastEquipmentService(SqliteBeastBagRepository& bag,OwnedBagProjectionService& projection,
        SqliteBeastSnapshotRepository& beasts,LuaEngine& lua):bag_(bag),projection_(projection),beasts_(beasts),lua_(lua){}
    static bool handles(std::span<const RecoveredWorldRecords::Record> records){
        for(const auto& record:records)if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&record))
            if(use->raw_slot==37||NativeBeastSourceCatalog::lookup(use->client_item_id))return true;
        return false;
    }
    static std::optional<RecoveredSelectionItemRequest::Request> request(std::span<const RecoveredWorldRecords::Record> records){
        std::optional<RecoveredSelectionItemRequest::Request> result;
        for(std::size_t i=0;i<records.size();++i){
            if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&records[i])){
                if(result||!RecoveredBeastInventoryProjection::domain(use->raw_slot)||!NativeBeastSourceCatalog::lookup(use->client_item_id))return {};
                result=*use;
            }else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!result||i+1!=records.size()||!std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return {};
        }
        return result;
    }
    std::optional<SqliteBeastBagRepository::Snapshot> capture(std::uint64_t account,std::uint64_t character,
        const RecoveredSelectionItemRequest::Request& use){
        const auto before=projection_.capture_proof(account,character).snapshot();
        const auto custody=beasts_.load_owned(account,character);
        if(!RecoveredBeastInventoryProjection::domain(use.raw_slot))return {};
        const auto& source=before.scalar[use.raw_slot];
        if(!source||source->count!=1||source->item_id!=use.client_item_id)return {};
        const auto instance=std::find_if(custody.begin(),custody.end(),[&](const auto& row){return row.inventory_slot==use.raw_slot;});
        if(instance==custody.end()||instance->panel.metadata_key()!=use.client_item_id)return {};
        std::vector<std::uint8_t> empty;
        for(std::uint8_t slot=0;slot<30;++slot)if(before.scalar[slot]&&!before.scalar[slot]->count)empty.push_back(slot);
        const auto destination=lua_.beast_equipment_destination(use.raw_slot,empty);if(!destination)return {};
        auto saved=bag_.capture(account,character,{use.raw_slot,*destination},SqliteBeastBagRepository::Domain::BeastEquipment);
        if(saved.bag!=before||saved.beasts!=custody)throw DatabaseError("Beast equipment rule snapshot changed during capture");
        return saved;
    }
private:
    SqliteBeastBagRepository& bag_;OwnedBagProjectionService& projection_;
    SqliteBeastSnapshotRepository& beasts_;LuaEngine& lua_;
};
}
