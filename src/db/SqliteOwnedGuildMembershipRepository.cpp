#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>
#include <map>
#include <set>

namespace god2 {
namespace {
using Repo=SqliteOwnedGuildMembershipRepository;
constexpr auto source="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool value,const char* message) {if(!value)throw DatabaseError(message);}
void positive(std::uint64_t value) {require(value && value<=maximum,"Invalid guild gameplay identity/revision");}
void provenance(const sqlite_detail::Statement& q,int at,const char* design) {
    require(q.text(at)=="CUSTOM_DESIGNED" && q.text(at+1)==design && q.text(at+2)==source,
            "Guild gameplay provenance mismatch");
}
std::string encoded_name(const std::string& name,bool simplified) {
    require(!name.empty() && name.size()<=60 && name.find('%')==std::string::npos &&
            std::none_of(name.begin(),name.end(),[](unsigned char c){return c<32 || c==127;}),"Unsafe guild/name text");
    try {
        const auto bytes=LegacyChineseCodec::encode(name,simplified);
        require(!bytes.empty() && bytes.size()<=15 && bytes.find('\0')==std::string::npos &&
                LegacyChineseCodec::decode(bytes,simplified)==name,"Guild/name is not lossless in both languages");
        return bytes;
    }catch(const std::exception&) {throw DatabaseError("Unrepresentable guild/name text");}
}
std::string fold(std::string name) {
    // Native551DE0 folds every byte, including a multibyte trail ASCII byte.
    for(auto& c:name)if(static_cast<unsigned char>(c)>='A' && static_cast<unsigned char>(c)<='Z')c+=32;
    return name;
}
void name_valid(const std::string& name) {(void)encoded_name(name,false);(void)encoded_name(name,true);}
void unambiguous(const std::vector<GuildRosterMember>& members) {
    for(const auto simplified:{false,true}) {
        std::set<std::string> names;
        for(const auto& member:members)require(names.insert(fold(encoded_name(member.name_utf8,simplified))).second,
                                               "Native folded guild member name collision");
    }
}
void nonbattle(sqlite3* db,std::uint64_t character) {
    sqlite_detail::Statement q(db,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s "
        "ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    q.bind_id(1,character);require(!q.row(),"Guild membership during pending battle");
}
void proof_valid(const Repo::Proof& proof) {
    require(bool(proof.before_write) && bool(proof.after_write),"Guild operation requires paired immutable session proof");
}
std::uint64_t next_revision(sqlite3* db) {
    sqlite_detail::Statement q(db,"SELECT COALESCE(MAX(revision),0) FROM owned_guilds");
    require(q.row(),"Missing guild generation clock");const auto before=q.number<std::uint64_t>(0);
    require(before<maximum,"Guild generation exhausted");return before+1;
}
std::uint64_t next_guild_id(sqlite3* db) {
    sqlite_detail::Statement q(db,"SELECT COALESCE(MAX(id),0) FROM owned_guilds");
    require(q.row(),"Missing guild identity clock");const auto before=q.number<std::uint64_t>(0);
    require(before<maximum,"Guild identity exhausted");return before+1;
}
void insert_member(sqlite3* db,std::uint64_t character,const Repo::Guild& guild) {
    sqlite_detail::Statement q(db,"INSERT INTO owned_guild_members(character_id,guild_id,revision,origin,design_id,source_sha256) "
        "VALUES(?,?,?,'CUSTOM_DESIGNED','CUSTOM-0075',?)");
    q.bind_id(1,character);q.bind_id(2,guild.id);q.bind_id(3,guild.revision);q.bind(4,std::string(source));q.done();
    require(sqlite3_changes(db)==1,"Guild member insert failed");
}
void bump(sqlite3* db,const Repo::Guild& before,std::uint64_t revision) {
    sqlite_detail::Statement q(db,"UPDATE owned_guilds SET revision=? WHERE id=? AND revision=? AND name_utf8=? "
        "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=?");
    q.bind_id(1,revision);q.bind_id(2,before.id);q.bind_id(3,before.revision);q.bind(4,before.name_utf8);
    q.bind(5,std::string(source));q.done();require(sqlite3_changes(db)==1,"Guild generation CAS failed");
}

// Preserve every other stored row, including trigger side effects in unrelated
// save tables. Membership operations are infrequent; this deliberately favors
// exact transactional preservation over a partial list of known save tables.
using Rows=std::vector<std::vector<std::uint8_t>>;
using Guard=std::map<std::string,Rows>;
using Exclusions=std::map<std::string,std::string>;
std::string quoted(const std::string& value) {
    std::string result="\"";for(auto c:value){result+=c;if(c=='\"')result+=c;}return result+'\"';
}
void append_number(std::vector<std::uint8_t>& bytes,std::uint64_t value) {
    const auto at=bytes.size();bytes.resize(at+8);
    for(unsigned i=0;i<8;++i)bytes[at+i]=static_cast<std::uint8_t>(value>>(i*8));
}
Guard guard(sqlite3* db,const Exclusions& exclusions,const Guard* capacity_hint=nullptr) {
    Guard result;
    // Capture indexes/triggers as well as tables. Paired proofs cannot silently
    // install a future mutation through a schema side effect.
    sqlite_detail::Statement schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    while(schema.row()) {
        std::vector<std::uint8_t> bytes;
        for(int column=0;column<4;++column) {
            const auto value=schema.text(column);append_number(bytes,value.size());bytes.insert(bytes.end(),value.begin(),value.end());
        }
        result[":sqlite_master"].push_back(std::move(bytes));
    }
    sqlite_detail::Statement tables(db,"SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0),definition=tables.text(1);
        auto& rows=result[name+":schema"];rows.push_back({definition.begin(),definition.end()});
        const auto found=exclusions.find(name);
        const auto sql="SELECT * FROM "+quoted(name)+(found==exclusions.end()?"":" WHERE "+found->second);
        sqlite3_stmt* statement=nullptr;
        sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&statement,nullptr));
        struct Finalize {sqlite3_stmt* statement;~Finalize(){sqlite3_finalize(statement);}} finalize{statement};
        auto& data=result[name];
        if(capacity_hint) {
            const auto hint=capacity_hint->find(name);
            if(hint!=capacity_hint->end())data.reserve(hint->second.size());
        }
        // SQLite values/pointers are valid until the next step/reset. Cache each
        // cell once, then allocate exactly one typed row without vector growth.
        // Hints reserve capacity only: every actual row/column is still read on
        // each of the baseline and both post-write preservation comparisons.
        struct Cell {int type=SQLITE_NULL,size=0;std::uint64_t number=0;const std::uint8_t* bytes=nullptr;};
        const auto column_count=sqlite3_column_count(statement);
        std::vector<Cell> cells(static_cast<std::size_t>(column_count));int rc;
        while((rc=sqlite3_step(statement))==SQLITE_ROW) {
            std::size_t row_size=static_cast<std::size_t>(column_count);
            for(int column=0;column<column_count;++column) {
                auto& cell=cells[static_cast<std::size_t>(column)];cell.type=sqlite3_column_type(statement,column);
                std::size_t extra=0;
                if(cell.type==SQLITE_INTEGER) {cell.number=static_cast<std::uint64_t>(sqlite3_column_int64(statement,column));extra=8;}
                else if(cell.type==SQLITE_FLOAT) {cell.number=std::bit_cast<std::uint64_t>(sqlite3_column_double(statement,column));extra=8;}
                else if(cell.type==SQLITE_TEXT || cell.type==SQLITE_BLOB) {
                    cell.size=sqlite3_column_bytes(statement,column);
                    // Preserve the original bytes-before-blob conversion order:
                    // TEXT in a UTF-16 database must be normalized to the same
                    // UTF-8 byte representation before obtaining its pointer.
                    cell.bytes=static_cast<const std::uint8_t*>(sqlite3_column_blob(statement,column));
                    require(cell.size>=0 && (!cell.size || cell.bytes!=nullptr),"Cannot preserve database row");
                    extra=8+static_cast<std::size_t>(cell.size);
                }
                require(extra<=std::numeric_limits<std::size_t>::max()-row_size,"Preserved database row size overflow");
                row_size+=extra;
            }
            std::vector<std::uint8_t> row(row_size);auto* write=row.data();
            const auto number=[&write](std::uint64_t value) {
                if constexpr(std::endian::native==std::endian::little)std::memcpy(write,&value,8);
                else for(unsigned i=0;i<8;++i)write[i]=static_cast<std::uint8_t>(value>>(i*8));
                write+=8;
            };
            for(const auto& cell:cells) {
                *write++=static_cast<std::uint8_t>(cell.type);
                if(cell.type==SQLITE_INTEGER || cell.type==SQLITE_FLOAT)number(cell.number);
                else if(cell.type==SQLITE_TEXT || cell.type==SQLITE_BLOB) {
                    number(static_cast<std::uint64_t>(cell.size));
                    if(cell.size){std::memcpy(write,cell.bytes,static_cast<std::size_t>(cell.size));write+=cell.size;}
                }
            }
            require(write==row.data()+row.size(),"Preserved database row encoding mismatch");
            data.push_back(std::move(row));
        }
        require(rc==SQLITE_DONE,"Cannot preserve database rows");std::sort(data.begin(),data.end());
    }
    return result;
}
void unchanged(sqlite3* db,const Guard& before,const Exclusions& exclusions) {
    require(guard(db,exclusions,&before)==before,"Guild operation changed unrelated saved rows/schema");
}
void erase_application(sqlite3* db,std::uint64_t id) {
    sqlite_detail::Statement q(db,"DELETE FROM owned_guild_applications_0078 WHERE id=?");
    q.bind_id(1,id);q.done();require(sqlite3_changes(db)==1,"Guild pending application CAS failed");
}
}

