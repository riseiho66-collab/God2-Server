#pragma once
#include "db/SqliteArmorSlotRepository.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredInventory.h"
#include "protocol/RecoveredArmorInstance.h"
#include "protocol/RecoveredWorldRecords.h"
#include <algorithm>
#include <utility>
#include <variant>

namespace god2 {
// CUSTOM-0066: separate full-instance armor28/bag24 route. No stats, appearance,
// acquisition, banker/trade category expansion or native equip-rule claim.
class OwnedArmorTransferService {
public:
    using Operation=std::variant<RecoveredSelectionItemRequest::Request,RecoveredInventoryMoveRequest::Request>;
    using PrepareExtra=std::function<std::vector<std::uint8_t>(const ArmorSlotMove&)>;
    struct Result{ArmorSlotMove state;std::vector<std::uint8_t> wire;bool changed;};
    explicit OwnedArmorTransferService(SqliteArmorSlotRepository& repository):repository_(repository){}
    static bool slot(std::uint8_t value){return value<34;}
    // Structural preflight only; Application must distinguish owned armor from
    // existing bag weapon/pet/MED routes before selecting this service.
    static std::optional<Operation> request(std::span<const RecoveredWorldRecords::Record> records){
        std::optional<Operation> result;
        for(std::size_t i=0;i<records.size();++i){
            if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&records[i])){if(result||!slot(use->raw_slot))return {};result=*use;}
            else if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&records[i])){if(result||move->source_slot>=30||move->destination_slot>=30)return {};result=*move;}
            else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!result||i+1!=records.size()||!std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return {};
        }
        return result;
    }
    static std::vector<std::uint8_t> slot_logical(const StoredArmorSlot& row){
        validate(row);const auto clear=RecoveredInventory::clear_slot(row.slot).value();std::vector<std::uint8_t> out(clear.begin(),clear.end());append(out,row);return out;
    }
    static std::vector<std::uint8_t> pair_logical(const ArmorSlotMove& next){
        validate(next.source);validate(next.destination);
        const auto a=RecoveredInventory::clear_slot(next.source.slot).value(),b=RecoveredInventory::clear_slot(next.destination.slot).value();
        std::vector<std::uint8_t> out(a.begin(),a.end());out.insert(out.end(),b.begin(),b.end());append(out,next.source);append(out,next.destination);return out;
    }
    std::optional<Result> select(std::uint64_t account,std::uint64_t character,const RecoveredSelectionItemRequest::Request& use,const PrepareExtra& extra={}){
        if(!slot(use.raw_slot))return {};auto saved=repository_.load_snapshot(account,character);const auto source=repository_.inspect(saved,use.raw_slot);
        if(!source||source->count!=1||source->item_id!=use.client_item_id)return {};
        std::optional<std::uint8_t> destination;
        if(use.raw_slot<30)destination=repository_.target(source->item_id);
        else{
            // Explicit custom lowest-owned-empty selection; wire28 has no
            // destination. Missing bag rows cannot become free capacity.
            for(std::uint8_t index=0;index<30;++index){const auto candidate=repository_.inspect(saved,index);if(candidate&&!candidate->count){destination=index;break;}}
        }
        if(!destination||!repository_.inspect(saved,*destination))return {};
        return commit(saved,use.raw_slot,*destination,extra);
    }
    std::optional<Result> bag_move(std::uint64_t account,std::uint64_t character,const RecoveredInventoryMoveRequest::Request& use){
        if(use.source_slot>=30||use.destination_slot>=30)return {};
        auto saved=repository_.load_snapshot(account,character);const auto source=repository_.inspect(saved,use.source_slot),destination=repository_.inspect(saved,use.destination_slot);
        if(!source||!destination)return {};
        if(!source->count||use.source_slot==use.destination_slot){ArmorSlotMove next{*source,*destination,std::move(saved)};return Result{next,RecoveredWorldFrame::encode(pair_logical(next)),false};}
        return commit(saved,use.source_slot,use.destination_slot,{});
    }
private:
    static void validate(const StoredArmorSlot& row){
        const auto key=static_cast<std::uint16_t>(row.logical20[0]|(std::uint16_t{row.logical20[1]}<<8));
        if(!slot(row.slot)||!row.revision||row.count>1||((row.count==0)!=(row.item_id==0))||
            (row.count&&(!row.metadata_present||key!=row.item_id||!RecoveredArmorInstance::armor_family(row.logical20)))||(!row.count&&row.metadata_present))throw DatabaseError("Invalid armor projection");
    }
    static void append(std::vector<std::uint8_t>& out,const StoredArmorSlot& row){
        if(!row.count)return;out.insert(out.end(),{0x3b,1,row.slot,0,0});out.insert(out.end(),row.logical20.begin(),row.logical20.end());
        const auto absolute=RecoveredInventory::encode_slot_update({row.item_id,row.slot,1}).value();out.insert(out.end(),absolute.begin(),absolute.end());
    }
    Result commit(const ArmorSnapshot& saved,std::uint8_t source,std::uint8_t destination,const PrepareExtra& extra){
        std::vector<std::uint8_t> wire;auto state=repository_.move(saved,source,destination,[&](const auto& next){auto logical=pair_logical(next);if(extra){const auto more=extra(next);logical.insert(logical.end(),more.begin(),more.end());}wire=RecoveredWorldFrame::encode(logical);});
        return {std::move(state),std::move(wire),true};
    }
    SqliteArmorSlotRepository& repository_;
};
}
