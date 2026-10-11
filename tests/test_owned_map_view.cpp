#include "handlers/RecoveredOwnedMapView.h"
#include "db/NativeMapItemCatalog.h"
#include "db/SqliteSupport.h"
#include <sqlite3.h>
#include <iostream>
#include <stdexcept>
using namespace god2;
namespace {unsigned checks=0;void check(bool yes){++checks;if(!yes)throw std::runtime_error("Owned map view contract failed");}}
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    sqlite3* db=nullptr;
    if(sqlite3_open_v2(argv[1],&db,SQLITE_OPEN_READONLY,nullptr)!=SQLITE_OK){sqlite3_close(db);return 3;}
    int result=0;
    try {
        NativeMapCatalog maps(db);NativeMapItemCatalog items(db);
        check(items.populated());check(items.contains(5569));check(items.contains(5576));check(!items.contains(5577));
        {
            sqlite_detail::Statement owner(db,"SELECT id,account_id FROM recovered_characters ORDER BY id LIMIT 1");
            check(owner.row());SqliteRecoveredCharacterRepository repository(db);
            const auto character=owner.number<std::uint64_t>(0),account=owner.number<std::uint64_t>(1);
            (void)repository.load_inventory_slot(account,character,0);
            bool rejected=false;try{(void)repository.load_inventory_slot(account+1,character,0);}catch(const DatabaseError&){rejected=true;}
            check(rejected);
        }
        for(const auto item:{5569,5576}) {
            const auto map=maps.lookup(NativeMapCatalog::current_dataset_id,item==5576?4:2,item==5576?3:4);
            check(map.has_value());check(RecoveredOwnedMapView::qualified_map(*map,static_cast<std::uint16_t>(item)));
            const StoredInventorySlot owned{static_cast<std::uint16_t>(item),1,3,std::string(RecoveredOwnedMapView::source_sha)};
            for(unsigned tail=0;tail<256;++tail) {
                const RecoveredInventoryItemRequest::Request use{static_cast<std::uint16_t>(item),0,static_cast<std::uint8_t>(tail)};
                check(RecoveredOwnedMapView::logical(use,owned,*map,true)==std::optional(std::vector<std::uint8_t>{0x3f,1,0}));
                const std::vector<RecoveredWorldRecords::Record> records{RecoveredWorldRecords::Tick{},use,RecoveredWorldRecords::ClientControl1F{}};
                check(RecoveredOwnedMapView::request(records).has_value());
                check(!RecoveredOwnedMapView::request(std::vector<RecoveredWorldRecords::Record>{use,use}));
                check(!RecoveredOwnedMapView::request(std::vector<RecoveredWorldRecords::Record>{use,RecoveredWorldRecords::ClientControl1F{},RecoveredWorldRecords::Tick{}}));
                check(!RecoveredOwnedMapView::logical(use,owned,*map,false));
            }
            RecoveredInventoryItemRequest::Request use{static_cast<std::uint16_t>(item),0,0};
            for(unsigned slot=30;slot<256;++slot){use.raw_slot=static_cast<std::uint8_t>(slot);check(!RecoveredOwnedMapView::logical(use,owned,*map,true));}
            use.raw_slot=0;
            for(unsigned count=0;count<128;++count)if(count!=1){auto bad=owned;bad.count=static_cast<std::uint8_t>(count);check(!RecoveredOwnedMapView::logical(use,bad,*map,true));}
            auto bad=owned;bad.revision=0;check(!RecoveredOwnedMapView::logical(use,bad,*map,true));
            bad=owned;bad.item_id=static_cast<std::uint16_t>(item==5576?5569:5576);check(!RecoveredOwnedMapView::logical(use,bad,*map,true));
            bad=owned;bad.source_sha256[0]='0';check(!RecoveredOwnedMapView::logical(use,bad,*map,true));
            auto altered=*map;altered.raw_record[0]^=1;check(!RecoveredOwnedMapView::logical(use,owned,altered,true));
            altered=*map;altered.kind=1;check(!RecoveredOwnedMapView::logical(use,owned,altered,true));
            altered=*map;altered.source.source_sha256[0]='0';check(!RecoveredOwnedMapView::logical(use,owned,altered,true));
            altered=*map;altered.source_line++;check(!RecoveredOwnedMapView::logical(use,owned,altered,true));
            const auto wrong=maps.lookup(NativeMapCatalog::current_dataset_id,item==5576?2:4,item==5576?4:3);
            check(!RecoveredOwnedMapView::logical(use,owned,*wrong,true));
        }
        std::cout<<"PASS "<<checks<<" owned map source/frame/slot/tail checks\n";
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';result=1;}
    sqlite3_close(db);return result;
}
