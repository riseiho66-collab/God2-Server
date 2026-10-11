#include "db/SqliteOwnedBlacklistRepository.h"
#include "db/SqliteSupport.h"
#include "text/OwnedCharacterNameText.h"
#include <algorithm>
#include <array>
#include <span>
#include <stdexcept>
namespace god2 {
namespace {
// Exact fresh schema; SQLite persists CREATE TABLE without its main qualifier.
constexpr auto stored_schema="CREATE TABLE character_blacklist_entries(row_id INTEGER PRIMARY KEY AUTOINCREMENT CHECK(row_id BETWEEN 1 AND 4294967294),account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,target_character_id INTEGER NOT NULL CHECK(target_character_id>0),name_bytes BLOB NOT NULL CHECK(typeof(name_bytes)='blob' AND length(name_bytes) BETWEEN 1 AND 14),name_codepage INTEGER NOT NULL CHECK(name_codepage=950),active INTEGER NOT NULL CHECK(active IN (0,1)),design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0096'),UNIQUE(character_id,name_bytes))";
void connection(sqlite3* db,bool installed,bool require_autocommit=true) {
    if(!db || (require_autocommit && !sqlite3_get_autocommit(db)))throw DatabaseError("Blacklist requires owned autocommit connection");
    sqlite_detail::Statement fk(db,"PRAGMA foreign_keys");
    if(!fk.row() || fk.integer(0)!=1)throw DatabaseError("Blacklist foreign keys unavailable");
    sqlite_detail::Statement shadows(db,"SELECT 1 FROM temp.sqlite_master WHERE lower(name) IN ('accounts','recovered_characters','character_blacklist_entries','sqlite_sequence') OR lower(tbl_name) IN ('accounts','recovered_characters','character_blacklist_entries','sqlite_sequence') LIMIT 1");
    if(shadows.row())throw DatabaseError("Blacklist TEMP source shadow");
    for(const auto name:{"accounts","recovered_characters"}) {
        sqlite_detail::Statement base(db,"SELECT type FROM main.sqlite_master WHERE name=? COLLATE NOCASE");base.bind(1,std::string(name));
        if(!base.row() || base.text(0)!="table" || base.row())throw DatabaseError("Blacklist common source table missing");
    }
    sqlite_detail::Statement present(db,"SELECT type,sql FROM main.sqlite_master WHERE name='character_blacklist_entries' COLLATE NOCASE");
    const bool exists=present.row();
    if(installed?(!exists || present.text(0)!="table" || present.text(1)!=stored_schema || present.row()):exists)
        throw DatabaseError(installed?"Blacklist schema missing/invalid":"Blacklist fresh schema already exists");
    sqlite_detail::Statement triggers(db,"SELECT 1 FROM main.sqlite_master WHERE type='trigger' AND tbl_name='character_blacklist_entries' COLLATE NOCASE LIMIT 1");
    if(triggers.row())throw DatabaseError("Blacklist unexpected trigger");
    if(installed) {
        sqlite_detail::Statement indexes(db,"SELECT name,sql IS NULL FROM main.sqlite_master WHERE type='index' AND tbl_name='character_blacklist_entries' COLLATE NOCASE");
        if(!indexes.row() || indexes.text(0)!="sqlite_autoindex_character_blacklist_entries_1" ||
           indexes.integer(1)!=1 || indexes.row())throw DatabaseError("Blacklist index shape changed");
    }
}
bool ascii_equal(std::string_view a,std::string_view b) {
    const auto fold=[](unsigned char c){return c>='A' && c<='Z'?unsigned(c+'a'-'A'):unsigned(c);};
    return a.size()==b.size() && std::equal(a.begin(),a.end(),b.begin(),[&](unsigned char x,unsigned char y){return fold(x)==fold(y);});
}
}
struct SqliteOwnedBlacklistRepository::Root {
    std::uint64_t account,id;std::uint8_t slot;
    std::array<std::uint8_t,40> profile;
    std::string name,created;std::uint16_t codepage;std::uint8_t streamer;
    bool operator==(const Root&) const=default;
};
struct SqliteOwnedBlacklistRepository::Operation {
    SqliteOwnedBlacklistRepository& repo;Current current;
    Operation(SqliteOwnedBlacklistRepository& r,Current c):repo(r),current(std::move(c)) {
        if(repo.active_){repo.reentered_=true;throw DatabaseError("Blacklist source reentry");}
        if(!repo.db_ || !current)throw DatabaseError("Blacklist actual connection/Current missing");
        repo.active_=true;repo.reentered_=false;
    }
    ~Operation(){repo.active_=false;}
    void check() const {if(repo.reentered_)throw DatabaseError("Blacklist caught reentry invalidated operation");}
    void fence() const {
        check();const auto changes=sqlite3_total_changes64(repo.db_);const auto autocommit=sqlite3_get_autocommit(repo.db_);
        const bool ready=current();
        check();
        if(!ready || sqlite3_total_changes64(repo.db_)!=changes || sqlite3_get_autocommit(repo.db_)!=autocommit)
            throw DatabaseError("Blacklist pure Current/source changed");
    }
    void roots(const Root& expected,const std::optional<Root>& target={}) const {
        fence();
        if(repo.owner(expected.account,expected.id)!=expected ||
           (target && repo.owner(target->account,target->id)!=*target))throw DatabaseError("Blacklist full common root changed");
        fence(); // Any SQL observer may have closed/reentered the actual Session.
    }
};
void SqliteOwnedBlacklistRepository::qualify(bool installed){connection(db_,installed);}
void SqliteOwnedBlacklistRepository::install_schema(sqlite3* db) {
    connection(db,false);
    sqlite_detail::Transaction transaction(db);
    connection(db,false,false); // Requalify base/TEMP/fresh source inside the owned DDL transaction.
    // CUSTOM-0096: AUTOINCREMENT preserves committed row DWORDs after tombstones
    // and owner cascade. Target is captured provenance, deliberately NOT an FK:
    // rename/deletion cannot silently overwrite/remove the client's name cache.
    auto schema=std::string(stored_schema);schema.insert(std::string("CREATE TABLE ").size(),"main.");
    sqlite_detail::execute(db,schema);
    connection(db,true,false);
    transaction.commit();
}
SqliteOwnedBlacklistRepository::Root SqliteOwnedBlacklistRepository::owner(std::uint64_t account,std::uint64_t character) {
    if(!account || !character)throw DatabaseError("Blacklist owner absent");
    sqlite_detail::Statement q(db_,"SELECT c.account_id,c.id,c.slot,c.profile,c.name_bytes,c.name_codepage,c.created_at,c.streamer_privilege FROM main.recovered_characters c JOIN main.accounts a ON a.id=c.account_id WHERE c.id=? AND c.account_id=?");
    q.bind_id(1,character);q.bind_id(2,account);
    if(!q.row())throw DatabaseError("Blacklist common character missing");
    Root value{q.number<std::uint64_t>(0),q.number<std::uint64_t>(1),q.number<std::uint8_t>(2),{}, {}, {},0,0};
    const auto profile=q.blob(3,40,40),name=q.blob(4,1,14);
    std::copy(profile.begin(),profile.end(),value.profile.begin());
    value.name.assign(reinterpret_cast<const char*>(name.data()),name.size());
    value.codepage=q.number<std::uint16_t>(5);value.created=q.text(6);value.streamer=q.number<std::uint8_t>(7);
    const auto end=std::find(value.profile.begin(),value.profile.begin()+15,0);
    if(value.account!=account || value.id!=character || value.slot>1 || value.streamer>3 || value.created.empty() ||
       end==value.profile.begin()+15 || std::size_t(end-value.profile.begin())!=name.size() ||
       !std::equal(name.begin(),name.end(),value.profile.begin()) ||
       (value.codepage!=0 && value.codepage!=936 && value.codepage!=950) ||
       (value.codepage && !OwnedCharacterNameText::from_encoded(value.name,value.codepage)) || q.row())
        throw DatabaseError("Blacklist full common name/profile source invalid");
    return value;
}
std::vector<SqliteOwnedBlacklistRepository::Row> SqliteOwnedBlacklistRepository::rows(std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Statement q(db_,"SELECT row_id,account_id,character_id,target_character_id,name_bytes,name_codepage,design_id,active FROM main.character_blacklist_entries WHERE character_id=? ORDER BY row_id");q.bind_id(1,character);
    std::vector<Row> result;
    while(q.row()) {
        const auto name=q.blob(4,1,14);
        Row row{q.number<std::uint32_t>(0),q.number<std::uint64_t>(1),q.number<std::uint64_t>(2),q.number<std::uint64_t>(3),std::string(reinterpret_cast<const char*>(name.data()),name.size()),q.number<std::uint8_t>(7)==1};
        if(!row.row_id || row.row_id==0xffffffffu || row.account!=account || row.character!=character || !row.target_character ||
           q.number<std::uint16_t>(5)!=950 || q.text(6)!="CUSTOM-0096" ||
           !OwnedCharacterNameText::from_encoded(row.name,950) || q.integer(7)<0 || q.integer(7)>1 || result.size()>=4096)
            throw DatabaseError("Blacklist owned captured row invalid");
        result.push_back(std::move(row));
    }
    if(std::count_if(result.begin(),result.end(),[](const Row& r){return r.active;})>10)throw DatabaseError("Blacklist active quota invalid");
    return result;
}
SqliteOwnedBlacklistRepository::Snapshot SqliteOwnedBlacklistRepository::load(std::uint64_t account,std::uint64_t character,Current current) {
    Operation operation(*this,std::move(current));operation.fence();qualify(true);operation.fence();
    sqlite_detail::Transaction transaction(db_);connection(db_,true,false);operation.fence();const auto root=owner(account,character);
    Snapshot result{root.codepage==950,{}};
    if(result.supported)result.rows=rows(account,character);
    operation.roots(root);transaction.commit();return result;
}
std::optional<SqliteOwnedBlacklistRepository::Row> SqliteOwnedBlacklistRepository::add(
        std::uint64_t account,std::uint64_t character,std::string_view input,Current current) {
    Operation operation(*this,std::move(current));
    const std::string name(input); // Own bytes and actual Current before SQL.
    operation.fence();
    if(!OwnedCharacterNameText::from_encoded(name,950))return {};
    qualify(true);operation.fence();
    sqlite_detail::Transaction transaction(db_);connection(db_,true,false);operation.fence();const auto root=owner(account,character);
    if(root.codepage!=950 || ascii_equal(root.name,name))return {};
    auto before=rows(account,character);
    const auto active=std::count_if(before.begin(),before.end(),[](const Row& r){return r.active;});
    for(auto& row:before)if(row.name==name) {
        if(!row.active) {
            if(active>=10)return {};
            operation.roots(root);
            const auto changes=sqlite3_total_changes64(db_);
            sqlite_detail::Statement reactivate(db_,"UPDATE main.character_blacklist_entries SET active=1 WHERE row_id=? AND account_id=? AND character_id=? AND active=0");
            reactivate.bind_id(1,row.row_id);reactivate.bind_id(2,account);reactivate.bind_id(3,character);operation.roots(root);reactivate.done();
            if(sqlite3_changes(db_)!=1 || sqlite3_total_changes64(db_)!=changes+1)throw DatabaseError("Blacklist reactivation conflict");
            row.active=true;
        }
        std::optional<Row> result(std::move(row));operation.roots(root);transaction.commit();return result;
    }
    if(active>=10 || before.size()>=4096)return {}; // CUSTOM-0096, not native permission.
    std::optional<Root> target_root;
    {
        sqlite_detail::Statement target(db_,"SELECT c.id,c.account_id FROM main.recovered_characters c JOIN main.accounts a ON a.id=c.account_id WHERE c.name_codepage=950 AND c.name_bytes=? ORDER BY c.id");
        target.bind_blob(1,std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(name.data()),name.size()));
        while(target.row()) {
            if(target_root)return {}; // Exact same-codepage ambiguity never guesses.
            target_root=owner(target.number<std::uint64_t>(1),target.number<std::uint64_t>(0));
            if(target_root->codepage!=950 || target_root->name!=name)throw DatabaseError("Blacklist target mismatch");
        }
    }
    if(!target_root || target_root->id==character)return {};
    {
        sqlite_detail::Statement sequence(db_,"SELECT seq FROM main.sqlite_sequence WHERE name='character_blacklist_entries'");
        if(sequence.row()) {
            const auto allocated=sequence.number<std::uint64_t>(0);
            if(sequence.row())throw DatabaseError("Blacklist allocator ambiguous");
            if(allocated>=0xfffffffeu)return {}; // Exhausted reserved DWORD namespace; no mutation/reply.
        }
    }
    operation.roots(root,target_root);
    const auto changes=sqlite3_total_changes64(db_);
    sqlite_detail::Statement insert(db_,"INSERT INTO main.character_blacklist_entries(account_id,character_id,target_character_id,name_bytes,name_codepage,active,design_id) VALUES(?,?,?,?,950,1,'CUSTOM-0096')");
    insert.bind_id(1,account);insert.bind_id(2,character);insert.bind_id(3,target_root->id);
    insert.bind_blob(4,std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(name.data()),name.size()));operation.roots(root,target_root);insert.done();
    const auto id=sqlite3_last_insert_rowid(db_);
    if(id<=0 || std::uint64_t(id)>0xfffffffeu || sqlite3_changes(db_)!=1 || sqlite3_total_changes64(db_)!=changes+1)
        throw DatabaseError("Blacklist allocation/write conflict");
    std::optional<Row> result(Row{std::uint32_t(id),account,character,target_root->id,name,true});
    operation.roots(root,target_root);transaction.commit();return result;
}
std::optional<SqliteOwnedBlacklistRepository::Row> SqliteOwnedBlacklistRepository::remove(
        std::uint64_t account,std::uint64_t character,std::uint32_t row_id,Current current) {
    Operation operation(*this,std::move(current));operation.fence();
    if(!row_id || row_id==0xffffffffu)return {};
    qualify(true);operation.fence();sqlite_detail::Transaction transaction(db_);connection(db_,true,false);operation.fence();const auto root=owner(account,character);
    if(root.codepage!=950)return {};
    auto before=rows(account,character);
    const auto at=std::find_if(before.begin(),before.end(),[&](const auto& row){return row.row_id==row_id;});
    if(at==before.end())return {};
    std::optional<Row> result(*at);
    if(!result->active){operation.roots(root);transaction.commit();return result;}
    operation.roots(root);
    const auto changes=sqlite3_total_changes64(db_);
    sqlite_detail::Statement remove(db_,"UPDATE main.character_blacklist_entries SET active=0 WHERE row_id=? AND account_id=? AND character_id=? AND target_character_id=? AND name_bytes=? AND active=1");
    remove.bind_id(1,row_id);remove.bind_id(2,account);remove.bind_id(3,character);remove.bind_id(4,result->target_character);
    remove.bind_blob(5,std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(result->name.data()),result->name.size()));operation.roots(root);remove.done();
    if(sqlite3_changes(db_)!=1 || sqlite3_total_changes64(db_)!=changes+1)throw DatabaseError("Blacklist deletion ownership conflict");
    result->active=false;operation.roots(root);transaction.commit();return result;
}
}
