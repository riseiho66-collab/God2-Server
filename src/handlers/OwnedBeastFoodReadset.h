#pragma once
#include "db/NativePfdSourceCatalog.h"
#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteBeastSnapshotRepository.h"
#include "db/SqliteSupport.h"
#include "handlers/OwnedBagProjectionService.h"
#include "protocol/RecoveredWorldRecords.h"
#include <optional>
#include <span>
#include <string_view>

namespace god2 {
// Source-stage readset for C2S6B lane0. This makes no gameplay decision and
// must never be wired as an accepting handler: PFD membership includes special
// transformation rows and does not define food eligibility or effects.
// A future writer must recapture/compare the entire saved owner state inside
// its mutation transaction before consuming an item or changing beast bytes.
class OwnedBeastFoodReadset {
public:
    using Request=RecoveredCompanionControl6B::Request;
    struct Candidate {
        Request request;
        ArmorSnapshot bag;
        SqliteBeastSnapshotRepository::Selected selected;
        SqliteBeastSnapshotRepository::SelectionRecord selection;
        StoredInventorySlot food;
        std::uint16_t pfd_key{};
    };
    static std::optional<Request> request(std::span<const RecoveredWorldRecords::Record> records) {
        std::optional<Request> chosen;
        for(std::size_t i=0;i<records.size();++i){
            if(const auto* value=std::get_if<Request>(&records[i])){
                if(chosen||value->lane!=0)return {};
                chosen=*value;
            }else if(std::holds_alternative<RecoveredWorldRecords::Tick>(records[i]))continue;
            else if(!chosen||i+1!=records.size()||
                    !std::holds_alternative<RecoveredWorldRecords::ClientControl1F>(records[i]))return {};
        }
        return chosen;
    }
    static std::optional<Candidate> inspect(const Request& use,const ArmorSnapshot& bag,
        const std::optional<SqliteBeastSnapshotRepository::Selected>& selected,
        const std::optional<SqliteBeastSnapshotRepository::SelectionRecord>& selection){
        if(use.lane!=0||use.inventory_slot>=30||!selected||!selection||
           bag.account!=selected->instance.account||bag.character!=selected->instance.character||
           selected->instance.panel.selector()!=use.selector||
           selection->selector!=use.selector||
           selection->custody_revision!=selected->instance.revision||
           selection->revision!=selected->revision)return {};
        const auto& food=bag.scalar[use.inventory_slot];
        if(!food||!food->count||std::string_view(food->source_sha256)!=NativePfdSourceCatalog::source_sha256||
           !NativePfdSourceCatalog::lookup(food->item_id))return {};
        const auto beast_slot=selected->instance.inventory_slot;
        if(beast_slot>=bag.scalar.size()||beast_slot==use.inventory_slot||
           !bag.scalar[beast_slot]||bag.scalar[beast_slot]->count!=1||
           bag.scalar[beast_slot]->item_id!=selected->instance.panel.metadata_key()||
           bag.scalar[beast_slot]->revision!=selected->instance.bag_revision)return {};
        return Candidate{use,bag,*selected,*selection,*food,food->item_id};
    }
    OwnedBeastFoodReadset(sqlite3* db,OwnedBagProjectionService& bag,
        SqliteBeastSnapshotRepository& beasts):db_(db),bag_(bag),beasts_(beasts){
        if(!db_||!bag_.shares_connection(db_)||!beasts_.shares_connection(db_))
            throw DatabaseError("Beast food readset requires one managed owner connection");
    }
    // Capture the full owner bag and selected custody in one SQLite read
    // transaction. This is a candidate only: a future writer must compare
    // the complete readset under its mutation transaction before any effect.
    std::optional<Candidate> capture(std::uint64_t account,std::uint64_t character,
        const Request& use){
        if(use.lane!=0||use.inventory_slot>=30)return {};
        if(sqlite3_get_autocommit(db_)==0)
            throw DatabaseError("Beast food readset requires standalone read transaction");
        sqlite_detail::execute(db_,"BEGIN");
        struct End {
            sqlite3* db;
            bool done=false;
            ~End(){if(!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
        } end{db_};
        const auto bag=bag_.capture_proof(account,character).snapshot();
        const auto selected=beasts_.load_selected(account,character);
        const auto selection=beasts_.load_selection_record(account,character);
        auto result=inspect(use,bag,selected,selection);
        sqlite_detail::execute(db_,"COMMIT");
        end.done=true;
        return result;
    }
private:
    sqlite3* db_;
    OwnedBagProjectionService& bag_;
    SqliteBeastSnapshotRepository& beasts_;
};
}
