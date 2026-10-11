#pragma once
#include "db/SqliteBeastBagRepository.h"
#include "protocol/RecoveredWorldRecords.h"
#include "scripting/LuaEngine.h"
#include <functional>

namespace god2 {
// CUSTOM-0085 native27 -> owned full PET -> Lua eligibility -> atomic
// custody/selection destruction and full journal -> native4B/41 presentation.
// This is a real source route, not recovery of original bind/drop rules.
class OwnedBeastDiscardService {
public:
    using Receipt=std::function<std::string()>;
    struct Prepared {
        SqliteBeastBagRepository::Snapshot expected;
        RecoveredInventoryDiscard::Request use;
        std::string receipt;
    };
    OwnedBeastDiscardService(SqliteBeastBagRepository& bag,LuaEngine& lua,Receipt receipt)
        :bag_(bag),lua_(lua),receipt_(std::move(receipt)){
        if(!receipt_)throw DatabaseError("Beast discard requires fresh journal keys");
    }
    static std::optional<RecoveredInventoryDiscard::Request> request(std::span<const RecoveredWorldRecords::Record> records){
        std::optional<RecoveredInventoryDiscard::Request> use;
        for(std::size_t i=0;i<records.size();++i){
            if(const auto* discard=std::get_if<RecoveredInventoryDiscard::Request>(&records[i])){
                if(use||discard->slot>=30||discard->quantity!=1||!NativeBeastSourceCatalog::lookup(discard->item))return {};
                use=*discard;
            }else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!use||i+1!=records.size()||!std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return {};
        }
        return use;
    }
    std::optional<Prepared> capture(std::uint64_t account,std::uint64_t character,const RecoveredInventoryDiscard::Request& use){
        if(use.slot>=30||use.quantity!=1||!NativeBeastSourceCatalog::lookup(use.item))return {};
        auto saved=bag_.capture(account,character,{use.slot,use.slot});
        if(!eligible(saved,use))return {};
        const auto found=std::find_if(saved.beasts.begin(),saved.beasts.end(),[&](const auto& row){return row.inventory_slot==use.slot;});
        const auto fields=found->inventory_fields();
        if(!lua_.beast_discard_allowed(use.slot,use.quantity,fields->native_exploring_label(),
            found->panel.control7_alternate(),found->panel.control8_alternate()))return {};
        return Prepared{std::move(saved),use,receipt_()};
    }
    SqliteBeastBagRepository::Result commit(const Prepared& prepared){
        if(!eligible(prepared.expected,prepared.use))throw DatabaseError("Beast discard captured policy domain rejected");
        return bag_.discard(prepared.expected,prepared.use,prepared.receipt);
    }
private:
    static bool eligible(const SqliteBeastBagRepository::Snapshot& saved,const RecoveredInventoryDiscard::Request& use){
        if(use.slot>=30||use.quantity!=1||!saved.bag.scalar[use.slot]||
           saved.bag.scalar[use.slot]->item_id!=use.item||saved.bag.scalar[use.slot]->count!=1)return false;
        const auto found=std::find_if(saved.beasts.begin(),saved.beasts.end(),[&](const auto& row){return row.inventory_slot==use.slot;});
        if(found==saved.beasts.end()||found->panel.metadata_key()!=use.item)return false;
        const auto fields=found->inventory_fields();
        return fields&&!fields->native_exploring_label()&&!found->panel.control7_alternate()&&!found->panel.control8_alternate();
    }
    SqliteBeastBagRepository& bag_;LuaEngine& lua_;Receipt receipt_;
};
}
