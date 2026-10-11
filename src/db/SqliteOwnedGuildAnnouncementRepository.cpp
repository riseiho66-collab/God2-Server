#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>
#include <map>

namespace god2 {
namespace announcement_detail {
constexpr auto source="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool value,const char* message) {if(!value)throw DatabaseError(message);}
void positive(std::uint64_t value) {require(value && value<=maximum,"Invalid guild announcement identity/revision");}
void text_valid(const std::string& text) {
    // CUSTOM-0078 cross-language publication safety. Native logical1044 permits
    // 1040 encoded text bytes. Preserve spaces and percent literally; native
    // getter adds no CRLF. Never silently replace unrepresentable characters.
    require(text.size()<=4160 && std::none_of(text.begin(),text.end(),[](unsigned char c){return c<32 || c==127;}),
            "Unsafe guild announcement text");
    try {
        for(const bool cn:{false,true}) {
            const auto bytes=LegacyChineseCodec::encode(text,cn);
            require(bytes.size()<=1040 && bytes.find('\0')==std::string::npos && LegacyChineseCodec::decode(bytes,cn)==text,
                    "Guild announcement is not lossless/bounded in both languages");
        }
    }catch(const std::exception&){throw DatabaseError("Unrepresentable guild announcement text");}
}

// Deliberate independent copy of frozen membership2576 full typed-row guard.
// No old helper is altered. Capacity hints affect allocation only, never scans.
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

// RETURNING * observes the first-insert defaults before AFTER triggers. On an
// existing row the immutable fields come from G0. This protects installation
// extensions without enumerating or overwriting their unknown columns.
std::vector<std::uint8_t> retained(sqlite3_stmt* statement) {
    std::vector<std::uint8_t> result;unsigned mutable_columns=0;
    for(int c=0;c<sqlite3_column_count(statement);++c) {
        const std::string name=sqlite3_column_name(statement,c);
        if(name=="text_utf8" || name=="revision"){++mutable_columns;continue;}
        const auto type=sqlite3_column_type(statement,c);result.push_back(static_cast<std::uint8_t>(type));
        if(type==SQLITE_INTEGER)append_number(result,static_cast<std::uint64_t>(sqlite3_column_int64(statement,c)));
        else if(type==SQLITE_FLOAT)append_number(result,std::bit_cast<std::uint64_t>(sqlite3_column_double(statement,c)));
        else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
            const auto size=sqlite3_column_bytes(statement,c);
            const auto* bytes=static_cast<const std::uint8_t*>(sqlite3_column_blob(statement,c));
            require(size>=0 && (!size || bytes),"Cannot preserve announcement retained fields");
            append_number(result,static_cast<std::uint64_t>(size));if(size)result.insert(result.end(),bytes,bytes+size);
        }
    }
    require(mutable_columns==2,"Ambiguous announcement retained fields");return result;
}
std::optional<std::vector<std::uint8_t>> retained(sqlite3* db,std::uint64_t guild) {
    sqlite3_stmt* statement=nullptr;
    sqlite_detail::check(db,sqlite3_prepare_v2(db,"SELECT * FROM owned_guild_announcements_0078 WHERE guild_id=?",-1,&statement,nullptr));
    struct Finalize{sqlite3_stmt* statement;~Finalize(){sqlite3_finalize(statement);}} finalize{statement};
    sqlite_detail::check(db,sqlite3_bind_int64(statement,1,static_cast<sqlite3_int64>(guild)));
    const auto rc=sqlite3_step(statement);if(rc==SQLITE_DONE)return {};
    require(rc==SQLITE_ROW,"Cannot read announcement retained fields");const auto fields=retained(statement);
    require(sqlite3_step(statement)==SQLITE_DONE,"Ambiguous announcement retained row");return fields;
}
}

