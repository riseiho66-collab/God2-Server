// Production SqliteDatabase adapters with the full qualified original catalogs.
#define main accepted_armor_adapter_companion_main
#include "storage_owned_armor_bank_adapter_0067.cpp"
#undef main
#include "db/SqliteOwnedForeignBankRepository.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "core/Config.h"
namespace {
using FRepo=SqliteOwnedForeignBankRepository;
void weapon_catalog(sqlite3* db){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/native-weapons-20260926/records.json");require(file.good(),"Qualified full weapon source missing");nlohmann::json groups;file>>groups;
    require(groups.size()==2&&groups[0].size()==2&&groups[1].size()==1259,"Full weapon source denominator changed");sqlite_detail::Transaction transaction(db);
    for(unsigned group=0;group<2;++group)for(const auto& row:groups[group]){require(row.size()==10,"Weapon source width changed");sqlite_detail::Statement insert(db,group==0?"INSERT INTO native_weapon_sources VALUES(?,?,?,?,?,?,?,?,?,?)":"INSERT INTO native_weapon_rows VALUES(?,?,?,?,?,?,?,?,?,?)");
        for(int i=0;i<10;++i){if(group==1&&(i==6||i==8))insert.bind_blob(i+1,unhex(row[i].get<std::string>()));else if((group==0&&i==7)||(group==1&&i>=1&&i<=4))insert.bind(i+1,row[i].get<std::int64_t>());else insert.bind(i+1,row[i].get<std::string>());}insert.done();
    }transaction.commit();
}
void migration44(){
    File file;SqliteDatabase database(file.path);rejects([&]{(void)database.foreign_bank();});database.initialize();rejects([&]{(void)database.foreign_bank();});database.migrate();auto raw=open(file.path);
    require(number(raw.get(),"SELECT max(version) FROM schema_migrations")==default_sqlite_migrations().back().version,"Fresh current schema missing");
    for(const auto* table:{"accounts","recovered_characters","diagnostic_inventory_slots","character_bank_item_slots","character_bank_foreign_metadata","character_bank_foreign_receipts"})require(dump(raw.get(),std::string("SELECT * FROM ")+table).empty(),"Fresh migration granted rows");
    const auto before=tables(raw.get());rejects([&]{(void)database.foreign_bank().load(1,1);});require(tables(raw.get())==before,"Unallocated foreign read wrote data");database.migrate();require(tables(raw.get())==before,"Migration44 not idempotent");require(dump(raw.get(),"PRAGMA foreign_key_check").empty(),"Schema44 foreign keys broken");
}
void production_transport(){
    Fixture f;weapon_catalog(f.raw.get());require(f.current->native_weapon_catalog().populated(),"Full1259 catalog invalid");
    std::array<std::array<std::uint8_t,20>,3> bytes{};
    for(unsigned n=0;n<3;++n){const std::uint16_t id=n==0?1:n==1?19001:16055;auto& b=bytes[n];b.fill(static_cast<std::uint8_t>(0x92+n));b[0]=static_cast<std::uint8_t>(id);b[1]=static_cast<std::uint8_t>(id>>8);b[2]=n==0?0xc1:n==1?0x99:8;if(n==2)b[3]=10;b[19]=static_cast<std::uint8_t>(0xf7+n);
        sqlite_detail::Statement scalar(f.raw.get(),"UPDATE diagnostic_inventory_slots SET item_id=?,count=1,revision=? WHERE character_id=? AND slot=?");scalar.bind(1,id);scalar.bind(2,11+n);scalar.bind_id(3,f.character);scalar.bind(4,10+n);scalar.done();
        sqlite_detail::Statement insert(f.raw.get(),n<2?"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,?,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter0068',?,?,'CUSTOM-0046')":"INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,?,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter0068',?,'CUSTOM-0057')");insert.bind_id(1,f.character);insert.bind(2,10+n);insert.bind_blob(3,b);insert.bind(4,11+n);insert.bind(5,SqliteArmorSlotRepository::source_sha256);if(n<2)insert.bind(6,SqliteWeaponSlotRepository::client_sha256);insert.done();
    }
    auto& repo=f.current->foreign_bank();const auto initial=repo.load(1,f.character),peer=repo.load(2,f.peer);
    for(unsigned n=0;n<3;++n){const FRepo::Request request{repo.load(1,f.character),Op::Deposit,0,static_cast<std::uint8_t>(10+n),static_cast<std::uint8_t>(6+n),1};auto planned=repo.plan(request);auto result=repo.commit(std::string(64,static_cast<char>('1'+n)),request,[](const auto&){});require(result.after==planned.after,"Production foreign deposit differs from exact plan");require(result.after.foreign[n].logical20==bytes[n],"Production foreign20 flattened");}
    require(repo.load(2,f.peer)==peer,"Production foreign changed another player");
    const auto correct=repo.load(1,f.character);auto bad=bytes[1];bad[2]=0xc1;sqlite_detail::Statement poison(f.raw.get(),"UPDATE character_bank_foreign_metadata SET logical20=? WHERE character_id=? AND slot=7");poison.bind_blob(1,bad);poison.bind_id(2,f.character);poison.done();const auto poisoned=tables(f.raw.get());rejects([&]{(void)repo.load(1,f.character);});require(tables(f.raw.get())==poisoned,"Invalid TWP namespace read wrote rows");sqlite_detail::Statement fix(f.raw.get(),"UPDATE character_bank_foreign_metadata SET logical20=? WHERE character_id=? AND slot=7");fix.bind_blob(1,bytes[1]);fix.bind_id(2,f.character);fix.done();require(repo.load(1,f.character)==correct,"Exact namespace correction altered instance");
    // This legal native-qualified plan must enter the actual production writer.
    // A receipt trigger corrupts an unrelated full tail; exact readback must roll
    // back the two scalar cells, metadata and receipt together.
    const FRepo::Request request{correct,Op::Withdraw,0,6,10,1};(void)repo.plan(request);
    f.sql("CREATE TRIGGER foreign_adapter_poison AFTER INSERT ON character_bank_foreign_receipts BEGIN UPDATE character_bank_foreign_metadata SET provenance='injected-late-other-instance' WHERE character_id=NEW.character_id AND slot=7; END");const auto before=tables(f.raw.get());rejects([&]{repo.commit(std::string(64,'9'),request,[](const auto&){});});require(tables(f.raw.get())==before,"Actual production foreign postwrite did not rollback");f.sql("DROP TRIGGER foreign_adapter_poison");require(repo.commit(std::string(64,'9'),request,[](const auto&){}).after.base.bag.weapons[0].logical20==bytes[0],"Same legal plan after trigger removal failed");
    for(unsigned n=1;n<3;++n){const FRepo::Request next{repo.load(1,f.character),Op::Withdraw,0,static_cast<std::uint8_t>(6+n),static_cast<std::uint8_t>(10+n),1};repo.commit(std::string(64,static_cast<char>('a'+n)),next,[](const auto&){});}
    const auto final=repo.load(1,f.character);require(final.foreign.empty()&&final.base.bag.weapons.size()==2&&final.base.bag.gems.size()==1,"Production instance return incomplete");require(final.base.bag.armor==initial.base.bag.armor&&final.base.armor==initial.base.armor&&repo.load(2,f.peer)==peer,"Production foreign changed protected armor/peer");
    require(dump(f.raw.get(),"PRAGMA foreign_key_check").empty(),"Production foreign FK failure");
}
void config_gate(){
    // Parse the actual installed accepted configuration in a private file.
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/releases/town-chat-welcome-20260924/server-config.json");require(file.good(),"Installed config source missing");nlohmann::json config;file>>config;config["world"].erase("owned_mixed_bank");config["world"].erase("owned_instance_discard");config["world"].erase("owned_foreign_bank");File temp;const auto path=temp.directory/"server-config.json";
    auto parse=[&]{std::ofstream out(path);out<<config.dump();out.close();return Config::load(path);};require(!parse().owned_foreign_bank_enabled,"New bank not default off");config["world"]["owned_foreign_bank"]={{"enabled",true}};require(parse().owned_foreign_bank_enabled,"Valid foreign bank opt-in rejected");
    const auto config_error=[&](const std::string& expected){bool rejected=false;try{(void)parse();}catch(const std::runtime_error& error){require(error.what()==expected,"Unexpected config gate error");rejected=true;}require(rejected,"Config accepted invalid opt-in");};
    config["world"]["owned_armor_bank"]["enabled"]=false;config_error("Owned foreign bank requires authenticated native world and owned armor bank");config["world"]["owned_armor_bank"]["enabled"]=true;config["world"]["owned_foreign_bank"]["enabled"]="true";config_error("Owned foreign bank bool required");
}
}
int main(){try{migration44();production_transport();config_gate();std::cout<<"PASS CUSTOM0068 true SqliteDatabase full1259 weapon catalog WPN1/TWP25/gem8 source qualification, full20 roundtrip, preserved armor/peer, actual writer trigger rollback and schema44/config opt-in; not live acceptance\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
