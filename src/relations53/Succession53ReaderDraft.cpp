#include "Succession53ReaderDraft.h"
#include "db/SqliteSupport.h"
#include "db/SqliteMigrationManager.h"
#include "RelationsSchemaDraft.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>
#include <set>

namespace god2 {
namespace {
using Repo=Succession53ReaderDraft;
using Legacy=Repo::Original;
constexpr auto source="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool value,const char* message){if(!value)throw DatabaseError(message);}
void positive(std::uint64_t value){require(value && value<=maximum,"Invalid effective ownership identity/revision");}
void provenance(const sqlite_detail::Statement& q,int at,const char* design){
    require(q.text(at)=="CUSTOM_DESIGNED" && q.text(at+1)==design && q.text(at+2)==source,"Effective ownership provenance mismatch");
}
void nonbattle(sqlite3* db,std::uint64_t character){
    sqlite_detail::Statement q(db,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    q.bind_id(1,character);require(!q.row(),"CUSTOM transfer nonbattle policy denied");
}
// Exact typed whole-save preservation helpers reused as a NEW source copy.
#include "preservation.inc"
Rows selected_rows(sqlite3* db,const std::string& sql){
    sqlite3_stmt* raw=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&raw,nullptr));
    struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{raw};
    Rows rows;int rc;
    while((rc=sqlite3_step(raw))==SQLITE_ROW){
        std::vector<std::uint8_t> row;
        for(int c=0;c<sqlite3_column_count(raw);++c){
            const auto type=sqlite3_column_type(raw,c);row.push_back(static_cast<std::uint8_t>(type));
            if(type==SQLITE_INTEGER)append_number(row,std::bit_cast<std::uint64_t>(sqlite3_column_int64(raw,c)));
            else if(type==SQLITE_FLOAT)append_number(row,std::bit_cast<std::uint64_t>(sqlite3_column_double(raw,c)));
            else if(type==SQLITE_TEXT || type==SQLITE_BLOB){
                const auto size=sqlite3_column_bytes(raw,c);append_number(row,static_cast<std::uint64_t>(size));
                const auto* data=type==SQLITE_TEXT?sqlite3_column_text(raw,c):static_cast<const unsigned char*>(sqlite3_column_blob(raw,c));
                require(size>=0 && (!size || data),"Invalid typed SQL bytes");if(size)row.insert(row.end(),data,data+size);
            }
        }
        rows.push_back(std::move(row));
    }
    require(rc==SQLITE_DONE,"Typed SQL read failed");std::sort(rows.begin(),rows.end());return rows;
}
Repo::TypedLease local_lease(sqlite3* db,std::uint64_t id){
    Repo::TypedLease result;
    for(const auto* table:{"owned_guilds","owned_guild_governance_0078","owned_guild_members","owned_guild_applications_0078","owned_guild_officers_0082","owned_guild_successions_0083"}){
        const auto key=std::string(table);const auto column=key=="owned_guilds"?"id":"guild_id";
        result[key]=selected_rows(db,"SELECT * FROM "+quoted(key)+" WHERE "+column+"="+std::to_string(id));
    }
    return result;
}
Rows stable_guild_columns(sqlite3* db,std::uint64_t id){
    sqlite_detail::Statement fields(db,"PRAGMA table_info(owned_guilds)");std::string selected;
    while(fields.row())if(fields.text(1)!="revision"){if(!selected.empty())selected+=',';selected+=quoted(fields.text(1));}
    require(!selected.empty(),"Guild columns missing");return selected_rows(db,"SELECT "+selected+" FROM owned_guilds WHERE id="+std::to_string(id));
}
void unambiguous(const std::vector<GuildRosterMember>& members){
    for(const auto cn:{false,true}){
        std::set<std::string> names;
        for(const auto& member:members){
            auto bytes=LegacyChineseCodec::encode(member.name_utf8,cn);
            for(auto& c:bytes)if(static_cast<unsigned char>(c)>='A' && static_cast<unsigned char>(c)<='Z')c+=32;
            require(names.insert(bytes).second,"Ambiguous native folded roster names");
        }
    }
}
struct ReadScope {
    sqlite3* db;bool owned,complete=false;
    explicit ReadScope(sqlite3* input):db(input),owned(sqlite3_get_autocommit(db)!=0){if(owned)sqlite_detail::execute(db,"BEGIN");}
    void finish(){if(owned)sqlite_detail::execute(db,"COMMIT");complete=true;}
    ~ReadScope(){if(owned && !complete)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
};
}
std::string Succession53ReaderDraft::schema52_proposal(){
#include "schema52.inc"
}
Succession53ReaderDraft::Succession53ReaderDraft(sqlite3* db,Original& legacy)
    :db_(db),legacy_(legacy),transfer_enabled_(false){require(db_!=nullptr,"Null succession database");exact_schema53();}
void Succession53ReaderDraft::exact_schema53(){
    auto migrations=owned_guild_announcement_migrations();require(migrations.size()==50,"Compiled50 migration vector missing");
    migrations.push_back({51,"owned_guild_officers_candidate",Original::officer_schema()});
    migrations.push_back({52,"owned_guild_successions_candidate",schema52_proposal()});
    migrations.push_back({53,"owned_guild_relations_private",relation53_migration()});
    sqlite_detail::Statement q(db_,"SELECT version,name,sql_text FROM schema_migrations ORDER BY version");std::size_t index=0;
    while(q.row()){
        require(index<migrations.size(),"Future schema denied");const auto& expected=migrations[index++];
        require(q.integer(0)==expected.version && q.text(1)==expected.name && q.text(2)==expected.sql,"Exact immutable1..52 history mismatch");
    }
    require(index==53,"Installed exact53 required; no downgrade/fallback");
    sqlite3* expected=nullptr;sqlite_detail::check(db_,sqlite3_open(":memory:",&expected));
    struct Close{sqlite3* p;~Close(){sqlite3_close_v2(p);}} close{expected};
    sqlite_detail::execute(expected,Original::officer_schema());
    sqlite_detail::execute(expected,schema52_proposal());
    sqlite_detail::execute(expected,relation53_ddl());
    const std::string objects="SELECT type,name,tbl_name,sql FROM sqlite_master WHERE tbl_name IN('owned_guild_officers_0082','owned_guild_successions_0083','owned_guild_relation_catalog_0084','owned_guild_relation_wire_ids_0084','owned_guild_relations_0084','owned_guild_relation_events_0084') ORDER BY type,name";
    require(selected_rows(db_,objects)==selected_rows(expected,objects),"Strict52 table/index/trigger/opaque schema mismatch");
}
bool Succession53ReaderDraft::succession_present(std::uint64_t id){
    positive(id);exact_schema53();sqlite_detail::Statement q(db_,"SELECT 1 FROM owned_guild_successions_0083 WHERE guild_id=?");q.bind_id(1,id);return q.row();
}
Succession53ReaderDraft::History Succession53ReaderDraft::history(std::uint64_t id){
    positive(id);exact_schema53();sqlite_detail::Statement q(db_,"SELECT guild_id,revision,previous_ownership_revision,guild_revision_before,from_account,from_character,from_slot,from_join_revision,to_account,to_character,to_slot,to_join_revision,target_previous_role,origin,design_id,source_sha256 FROM owned_guild_successions_0083 WHERE guild_id=? ORDER BY revision");
    q.bind_id(1,id);History result;
    while(q.row()){
        SuccessionRecord r;r.guild_id=q.number<std::uint64_t>(0);r.revision=q.number<std::uint64_t>(1);
        r.previous_ownership_revision=q.number<std::uint64_t>(2);r.guild_revision_before=q.number<std::uint64_t>(3);
        r.from={id,q.number<std::uint64_t>(4),q.number<std::uint64_t>(5),q.number<std::uint64_t>(7),r.previous_ownership_revision,q.number<std::uint8_t>(6)};
        r.to={id,q.number<std::uint64_t>(8),q.number<std::uint64_t>(9),q.number<std::uint64_t>(11),r.revision,q.number<std::uint8_t>(10)};
        r.target_previous_role=q.number<std::uint8_t>(12);provenance(q,13,"CUSTOM-0083");
        positive(r.revision);positive(r.guild_revision_before);positive(r.from.account_id);positive(r.from.character_id);positive(r.from.membership_revision);
        positive(r.to.account_id);positive(r.to.character_id);positive(r.to.membership_revision);
        require(r.guild_id==id && r.from.account_slot<=1 && r.to.account_slot<=1 && (r.target_previous_role==1 || r.target_previous_role==2) && r.from.character_id!=r.to.character_id &&
            r.from.membership_revision<=r.guild_revision_before && r.to.membership_revision<=r.guild_revision_before && r.guild_revision_before<r.revision,
            "Malformed succession audit row");
        if(result.empty())require(r.previous_ownership_revision==0,"Missing initial succession chain");
        else require(r.previous_ownership_revision==result.back().revision && r.from==result.back().to && result.back().revision<=r.guild_revision_before,"Broken ownership chain/ABA");
        result.push_back(r);
    }
    return result;
}
SqliteOwnedGuildMembershipRepository::Governance Succession53ReaderDraft::creation(std::uint64_t id){
    const auto g=legacy_.guild(id);sqlite_detail::Statement q(db_,"SELECT guild_id,owner_account,owner_character,created_revision,created_cost,capacity,origin,design_id,source_sha256 FROM owned_guild_governance_0078 WHERE guild_id=?");
    q.bind_id(1,id);require(q.row(),"Retired guild has no effective ownership");
    Original::Governance result{q.number<std::uint64_t>(0),q.number<std::uint64_t>(1),q.number<std::uint64_t>(2),q.number<std::uint64_t>(3),q.number<std::uint32_t>(4),q.number<std::uint8_t>(5)};
    positive(result.owner_account);positive(result.owner_character);positive(result.created_revision);provenance(q,6,"CUSTOM-0078");
    require(result.guild_id==id && result.created_revision<=g.revision && result.created_cost && result.capacity && result.capacity<=50,"Invalid historical creation");
    // Deliberately NO lookup of the original founder's current membership.
    return result;
}
std::vector<GuildRosterMember> Succession53ReaderDraft::roster(const Original::Guild& target){
    sqlite_detail::Statement q(db_,"SELECT m.character_id,m.revision,m.origin,m.design_id,m.source_sha256,c.account_id FROM owned_guild_members m LEFT JOIN recovered_characters c ON c.id=m.character_id WHERE m.guild_id=? ORDER BY m.character_id");
    q.bind_id(1,target.id);std::vector<GuildRosterMember> result;std::set<std::pair<std::uint64_t,std::uint8_t>> slots;
    while(q.row()){
        const auto character=q.number<std::uint64_t>(0),join=q.number<std::uint64_t>(1);positive(character);positive(join);provenance(q,2,"CUSTOM-0075");
        require(join<=target.revision,"Future join revision");auto member=legacy_.identity(q.number<std::uint64_t>(5),character);
        require(slots.emplace(member.account_id,member.slot).second,"Duplicate current join account/slot");member.membership_revision=join;result.push_back(member);
    }
    require(!result.empty() && result.size()<=50,"Incomplete accepted roster");unambiguous(result);return result;
}
Succession53ReaderDraft::EffectiveLeader Succession53ReaderDraft::effective_snapshot(std::uint64_t id){
    ReadScope scope(db_);exact_schema53();EffectiveLeader result;
    result.guild=legacy_.guild(id);result.original_creation=creation(id);result.succession_history=history(id);
    result.roster=roster(result.guild);require(result.roster.size()<=result.original_creation.capacity,"Roster exceeds creation capacity");
    const auto& gov=result.original_creation;
    if(result.succession_history.empty()){
        const auto who=legacy_.identity(gov.owner_account,gov.owner_character);
        result.owner={id,gov.owner_account,gov.owner_character,gov.created_revision,0,who.slot};
    }else{
        const auto& initial=result.succession_history.front();
        require(initial.from.account_id==gov.owner_account && initial.from.character_id==gov.owner_character && initial.from.membership_revision==gov.created_revision,
            "Succession source does not match immutable creation");
        require(result.succession_history.back().revision<=result.guild.revision,"Future ownership revision");result.owner=result.succession_history.back().to;
    }
    result.owner_identity=legacy_.identity(result.owner.account_id,result.owner.character_id);
    require(result.owner_identity.slot==result.owner.account_slot,"Owner character-slot ABA");
    SqliteGuildRepository memberships(db_);const auto member=memberships.load(result.owner.account_id,result.owner.character_id);
    require(member && *member==StoredGuildMembership{id,result.guild.name_utf8,result.guild.revision,result.owner.membership_revision},"Owner current join ABA or missing membership");
    result.owner_membership=*member;
    const auto owner_row=std::find_if(result.roster.begin(),result.roster.end(),[&](const auto& r){return r.character_id==result.owner.character_id;});
    require(owner_row!=result.roster.end() && owner_row->membership_revision==result.owner.membership_revision && owner_row->slot==result.owner.account_slot,"Owner absent from complete accepted audience");
    result.officer_history=legacy_.officer_history(id);
    for(const auto& row:result.officer_history){
        require(row.revision<=result.guild.revision,"Future officer audit");
        const auto current=std::find_if(result.roster.begin(),result.roster.end(),[&](const auto& r){return r.character_id==row.character_id && r.membership_revision==row.membership_revision;});
        if(current!=result.roster.end())require(current->account_id==row.account_id && current->slot==row.account_slot,"Current join officer audit identity mismatch");
    }
    result.persistent_guild_lease=local_lease(db_,id);scope.finish();return result;
}
Succession53ReaderDraft::EffectiveLeader Succession53ReaderDraft::effective_leader(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);const auto member=SqliteGuildRepository(db_).load(account,character);require(bool(member),"Effective leader not accepted");
    auto result=effective_snapshot(member->guild_id);
    require(result.owner.account_id==account && result.owner.character_id==character,"Not the current effective owner");nonbattle(db_,character);scope.finish();return result;
}
std::vector<SqliteOwnedGuildMembershipRepository::Application> Succession53ReaderDraft::applications(std::uint64_t id){
    ReadScope scope(db_);const auto effective=effective_snapshot(id);
    sqlite_detail::Statement q(db_,"SELECT id,account_id,character_id FROM owned_guild_applications_0078 WHERE guild_id=? ORDER BY id");q.bind_id(1,id);
    std::vector<Original::Application> result;
    while(q.row()){
        const auto entry=legacy_.pending(q.number<std::uint64_t>(1),q.number<std::uint64_t>(2));
        require(entry && entry->id==q.number<std::uint64_t>(0) && entry->target.id==id && entry->target.name_utf8==effective.guild.name_utf8 && entry->target.revision<=effective.guild.revision,"Incomplete pending audience");
        result.push_back(*entry);
    }
    require(effective.roster.size()+result.size()<=50,"Complete audience exceeds native ceiling");scope.finish();return result;
}
std::optional<SqliteOwnedGuildMembershipRepository::Guild> Succession53ReaderDraft::find_by_name(const std::string& name){
    ReadScope scope(db_);exact_schema53();std::array<std::string,2> wanted;
    require(!name.empty() && name.size()<=60 && name.find('%')==std::string::npos &&
        std::none_of(name.begin(),name.end(),[](unsigned char c){return c<32 || c==127;}),"Unsafe native lookup name");
    for(unsigned cn=0;cn<2;++cn){
        auto bytes=LegacyChineseCodec::encode(name,cn!=0);
        require(!bytes.empty() && bytes.size()<=15 && bytes.find('\0')==std::string::npos && LegacyChineseCodec::decode(bytes,cn!=0)==name,"Invalid dual-language lookup name");
        for(auto& c:bytes)if(static_cast<unsigned char>(c)>='A' && static_cast<unsigned char>(c)<='Z')c+=32;wanted[cn]=bytes;
    }
    sqlite_detail::Statement q(db_,"SELECT g.id,g.name_utf8 FROM owned_guilds g JOIN owned_guild_governance_0078 v ON v.guild_id=g.id ORDER BY g.id");
    std::optional<Original::Guild> result;
    while(q.row()){
        bool matched[2]{};
        for(unsigned cn=0;cn<2;++cn){auto bytes=LegacyChineseCodec::encode(q.text(1),cn!=0);
            for(auto& c:bytes)if(static_cast<unsigned char>(c)>='A' && static_cast<unsigned char>(c)<='Z')c+=32;matched[cn]=bytes==wanted[cn];}
        if(!matched[0] && !matched[1])continue;
        require(matched[0] && matched[1] && !result,"Ambiguous native guild lookup");result=effective_snapshot(q.number<std::uint64_t>(0)).guild;
    }
    scope.finish();return result;
}
std::uint8_t Succession53ReaderDraft::effective_display_role(const EffectiveLeader& state,const GuildRosterMember& member){
    const auto current=std::find(state.roster.begin(),state.roster.end(),member);require(current!=state.roster.end() && member.membership_revision,"Display must use complete current join");
    if(member.character_id==state.owner.character_id){
        require(member.account_id==state.owner.account_id && member.slot==state.owner.account_slot && member.membership_revision==state.owner.membership_revision,"Current owner join conflict");return 3;
    }
    std::uint64_t retired_office_cutoff=0;
    for(const auto& event:state.succession_history)if(event.from.character_id==member.character_id && event.from.membership_revision==member.membership_revision)retired_office_cutoff=event.revision;
    std::uint8_t role=1;
    for(const auto& row:state.officer_history){
        require(row.guild_id==state.guild.id && row.revision<=state.guild.revision,"Officer display audit outside guild lease");
        if(row.character_id!=member.character_id || row.membership_revision!=member.membership_revision)continue;
        require(row.account_id==member.account_id && row.account_slot==member.slot && (row.role==1 || row.role==2),"Officer join identity mismatch");
        if(row.revision>retired_office_cutoff)role=row.role;
    }
    return role;
}
Succession53ReaderDraft::Transferred Succession53ReaderDraft::transfer(
    const EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Identity& target,
    const StoredGuildMembership& membership,const Original::Proof& proof){
    require(transfer_enabled_,"New transfer mutation disabled; installed52 reads remain effective");
    require(bool(proof.before_write) && bool(proof.after_write),"Paired immutable world-only proof required");
    require(!target.membership_revision,"Target identity is not action authority");const auto id=expected.guild.id;positive(id);
    sqlite_detail::Transaction transaction(db_);exact_schema53();
    require(effective_leader(expected.owner.account_id,expected.owner.character_id)==expected && applications(id)==apps,"Effective leader/full typed publication stale");
    require(target.character_id!=expected.owner.character_id && legacy_.identity(target.account_id,target.character_id)==target,"Transfer target identity conflict");
    require(SqliteGuildRepository(db_).load(target.account_id,target.character_id)==std::optional{membership} &&
        membership.guild_id==id && membership.guild_revision==expected.guild.revision && membership.name_utf8==expected.guild.name_utf8,"Transfer target wrong guild/join");
    auto accepted=target;accepted.membership_revision=membership.membership_revision;
    const auto target_role=effective_display_role(expected,accepted);
    require(target_role==1 || target_role==2,"CUSTOM accepted nonfounder role1/2 target required");
    for(const auto& member:expected.roster){require(!legacy_.pending(member.account_id,member.character_id),"Accepted member also pending");nonbattle(db_,member.character_id);}
    for(const auto& app:apps){require(legacy_.identity(app.applicant.account_id,app.applicant.character_id)==app.applicant && !SqliteGuildRepository(db_).load(app.applicant.account_id,app.applicant.character_id),"Pending audience identity/current membership changed");nonbattle(db_,app.applicant.character_id);}
    sqlite_detail::Statement maximum_revision(db_,"SELECT COALESCE(MAX(revision),0) FROM owned_guilds");require(maximum_revision.row(),"Missing global generation");
    const auto previous=maximum_revision.number<std::uint64_t>(0);require(previous<maximum,"Global generation exhausted");const auto revision=previous+1;
    const Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)},
        {"owned_guild_successions_0083","NOT(guild_id="+std::to_string(id)+" AND revision="+std::to_string(revision)+")"}};
    const auto preserved=guard(db_,allowed);const auto stable=stable_guild_columns(db_,id);
    proof.before_write();unchanged(db_,preserved,allowed);
    require(stable_guild_columns(db_,id)==stable && effective_snapshot(id)==expected && applications(id)==apps,"Before-write proof changed captured authority");
    sqlite_detail::Statement bump(db_,"UPDATE owned_guilds SET revision=? WHERE id=? AND revision=? AND name_utf8=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=?");
    bump.bind_id(1,revision);bump.bind_id(2,id);bump.bind_id(3,expected.guild.revision);bump.bind(4,expected.guild.name_utf8);bump.bind(5,std::string(source));bump.done();require(sqlite3_changes(db_)==1,"Transfer generation CAS denied");
    SuccessionRecord event{id,revision,expected.owner.ownership_revision,expected.guild.revision,expected.owner,
        {id,target.account_id,target.character_id,membership.membership_revision,revision,target.slot},target_role};
    sqlite_detail::Statement insert(db_,"INSERT INTO owned_guild_successions_0083(guild_id,revision,previous_ownership_revision,guild_revision_before,from_account,from_character,from_slot,from_join_revision,to_account,to_character,to_slot,to_join_revision,target_previous_role,origin,design_id,source_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0083',?)");
    insert.bind_id(1,id);insert.bind_id(2,revision);insert.bind_id(3,event.previous_ownership_revision);insert.bind_id(4,event.guild_revision_before);
    insert.bind_id(5,event.from.account_id);insert.bind_id(6,event.from.character_id);insert.bind(7,event.from.account_slot);insert.bind_id(8,event.from.membership_revision);
    insert.bind_id(9,event.to.account_id);insert.bind_id(10,event.to.character_id);insert.bind(11,event.to.account_slot);insert.bind_id(12,event.to.membership_revision);insert.bind(13,target_role);insert.bind(14,std::string(source));insert.done();require(sqlite3_changes(db_)==1,"Transfer audit insertion failed");
    const auto after=effective_snapshot(id);auto wanted=expected;wanted.guild.revision=revision;wanted.owner=event.to;
    wanted.owner_identity=target;wanted.owner_membership={id,expected.guild.name_utf8,revision,membership.membership_revision};wanted.succession_history.push_back(event);
    wanted.persistent_guild_lease=after.persistent_guild_lease;
    const auto verify=[&]{require(effective_snapshot(id)==wanted && applications(id)==apps && stable_guild_columns(db_,id)==stable,"Transfer effective owner/readback conflict");
        unchanged(db_,preserved,allowed);};
    verify();proof.after_write();verify();transaction.commit();return {expected,wanted,event};
}
Succession53ReaderDraft::Transferred Succession53ReaderDraft::coordinated_transfer(
    const EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Identity& target,
    const StoredGuildMembership& membership,const Original::Proof& proof){
    require(sqlite3_get_autocommit(db_)==0,"Coordinated transfer requires enclosing transaction");
    require(bool(proof.before_write) && bool(proof.after_write),"Paired immutable world-only proof required");
    require(!target.membership_revision,"Target identity is not action authority");const auto id=expected.guild.id;positive(id);
    exact_schema53();
    require(effective_leader(expected.owner.account_id,expected.owner.character_id)==expected && applications(id)==apps,"Effective leader/full typed publication stale");
    require(target.character_id!=expected.owner.character_id && legacy_.identity(target.account_id,target.character_id)==target,"Transfer target identity conflict");
    require(SqliteGuildRepository(db_).load(target.account_id,target.character_id)==std::optional{membership} &&
        membership.guild_id==id && membership.guild_revision==expected.guild.revision && membership.name_utf8==expected.guild.name_utf8,"Transfer target wrong guild/join");
    auto accepted=target;accepted.membership_revision=membership.membership_revision;
    const auto target_role=effective_display_role(expected,accepted);
    require(target_role==1 || target_role==2,"CUSTOM accepted nonfounder role1/2 target required");
    for(const auto& member:expected.roster){require(!legacy_.pending(member.account_id,member.character_id),"Accepted member also pending");nonbattle(db_,member.character_id);}
    for(const auto& app:apps){require(legacy_.identity(app.applicant.account_id,app.applicant.character_id)==app.applicant && !SqliteGuildRepository(db_).load(app.applicant.account_id,app.applicant.character_id),"Pending audience identity/current membership changed");nonbattle(db_,app.applicant.character_id);}
    sqlite_detail::Statement maximum_revision(db_,"SELECT COALESCE(MAX(revision),0) FROM owned_guilds");require(maximum_revision.row(),"Missing global generation");
    const auto previous=maximum_revision.number<std::uint64_t>(0);require(previous<maximum,"Global generation exhausted");const auto revision=previous+1;
    const Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)},
        {"owned_guild_successions_0083","NOT(guild_id="+std::to_string(id)+" AND revision="+std::to_string(revision)+")"}};
    const auto preserved=guard(db_,allowed);const auto stable=stable_guild_columns(db_,id);
    proof.before_write();unchanged(db_,preserved,allowed);
    require(stable_guild_columns(db_,id)==stable && effective_snapshot(id)==expected && applications(id)==apps,"Before-write proof changed captured authority");
    sqlite_detail::Statement bump(db_,"UPDATE owned_guilds SET revision=? WHERE id=? AND revision=? AND name_utf8=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=?");
    bump.bind_id(1,revision);bump.bind_id(2,id);bump.bind_id(3,expected.guild.revision);bump.bind(4,expected.guild.name_utf8);bump.bind(5,std::string(source));bump.done();require(sqlite3_changes(db_)==1,"Transfer generation CAS denied");
    SuccessionRecord event{id,revision,expected.owner.ownership_revision,expected.guild.revision,expected.owner,
        {id,target.account_id,target.character_id,membership.membership_revision,revision,target.slot},target_role};
    sqlite_detail::Statement insert(db_,"INSERT INTO owned_guild_successions_0083(guild_id,revision,previous_ownership_revision,guild_revision_before,from_account,from_character,from_slot,from_join_revision,to_account,to_character,to_slot,to_join_revision,target_previous_role,origin,design_id,source_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0083',?)");
    insert.bind_id(1,id);insert.bind_id(2,revision);insert.bind_id(3,event.previous_ownership_revision);insert.bind_id(4,event.guild_revision_before);
    insert.bind_id(5,event.from.account_id);insert.bind_id(6,event.from.character_id);insert.bind(7,event.from.account_slot);insert.bind_id(8,event.from.membership_revision);
    insert.bind_id(9,event.to.account_id);insert.bind_id(10,event.to.character_id);insert.bind(11,event.to.account_slot);insert.bind_id(12,event.to.membership_revision);insert.bind(13,target_role);insert.bind(14,std::string(source));insert.done();require(sqlite3_changes(db_)==1,"Transfer audit insertion failed");
    const auto after=effective_snapshot(id);auto wanted=expected;wanted.guild.revision=revision;wanted.owner=event.to;
    wanted.owner_identity=target;wanted.owner_membership={id,expected.guild.name_utf8,revision,membership.membership_revision};wanted.succession_history.push_back(event);
    wanted.persistent_guild_lease=after.persistent_guild_lease;
    const auto verify=[&]{require(effective_snapshot(id)==wanted && applications(id)==apps && stable_guild_columns(db_,id)==stable,"Transfer effective owner/readback conflict");
        unchanged(db_,preserved,allowed);};
    verify();proof.after_write();verify();return {expected,wanted,event};
}
}