SqliteOwnedGuildAnnouncementRepository::SqliteOwnedGuildAnnouncementRepository(sqlite3* db):db_(db) {
    announcement_detail::require(db_!=nullptr,"Null guild announcement connection");
}
std::string SqliteOwnedGuildAnnouncementRepository::schema() {
    return R"SQL(
-- CUSTOM-0078 announcement policy candidate; separate explicit migration only.
CREATE TABLE owned_guild_announcements_0078 (
 guild_id INTEGER PRIMARY KEY REFERENCES owned_guilds(id) CHECK(typeof(guild_id)='integer' AND guild_id>0),
 text_utf8 TEXT NOT NULL CHECK(typeof(text_utf8)='text' AND length(CAST(text_utf8 AS BLOB))<=4160 AND instr(text_utf8,char(0))=0),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0078'),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
);
)SQL";
}
SqliteOwnedGuildAnnouncementRepository::Snapshot SqliteOwnedGuildAnnouncementRepository::load(std::uint64_t guild_id) {
    announcement_detail::positive(guild_id);
    Membership members(db_);(void)members.governance(guild_id);
    sqlite_detail::Statement q(db_,"SELECT guild_id,text_utf8,revision,origin,design_id,source_sha256 FROM owned_guild_announcements_0078 WHERE guild_id=?");
    q.bind_id(1,guild_id);Snapshot result{guild_id,{}};if(!q.row())return result;
    announcement_detail::require(q.number<std::uint64_t>(0)==guild_id && q.text(3)=="CUSTOM_DESIGNED" &&
        q.text(4)=="CUSTOM-0078" && q.text(5)==announcement_detail::source,"Guild announcement provenance mismatch");
    Value value{q.text(1),q.number<std::uint64_t>(2)};
    announcement_detail::positive(value.revision);announcement_detail::text_valid(value.text_utf8);
    result.value=value;announcement_detail::require(!q.row(),"Ambiguous guild announcement");return result;
}
SqliteOwnedGuildAnnouncementRepository::Snapshot SqliteOwnedGuildAnnouncementRepository::save(
    const Membership::Leader& expected_leader,const Snapshot& expected,const std::string& text,
    const Membership::Proof& proof) {
    namespace ad=announcement_detail;
    ad::require(bool(proof.before_write) && bool(proof.after_write),"Guild announcement requires paired immutable world proof");
    ad::positive(expected.guild_id);ad::text_valid(text);
    ad::require(expected.guild_id==expected_leader.governance.guild_id && expected.guild_id==expected_leader.membership.guild_id,
                "Guild announcement target/leader lease conflict");
    if(expected.value){ad::positive(expected.value->revision);ad::text_valid(expected.value->text_utf8);}
    ad::require(!expected.value || expected.value->revision<ad::maximum,"Guild announcement revision exhausted");
    sqlite_detail::Transaction transaction(db_);
    Membership members(db_);const auto& owner=expected_leader.identity;
    const ad::Exclusions allowed{{"owned_guild_announcements_0078","guild_id<>"+std::to_string(expected.guild_id)}};
    const auto preserved=ad::guard(db_,allowed); // G0: all other typed rows and full schema.
    auto retained_fields=ad::retained(db_,expected.guild_id);
    proof.before_write();
    ad::require(members.leader(owner.account_id,owner.character_id)==expected_leader,
                "Guild announcement founder/governance/full-roster lease conflict");
    ad::require(load(expected.guild_id)==expected,"Guild announcement version/text snapshot conflict");
    const auto revision=expected.value?expected.value->revision+1:1;
    sqlite3_stmt* statement=nullptr;
    const char* sql=expected.value?
        "UPDATE owned_guild_announcements_0078 SET text_utf8=?,revision=? WHERE guild_id=? AND revision=? AND text_utf8=? "
        "AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0078' AND source_sha256=? RETURNING *":
        "INSERT INTO owned_guild_announcements_0078(guild_id,text_utf8,revision,origin,design_id,source_sha256) "
        "VALUES(?,?,1,'CUSTOM_DESIGNED','CUSTOM-0078',?) RETURNING *";
    sqlite_detail::check(db_,sqlite3_prepare_v2(db_,sql,-1,&statement,nullptr));
    struct Finalize{sqlite3_stmt* statement;~Finalize(){sqlite3_finalize(statement);}} finalize{statement};
    const auto bind_text=[&](int at,const std::string& s) {
        sqlite_detail::check(db_,sqlite3_bind_text(statement,at,s.data(),static_cast<int>(s.size()),SQLITE_TRANSIENT));
    };
    const auto bind_id=[&](int at,std::uint64_t id) {
        sqlite_detail::check(db_,sqlite3_bind_int64(statement,at,static_cast<sqlite3_int64>(id)));
    };
    if(expected.value) {
        bind_text(1,text);bind_id(2,revision);bind_id(3,expected.guild_id);bind_id(4,expected.value->revision);
        bind_text(5,expected.value->text_utf8);bind_text(6,ad::source);
    }else {bind_id(1,expected.guild_id);bind_text(2,text);bind_text(3,ad::source);}
    ad::require(sqlite3_step(statement)==SQLITE_ROW,"Guild announcement CAS returned no row");
    const auto returned_fields=ad::retained(statement);
    ad::require(sqlite3_step(statement)==SQLITE_DONE && sqlite3_changes(db_)==1,"Guild announcement CAS failed");
    if(!retained_fields)retained_fields=returned_fields;
    ad::require(returned_fields==*retained_fields,"Guild announcement CAS changed immutable row fields");
    const Snapshot wanted{expected.guild_id,Value{text,revision}};
    const auto verify=[&] {
        ad::require(members.leader(owner.account_id,owner.character_id)==expected_leader && load(expected.guild_id)==wanted,
                    "Guild announcement complete authority/readback conflict");
        ad::require(ad::retained(db_,expected.guild_id)==retained_fields,"Guild announcement changed immutable extension fields");
        ad::unchanged(db_,preserved,allowed); // G1, then G2 after paired world proof.
    };
    verify();proof.after_write();verify();transaction.commit();return wanted;
}
}
