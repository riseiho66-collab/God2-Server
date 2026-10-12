from pathlib import Path
import hashlib,json

OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round339-rommaps-common-source-implementation')
BASE=OUT.parent;ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
PRIOR338=BASE/'round338-spi-rommaps-retained-source-audit'
PRIOR339=BASE/'tw-native-rommaps-loader-source-339'
sha=lambda b:hashlib.sha256(b).hexdigest()
OUT.mkdir(parents=True,exist_ok=True)
verified=[]
for package in [PRIOR338,PRIOR339]:
    seal_bytes=(package/'seal.json').read_bytes();seal=json.loads(seal_bytes)
    checked=[]
    for member in seal['members']:
        path=package/member['path'];assert path.resolve().is_relative_to(package.resolve())
        raw=path.read_bytes();assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
        checked.append(dict(path=member['path'],bytes=len(raw),sha256=sha(raw)))
    assert len(checked)==seal['member_count'] and sum(x['bytes'] for x in checked)==seal['retained_member_bytes']
    verified.append(dict(package=str(package),seal_sha256=sha(seal_bytes),member_count=len(checked),retained_member_bytes=sum(x['bytes'] for x in checked),members=checked))
SOURCE=BASE/'tw-native-resource-custody-and-remote-opaque-314/source-entry/inputs/exact-restored/gamedata.csvZ.decoded'
source=SOURCE.read_bytes();assert len(source)==2783008 and sha(source)=='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
rows=json.loads((PRIOR338/'rommaps57-source-line-cuts.json').read_bytes())
facts=json.loads((PRIOR338/'source-window-facts.json').read_bytes())
header=bytes.fromhex(facts['header_raw_cp950_hex'])
assert source[4374:4397]==header and sha(source[4374:7887])==facts['window_sha256']
assert len(rows)==57
pins=[]
for ordinal,row in enumerate(rows):
    line=bytes.fromhex(row['raw_line_cp950_hex']);body=line[:-2]
    assert line.endswith(b'\r\n') and len(line)==row['raw_line_bytes'] and sha(line)==row['raw_line_sha256']
    assert sha(body)==row['raw_body_sha256'] and len(body)==row['raw_body_bytes']
    assert source[row['decoded_offset']:row['decoded_offset']+len(line)]==line
    fields=[bytes.fromhex(x) for x in row['raw_body_fields_hex']]
    assert len(fields)==5 and b','.join(fields)==body and fields[0]==str(ordinal).encode('ascii')
    assert row['source_order_ordinal']==ordinal and row['source_line']==58+ordinal
    pins.append(dict(slot_index=ordinal,source_record_index=ordinal,source_line=row['source_line'],decoded_offset=row['decoded_offset'],record_sha256=sha(body),normalized_record_hex=body.hex(),raw_fields_hex=row['raw_body_fields_hex']))
dataset='tw149c-historical-rommaps-source-v1'
authority='HISTORICAL_RAW_RESOURCE_SOURCE_ONLY'
encoded='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
decoded='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
image='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
atoms=[b'GOD2-NATIVE-ROMMAPS-SOURCE-CANONICAL-V1',dataset.encode(),b'TW149c_HISTORICAL_TEXT',b'Data2/Patch/Comm/gamedata.csvZ',encoded.encode(),decoded.encode(),image.encode(),b'RomMaps',authority.encode(),b'CP950_NORMALIZED_RECORD',b'CRLF',b'57',b'4374',header,sha(header).encode(),b'5',b'57',b'0',b'56',b'58',b'114',b'4374',b'7887',facts['window_sha256'].encode()]
for pin in pins:
    atoms.extend([str(pin['slot_index']).encode(),str(pin['source_record_index']).encode(),str(pin['source_line']).encode(),str(pin['decoded_offset']).encode(),b'5',pin['record_sha256'].encode(),bytes.fromhex(pin['normalized_record_hex'])]+[bytes.fromhex(x) for x in pin['raw_fields_hex']])