SqliteOwnedGuildMembershipRepository::SqliteOwnedGuildMembershipRepository(sqlite3* db):db_(db) {
    require(db_!=nullptr,"Null guild gameplay connection");
}
std::string SqliteOwnedGuildMembershipRepository::schema() {
    return R"SQL(
-- CUSTOM-0078 policy governance. Frozen75 guild/member provenance stays intact.
CREATE TABLE owned_guild_governance_0078 (
 guild_id INTEGER PRIMARY KEY REFERENCES owned_guilds(id) CHECK(typeof(guild_id)='integer' AND guild_id>0),
 owner_account INTEGER NOT NULL REFERENCES accounts(id) CHECK(typeof(owner_account)='integer' AND owner_account>0),
 owner_character INTEGER NOT NULL REFERENCES recovered_characters(id) CHECK(typeof(owner_character)='integer' AND owner_character>0),
 created_revision INTEGER NOT NULL CHECK(typeof(created_revision)='integer' AND created_revision>0),
 created_cost INTEGER NOT NULL CHECK(typeof(created_cost)='integer' AND created_cost BETWEEN 1 AND 4294967295),
 capacity INTEGER NOT NULL CHECK(typeof(capacity)='integer' AND capacity BETWEEN 1 AND 50),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0078'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
);
CREATE TABLE owned_guild_applications_0078 (
 id INTEGER PRIMARY KEY AUTOINCREMENT CHECK(typeof(id)='integer' AND id>0),
 guild_id INTEGER NOT NULL REFERENCES owned_guilds(id) CHECK(typeof(guild_id)='integer' AND guild_id>0),
 guild_name TEXT NOT NULL, observed_revision INTEGER NOT NULL CHECK(typeof(observed_revision)='integer' AND observed_revision>0),
 character_id INTEGER NOT NULL UNIQUE REFERENCES recovered_characters(id) ON DELETE CASCADE,
 account_id INTEGER NOT NULL REFERENCES accounts(id), slot INTEGER NOT NULL CHECK(slot BETWEEN 0 AND 1),
 profile BLOB NOT NULL CHECK(length(profile)=40),name_bytes BLOB NOT NULL CHECK(length(name_bytes) BETWEEN 1 AND 14),
 name_codepage INTEGER NOT NULL CHECK(name_codepage IN (0,950,936)),name_utf8 TEXT NOT NULL,
 role BLOB NOT NULL CHECK(length(role)=25),role_revision INTEGER NOT NULL CHECK(typeof(role_revision)='integer' AND role_revision>0),
 role_design TEXT NOT NULL CHECK(role_design='CUSTOM-0013'),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0078'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
);
CREATE INDEX owned_guild_pending_audience_0078 ON owned_guild_applications_0078(guild_id,id);
)SQL";
}
SqliteOwnedGuildMembershipRepository::Identity SqliteOwnedGuildMembershipRepository::identity(std::uint64_t account,std::uint64_t character) {
    positive(account);positive(character);
    sqlite_detail::Statement q(db_,"SELECT c.id,c.account_id,c.slot,c.profile,c.name_bytes,c.name_codepage,a.id,"
        "r.logical,r.revision,r.design_id FROM recovered_characters c LEFT JOIN accounts a ON a.id=c.account_id "
        "LEFT JOIN character_role_snapshots r ON r.character_id=c.id WHERE c.id=? AND c.account_id=?");
    q.bind_id(1,character);q.bind_id(2,account);require(q.row(),"Missing owned guild character");
    Identity result;result.character_id=q.number<std::uint64_t>(0);result.account_id=q.number<std::uint64_t>(1);
    require(result.character_id==character && result.account_id==account && q.number<std::uint64_t>(6)==account,
            "Guild gameplay account ownership mismatch");
    result.slot=q.number<std::uint8_t>(2);require(result.slot<=1,"Invalid guild gameplay character slot");
    const auto profile=q.blob(3,40,40),name=q.blob(4,1,14);
    std::copy(profile.begin(),profile.end(),result.profile.begin());result.name_bytes.assign(name.begin(),name.end());
    require(std::find(name.begin(),name.end(),0)==name.end() && std::equal(name.begin(),name.end(),result.profile.begin()) &&
            result.profile[name.size()]==0 && result.profile[29]>=1 && result.profile[29]<=8,"Invalid guild gameplay profile/name/class");
    result.name_codepage=q.number<std::uint16_t>(5);
    require(result.name_codepage==0 || result.name_codepage==950 || result.name_codepage==936,"Invalid guild gameplay name codepage");
    const std::string bytes(reinterpret_cast<const char*>(name.data()),name.size());
    try {
        if(!result.name_codepage)require(std::none_of(name.begin(),name.end(),[](auto c){return c>=128;}),"Unqualified guild name encoding");
        result.name_utf8=LegacyChineseCodec::decode(bytes,result.name_codepage==936);
        require(LegacyChineseCodec::encode(result.name_utf8,result.name_codepage==936)==bytes,"Guild identity text is not lossless");
        name_valid(result.name_utf8);
    }catch(const std::exception&){throw DatabaseError("Invalid guild gameplay character name");}
    CharacterRoleSnapshot role;const auto logical=q.blob(7,25,25);
    std::copy(logical.begin(),logical.end(),role.logical.begin());role.revision=q.number<std::uint64_t>(8);role.design_id=q.text(9);
    const auto parsed=RecoveredRoleLevel::parse(role.logical);positive(role.revision);
    require(parsed && parsed->level() && parsed->max_hp() && role.design_id=="CUSTOM-0013","Invalid/missing guild gameplay role snapshot");
    result.role=role;return result;
}
SqliteOwnedGuildMembershipRepository::Identity SqliteOwnedGuildMembershipRepository::nonmember(std::uint64_t account,std::uint64_t character) {
    const auto result=identity(account,character);SqliteGuildRepository memberships(db_);
    require(!memberships.load(account,character),"Character is already a guild member");nonbattle(db_,character);return result;
}
SqliteOwnedGuildMembershipRepository::Guild SqliteOwnedGuildMembershipRepository::guild(std::uint64_t id) {
    positive(id);sqlite_detail::Statement q(db_,"SELECT id,revision,name_utf8,origin,design_id,source_sha256 FROM owned_guilds WHERE id=?");
    q.bind_id(1,id);require(q.row(),"Guild does not exist");Guild result{q.number<std::uint64_t>(0),q.number<std::uint64_t>(1),q.text(2)};
    positive(result.revision);name_valid(result.name_utf8);provenance(q,3,"CUSTOM-0075");return result;
}
SqliteOwnedGuildMembershipRepository::Governance SqliteOwnedGuildMembershipRepository::governance(std::uint64_t id) {
    const auto target=guild(id);
    sqlite_detail::Statement q(db_,"SELECT guild_id,owner_account,owner_character,created_revision,created_cost,capacity,origin,design_id,source_sha256 "
        "FROM owned_guild_governance_0078 WHERE guild_id=?");q.bind_id(1,id);require(q.row(),"Guild has no player-created governance");
    Governance result{q.number<std::uint64_t>(0),q.number<std::uint64_t>(1),q.number<std::uint64_t>(2),q.number<std::uint64_t>(3),
                      q.number<std::uint32_t>(4),q.number<std::uint8_t>(5)};
    positive(result.owner_account);positive(result.owner_character);positive(result.created_revision);provenance(q,6,"CUSTOM-0078");
    require(result.guild_id==id && result.created_revision<=target.revision && result.created_cost && result.capacity && result.capacity<=50,
            "Invalid guild gameplay governance");
    SqliteGuildRepository memberships(db_);const auto owner=memberships.load(result.owner_account,result.owner_character);
    require(owner && owner->guild_id==id && owner->membership_revision==result.created_revision,"Guild owner is no longer the original member");
    return result;
}
bool SqliteOwnedGuildMembershipRepository::player_created(std::uint64_t id) {
    positive(id);sqlite_detail::Statement q(db_,"SELECT 1 FROM owned_guild_governance_0078 WHERE guild_id=?");
    q.bind_id(1,id);return q.row();
}
std::optional<SqliteOwnedGuildMembershipRepository::Guild> SqliteOwnedGuildMembershipRepository::find_by_name(const std::string& name) {
    name_valid(name);const auto tw=fold(encoded_name(name,false)),simplified=fold(encoded_name(name,true));
    sqlite_detail::Statement q(db_,"SELECT g.id,g.name_utf8 FROM owned_guilds g JOIN owned_guild_governance_0078 v ON v.guild_id=g.id ORDER BY g.id");
    std::optional<Guild> result;
    while(q.row()) {
        const auto candidate=q.text(1);const auto tw_matches=fold(encoded_name(candidate,false))==tw;
        const auto simplified_matches=fold(encoded_name(candidate,true))==simplified;
        if(!tw_matches && !simplified_matches)continue;
        require(tw_matches && simplified_matches && !result,"Ambiguous dual-language native folded guild lookup");
        result=guild(q.number<std::uint64_t>(0));(void)governance(result->id);
    }
    return result;
}
std::vector<GuildRosterMember> SqliteOwnedGuildMembershipRepository::roster(const Guild& target) {
    sqlite_detail::Statement q(db_,"SELECT character_id,revision,origin,design_id,source_sha256 FROM owned_guild_members WHERE guild_id=? ORDER BY character_id");
    q.bind_id(1,target.id);std::vector<GuildRosterMember> result;std::set<std::pair<std::uint64_t,std::uint8_t>> slots;
    while(q.row()) {
        const auto character=q.number<std::uint64_t>(0);positive(character);const auto revision=q.number<std::uint64_t>(1);
        positive(revision);require(revision<=target.revision,"Guild member generation exceeds guild");provenance(q,2,"CUSTOM-0075");
        sqlite_detail::Statement owner(db_,"SELECT account_id FROM recovered_characters WHERE id=?");owner.bind_id(1,character);
        require(owner.row(),"Orphan guild member");auto member=identity(owner.number<std::uint64_t>(0),character);
        require(slots.emplace(member.account_id,member.slot).second,"Duplicate guild roster account slot");
        member.membership_revision=revision;result.push_back(std::move(member));
    }
    require(!result.empty() && result.size()<=50,"Invalid complete guild roster size");unambiguous(result);return result;
}
SqliteOwnedGuildMembershipRepository::Leader SqliteOwnedGuildMembershipRepository::leader(std::uint64_t account,std::uint64_t character) {
    auto owner=identity(account,character);nonbattle(db_,character);SqliteGuildRepository memberships(db_);
    const auto membership=memberships.load(account,character);require(bool(membership),"Guild leader is not a member");
    const auto gov=governance(membership->guild_id);
    require(gov.owner_account==account && gov.owner_character==character,"Guild gameplay owner authority rejected");
    const auto members=roster(guild(membership->guild_id));require(members.size()<=gov.capacity,"Guild exceeds reviewed capacity");
    return {*membership,gov,owner,members};
}
SqliteOwnedGuildMembershipRepository::Leader SqliteOwnedGuildMembershipRepository::governance_snapshot(std::uint64_t account,std::uint64_t character) {
    // Pure read-only governance qualification. A founder's active reservation
    // is unrelated to an ordinary member's own departure. Never substitute
    // this snapshot for leader() inside any leader/officer mutation.
    auto owner=identity(account,character);SqliteGuildRepository memberships(db_);
    const auto membership=memberships.load(account,character);require(bool(membership),"Guild leader is not a member");
    const auto gov=governance(membership->guild_id);
    require(gov.owner_account==account && gov.owner_character==character,"Guild gameplay owner authority rejected");
    const auto members=roster(guild(membership->guild_id));require(members.size()<=gov.capacity,"Guild exceeds reviewed capacity");
    return {*membership,gov,owner,members};
}
std::optional<SqliteOwnedGuildMembershipRepository::Application> SqliteOwnedGuildMembershipRepository::pending(std::uint64_t account,std::uint64_t character) {
    (void)identity(account,character);sqlite_detail::Statement q(db_,
        "SELECT id,guild_id,observed_revision,guild_name,character_id,account_id,slot,profile,name_bytes,name_codepage,name_utf8,"
        "role,role_revision,role_design,origin,design_id,source_sha256 FROM owned_guild_applications_0078 WHERE character_id=? AND account_id=?");
    q.bind_id(1,character);q.bind_id(2,account);if(!q.row())return {};
    Application result;result.id=q.number<std::uint64_t>(0);positive(result.id);
    result.target={q.number<std::uint64_t>(1),q.number<std::uint64_t>(2),q.text(3)};positive(result.target.id);positive(result.target.revision);name_valid(result.target.name_utf8);
    auto& person=result.applicant;person.character_id=q.number<std::uint64_t>(4);person.account_id=q.number<std::uint64_t>(5);
    require(person.character_id==character && person.account_id==account,"Pending guild application owner mismatch");
    person.slot=q.number<std::uint8_t>(6);require(person.slot<=1,"Invalid pending guild application slot");
    const auto profile=q.blob(7,40,40),name=q.blob(8,1,14);std::copy(profile.begin(),profile.end(),person.profile.begin());person.name_bytes.assign(name.begin(),name.end());
    person.name_codepage=q.number<std::uint16_t>(9);person.name_utf8=q.text(10);name_valid(person.name_utf8);
    require((person.name_codepage==0 || person.name_codepage==950 || person.name_codepage==936) &&
            std::find(name.begin(),name.end(),0)==name.end() && std::equal(name.begin(),name.end(),person.profile.begin()) &&
            person.profile[name.size()]==0 && person.profile[29]>=1 && person.profile[29]<=8,"Invalid pending guild identity/profile");
    try {
        const std::string bytes(reinterpret_cast<const char*>(name.data()),name.size());
        if(!person.name_codepage)require(std::none_of(name.begin(),name.end(),[](auto c){return c>=128;}),"Unqualified pending guild name encoding");
        require(LegacyChineseCodec::decode(bytes,person.name_codepage==936)==person.name_utf8 &&
                LegacyChineseCodec::encode(person.name_utf8,person.name_codepage==936)==bytes,"Pending guild name identity mismatch");
    }catch(const std::exception&) {throw DatabaseError("Invalid pending guild name encoding");}
    CharacterRoleSnapshot role;const auto logical=q.blob(11,25,25);std::copy(logical.begin(),logical.end(),role.logical.begin());
    role.revision=q.number<std::uint64_t>(12);positive(role.revision);role.design_id=q.text(13);
    const auto parsed=RecoveredRoleLevel::parse(role.logical);
    require(parsed && parsed->level() && parsed->max_hp() && role.design_id=="CUSTOM-0013","Invalid pending guild role snapshot");
    person.role=role;provenance(q,14,"CUSTOM-0078");
    return result;
}
std::vector<SqliteOwnedGuildMembershipRepository::Application> SqliteOwnedGuildMembershipRepository::applications(std::uint64_t id) {
    (void)governance(id);sqlite_detail::Statement q(db_,"SELECT id,account_id,character_id FROM owned_guild_applications_0078 WHERE guild_id=? ORDER BY id");
    q.bind_id(1,id);std::vector<Application> result;
    while(q.row()) {
        const auto entry=pending(q.number<std::uint64_t>(1),q.number<std::uint64_t>(2));
        require(entry && entry->id==q.number<std::uint64_t>(0) && entry->target.id==id,"Guild application audience snapshot conflict");
        result.push_back(*entry);
    }
    return result;
}
SqliteOwnedGuildMembershipRepository::Created SqliteOwnedGuildMembershipRepository::create(
    const Identity& expected,const Wallet& wallet,const std::string& name,const Policy& policy,const Proof& proof) {
    proof_valid(proof);name_valid(name);positive(wallet.revision);
    require(policy.creation_fee && policy.minimum_level && policy.initial_capacity && policy.initial_capacity<=50,
            "Guild creation policy is missing/out of technical range");
    require(wallet.revision<maximum && wallet.amount>=policy.creation_fee,"Guild creation wallet insufficient/exhausted");
    sqlite_detail::Transaction transaction(db_);const auto id=next_guild_id(db_);
    const Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)},
        {"owned_guild_members","character_id<>"+std::to_string(expected.character_id)},
        {"owned_guild_governance_0078","guild_id<>"+std::to_string(id)},
        {"character_trade_wallets","character_id<>"+std::to_string(expected.character_id)}};
    const auto preserved=guard(db_,allowed);proof.before_write();
    require(nonmember(expected.account_id,expected.character_id)==expected,"Guild creation character snapshot conflict");
    require(!pending(expected.account_id,expected.character_id),"Guild creation has pending application");
    require(expected.role && RecoveredRoleLevel::parse(expected.role->logical)->level()>=policy.minimum_level,"Guild creation level below policy");
    SqliteTradeRepository money(db_);require(money.load_wallet(expected.account_id,expected.character_id)==std::optional(wallet),"Guild creation wallet snapshot conflict");
    sqlite_detail::Statement names(db_,"SELECT name_utf8 FROM owned_guilds");
    while(names.row())for(const auto simplified:{false,true})require(fold(encoded_name(names.text(0),simplified))!=fold(encoded_name(name,simplified)),"Native folded guild name collision");
    const auto revision=next_revision(db_);const Guild created{id,revision,name};
    sqlite_detail::Statement insert(db_,"INSERT INTO owned_guilds(id,name_utf8,revision,origin,design_id,source_sha256) VALUES(?,?,?,'CUSTOM_DESIGNED','CUSTOM-0075',?)");
    insert.bind_id(1,id);insert.bind(2,name);insert.bind_id(3,revision);insert.bind(4,std::string(source));insert.done();require(sqlite3_changes(db_)==1,"Guild creation insert failed");
    insert_member(db_,expected.character_id,created);
    Governance gov{id,expected.account_id,expected.character_id,revision,policy.creation_fee,policy.initial_capacity};
    sqlite_detail::Statement write(db_,"INSERT INTO owned_guild_governance_0078 VALUES(?,?,?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0078',?)");
    write.bind_id(1,id);write.bind_id(2,gov.owner_account);write.bind_id(3,gov.owner_character);write.bind_id(4,revision);
    write.bind(5,policy.creation_fee);write.bind(6,policy.initial_capacity);write.bind(7,std::string(source));write.done();require(sqlite3_changes(db_)==1,"Guild governance insert failed");
    const Wallet after{wallet.amount-policy.creation_fee,wallet.revision+1};
    sqlite_detail::Statement debit(db_,"UPDATE character_trade_wallets SET amount=?,revision=? WHERE character_id=? AND amount=? AND revision=? AND design_id='CUSTOM-0063'");
    debit.bind(1,after.amount);debit.bind_id(2,after.revision);debit.bind_id(3,expected.character_id);debit.bind(4,wallet.amount);debit.bind_id(5,wallet.revision);
    debit.done();require(sqlite3_changes(db_)==1,"Guild creation wallet CAS failed");
    const auto verify=[&] {
        require(guild(id)==created && governance(id)==gov,"Guild creation readback conflict");
        const auto owner=leader(expected.account_id,expected.character_id);
        auto row=expected;row.membership_revision=revision;
        require(owner.identity==expected && owner.membership==StoredGuildMembership{id,name,revision,revision} && owner.roster==std::vector<GuildRosterMember>{row},
                "Guild creation member/role readback conflict");
        require(money.load_wallet(expected.account_id,expected.character_id)==std::optional(after),"Guild creation wallet readback conflict");
        unchanged(db_,preserved,allowed);
    };verify();proof.after_write();verify();const Created result{leader(expected.account_id,expected.character_id),after};transaction.commit();return result;
}
SqliteOwnedGuildMembershipRepository::Application SqliteOwnedGuildMembershipRepository::apply(
    const Identity& expected,const Guild& target,const Proof& proof) {
    proof_valid(proof);sqlite_detail::Transaction transaction(db_);
    const Exclusions allowed{{"owned_guild_applications_0078","character_id<>"+std::to_string(expected.character_id)},
                              {"sqlite_sequence","name<>'owned_guild_applications_0078'"}};
    const auto preserved=guard(db_,allowed);
    sqlite_detail::Statement clock(db_,"SELECT max(COALESCE((SELECT seq FROM sqlite_sequence WHERE name='owned_guild_applications_0078'),0),COALESCE((SELECT MAX(id) FROM owned_guild_applications_0078),0))");
    require(clock.row(),"Missing guild application identity clock");const auto previous_id=clock.number<std::uint64_t>(0);
    require(previous_id<maximum,"Guild application identity exhausted");proof.before_write();
    require(nonmember(expected.account_id,expected.character_id)==expected,"Guild application identity snapshot conflict");
    require(guild(target.id)==target,"Guild application target snapshot conflict");const auto gov=governance(target.id);
    auto members=roster(target);require(members.size()<gov.capacity,"Guild application capacity exhausted");
    // CUSTOM-0078 technical projection admission, not a recovered native
    // pending-application gameplay rule. Members and pending identities share
    // the native50 roster cache, so qualify the entire audience under the same
    // reserved writer lock before adding another pending row. This prevents an
    // accepted request from making every leader panel unprojectable.
    const auto requests=applications(target.id);
    require(members.size()+requests.size()<50,"Guild member/pending native projection capacity exhausted");
    for(const auto& request:requests) {
        require(request.target.id==target.id && request.target.name_utf8==target.name_utf8 &&
                request.target.revision<=target.revision,"Guild pending target projection identity conflict");
        members.push_back(request.applicant);
    }
    members.push_back(expected);
    std::set<std::uint64_t> identities;
    std::set<std::pair<std::uint64_t,std::uint8_t>> owner_slots;
    for(const auto& member:members)require(identities.insert(member.character_id).second &&
        owner_slots.emplace(member.account_id,member.slot).second,"Duplicate guild member/pending projection identity");
    unambiguous(members);
    require(!pending(expected.account_id,expected.character_id),"Duplicate guild application");
    sqlite_detail::Statement write(db_,"INSERT INTO owned_guild_applications_0078(guild_id,guild_name,observed_revision,character_id,account_id,slot,profile,"
        "name_bytes,name_codepage,name_utf8,role,role_revision,role_design,origin,design_id,source_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0078',?)");
    write.bind_id(1,target.id);write.bind(2,target.name_utf8);write.bind_id(3,target.revision);write.bind_id(4,expected.character_id);write.bind_id(5,expected.account_id);
    write.bind(6,expected.slot);write.bind_blob(7,expected.profile);write.bind_blob(8,expected.name_bytes);write.bind(9,expected.name_codepage);write.bind(10,expected.name_utf8);
    write.bind_blob(11,expected.role->logical);write.bind_id(12,expected.role->revision);write.bind(13,expected.role->design_id);write.bind(14,std::string(source));write.done();
    require(sqlite3_changes(db_)==1,"Guild application insert failed");const auto id=static_cast<std::uint64_t>(sqlite3_last_insert_rowid(db_));positive(id);
    require(id==previous_id+1,"Guild application identity clock conflict");
    const Application result{id,target,expected};
    const auto verify=[&] {
        require(pending(expected.account_id,expected.character_id)==std::optional(result) && nonmember(expected.account_id,expected.character_id)==expected &&
                guild(target.id)==target && governance(target.id)==gov,"Guild application readback conflict");
        sqlite_detail::Statement seq(db_,"SELECT seq FROM sqlite_sequence WHERE name='owned_guild_applications_0078'");
        require(seq.row() && seq.number<std::uint64_t>(0)==id,"Guild application retained identity clock conflict");
        unchanged(db_,preserved,allowed);
    };verify();proof.after_write();verify();transaction.commit();return result;
}
SqliteOwnedGuildMembershipRepository::Approved SqliteOwnedGuildMembershipRepository::approve(
    const Leader& expected,const Application& application,const Proof& proof) {
    proof_valid(proof);sqlite_detail::Transaction transaction(db_);
    const Exclusions allowed{{"owned_guilds","id<>"+std::to_string(expected.governance.guild_id)},
        {"owned_guild_members","character_id<>"+std::to_string(application.applicant.character_id)},
        {"owned_guild_applications_0078","id<>"+std::to_string(application.id)}};
    const auto preserved=guard(db_,allowed);proof.before_write();
    const auto& owner=expected.identity;const auto& applicant=application.applicant;
    require(leader(owner.account_id,owner.character_id)==expected,"Guild approval leader/governance/full-roster snapshot conflict");
    require(pending(applicant.account_id,applicant.character_id)==std::optional(application) && nonmember(applicant.account_id,applicant.character_id)==applicant,
            "Guild approval applicant snapshot conflict");
    const auto before=guild(expected.governance.guild_id);
    // Other approvals may advance generation. Require the leader's current full
    // lease and the application's exact retained identity/name, not old bytes as
    // authority to join a renamed/reassigned guild.
    require(application.target.id==before.id && application.target.name_utf8==before.name_utf8 && application.target.revision<=before.revision,
            "Guild approval target identity conflict");
    require(expected.roster.size()<expected.governance.capacity,"Guild approval capacity exhausted");
    auto members=expected.roster;members.push_back(applicant);unambiguous(members);
    const auto revision=next_revision(db_);const Guild after{before.id,revision,before.name_utf8};bump(db_,before,revision);
    insert_member(db_,applicant.character_id,after);erase_application(db_,application.id);
    const StoredGuildMembership joined{after.id,after.name_utf8,revision,revision};
    auto row=applicant;row.membership_revision=revision;members.back()=row;
    std::sort(members.begin(),members.end(),[](const auto& a,const auto& b){return a.character_id<b.character_id;});
    auto wanted=expected;wanted.membership.guild_revision=revision;wanted.roster=members;
    SqliteGuildRepository memberships(db_);
    const auto verify=[&] {
        require(guild(after.id)==after && leader(owner.account_id,owner.character_id)==wanted &&
                memberships.load(applicant.account_id,applicant.character_id)==std::optional(joined) &&
                identity(applicant.account_id,applicant.character_id)==applicant && !pending(applicant.account_id,applicant.character_id),
                "Guild approval readback conflict");
        nonbattle(db_,applicant.character_id);unchanged(db_,preserved,allowed);
    };verify();proof.after_write();verify();const Approved result{wanted,joined};transaction.commit();return result;
}
void SqliteOwnedGuildMembershipRepository::reject(const Leader& expected,const Application& application,const Proof& proof) {
    proof_valid(proof);sqlite_detail::Transaction transaction(db_);
    const Exclusions allowed{{"owned_guild_applications_0078","id<>"+std::to_string(application.id)}};
    const auto preserved=guard(db_,allowed);proof.before_write();const auto& owner=expected.identity;const auto& applicant=application.applicant;
    require(leader(owner.account_id,owner.character_id)==expected && application.target.id==expected.governance.guild_id &&
            application.target.name_utf8==expected.membership.name_utf8 && pending(applicant.account_id,applicant.character_id)==std::optional(application),
            "Guild rejection lease/target conflict");
    erase_application(db_,application.id);
    const auto verify=[&] {require(leader(owner.account_id,owner.character_id)==expected && !pending(applicant.account_id,applicant.character_id),"Guild rejection readback conflict");unchanged(db_,preserved,allowed);};
    verify();proof.after_write();verify();transaction.commit();
}
void SqliteOwnedGuildMembershipRepository::cancel(const Identity& expected,const Application& application,const Proof& proof) {
    proof_valid(proof);sqlite_detail::Transaction transaction(db_);
    const Exclusions allowed{{"owned_guild_applications_0078","id<>"+std::to_string(application.id)}};
    const auto preserved=guard(db_,allowed);proof.before_write();
    // Cancellation authenticates the current owner and exact pending record.
    // Advancing level/name after applying invalidates approval but must not
    // trap that player in a permanently uncancellable old application.
    require(expected.account_id==application.applicant.account_id && expected.character_id==application.applicant.character_id &&
            nonmember(expected.account_id,expected.character_id)==expected &&
            pending(expected.account_id,expected.character_id)==std::optional(application),"Guild cancellation owner/lease conflict");
    erase_application(db_,application.id);
    const auto verify=[&] {require(nonmember(expected.account_id,expected.character_id)==expected && !pending(expected.account_id,expected.character_id),"Guild cancellation readback conflict");unchanged(db_,preserved,allowed);};
    verify();proof.after_write();verify();transaction.commit();
}
SqliteOwnedGuildMembershipRepository::Left SqliteOwnedGuildMembershipRepository::member_leave(
    const Identity& self,const StoredGuildMembership& membership,const Leader& expected_leader,
    const std::vector<Application>& expected_applications,const Proof& proof) {
    proof_valid(proof);positive(self.account_id);positive(self.character_id);
    positive(membership.guild_id);positive(membership.guild_revision);positive(membership.membership_revision);
    require(!self.membership_revision,"Guild leave self identity carries membership authority");
    sqlite_detail::Transaction transaction(db_); // BEGIN IMMEDIATE before proof/leases/CAS.
    const Exclusions allowed{{"owned_guilds","id<>"+std::to_string(membership.guild_id)},
        {"owned_guild_members","character_id<>"+std::to_string(self.character_id)}};
    const auto preserved=guard(db_,allowed); // G0: every other typed row and complete schema.
    // The sanctioned guild row may change only its revision, including when
    // an installation has unknown extra columns. Preserve every other column
    // with the same typed representation as G0/G1/G2, not a known-field list.
    const auto guild_fields=[&] {
        sqlite3_stmt* statement=nullptr;
        sqlite_detail::check(db_,sqlite3_prepare_v2(db_,"SELECT * FROM owned_guilds WHERE id=?",-1,&statement,nullptr));
        struct Finalize {sqlite3_stmt* statement;~Finalize(){sqlite3_finalize(statement);}} finalize{statement};
        sqlite_detail::check(db_,sqlite3_bind_int64(statement,1,static_cast<sqlite3_int64>(membership.guild_id)));
        require(sqlite3_step(statement)==SQLITE_ROW,"Missing guild leave retained row");
        std::vector<std::uint8_t> result;unsigned revisions=0;
        for(int column=0;column<sqlite3_column_count(statement);++column) {
            if(std::string(sqlite3_column_name(statement,column))=="revision") {++revisions;continue;}
            const auto type=sqlite3_column_type(statement,column);result.push_back(static_cast<std::uint8_t>(type));
            if(type==SQLITE_INTEGER)append_number(result,static_cast<std::uint64_t>(sqlite3_column_int64(statement,column)));
            else if(type==SQLITE_FLOAT)append_number(result,std::bit_cast<std::uint64_t>(sqlite3_column_double(statement,column)));
            else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                const auto size=sqlite3_column_bytes(statement,column);
                const auto* bytes=static_cast<const std::uint8_t*>(sqlite3_column_blob(statement,column));
                require(size>=0 && (!size || bytes),"Cannot preserve guild leave retained fields");
                append_number(result,static_cast<std::uint64_t>(size));if(size)result.insert(result.end(),bytes,bytes+size);
            }
        }
        require(revisions==1 && sqlite3_step(statement)==SQLITE_DONE,"Ambiguous guild leave retained row");return result;
    };
    const auto retained_fields=guild_fields();proof.before_write();
    require(identity(self.account_id,self.character_id)==self,"Guild leave identity snapshot conflict");
    nonbattle(db_,self.character_id);SqliteGuildRepository memberships(db_);
    require(memberships.load(self.account_id,self.character_id)==std::optional(membership),"Guild leave membership snapshot conflict");
    const auto before=guild(membership.guild_id);const auto gov=governance(membership.guild_id);
    require(before==Guild{membership.guild_id,membership.guild_revision,membership.name_utf8} &&
        governance_snapshot(gov.owner_account,gov.owner_character)==expected_leader &&
        expected_leader.governance==gov,"Guild leave governance/leader/full-roster snapshot conflict");
    require(self.character_id!=gov.owner_character,"Guild founder cannot leave the player-created guild");
    auto wanted=expected_leader;
    const auto member=std::find_if(wanted.roster.begin(),wanted.roster.end(),[&](const auto& row){return row.character_id==self.character_id;});
    require(member!=wanted.roster.end() && member->membership_revision==membership.membership_revision,
            "Guild leave member absent from complete roster");
    auto own=*member;own.membership_revision=0;require(own==self,"Guild leave full self member identity conflict");
    const auto requests=applications(before.id);
    require(requests==expected_applications && wanted.roster.size()+requests.size()<=50,
            "Guild leave complete pending projection snapshot conflict");
    auto audience=wanted.roster;std::set<std::uint64_t> characters,request_ids;
    std::set<std::pair<std::uint64_t,std::uint8_t>> slots;
    for(const auto& request:requests) {
        const auto& applicant=request.applicant;
        require(request.target.id==before.id && request.target.name_utf8==before.name_utf8 &&
                request.target.revision<=before.revision && !applicant.membership_revision &&
                request_ids.insert(request.id).second &&
                !memberships.load(applicant.account_id,applicant.character_id),
                "Guild leave pending/member projection identity conflict");
        audience.push_back(applicant);
    }
    for(const auto& accepted:wanted.roster)require(!pending(accepted.account_id,accepted.character_id),
        "Guild leave accepted member is also a pending applicant");
    for(const auto& row:audience)require(characters.insert(row.character_id).second &&
        slots.emplace(row.account_id,row.slot).second,"Guild leave ambiguous complete audience identity");
    unambiguous(audience);
    require(guild_fields()==retained_fields,"Guild leave retained fields changed before CAS");
    wanted.roster.erase(member);
    const auto revision=next_revision(db_);const Guild after{before.id,revision,before.name_utf8};bump(db_,before,revision);
    const StoredGuildMembership bumped{membership.guild_id,membership.name_utf8,revision,membership.membership_revision};
    require(memberships.load(self.account_id,self.character_id)==std::optional(bumped),"Guild leave membership changed during generation CAS");
    sqlite_detail::Statement erase(db_,"DELETE FROM owned_guild_members WHERE character_id=? AND guild_id=? AND revision=? "
        "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=? "
        "AND EXISTS(SELECT 1 FROM recovered_characters c WHERE c.id=owned_guild_members.character_id AND c.account_id=?)");
    erase.bind_id(1,self.character_id);erase.bind_id(2,membership.guild_id);erase.bind_id(3,membership.membership_revision);
    erase.bind(4,std::string(source));erase.bind_id(5,self.account_id);erase.done();require(sqlite3_changes(db_)==1,"Guild leave self-member delete CAS failed");
    wanted.membership.guild_revision=revision;
    const auto verify=[&] {
        require(guild(before.id)==after && governance(before.id)==gov &&
                governance_snapshot(gov.owner_account,gov.owner_character)==wanted &&
                applications(before.id)==requests && nonmember(self.account_id,self.character_id)==self &&
                !pending(self.account_id,self.character_id),"Guild leave complete readback conflict");
        require(guild_fields()==retained_fields,"Guild leave changed protected retained fields");
        unchanged(db_,preserved,allowed); // G1 before callback; G2 after immutable world callback.
    };
    verify();proof.after_write();verify();const Left result{after,wanted};transaction.commit();return result;
}
SqliteOwnedGuildMembershipRepository::Kicked SqliteOwnedGuildMembershipRepository::member_kick(
    const Leader& expected_leader,const std::vector<Application>& expected_applications,
    const Identity& target,const StoredGuildMembership& membership,const Proof& proof) {
    // CUSTOM-0080: founder authority and target readiness are independent leases.
    // Original kick/officer restrictions remain unknown. This explicit custom
    // scope only removes an ordinary accepted nonbattle member, including offline.
    proof_valid(proof);positive(target.account_id);positive(target.character_id);
    positive(membership.guild_id);positive(membership.guild_revision);positive(membership.membership_revision);
    require(!target.membership_revision,"Guild kick target identity carries membership authority");
    sqlite_detail::Transaction transaction(db_); // Paired proofs and all SQL leases share BEGIN IMMEDIATE.
    const Exclusions allowed{{"owned_guilds","id<>"+std::to_string(membership.guild_id)},
        {"owned_guild_members","character_id<>"+std::to_string(target.character_id)}};
    const auto preserved=guard(db_,allowed);
    // Only the sanctioned guild revision can change. Every other known/opaque
    // column is retained with its full typed representation, including extensions.
    const auto guild_fields=[&] {
        sqlite3_stmt* statement=nullptr;
        sqlite_detail::check(db_,sqlite3_prepare_v2(db_,"SELECT * FROM owned_guilds WHERE id=?",-1,&statement,nullptr));
        struct Finalize {sqlite3_stmt* statement;~Finalize(){sqlite3_finalize(statement);}} finalize{statement};
        sqlite_detail::check(db_,sqlite3_bind_int64(statement,1,static_cast<sqlite3_int64>(membership.guild_id)));
        require(sqlite3_step(statement)==SQLITE_ROW,"Missing guild kick retained row");
        std::vector<std::uint8_t> result;unsigned revisions=0;
        for(int column=0;column<sqlite3_column_count(statement);++column) {
            if(std::string(sqlite3_column_name(statement,column))=="revision") {++revisions;continue;}
            const auto type=sqlite3_column_type(statement,column);result.push_back(static_cast<std::uint8_t>(type));
            if(type==SQLITE_INTEGER)append_number(result,static_cast<std::uint64_t>(sqlite3_column_int64(statement,column)));
            else if(type==SQLITE_FLOAT)append_number(result,std::bit_cast<std::uint64_t>(sqlite3_column_double(statement,column)));
            else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                const auto size=sqlite3_column_bytes(statement,column);
                const auto* bytes=static_cast<const std::uint8_t*>(sqlite3_column_blob(statement,column));
                require(size>=0 && (!size || bytes),"Cannot preserve guild kick retained fields");
                append_number(result,static_cast<std::uint64_t>(size));if(size)result.insert(result.end(),bytes,bytes+size);
            }
        }
        require(revisions==1 && sqlite3_step(statement)==SQLITE_DONE,"Ambiguous guild kick retained row");return result;
    };
    const auto retained_fields=guild_fields();proof.before_write();
    const auto& owner=expected_leader.identity;
    require(leader(owner.account_id,owner.character_id)==expected_leader,
            "Guild kick founder/governance/full-roster snapshot conflict");
    require(identity(target.account_id,target.character_id)==target,"Guild kick target identity snapshot conflict");
    nonbattle(db_,target.character_id);SqliteGuildRepository memberships(db_);
    require(memberships.load(target.account_id,target.character_id)==std::optional(membership),
            "Guild kick target membership snapshot conflict");
    const auto before=guild(membership.guild_id);const auto gov=governance(membership.guild_id);
    require(before==Guild{membership.guild_id,membership.guild_revision,membership.name_utf8} &&
        expected_leader.membership.guild_id==before.id && expected_leader.governance==gov,
        "Guild kick foreign guild/governance snapshot conflict");
    require(target.character_id!=owner.character_id && target.character_id!=gov.owner_character,
            "Guild founder cannot kick self/founder");
    auto wanted=expected_leader;
    const auto member=std::find_if(wanted.roster.begin(),wanted.roster.end(),[&](const auto& row){return row.character_id==target.character_id;});
    require(member!=wanted.roster.end() && member->membership_revision==membership.membership_revision,
            "Guild kick target absent from complete accepted roster");
    auto target_row=*member;target_row.membership_revision=0;
    require(target_row==target,"Guild kick full target roster identity conflict");
    const auto requests=applications(before.id);
    require(requests==expected_applications && wanted.roster.size()+requests.size()<=50,
            "Guild kick complete pending projection snapshot conflict");
    auto audience=wanted.roster;std::set<std::uint64_t> characters,request_ids;
    std::set<std::pair<std::uint64_t,std::uint8_t>> slots;
    for(const auto& request:requests) {
        const auto& applicant=request.applicant;
        require(request.target.id==before.id && request.target.name_utf8==before.name_utf8 &&
                request.target.revision<=before.revision && !applicant.membership_revision &&
                request_ids.insert(request.id).second &&
                !memberships.load(applicant.account_id,applicant.character_id),
                "Guild kick pending/member projection identity conflict");
        audience.push_back(applicant);
    }
    for(const auto& accepted:wanted.roster)require(!pending(accepted.account_id,accepted.character_id),
        "Guild kick accepted member is also a pending applicant");
    for(const auto& row:audience)require(characters.insert(row.character_id).second &&
        slots.emplace(row.account_id,row.slot).second,"Guild kick ambiguous complete audience identity");
    unambiguous(audience);
    require(guild_fields()==retained_fields,"Guild kick retained fields changed before CAS");
    wanted.roster.erase(member);
    const auto revision=next_revision(db_);const Guild after{before.id,revision,before.name_utf8};bump(db_,before,revision);
    const StoredGuildMembership bumped{membership.guild_id,membership.name_utf8,revision,membership.membership_revision};
    require(memberships.load(target.account_id,target.character_id)==std::optional(bumped),
            "Guild kick target membership changed during generation CAS");
    sqlite_detail::Statement erase(db_,"DELETE FROM owned_guild_members WHERE character_id=? AND guild_id=? AND revision=? "
        "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=? "
        "AND EXISTS(SELECT 1 FROM recovered_characters c WHERE c.id=owned_guild_members.character_id AND c.account_id=?)");
    erase.bind_id(1,target.character_id);erase.bind_id(2,membership.guild_id);erase.bind_id(3,membership.membership_revision);
    erase.bind(4,std::string(source));erase.bind_id(5,target.account_id);erase.done();require(sqlite3_changes(db_)==1,"Guild kick target-member delete CAS failed");
    wanted.membership.guild_revision=revision;
    const auto verify=[&] {
        require(guild(before.id)==after && governance(before.id)==gov &&
                leader(owner.account_id,owner.character_id)==wanted && applications(before.id)==requests &&
                nonmember(target.account_id,target.character_id)==target && !pending(target.account_id,target.character_id),
                "Guild kick complete readback conflict");
        require(guild_fields()==retained_fields,"Guild kick changed protected retained fields");
        unchanged(db_,preserved,allowed);
    };
    verify();proof.after_write();verify();
    const Kicked result{after,wanted,target,membership};transaction.commit();return result;
}
// CUSTOM-0081 native75: retained identity/history, no fee or refund.
SqliteOwnedGuildMembershipRepository::Disbanded
SqliteOwnedGuildMembershipRepository::disband(
    const Leader& expected,const std::vector<Application>& expected_applications,
    const Proof& proof) {
    // Original server restrictions/economics remain unknown. This candidate
    // retains guild identity, folded name reservation and announcement history;
    // it grants no refund and no unrelated save mutation. Pending applicants are
    // also nonbattle under this stricter explicit candidate audience policy.
    proof_valid(proof);
    positive(expected.membership.guild_id);
    positive(expected.membership.guild_revision);
    positive(expected.membership.membership_revision);
    const auto id=expected.membership.guild_id;
    sqlite_detail::Transaction transaction(db_); // BEGIN IMMEDIATE, one commit.
    const Exclusions allowed{
        {"owned_guilds","id<>"+std::to_string(id)},
        {"owned_guild_members","guild_id<>"+std::to_string(id)},
        {"owned_guild_governance_0078","guild_id<>"+std::to_string(id)},
        {"owned_guild_applications_0078","guild_id<>"+std::to_string(id)}};
    // Keep all sequences, all announcement rows and foreign/unknown tables.
    const auto preserved=guard(db_,allowed);
    const Exclusions nothing;
    const auto before_proof=guard(db_,nothing);
    const auto retained_fields=[&] {
        sqlite3_stmt* statement=nullptr;
        sqlite_detail::check(db_,sqlite3_prepare_v2(db_,
            "SELECT * FROM owned_guilds WHERE id=?",-1,&statement,nullptr));
        struct Finalize {sqlite3_stmt* statement;~Finalize(){sqlite3_finalize(statement);}} finalize{statement};
        sqlite_detail::check(db_,sqlite3_bind_int64(statement,1,static_cast<sqlite3_int64>(id)));
        require(sqlite3_step(statement)==SQLITE_ROW,"Missing disband retained guild row");
        std::vector<std::uint8_t> result;unsigned revisions=0;
        for(int column=0;column<sqlite3_column_count(statement);++column) {
            if(std::string(sqlite3_column_name(statement,column))=="revision") {++revisions;continue;}
            const auto type=sqlite3_column_type(statement,column);
            result.push_back(static_cast<std::uint8_t>(type));
            if(type==SQLITE_INTEGER)append_number(result,static_cast<std::uint64_t>(sqlite3_column_int64(statement,column)));
            else if(type==SQLITE_FLOAT)append_number(result,std::bit_cast<std::uint64_t>(sqlite3_column_double(statement,column)));
            else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                const auto size=sqlite3_column_bytes(statement,column);
                const auto* bytes=static_cast<const std::uint8_t*>(sqlite3_column_blob(statement,column));
                require(size>=0 && (!size || bytes),"Cannot preserve disband retained guild fields");
                append_number(result,static_cast<std::uint64_t>(size));
                if(size)result.insert(result.end(),bytes,bytes+size);
            }
        }
        require(revisions==1 && sqlite3_step(statement)==SQLITE_DONE,
            "Ambiguous disband retained guild row");return result;
    };
    const auto fields=retained_fields();
    proof.before_write();
    // Unlike the mutation allowlist, a proof itself may alter NO SQL value,
    // including opaque columns of rows that will be deleted by the operation.
    unchanged(db_,before_proof,nothing);
    const auto& owner=expected.identity;
    require(!owner.membership_revision &&
        leader(owner.account_id,owner.character_id)==expected,
        "Disband founder/governance/full accepted roster conflict");
    const Guild before{id,expected.membership.guild_revision,expected.membership.name_utf8};
    require(guild(id)==before && governance(id)==expected.governance &&
        expected.governance.guild_id==id && expected.governance.owner_account==owner.account_id &&
        expected.governance.owner_character==owner.character_id,
        "Disband foreign guild/governance founder conflict");
    const auto requests=applications(id);
    require(requests==expected_applications && !expected.roster.empty() &&
        expected.roster.size()<=expected.governance.capacity &&
        requests.size()<=50-expected.roster.size(),"Disband complete audience snapshot conflict");
    SqliteGuildRepository memberships(db_);
    auto audience=expected.roster;
    std::set<std::uint64_t> characters,request_ids;
    std::set<std::pair<std::uint64_t,std::uint8_t>> slots;
    bool has_founder=false;
    for(const auto& accepted:expected.roster) {
        auto identity_row=accepted;identity_row.membership_revision=0;
        require(identity(accepted.account_id,accepted.character_id)==identity_row &&
            memberships.load(accepted.account_id,accepted.character_id)==
                std::optional(StoredGuildMembership{id,before.name_utf8,before.revision,accepted.membership_revision}) &&
            !pending(accepted.account_id,accepted.character_id),"Disband accepted member identity/membership conflict");
        nonbattle(db_,accepted.character_id);
        if(accepted.character_id==owner.character_id) {
            require(!has_founder && accepted.account_id==owner.account_id &&
                accepted.membership_revision==expected.governance.created_revision,
                "Disband original founder row conflict");has_founder=true;
        }
    }
    require(has_founder,"Disband founder absent from complete accepted roster");
    for(const auto& request:requests) {
        const auto& applicant=request.applicant;
        require(request.target.id==id && request.target.name_utf8==before.name_utf8 &&
            request.target.revision<=before.revision && !applicant.membership_revision &&
            request_ids.insert(request.id).second &&
            !memberships.load(applicant.account_id,applicant.character_id),
            "Disband pending/member identity conflict");
        // Pending profile/role/name is saved application history, not current
        // character action authority. Current identity must remain valid and
        // owned in the same slot, but legitimate role/level evolution is allowed.
        const auto now=identity(applicant.account_id,applicant.character_id);
        require(now.slot==applicant.slot,"Disband pending owner slot conflict");
        nonbattle(db_,applicant.character_id);
        audience.push_back(applicant);
    }
    for(const auto& row:audience)require(characters.insert(row.character_id).second &&
        slots.emplace(row.account_id,row.slot).second,"Disband ambiguous complete audience");
    unambiguous(audience);
    require(retained_fields()==fields,"Disband retained row changed before mutation");
    const auto revision=next_revision(db_);
    const Guild after{id,revision,before.name_utf8};
    bump(db_,before,revision); // Retain identity/name/unknown columns and trigger.
    for(const auto& request:requests) {
        sqlite_detail::Statement erase(db_,
            "DELETE FROM owned_guild_applications_0078 WHERE id=? AND guild_id=? AND "
            "observed_revision=? AND guild_name=? AND character_id=? AND account_id=? AND slot=? "
            "AND profile=? AND name_bytes=? AND name_codepage=? AND name_utf8=? "
            "AND role=? AND role_revision=? AND role_design=? "
            "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0078' AND source_sha256=?");
        erase.bind_id(1,request.id);erase.bind_id(2,id);erase.bind_id(3,request.target.revision);
        erase.bind(4,request.target.name_utf8);erase.bind_id(5,request.applicant.character_id);
        erase.bind_id(6,request.applicant.account_id);erase.bind(7,request.applicant.slot);
        erase.bind_blob(8,request.applicant.profile);erase.bind_blob(9,request.applicant.name_bytes);
        erase.bind(10,request.applicant.name_codepage);erase.bind(11,request.applicant.name_utf8);
        erase.bind_blob(12,request.applicant.role->logical);erase.bind_id(13,request.applicant.role->revision);
        erase.bind(14,request.applicant.role->design_id);erase.bind(15,std::string(source));erase.done();
        require(sqlite3_changes(db_)==1,"Disband pending deletion CAS failed");
    }
    // Members are deleted individually with immutable ownership/provenance CAS.
    // Governance stays until all membership deletions complete; none of these
    // statements are separate transactions and any later failure rolls back all.
    for(const auto& accepted:expected.roster) {
        sqlite_detail::Statement erase(db_,
            "DELETE FROM owned_guild_members WHERE character_id=? AND guild_id=? AND revision=? "
            "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0075' AND source_sha256=? "
            "AND EXISTS(SELECT 1 FROM recovered_characters c WHERE c.id=owned_guild_members.character_id "
            "AND c.account_id=? AND c.slot=?)");
        erase.bind_id(1,accepted.character_id);erase.bind_id(2,id);erase.bind_id(3,accepted.membership_revision);
        erase.bind(4,std::string(source));erase.bind_id(5,accepted.account_id);erase.bind(6,accepted.slot);
        erase.done();require(sqlite3_changes(db_)==1,"Disband accepted deletion CAS failed");
    }
    const auto& gov=expected.governance;
    sqlite_detail::Statement retire(db_,
        "DELETE FROM owned_guild_governance_0078 WHERE guild_id=? AND owner_account=? AND owner_character=? "
        "AND created_revision=? AND created_cost=? AND capacity=? AND origin='CUSTOM_DESIGNED' "
        "AND design_id='CUSTOM-0078' AND source_sha256=?");
    retire.bind_id(1,id);retire.bind_id(2,gov.owner_account);retire.bind_id(3,gov.owner_character);
    retire.bind_id(4,gov.created_revision);retire.bind(5,gov.created_cost);retire.bind(6,gov.capacity);
    retire.bind(7,std::string(source));retire.done();
    require(sqlite3_changes(db_)==1,"Disband governance deletion CAS failed");
    const auto verify=[&] {
        require(guild(id)==after && retained_fields()==fields,
            "Disband retained guild generation/nonrevision conflict");
        // governance()/leader()/applications(gid) intentionally fail once
        // governance is gone: do not call them for successful final readback.
        for(const auto* table:{"owned_guild_members","owned_guild_governance_0078","owned_guild_applications_0078"}) {
            const auto sql="SELECT COUNT(*) FROM "+quoted(table)+" WHERE guild_id=?";
            sqlite_detail::Statement rows(db_,sql.c_str());
            rows.bind_id(1,id);require(rows.row() && rows.number<std::uint64_t>(0)==0,
                "Disband left target membership/governance/pending rows");
        }
        require(!player_created(id) && !find_by_name(before.name_utf8),"Disband retired guild remains discoverable");
        for(const auto& accepted:expected.roster) {
            auto expected_identity=accepted;expected_identity.membership_revision=0;
            require(nonmember(accepted.account_id,accepted.character_id)==expected_identity &&
                !pending(accepted.account_id,accepted.character_id),"Disband former member readback conflict");
        }
        for(const auto& request:requests) {
            require(!memberships.load(request.applicant.account_id,request.applicant.character_id) &&
                !pending(request.applicant.account_id,request.applicant.character_id),
                "Disband former applicant readback conflict");
            nonbattle(db_,request.applicant.character_id);
        }
        unchanged(db_,preserved,allowed);
    };
    verify();proof.after_write();verify();
    const Disbanded result{after,expected,requests};
    transaction.commit();return result;
}

