from pathlib import Path
import hashlib,json
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round340-spi-conditional-record-implementation')
BASE=OUT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8',newline='\n')
verified=[]
for folder,expected in [('tw-native-spi-allocation-zero-source-340','b68ef4dc5494bfe74e057ce0140fb0d955d8e462022cb831c4dc4af6188dcc4c'),('tw-native-spi-generic-record-write-source-340','eea7b0a2c86f7cb32a75f869acd8503650299670ed45758d69f7069a3ebefa03')]:
    package=BASE/folder;sealbytes=(package/'seal.json').read_bytes();assert sha(sealbytes)==expected
    seal=json.loads(sealbytes);members=[]
    for member in seal['members']:
        raw=(package/member['path']).read_bytes();assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
        members.append(dict(path=member['path'],bytes=len(raw),sha256=sha(raw)))
    total=sum(m['bytes'] for m in members)
    assert len(members)==seal['member_count'] and total==seal.get('retained_member_bytes',seal.get('member_bytes'))
    verified.append(dict(package=folder,seal_sha256=sha(sealbytes),member_count=len(members),total_member_bytes=total,members=members))
put('upstream-member-verification.json',verified)
header=ROOT/'src/db/NativePetRoomSourceCatalog.h';cpp=ROOT/'src/db/NativePetRoomSourceCatalog.cpp'
before=[]
for path in [header,cpp]:
    raw=path.read_bytes();name=path.name
    target=OUT/'source-before'/name;target.parent.mkdir(exist_ok=True)
    assert not target.exists();target.write_bytes(raw)
    before.append(dict(path=str(path),bytes=len(raw),sha256=sha(raw),archived_as=str(target.relative_to(OUT))))
