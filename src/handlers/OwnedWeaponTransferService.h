#pragma once
#include "db/SqliteWeaponSlotRepository.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredInventory.h"
#include "protocol/RecoveredWorldRecords.h"
#include <algorithm>
#include <variant>
namespace god2 {
// CUSTOM-0046. Instance transfer/slot icons only; no original equipment-rule,
// appearance mapping or final-stat calculation is implied by this service.
class OwnedWeaponTransferService {
public:
    using Operation=std::variant<RecoveredSelectionItemRequest::Request,RecoveredInventoryMoveRequest::Request>;
    using PrepareExtra=std::function<std::vector<std::uint8_t>(const WeaponSlotMove&)>;
    struct Result {WeaponSlotMove state;std::vector<std::uint8_t> wire;bool changed;};
    explicit OwnedWeaponTransferService(SqliteWeaponSlotRepository& repository):repository_(repository){}
    static bool slot(std::uint8_t index){return index<30 || index==34;}
    static std::optional<Operation> request(std::span<const RecoveredWorldRecords::Record> records) {
        std::optional<Operation> result;
        for(std::size_t i=0;i<records.size();++i) {
            if(const auto* use=std::get_if<RecoveredSelectionItemRequest::Request>(&records[i])) {
                if(result || !slot(use->raw_slot))return std::nullopt;result=*use;
            } else if(const auto* move=std::get_if<RecoveredInventoryMoveRequest::Request>(&records[i])) {
                if(result || move->source_slot>=30 || move->destination_slot>=30)return std::nullopt;result=*move;
            } else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!result || i+1!=records.size() || !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return std::nullopt;
        }
        return result;
    }
    static std::vector<std::uint8_t> slot_logical(const StoredWeaponSlot& value) {
        validate(value);const auto clear=RecoveredInventory::clear_slot(value.slot).value();
        std::vector<std::uint8_t> bytes(clear.begin(),clear.end());append_occupied(bytes,value);return bytes;
    }
    static std::vector<std::uint8_t> pair_logical(const WeaponSlotMove& values) {
        validate(values.source);validate(values.destination);
        const auto a=RecoveredInventory::clear_slot(values.source.slot).value(),b=RecoveredInventory::clear_slot(values.destination.slot).value();
        std::vector<std::uint8_t> bytes(a.begin(),a.end());bytes.insert(bytes.end(),b.begin(),b.end());
        append_occupied(bytes,values.source);append_occupied(bytes,values.destination);return bytes;
    }
    std::optional<Result> select(std::uint64_t account,std::uint64_t character,const RecoveredSelectionItemRequest::Request& use,const PrepareExtra& extra={}) {
        if(!slot(use.raw_slot))return std::nullopt;
        const auto source=repository_.load(account,character,use.raw_slot);
        if(!source || source->count!=1 || source->item_id!=use.client_item_id)return std::nullopt;
        std::optional<StoredWeaponSlot> destination;
        if(use.raw_slot<30)destination=repository_.load(account,character,34);
        else {
            // Wire28 carries no destination. Lowest explicitly owned empty bag
            // cell is a named server policy, never inference from a missing row.
            const auto saved=repository_.load_saved(account,character);
            for(const auto& candidate:saved)if(candidate.slot<30 && !candidate.count &&
               (!destination || candidate.slot<destination->slot))destination=candidate;
        }
        if(!destination)return std::nullopt;
        return commit(account,character,*source,*destination,extra);
    }
    std::optional<Result> bag_move(std::uint64_t account,std::uint64_t character,const RecoveredInventoryMoveRequest::Request& request) {
        if(request.source_slot>=30 || request.destination_slot>=30)return std::nullopt;
        const auto source=repository_.load(account,character,request.source_slot),destination=repository_.load(account,character,request.destination_slot);
        if(!source || !destination)return std::nullopt;
        if(!source->count || request.source_slot==request.destination_slot) {
            WeaponSlotMove next{*source,*destination};return Result{next,RecoveredWorldFrame::encode(pair_logical(next)),false};
        }
        return commit(account,character,*source,*destination);
    }
private:
    static void validate(const StoredWeaponSlot& value) {
        const auto key=static_cast<std::uint16_t>(value.logical20[0]+256u*value.logical20[1]);
        if(!slot(value.slot) || !value.revision || value.count>1 || key!=value.item_id ||
           (value.count==0)!=(key==0) || (value.count && !value.metadata_present))throw DatabaseError("Invalid weapon projection");
    }
    static void append_occupied(std::vector<std::uint8_t>& bytes,const StoredWeaponSlot& value) {
        if(!value.count)return;
        bytes.insert(bytes.end(),{0x3b,1,value.slot,0,0});bytes.insert(bytes.end(),value.logical20.begin(),value.logical20.end());
        const auto absolute=RecoveredInventory::encode_slot_update({value.item_id,value.slot,1}).value();bytes.insert(bytes.end(),absolute.begin(),absolute.end());
    }
    Result commit(std::uint64_t account,std::uint64_t character,const StoredWeaponSlot& source,const StoredWeaponSlot& destination,const PrepareExtra& extra={}) {
        std::vector<std::uint8_t> wire;
        const auto next=repository_.move(account,character,source,destination,[&](const WeaponSlotMove& proposed) {
            auto logical=pair_logical(proposed);
            if(extra) { const auto appended=extra(proposed);logical.insert(logical.end(),appended.begin(),appended.end()); }
            wire=RecoveredWorldFrame::encode(logical);
        });
        return {next,std::move(wire),true};
    }
    SqliteWeaponSlotRepository& repository_;
};
}