// REVIEW DRAFT ONLY. Insert before final namespace god2 closing brace of the
// existing membership repository .cpp. Reuses that translation unit's private
// require/guard/bump/nonbattle/next_revision/proof_valid helpers without edits.
// Not a standalone TU. Schema51/officer feature is NOT activated by this file.
namespace {
// Typed column-exclusion snapshot for exactly one retained row. Never ignore
// whole rows just because known columns match; unknown fields also survive.
std::vector<std::uint8_t> officer_retained_fields(sqlite3* db,const std::string& sql,
                                               const std::set<std::string>& permitted) {
    sqlite3_stmt* s=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&s,nullptr));
    struct Finalize {sqlite3_stmt* s;~Finalize(){sqlite3_finalize(s);}} f{s};
    const auto step=sqlite3_step(s);require(step==SQLITE_ROW || step==SQLITE_DONE,"Officer retained row read failed");
    if(step==SQLITE_DONE)return {};std::vector<std::uint8_t> out;out.push_back(1);
    std::set<std::string> seen;
    for(int c=0;c<sqlite3_column_count(s);++c) {
        const std::string name=sqlite3_column_name(s,c);
        if(permitted.contains(name)){seen.insert(name);continue;}
        append_number(out,name.size());out.insert(out.end(),name.begin(),name.end());
        const auto type=sqlite3_column_type(s,c);out.push_back(static_cast<std::uint8_t>(type));
        if(type==SQLITE_INTEGER)append_number(out,static_cast<std::uint64_t>(sqlite3_column_int64(s,c)));
        else if(type==SQLITE_FLOAT)append_number(out,std::bit_cast<std::uint64_t>(sqlite3_column_double(s,c)));
        else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
            const auto n=sqlite3_column_bytes(s,c);const auto* p=static_cast<const std::uint8_t*>(sqlite3_column_blob(s,c));
            require(n>=0 && (!n || p),"Officer retained bytes invalid");append_number(out,n);
            if(n)out.insert(out.end(),p,p+n);
        }
    }
    require(seen==permitted && sqlite3_step(s)==SQLITE_DONE,"Officer retained row ambiguity");return out;
}
bool officer_literal_default(const std::string& text) {
    if(text=="NULL")return true;
    if(text.size()>=3 && (text[0]=='x' || text[0]=='X') && text[1]=='\'' && text.back()=='\'') {
        if((text.size()-3)%2)return false;
        for(std::size_t i=2;i+1<text.size();++i) {
            const auto c=text[i];if(!((c>='0' && c<='9') || (c>='a' && c<='f') || (c>='A' && c<='F')))return false;
        }
        return true;
    }
    if(text.size()>=2 && text.front()=='\'' && text.back()=='\'') {
        for(std::size_t i=1;i+1<text.size();++i)if(text[i]=='\'') {
            if(i+2>=text.size() || text[i+1]!='\'')return false;++i;
        }
        return true;
    }
    if(text.empty())return false;
    bool digit=false;
    for(const auto c:text) {
        if(c>='0' && c<='9'){digit=true;continue;}
        if(c!='+' && c!='-' && c!='.' && c!='e' && c!='E')return false;
    }
    return digit; // Malformed numerical syntax fails readonly SQL prepare.
}
std::vector<std::uint8_t> officer_new_opaque_defaults(sqlite3* db,const std::set<std::string>& known) {
    // A freshly inserted row has no old opaque-field snapshot. Compare unknown
    // columns to literal schema defaults; do not let AFTER INSERT rewrite them
    // under the new-row allowlist. Expressions/functions fail closed, not execute.
    sqlite_detail::Statement q(db,"SELECT name,COALESCE(dflt_value,'NULL') FROM pragma_table_info('owned_guild_officers_0082') ORDER BY cid");
    std::string sql;std::set<std::string> seen;
    while(q.row()) {
        const auto name=q.text(0);if(known.contains(name)){seen.insert(name);continue;}
        const auto literal=q.text(1);require(officer_literal_default(literal),"Officer unknown column default is not a safe literal");
        sql+=(sql.empty()?"SELECT ":",")+literal+" AS "+quoted(name);
    }
    require(seen==known,"Officer schema known columns missing");
    return sql.empty()?std::vector<std::uint8_t>{1}:officer_retained_fields(db,sql,{});
}
}
std::string SqliteOwnedGuildMembershipRepository::officer_schema() {
    // CUSTOM-0082 PROPOSED. No character FK: character deletion must preserve
    // inert history rather than delete an audit row or block a character save.
    // No governance FK: native75 retains gid but removes governance. Current
    // authority ALWAYS joins live governance+member+exact join revision.
    return R"SQL(CREATE TABLE owned_guild_officers_0082(
guild_id INTEGER NOT NULL CHECK(typeof(guild_id)='integer' AND guild_id>0) REFERENCES owned_guilds(id),
account_id INTEGER NOT NULL CHECK(typeof(account_id)='integer' AND account_id>0),
character_id INTEGER NOT NULL CHECK(typeof(character_id)='integer' AND character_id>0),
account_slot INTEGER NOT NULL CHECK(typeof(account_slot)='integer' AND account_slot BETWEEN 0 AND 1),
membership_revision INTEGER NOT NULL CHECK(typeof(membership_revision)='integer' AND membership_revision>0),
revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>=membership_revision),
role INTEGER NOT NULL CHECK(typeof(role)='integer' AND role IN(1,2)),
origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0082'),
source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'),
PRIMARY KEY(guild_id,character_id,membership_revision)
) WITHOUT ROWID;)SQL";
}
SqliteOwnedGuildMembershipRepository::OfficerHistory
SqliteOwnedGuildMembershipRepository::officer_history(std::uint64_t id) {
    positive(id);OfficerHistory rows;
    sqlite_detail::Statement q(db_,"SELECT guild_id,account_id,character_id,account_slot,membership_revision,revision,role,"
        "origin,design_id,source_sha256 FROM owned_guild_officers_0082 WHERE guild_id=? "
        "ORDER BY character_id,membership_revision");q.bind_id(1,id);
    while(q.row()) {
        provenance(q,7,"CUSTOM-0082");
        OfficerRow row{q.number<std::uint64_t>(0),q.number<std::uint64_t>(1),q.number<std::uint64_t>(2),
            q.number<std::uint64_t>(4),q.number<std::uint64_t>(5),q.number<std::uint8_t>(3),q.number<std::uint8_t>(6)};
        positive(row.account_id);positive(row.character_id);positive(row.membership_revision);positive(row.revision);
        require(row.guild_id==id && row.account_slot<2 && (row.role==1 || row.role==2) &&
            row.revision>=row.membership_revision,"Invalid officer history row");rows.push_back(row);
    }
    return rows; // Deliberately reads retired guild history without governance().
}
std::uint8_t SqliteOwnedGuildMembershipRepository::officer_display_role(
    const Leader& leader,const GuildRosterMember& member,const OfficerHistory& history) {
    const auto& gov=leader.governance;const auto id=leader.membership.guild_id;
    require(gov.guild_id==id && member.membership_revision,"Officer display requires accepted member");
    require(std::find(leader.roster.begin(),leader.roster.end(),member)!=leader.roster.end(),
        "Officer display not in complete accepted roster");
    const bool founder=member.account_id==gov.owner_account && member.character_id==gov.owner_character;
    std::uint8_t role=founder?3:1;bool matched=false;
    for(const auto& row:history) {
        require(row.guild_id==id && row.revision<=leader.membership.guild_revision,
            "Officer history guild/generation conflict");
        if(row.character_id!=member.character_id || row.membership_revision!=member.membership_revision)continue;
        require(!matched && !founder && row.account_id==member.account_id && row.account_slot==member.slot,
            "Officer current join ownership/founder conflict");matched=true;role=row.role;
    }
    return role;
}
SqliteOwnedGuildMembershipRepository::OfficerChanged
SqliteOwnedGuildMembershipRepository::change_officer(
    const Leader& founder,const std::vector<Application>& expected_applications,const OfficerHistory& history,
    const Identity& target,const StoredGuildMembership& membership,OfficerAction action,const Proof& proof) {
    proof_valid(proof);positive(membership.guild_id);positive(membership.guild_revision);positive(membership.membership_revision);
    positive(target.account_id);positive(target.character_id);
    require(!target.membership_revision && (action==OfficerAction::Appoint || action==OfficerAction::RemoveOffice),
        "Invalid officer action identity");
    const auto id=membership.guild_id;
    const auto key="guild_id="+std::to_string(id)+" AND character_id="+std::to_string(target.character_id)+
        " AND membership_revision="+std::to_string(membership.membership_revision);
    sqlite_detail::Transaction tx(db_);
    const Exclusions allowed{{"owned_guilds","id<>"+std::to_string(id)},
        {"owned_guild_officers_0082","NOT("+key+")"}};
    const Exclusions none;const auto preserved=guard(db_,allowed);const auto g0=guard(db_,none);
    const auto guild_sql="SELECT * FROM owned_guilds WHERE id="+std::to_string(id);
    const auto row_sql="SELECT * FROM owned_guild_officers_0082 WHERE "+key;
    const auto guild_fields=officer_retained_fields(db_,guild_sql,{"revision"});
    const auto rank_fields=officer_retained_fields(db_,row_sql,{"role","revision"});
    const std::set<std::string> known_rank_columns{"guild_id","account_id","character_id","account_slot",
        "membership_revision","revision","role","origin","design_id","source_sha256"};
    const auto new_opaque_defaults=rank_fields.empty()?officer_new_opaque_defaults(db_,known_rank_columns):
        std::vector<std::uint8_t>{};
    proof.before_write();unchanged(db_,g0,none); // Callback cannot mutate even an allowed row.
    const auto& owner=founder.identity;
    require(!owner.membership_revision && leader(owner.account_id,owner.character_id)==founder &&
        founder.governance.owner_account==owner.account_id && founder.governance.owner_character==owner.character_id &&
        founder.membership.guild_id==id && founder.membership.guild_revision==membership.guild_revision &&
        founder.membership.name_utf8==membership.name_utf8,"Officer original founder/full roster conflict");
    require(identity(target.account_id,target.character_id)==target && target.character_id!=owner.character_id &&
        !pending(target.account_id,target.character_id),"Officer accepted target identity conflict");
    nonbattle(db_,target.character_id);SqliteGuildRepository memberships(db_);
    require(memberships.load(target.account_id,target.character_id)==std::optional{membership} &&
        applications(id)==expected_applications && officer_history(id)==history &&
        founder.roster.size()+expected_applications.size()<=50,"Officer full membership/application/rank snapshot conflict");
    auto audience=founder.roster;std::set<std::uint64_t> characters,request_ids;
    std::set<std::pair<std::uint64_t,std::uint8_t>> account_slots;
    for(const auto& member:founder.roster)require(!pending(member.account_id,member.character_id),
        "Officer accepted member has pending application");
    for(const auto& request:expected_applications) {
        require(request.target.id==id && request.target.name_utf8==membership.name_utf8 &&
            request.target.revision<=membership.guild_revision && !request.applicant.membership_revision &&
            request_ids.insert(request.id).second &&
            !memberships.load(request.applicant.account_id,request.applicant.character_id),
            "Officer pending/member audience conflict");audience.push_back(request.applicant);
    }
    for(const auto& member:audience)require(characters.insert(member.character_id).second &&
        account_slots.emplace(member.account_id,member.slot).second,"Officer ambiguous audience identity");
    unambiguous(audience);
    const auto at=std::find_if(founder.roster.begin(),founder.roster.end(),[&](const auto& r){return r.character_id==target.character_id;});
    require(at!=founder.roster.end() && at->membership_revision==membership.membership_revision,
        "Officer target join absent");auto identity_row=*at;identity_row.membership_revision=0;
    require(identity_row==target,"Officer full target profile/role/name conflict");
    for(const auto& member:founder.roster)(void)officer_display_role(founder,member,history);
    const auto previous_role=officer_display_role(founder,*at,history);
    require(previous_role==(action==OfficerAction::Appoint?1:2),"Officer exact role transition conflict");
    const Guild before{id,membership.guild_revision,membership.name_utf8};const auto revision=next_revision(db_);
    const Guild after{id,revision,before.name_utf8};bump(db_,before,revision);
    const auto to_role=static_cast<std::uint8_t>(action==OfficerAction::Appoint?2:1);
    auto wanted_history=history;
    auto row=std::find_if(wanted_history.begin(),wanted_history.end(),[&](const auto& r){
        return r.character_id==target.character_id && r.membership_revision==membership.membership_revision;});
    if(row==wanted_history.end()) {
        require(action==OfficerAction::Appoint && rank_fields.empty(),"Officer missing remove-office lease");
        sqlite_detail::Statement q(db_,"INSERT INTO owned_guild_officers_0082(guild_id,account_id,character_id,account_slot,"
            "membership_revision,revision,role,origin,design_id,source_sha256) VALUES(?,?,?,?,?,?,2,'CUSTOM_DESIGNED','CUSTOM-0082',?)");
        q.bind_id(1,id);q.bind_id(2,target.account_id);q.bind_id(3,target.character_id);q.bind(4,target.slot);
        q.bind_id(5,membership.membership_revision);q.bind_id(6,revision);q.bind(7,std::string(source));q.done();
        wanted_history.push_back({id,target.account_id,target.character_id,membership.membership_revision,revision,target.slot,2});
    } else {
        sqlite_detail::Statement q(db_,"UPDATE owned_guild_officers_0082 SET role=?,revision=? WHERE guild_id=? "
            "AND account_id=? AND character_id=? AND account_slot=? AND membership_revision=? AND revision=? AND role=? "
            "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0082' AND source_sha256=?");
        q.bind(1,to_role);q.bind_id(2,revision);q.bind_id(3,id);q.bind_id(4,target.account_id);q.bind_id(5,target.character_id);
        q.bind(6,target.slot);q.bind_id(7,membership.membership_revision);q.bind_id(8,row->revision);q.bind(9,previous_role);
        q.bind(10,std::string(source));q.done();row->role=to_role;row->revision=revision;
    }
    require(sqlite3_changes(db_)==1,"Officer exact rank row CAS failed");
    std::sort(wanted_history.begin(),wanted_history.end(),[](const auto& a,const auto& b){
        return std::pair(a.character_id,a.membership_revision)<std::pair(b.character_id,b.membership_revision);});
    auto wanted=founder;wanted.membership.guild_revision=revision;
    const auto verify=[&] {
        require(guild(id)==after && leader(owner.account_id,owner.character_id)==wanted &&
            applications(id)==expected_applications && officer_history(id)==wanted_history &&
            identity(target.account_id,target.character_id)==target &&
            memberships.load(target.account_id,target.character_id)==std::optional{
                StoredGuildMembership{id,before.name_utf8,revision,membership.membership_revision}} &&
            officer_retained_fields(db_,guild_sql,{"revision"})==guild_fields,
            "Officer readback/generation/retained guild conflict");
        if(!rank_fields.empty())require(officer_retained_fields(db_,row_sql,{"role","revision"})==rank_fields,
            "Officer opaque retained rank fields changed");
        else require(officer_retained_fields(db_,row_sql,known_rank_columns)==new_opaque_defaults,
            "Officer newly inserted opaque fields differ from literal defaults");
        nonbattle(db_,target.character_id);unchanged(db_,preserved,allowed);
    };
    verify();const auto g1=guard(db_,none);proof.after_write();unchanged(db_,g1,none);verify();
    OfficerChanged result{after,wanted,wanted_history};tx.commit();return result;
}
SqliteOwnedGuildMembershipRepository::Left SqliteOwnedGuildMembershipRepository::officer_leave(
    const Identity& self,const StoredGuildMembership& membership,const Leader& founder,
    const std::vector<Application>& applications,const OfficerHistory& history,const Proof& proof) {
    proof_valid(proof);const auto id=membership.guild_id;positive(id);
    const auto exact_rank=[&] {
        require(officer_history(id)==history,"Officer leave complete rank history conflict");
        const auto at=std::find_if(founder.roster.begin(),founder.roster.end(),[&](const auto& r){return r.character_id==self.character_id;});
        require(at!=founder.roster.end() && at->account_id==self.account_id &&
            at->membership_revision==membership.membership_revision &&
            officer_display_role(founder,*at,history)==2,"Officer leave exact self role2 conflict");
    };
    // Runs inside frozen member_leave BEGIN IMMEDIATE. Its own exact identity,
    // complete roster/application CAS and foreign-table guard remain unchanged.
    // No founder nonbattle restriction is added to the frozen selfleave policy.
    const auto before=[&] {
        exact_rank();const Exclusions none;const auto g0=guard(db_,none);
        proof.before_write();unchanged(db_,g0,none);exact_rank();
    };
    const auto after=[&] {
        // Membership is gone: do NOT require current accepted self SQL state.
        require(officer_history(id)==history,"Officer leave changed retained history");
        const Exclusions none;const auto g1=guard(db_,none);
        proof.after_write();unchanged(db_,g1,none);
        require(officer_history(id)==history,"Officer leave callback changed history");
    };
    return member_leave(self,membership,founder,applications,{before,after});
}

}
