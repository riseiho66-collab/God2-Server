#include "db/OwnedBankCapacityProvision.h"
#include "db/SqliteProcessOwnership.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#else
#include <sys/wait.h>
#include <unistd.h>
#endif
namespace {
using namespace god2;
using Source=OwnedBankCapacityProvision;using Tx=Source::Tx;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> void rejects(F f,const char* message){bool refused=false;try{f();}catch(const std::exception&){refused=true;}require(refused,message);}
Tx::State synthetic() {
    Tx::State value;auto& i=value.inventory;i.root.id=1;i.root.account_id=1;i.root.created_at="SYNTHETIC";
    i.revision=1;i.source_sha256=std::string(64,'a');i.source_record="SYNTHETIC-MATERIAL";
    for(unsigned slot=0;slot<30;++slot)i.cells.push_back({"bag",slot,{}});
    i.cells.push_back({"bank",0,{}});
    OwnedInventoryInstance item;item.id=113;item.definition_key=4422;item.quantity=17;item.revision=1;item.stackable=true;
    item.acquisition_sha256=std::string(64,'b');item.acquisition_record="SYNTHETIC-ACQUISITION";
    item.aliases.push_back({NativeEquipmentSnapshot::client_pin,"synthetic-full25",std::string(64,'c'),"SYNTHETIC-ALIAS",4422,5,1,std::vector<std::uint8_t>(25,0x83)});
    i.cells[5].instance=item;
    auto& e=value.equipment;e.root=i.root;e.position={1,1,18,14,1};e.revision=1;e.actor_handle=7;
    e.source_sha256=std::string(64,'d');e.source_record="SYNTHETIC-NATIVE";
    e.client_sha256=NativeEquipmentSnapshot::client_pin;e.record_kind=NativeEquipmentSnapshot::kind;
    e.record.resize(NativeEquipmentSnapshot::record_bytes,0);e.record[1200]=0xda;e.record[1201]=7;
    return value;
}
nlohmann::json approved(const Tx::State& state,std::string_view identity="fixture-file") {
    auto manifest=Source::draft(state,identity);manifest["approved"]=true;manifest["permit_id"]="SYNTHETIC_PERMISSION_1";
    manifest["operator_note"]="Synthetic explicit capacity authorization; no native unlock claim";
    for(unsigned i=1;i<300;++i)manifest["new_bank_indices"].push_back(i);
    return manifest;
}
void planner() {
    const auto old=synthetic();const Tx::Before before{old.inventory,old.equipment};
    const auto draft=Source::draft(old,"fixture-file");
    require(draft.at("approved")==false&&draft.at("new_bank_indices").empty(),"Draft must not manufacture approval or cells");
    rejects([&]{Source::plan(draft,before,"fixture-file");},"Unapproved draft must refuse");
    const auto manifest=approved(old);const auto plan=Source::plan(Source::parse(manifest.dump()),before,"fixture-file");
    require(plan.next.inventory.cells.size()==330&&plan.next.inventory.cells[5].instance==old.inventory.cells[5].instance,
        "Only empty source cells may be added; all instance/alias/acquisition/full25 retained");
    require(plan.next.equipment.record==old.equipment.record&&plan.next.equipment.position==old.equipment.position&&
        NativeEquipmentSnapshot::same_root(plan.next.equipment.root,old.equipment.root)&&plan.next.equipment.actor_handle==old.equipment.actor_handle,
        "Capacity must not generate native cache, DA, actor or pose");
    require(plan.next.inventory.revision==2&&plan.next.equipment.revision==2&&
        plan.next.inventory.source_sha256==old.inventory.source_sha256,"Joint revisions advance, original source pin retained");
    auto bad=manifest;bad["new_bank_indices"].push_back(0u);
    rejects([&]{Source::plan(bad,before,"fixture-file");},"Existing capacity may not be overwritten");
    bad=manifest;bad["new_bank_indices"].erase(bad["new_bank_indices"].end()-1);
    rejects([&]{Source::plan(bad,before,"fixture-file");},"Partial capacity must not claim bank ready");
    bad=manifest;bad["new_bank_indices"][0]=300u;
    rejects([&]{Source::plan(bad,before,"fixture-file");},"Bank namespace overflow");
    rejects([&]{Source::plan(manifest,before,"other-file");},"Same values in a foreign file are not import authority");
    rejects([&]{Source::plan(manifest,{},"fixture-file");},"Missing initial population must not be manufactured");
    for(const auto* part:{"inventory","equipment"}) {
        bad=manifest;bad["expected_material"][part]["source_record"]="changed";
        rejects([&]{Source::plan(bad,before,"fixture-file");},"Full original provenance is part of CAS");
    }
    bad=manifest;bad["expected_material"]["inventory"]["cells"][5]["instance"]["aliases"][0]["record"][24]=0u;
    rejects([&]{Source::plan(bad,before,"fixture-file");},"Opaque full25 tail must be compared");
    bad=manifest;bad["account_id"]=1.0;
    rejects([&]{Source::plan(bad,before,"fixture-file");},"Direct typed caller cannot bypass float refusal");
    rejects([&]{Source::parse("{\"x\":1,\"x\":2}");},"Duplicate manifest keys");
    rejects([&]{Source::parse("{\"x\":1.0}");},"Floating point manifest values");
    auto exhausted=old;exhausted.inventory.revision=0x7fffffffffffffffULL;
    rejects([&]{Source::plan(approved(exhausted),{exhausted.inventory,exhausted.equipment},"fixture-file");},"Revision exhaustion must fail closed");
}
int child(const std::filesystem::path& file) {
    try{auto guard=SqliteProcessOwnership::acquire(file,SqliteProcessOwnership::Mode::Exclusive);return guard->current()?0:24;}
    catch(const std::exception&){return 23;}
}
int process_probe(const std::filesystem::path& executable,const std::filesystem::path& file) {
#ifdef _WIN32
    std::wstring command=L"\""+executable.wstring()+L"\" --exclusive-probe \""+file.wstring()+L"\"";
    STARTUPINFOW startup{};startup.cb=sizeof(startup);PROCESS_INFORMATION process{};
    require(CreateProcessW(executable.c_str(),command.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW,nullptr,nullptr,&startup,&process)!=0,"Cannot start isolated lock probe");
    CloseHandle(process.hThread);const auto waited=WaitForSingleObject(process.hProcess,10000);DWORD status=25;
    if(waited==WAIT_OBJECT_0)GetExitCodeProcess(process.hProcess,&status);else TerminateProcess(process.hProcess,25);
    CloseHandle(process.hProcess);require(waited==WAIT_OBJECT_0,"Isolated lock probe did not finish");return static_cast<int>(status);
#else
    const auto pid=fork();require(pid>=0,"Cannot fork isolated lock probe");
    if(pid==0){execl(executable.c_str(),executable.c_str(),"--exclusive-probe",file.c_str(),nullptr);_exit(26);}
    int status=0;require(waitpid(pid,&status,0)==pid&&WIFEXITED(status),"Lock probe failed");return WEXITSTATUS(status);
#endif
}
void ownership(const std::filesystem::path& executable,const std::filesystem::path& file) {
    {std::ofstream out(file,std::ios::binary);out<<"SYNTHETIC-LOCK-NOT-SQLITE";}
    const auto size=std::filesystem::file_size(file);
    auto first=SqliteProcessOwnership::acquire(file,SqliteProcessOwnership::Mode::Shared);
    auto second=SqliteProcessOwnership::acquire(file,SqliteProcessOwnership::Mode::Shared);
    require(first->file_identity()==second->file_identity()&&first->path_current(),"Actual same-file owner identity");
    rejects([&]{SqliteProcessOwnership::acquire(file,SqliteProcessOwnership::Mode::Exclusive);},"Same-process distinct handles must conflict");
    const auto alias=file.parent_path()/"same-file-hardlink.bin";
    std::filesystem::create_hard_link(file,alias);
    auto alias_owner=SqliteProcessOwnership::acquire(alias,SqliteProcessOwnership::Mode::Shared);
    require(alias_owner->file_identity()==first->file_identity(),"Hardlink aliases must retain same actual file identity");
    rejects([&]{SqliteProcessOwnership::acquire(alias,SqliteProcessOwnership::Mode::Exclusive);},"Hardlinks must not bypass shared current owners");
    require(process_probe(executable,file)==23,"Other-process exclusive must fail while normal owners are idle");
    first.reset();second.reset();alias_owner.reset();
    require(process_probe(executable,file)==0,"Owner release must permit later explicit offline operation");
    auto exclusive=SqliteProcessOwnership::acquire(file,SqliteProcessOwnership::Mode::Exclusive);
    rejects([&]{SqliteProcessOwnership::acquire(file,SqliteProcessOwnership::Mode::Shared);},"Offline exclusive excludes new server startup");
    require(std::filesystem::file_size(file)==size,"High range lock must not extend DB file");exclusive.reset();
    rejects([&]{SqliteProcessOwnership::acquire(":memory:",SqliteProcessOwnership::Mode::Exclusive);},"Memory DB cannot claim offline ownership");
}
void actual_source(const std::filesystem::path& file) {
    auto initial=synthetic();sqlite3* raw=nullptr;
    require(sqlite3_open(file.string().c_str(),&raw)==SQLITE_OK,"Private source fixture open");
    {std::unique_ptr<sqlite3,decltype(&sqlite3_close)> db(raw,sqlite3_close);
     SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
     SqliteAccountRepository accounts(raw);SqliteRecoveredCharacterRepository characters(raw);
     const auto account=accounts.create("capacity-fixture","not-a-real-credential");
     std::array<std::uint8_t,40> profile{};profile[0]='A';
     const auto root=characters.create(account.id,profile);initial.inventory.root=initial.equipment.root=root;
     initial.equipment.position=characters.commit_position(root.account_id,root.id,{},1,1,18,14);
     sqlite_detail::execute(raw,SqliteOwnedInventoryRepository::schema());
     sqlite_detail::execute(raw,SqliteNativeEquipmentSnapshotRepository::schema());
     SqliteOwnedInventoryRepository inventory(raw,accounts,characters);SqliteNativeEquipmentSnapshotRepository equipment(raw,accounts,characters);
     Tx joint(inventory,equipment);
     require(joint.replace_from_issuer({},initial,[](const auto&,const auto& next,auto){return std::optional{next};}).has_value(),"Synthetic fixture material only");}
    nlohmann::json manifest;
    {SqliteDatabase offline(file,std::vector<Migration>{});offline.initialize_existing_for_owned_bank_capacity();
     manifest=offline.owned_bank_capacity_draft(initial.inventory.root.account_id,initial.inventory.root.id);
     manifest["approved"]=true;manifest["permit_id"]="SYNTHETIC_ACTUAL_SOURCE";manifest["operator_note"]="Private fixture explicit capacity permission";
     for(unsigned n=1;n<300;++n)manifest["new_bank_indices"].push_back(n);
     const auto result=offline.provision_owned_bank_capacity(Source::parse(manifest.dump()));
     require(result.commit_confirmed&&result.connection_current,"Actual dedicated source must commit one joint CAS");
     rejects([&]{offline.provision_owned_bank_capacity(manifest);},"Replayed complete old manifest must not retry");
     rejects([&]{offline.migrate();},"Capacity owner cannot execute migrations");}
    {SqliteDatabase live(file);live.initialize();
     SqliteDatabase offline(file,std::vector<Migration>{});
     rejects([&]{offline.initialize_existing_for_owned_bank_capacity();},"Actual normal Database lifetime blocks offline source with no Session/SQL active");}
}
}
int main(int argc,char** argv)try {
    if(argc==3&&std::string_view(argv[1])=="--exclusive-probe") {
#ifdef _WIN32
        int count=0;auto** wide=CommandLineToArgvW(GetCommandLineW(),&count);
        require(wide&&count==3,"Actual child Unicode arguments unavailable");
        struct End{LPWSTR* value;~End(){LocalFree(value);}} end{wide};
        return child(std::filesystem::path(wide[2]));
#else
        return child(std::filesystem::u8path(argv[2]));
#endif
    }
    const auto root=std::filesystem::temp_directory_path()/("god2-capacity-source-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    require(std::filesystem::create_directory(root),"Private test root must be freshly created");
    struct End{std::filesystem::path root;~End(){std::error_code ignored;std::filesystem::remove_all(root,ignored);}} end{root};
    planner();ownership(std::filesystem::absolute(argv[0]),root/"ownership-fixture.bin");actual_source(root/"source-fixture.sqlite");
    std::cout<<"CUSTOM-0163 synthetic source regressions; not native unlock acceptance\n";return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
