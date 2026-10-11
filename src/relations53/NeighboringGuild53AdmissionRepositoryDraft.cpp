#include "NeighboringGuild53AdmissionRepositoryDraft.h"
#include "db/SqliteSupport.h"
#include "db/SqliteTradeRepository.h"
#include "text/LegacyChineseCodec.h"
#include "handlers/OwnedGuildMembershipName.h"
#include <algorithm>
#include <array>
#include <bit>
#include <cstring>
#include <limits>
#include <set>

namespace god2 {
namespace admission53_detail {
constexpr auto source="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
void require(bool value,const char* message){if(!value)throw DatabaseError(message);}
#include "preservation.inc"
std::vector<std::uint8_t> typed(sqlite3_stmt* statement,bool retain_revision=true) {
    std::vector<std::uint8_t> result;unsigned omitted=0;
    for(int c=0;c<sqlite3_column_count(statement);++c) {
        if(!retain_revision && std::string(sqlite3_column_name(statement,c))=="revision"){++omitted;continue;}
        const auto type=sqlite3_column_type(statement,c);result.push_back(static_cast<std::uint8_t>(type));
        if(type==SQLITE_INTEGER)append_number(result,std::bit_cast<std::uint64_t>(sqlite3_column_int64(statement,c)));
        else if(type==SQLITE_FLOAT)append_number(result,std::bit_cast<std::uint64_t>(sqlite3_column_double(statement,c)));
        else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
            const auto size=sqlite3_column_bytes(statement,c);
            const auto* bytes=type==SQLITE_TEXT?sqlite3_column_text(statement,c):static_cast<const unsigned char*>(sqlite3_column_blob(statement,c));
            require(size>=0 && (!size || bytes),"Malformed retained typed row");append_number(result,static_cast<std::uint64_t>(size));if(size)result.insert(result.end(),bytes,bytes+size);
        }
    }
    require(retain_revision || omitted==1,"Ambiguous guild revision field");return result;
}
std::vector<std::uint8_t> one(sqlite3* db,const std::string& sql,std::uint64_t id,bool retain_revision=true) {
    sqlite3_stmt* q=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&q,nullptr));
    struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};
    sqlite_detail::check(db,sqlite3_bind_int64(q,1,static_cast<sqlite3_int64>(id)));
    require(sqlite3_step(q)==SQLITE_ROW,"Missing retained typed row");const auto result=typed(q,retain_revision);
    require(sqlite3_step(q)==SQLITE_DONE,"Ambiguous retained typed row");return result;
}
void unique_names(const std::vector<GuildRosterMember>& members) {
    std::set<std::uint64_t> characters;std::set<std::pair<std::uint64_t,std::uint8_t>> slots;
    for(const auto& member:members)require(characters.insert(member.character_id).second && slots.emplace(member.account_id,member.slot).second,"Duplicate complete admission identity");
    for(const bool cn:{false,true}) {
        std::set<std::string> names;
        for(const auto& member:members){auto name=LegacyChineseCodec::encode(member.name_utf8,cn);
            require(!name.empty() && name.size()<=15 && name.find('%')==std::string::npos && name.find('\0')==std::string::npos && LegacyChineseCodec::decode(name,cn)==member.name_utf8,"Unsafe/unrepresentable admission name");
            for(auto& c:name)if(static_cast<unsigned char>(c)>='A' && static_cast<unsigned char>(c)<='Z')c+=32;
            require(names.insert(name).second,"Native folded complete audience name collision");}
    }
}
void erase(sqlite3* db,const NeighboringGuild53AdmissionRepositoryDraft::Original::Application& application) {
    sqlite_detail::Statement q(db,"DELETE FROM owned_guild_applications_0078 WHERE id=? AND guild_id=? AND character_id=? AND account_id=? AND observed_revision=? "
        "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0078' AND source_sha256=?");
    q.bind_id(1,application.id);q.bind_id(2,application.target.id);q.bind_id(3,application.applicant.character_id);
    q.bind_id(4,application.applicant.account_id);q.bind_id(5,application.target.revision);q.bind(6,std::string(source));q.done();require(sqlite3_changes(db)==1,"Effective52 application delete CAS denied");
}
std::uint64_t next_revision(sqlite3* db) {
    sqlite_detail::Statement q(db,"SELECT COALESCE(MAX(revision),0) FROM owned_guilds");require(q.row(),"Guild clock absent");const auto old=q.number<std::uint64_t>(0);
    require(old<static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Guild generation exhausted");return old+1;
}

// Same reserved-connection contract as the qualified CUSTOM84 lifecycle guard.
// Trusted callbacks MUST NOT reset the authorizer; no permanent owner authorizer
// may be overwritten. This is not a sandbox for arbitrary native C++ callbacks.
void immutable_world(sqlite3* db,const std::function<void()>& callback){
    require(sqlite3_get_autocommit(db)==0,"Neighboring53 WORLD requires active owned transaction");
    bool denied=false;const auto auth=[](void* state,int,const char*,const char*,const char*,const char*)->int{*static_cast<bool*>(state)=true;return SQLITE_DENY;};
    sqlite_detail::check(db,sqlite3_set_authorizer(db,auth,&denied));
    try{callback();}catch(...){sqlite3_set_authorizer(db,nullptr,nullptr);throw;}
    sqlite_detail::check(db,sqlite3_set_authorizer(db,nullptr,nullptr));
    require(!denied&&sqlite3_get_autocommit(db)==0,"Neighboring53 WORLD attempted SQL/transaction mutation");
}
void proof_valid(const NeighboringGuild53AdmissionRepositoryDraft::Original::Proof& proof){require(bool(proof.before_write) && bool(proof.after_write),"Paired immutable complete publication/world proof required");}
}
NeighboringGuild53AdmissionRepositoryDraft::NeighboringGuild53AdmissionRepositoryDraft(sqlite3* db,Original& original,Succession& effective,bool enabled,RelationsRepositoryDraft* relations):db_(db),original_(original),effective_(effective),enabled_(enabled),relations_(relations){admission53_detail::require(db_!=nullptr,"Null effective admission database");}
NeighboringGuild53AdmissionRepositoryDraft::Approved NeighboringGuild53AdmissionRepositoryDraft::approve(
    const Succession::EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Application& application,const Original::Proof& proof) {require_enabled();
    namespace ad=admission53_detail;ad::proof_valid(proof);sqlite_detail::Transaction transaction(db_);
    const auto id=expected.guild.id;const auto& owner=expected.owner_identity;const auto& applicant=application.applicant;
    ad::require(effective_.effective_leader(owner.account_id,owner.character_id)==expected && effective_.applications(id)==apps &&
        std::count(apps.begin(),apps.end(),application)==1,"Effective52 approval full founder/pending lease stale");
    ad::require(original_.nonmember(applicant.account_id,applicant.character_id)==applicant && original_.pending(applicant.account_id,applicant.character_id)==std::optional{application},"Approval exact applicant lease stale");
    ad::require(application.target.id==id && application.target.name_utf8==expected.guild.name_utf8 && application.target.revision<=expected.guild.revision,
        "Approval target guild identity mismatch");
    ad::require(expected.roster.size()<expected.original_creation.capacity,"Approval capacity exhausted");
    auto audience=expected.roster;for(const auto& app:apps)audience.push_back(app.applicant);ad::unique_names(audience);ad::require(audience.size()<=50,"Native admission projection overflow");
    const ad::Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)},
        {"owned_guild_members","character_id<>"+std::to_string(applicant.character_id)},
        {"owned_guild_applications_0078","id<>"+std::to_string(application.id)}};
    const auto preserved=ad::guard(db_,allowed);const auto retained=ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false);
    ad::immutable_world(db_,proof.before_write);ad::unchanged(db_,preserved,allowed);
    ad::require(ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false)==retained &&
        effective_.effective_leader(owner.account_id,owner.character_id)==expected && effective_.applications(id)==apps &&
        original_.nonmember(applicant.account_id,applicant.character_id)==applicant,"Approval before-write authority changed");
    const auto revision=ad::next_revision(db_);
    sqlite_detail::Statement bump(db_,"UPDATE owned_guilds SET revision=? WHERE id=? AND revision=? AND name_utf8=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=?");
    bump.bind_id(1,revision);bump.bind_id(2,id);bump.bind_id(3,expected.guild.revision);bump.bind(4,expected.guild.name_utf8);bump.bind(5,std::string(ad::source));bump.done();ad::require(sqlite3_changes(db_)==1,"Approval guild CAS denied");
    sqlite3_stmt* q=nullptr;sqlite_detail::check(db_,sqlite3_prepare_v2(db_,"INSERT INTO owned_guild_members(character_id,guild_id,revision,origin,design_id,source_sha256) VALUES(?,?,?,'CUSTOM_DESIGNED','CUSTOM-0075',?) RETURNING *",-1,&q,nullptr));
    struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};
    sqlite_detail::check(db_,sqlite3_bind_int64(q,1,static_cast<sqlite3_int64>(applicant.character_id)));sqlite_detail::check(db_,sqlite3_bind_int64(q,2,static_cast<sqlite3_int64>(id)));
    sqlite_detail::check(db_,sqlite3_bind_int64(q,3,static_cast<sqlite3_int64>(revision)));sqlite_detail::check(db_,sqlite3_bind_text(q,4,ad::source,-1,SQLITE_STATIC));
    ad::require(sqlite3_step(q)==SQLITE_ROW,"Approval member insertion absent");const auto inserted=ad::typed(q);
    ad::require(sqlite3_step(q)==SQLITE_DONE && sqlite3_changes(db_)==1,"Approval member insertion failed");
    ad::erase(db_,application);
    auto wanted=expected;wanted.guild.revision=revision;wanted.owner_membership.guild_revision=revision;
    auto member=applicant;member.membership_revision=revision;wanted.roster.push_back(member);
    std::sort(wanted.roster.begin(),wanted.roster.end(),[](const auto& a,const auto& b){return a.character_id<b.character_id;});
    auto wanted_apps=apps;std::erase(wanted_apps,application);
    const StoredGuildMembership joined{id,expected.guild.name_utf8,revision,revision};
    auto after=effective_.effective_snapshot(id);wanted.persistent_guild_lease=after.persistent_guild_lease;
    const auto verify=[&] {
        ad::require(effective_.effective_leader(owner.account_id,owner.character_id)==wanted && effective_.applications(id)==wanted_apps &&
            SqliteGuildRepository(db_).load(applicant.account_id,applicant.character_id)==std::optional{joined} &&
            original_.identity(applicant.account_id,applicant.character_id)==applicant && !original_.pending(applicant.account_id,applicant.character_id),"Approval complete effective52 readback conflict");
        ad::require(ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false)==retained && ad::one(db_,"SELECT * FROM owned_guild_members WHERE character_id=?",applicant.character_id)==inserted,"Approval changed opaque allowed-row fields");
        // The founder remains nonbattle via effective_leader, target via nonmember check beforewrite; ensure no reservation arose.
        sqlite_detail::Statement battle(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");battle.bind_id(1,applicant.character_id);ad::require(!battle.row(),"Approval applicant battle changed");ad::unchanged(db_,preserved,allowed);
    };
    verify();ad::immutable_world(db_,proof.after_write);verify();transaction.commit();return {expected,wanted,joined,wanted_apps};
}
NeighboringGuild53AdmissionRepositoryDraft::Rejected NeighboringGuild53AdmissionRepositoryDraft::reject(
    const Succession::EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Application& application,const Original::Proof& proof) {require_enabled();
    namespace ad=admission53_detail;ad::proof_valid(proof);sqlite_detail::Transaction transaction(db_);const auto id=expected.guild.id;const auto& owner=expected.owner_identity;
    ad::require(effective_.effective_leader(owner.account_id,owner.character_id)==expected && effective_.applications(id)==apps && std::count(apps.begin(),apps.end(),application)==1,"Effective52 rejection full publication stale");
    ad::require(application.target.id==id && application.target.name_utf8==expected.guild.name_utf8 && application.target.revision<=expected.guild.revision &&
        original_.pending(application.applicant.account_id,application.applicant.character_id)==std::optional{application},"Rejection exact pending lease stale");
    const ad::Exclusions allowed{{"owned_guild_applications_0078","id<>"+std::to_string(application.id)}};const auto preserved=ad::guard(db_,allowed);
    ad::immutable_world(db_,proof.before_write);ad::unchanged(db_,preserved,allowed);
    ad::require(effective_.effective_leader(owner.account_id,owner.character_id)==expected && effective_.applications(id)==apps,"Rejection before-write authority changed");
    ad::erase(db_,application);auto wanted_apps=apps;std::erase(wanted_apps,application);auto wanted=expected;
    wanted.persistent_guild_lease=effective_.effective_snapshot(id).persistent_guild_lease;
    const auto verify=[&] {ad::require(effective_.effective_leader(owner.account_id,owner.character_id)==wanted && effective_.applications(id)==wanted_apps &&
        !original_.pending(application.applicant.account_id,application.applicant.character_id),"Rejection effective52 readback conflict");ad::unchanged(db_,preserved,allowed);};
    verify();ad::immutable_world(db_,proof.after_write);verify();transaction.commit();return {expected,wanted,wanted_apps};
}
NeighboringGuild53AdmissionRepositoryDraft::Original::Application NeighboringGuild53AdmissionRepositoryDraft::apply(
    const Original::Identity& expected,const Succession::EffectiveLeader& target,const std::vector<Original::Application>& apps,const Original::Proof& proof) {require_enabled();
    namespace ad=admission53_detail;ad::proof_valid(proof);sqlite_detail::Transaction transaction(db_);const auto id=target.guild.id;
    ad::require(original_.nonmember(expected.account_id,expected.character_id)==expected && !original_.pending(expected.account_id,expected.character_id),"Effective52 apply current nonmember identity/pending conflict");
    ad::require(effective_.effective_snapshot(id)==target && effective_.applications(id)==apps,"Effective52 apply full target lease stale");
    ad::require(target.roster.size()<target.original_creation.capacity && target.roster.size()+apps.size()<50,"Effective52 apply complete projection capacity exhausted");
    auto audience=target.roster;for(const auto& app:apps)audience.push_back(app.applicant);audience.push_back(expected);ad::unique_names(audience);
    const ad::Exclusions allowed{{"owned_guild_applications_0078","character_id<>"+std::to_string(expected.character_id)}, {"sqlite_sequence","name<>'owned_guild_applications_0078'"}};
    const auto preserved=ad::guard(db_,allowed);
    sqlite_detail::Statement clock(db_,"SELECT max(COALESCE((SELECT seq FROM sqlite_sequence WHERE name='owned_guild_applications_0078'),0),COALESCE((SELECT MAX(id) FROM owned_guild_applications_0078),0))");
    ad::require(clock.row(),"Application clock absent");const auto previous=clock.number<std::uint64_t>(0);
    ad::require(previous<static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Application identity exhausted");
    ad::immutable_world(db_,proof.before_write);ad::unchanged(db_,preserved,allowed);
    ad::require(original_.nonmember(expected.account_id,expected.character_id)==expected && !original_.pending(expected.account_id,expected.character_id) &&
        effective_.effective_snapshot(id)==target && effective_.applications(id)==apps,"Effective52 apply beforewrite lease changed");
    sqlite3_stmt* q=nullptr;
    sqlite_detail::check(db_,sqlite3_prepare_v2(db_,"INSERT INTO owned_guild_applications_0078(guild_id,guild_name,observed_revision,character_id,account_id,slot,profile,name_bytes,name_codepage,name_utf8,role,role_revision,role_design,origin,design_id,source_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0078',?) RETURNING *",-1,&q,nullptr));
    struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};
    const auto bind_id=[&](int at,std::uint64_t value){sqlite_detail::check(db_,sqlite3_bind_int64(q,at,static_cast<sqlite3_int64>(value)));};
    const auto bind_text=[&](int at,const std::string& value){sqlite_detail::check(db_,sqlite3_bind_text(q,at,value.data(),static_cast<int>(value.size()),SQLITE_TRANSIENT));};
    const auto bind_bytes=[&](int at,std::span<const std::uint8_t> bytes){sqlite_detail::check(db_,sqlite3_bind_blob(q,at,bytes.data(),static_cast<int>(bytes.size()),SQLITE_TRANSIENT));};
    bind_id(1,id);bind_text(2,target.guild.name_utf8);bind_id(3,target.guild.revision);bind_id(4,expected.character_id);bind_id(5,expected.account_id);
    bind_id(6,expected.slot);bind_bytes(7,expected.profile);bind_bytes(8,expected.name_bytes);bind_id(9,expected.name_codepage);bind_text(10,expected.name_utf8);
    ad::require(expected.role.has_value(),"Application role absent");bind_bytes(11,expected.role->logical);bind_id(12,expected.role->revision);bind_text(13,expected.role->design_id);bind_text(14,ad::source);
    ad::require(sqlite3_step(q)==SQLITE_ROW,"Application INSERT returned no row");const auto inserted=ad::typed(q);
    ad::require(sqlite3_step(q)==SQLITE_DONE && sqlite3_changes(db_)==1,"Application insertion failed");
    const auto application_id=static_cast<std::uint64_t>(sqlite3_last_insert_rowid(db_));ad::require(application_id==previous+1,"Application identity clock conflict");
    const Original::Application result{application_id,target.guild,expected};auto wanted_apps=apps;wanted_apps.push_back(result);
    auto wanted=target;wanted.persistent_guild_lease=effective_.effective_snapshot(id).persistent_guild_lease;
    const auto verify=[&] {
        ad::require(original_.nonmember(expected.account_id,expected.character_id)==expected && original_.pending(expected.account_id,expected.character_id)==std::optional{result} &&
            effective_.effective_snapshot(id)==wanted && effective_.applications(id)==wanted_apps,"Effective52 application complete readback conflict");
        sqlite_detail::Statement seq(db_,"SELECT seq FROM sqlite_sequence WHERE name='owned_guild_applications_0078'");ad::require(seq.row() && seq.number<std::uint64_t>(0)==application_id,"Application sequence readback mismatch");
        ad::require(ad::one(db_,"SELECT * FROM owned_guild_applications_0078 WHERE id=?",application_id)==inserted,"Application insertion changed opaque defaults");ad::unchanged(db_,preserved,allowed);
    };
    verify();ad::immutable_world(db_,proof.after_write);verify();transaction.commit();return result;
}
void NeighboringGuild53AdmissionRepositoryDraft::cancel(const Original::Identity& expected,const Succession::EffectiveLeader& target,
    const std::vector<Original::Application>& apps,const Original::Application& application,const Original::Proof& proof) {require_enabled();
    namespace ad=admission53_detail;ad::proof_valid(proof);sqlite_detail::Transaction transaction(db_);const auto id=target.guild.id;
    ad::require(expected.account_id==application.applicant.account_id && expected.character_id==application.applicant.character_id &&
        original_.nonmember(expected.account_id,expected.character_id)==expected && original_.pending(expected.account_id,expected.character_id)==std::optional{application},"Effective52 cancellation current applicant identity/pending stale");
    ad::require(effective_.effective_snapshot(id)==target && effective_.applications(id)==apps && std::count(apps.begin(),apps.end(),application)==1,"Effective52 cancellation full target/pending stale");
    const ad::Exclusions allowed{{"owned_guild_applications_0078","id<>"+std::to_string(application.id)}};const auto preserved=ad::guard(db_,allowed);
    ad::immutable_world(db_,proof.before_write);ad::unchanged(db_,preserved,allowed);
    ad::require(original_.nonmember(expected.account_id,expected.character_id)==expected && effective_.effective_snapshot(id)==target && effective_.applications(id)==apps,
        "Cancellation beforewrite lease changed");
    ad::erase(db_,application);auto wanted_apps=apps;std::erase(wanted_apps,application);auto wanted=target;wanted.persistent_guild_lease=effective_.effective_snapshot(id).persistent_guild_lease;
    const auto verify=[&] {ad::require(original_.nonmember(expected.account_id,expected.character_id)==expected && !original_.pending(expected.account_id,expected.character_id) &&
        effective_.effective_snapshot(id)==wanted && effective_.applications(id)==wanted_apps,"Effective52 cancellation readback mismatch");ad::unchanged(db_,preserved,allowed);};
    verify();ad::immutable_world(db_,proof.after_write);verify();transaction.commit();
}
NeighboringGuild53AdmissionRepositoryDraft::Removed NeighboringGuild53AdmissionRepositoryDraft::leave(const Original::Identity& self,const StoredGuildMembership& join,
    const Succession::EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Proof& proof){require_enabled();return remove_member(false,self,join,expected,apps,proof);}
