#include "db/SqliteOwnedInstanceTradeRepository.h"
#include "db/SqliteSupport.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "protocol/RecoveredArmorInstance.h"
#include "protocol/RecoveredTeleportGem.h"
#include <algorithm>
#include <limits>
#include <map>
#include <nlohmann/json.hpp>
#include <set>
#include <type_traits>
#include <utility>
#include <bit>
#include <cstring>
#include <memory>
#include <initializer_list>

namespace god2 {
namespace {
constexpr auto max_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool ok,const char* why){if(!ok)throw DatabaseError(why);}
bool hash(const std::string& value){return value.size()==64&&value.find_first_not_of("0123456789abcdef")==std::string::npos;}
bool evidence(const std::string& value){return !value.empty()&&value.size()<=512&&value.find('\0')==std::string::npos;}
bool origin(const std::string& value){return value=="NATIVE_CAPTURE_VERIFIED"||value=="CUSTOM_TEST_NOT_NATIVE";}
std::uint16_t key(const std::array<std::uint8_t,20>& value){return static_cast<std::uint16_t>(value[0]|(std::uint16_t{value[1]}<<8));}
template<class T>const T* row(const std::vector<T>& rows,std::uint8_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& value){return value.slot==slot;});return found==rows.end()?nullptr:&*found;}
template<class T>void sort(std::vector<T>& rows){std::sort(rows.begin(),rows.end(),[](const auto& a,const auto& b){return a.slot<b.slot;});}
const StoredBeastSnapshot* beast_at(const std::vector<StoredBeastSnapshot>& rows,std::uint8_t slot){
    const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& value){return value.inventory_slot==slot;});return found==rows.end()?nullptr:&*found;
}
// Additional typed preservation consumer only for the opt-in0085 route.
#include "../relations53/preservation.inc"
void beast_trade_shape(sqlite3* db){
    const auto columns=[&](const char* table,std::initializer_list<const char*> wanted){
        sqlite_detail::Statement q(db,("PRAGMA table_info("+quoted(table)+")").c_str());
        std::vector<std::string> actual,expected;while(q.row())actual.push_back(q.text(1));for(const auto* value:wanted)expected.emplace_back(value);
        require(actual==expected,"PET trade affected table has unsupported opaque columns");
    };
    columns("diagnostic_inventory_slots",{"character_id","slot","item_id","count","revision","source_sha256","design_id"});
    columns("character_trade_wallets",{"character_id","amount","revision","design_id"});
    columns("character_armor_slot_metadata",{"character_id","slot","logical20","revision","origin","provenance","source_sha256","client_sha256","design_id"});
    columns("character_weapon_slot_metadata",{"character_id","slot","logical20","revision","origin","provenance","source_sha256","client_sha256","design_id"});
    columns("character_teleport_gem_metadata",{"character_id","slot","metadata20","revision","origin","provenance","source_sha256","design_id"});
    SqliteBeastSnapshotRepository::require_schema(db);
}
void erase_beast(sqlite3* db,const StoredBeastSnapshot& value){
    sqlite_detail::Statement q(db,"DELETE FROM character_beast_snapshot_custody WHERE character_id=? AND inventory_slot=? AND selector=? AND bag_revision=? AND inventory_metadata=? AND panel4c=? AND COALESCE(explorationc5,X'')=? AND revision=? AND origin=? AND evidence_id=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0085'");
    q.bind_id(1,value.character);q.bind(2,value.inventory_slot);q.bind(3,value.panel.selector());q.bind_id(4,value.bag_revision);q.bind_blob(5,value.inventory_metadata);q.bind_blob(6,value.panel.bytes);
    if(value.exploration)q.bind_blob(7,value.exploration->bytes);else q.bind_blob(7,std::span<const std::uint8_t>{});
    q.bind_id(8,value.revision);q.bind(9,value.origin);q.bind(10,value.evidence_id);q.bind(11,std::string(NativeBeastSourceCatalog::source_sha256));q.bind(12,std::string(SqliteBeastSnapshotRepository::client_sha256));q.done();require(sqlite3_changes(db)==1,"PET trade full custody delete CAS failed");
}
void put_beast(sqlite3* db,const StoredBeastSnapshot& value){
    sqlite_detail::Statement q(db,"INSERT INTO character_beast_snapshot_custody VALUES(?,?,?,?,?,?,NULLIF(?,X''),?,?,?,?,?,?)");
    q.bind_id(1,value.character);q.bind(2,value.inventory_slot);q.bind(3,value.panel.selector());q.bind_id(4,value.bag_revision);q.bind_blob(5,value.inventory_metadata);q.bind_blob(6,value.panel.bytes);
    if(value.exploration)q.bind_blob(7,value.exploration->bytes);else q.bind_blob(7,std::span<const std::uint8_t>{});
    q.bind_id(8,value.revision);q.bind(9,value.origin);q.bind(10,value.evidence_id);q.bind(11,std::string(NativeBeastSourceCatalog::source_sha256));q.bind(12,std::string(SqliteBeastSnapshotRepository::client_sha256));q.bind(13,std::string(SqliteBeastSnapshotRepository::design_id));q.done();require(sqlite3_changes(db)==1,"PET trade target custody insertion failed");
}
void clear(ArmorSnapshot& bag,std::uint8_t slot){
    std::erase_if(bag.armor,[&](const auto& value){return value.slot==slot;});
    std::erase_if(bag.weapons,[&](const auto& value){return value.slot==slot;});
    std::erase_if(bag.gems,[&](const auto& value){return value.slot==slot;});
}
struct ReadScope {
    sqlite3* db;bool owns,done=false;
    explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owns&&!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");done=true;}
};
using Repo=SqliteOwnedInstanceTradeRepository;
std::string state(const std::array<Repo::Snapshot,2>& sides){
    using J=nlohmann::json;J out=J::array();
    for(const auto& side:sides){
        const auto& bag=side.bag;J scalar=J::array(),armor=J::array(),weapons=J::array(),gems=J::array();
        for(const auto& value:bag.scalar)scalar.push_back(value?J::array({value->item_id,value->count,value->revision,value->source_sha256}):J(nullptr));
        for(const auto& value:bag.armor)armor.push_back(J::array({value.slot,value.item_id,value.count,value.revision,value.logical20,value.origin,value.provenance,value.metadata_present,SqliteArmorSlotRepository::source_sha256,SqliteArmorSlotRepository::client_sha256,SqliteArmorSlotRepository::design_id}));
        const auto foreign=[](const auto& value){return J::array({value.slot,value.logical20,value.revision,value.origin,value.provenance,value.source_sha256,value.client_sha256,value.design_id});};
        for(const auto& value:bag.weapons)weapons.push_back(foreign(value));for(const auto& value:bag.gems)gems.push_back(foreign(value));
        auto record=J::array({bag.account,bag.character,side.wallet.amount,side.wallet.revision,scalar,armor,weapons,gems});
        if(side.beast_scope){
            J beasts=J::array(),selection=nullptr;
            for(const auto& value:side.beasts){J item=J::array({value.account,value.character,value.inventory_slot,value.bag_revision,value.revision,value.inventory_metadata,value.panel.bytes,nullptr,value.origin,value.evidence_id,"CUSTOM-0085",std::string(NativeBeastSourceCatalog::source_sha256),std::string(SqliteBeastSnapshotRepository::client_sha256)});if(value.exploration)item[7]=value.exploration->bytes;beasts.push_back(std::move(item));}
            if(side.beast_selection)selection=J::array({side.beast_selection->selector,side.beast_selection->custody_revision,side.beast_selection->revision});
            record.push_back(J::array({"CUSTOM-0085_PET_SCOPE",beasts,selection}));
        }
        out.push_back(std::move(record));
    }
    return out.dump();
}
std::string offers(const std::array<Repo::Side,2>& sides,const Repo::Plan& next){
    using J=nlohmann::json;J out=J::array(),transfers=J::array();
    for(const auto& side:sides){J items=J::array();for(const auto& value:side.items)items.push_back(J::array({value.slot,value.quantity}));out.push_back(J::array({side.expected.bag.account,side.expected.bag.character,side.money,items}));}
    for(const auto& value:next.transfers)transfers.push_back(J::array({value.from_side,value.source,value.to_side,value.destination,value.quantity}));out.push_back(transfers);return out.dump();
}
void erase_armor(sqlite3* db,std::uint64_t character,const StoredArmorSlot& value){
    sqlite_detail::Statement erase(db,"DELETE FROM character_armor_slot_metadata WHERE character_id=? AND slot=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0066'");
    erase.bind_id(1,character);erase.bind(2,value.slot);erase.bind_blob(3,value.logical20);erase.bind_id(4,value.revision);erase.bind(5,value.origin);erase.bind(6,value.provenance);erase.bind(7,SqliteArmorSlotRepository::source_sha256);erase.bind(8,SqliteArmorSlotRepository::client_sha256);erase.done();require(sqlite3_changes(db)==1,"Owned trade armor delete CAS failed");
}
void erase_foreign(sqlite3* db,std::uint64_t character,const ArmorForeignOverlay& value,bool weapon){
    sqlite_detail::Statement erase(db,weapon?
        "DELETE FROM character_weapon_slot_metadata WHERE character_id=? AND slot=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0046'":
        "DELETE FROM character_teleport_gem_metadata WHERE character_id=? AND slot=? AND metadata20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND design_id='CUSTOM-0057'");
    erase.bind_id(1,character);erase.bind(2,value.slot);erase.bind_blob(3,value.logical20);erase.bind_id(4,value.revision);erase.bind(5,value.origin);erase.bind(6,value.provenance);erase.bind(7,value.source_sha256);if(weapon)erase.bind(8,value.client_sha256);erase.done();require(sqlite3_changes(db)==1,"Owned trade foreign delete CAS failed");
}
void put_armor(sqlite3* db,std::uint64_t character,const StoredArmorSlot& value){
    sqlite_detail::Statement insert(db,"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,?,?,?,?,?, 'CUSTOM-0066')");insert.bind_id(1,character);insert.bind(2,value.slot);insert.bind_blob(3,value.logical20);insert.bind_id(4,value.revision);insert.bind(5,value.origin);insert.bind(6,value.provenance);insert.bind(7,SqliteArmorSlotRepository::source_sha256);insert.bind(8,SqliteArmorSlotRepository::client_sha256);insert.done();require(sqlite3_changes(db)==1,"Owned trade armor install failed");
}
void put_foreign(sqlite3* db,std::uint64_t character,const ArmorForeignOverlay& value,bool weapon){
    sqlite_detail::Statement insert(db,weapon?"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,?,?,?,?,?, 'CUSTOM-0046')":"INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,?,?,?,?,'CUSTOM-0057')");insert.bind_id(1,character);insert.bind(2,value.slot);insert.bind_blob(3,value.logical20);insert.bind_id(4,value.revision);insert.bind(5,value.origin);insert.bind(6,value.provenance);insert.bind(7,value.source_sha256);if(weapon)insert.bind(8,value.client_sha256);insert.done();require(sqlite3_changes(db)==1,"Owned trade foreign install failed");
}
}

