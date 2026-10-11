#include "LifecycleCore53.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include "handlers/OwnedGuildMembershipName.h"
#include <algorithm>
#include <array>
#include <bit>
#include <cstring>
#include <limits>
#include <set>

namespace god2 {
namespace lifecycle53_detail {
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
void erase(sqlite3* db,const LifecycleCore53::Original::Application& application) {
    sqlite_detail::Statement q(db,"DELETE FROM owned_guild_applications_0078 WHERE id=? AND guild_id=? AND character_id=? AND account_id=? AND observed_revision=? "
        "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0078' AND source_sha256=?");
    q.bind_id(1,application.id);q.bind_id(2,application.target.id);q.bind_id(3,application.applicant.character_id);
    q.bind_id(4,application.applicant.account_id);q.bind_id(5,application.target.revision);q.bind(6,std::string(source));q.done();require(sqlite3_changes(db)==1,"Effective52 application delete CAS denied");
}
std::uint64_t next_revision(sqlite3* db) {
    sqlite_detail::Statement q(db,"SELECT COALESCE(MAX(revision),0) FROM owned_guilds");require(q.row(),"Guild clock absent");const auto old=q.number<std::uint64_t>(0);
    require(old<static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Guild generation exhausted");return old+1;
}
void proof_valid(const LifecycleCore53::Original::Proof& proof){require(bool(proof.before_write) && bool(proof.after_write),"Paired immutable complete publication/world proof required");}
}
LifecycleCore53::LifecycleCore53(sqlite3* db,Original& original,Succession& effective):db_(db),original_(original),effective_(effective){lifecycle53_detail::require(db_!=nullptr,"Null effective admission database");}
namespace lifecycle53_detail {
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
void bump(sqlite3* db,const LifecycleCore53::Succession::EffectiveLeader& expected,std::uint64_t revision){
    sqlite_detail::Statement q(db,"UPDATE owned_guilds SET revision=? WHERE id=? AND revision=? AND name_utf8=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=?");
    q.bind_id(1,revision);q.bind_id(2,expected.guild.id);q.bind_id(3,expected.guild.revision);q.bind(4,expected.guild.name_utf8);q.bind(5,std::string(source));q.done();require(sqlite3_changes(db)==1,"Effective52 governance guild CAS denied");
}
}
LifecycleCore53::CreationSnapshot LifecycleCore53::creation_snapshot(){
    namespace ad=lifecycle53_detail;CreationSnapshot out;sqlite3_stmt* q=nullptr;sqlite_detail::check(db_,sqlite3_prepare_v2(db_,"SELECT * FROM owned_guilds ORDER BY id",-1,&q,nullptr));
    struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};int step;while((step=sqlite3_step(q))==SQLITE_ROW)out.guild_rows.push_back(ad::typed(q));ad::require(step==SQLITE_DONE,"Creation catalog read failed");
    sqlite_detail::Statement clock(db_,"SELECT COALESCE(MAX(id),0),COALESCE(MAX(revision),0) FROM owned_guilds");ad::require(clock.row(),"Creation catalog clock absent");const auto id=clock.number<std::uint64_t>(0),revision=clock.number<std::uint64_t>(1);
    const auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());ad::require(id<maximum && revision<maximum,"Creation identity or revision exhausted");out.next_id=id+1;out.next_revision=revision+1;return out;
}
LifecycleCore53::Created52 LifecycleCore53::create52(
    const Original::Identity& actor,const Original::Wallet& wallet,const std::string& name,const Original::Policy& policy,const CreationSnapshot& catalog,const Original::Proof& proof){
    namespace ad=lifecycle53_detail;ad::proof_valid(proof);ad::require(sqlite3_get_autocommit(db_)==0,"Lifecycle core requires enclosing transaction");
    ad::require(!actor.membership_revision && original_.nonmember(actor.account_id,actor.character_id)==actor && !original_.pending(actor.account_id,actor.character_id),"Creation current nonmember identity stale");
    ad::require(policy.creation_fee && policy.minimum_level && policy.initial_capacity && policy.initial_capacity<=50 && actor.role,"Creation policy absent");const auto role=RecoveredRoleLevel::parse(actor.role->logical);
    const auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());ad::require(role && role->level()>=policy.minimum_level && wallet.revision && wallet.revision<maximum && wallet.amount>=policy.creation_fee,"Creation policy level/wallet denied");
    SqliteTradeRepository money(db_);ad::require(money.load_wallet(actor.account_id,actor.character_id)==std::optional{wallet} && creation_snapshot()==catalog,"Creation wallet/catalog original lease stale");
    const auto encode_name=[](const std::string& text,bool cn){const auto encoded=LegacyChineseCodec::encode(text,cn);ad::require(!encoded.empty() && encoded.size()<=15 && LegacyChineseCodec::decode(encoded,cn)==text,"Creation name not lossless bilingual");RecoveredGuildMembership::Name field{};std::copy(encoded.begin(),encoded.end(),field.begin());ad::require(OwnedGuildMembershipName::valid(field,static_cast<std::uint16_t>(cn?936:950)),"Creation native name unsafe");auto folded=encoded;for(auto& c:folded)if(static_cast<unsigned char>(c)>='A' && static_cast<unsigned char>(c)<='Z')c+=32;return folded;};
    const std::array<std::string,2> names{encode_name(name,false),encode_name(name,true)};sqlite_detail::Statement existing(db_,"SELECT name_utf8 FROM owned_guilds");while(existing.row())for(unsigned cn=0;cn<2;++cn)ad::require(encode_name(existing.text(0),cn!=0)!=names[cn],"Creation reserved native folded name collision");
    const auto id=catalog.next_id,revision=catalog.next_revision;
    const ad::Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)},{"owned_guild_members","character_id<>"+std::to_string(actor.character_id)},
        {"owned_guild_governance_0078","guild_id<>"+std::to_string(id)},{"character_trade_wallets","character_id<>"+std::to_string(actor.character_id)}},none;
    const auto preserved=ad::guard(db_,allowed),g0=ad::guard(db_,none);const auto wallet_sql="SELECT * FROM character_trade_wallets WHERE character_id="+std::to_string(actor.character_id);const auto wallet_fields=ad::office_fields(db_,wallet_sql,{"amount","revision"});
    proof.before_write();ad::unchanged(db_,g0,none);ad::require(creation_snapshot()==catalog && original_.nonmember(actor.account_id,actor.character_id)==actor && !original_.pending(actor.account_id,actor.character_id) && money.load_wallet(actor.account_id,actor.character_id)==std::optional{wallet},"Creation beforewrite lease changed");
    const auto write=[&](const char* sql,const std::function<void(sqlite3_stmt*)>& bind){sqlite3_stmt* q=nullptr;sqlite_detail::check(db_,sqlite3_prepare_v2(db_,sql,-1,&q,nullptr));struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};bind(q);ad::require(sqlite3_step(q)==SQLITE_ROW,"Creation RETURNING row missing");const auto inserted=ad::typed(q);ad::require(sqlite3_step(q)==SQLITE_DONE && sqlite3_changes(db_)==1,"Creation exact write failed");return inserted;};
    const auto bind_id=[&](sqlite3_stmt* q,int slot,std::uint64_t value){sqlite_detail::check(db_,sqlite3_bind_int64(q,slot,static_cast<sqlite3_int64>(value)));};
    const auto source_bind=[&](sqlite3_stmt* q,int slot){sqlite_detail::check(db_,sqlite3_bind_text(q,slot,ad::source,-1,SQLITE_STATIC));};
    const auto guild_row=write("INSERT INTO owned_guilds(id,name_utf8,revision,origin,design_id,source_sha256) VALUES(?,?,?,'CUSTOM_DESIGNED','CUSTOM-0075',?) RETURNING *",[&](auto q){bind_id(q,1,id);sqlite_detail::check(db_,sqlite3_bind_text(q,2,name.data(),static_cast<int>(name.size()),SQLITE_TRANSIENT));bind_id(q,3,revision);source_bind(q,4);});
    const auto member_row=write("INSERT INTO owned_guild_members(character_id,guild_id,revision,origin,design_id,source_sha256) VALUES(?,?,?,'CUSTOM_DESIGNED','CUSTOM-0075',?) RETURNING *",[&](auto q){bind_id(q,1,actor.character_id);bind_id(q,2,id);bind_id(q,3,revision);source_bind(q,4);});
    const auto gov_row=write("INSERT INTO owned_guild_governance_0078(guild_id,owner_account,owner_character,created_revision,created_cost,capacity,origin,design_id,source_sha256) VALUES(?,?,?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0078',?) RETURNING *",[&](auto q){bind_id(q,1,id);bind_id(q,2,actor.account_id);bind_id(q,3,actor.character_id);bind_id(q,4,revision);bind_id(q,5,policy.creation_fee);bind_id(q,6,policy.initial_capacity);source_bind(q,7);});
    const Original::Wallet remaining{wallet.amount-policy.creation_fee,wallet.revision+1};
    const auto wallet_row=write("UPDATE character_trade_wallets SET amount=?,revision=? WHERE character_id=? AND amount=? AND revision=? AND design_id='CUSTOM-0063' RETURNING *",[&](auto q){bind_id(q,1,remaining.amount);bind_id(q,2,remaining.revision);bind_id(q,3,actor.character_id);bind_id(q,4,wallet.amount);bind_id(q,5,wallet.revision);});
    auto member=actor;member.membership_revision=revision;const Original::Governance creation{id,actor.account_id,actor.character_id,revision,policy.creation_fee,policy.initial_capacity};
    const auto expected_leader=effective_.effective_snapshot(id);
    const auto verify=[&]{const auto leader=effective_.effective_snapshot(id);ad::require(leader==expected_leader && leader.guild==Original::Guild{id,revision,name} && leader.owner_identity==actor && leader.original_creation==creation && leader.succession_history.empty() && leader.officer_history.empty() && leader.roster==std::vector<GuildRosterMember>{member} && leader.owner_membership==StoredGuildMembership{id,name,revision,revision} && leader.owner.ownership_revision==0 && leader.owner.character_id==actor.character_id &&
            original_.identity(actor.account_id,actor.character_id)==actor && !original_.pending(actor.account_id,actor.character_id) && effective_.applications(id).empty() && money.load_wallet(actor.account_id,actor.character_id)==std::optional{remaining},"Creation effective52 full readback mismatch");
        ad::require(ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id)==guild_row && ad::one(db_,"SELECT * FROM owned_guild_members WHERE character_id=?",actor.character_id)==member_row && ad::one(db_,"SELECT * FROM owned_guild_governance_0078 WHERE guild_id=?",id)==gov_row && ad::one(db_,"SELECT * FROM character_trade_wallets WHERE character_id=?",actor.character_id)==wallet_row && ad::office_fields(db_,wallet_sql,{"amount","revision"})==wallet_fields,"Creation typed inserted defaults/retained wallet corrupted");ad::nonbattle(db_,actor.character_id);ad::unchanged(db_,preserved,allowed);};
    verify();const auto g1=ad::guard(db_,none);proof.after_write();ad::unchanged(db_,g1,none);verify();return {expected_leader,remaining};
}
LifecycleCore53::Disbanded LifecycleCore53::disband(
    const Succession::EffectiveLeader& expected,const std::vector<Original::Application>& apps,const Original::Proof& proof){
    namespace ad=lifecycle53_detail;ad::proof_valid(proof);ad::require(sqlite3_get_autocommit(db_)==0,"Lifecycle core requires enclosing transaction");const auto id=expected.guild.id;
    ad::require(effective_.effective_leader(expected.owner.account_id,expected.owner.character_id)==expected && effective_.applications(id)==apps,"Disband current effectivefounder/full pending stale");
    auto audience=expected.roster;for(const auto& app:apps)audience.push_back(app.applicant);ad::unique_names(audience);ad::require(!expected.roster.empty() && audience.size()<=50,"Disband full audience invalid");
    for(const auto& row:expected.roster){ad::require(!original_.pending(row.account_id,row.character_id),"Disband accepted also pending");ad::nonbattle(db_,row.character_id);}
    for(const auto& app:apps){ad::require(!SqliteGuildRepository(db_).load(app.applicant.account_id,app.applicant.character_id) && original_.identity(app.applicant.account_id,app.applicant.character_id).slot==app.applicant.slot,"Disband pending ownership stale");ad::nonbattle(db_,app.applicant.character_id);}
    const ad::Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)},{"owned_guild_members","guild_id<>"+std::to_string(id)},
        {"owned_guild_governance_0078","guild_id<>"+std::to_string(id)},{"owned_guild_applications_0078","guild_id<>"+std::to_string(id)}},none;
    const auto preserved=ad::guard(db_,allowed),g0=ad::guard(db_,none);const auto fields=ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false);
    proof.before_write();ad::unchanged(db_,g0,none);ad::require(effective_.effective_leader(expected.owner.account_id,expected.owner.character_id)==expected && effective_.applications(id)==apps,"Disband beforewrite effectiveowner changed");
    const auto revision=ad::next_revision(db_);ad::bump(db_,expected,revision);for(const auto& app:apps)ad::erase(db_,app);
    for(const auto& row:expected.roster){sqlite_detail::Statement q(db_,"DELETE FROM owned_guild_members WHERE guild_id=? AND character_id=? AND revision=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=? AND EXISTS(SELECT 1 FROM recovered_characters c WHERE c.id=owned_guild_members.character_id AND c.account_id=? AND c.slot=?)");
        q.bind_id(1,id);q.bind_id(2,row.character_id);q.bind_id(3,row.membership_revision);q.bind(4,std::string(ad::source));q.bind_id(5,row.account_id);q.bind(6,row.slot);q.done();ad::require(sqlite3_changes(db_)==1,"Disband exact accepted deletion failed");}
    const auto& creation=expected.original_creation;sqlite_detail::Statement retire(db_,"DELETE FROM owned_guild_governance_0078 WHERE guild_id=? AND owner_account=? AND owner_character=? AND created_revision=? AND created_cost=? AND capacity=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0078' AND source_sha256=?");
    retire.bind_id(1,id);retire.bind_id(2,creation.owner_account);retire.bind_id(3,creation.owner_character);retire.bind_id(4,creation.created_revision);retire.bind(5,creation.created_cost);retire.bind(6,creation.capacity);retire.bind(7,std::string(ad::source));retire.done();ad::require(sqlite3_changes(db_)==1,"Disband original active creation retirement CAS denied");
    const Original::Guild retired{id,revision,expected.guild.name_utf8};
    const auto verify=[&]{ad::require(original_.guild(id)==retired && ad::one(db_,"SELECT * FROM owned_guilds WHERE id=?",id,false)==fields && !original_.player_created(id) && !original_.find_by_name(retired.name_utf8),"Disband reserved guild/retirement readback invalid");
        for(const auto* table:{"owned_guild_members","owned_guild_governance_0078","owned_guild_applications_0078"}){sqlite_detail::Statement q(db_,("SELECT COUNT(*) FROM "+ad::quoted(table)+" WHERE guild_id=?").c_str());q.bind_id(1,id);ad::require(q.row() && q.number<std::uint64_t>(0)==0,"Disband target active rows remain");}
        for(const auto& row:expected.roster){auto identity=row;identity.membership_revision=0;ad::require(original_.nonmember(row.account_id,row.character_id)==identity && !original_.pending(row.account_id,row.character_id),"Disband accepted identity/battle changed");}
        for(const auto& app:apps){ad::require(!original_.pending(app.applicant.account_id,app.applicant.character_id) && !SqliteGuildRepository(db_).load(app.applicant.account_id,app.applicant.character_id) && original_.identity(app.applicant.account_id,app.applicant.character_id).slot==app.applicant.slot,"Disband pending readback invalid");ad::nonbattle(db_,app.applicant.character_id);}
        ad::unchanged(db_,preserved,allowed);};
    verify();const auto g1=ad::guard(db_,none);proof.after_write();ad::unchanged(db_,g1,none);verify();return {expected,retired,apps};
}
}
