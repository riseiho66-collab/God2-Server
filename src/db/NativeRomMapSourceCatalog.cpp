#include "db/NativeRomMapSourceCatalog.h"
#include "db/SqliteSupport.h"
#include <array>
#include <string_view>
#include <utility>

namespace god2 {
namespace {
std::vector<std::uint8_t> hex(std::string_view text) {
    auto digit=[](char c)->unsigned {
        if(c>='0' && c<='9')return static_cast<unsigned>(c-'0');
        if(c>='a' && c<='f')return static_cast<unsigned>(c-'a'+10);
        throw DatabaseError("Invalid pinned RomMaps source hex");
    };
    if(text.size()%2)throw DatabaseError("Odd pinned RomMaps source hex");
    std::vector<std::uint8_t> out;out.reserve(text.size()/2);
    for(std::size_t i=0;i<text.size();i+=2)
        out.push_back(static_cast<std::uint8_t>((digit(text[i])<<4)|digit(text[i+1])));
    return out;
}
constexpr char header_record_sha256[]="afe2472b3f170f586df7e834f6d1238acb2b5f8c4d724ad32e7844a63ce2f678";
constexpr char source_window_sha256[]="1a5c850ba16876b8c28c67d2b1f36c7bcf0670643364f29edc029c6b9cc214e2";
// The original header includes its CRLF; source rows below are CRLF-stripped
// exact byte bodies with independently retained physical offsets and body hashes.
const auto raw_header=hex("526f6d4d6170732c35372c2cc163c5e92cc2b2c5e90d0a");
const std::array<NativeRomMapSourceRecord,57> pinned{{
    {0,0,58,4397,"e0fd5b4e1889116040f363cf662048e0dae026d57d23c375393e3308508ccd65",hex("302c312c363030302c64617461325c49746d496d675c57504e30312e726f6d2c64617461325c49746d496d675c57504e30312e726f6d")},
    {1,1,59,4453,"7918224d5e7f8ee62a920114a591c5f52786f471bb3deab71b6fefef9e12e891",hex("312c363030312c31303030302c64617461325c49746d496d675c57504e30322e726f6d2c64617461325c49746d496d675c57504e30322e726f6d")},
    {2,2,60,4513,"3a067c82a38ab5b73a79b89d2a9c82ffe29d921936a966a6e4cbbfa94fcaf9b9",hex("322c31303030312c31353030302c64617461325c49746d496d675c45515530312e726f6d2c64617461325c49746d496d675c45515530312e726f6d")},
    {3,3,61,4574,"a75a29f79a9850237500eb7d82940929fe07a829a2e9d3751fcab5bae2494204",hex("332c31353030312c32303030302c64617461325c49746d496d675c45515530322e726f6d2c64617461325c49746d496d675c45515530322e726f6d")},
    {4,4,62,4635,"611ff0661f72b8a7feff047a95764079a37286fa50da078a07629dd5a2d77fd7",hex("342c32303030312c32313030302c64617461325c49746d496d675c534b4230312e726f6d2c64617461325c49746d496d675c534b4230312e726f6d")},
    {5,5,63,4696,"6bfcd1007c669033712581aed6010d36c83723d00a4460b6d5b2598d4c63ffe9",hex("352c32313030312c32323030302c64617461325c49746d496d675c534b4930312e726f6d2c64617461325c49746d496d675c534b4930312e726f6d")},
    {6,6,64,4757,"9361c5396458ee8c5d35e7a53031e3b430d9605a22edceb918628a6a50cd43e7",hex("362c32323030312c32333030302c64617461325c49746d496d675c534b4930322e726f6d2c64617461325c49746d496d675c534b4930322e726f6d")},
    {7,7,65,4818,"18fd9e3b98e54a676ea586388904848cb40f610bd02fec52d963229c6468e2e9",hex("372c32333030312c32343030302c64617461325c49746d496d675c534b4930332e726f6d2c64617461325c49746d496d675c534b4930332e726f6d")},
    {8,8,66,4879,"372f61a91820f2ba1d30855e5c38d3af76d22fe19a825f9248fe3326279dd868",hex("382c32343030312c32353030302c64617461325c49746d496d675c534b4930342e726f6d2c64617461325c49746d496d675c534b4930342e726f6d")},
    {9,9,67,4940,"32b8dad4414418a4b7d5d0ad2c54b60362376b856ef95195810d248f79fe2b56",hex("392c32353030312c32353230302c64617461325c49746d496d675c45514330312e726f6d2c64617461325c49746d496d675c45514330312e726f6d")},
    {10,10,68,5001,"425a5a53690db07c74d667dea27733c90638c608cef3de3d77c65083285e0899",hex("31302c32353230312c32353430302c64617461325c49746d496d675c45514330322e726f6d2c64617461325c49746d496d675c45514330322e726f6d")},
    {11,11,69,5063,"b18506fe1fb58e259f3bbaee562134463cbdf8ae438993ba2e6f98d4ecdd532a",hex("31312c32353430312c32353630302c64617461325c49746d496d675c45514330332e726f6d2c64617461325c49746d496d675c45514330332e726f6d")},
    {12,12,70,5125,"e7313e69aacb26f84b7131634f5cc3d8bbf32822baea13e0643c42c71ea87b3c",hex("31322c32353630312c32353830302c64617461325c49746d496d675c45514330342e726f6d2c64617461325c49746d496d675c45514330342e726f6d")},
    {13,13,71,5187,"6f533a767bb1b259a6e3a807a1059a0d575e4218f8ab2de594ff8249c9f1486d",hex("31332c32353830312c32363030302c64617461325c49746d496d675c45514330352e726f6d2c64617461325c49746d496d675c45514330352e726f6d")},
    {14,14,72,5249,"0098555777d389e830566e7790a71bf11d6dc4a358b1c3b342aaea01c42893f7",hex("31342c32363030312c32363230302c64617461325c49746d496d675c45514330362e726f6d2c64617461325c49746d496d675c45514330362e726f6d")},
    {15,15,73,5311,"69c12c88d84d23cc7aa7052fd67bd67fc6c0c8ec8f745cf6a1d7ea0550b0da70",hex("31352c32363230312c32363430302c64617461325c49746d496d675c45514330372e726f6d2c64617461325c49746d496d675c45514330372e726f6d")},
    {16,16,74,5373,"fd66c52ca443d669ed4e4c7cbd53b16591238430352fcd978427bf3e9922df5d",hex("31362c32363430312c32363630302c64617461325c49746d496d675c45514330382e726f6d2c64617461325c49746d496d675c45514330382e726f6d")},
    {17,17,75,5435,"85a1710641939b642a77e6b03de936d2d4ea42bbee2979c22cb8c0f0cc8f2679",hex("31372c32373030312c32373230302c64617461325c49746d496d675c41534230312e726f6d2c64617461325c49746d496d675c41534230312e726f6d")},
    {18,18,76,5497,"9d96c4af8ed0e0bfac73f2ab319a093f2a239c71491cee5cfb538b7bec641934",hex("31382c32383030312c32383230302c64617461325c49746d496d675c42454230312e726f6d2c64617461325c49746d496d675c42454230312e726f6d")},
    {19,19,77,5559,"ff3a294912610b0647b39e1af026032f55aff6009e48fb4406fdf563e53f1030",hex("31392c32383230312c32383430302c64617461325c49746d496d675c42454230322e726f6d2c64617461325c49746d496d675c42454230322e726f6d")},
    {20,20,78,5621,"8746b46fc9089022628bdb4b6d56c22875e5ebaa04c3bebaa247f537dd402ec4",hex("32302c32393030312c32393130302c64617461325c49746d496d675c45474730312e726f6d2c64617461325c49746d496d675c45474730312e726f6d")},
    {21,21,79,5683,"4fe35288202c2fa228c549b2df7f94a0d630129e227372090ae6679e340cb904",hex("32312c32393130312c32393230302c64617461325c49746d496d675c53505030312e726f6d2c64617461325c49746d496d675c53505030312e726f6d")},
    {22,22,80,5745,"38887b20cebfdc8717e205749e556dba7666a8915103f601c6c8ef5d446d8445",hex("32322c32393230312c32393330302c64617461325c49746d496d675c43424630312e726f6d2c64617461325c49746d496d675c43424630312e726f6d")},
    {23,23,81,5807,"a207f790267ab5d6db12031cf16fbf54bbee2afb9e90d0b622369f5646fae0df",hex("32332c32393330312c32393430302c64617461325c49746d496d675c4e4d5030312e726f6d2c64617461325c49746d496d675c4e4d5030312e726f6d")},
    {24,24,82,5869,"6b7e26fc3a46953d47217542bbb20ab4a045f2e2ad3b7b3f57d1da8ff828b2c2",hex("32342c33303030312c33353030302c64617461325c49746d496d675c50455430312e726f6d2c64617461325c49746d496d675c50455430312e726f6d")},
    {25,25,83,5931,"204e2328cce9840d1ac1afa9e6bba285d4b18749402b7f305fea00a82c30bd59",hex("32352c33353030312c33363230302c64617461325c49746d496d675c4d454430312e726f6d2c64617461325c49746d496d675c4d454430312e726f6d")},
    {26,26,84,5993,"2116f221213e0f5ca38aaad0ac96b0783c952c058cb6895d3fa18de405e4a1a5",hex("32362c34303030312c34303139392c64617461325c49746d496d675c4d415430322e726f6d2c64617461325c49746d496d675c4d415430322e726f6d")},
    {27,27,85,6055,"b5c15c9ffefac1ad68e65bc5e914b565813954ff1c51c1edd8c68a80b7e43eff",hex("32372c34303230302c34303430302c64617461325c49746d496d675c4d415430312e726f6d2c64617461325c49746d496d675c4d415430312e726f6d")},
    {28,28,86,6117,"66a6dcd962699a8ba1dfdc2b292684470cf9b8bec3a300f682b45e39db22a6c0",hex("32382c34313030312c34313230302c64617461325c49746d496d675c4d415430332e726f6d2c64617461325c49746d496d675c4d415430332e726f6d")},
    {29,29,87,6179,"0e8c92715e1acc8eed7c675baaf720f41b7d19b077558661daefa82ded3e0c97",hex("32392c34313230312c34313430302c64617461325c49746d496d675c4d415430372e726f6d2c64617461325c49746d496d675c4d415430372e726f6d")},
    {30,30,88,6241,"80845c26e1ee38ca05c79cdba0faab97e7cb00a9c1626dc9ad88292f7cc8ebf1",hex("33302c34313530312c34313630302c64617461325c49746d496d675c4d415431322e726f6d2c64617461325c49746d496d675c4d415431322e726f6d")},
    {31,31,89,6303,"5321e3fc78b6e2d8d79fe4a19ba4b6a74fbe08e0e5bcef977e0a57d4016cf7d4",hex("33312c34313630312c34313735302c64617461325c49746d496d675c4d415431332e726f6d2c64617461325c49746d496d675c4d415431332e726f6d")},
    {32,32,90,6365,"52cb7ff4b92e82f51222c3b63694647224c244198473a4fe42f28d501a474ebd",hex("33322c34323030312c34323230302c64617461325c49746d496d675c4b495430312e726f6d2c64617461325c49746d496d675c4b495430312e726f6d")},
    {33,33,91,6427,"baf1d91d414e91d39fa1ebae9f151f71a6a9ba070720c808e599d7a77118dbe0",hex("33332c34333030312c34353030302c64617461325c49746d496d675c4b495430322e726f6d2c64617461325c49746d496d675c4b495430322e726f6d")},
    {34,34,92,6489,"a297794dee1a476526d44dc62d322e744802ca157911c4e8e12491c1a52a435a",hex("33342c34353030312c34353530302c64617461325c49746d496d675c4e53542e726f6d2c64617461325c49746d496d675c4e53542e726f6d")},
    {35,35,93,6547,"473052b03224d308c53610b044d6922952b933cb59f0443d9db3b1c2b5f1951d",hex("33352c35303030312c35303230302c64617461325c49746d496d675c4d495330312e726f6d2c64617461325c49746d496d675c4d495330312e726f6d")},
    {36,36,94,6609,"a83c95443c71a6fa163647d6e837623ab9b0e70457d65524a57a26e06e013188",hex("33362c35303230312c35303430302c64617461325c49746d496d675c4d495330322e726f6d2c64617461325c49746d496d675c4d495330322e726f6d")},
    {37,37,95,6671,"f39378b95ab71653987432103df17d966f314358ae2f1ce4f171b0b2bf16f1be",hex("33372c35313030312c35313230302c64617461325c49746d496d675c4d495330332e726f6d2c64617461325c49746d496d675c4d495330332e726f6d")},
    {38,38,96,6733,"2c944642380374f8ecdbf7b254af0c87546e1a3b9fd476a6ba1ad81331969d03",hex("33382c35313230312c35313430302c64617461325c49746d496d675c4d495330342e726f6d2c64617461325c49746d496d675c4d495330342e726f6d")},
    {39,39,97,6795,"5eab02ff761e8d9e22ce6ada65e50c16031f79a6413633a165c2282aa2b283d5",hex("33392c35313430312c35313530302c64617461325c49746d496d675c56505430312e726f6d2c64617461325c49746d496d675c56505430312e726f6d")},
    {40,40,98,6857,"eadf24e3e123ef384405a4b581913b55b9a28625203cd8f5a7b890ee4a81004e",hex("34302c35313530312c35323030302c64617461325c49746d496d675c414d5530312e726f6d2c64617461325c49746d496d675c414d5530312e726f6d")},
    {41,41,99,6919,"cf0473c012f9e35654b35fcb81885fc93557fe19a5d480a2433f6eddcfa5875c",hex("34312c35353030312c35353235302c64617461335c49746d496d675c53504930312e726f6d2c64617461325c49746d496d675c5350493031636e2e726f6d")},
    {42,42,100,6983,"961f5d88afbce874b6ffd33ef366281e5e304ae385988531259d9e1c6c0a5118",hex("34322c35353235312c35353434362c64617461325c49746d496d675c53504930322e726f6d2c64617461325c49746d496d675c53504930322e726f6d")},
    {43,43,101,7045,"d1cf64c0672c2df80c84fa608a90ca2d1e349e3749cb688fdc959ce677a5d583",hex("34332c35353434372c35353738332c64617461325c49746d496d675c53504930332e726f6d2c64617461325c49746d496d675c53504930332e726f6d")},
    {44,44,102,7107,"514b3be95b51c10de830d489a8ffae92f46e9d71367a52aacc270af0c1bd47ce",hex("34342c35353738342c35353938372c64617461325c49746d496d675c53504930342e726f6d2c64617461325c49746d496d675c53504930342e726f6d")},
    {45,45,103,7169,"d66d2ae1c1f2e6f88234e6f6cb7e5a3f84303a67b93a10375b41a216d46a9c55",hex("34352c35353938382c35363130302c64617461325c49746d496d675c53504930352e726f6d2c64617461325c49746d496d675c53504930352e726f6d")},
    {46,46,104,7231,"9305a2bba98ee39259adea24095d3363afde0aca7b7709d9e6997f8d650450e6",hex("34362c35383030312c35383230302c64617461325c49746d496d675c50464430312e726f6d2c64617461325c49746d496d675c50464430312e726f6d")},
    {47,47,105,7293,"330484f253902e094d8a08c624b40d28b06c94d6edc2908197dbb1eacbf8898c",hex("34372c36303030312c36303230302c64617461325c49746d496d675c544c4930312e726f6d2c64617461325c49746d496d675c544c4930312e726f6d")},
    {48,48,106,7355,"0bb8e516a2664f8c6c786deb27b3ed19af8413e8ba07497e9085281c905f6a2a",hex("34382c36333030312c36333230302c64617461325c49746d496d675c5354522e726f6d2c64617461325c49746d496d675c5354522e726f6d")},
    {49,49,107,7413,"9a838f16dee33cb0e32fa332af2b39cf5b5b961689b2c2db4132f69a8f62d4b8",hex("34392c36343030312c36343230302c64617461325c49746d496d675c534d4330312e726f6d2c64617461325c49746d496d675c534d4330312e726f6d")},
    {50,50,108,7475,"83873b65de07a94e3b7c4d2adb00fe2080ed81eb4c9257d429049fe461273887",hex("35302c36343830312c36353030302c64617461335c49746d496d675c4c4e472e726f6d2c64617461325c49746d496d675c4c4e47434e2e726f6d")},
    {51,51,109,7535,"2d7cf92f3b109ac7d32f673218167d70360e9f48abc4d36413ed2862388d66da",hex("35312c36353030312c36353130302c64617461325c49746d496d675c4745482e726f6d2c64617461325c49746d496d675c4745482e726f6d")},
    {52,52,110,7593,"1025efd1b5879e83e87125b7578e75fa9cb57f43f1135837f257c210e2a55e26",hex("35322c36353130312c36353230302c64617461325c49746d496d675c4745422e726f6d2c64617461325c49746d496d675c4745422e726f6d")},
    {53,53,111,7651,"81268e9125b3335b948cfad75fab2736e21adec16e5cc5dc2069e8acb1b1fc54",hex("35332c36353230312c36353234312c64617461325c49746d496d675c4757502e726f6d2c64617461325c49746d496d675c4757502e726f6d")},
    {54,54,112,7709,"05cb6c70560363a335b4036e7642631af7dd653eb231d7e7b593532db1aecab0",hex("35342c36353234322c36353330302c64617461325c49746d496d675c47575030322e726f6d2c64617461325c49746d496d675c47575030322e726f6d")},
    {55,55,113,7771,"14cf0abbc91f1406e2d3837b2691f7f8a2a1b3c055e4d03c14952a6213f0771b",hex("35352c36353330312c36353430302c64617461325c49746d496d675c4745512e726f6d2c64617461325c49746d496d675c4745512e726f6d")},
    {56,56,114,7829,"7c90e9b410a3658888fd2e88387e56adcc60bff0ccdada4743e63e6fbd697d98",hex("35362c36353430312c36353530302c64617461325c49746d496d675c5045512e726f6d2c64617461325c49746d496d675c5045512e726f6d")},
}};
std::vector<std::uint8_t> blob(sqlite_detail::Statement& row,int column) {
    const auto bytes=row.blob(column,1,4096);return {bytes.begin(),bytes.end()};
}
void bind(sqlite_detail::Statement& row,int index,const char* value) {
    row.bind(index,std::string(value));
}
void source_schema(sqlite3* db,bool require_both) {
    sqlite_detail::Statement objects(db,
        "SELECT type,name FROM main.sqlite_schema WHERE name COLLATE NOCASE IN("
        "'native_raw_resource_source_sets','native_raw_resource_source_rows') "
        "OR (type='trigger' AND tbl_name COLLATE NOCASE IN("
        "'native_raw_resource_source_sets','native_raw_resource_source_rows'))");
    unsigned tables=0;
    while(objects.row()) {
        if(objects.text(0)!="table")throw DatabaseError("RomMaps source table/view/trigger collision");
        ++tables;
    }
    if((tables!=0 && tables!=2) || (require_both && tables!=2))
        throw DatabaseError("RomMaps source tables absent or partial");
}
void import_temp_triggers(sqlite3* db) {
    // TEMP triggers can target main tables and perform collateral writes even
    // when the final source pins still match. Guard before any schema/data write.
    sqlite_detail::Statement triggers(db,
        "SELECT name FROM temp.sqlite_schema WHERE type='trigger' AND tbl_name COLLATE NOCASE IN("
        "'native_raw_resource_source_sets','native_raw_resource_source_rows')");
    if(triggers.row())throw DatabaseError("RomMaps source import TEMP trigger collision");
}
struct ReadScope {
    sqlite3* db;bool owned,committed=false;
    explicit ReadScope(sqlite3* value):db(value),owned(sqlite3_get_autocommit(db)!=0) {
        if(owned)sqlite_detail::execute(db,"BEGIN");
    }
    ReadScope(const ReadScope&)=delete;
    ReadScope& operator=(const ReadScope&)=delete;
    ~ReadScope(){if(owned && !committed)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owned)sqlite_detail::execute(db,"COMMIT");committed=true;}
};
}
NativeRomMapSourceCatalog::NativeRomMapSourceCatalog(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null RomMaps source connection");
}
std::vector<NativeRomMapSourceRecord> NativeRomMapSourceCatalog::records() const {
    ReadScope scope(db_);source_schema(db_,true);
    // Counts are independent of the join: orphan rows are visible even if the
    // envelope is absent. One seed/join query keeps counts and every byte in the
    // same transaction view. Explicit main names prevent TEMP/ATTACH fallback.
    sqlite_detail::Statement rows(db_,
        "SELECT (SELECT count(*) FROM main.native_raw_resource_source_sets WHERE dataset_id=?1),"
        "(SELECT count(*) FROM main.native_raw_resource_source_rows WHERE dataset_id=?1),"
        "s.version_scope,s.source_file,s.encoded_sha256,s.decoded_sha256,s.parser_image_sha256,"
        "s.section_name,s.header_source_line,s.header_decoded_offset,s.header_record_sha256,s.header_record,"
        "s.header_field_count,s.record_count,s.first_slot_index,s.last_slot_index,"
        "s.first_source_line,s.last_source_line,s.window_start_offset,s.window_end_offset,s.window_sha256,"
        "s.encoding,s.line_ending,s.authority,s.catalog_sha256,"
        "r.slot_index,r.source_record_index,r.source_line,r.decoded_offset,r.field_count,"
        "r.record_sha256,r.normalized_record,r.section_name,r.authority,s.dataset_id,r.dataset_id "
        "FROM (SELECT 1) seed LEFT JOIN main.native_raw_resource_source_sets s ON s.dataset_id=?1 "
        "LEFT JOIN main.native_raw_resource_source_rows r ON r.dataset_id=s.dataset_id "
        "ORDER BY r.source_record_index,r.slot_index");
    bind(rows,1,dataset_id);
    std::vector<NativeRomMapSourceRecord> result;result.reserve(pinned.size());
    while(rows.row()) {
        if(rows.integer(0)==0 && rows.integer(1)==0) {
            if(!result.empty() || rows.row())throw DatabaseError("Ambiguous empty RomMaps source");
            scope.finish();return {};
        }
        if(rows.integer(0)!=1 || rows.integer(1)!=57 || result.size()>=pinned.size() ||
           rows.text(2)!="TW149c_HISTORICAL_TEXT" || rows.text(3)!=source_file ||
           rows.text(4)!=encoded_sha256 || rows.text(5)!=decoded_sha256 ||
           rows.text(6)!=parser_image_sha256 || rows.text(7)!="RomMaps" ||
           rows.integer(8)!=57 || rows.integer(9)!=4374 || rows.text(10)!=header_record_sha256 ||
           blob(rows,11)!=raw_header || rows.integer(12)!=5 || rows.integer(13)!=57 ||
           rows.integer(14)!=0 || rows.integer(15)!=56 || rows.integer(16)!=58 ||
           rows.integer(17)!=114 || rows.integer(18)!=4374 || rows.integer(19)!=7887 ||
           rows.text(20)!=source_window_sha256 || rows.text(21)!="CP950_NORMALIZED_RECORD" ||
           rows.text(22)!="CRLF" || rows.text(23)!=authority || rows.text(24)!=catalog_sha256 ||
           rows.integer(29)!=5 || rows.text(32)!="RomMaps" || rows.text(33)!=authority ||
           rows.text(34)!=dataset_id || rows.text(35)!=dataset_id)
            throw DatabaseError("RomMaps source provenance/count mismatch");
        NativeRomMapSourceRecord value{rows.number<std::uint16_t>(25),rows.number<std::uint32_t>(26),
            rows.number<std::uint32_t>(27),rows.number<std::uint32_t>(28),rows.text(30),blob(rows,31)};
        // Stored SHA/fingerprint strings alone cannot qualify changed data.
        // Exact value and full-byte comparisons check every field of all57 pins.
        if(value!=pinned[result.size()])throw DatabaseError("RomMaps source record differs from pin");
        result.push_back(std::move(value));
    }
    if(result.size()!=pinned.size())throw DatabaseError("Incomplete RomMaps source");
    scope.finish();return result;
}
void NativeRomMapSourceCatalog::import_pinned_source(sqlite3* db) {
    if(!db || !sqlite3_get_autocommit(db))throw DatabaseError("RomMaps source import requires own transaction");
    sqlite_detail::Transaction transaction(db);
    import_temp_triggers(db);
    source_schema(db,false);
    // Shared dataset-namespaced source tables supply historical raw bytes only.
    // Native slot indices are not common gameplay IDs or inventory ownership.
    sqlite_detail::execute(db,
        "CREATE TABLE IF NOT EXISTS main.native_raw_resource_source_sets("
        "dataset_id TEXT PRIMARY KEY,version_scope TEXT NOT NULL,source_file TEXT NOT NULL,"
        "encoded_sha256 TEXT NOT NULL,decoded_sha256 TEXT NOT NULL,parser_image_sha256 TEXT NOT NULL,"
        "section_name TEXT NOT NULL,header_source_line INTEGER NOT NULL,header_decoded_offset INTEGER NOT NULL,"
        "header_record_sha256 TEXT NOT NULL,header_record BLOB NOT NULL,header_field_count INTEGER NOT NULL,"
        "record_count INTEGER NOT NULL,first_slot_index INTEGER NOT NULL,last_slot_index INTEGER NOT NULL,"
        "first_source_line INTEGER NOT NULL,last_source_line INTEGER NOT NULL,window_start_offset INTEGER NOT NULL,"
        "window_end_offset INTEGER NOT NULL,window_sha256 TEXT NOT NULL,encoding TEXT NOT NULL,"
        "line_ending TEXT NOT NULL,authority TEXT NOT NULL,catalog_sha256 TEXT NOT NULL)");
    sqlite_detail::execute(db,
        "CREATE TABLE IF NOT EXISTS main.native_raw_resource_source_rows("
        "dataset_id TEXT NOT NULL,slot_index INTEGER NOT NULL,source_record_index INTEGER NOT NULL,"
        "source_line INTEGER NOT NULL,decoded_offset INTEGER NOT NULL,field_count INTEGER NOT NULL,"
        "record_sha256 TEXT NOT NULL,normalized_record BLOB NOT NULL,section_name TEXT NOT NULL,authority TEXT NOT NULL,"
        "PRIMARY KEY(dataset_id,source_record_index),UNIQUE(dataset_id,slot_index),"
        "FOREIGN KEY(dataset_id) REFERENCES native_raw_resource_source_sets(dataset_id))");
    NativeRomMapSourceCatalog catalog(db);
    if(!catalog.records().empty()) {transaction.commit();return;}
    {
        sqlite_detail::Statement source(db,
            "INSERT INTO main.native_raw_resource_source_sets("
            "dataset_id,version_scope,source_file,encoded_sha256,decoded_sha256,parser_image_sha256,section_name,"
            "header_source_line,header_decoded_offset,header_record_sha256,header_record,header_field_count,"
            "record_count,first_slot_index,last_slot_index,first_source_line,last_source_line,"
            "window_start_offset,window_end_offset,window_sha256,encoding,line_ending,authority,catalog_sha256) "
            "VALUES(?1,'TW149c_HISTORICAL_TEXT',?2,?3,?4,?5,'RomMaps',57,4374,?6,?7,5,57,0,56,58,114,"
            "4374,7887,?8,'CP950_NORMALIZED_RECORD','CRLF',?9,?10)");
        bind(source,1,dataset_id);bind(source,2,source_file);bind(source,3,encoded_sha256);
        bind(source,4,decoded_sha256);bind(source,5,parser_image_sha256);bind(source,6,header_record_sha256);
        source.bind_blob(7,raw_header);bind(source,8,source_window_sha256);
        bind(source,9,authority);bind(source,10,catalog_sha256);source.done();
    }
    for(const auto& value:pinned) {
        sqlite_detail::Statement row(db,
            "INSERT INTO main.native_raw_resource_source_rows("
            "dataset_id,slot_index,source_record_index,source_line,decoded_offset,field_count,"
            "record_sha256,normalized_record,section_name,authority) "
            "VALUES(?1,?2,?3,?4,?5,5,?6,?7,'RomMaps',?8)");
        bind(row,1,dataset_id);row.bind(2,static_cast<std::int64_t>(value.slot_index));
        row.bind(3,static_cast<std::int64_t>(value.source_record_index));
        row.bind(4,static_cast<std::int64_t>(value.source_line));
        row.bind(5,static_cast<std::int64_t>(value.decoded_offset));row.bind(6,value.record_sha256);
        row.bind_blob(7,value.normalized_record);bind(row,8,authority);row.done();
    }
    // Borrow this import transaction to verify all inserted rows and metadata;
    // any exception rolls back both newly created schema and source data.
    if(catalog.records().size()!=pinned.size())throw DatabaseError("RomMaps source import did not qualify");
    transaction.commit();
}
}