canonical=b''.join(len(atom).to_bytes(4,'big')+atom for atom in atoms)
fingerprint=sha(canonical)
(OUT/'canonical-fingerprint-input.bin').write_bytes(canonical)
(OUT/'fingerprint-contract.json').write_text(json.dumps(dict(dataset_id=dataset,authority=authority,catalog_sha256=fingerprint,canonical_bytes=len(canonical),atom_count=len(atoms),atom_encoding='Each atom: unsigned32 big-endian byte length then exact bytes; integers canonical decimal ASCII; no host filesystem paths',envelope_atom_order=['canonical-format','dataset_id','version_scope','logical_source_file','encoded_sha256','decoded_sha256','parser_image_sha256','section_name','authority','encoding','line_ending','header_source_line','header_decoded_offset','raw_header_CRLF','header_record_sha256','header_field_count','record_count','first_slot_index','last_slot_index','first_source_line','last_source_line','window_start_offset','window_end_offset','window_sha256'],row_atom_order=['slot_index','source_record_index','source_line','decoded_offset','field_count','record_sha256','normalized_record','raw_field0','raw_field1','raw_field2','raw_field3','raw_field4'],raw_header_hex=header.hex(),header_record_sha256=sha(header),source_window_sha256=facts['window_sha256']),indent=2)+'\n',encoding='utf8',newline='\n')
HEADER=r'''#pragma once
#include <cstdint>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Exact historical RomMaps source text. The native token0 slot and physical
// source ordinal are separate fields even though both are0..56 in these pins.
// normalized_record preserves all5 raw CP950 fields, including both paths;
// token4 meaning, native converted ranges and current bank state are not supplied.
struct NativeRomMapSourceRecord {
    std::uint16_t slot_index;
    std::uint32_t source_record_index,source_line,decoded_offset;
    std::string record_sha256;
    std::vector<std::uint8_t> normalized_record;
    bool operator==(const NativeRomMapSourceRecord&) const=default;
};
class NativeRomMapSourceCatalog final {
public:
    static constexpr char dataset_id[]="tw149c-historical-rommaps-source-v1";
    static constexpr char authority[]="HISTORICAL_RAW_RESOURCE_SOURCE_ONLY";
    static constexpr char source_file[]="Data2/Patch/Comm/gamedata.csvZ";
    static constexpr char encoded_sha256[]="@ENCODED@";
    static constexpr char decoded_sha256[]="@DECODED@";
    static constexpr char parser_image_sha256[]="@IMAGE@";
    static constexpr char catalog_sha256[]="@FINGERPRINT@";
    explicit NativeRomMapSourceCatalog(sqlite3* db);
    // Reads actual main tables and validates the entire envelope/all57 exact
    // records in one joined snapshot. Empty installed tables return no records;
    // absent/partial schema or orphan/partial/corrupt source data throws.
    // Borrows a caller transaction; otherwise owns a read transaction.
    std::vector<NativeRomMapSourceRecord> records() const;
    // Explicit atomic, idempotent source import into the caller's main database.
    // Requires nonnull/autocommit, uses BEGIN IMMEDIATE, and never repairs or
    // replaces present corrupt data. No Main/Migration/gameplay caller is added.
    static void import_pinned_source(sqlite3* db);
private:
    sqlite3* db_;
};
}
'''
CPP=r'''#include "db/NativeRomMapSourceCatalog.h"
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
constexpr char header_record_sha256[]="@HEADER_SHA@";
constexpr char source_window_sha256[]="@WINDOW_SHA@";
// The original header includes its CRLF; source rows below are CRLF-stripped
// exact byte bodies with independently retained physical offsets and body hashes.
const auto raw_header=hex("@HEADER_HEX@");
const std::array<NativeRomMapSourceRecord,57> pinned{{
@PINS@
}};
std::vector<std::uint8_t> blob(sqlite_detail::Statement& row,int column) {
    const auto bytes=row.blob(column,1,4096);return {bytes.begin(),bytes.end()};
}
void bind(sqlite_detail::Statement& row,int index,const char* value) {
    row.bind(index,std::string(value));
}
void source_schema(sqlite3* db,bool require_both) {
    sqlite_detail::Statement objects(db,
        "SELECT type,name FROM main.sqlite_schema WHERE name IN("
        "'native_raw_resource_source_sets','native_raw_resource_source_rows') "
        "OR (type='trigger' AND tbl_name IN("
        "'native_raw_resource_source_sets','native_raw_resource_source_rows'))");
    unsigned tables=0;
    while(objects.row()) {
        if(objects.text(0)!="table")throw DatabaseError("RomMaps source table/view/trigger collision");
        ++tables;
    }
    if((tables!=0 && tables!=2) || (require_both && tables!=2))
        throw DatabaseError("RomMaps source tables absent or partial");
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
'''
pin_text='\n'.join('    {'+f"{p['slot_index']},{p['source_record_index']},{p['source_line']},{p['decoded_offset']},\"{p['record_sha256']}\",hex(\"{p['normalized_record_hex']}\")"+'},' for p in pins)
replacements={'@ENCODED@':encoded,'@DECODED@':decoded,'@IMAGE@':image,'@FINGERPRINT@':fingerprint,'@HEADER_SHA@':sha(header),'@WINDOW_SHA@':facts['window_sha256'],'@HEADER_HEX@':header.hex(),'@PINS@':pin_text}
for key,value in replacements.items():HEADER=HEADER.replace(key,value);CPP=CPP.replace(key,value)
assert '@PINS@' not in CPP and '@FINGERPRINT@' not in HEADER
destinations=[(ROOT/'src/db/NativeRomMapSourceCatalog.h',HEADER),(ROOT/'src/db/NativeRomMapSourceCatalog.cpp',CPP)]
assert all(not path.exists() for path,_ in destinations),'Refuse to overwrite existing files'
modified=[]
for path,text in destinations:
    path.write_text(text,encoding='utf8',newline='\n');raw=path.read_bytes()
    snapshot=OUT/'source'/path.name;snapshot.parent.mkdir(exist_ok=True);snapshot.write_bytes(raw)
    modified.append(dict(path=str(path),bytes=len(raw),sha256=sha(raw),retained=snapshot.relative_to(OUT).as_posix()))
(OUT/'upstream-member-verification.json').write_text(json.dumps(verified,indent=2)+'\n',encoding='utf8',newline='\n')
(OUT/'source-generation-manifest.json').write_text(json.dumps(dict(source=str(SOURCE),source_bytes=len(source),source_sha256=sha(source),catalog_sha256=fingerprint,canonical_bytes=len(canonical),atoms=len(atoms),pin_rows=len(pins),modified_files=modified,scope='Static raw-data generation and C++ source edits only; no project parser/native/API/SQLite/compiler/tests execution',full_source_copied=False),indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(catalog_sha256=fingerprint,canonical_bytes=len(canonical),atoms=len(atoms),pin_rows=len(pins),modified_files=modified)))
