#include "db/NativeMultiMessageCatalog.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <array>
#include <string_view>
#include <vector>
namespace god2 {
namespace {
struct ReadTransaction {
    sqlite3* db;
    bool committed=false;
    explicit ReadTransaction(sqlite3* value):db(value){sqlite_detail::execute(db,"BEGIN");}
    ~ReadTransaction(){if(!committed)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void commit(){sqlite_detail::execute(db,"COMMIT");committed=true;}
};
struct Source {const char* path;const char* compressed;const char* decoded;int count,lines,size;};
const Source sources[]={
{"Data2/Patch/Comm/MultiMessage01.csvZ","0d573b607f477c0da53c2efa7aeb1881bcb1d38941cf36472cd9a506d13f9985","e5234537a68f63df15d6279a232395a130f2c2cfddd3589b2a66372d2da4b4b9",1000,3533,259585},
{"Data2/Patch/Comm/MultiMessage02.csvZ","441b2828b6edccdb36098c3aba9d6e631ae351d82e685969d34758b67fe6c10f","72c1840846e3925b43a62552c354308ecbc83a5d0e1e4121826bc59303d99003",1000,3782,247509},
{"Data2/Patch/Comm/MultiMessage03.csvZ","e0551afec2108f478f27f2364bd15bd8d7ff999c8f12a087b320d06d23659e4d","eb6551f327caba720f71bcee78dda84a796b3c1b615e0287651d5e6cae6af58c",995,4485,171585},
};
struct Row {int line,offset;const char* sha;const char* raw;};
const Row rows[]={
{1529,105276,"2728ebb1259583d8e23cca33d1d8a7a9b0d79907ccfc7a4c9d2263e078d52e08","313433342c372cabdca66ea141c0a9a46ca569b1d0a141a759b54da741a84da977ad6ea662a550acc9b669a6e6add7bd6da141b44ec5fda5bba4d1b44ca5fdb1d0bec9a741a440a8c7b0f2a5bbaabaaabec3d1a761a149"},
{1530,105365,"77f03d7495d8ae37599d0f6001e0bfa4159cbee8167879b03d06eaa33d85bc69","2c312ca7daa477b867aabebee5bae7a4a4b6f8a7aea446a149a7daad6eb669a6e6a455a440b6a5ac71aabaadd7bd6da143"},
{1531,105416,"a032e8f6f67d9ae62a8c7834dec3cabb7c547fa41f77217ce7723d9ae2be3e99","2c322cb7c6b9aba55cafe0"},
{1532,105429,"f264d30139eaf6c4e7c9c059325945ef01576ab4cf3b7e67084a2408790adc58","2c332ca4b6adb1b7a7ad7a"},
{1533,105442,"b89cd3ec6dc3e635a8a0ebcd46391434cfb8920e225e9a1d59f30ee4a1e6b422","2c342cb652bde6bba1a9fa"},
{1534,105455,"484319f84af9a3dcdbc3324299cdac804b4a74cb5a1e00a8df13e5ade5e1fc4a","2c352ca5e6a9f6b8d1b462"},
{1535,105468,"543c706532b798d54341b891a4fd4879f05558ab03fd8edabea557f9fc2a2505","2c362cb2d5b6a4c4c0bac3"},
{1536,105481,"8d0a1f1158347e5afc840808d6ae980c468945cc8cdb6fd83e11a225f1a02731","2c372ca4c9afc5c249bcc6b074b86d"},
};
std::vector<std::uint8_t> unhex(std::string_view hex) {
    std::vector<std::uint8_t> value;
    const auto digit=[](char c){return c<='9'?c-'0':c-'a'+10;};
    for(std::size_t i=0;i<hex.size();i+=2)value.push_back(static_cast<std::uint8_t>((digit(hex[i])<<4)|digit(hex[i+1])));
    return value;
}
}
bool NativeMultiMessageCatalog::populated() const {
    if(!db_)throw DatabaseError("Null MultiMessage connection");
    sqlite_detail::Statement counts(db_,"SELECT (SELECT count(*) FROM native_multi_message_sources)+(SELECT count(*) FROM native_multi_messages)+(SELECT count(*) FROM native_multi_message_rows)");
    if(!counts.row())throw DatabaseError("MultiMessage source counts unavailable");
    return counts.integer(0)!=0;
}
std::uint32_t NativeMultiMessageCatalog::knowledge_menu_count() const {
    using sqlite_detail::Statement;
    if(!db_)throw DatabaseError("Null MultiMessage connection");
    ReadTransaction transaction(db_);
    Statement counts(db_,"SELECT (SELECT count(*) FROM native_multi_message_sources),(SELECT count(*) FROM native_multi_messages),(SELECT count(*) FROM native_multi_message_rows)");
    if(!counts.row() || counts.integer(0)!=3 || counts.integer(1)!=2995 || counts.integer(2)!=11794)
        throw DatabaseError("Incomplete MultiMessage source catalog");
    for(const auto& expected:sources) {
        Statement source(db_,"SELECT source_sha256,decoded_sha256,encoding,record_count,line_count,decoded_size,authority FROM native_multi_message_sources WHERE source_file=?");
        source.bind(1,std::string(expected.path));
        if(!source.row() || source.text(0)!=expected.compressed || source.text(1)!=expected.decoded || source.text(2)!="CP950" || source.integer(3)!=expected.count || source.integer(4)!=expected.lines || source.integer(5)!=expected.size || source.text(6)!="SOURCE_DISPLAY_ONLY")
            throw DatabaseError("MultiMessage source provenance mismatch");
    }
    Statement malformed(db_,"SELECT m.message_key FROM native_multi_messages m LEFT JOIN native_multi_message_rows r ON m.message_key=r.message_key GROUP BY m.message_key HAVING count(r.ordinal)!=m.option_count+1 OR min(r.ordinal)!=0 OR max(r.ordinal)!=m.option_count LIMIT 1");
    if(malformed.row())throw DatabaseError("MultiMessage option group incomplete");
    Statement definition(db_,"SELECT source_file,option_count,authority FROM native_multi_messages WHERE message_key=1434");
    if(!definition.row() || definition.text(0)!="Data2/Patch/Comm/MultiMessage02.csvZ" || definition.integer(1)!=7 || definition.text(2)!="SOURCE_DISPLAY_ONLY")
        throw DatabaseError("Knowledge menu namespace mismatch");
    Statement text(db_,"SELECT ordinal,source_line,decoded_offset,record_sha256,raw_record,text_bytes FROM native_multi_message_rows WHERE message_key=1434 ORDER BY ordinal");
    for(unsigned i=0;i<8;++i) {
        const auto expected=unhex(rows[i].raw);
        if(!text.row() || text.integer(0)!=i || text.integer(1)!=rows[i].line || text.integer(2)!=rows[i].offset || text.text(3)!=rows[i].sha)
            throw DatabaseError("Knowledge menu row provenance mismatch");
        const auto raw=text.blob(4,1,65535);
        if(raw.size()!=expected.size() || !std::equal(raw.begin(),raw.end(),expected.begin()))throw DatabaseError("Knowledge menu source bytes changed");
        auto content=std::find(expected.begin(),expected.end(),',');
        content=std::find(content+1,expected.end(),',')+1;
        const auto bytes=text.blob(5,1,65535);
        if(bytes.size()!=static_cast<std::size_t>(expected.end()-content) || !std::equal(bytes.begin(),bytes.end(),content) || std::find(bytes.begin(),bytes.end(),'%')!=bytes.end())throw DatabaseError("Knowledge menu text mismatch or formatting unsupported");
    }
    if(text.row())throw DatabaseError("Extra knowledge menu row");
    transaction.commit();return 2995;
}
}