std::string SqliteOwnedInstanceTradeRepository::schema(){return R"SQL(
CREATE TABLE character_owned_instance_trade_receipts(
 receipt TEXT PRIMARY KEY CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 first_account INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 first_character INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 second_account INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 second_character INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 before_state TEXT NOT NULL CHECK(typeof(before_state)='text' AND length(before_state)>0),
 after_state TEXT NOT NULL CHECK(typeof(after_state)='text' AND length(after_state)>0),
 offers_state TEXT NOT NULL CHECK(typeof(offers_state)='text' AND length(offers_state)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0069'),CHECK(first_character<>second_character)
);
)SQL";}
SqliteOwnedInstanceTradeRepository::SqliteOwnedInstanceTradeRepository(sqlite3* db,QualifyArmor armor,QualifyInstance instance,LookupWeapon weapon,EligiblePlain plain,SqliteBeastSnapshotRepository* beasts):db_(db),armor_(std::move(armor)),armor_instance_(std::move(instance)),weapon_(std::move(weapon)),plain_(std::move(plain)),beasts_(beasts){
    require(!beasts_||beasts_->shares_connection(db_),"PET trade custody must share writer connection");
    require(db_&&bool(armor_)&&bool(armor_instance_)&&bool(weapon_)&&bool(plain_),"Owned trade requires complete native qualifiers");
}
void SqliteOwnedInstanceTradeRepository::validate(const Snapshot& saved) const{
    const auto& bag=saved.bag;
    require(saved.beast_scope==(beasts_!=nullptr)&&(!beasts_?(saved.beasts.empty()&&!saved.beast_selection):true),"Owned trade PET feature scope mismatch");
    require(bag.account&&bag.account<=max_revision&&bag.character&&bag.character<=max_revision&&saved.wallet.revision&&saved.wallet.revision<=max_revision&&ExtendedCoinAmount::from(saved.wallet.amount).has_value(),"Owned trade owner/wallet invalid");
    for(std::size_t slot=0;slot<50;++slot){const auto& value=bag.scalar[slot];require(slot>=30||value.has_value(),"Owned trade ordinary capacity missing");if(value)require(value->revision&&value->revision<=max_revision&&value->count<=127&&((value->item_id==0)==(value->count==0))&&hash(value->source_sha256),"Owned trade scalar invalid");}
    std::uint8_t previous=0;bool first=true;
    for(const auto& value:bag.armor){
        require(value.slot<34&&(first||value.slot>previous),"Owned trade armor domain/order conflict");first=false;previous=value.slot;const auto& scalar=bag.scalar[value.slot];const auto part=armor_(value.item_id);
        require(scalar&&scalar->item_id==value.item_id&&scalar->count==1&&scalar->revision==value.revision&&scalar->source_sha256==SqliteArmorSlotRepository::source_sha256&&value.count==1&&value.metadata_present&&key(value.logical20)==value.item_id&&part&&*part>=30&&*part<=33&&(value.slot<30||value.slot==*part)&&!weapon_(value.item_id)&&value.item_id!=RecoveredTeleportGem::item_id&&RecoveredArmorInstance::armor_family(value.logical20)&&armor_instance_(value.item_id,value.logical20)&&origin(value.origin)&&evidence(value.provenance)&&!row(bag.weapons,value.slot)&&!row(bag.gems,value.slot),"Owned trade armor family/source/instance conflict");
    }
    const auto foreign=[&](const auto& values,bool weapon){
        std::uint8_t last=0;bool initial=true;
        for(const auto& value:values){
            require((weapon?(value.slot<30||value.slot==34):value.slot<30)&&(initial||value.slot>last),"Owned trade foreign domain/order conflict");initial=false;last=value.slot;
            const auto& scalar=bag.scalar[value.slot];require(scalar&&scalar->revision==value.revision&&scalar->item_id==key(value.logical20)&&scalar->source_sha256==value.source_sha256&&value.source_sha256==SqliteArmorSlotRepository::source_sha256&&evidence(value.provenance)&&!row(bag.armor,value.slot)&&!(weapon?row(bag.gems,value.slot):row(bag.weapons,value.slot)),"Owned trade foreign owner/scalar/overlay conflict");
            if(weapon)require(value.client_sha256==SqliteWeaponSlotRepository::client_sha256&&value.design_id=="CUSTOM-0046","Owned trade weapon pins conflict");
            else require(value.client_sha256.empty()&&value.design_id=="CUSTOM-0057","Owned trade gem pins conflict");
            if(!scalar->count){require(weapon&&value.origin=="EMPTY_SLOT_POLICY","Owned trade invalid empty overlay");continue;}
            require(scalar->count==1&&origin(value.origin)&&!armor_(scalar->item_id),"Owned trade foreign not whole/category conflict");
            const auto definition=weapon_(scalar->item_id);
            if(weapon)require(scalar->item_id!=RecoveredTeleportGem::item_id&&definition&&definition->item_id==scalar->item_id&&(definition->family=="WPN"||definition->family=="TWP")&&definition->parsed_record.size()==396&&(definition->parsed_record[0x11a]&4)!=0&&hash(definition->parsed_sha256)&&(value.logical20[2]&0x3fu)==(definition->family=="WPN"?1u:25u),"Owned trade weapon source definition/type conflict");
            else require(!definition&&scalar->item_id==RecoveredTeleportGem::item_id&&RecoveredTeleportGem::displayed_charges(value.logical20).has_value(),"Owned trade gem key/type/charges conflict");
        }
    };foreign(bag.weapons,true);foreign(bag.gems,false);
    std::array<bool,256> selectors{};std::uint8_t last_beast=0;bool initial_beast=true;
    for(const auto& value:saved.beasts){
        require((value.inventory_slot<30||value.inventory_slot==37)&&(initial_beast||value.inventory_slot>last_beast),"PET trade custody domain/order conflict");initial_beast=false;last_beast=value.inventory_slot;
        const auto& scalar=bag.scalar[value.inventory_slot];const auto fields=value.inventory_fields();
        const bool qualified_origin=value.origin=="NATIVE_OBSERVED"||value.origin=="NATIVE_VERIFIED"||value.origin=="CUSTOM_DESIGNED"||value.origin=="CUSTOM_TEST_NOT_NATIVE";
        require(value.account==bag.account&&value.character==bag.character&&value.revision&&value.revision<=max_revision&&
            fields&&RecoveredBeastPanel::decode_snapshot(value.panel.bytes)&&fields->key()==value.panel.metadata_key()&&scalar&&scalar->item_id==fields->key()&&scalar->count==1&&
            scalar->revision==value.bag_revision&&scalar->source_sha256==NativeBeastSourceCatalog::source_sha256&&
            !selectors[value.panel.selector()]&&value.panel.kind_display_raw2()<3&&value.panel.meter_denominator_raw11()!=0&&
            qualified_origin&&evidence(value.evidence_id)&&!row(bag.armor,value.inventory_slot)&&!row(bag.weapons,value.inventory_slot)&&!row(bag.gems,value.inventory_slot)&&
            !armor_(scalar->item_id)&&!weapon_(scalar->item_id)&&scalar->item_id!=RecoveredTeleportGem::item_id,"PET trade owner/scalar/source/full instance conflict");
        selectors[value.panel.selector()]=true;
        if(value.exploration)require(RecoveredBeastExploration::decode_snapshot(value.exploration->bytes)&&value.exploration->metadata_key()==fields->key()&&value.exploration->selector()==value.panel.selector(),"PET trade C5 context belongs to another instance");
    }
    if(saved.beast_selection)require(selectors[saved.beast_selection->selector]&&saved.beast_selection->custody_revision&&saved.beast_selection->custody_revision<=max_revision&&saved.beast_selection->revision&&saved.beast_selection->revision<=max_revision,"PET trade raw selection invalid");
    for(std::uint8_t slot=0;slot<50;++slot){const auto& scalar=bag.scalar[slot];if(!scalar||!scalar->count)continue;
        const auto part=armor_(scalar->item_id);const bool weapon=weapon_(scalar->item_id).has_value(),gem=scalar->item_id==RecoveredTeleportGem::item_id;
        require(unsigned(part.has_value())+unsigned(weapon)+unsigned(gem)<=1,"Owned trade catalog category conflict");
        if(part&&slot<34)require(row(bag.armor,slot),"Owned trade armor missing complete metadata");
        if(weapon&&(slot<30||slot==34))require(row(bag.weapons,slot),"Owned trade weapon missing complete metadata");
        if(gem&&slot<30)require(row(bag.gems,slot),"Owned trade gem missing complete metadata");
        if(saved.beast_scope&&NativeBeastSourceCatalog::lookup(scalar->item_id)&&(slot<30||slot==37))require(beast_at(saved.beasts,slot),"PET trade owned scalar missing full custody");
    }
}
SqliteOwnedInstanceTradeRepository::Snapshot SqliteOwnedInstanceTradeRepository::load(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);Snapshot saved;saved.bag=SqliteArmorSlotRepository(db_,armor_,armor_instance_).load_snapshot(account,character);
    const auto wallet=SqliteTradeRepository(db_).load_wallet(account,character);require(wallet.has_value(),"Owned trade wallet unavailable");saved.wallet=*wallet;
    if(beasts_){beast_trade_shape(db_);saved.beast_scope=true;saved.beasts=beasts_->load_owned(account,character);saved.beast_selection=beasts_->load_selection_record(account,character);}
    validate(saved);scope.finish();return saved;
}
SqliteOwnedInstanceTradeRepository::Plan SqliteOwnedInstanceTradeRepository::plan(const std::array<Side,2>& sides) const{
    require(sides[0].expected.bag.character!=sides[1].expected.bag.character,"Owned trade participants coincide");
    Plan next{{sides[0].expected,sides[1].expected},{}};
    struct Item {StoredInventorySlot scalar;std::uint8_t source;std::optional<StoredArmorSlot> armor;std::optional<ArmorForeignOverlay> weapon,gem;std::optional<StoredBeastSnapshot> beast;};
    std::array<std::vector<Item>,2> outgoing;std::array<std::array<bool,30>,2> touched{};
    for(std::uint8_t n=0;n<2;++n){validate(sides[n].expected);const auto& side=sides[n];auto& saved=next.sides[n];
        require(side.items.size()<=8&&side.money<=saved.wallet.amount,"Owned trade offer/money invalid");std::set<std::uint8_t> used;
        for(const auto& offer:side.items){
            require(offer.slot<30&&used.insert(offer.slot).second,"Owned trade duplicate/protected offer");auto& scalar=*saved.bag.scalar[offer.slot];require(offer.quantity&&offer.quantity<=scalar.count,"Owned trade quantity invalid");
            Item item{scalar,offer.slot,{},{},{},{}};
            if(const auto* value=row(saved.bag.armor,offer.slot))item.armor=*value;
            if(const auto* value=row(saved.bag.weapons,offer.slot))item.weapon=*value;
            if(const auto* value=row(saved.bag.gems,offer.slot))item.gem=*value;
            if(const auto* value=beast_at(saved.beasts,offer.slot))item.beast=*value;
            const bool whole=item.armor.has_value()||item.weapon.has_value()||item.gem.has_value()||item.beast.has_value();
            require(whole?(scalar.count==1&&offer.quantity==1):(!armor_(scalar.item_id)&&!weapon_(scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id&&plain_(scalar.item_id)),"Owned trade item admission rejected");
            if(item.beast){
                const auto fields=item.beast->inventory_fields();
                require(fields&&!fields->native_exploring_label()&&!item.beast->panel.control7_alternate()&&!item.beast->panel.control8_alternate(),"PET trade outside custom inactive presentation domain");
                if(saved.beast_selection&&saved.beast_selection->selector==item.beast->panel.selector())saved.beast_selection.reset();
                std::erase_if(saved.beasts,[&](const auto& value){return value.inventory_slot==offer.slot;});
            }
            item.scalar.count=offer.quantity;outgoing[n].push_back(std::move(item));scalar.count=static_cast<std::uint8_t>(scalar.count-offer.quantity);if(!scalar.count){scalar.item_id=0;clear(saved.bag,offer.slot);}touched[n][offer.slot]=true;
        }
        const auto amount=ExtendedCoinAmount::exchange(saved.wallet.amount,side.money,sides[1-n].money);require(amount.has_value(),"Owned trade owner coin cap/insufficient balance");saved.wallet.amount=amount->value();
    }
    // Both owners' offers have been removed before capacity assignment. No
    // stack merging; the first explicit empty ordinary cell receives the item.
    for(std::uint8_t n=0;n<2;++n){auto& saved=next.sides[n];
        for(const auto& item:outgoing[1-n]){
            std::uint8_t destination=0;while(destination<30&&saved.bag.scalar[destination]->count)++destination;require(destination<30,"Owned trade destination capacity insufficient");
            const auto revision=sides[n].expected.bag.scalar[destination]->revision;clear(saved.bag,destination);saved.bag.scalar[destination]=item.scalar;saved.bag.scalar[destination]->revision=revision;touched[n][destination]=true;
            if(item.armor){auto value=*item.armor;value.slot=destination;value.revision=revision;saved.bag.armor.push_back(std::move(value));}
            if(item.weapon){auto value=*item.weapon;value.slot=destination;value.revision=revision;saved.bag.weapons.push_back(std::move(value));}
            if(item.gem){auto value=*item.gem;value.slot=destination;value.revision=revision;saved.bag.gems.push_back(std::move(value));}
            if(item.beast){
                auto value=*item.beast;value.account=saved.bag.account;value.character=saved.bag.character;
                value.inventory_slot=destination;value.bag_revision=revision;
                require(value.revision<max_revision,"PET trade custody revision exhausted");++value.revision;
                std::array<bool,256> used{};for(const auto& own:saved.beasts)used[own.panel.selector()]=true;
                auto selector=value.panel.selector();
                if(used[selector]){unsigned available=0;while(available<used.size()&&used[available])++available;require(available<used.size(),"PET trade selector capacity exhausted");selector=static_cast<std::uint8_t>(available);}
                // CUSTOM0085 per-character identity rebinding only. Preserve
                // every stat/time/palette/opaque byte and nullable menu payload.
                value.panel.bytes[3]=selector;if(value.exploration)value.exploration->bytes[3]=selector;
                saved.beasts.push_back(std::move(value));
            }
            next.transfers.push_back({static_cast<std::uint8_t>(1-n),item.source,n,destination,item.scalar.count});
        }
        for(std::uint8_t slot=0;slot<30;++slot)if(touched[n][slot]){
            auto& scalar=*saved.bag.scalar[slot];require(sides[n].expected.bag.scalar[slot]->revision<max_revision,"Owned trade physical revision exhausted");scalar.revision=sides[n].expected.bag.scalar[slot]->revision+1;
            for(auto& value:saved.bag.armor)if(value.slot==slot)value.revision=scalar.revision;
            for(auto& value:saved.bag.weapons)if(value.slot==slot)value.revision=scalar.revision;
            for(auto& value:saved.bag.gems)if(value.slot==slot)value.revision=scalar.revision;
            for(auto& value:saved.beasts)if(value.inventory_slot==slot)value.bag_revision=scalar.revision;
        }
        if(saved.wallet.amount!=sides[n].expected.wallet.amount){require(saved.wallet.revision<max_revision,"Owned trade wallet revision exhausted");++saved.wallet.revision;}
        sort(saved.bag.armor);sort(saved.bag.weapons);sort(saved.bag.gems);
        std::sort(saved.beasts.begin(),saved.beasts.end(),[](const auto& a,const auto& b){return a.inventory_slot<b.inventory_slot;});validate(saved);
    }
    require(std::uint64_t{next.sides[0].wallet.amount}+next.sides[1].wallet.amount==std::uint64_t{sides[0].expected.wallet.amount}+sides[1].expected.wallet.amount,"Owned trade money conservation failed");
    const auto quantities=[](const std::array<Snapshot,2>& values){std::map<std::uint16_t,std::uint32_t> counts;for(const auto& side:values)for(std::uint8_t slot=0;slot<30;++slot){const auto& value=*side.bag.scalar[slot];if(value.count)counts[value.item_id]+=value.count;}return counts;};
    require(quantities(next.sides)==quantities({sides[0].expected,sides[1].expected}),"Owned trade item quantity conservation failed");return next;
}
bool SqliteOwnedInstanceTradeRepository::receipt_exists(const std::string& receipt){
    require(hash(receipt),"Owned trade receipt malformed");sqlite_detail::Statement read(db_,"SELECT 1 FROM character_owned_instance_trade_receipts WHERE receipt=? UNION ALL SELECT 1 FROM character_trade_receipts WHERE receipt=? LIMIT 1");read.bind(1,receipt);read.bind(2,receipt);return read.row();
}
void SqliteOwnedInstanceTradeRepository::no_battle(std::uint64_t character){sqlite_detail::Statement read(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");read.bind_id(1,character);require(!read.row(),"Owned trade pending battle");}
SqliteOwnedInstanceTradeRepository::Plan SqliteOwnedInstanceTradeRepository::commit(const std::string& receipt,const std::array<Side,2>& sides,const PreparePlan& prepare,const CheckPlan& check,const FinalCurrent& current){
    static_assert(std::is_nothrow_move_constructible_v<Plan>,"Committed plan must return without allocation or exceptions");
    require(hash(receipt)&&bool(prepare),"Owned trade requires receipt and prepared replies");auto next=plan(sides);const auto before=state({sides[0].expected,sides[1].expected}),after=state(next.sides),operation=offers(sides,next);
    require(sqlite3_get_autocommit(db_)!=0,"Owned trade must own mutation transaction");prepare(next);
    sqlite_detail::Transaction transaction(db_);require(!receipt_exists(receipt),"Owned trade duplicate receipt");
    for(const auto& side:sides){require(load(side.expected.bag.account,side.expected.bag.character)==side.expected,"Owned trade complete before CAS conflict");no_battle(side.expected.bag.character);}
    const auto changed=[&](std::size_t n,std::uint8_t slot){return next.sides[n].bag.scalar[slot]!=sides[n].expected.bag.scalar[slot];};
    Exclusions permitted;Guard preserved;
    if(beasts_){
        sqlite_detail::Statement fk(db_,"PRAGMA foreign_keys");require(fk.row()&&fk.integer(0)==1,"PET trade requires foreign keys");
        const auto allow=[&](const char* table,const std::string& predicate){auto& expression=permitted[table];expression=expression.empty()?"NOT("+predicate+")":expression+" AND NOT("+predicate+")";};
        for(std::size_t n=0;n<2;++n){const auto actor="character_id="+std::to_string(sides[n].expected.bag.character);
            for(std::uint8_t slot=0;slot<30;++slot)if(changed(n,slot)){
                for(const auto* table:{"diagnostic_inventory_slots","character_armor_slot_metadata","character_weapon_slot_metadata","character_teleport_gem_metadata"})allow(table,actor+" AND slot="+std::to_string(slot));
                allow("character_beast_snapshot_custody",actor+" AND inventory_slot="+std::to_string(slot));
            }
            if(next.sides[n].beast_selection!=sides[n].expected.beast_selection)allow("character_beast_selection_0085",actor);
            if(next.sides[n].wallet!=sides[n].expected.wallet)allow("character_trade_wallets",actor);
        }
        permitted["character_owned_instance_trade_receipts"]="receipt<>'"+receipt+"'";
        preserved=guard(db_,permitted);
        // Retire only the binding to an outgoing instance before removing
        // its FK parent; preserve another valid or stale selection exactly.
        for(std::size_t n=0;n<2;++n)if(next.sides[n].beast_selection!=sides[n].expected.beast_selection){
            require(sides[n].expected.beast_selection&&!next.sides[n].beast_selection,"PET trade cannot create or alter another selection");
            const auto& selection=*sides[n].expected.beast_selection;
            sqlite_detail::Statement q(db_,"DELETE FROM character_beast_selection_0085 WHERE character_id=? AND selector=? AND custody_revision=? AND revision=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0085'");
            q.bind_id(1,sides[n].expected.bag.character);q.bind(2,selection.selector);q.bind_id(3,selection.custody_revision);q.bind_id(4,selection.revision);q.done();require(sqlite3_changes(db_)==1,"PET trade sender selection retire CAS failed");
        }
        for(std::size_t n=0;n<2;++n)for(const auto& value:sides[n].expected.beasts)
            if(value.inventory_slot<30&&changed(n,value.inventory_slot))erase_beast(db_,value);
    }
    // Delete every changed old overlay on both owners before scalar mutation.
    // Empty weapon retirement is limited to actually changed physical cells.
    for(std::size_t n=0;n<2;++n){const auto& bag=sides[n].expected.bag;
        for(const auto& value:bag.armor)if(value.slot<30&&changed(n,value.slot))erase_armor(db_,bag.character,value);
        for(const auto& value:bag.weapons)if(value.slot<30&&changed(n,value.slot))erase_foreign(db_,bag.character,value,true);
        for(const auto& value:bag.gems)if(value.slot<30&&changed(n,value.slot))erase_foreign(db_,bag.character,value,false);
    }
    for(std::size_t n=0;n<2;++n){const auto& old=sides[n].expected;const auto& saved=next.sides[n];
        for(std::uint8_t slot=0;slot<30;++slot)if(changed(n,slot)){
            const auto& a=*old.bag.scalar[slot];const auto& b=*saved.bag.scalar[slot];sqlite_detail::Statement write(db_,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=? AND item_id=? AND count=? AND revision=? AND source_sha256=? AND design_id='CUSTOM-0015'");write.bind(1,b.item_id);write.bind(2,b.count);write.bind_id(3,b.revision);write.bind(4,b.source_sha256);write.bind_id(5,saved.bag.character);write.bind(6,slot);write.bind(7,a.item_id);write.bind(8,a.count);write.bind_id(9,a.revision);write.bind(10,a.source_sha256);write.done();require(sqlite3_changes(db_)==1,"Owned trade scalar CAS write failed");
        }
        if(saved.wallet!=old.wallet){sqlite_detail::Statement write(db_,"UPDATE character_trade_wallets SET amount=?,revision=? WHERE character_id=? AND amount=? AND revision=? AND design_id='CUSTOM-0063'");write.bind(1,saved.wallet.amount);write.bind_id(2,saved.wallet.revision);write.bind_id(3,saved.bag.character);write.bind(4,old.wallet.amount);write.bind_id(5,old.wallet.revision);write.done();require(sqlite3_changes(db_)==1,"Owned trade wallet CAS write failed");}
    }
    for(std::size_t n=0;n<2;++n){const auto& bag=next.sides[n].bag;
        for(const auto& value:bag.armor)if(value.slot<30&&changed(n,value.slot))put_armor(db_,bag.character,value);
        for(const auto& value:bag.weapons)if(value.slot<30&&changed(n,value.slot))put_foreign(db_,bag.character,value,true);
        for(const auto& value:bag.gems)if(value.slot<30&&changed(n,value.slot))put_foreign(db_,bag.character,value,false);
        if(beasts_)for(const auto& value:next.sides[n].beasts)if(value.inventory_slot<30&&changed(n,value.inventory_slot))put_beast(db_,value);
    }
    sqlite_detail::Statement insert(db_,"INSERT INTO character_owned_instance_trade_receipts VALUES(?,?,?,?,?,?,?,?,'CUSTOM-0069')");insert.bind(1,receipt);insert.bind_id(2,sides[0].expected.bag.account);insert.bind_id(3,sides[0].expected.bag.character);insert.bind_id(4,sides[1].expected.bag.account);insert.bind_id(5,sides[1].expected.bag.character);insert.bind(6,before);insert.bind(7,after);insert.bind(8,operation);insert.done();require(sqlite3_changes(db_)==1,"Owned trade receipt insert failed");
    const auto verify=[&]{
        sqlite_detail::Statement recorded(db_,"SELECT first_account,first_character,second_account,second_character,before_state,after_state,offers_state,design_id FROM character_owned_instance_trade_receipts WHERE receipt=?");recorded.bind(1,receipt);require(recorded.row()&&recorded.number<std::uint64_t>(0)==sides[0].expected.bag.account&&recorded.number<std::uint64_t>(1)==sides[0].expected.bag.character&&recorded.number<std::uint64_t>(2)==sides[1].expected.bag.account&&recorded.number<std::uint64_t>(3)==sides[1].expected.bag.character&&recorded.text(4)==before&&recorded.text(5)==after&&recorded.text(6)==operation&&recorded.text(7)==design_id&&!recorded.row(),"Owned trade receipt full readback conflict");
        sqlite_detail::Statement duplicate(db_,"SELECT 1 FROM character_trade_receipts WHERE receipt=?");duplicate.bind(1,receipt);require(!duplicate.row(),"Owned trade late CUSTOM0063 receipt conflict");
        for(const auto& side:next.sides){require(load(side.bag.account,side.bag.character)==side,"Owned trade complete after readback conflict");no_battle(side.bag.character);}
        if(beasts_){require(guard(db_,permitted,&preserved)==preserved,"PET trade changed unrelated rows/schema/history/protected equipment");sqlite_detail::Statement fk(db_,"PRAGMA foreign_key_check");require(!fk.row(),"PET trade foreign key mismatch");}
    };verify();if(check){check(next);verify();}
    // A final qualifier/readback may itself retire the original caller. Nothing
    // that invokes providers or reconstructs metadata may follow this fence.
    if(current){const auto changes=sqlite3_total_changes64(db_);const bool valid=current();require(valid&&sqlite3_get_autocommit(db_)==0&&sqlite3_total_changes64(db_)==changes,"Owned trade final pure current retired or mutated transaction");}
    transaction.commit();return next;
}
}