NeighboringGuild53AdmissionRepositoryDraft::Removed NeighboringGuild53AdmissionRepositoryDraft::kick(const Original::Identity& target,const StoredGuildMembership& join,
    const Succession::EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Proof& proof){require_enabled();return remove_member(true,target,join,expected,apps,proof);}
NeighboringGuild53AdmissionRepositoryDraft::Removed NeighboringGuild53AdmissionRepositoryDraft::remove_member(bool kick,const Original::Identity& target,const StoredGuildMembership& join,
    const Succession::EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Proof& proof) {
    namespace ad=admission53_detail;ad::proof_valid(proof);sqlite_detail::Transaction transaction(db_);const auto id=expected.guild.id;
    ad::require(!target.membership_revision && original_.identity(target.account_id,target.character_id)==target,"Effective52 removal identity stale");
    ad::require(effective_.effective_snapshot(id)==expected && effective_.applications(id)==apps && join.guild_id==id && join.guild_revision==expected.guild.revision &&
        join.name_utf8==expected.guild.name_utf8 && SqliteGuildRepository(db_).load(target.account_id,target.character_id)==std::optional{join},"Effective52 removal full join/owner/audience stale");
    if(kick)ad::require(effective_.effective_leader(expected.owner.account_id,expected.owner.character_id)==expected,"Effective52 kick founder not ready");
    ad::require(target.character_id!=expected.owner.character_id,"Current effective founder cannot leave/be kicked");
    auto member=target;member.membership_revision=join.membership_revision;
    ad::require(std::find(expected.roster.begin(),expected.roster.end(),member)!=expected.roster.end(),"Removal exact member absent");
    const auto role=Succession::effective_display_role(expected,member);ad::require(kick?role==1:(role==1 || role==2),"CUSTOM ordinary kick or nonfounder role1/2 leave policy denied");
    const auto nonbattle=[&]{sqlite_detail::Statement q(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");q.bind_id(1,target.character_id);ad::require(!q.row(),"Removal actor/target pending battle");};nonbattle();
    auto audience=expected.roster;for(const auto& app:apps)audience.push_back(app.applicant);ad::unique_names(audience);ad::require(audience.size()<=50,"Removal complete native projection overflow");
    for(const auto& accepted:expected.roster)ad::require(!original_.pending(accepted.account_id,accepted.character_id),"Removal accepted member also pending");
    for(const auto& app:apps)ad::require(!SqliteGuildRepository(db_).load(app.applicant.account_id,app.applicant.character_id),"Removal pending also accepted");
    const ad::Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)}, {"owned_guild_members","character_id<>"+std::to_string(target.character_id)}};
    const auto preserved=ad::guard(db_,allowed);const auto retained=ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false);
    ad::immutable_world(db_,proof.before_write);ad::unchanged(db_,preserved,allowed);
    ad::require(ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false)==retained && effective_.effective_snapshot(id)==expected && effective_.applications(id)==apps &&
        original_.identity(target.account_id,target.character_id)==target,"Removal beforewrite complete lease changed");nonbattle();
    if(kick)ad::require(effective_.effective_leader(expected.owner.account_id,expected.owner.character_id)==expected,"Kick actor battle changed");
    const auto revision=ad::next_revision(db_);sqlite_detail::Statement bump(db_,"UPDATE owned_guilds SET revision=? WHERE id=? AND revision=? AND name_utf8=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=?");
    bump.bind_id(1,revision);bump.bind_id(2,id);bump.bind_id(3,expected.guild.revision);bump.bind(4,expected.guild.name_utf8);bump.bind(5,std::string(ad::source));bump.done();ad::require(sqlite3_changes(db_)==1,"Removal guild generation CAS denied");
    sqlite_detail::Statement erase(db_,"DELETE FROM owned_guild_members WHERE guild_id=? AND character_id=? AND revision=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=? AND EXISTS(SELECT 1 FROM recovered_characters c WHERE c.id=owned_guild_members.character_id AND c.account_id=?)");
    erase.bind_id(1,id);erase.bind_id(2,target.character_id);erase.bind_id(3,join.membership_revision);erase.bind(4,std::string(ad::source));erase.bind_id(5,target.account_id);erase.done();ad::require(sqlite3_changes(db_)==1,"Removal member delete CAS denied");
    auto wanted=expected;wanted.guild.revision=revision;wanted.owner_membership.guild_revision=revision;std::erase(wanted.roster,member);
    wanted.persistent_guild_lease=effective_.effective_snapshot(id).persistent_guild_lease;
    const auto verify=[&] {
        ad::require(effective_.effective_snapshot(id)==wanted && effective_.applications(id)==apps && original_.nonmember(target.account_id,target.character_id)==target &&
            !original_.pending(target.account_id,target.character_id),"Removal complete effective52 readback conflict");
        if(kick)ad::require(effective_.effective_leader(expected.owner.account_id,expected.owner.character_id)==wanted,"Kick owner afterwrite state conflict");
        ad::require(ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false)==retained,"Removal changed opaque guild fields");ad::unchanged(db_,preserved,allowed);
    };
    verify();ad::immutable_world(db_,proof.after_write);verify();transaction.commit();return {expected,wanted,target,join,kick};
}
namespace admission53_detail {
std::optional<std::vector<std::uint8_t>> office_fields(sqlite3* db,const std::string& sql,const std::set<std::string>& omitted={"role","revision"}) {
    sqlite3_stmt* q=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&q,nullptr));
    struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};
    const auto status=sqlite3_step(q);if(status==SQLITE_DONE)return {};
    require(status==SQLITE_ROW,"Officer retained query failed");std::vector<std::uint8_t> result;
    for(int c=0;c<sqlite3_column_count(q);++c){const std::string name=sqlite3_column_name(q,c);if(omitted.contains(name))continue;
        const auto type=sqlite3_column_type(q,c);result.push_back(static_cast<std::uint8_t>(type));
        if(type==SQLITE_INTEGER)append_number(result,std::bit_cast<std::uint64_t>(sqlite3_column_int64(q,c)));
        else if(type==SQLITE_FLOAT)append_number(result,std::bit_cast<std::uint64_t>(sqlite3_column_double(q,c)));
        else if(type==SQLITE_TEXT || type==SQLITE_BLOB){const auto size=sqlite3_column_bytes(q,c);const auto* bytes=static_cast<const std::uint8_t*>(sqlite3_column_blob(q,c));require(size>=0 && (!size || bytes),"Officer retained value invalid");append_number(result,static_cast<std::uint64_t>(size));if(size)result.insert(result.end(),bytes,bytes+size);}
    }
    require(sqlite3_step(q)==SQLITE_DONE,"Officer rank key ambiguous");return result;
}
void nonbattle(sqlite3* db,std::uint64_t character){sqlite_detail::Statement q(db,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");q.bind_id(1,character);require(!q.row(),"Effective52 governance actor/audience pending battle");}
void bump(sqlite3* db,const NeighboringGuild53AdmissionRepositoryDraft::Succession::EffectiveLeader& expected,std::uint64_t revision){
    sqlite_detail::Statement q(db,"UPDATE owned_guilds SET revision=? WHERE id=? AND revision=? AND name_utf8=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=?");
    q.bind_id(1,revision);q.bind_id(2,expected.guild.id);q.bind_id(3,expected.guild.revision);q.bind(4,expected.guild.name_utf8);q.bind(5,std::string(source));q.done();require(sqlite3_changes(db)==1,"Effective52 governance guild CAS denied");
}
}


NeighboringGuild53AdmissionRepositoryDraft::OfficeChanged NeighboringGuild53AdmissionRepositoryDraft::change_officer(
    const Succession::EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Identity& target,const StoredGuildMembership& join,
    Original::OfficerAction action,const Original::Proof& proof){require_enabled();
    namespace ad=admission53_detail;ad::proof_valid(proof);sqlite_detail::Transaction transaction(db_);const auto id=expected.guild.id;
    ad::require(action==Original::OfficerAction::Appoint || action==Original::OfficerAction::RemoveOffice,"Unknown effective52 office action");
    ad::require(effective_.effective_leader(expected.owner.account_id,expected.owner.character_id)==expected && effective_.applications(id)==apps,"Office complete effectivefounder/pending lease stale");
    ad::require(!target.membership_revision && original_.identity(target.account_id,target.character_id)==target && target.character_id!=expected.owner.character_id &&
        !original_.pending(target.account_id,target.character_id) && join.guild_id==id && join.guild_revision==expected.guild.revision && join.name_utf8==expected.guild.name_utf8 &&
        SqliteGuildRepository(db_).load(target.account_id,target.character_id)==std::optional{join},"Office exact nonfounder target join stale");
    auto member=target;member.membership_revision=join.membership_revision;ad::require(std::find(expected.roster.begin(),expected.roster.end(),member)!=expected.roster.end(),"Office target absent from full roster");
    const auto previous=Succession::effective_display_role(expected,member);const auto to=static_cast<std::uint8_t>(action==Original::OfficerAction::Appoint?2:1);
    ad::require(previous==(to==2?1:2),"Office effective role transition denied");ad::nonbattle(db_,target.character_id);
    auto audience=expected.roster;for(const auto& app:apps){ad::require(!SqliteGuildRepository(db_).load(app.applicant.account_id,app.applicant.character_id),"Office pending also accepted");audience.push_back(app.applicant);}
    for(const auto& row:expected.roster)ad::require(!original_.pending(row.account_id,row.character_id),"Office accepted also pending");ad::unique_names(audience);ad::require(audience.size()<=50,"Office projection overflow");
    const auto key="guild_id="+std::to_string(id)+" AND character_id="+std::to_string(target.character_id)+" AND membership_revision="+std::to_string(join.membership_revision);
    const auto rank_sql="SELECT * FROM owned_guild_officers_0082 WHERE "+key;
    const ad::Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)},{"owned_guild_officers_0082","NOT("+key+")"}},none;
    const auto preserved=ad::guard(db_,allowed),g0=ad::guard(db_,none);const auto guild_fields=ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false);const auto rank_fields=ad::office_fields(db_,rank_sql);
    ad::immutable_world(db_,proof.before_write);ad::unchanged(db_,g0,none);ad::require(effective_.effective_leader(expected.owner.account_id,expected.owner.character_id)==expected && effective_.applications(id)==apps,"Office beforewrite founder lease changed");ad::nonbattle(db_,target.character_id);
    const auto revision=ad::next_revision(db_);ad::bump(db_,expected,revision);auto wanted=expected;wanted.guild.revision=revision;wanted.owner_membership.guild_revision=revision;
    auto at=std::find_if(wanted.officer_history.begin(),wanted.officer_history.end(),[&](const auto& row){return row.character_id==target.character_id && row.membership_revision==join.membership_revision;});
    std::optional<std::vector<std::uint8_t>> inserted;
    if(at==wanted.officer_history.end()){
        ad::require(to==2 && !rank_fields,"Office missing demotion audit");sqlite3_stmt* q=nullptr;
        sqlite_detail::check(db_,sqlite3_prepare_v2(db_,"INSERT INTO owned_guild_officers_0082(guild_id,account_id,character_id,account_slot,membership_revision,revision,role,origin,design_id,source_sha256) VALUES(?,?,?,?,?,?,2,'CUSTOM_DESIGNED','CUSTOM-0082',?) RETURNING *",-1,&q,nullptr));
        struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};const std::array<std::uint64_t,6> values{id,target.account_id,target.character_id,target.slot,join.membership_revision,revision};
        for(int i=0;i<6;++i)sqlite_detail::check(db_,sqlite3_bind_int64(q,i+1,static_cast<sqlite3_int64>(values[static_cast<std::size_t>(i)])));sqlite_detail::check(db_,sqlite3_bind_text(q,7,ad::source,-1,SQLITE_STATIC));
        ad::require(sqlite3_step(q)==SQLITE_ROW,"Office audit insertion missing");inserted=ad::typed(q);ad::require(sqlite3_step(q)==SQLITE_DONE && sqlite3_changes(db_)==1,"Office insertion failed");
        wanted.officer_history.push_back({id,target.account_id,target.character_id,join.membership_revision,revision,target.slot,2});
    }else{
        // Retired founder cutoff may hide a retained role2 row. CAS saved role, not effective role.
        sqlite_detail::Statement q(db_,"UPDATE owned_guild_officers_0082 SET role=?,revision=? WHERE guild_id=? AND account_id=? AND character_id=? AND account_slot=? AND membership_revision=? AND revision=? AND role=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0082' AND source_sha256=?");
        q.bind(1,to);q.bind_id(2,revision);q.bind_id(3,id);q.bind_id(4,target.account_id);q.bind_id(5,target.character_id);q.bind(6,target.slot);q.bind_id(7,join.membership_revision);q.bind_id(8,at->revision);q.bind(9,at->role);q.bind(10,std::string(ad::source));q.done();ad::require(sqlite3_changes(db_)==1,"Office saved audit CAS failed");at->role=to;at->revision=revision;
    }
    std::sort(wanted.officer_history.begin(),wanted.officer_history.end(),[](const auto& a,const auto& b){return std::pair(a.character_id,a.membership_revision)<std::pair(b.character_id,b.membership_revision);});
    wanted.persistent_guild_lease=effective_.effective_snapshot(id).persistent_guild_lease;
    const auto verify=[&]{ad::require(effective_.effective_leader(expected.owner.account_id,expected.owner.character_id)==wanted && effective_.applications(id)==apps && original_.identity(target.account_id,target.character_id)==target &&
        SqliteGuildRepository(db_).load(target.account_id,target.character_id)==std::optional{StoredGuildMembership{id,join.name_utf8,revision,join.membership_revision}} && Succession::effective_display_role(wanted,member)==to,"Office complete readback mismatch");
        ad::require(ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false)==guild_fields,"Office retained guild changed");
        if(rank_fields)ad::require(ad::office_fields(db_,rank_sql)==rank_fields,"Office retained rank fields changed");
        if(inserted)ad::require(ad::one(db_,"SELECT * FROM owned_guild_officers_0082 WHERE guild_id=? AND character_id="+std::to_string(target.character_id)+" AND membership_revision="+std::to_string(join.membership_revision),id)==*inserted,"Office inserted opaque defaults changed");
        ad::nonbattle(db_,target.character_id);ad::unchanged(db_,preserved,allowed);};
    verify();const auto g1=ad::guard(db_,none);ad::immutable_world(db_,proof.after_write);ad::unchanged(db_,g1,none);verify();transaction.commit();return {expected,wanted,target,join,action};
}