put('before-source-manifest.json',before)
h=header.read_text(encoding='utf8');c=cpp.read_text(encoding='utf8')
assert 'NativePetRoomDefinitionRecordSource' not in h and 'lookup_definition_record_source' not in c
struct_text='''// Conditional reconstruction of the historical generic SPI396 source path.
// All conditions below are assumptions of this source projection; the API does
// not observe original allocation, current bank identity or a native record.
// Owning resource/text records retain the same raw SPI provenance independently.
struct NativePetRoomDefinitionRecordSource {
    static constexpr char qualification[]="CONDITIONAL_HISTORICAL_SPI396_SOURCE_PROJECTION";
    static constexpr const char* required_input=NativePetRoomDefinitionScalars::required_input;
    static constexpr const char* required_classification=NativePetRoomDefinitionScalars::required_classification;
    static constexpr const char* required_line_input=NativePetRoomDefinitionResource::required_line_input;
    static constexpr const char* required_native_bank=NativePetRoomDefinitionResource::required_native_bank;
    static constexpr char required_zero_allocation[]=
        "Successful original correctly sized allocations: native ItemType count46 "
        "with1602 stride and native SPI count737 with396 stride; valid storage and "
        "fault-free completion under normal DF-clear "
        "x86 calling conditions; actual547E23 small-block success clears the original "
        "product through54A550, or successful HeapAlloc uses HEAP_ZERO_MEMORY flag8";
    static constexpr char required_spi_selector[]=
        "Original historical ItemType physical ordinal9 is SPI, in the native46-row "
        "category bank; its bounded row has selector at63D; "
        "all36 original category comparisons return nonzero, preserving allocated "
        "zero at category63D; lookup forwards selector0 and the same catalog to459420";
    static constexpr char required_physical_slot[]=
        "Original native SPI bank contains737 physical rows, not the retained22; "
        "correct preceding native row reads place source_record_index517..538 in "
        "the same correctly allocated396 physical slots; row advancement also "
        "occurs for invalid token0 rows; valid full native bank/key-pointer-table "
        "storage registers the source key to that physical slot; the key is not "
        "a physical slot and there are no prior out-of-bounds record writes";
    static constexpr char required_record_construction[]=
        "Exact bounded historical22 source fields and qualified normalized numeric "
        "input under stable classification/rt; complete correct native row placement "
        "and RomMaps population; stable original5B4640 byte0 and584BB0 LF+NUL "
        "literals; valid fault-free token/copy/conversion children and DF-clear "
        "REP copies; no faults, out-of-bounds or intervening record/bank writes; "
        "current resource/bank identity and full396 native output remain unobserved";
    NativePetRoomDefinitionResource source_resource;
    NativePetRoomDefinitionText source_text;
    std::array<std::uint8_t,396> conditional_record_bytes;
};
'''
h=h.replace('#include <cstdint>','#include <array>\n#include <cstdint>',1)
anchor='class NativePetRoomSourceCatalog final {'
assert h.count(anchor)==1;h=h.replace(anchor,struct_text+anchor,1)
method_decl='''    // Composes the existing complete57+22 resource and text projections in one
    // read scope, requiring identical owning SPI records. Returns separately
    // typed conditional historical396 bytes; no observed/native gameplay state.
    std::optional<NativePetRoomDefinitionRecordSource> lookup_definition_record_source(std::uint16_t native_key) const;
'''
anchor='    std::optional<NativePetRoomDefinitionResource> lookup_definition_resource(std::uint16_t native_key) const;\n'
assert h.count(anchor)==1;h=h.replace(anchor,anchor+method_decl,1)
helpers='''// Byte stores reproduce the selected native physical layout without host
// endianness, packed-struct aliasing or treating metadataDWORD0 as a source key.
void store_record_word(std::array<std::uint8_t,396>& bytes,std::size_t offset,std::uint16_t value) {
    bytes[offset]=static_cast<std::uint8_t>(value);
    bytes[offset+1]=static_cast<std::uint8_t>(value>>8u);
}
void store_record_dword(std::array<std::uint8_t,396>& bytes,std::size_t offset,std::uint32_t value) {
    for(unsigned i=0;i<4;++i)bytes[offset+i]=static_cast<std::uint8_t>(value>>(8u*i));
}
void copy_record_string(std::array<std::uint8_t,396>& bytes,std::size_t offset,
                        const std::vector<std::uint8_t>& text,std::size_t capacity) {
    // The native copies precede forced end bytes and do not have these guards.
    // These finite-source bounds preserve their actual meaningful text+NUL.
    if(text.size()>=capacity || offset>bytes.size() || capacity>bytes.size()-offset)
        throw DatabaseError("PetRoom conditional record string exceeds qualified region");
    for(std::size_t i=0;i<text.size();++i)bytes[offset+i]=text[i];
    bytes[offset+text.size()]=0;
}
NativePetRoomDefinitionRecordSource project_record_source(
    NativePetRoomDefinitionResource resource,NativePetRoomDefinitionText text) {
    // Value initialization is explicitly conditional on the original successful
    // zero-allocation/selector0 premises, not an observed current record buffer.
    NativePetRoomDefinitionRecordSource result{std::move(resource),std::move(text),{}};
    auto& bytes=result.conditional_record_bytes;
    const auto& scalars=result.source_resource.source_scalars;
    store_record_dword(bytes,0x000,scalars.metadata_dword0); // token5
    store_record_dword(bytes,0x004,scalars.metadata_dword4); // token6
    copy_record_string(bytes,0x008,result.source_text.definition_name_cp950,38);
    bytes[0x02d]=0; //459473 forces this byte after the whole token4+NUL copy
    copy_record_string(bytes,0x02e,result.source_text.caption_cp950,38);
    bytes[0x053]=0; //45949D forces this byte after the whole token7+NUL copy
    copy_record_string(bytes,0x054,result.source_text.description_cp950,190);
    // No forced recordBYTE111 write: native forces scratch[BDh], then copies
    // the meaningful description+NUL; remaining bytes retain allocated zero.
    store_record_word(bytes,0x112,scalars.metadata_word112);
    store_record_word(bytes,0x114,scalars.metadata_word114);
    store_record_word(bytes,0x116,result.source_resource.metadata_word116);
    store_record_word(bytes,0x118,0xffffu);
    bytes[0x11a]=scalars.metadata_byte11A;
    if((scalars.metadata_byte11B_low4&0xf0u)!=0)
        throw DatabaseError("PetRoom conditional scalar low4 shape differs");
    bytes[0x11b]=scalars.metadata_byte11B_low4; // preserved high4 conditional initial0
    // Selector0 skips category-specific stores:11C..18B retains conditional0.
    return result;
}
'''
anchor='void source_schema(sqlite3* db,bool require_both) {'
assert c.count(anchor)==1;c=c.replace(anchor,helpers+anchor,1)
method='''std::optional<NativePetRoomDefinitionRecordSource> NativePetRoomSourceCatalog::lookup_definition_record_source(std::uint16_t key) const {
    ReadScope scope(db_);
    // Resource validates both complete installed datasets before even an
    // absent-key return. Every nested read borrows this same transaction view.
    auto resource=lookup_definition_resource(key);
    if(!resource) {scope.finish();return {};}
    auto text=lookup_definition_text(key);
    if(!text || text->source_record!=resource->source_scalars.source_record)
        throw DatabaseError("PetRoom conditional resource/text source mismatch");
    auto result=project_record_source(std::move(*resource),std::move(*text));
    scope.finish();return result;
}
'''
anchor='void NativePetRoomSourceCatalog::import_pinned_source(sqlite3* db) {'
assert c.count(anchor)==1;c=c.replace(anchor,method+anchor,1)
header.write_text(h,encoding='utf8',newline='\n');cpp.write_text(c,encoding='utf8',newline='\n')
after=[]
for path in [header,cpp]:
    raw=path.read_bytes();target=OUT/'source-final'/path.name;target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
    after.append(dict(path=str(path),bytes=len(raw),sha256=sha(raw),archived_as=str(target.relative_to(OUT))))
put('final-source-manifest.json',after)
put('additive-source-edits.json',dict(header_include='#include <array>',header_type=struct_text,header_method_declaration=method_decl,cpp_helpers=helpers,cpp_method=method,scope='Only additive two-file source edit; no existing pins/contracts/readers/importer rewritten; no C++/API/SQL/native execution'))
print(json.dumps(dict(before=before,after=after,upstream_packages=len(verified),upstream_members=sum(v['member_count'] for v in verified))))
