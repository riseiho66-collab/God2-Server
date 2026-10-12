"""One-shot source edit/custody only. No target API/SQL/compiler/test execution."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(name,b):
 p=OUT/name
 if p.exists():raise RuntimeError('Refusing overwrite '+name)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def js(name,x):emit(name,(json.dumps(x,indent=2)+'\n').encode())
if (OUT/'generation-manifest.json').exists():raise RuntimeError('Already generated')
paths=['src/db/SqliteOwnedBlacklistRepository.h','src/db/SqliteOwnedBlacklistRepository.cpp',
       'src/handlers/OwnedBlacklistService.h','src/handlers/OwnedBlacklistService.cpp']
old={p:(ROOT/p).read_bytes() for p in paths}
text={p:b.decode().replace('\r\n','\n') for p,b in old.items()}
for p,b in old.items():emit('before/'+p,b)
edits=[]
def change(path,original,replacement):
 if text[path].count(original)!=1:raise RuntimeError('Nonunique edit '+path+' '+original[:70])
 text[path]=text[path].replace(original,replacement,1)
 edits.append({'path':path,'original':original,'replacement':replacement})
rh,rc,sh,sc=paths
change(rh,'#include <cstdint>\n','#include <cstdint>\n#include <utility>\n')
change(rh,'namespace god2 {\n','namespace god2 {\nclass OwnedBlacklistService;\n')
change(rh,'    Snapshot load(std::uint64_t account,std::uint64_t character,Current);\n','''    Snapshot load(std::uint64_t account,std::uint64_t character,Current);
    // Exact material from this actual owned operation, allocated and qualified
    // inside its one transaction before COMMIT. No observation or public mint.
    // changed=false retains the original idempotent reply, never a fanout event.
    class CommittedChange {
    public:
        CommittedChange(const CommittedChange&)=delete;
        CommittedChange& operator=(const CommittedChange&)=delete;
        CommittedChange(CommittedChange&&) noexcept=default;
        CommittedChange& operator=(CommittedChange&&) noexcept=default;
        const Snapshot& before() const noexcept{return before_;}
        const Snapshot& after() const noexcept{return after_;}
        const Row& row() const noexcept{return row_;}
        const std::vector<std::uint8_t>& logical() const noexcept{return logical_;}
        bool changed() const noexcept{return changed_;}
    private:
        friend class SqliteOwnedBlacklistRepository;
        friend class OwnedBlacklistService;
        CommittedChange(Snapshot before,Snapshot after,Row row,
            std::vector<std::uint8_t> logical,bool changed) noexcept
            :before_(std::move(before)),after_(std::move(after)),row_(std::move(row)),
             logical_(std::move(logical)),changed_(changed) {}
        Snapshot before_,after_;
        Row row_;
        std::vector<std::uint8_t> logical_;
        bool changed_;
    };
    std::optional<CommittedChange> add_committed(std::uint64_t account,std::uint64_t character,std::string_view name,Current);
    std::optional<CommittedChange> remove_committed(std::uint64_t account,std::uint64_t character,std::uint32_t row_id,Current);
''')
change(rh,'    std::vector<Row> rows(std::uint64_t account,std::uint64_t character);\n','''    std::vector<Row> rows(std::uint64_t account,std::uint64_t character);
    CommittedChange prepare_committed_change(const Snapshot&,Row,bool,Operation&,const Root&,const Root*);
''')
change(rc,'#include "db/SqliteSupport.h"\n','#include "db/SqliteSupport.h"\n#include "protocol/TaiwanNativeBlacklist.h"\n')
start=text[rc].index('std::optional<SqliteOwnedBlacklistRepository::Row> SqliteOwnedBlacklistRepository::add(')
original=text[rc][start:-2]
replacement='''SqliteOwnedBlacklistRepository::CommittedChange SqliteOwnedBlacklistRepository::prepare_committed_change(
        const Snapshot& before,Row row,bool changed,Operation& operation,const Root& root,const Root* target) {
    const auto target_root=target?std::optional<Root>(*target):std::nullopt;
    auto expected=before.rows; // The actual before is never mutated or moved from.
    const auto at=std::find_if(expected.begin(),expected.end(),[&](const auto& r){return r.row_id==row.row_id;});
    if(at==expected.end()) {
        if(!changed || !row.active)throw DatabaseError("Blacklist committed new row invalid");
        expected.push_back(row);
    } else {
        auto same=*at;same.active=row.active;
        if(same!=row || changed==(at->active==row.active))
            throw DatabaseError("Blacklist committed row identity/change mismatch");
        *at=row;
    }
    operation.roots(root,target_root);
    auto after=rows(root.account,root.id); // Actual staged rows, not a post-COMMIT observation.
    operation.roots(root,target_root);
    if(!before.supported || after!=expected || (!changed && after!=before.rows))
        throw DatabaseError("Blacklist complete committed change mismatch");
    auto logical=row.active?TaiwanNativeBlacklist::added(row.row_id,row.name):TaiwanNativeBlacklist::removed(row.row_id);
    if(!logical)throw DatabaseError("Committed owned blacklist projection invalid");
    return CommittedChange(before,Snapshot{true,std::move(after)},std::move(row),std::move(*logical),changed);
}
std::optional<SqliteOwnedBlacklistRepository::CommittedChange> SqliteOwnedBlacklistRepository::add_committed(
        std::uint64_t account,std::uint64_t character,std::string_view input,Current current) {
    Operation operation(*this,std::move(current));
    const std::string name(input); // Own bytes and actual Current before SQL.
    operation.fence();
    if(!OwnedCharacterNameText::from_encoded(name,950))return {};
    qualify(true);operation.fence();
    sqlite_detail::Transaction transaction(db_);connection(db_,true,false);operation.fence();const auto root=owner(account,character);
    if(root.codepage!=950 || ascii_equal(root.name,name))return {};
    const Snapshot before{true,rows(account,character)};
    const auto active=std::count_if(before.rows.begin(),before.rows.end(),[](const Row& r){return r.active;});
    for(const auto& row:before.rows)if(row.name==name) {
        Row selected=row;const bool changed=!row.active;
        if(changed) {
            if(active>=10)return {};
            operation.roots(root);
            const auto changes=sqlite3_total_changes64(db_);
            sqlite_detail::Statement reactivate(db_,"UPDATE main.character_blacklist_entries SET active=1 WHERE row_id=? AND account_id=? AND character_id=? AND active=0");
            reactivate.bind_id(1,row.row_id);reactivate.bind_id(2,account);reactivate.bind_id(3,character);operation.roots(root);reactivate.done();
            if(sqlite3_changes(db_)!=1 || sqlite3_total_changes64(db_)!=changes+1)throw DatabaseError("Blacklist reactivation conflict");
            selected.active=true;
        }
        std::optional<CommittedChange> result(prepare_committed_change(before,std::move(selected),changed,operation,root,nullptr));
        operation.roots(root);transaction.commit();return result;
    }
    if(active>=10 || before.rows.size()>=4096)return {}; // CUSTOM-0096, not native permission.
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
    std::optional<CommittedChange> result(prepare_committed_change(before,
        Row{std::uint32_t(id),account,character,target_root->id,name,true},true,operation,root,&*target_root));
    operation.roots(root,target_root);transaction.commit();return result;
}
std::optional<SqliteOwnedBlacklistRepository::CommittedChange> SqliteOwnedBlacklistRepository::remove_committed(
        std::uint64_t account,std::uint64_t character,std::uint32_t row_id,Current current) {
    Operation operation(*this,std::move(current));operation.fence();
    if(!row_id || row_id==0xffffffffu)return {};
    qualify(true);operation.fence();sqlite_detail::Transaction transaction(db_);connection(db_,true,false);operation.fence();const auto root=owner(account,character);
    if(root.codepage!=950)return {};
    const Snapshot before{true,rows(account,character)};
    const auto at=std::find_if(before.rows.begin(),before.rows.end(),[&](const auto& row){return row.row_id==row_id;});
    if(at==before.rows.end())return {};
    Row selected=*at;const bool changed=selected.active;
    if(changed) {
        operation.roots(root);
        const auto changes=sqlite3_total_changes64(db_);
        sqlite_detail::Statement remove(db_,"UPDATE main.character_blacklist_entries SET active=0 WHERE row_id=? AND account_id=? AND character_id=? AND target_character_id=? AND name_bytes=? AND active=1");
        remove.bind_id(1,row_id);remove.bind_id(2,account);remove.bind_id(3,character);remove.bind_id(4,selected.target_character);
        remove.bind_blob(5,std::span<const std::uint8_t>(reinterpret_cast<const std::uint8_t*>(selected.name.data()),selected.name.size()));operation.roots(root);remove.done();
        if(sqlite3_changes(db_)!=1 || sqlite3_total_changes64(db_)!=changes+1)throw DatabaseError("Blacklist deletion ownership conflict");
        selected.active=false;
    }
    std::optional<CommittedChange> result(prepare_committed_change(before,std::move(selected),changed,operation,root,nullptr));
    operation.roots(root);transaction.commit();return result;
}
std::optional<SqliteOwnedBlacklistRepository::Row> SqliteOwnedBlacklistRepository::add(
        std::uint64_t account,std::uint64_t character,std::string_view input,Current current) {
    auto result=add_committed(account,character,input,std::move(current));
    if(!result)return {};
    return std::optional<Row>(std::move(result->row_));
}
std::optional<SqliteOwnedBlacklistRepository::Row> SqliteOwnedBlacklistRepository::remove(
        std::uint64_t account,std::uint64_t character,std::uint32_t row_id,Current current) {
    auto result=remove_committed(account,character,row_id,std::move(current));
    if(!result)return {};
    return std::optional<Row>(std::move(result->row_));
}
'''
change(rc,original,replacement)
change(sh,'    struct Replay {std::vector<std::uint8_t> logical;std::uint32_t last_row;bool done;};\n','''    std::optional<SqliteOwnedBlacklistRepository::CommittedChange> handle_committed(
        std::uint64_t account,std::uint64_t character,const TaiwanNativeBlacklist::Request&,
        SqliteOwnedBlacklistRepository::Current);
    struct Replay {std::vector<std::uint8_t> logical;std::uint32_t last_row;bool done;};
''')
oldhandle=text[sc][text[sc].index('std::optional<std::vector<std::uint8_t>> OwnedBlacklistService::handle('):text[sc].index('SqliteOwnedBlacklistRepository::Snapshot OwnedBlacklistService::observe(')]
change(sc,oldhandle,'''std::optional<SqliteOwnedBlacklistRepository::CommittedChange> OwnedBlacklistService::handle_committed(
        std::uint64_t account,std::uint64_t character,const TaiwanNativeBlacklist::Request& actual,SqliteOwnedBlacklistRepository::Current current) {
    const auto request=actual; // Own original bytes before any storage observer.
    return request.adding()?repository_.add_committed(account,character,request.name(),std::move(current)):
        repository_.remove_committed(account,character,request.row_id(),std::move(current));
}
std::optional<std::vector<std::uint8_t>> OwnedBlacklistService::handle(
        std::uint64_t account,std::uint64_t character,const TaiwanNativeBlacklist::Request& actual,SqliteOwnedBlacklistRepository::Current current) {
    auto result=handle_committed(account,character,actual,std::move(current));
    if(!result)return std::vector<std::uint8_t>{}; // Original rejected/no-mutation behavior.
    // Move the exact pre-COMMIT original projection; no allocation/re-observation.
    return std::optional<std::vector<std::uint8_t>>(std::move(result->logical_));
}
''')
for p in paths:
 inverse=text[p]
 for e in reversed(edits):
  if e['path']==p:
   if inverse.count(e['replacement'])!=1:raise RuntimeError('Inverse nonunique '+p)
   inverse=inverse.replace(e['replacement'],e['original'],1)
 ending='\r\n' if b'\r\n' in old[p] else '\n'
 if inverse.replace('\n',ending).encode()!=old[p]:raise RuntimeError('Inverse mismatch '+p)
 new=text[p].replace('\n',ending).encode()
 if (ROOT/p).read_bytes()!=old[p]:raise RuntimeError('Source changed before edit '+p)
 (ROOT/p).write_bytes(new);emit('candidate/'+p,new)
js('exact-edits-and-inverse.json',{'edits':edits,'all_four_inverse_byte_equal':True})
js('generation-manifest.json',{'head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),
 'files':[{'path':p,'before_bytes':len(old[p]),'before_sha256':sha(old[p]),'candidate_bytes':len((ROOT/p).read_bytes()),
           'candidate_sha256':sha((ROOT/p).read_bytes()),'line_endings_preserved':True} for p in paths],
 'scope':'Only four authorized source edits; all source-only. No target/SQL/API/compiler/tests.',
 'private_token':'Move-only, privately constructed complete before/after+row+wire+changed actual transaction result; allocations and actual after rows before COMMIT.'})
print(json.dumps({'files':[{ 'path':p,'bytes':len((ROOT/p).read_bytes()),'sha256':sha((ROOT/p).read_bytes())} for p in paths]}))
