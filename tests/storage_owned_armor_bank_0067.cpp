#include "db/SqliteOwnedArmorBankRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "handlers/OwnedBagProjectionService.h"
#include "protocol/RecoveredArmorSourceInstance.h"
#include <iostream>
#include <cstring>
#include <limits>
#include <memory>
#include <stdexcept>
#include <filesystem>
#include <chrono>

namespace {
using namespace god2;
using Repo=SqliteOwnedArmorBankRepository;
using Op=Repo::Operation;
void require(bool ok,const char* reason){if(!ok)throw std::runtime_error(reason);}
template<class F>void rejects(F&& run){try{run();}catch(const DatabaseError&){return;}throw std::runtime_error("Expected owned armor bank rejection");}
std::optional<std::uint8_t> armor(std::uint16_t key){if(key==1001||key==20001)return 31;if(key==1201)return 30;return {};}
bool exact(std::uint16_t key,const std::array<std::uint8_t,20>& bytes){return armor(key)&&RecoveredArmorSourceInstance::matches(key,key==20001?"TEQ":"EQU",bytes);}
std::string dump(sqlite3* db,const std::string& query){
    sqlite3_stmt* statement=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,query.c_str(),-1,&statement,nullptr));
    std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> guard(statement,sqlite3_finalize);std::string result;
    int code=SQLITE_OK;
    while((code=sqlite3_step(statement))==SQLITE_ROW){for(int c=0;c<sqlite3_column_count(statement);++c){const auto kind=sqlite3_column_type(statement,c);const auto* data=kind==SQLITE_BLOB?sqlite3_column_blob(statement,c):sqlite3_column_text(statement,c);const auto length=sqlite3_column_bytes(statement,c);result+=std::to_string(kind)+":"+std::to_string(length)+":";if(length)result.append(static_cast<const char*>(data),length);result+=';';}result+='\n';}
    require(code==SQLITE_DONE,"Fixture typed dump failed");return result;
}
struct Fixture {
    sqlite3* raw{};std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> owned{nullptr,sqlite3_close_v2};std::array<std::uint64_t,2> ids{};
    std::uint8_t serial{};
    std::filesystem::path file;
    explicit Fixture(unsigned bag_slots=50,bool file_backed=false){
        if(file_backed)file=std::filesystem::temp_directory_path()/("god2-owned-armor-bank-0067-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".sqlite3");
        const auto path=file_backed?file.string():std::string(":memory:");require(sqlite3_open(path.c_str(),&raw)==SQLITE_OK,"Fixture open failed");owned.reset(raw);sql("PRAGMA foreign_keys=ON");auto migrations=default_sqlite_migrations();std::erase_if(migrations,[](const auto& migration){return migration.version>42;});SqliteMigrationManager(raw,migrations).migrate();
        sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'owned-bank-a','hash'),(2,'owned-bank-b','hash')");SqliteRecoveredCharacterRepository characters(raw);SqliteBankItemsRepository bank(raw);bank.install_schema();
        for(unsigned n=0;n<2;++n){std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+n);ids[n]=characters.create(n+1,profile).id;
            for(unsigned slot=0;slot<bag_slots;++slot){sqlite_detail::Statement write(raw,"INSERT INTO diagnostic_inventory_slots VALUES(?,?,0,0,1,?,'CUSTOM-0015')");write.bind_id(1,ids[n]);write.bind(2,slot);write.bind(3,SqliteArmorSlotRepository::source_sha256);write.done();}
            bank.provision_empty(n+1,ids[n]);
        }
        sql("CREATE TABLE armor_bank_test_money(character_id INTEGER PRIMARY KEY,amount INTEGER);INSERT INTO armor_bank_test_money VALUES(1,1234),(2,5678)");
    }
    ~Fixture(){owned.reset();if(!file.empty()){std::error_code ignored;std::filesystem::remove(file,ignored);}}
    void sql(const std::string& value){sqlite_detail::execute(raw,value);}
    Repo repo(){return {raw,armor,exact};}
    void install(){sql(Repo::schema());}
    auto load(unsigned owner=0){return repo().load(owner+1,ids[owner]);}
    std::string rows(){sqlite_detail::Statement names(raw,"SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name");std::string out;while(names.row()){const auto name=names.text(0);require(name.find('"')==std::string::npos,"Unsafe test table");out+=name+'\n'+dump(raw,"SELECT * FROM \""+name+"\" ORDER BY rowid");}return out;}
    std::string receipt(){const char* hex="0123456789abcdef";require(serial<16,"Fixture receipt domain exhausted");return std::string(63,'0')+hex[serial++];}
    void scalar(unsigned slot,std::uint16_t item,unsigned count,std::uint64_t revision,unsigned owner=0){sqlite_detail::Statement write(raw,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=?");write.bind(1,item);write.bind(2,count);write.bind_id(3,revision);write.bind_id(4,ids[owner]);write.bind(5,slot);write.done();}
    auto add(unsigned slot,std::uint16_t item,std::uint8_t fill,std::uint64_t revision,unsigned owner=0){
        scalar(slot,item,1,revision,owner);std::array<std::uint8_t,20> bytes;bytes.fill(fill);bytes[0]=static_cast<std::uint8_t>(item);bytes[1]=static_cast<std::uint8_t>(item>>8);bytes[2]=static_cast<std::uint8_t>((fill&0xc0u)|(item==20001?26u:2u));
        sqlite_detail::Statement insert(raw,"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,?,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0066')");insert.bind_id(1,ids[owner]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind_id(4,revision);insert.bind(5,std::string("opaque-custom-bank-")+std::to_string(fill));insert.bind(6,SqliteArmorSlotRepository::source_sha256);insert.bind(7,SqliteArmorSlotRepository::client_sha256);insert.done();return bytes;
    }
    void foreign(){
        for(unsigned slot:{10u,34u}){scalar(slot,60010,1,9);std::array<std::uint8_t,20> bytes;bytes.fill(0xa9);bytes[0]=0x6a;bytes[1]=0xea;bytes[2]=0xc1;
            sqlite_detail::Statement write(raw,"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,9,'CUSTOM_TEST_NOT_NATIVE','opaque-old-weapon',?,?,'CUSTOM-0046')");write.bind_id(1,ids[0]);write.bind(2,slot);write.bind_blob(3,bytes);write.bind(4,SqliteArmorSlotRepository::source_sha256);write.bind(5,SqliteWeaponSlotRepository::client_sha256);write.done();}
        scalar(11,16055,1,6);std::array<std::uint8_t,20> bytes;bytes.fill(0x91);bytes[0]=0xb7;bytes[1]=0x3e;bytes[2]=8;bytes[3]=6;
        sqlite_detail::Statement write(raw,"INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,6,'CUSTOM_TEST_NOT_NATIVE','opaque-gem',?,'CUSTOM-0057')");write.bind_id(1,ids[0]);write.bind(2,11);write.bind_blob(3,bytes);write.bind(4,SqliteArmorSlotRepository::source_sha256);write.done();
        std::array<std::uint8_t,20> empty{};empty[19]=0x91;sqlite_detail::Statement e(raw,"INSERT INTO character_weapon_slot_metadata VALUES(?,29,?,1,'EMPTY_SLOT_POLICY','opaque-empty-weapon',?,?,'CUSTOM-0046')");e.bind_id(1,ids[0]);e.bind_blob(2,empty);e.bind(3,SqliteArmorSlotRepository::source_sha256);e.bind(4,SqliteWeaponSlotRepository::client_sha256);e.done();
    }
    Repo::Request request(Op operation,std::uint8_t source,std::uint8_t destination,std::uint8_t page=0){return {load(),operation,page,source,destination,1};}
    Repo::Plan transfer(const Repo::Request& request){auto repository=repo();bool called=false;const auto planned=repository.plan(request);
        auto result=repository.commit(receipt(),request,[&](const auto& after){require(sqlite3_get_autocommit(raw)!=0,"Projection was not before BEGIN");require(after.after==planned.after,"Prepared projection plan changed");called=true;},[&](const auto&){require(sqlite3_get_autocommit(raw)==0,"Final proof was not inside mutation transaction");});require(called,"Projection skipped");return result;
    }
};
const StoredVaultArmor& vault(const Repo::Snapshot& saved,unsigned slot){const auto it=std::find_if(saved.armor.begin(),saved.armor.end(),[&](const auto& row){return row.slot==slot;});require(it!=saved.armor.end(),"Expected vault full20 missing");return *it;}
void reader_and_transport(){
    Fixture f;auto repository=f.repo();const auto initial=f.rows();const auto changes=sqlite3_total_changes(f.raw);rejects([&]{repository.load(1,f.ids[0]);});require(f.rows()==initial&&sqlite3_total_changes(f.raw)==changes,"Reader made DDL/capacity/grants");f.install();const auto empty=f.load();require(empty.armor.empty(),"Schema granted armor");
    f.foreign();const auto a=f.add(0,1001,0xa1,7),b=f.add(1,1201,0xb2,13),c=f.add(2,1001,0xc3,3);f.add(0,20001,0xd4,11,1);const auto peer=f.load(1);const auto before=f.load();const auto money=dump(f.raw,"SELECT * FROM armor_bank_test_money ORDER BY character_id");
    f.sql("UPDATE character_bank_item_slots SET revision=17 WHERE character_id=1 AND slot=299");auto request=f.request(Op::Deposit,0,49,5);const auto deposited=f.transfer(request);
    require(deposited.after.bag.scalar[0]->count==0&&deposited.after.bag.scalar[0]->revision==8&&vault(deposited.after,299).logical20==a&&vault(deposited.after,299).revision==18&&vault(deposited.after,299).instance_design_id=="CUSTOM-0066","Deposit lost full20/physical revision/instance identity");
    auto moved=f.transfer(f.request(Op::Move,49,0,5));require(moved.after.vault[299].count==0&&moved.after.vault[299].revision==19&&vault(moved.after,250).logical20==a&&vault(moved.after,250).revision==2,"Native65 empty move lost whole20/physical revision");
    auto withdrawn=f.transfer(f.request(Op::Withdraw,0,29,5));require(withdrawn.after.vault[250].count==0&&withdrawn.after.vault[250].revision==3&&withdrawn.after.bag.scalar[29]->revision==2&&withdrawn.after.bag.armor.back().logical20==a,"Withdrawal lost whole20/physical revision");
    require(std::none_of(withdrawn.after.bag.weapons.begin(),withdrawn.after.bag.weapons.end(),[](const auto& row){return row.slot==29;}),"Only empty weapon overlay was not retired");
    f.transfer(f.request(Op::Deposit,29,2));f.transfer(f.request(Op::Deposit,1,3));f.transfer(f.request(Op::Deposit,2,4));
    const auto pair=f.load();auto swapped=f.transfer(f.request(Op::Move,2,3));require(vault(swapped.after,2).logical20==b&&vault(swapped.after,3).logical20==a&&vault(swapped.after,2).revision==pair.vault[2].revision+1&&vault(swapped.after,3).revision==pair.vault[3].revision+1,"Cross-part bank exchange swapped revisions or lost instances");
    auto same=f.transfer(f.request(Op::Move,3,4));require(vault(same.after,3).logical20==c&&vault(same.after,4).logical20==a&&vault(same.after,3).provenance==vault(pair,4).provenance,"Same-ID bank exchange collapsed opaque metadata");
    auto foreign=before.bag.weapons;std::erase_if(foreign,[](const auto& row){return row.slot==29;});
    require(f.load(1)==peer&&dump(f.raw,"SELECT * FROM armor_bank_test_money ORDER BY character_id")==money&&same.after.bag.weapons==foreign&&same.after.bag.gems==before.bag.gems,"Unrelated owner/money/foreign overlay changed");
}
void exclusions_and_stale(){
    Fixture f;f.install();f.foreign();f.add(0,1001,0xa1,7);f.add(1,20001,0xb2,8);f.scalar(5,3107,7,3);auto repository=f.repo();const auto expected=f.load();
    auto denied=[&](const Repo::Request& request){const auto before=f.rows();rejects([&]{repository.commit(std::string(64,'a'),request,[](const auto&){});});require(f.rows()==before,"Denied operation changed rows");};
    for(auto source:{5,10,11,30,34,255}){auto request=f.request(Op::Deposit,static_cast<std::uint8_t>(source),0);denied(request);}
    auto request=f.request(Op::Deposit,0,0);request.quantity=2;denied(request);request.quantity=127;denied(request);request.quantity=1;request.page=6;denied(request);
    request=f.request(Op::Deposit,0,0);auto malformed=request;malformed.expected.bag.armor[0].logical20[2]=(malformed.expected.bag.armor[0].logical20[2]&0xc0u)|26u;denied(malformed);
    malformed=request;malformed.expected.bag.armor[0].slot=255;denied(malformed);
    for(unsigned slot:{29u,44u}){auto stale=request;++stale.expected.bag.scalar[slot]->revision;denied(stale);}
    auto stale=request;++stale.expected.vault[299].revision;denied(stale);stale=request;stale.expected.bag.weapons.back().logical20[19]^=1;denied(stale);
    rejects([&]{repository.load(2,f.ids[0]);});
    auto maximum=request;maximum.expected.vault[0].revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());denied(maximum);
    auto last=maximum;--last.expected.vault[0].revision;require(repository.plan(last).after.vault[0].revision==maximum.expected.vault[0].revision,"Last legal physical revision rejected");
    bool before_called=false;const auto success=repository.commit(std::string(64,'b'),request,[&](const auto&){before_called=true;});require(before_called,"Before-projection missing");request=f.request(Op::Withdraw,0,1);denied(request); // occupied target
    auto replay=f.request(Op::Withdraw,0,2);const auto before=f.rows();rejects([&]{repository.commit(std::string(64,'b'),replay,[](const auto&){});});require(f.rows()==before,"Duplicate receipt mutated rows");
    auto move=f.request(Op::Move,0,0);denied(move);move=f.request(Op::Move,0,1);f.sql("UPDATE character_bank_item_slots SET item_id=3107,count=127,source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731' WHERE character_id=1 AND slot=1");move=f.request(Op::Move,0,1);denied(move);
    // Existing scalar MED transport remains independent and unchanged.
    SqliteBankItemsRepository bank(f.raw);const auto scalar=bank.load(1,f.ids[0]);const auto plain=bank.commit(std::string(64,'c'),{scalar,Op::Deposit,0,5,2,3});require(plain.bag[5].count==4&&plain.vault[2].count==3,"Legacy MED quantity behavior changed");
    rejects([&]{repository.commit(std::string(64,'c'),f.request(Op::Withdraw,0,2),[](const auto&){});});
    require(success.after.bag.weapons==expected.bag.weapons&&success.after.bag.gems==expected.bag.gems,"Normal deposit changed foreign overlays");
}
void failures_and_triggers(){
    Fixture f;f.install();f.foreign();f.add(0,1001,0xa1,7);f.add(1,20001,0xb2,8);auto repository=f.repo();const auto request=f.request(Op::Deposit,0,0);
    const auto unchanged=[&](auto run){const auto before=f.rows();rejects(run);require(f.rows()==before,"Failure did not rollback complete storage rows");};
    for(const auto* sql:{
        "CREATE TRIGGER injected BEFORE DELETE ON character_armor_slot_metadata BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE UPDATE ON character_bank_item_slots WHEN NEW.slot=0 BEGIN SELECT RAISE(ABORT,'second scalar'); END",
        "CREATE TRIGGER injected BEFORE INSERT ON character_bank_armor_metadata BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE INSERT ON character_bank_armor_receipts BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected AFTER INSERT ON character_bank_armor_receipts BEGIN UPDATE character_bank_armor_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB); END",
        "CREATE TRIGGER injected AFTER INSERT ON character_bank_armor_receipts BEGIN UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=44; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_bank_armor_receipts BEGIN UPDATE character_bank_item_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=299; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_bank_armor_receipts BEGIN UPDATE character_weapon_slot_metadata SET provenance='corrupt-foreign' WHERE character_id=NEW.character_id AND slot=34; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_bank_armor_receipts BEGIN UPDATE character_teleport_gem_metadata SET provenance='corrupt-gem' WHERE character_id=NEW.character_id; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_bank_armor_receipts BEGIN UPDATE character_bank_armor_receipts SET after_state='valid-but-wrong'; END"
    }){f.sql(sql);bool exercised=false;
        sqlite3_trace_v2(f.raw,SQLITE_TRACE_STMT,[](unsigned,void* context,void*,void* sql)->int{if(sql&&std::strstr(static_cast<const char*>(sql),"TRIGGER injected"))*static_cast<bool*>(context)=true;return 0;},&exercised);
        unchanged([&]{repository.commit(std::string(64,'d'),request,[](const auto&){});});sqlite3_trace_v2(f.raw,0,nullptr,nullptr);
        require(exercised,"SQL failure trigger was not actually exercised");f.sql("DROP TRIGGER injected");}
    const auto before=f.rows();try{repository.commit(std::string(64,'e'),request,[](const auto&){throw std::runtime_error("Projection failed");});throw std::logic_error("Failure not raised");}catch(const std::runtime_error& error){require(std::string(error.what())=="Projection failed","Wrong preparation failure");}require(f.rows()==before,"Pre-BEGIN projection failure wrote rows");
    bool checked=false;unchanged([&]{repository.commit(std::string(64,'e'),request,[](const auto&){},[&](const auto&){checked=true;f.sql("UPDATE character_bank_armor_receipts SET after_state='late-mutation'");});});require(checked,"Postcheck corruption path was not executed");
    SqliteRecoveredCharacterRepository characters(f.raw);const auto resources=characters.commit_resources(1,f.ids[0],{},{52,120,2,80,0,"CUSTOM-0012"});const auto battle=characters.reserve_battle(1,f.ids[0],resources);
    unchanged([&]{repository.commit(std::string(64,'f'),request,[](const auto&){});});characters.settle_battle(1,f.ids[0],battle,resources,resources,true,0);
    bool pending=false;unchanged([&]{repository.commit(std::string(64,'f'),request,[](const auto&){},[&](const auto&){sqlite_detail::Statement write(f.raw,"INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(?,?,'CUSTOM-0012')");write.bind_id(1,f.ids[0]);write.bind_id(2,characters.load_resources(1,f.ids[0])->revision);write.done();pending=true;});});require(pending,"Late pending battle rollback not exercised");
}
void vault_admission_and_readonly(){
    Fixture f;f.install();f.add(0,1001,0xa1,7);f.add(1,20001,0xb2,9);f.transfer(f.request(Op::Deposit,0,0));f.transfer(f.request(Op::Deposit,1,1));auto repository=f.repo();
    const auto request=f.request(Op::Move,0,1);const auto unchanged=[&](auto call){const auto before=f.rows();rejects(call);require(f.rows()==before,"Vault admission refusal modified rows");};
    auto wrong=request;wrong.expected.armor[1].logical20[2]=static_cast<std::uint8_t>((wrong.expected.armor[1].logical20[2]&0xc0u)|2u);
    unchanged([&]{repository.commit(std::string(64,'9'),wrong,[](const auto&){});}); // TEQ same key cannot become EQU2
    wrong=request;wrong.expected.armor[0].source_sha256=std::string(64,'1');unchanged([&]{repository.plan(wrong);});
    wrong=request;wrong.expected.armor[0].logical20[19]^=1;unchanged([&]{repository.commit(std::string(64,'9'),wrong,[](const auto&){});});
    rejects([&]{Repo denied(f.raw,armor,{});});
    const auto correct=vault(f.load(),0).logical20;
    f.sql("UPDATE character_bank_armor_metadata SET logical20=CAST(substr(logical20,1,2)||X'9A'||substr(logical20,4) AS BLOB) WHERE character_id=1 AND slot=0");
    unchanged([&]{repository.load(1,f.ids[0]);}); // EQU same key with valid generic armor26 must still refuse
    {sqlite_detail::Statement restore(f.raw,"UPDATE character_bank_armor_metadata SET logical20=? WHERE character_id=? AND slot=0");restore.bind_blob(1,correct);restore.bind_id(2,f.ids[0]);restore.done();}
    f.sql("DELETE FROM character_bank_armor_metadata WHERE character_id=1 AND slot=0");unchanged([&]{repository.load(1,f.ids[0]);}); // no metadata fabrication
    f.sql("DELETE FROM character_bank_item_slots WHERE character_id=2 AND slot=299");unchanged([&]{repository.load(2,f.ids[1]);}); // no silent capacity fill
}
void sparse_protected_and_delete(){
    Fixture f(30,true);f.install();f.add(0,1001,0xa1,7);f.add(0,20001,0xb2,9,1);
    const auto absent=[](const auto& snapshot){for(unsigned slot=30;slot<50;++slot)require(!snapshot.bag.scalar[slot],"Protected absent row was provisioned");};
    const auto before=f.load();absent(before);f.repo().commit(f.receipt(),{f.load(1),Op::Deposit,0,0,0,1},[](const auto&){});const auto peer=f.load(1);const auto peer_receipt=dump(f.raw,"SELECT * FROM character_bank_armor_receipts WHERE character_id=2");const auto deposited=f.transfer(f.request(Op::Deposit,0,0));absent(deposited.after);
    const auto withdrawn=f.transfer(f.request(Op::Withdraw,0,29));absent(withdrawn.after);require(withdrawn.after.bag.armor[0].logical20==before.bag.armor[0].logical20,"Sparse protected transfer lost armor20");
    auto request=f.request(Op::Deposit,29,0);auto orphan=request;orphan.expected.bag.armor[0].slot=31;const auto rows=f.rows();rejects([&]{f.repo().plan(orphan);});require(f.rows()==rows,"Missing armor scalar refusal wrote rows");
    // Optional absence participates in complete CAS, including a new protected row.
    f.sql("INSERT INTO diagnostic_inventory_slots VALUES(1,44,0,0,1,'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731','CUSTOM-0015')");
    const auto changed=f.rows();rejects([&]{f.repo().commit(f.receipt(),request,[](const auto&){});});require(f.rows()==changed,"Absent-to-present conflict did not rollback");f.sql("DELETE FROM diagnostic_inventory_slots WHERE character_id=1 AND slot=44");
    f.transfer(f.request(Op::Deposit,29,0));const auto money=dump(f.raw,"SELECT * FROM armor_bank_test_money WHERE character_id=2");
    require(!dump(f.raw,"SELECT * FROM character_bank_armor_receipts WHERE character_id=1").empty()&&!dump(f.raw,"SELECT * FROM character_bank_armor_metadata WHERE character_id=1").empty(),"Delete fixture lacked receipt/occupied vault");
    SqliteRecoveredCharacterRepository characters(f.raw);const std::array<std::uint8_t,1> name{'A'};require(characters.erase_owned(1,f.ids[0],name),"New receipt blocked existing erase_owned");
    require(dump(f.raw,"SELECT * FROM character_bank_armor_receipts WHERE character_id=1").empty()&&dump(f.raw,"SELECT * FROM character_bank_armor_metadata WHERE character_id=1").empty(),"Deleted character left owned vault descendants");
    require(f.load(1)==peer&&dump(f.raw,"SELECT * FROM character_bank_armor_receipts WHERE character_id=2")==peer_receipt&&dump(f.raw,"SELECT * FROM armor_bank_test_money WHERE character_id=2")==money,"Character cascade changed another owner/vault/receipt/money");
    f.sql("DELETE FROM diagnostic_inventory_slots WHERE character_id=2 AND slot=29");const auto missing=f.rows();rejects([&]{f.repo().load(2,f.ids[1]);});require(f.rows()==missing,"Missing bag row was filled implicitly");
    Fixture account(30,true);account.install();account.add(0,1001,0xc3,3);account.add(0,1201,0xd4,4,1);account.transfer(account.request(Op::Deposit,0,0));const auto other=account.load(1);
    // Existing character/account FKs are restrictive, so exercise the new
    // account receipt cascade before the established character deletion order.
    account.sql("BEGIN IMMEDIATE;PRAGMA defer_foreign_keys=ON;DELETE FROM accounts WHERE id=1");
    require(dump(account.raw,"SELECT * FROM character_bank_armor_receipts WHERE account_id=1").empty()&&account.load(1)==other,"Account receipt cascade failed or changed another owner");account.sql("ROLLBACK");
    require(!dump(account.raw,"SELECT * FROM character_bank_armor_receipts WHERE account_id=1").empty(),"Account cascade rollback did not restore receipt");
    require(SqliteRecoveredCharacterRepository(account.raw).erase_owned(1,account.ids[0],name),"Account cleanup character deletion failed");account.sql("DELETE FROM accounts WHERE id=1");require(account.load(1)==other,"Completed account deletion changed another owner");
}
}
int main(){try{reader_and_transport();exclusions_and_stale();failures_and_triggers();vault_admission_and_readonly();sparse_protected_and_delete();std::cout<<"PASS CUSTOM0067 armor-only full20 bank storage: 30 required bag +20 optional protected/3-overlay +300/fullmeta CAS; 63/64/65 whole transfer/swap; physical revisions; immutable receipts; source/family/owner eligibility; 10 actual trigger rollbacks; scalar MED regression; foreign/peer/money preservation; file-backed sparse protected and character/account cascade; no implicit schema/grants\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