NeighboringGuild53AdmissionRepositoryDraft::CreationSnapshot NeighboringGuild53AdmissionRepositoryDraft::creation_snapshot(){require_enabled();
    namespace ad=admission53_detail;CreationSnapshot out;sqlite3_stmt* q=nullptr;sqlite_detail::check(db_,sqlite3_prepare_v2(db_,"SELECT * FROM owned_guilds ORDER BY id",-1,&q,nullptr));
    struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};int step;while((step=sqlite3_step(q))==SQLITE_ROW)out.guild_rows.push_back(ad::typed(q));ad::require(step==SQLITE_DONE,"Creation catalog read failed");
    sqlite_detail::Statement clock(db_,"SELECT COALESCE(MAX(id),0),COALESCE(MAX(revision),0) FROM owned_guilds");ad::require(clock.row(),"Creation catalog clock absent");const auto id=clock.number<std::uint64_t>(0),revision=clock.number<std::uint64_t>(1);
    const auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());ad::require(id<maximum && revision<maximum,"Creation identity or revision exhausted");out.next_id=id+1;out.next_revision=revision+1;return out;
}
NeighboringGuild53AdmissionRepositoryDraft::Created53 NeighboringGuild53AdmissionRepositoryDraft::create53(
    const Original::Identity& actor,const Original::Wallet& wallet,const std::string& name,const Original::Policy& policy,
    const CreationSnapshot& catalog,const Original::Proof& proof,const RelationsRepositoryDraft::Authority& authority){
    require_enabled();namespace ad=admission53_detail;
    ad::require(relations_&&authority.account==actor.account_id&&authority.character==actor.character_id&&authority.slot==actor.slot,
        "Creation53 coordinated relation allocator/actor required");
    ad::require(creation_snapshot()==catalog,"Creation53 original catalog lease changed");
    const auto lease=relations_->capture_create(authority,true,name,policy);
    ad::require(lease.identity==actor&&lease.wallet==wallet&&lease.next_guild_id==catalog.next_id&&
        lease.next_guild_revision==catalog.next_revision&&lease.guild_rows==catalog.guild_rows,"Creation53 original input lease changed");
    const auto created=relations_->create53(lease,proof);return {created.leader,created.wallet};
}
}
