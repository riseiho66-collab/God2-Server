#include "cn/world/CnWorldConsumerSource.h"
#include "cn/protocol/CnSubjectStatus31.h"
#include <limits>
#include <utility>

namespace god2cn {
namespace {
constexpr std::size_t ui=0x89b26c;
std::uint16_t u16(std::span<const std::uint8_t> b,std::size_t n) {
    return std::uint16_t(b[n])|(std::uint16_t(b[n+1])<<8);
}
std::uint32_t u32(std::span<const std::uint8_t> b,std::size_t n) {
    return std::uint32_t(u16(b,n))|(std::uint32_t(u16(b,n+2))<<16);
}
std::int16_t s16(std::span<const std::uint8_t> b,std::size_t n) {
    return std::bit_cast<std::int16_t>(u16(b,n));
}
void put16(std::span<std::uint8_t> b,std::size_t n,std::uint16_t value) {
    b[n]=std::uint8_t(value);b[n+1]=std::uint8_t(value>>8);
}
void put32(std::span<std::uint8_t> b,std::size_t n,std::uint32_t value) {
    put16(b,n,std::uint16_t(value));put16(b,n+2,std::uint16_t(value>>16));
}
bool scope_qualifies(const CnWorldConsumerSource::Scope& s) {
    const auto alias=std::uint64_t(s.actual_world_owner_word)+ui;
    return s.actual_world_owner_word && s.actual_related_owner_word && s.actual_revision &&
        alias<=std::numeric_limits<std::uint32_t>::max() && s.actual_ui_owner_word==alias;
}
}
CnWorldConsumerSource::OwnedRows31::OwnedRows31(Scope scope,Current current,std::vector<Row31> rows)
    :scope_(scope),current_(std::move(current)),rows_(std::move(rows)) {}
bool CnWorldConsumerSource::OwnedRows31::current() const {return current_(scope_);}
std::optional<CnWorldConsumerSource::OwnedRows31> CnWorldConsumerSource::read_owned_rows31(
    Scope s,std::span<const std::uint8_t> world,std::span<const std::uint8_t> related,Current current) {
    if(!scope_qualifies(s) || !current || world.size()<ui+0x430ac || related.size()<0xd8 ||
       !current(s) || u32(world,ui+0x430a8)!=s.actual_related_owner_word)return std::nullopt;
    const auto count=std::size_t(related[0xd4]);
    if(related.size()<0xd8+count*0x3ec)return std::nullopt;
    std::vector<Row31> rows(count);
    for(std::size_t i=0;i<count;++i)std::copy_n(related.begin()+0xd8+i*0x3ec,0x3ec,rows[i].begin());
    if(!current(s))return std::nullopt;
    return OwnedRows31(s,std::move(current),std::move(rows));
}
std::optional<CnWorldConsumerSource::OwnedRowUpdate31>
CnWorldConsumerSource::OwnedRows31::project_existing_row(const CnOwnedRowRecord31& record) const {
    if(!current())return std::nullopt;
    const auto status=CnSubjectStatus31::read(record.logical_bytes());
    if(!status)return std::nullopt;
    //Reuse the same qualified WORLD31 fields/first-match semantics as the
    //publication source. The BYTE active count gives at most255 real entries.
    std::array<std::uint16_t,255> identifiers;
    for(std::size_t i=0;i<rows_.size();++i)identifiers[i]=u16(rows_[i],0);
    const auto match=status->first_native_roster_match({identifiers.data(),rows_.size()});
    if(!match)return std::nullopt;
    const auto ordinal=*match;
    const auto fields=status->native_fields();
    const auto row_word=std::uint64_t(scope_.actual_related_owner_word)+0xd8+ordinal*0x3ec;
    if(row_word>std::numeric_limits<std::uint32_t>::max())return std::nullopt;
    auto after=rows_[ordinal];after[2]=fields.native_entry_byte2;
    for(std::size_t i=0;i<5;++i)put32(after,0x44+i*4,fields.native_entry_dwords44_through54[i]);
    for(std::size_t i=0;i<4;++i)put16(after,0x38+i*2,fields.native_entry_words38_through3E[i]);
    put16(after,0x28,fields.native_entry_word28);after[0x5a]=fields.native_entry_byte5A;
    after[0x3e8]=0;after[0x3e9]=std::uint8_t((std::uint32_t(after[0x1f0])+24)/25);
    bool any=false;
    for(std::size_t i=0;i<rows_.size();++i)any=any || (i==ordinal?after[0x5a]:rows_[i][0x5a])==1;
    if(!current())return std::nullopt;
    return OwnedRowUpdate31{std::uint8_t(ordinal),std::uint32_t(row_word),rows_[ordinal],after,any};
}
CnWorldConsumerSource::ResourceRows68::ResourceRows68(Scope s,Current current,
    std::int16_t handle,std::int16_t resource_word,std::int16_t count,std::uint32_t table_word,
    std::vector<std::array<std::uint8_t,0x8c>> rows)
    :scope_(s),current_(std::move(current)),handle_(handle),resource_word_(resource_word),count_(count),
     table_word_(table_word),rows_(std::move(rows)) {}
bool CnWorldConsumerSource::ResourceRows68::current() const {return current_(scope_);}
std::optional<CnWorldConsumerSource::ResourceRows68> CnWorldConsumerSource::read_resource_rows68(
    Scope s,std::span<const std::uint8_t> world,std::span<const std::uint8_t> related,
    std::uint32_t actual_table_word,std::span<const std::uint8_t> table,Current current) {
    if(!scope_qualifies(s) || !current || world.size()<0xa69f24 || related.size()<0xb2f80 ||
       !current(s) || u32(world,0xa69f20)!=s.actual_related_owner_word ||
       u32(related,0xb2f7c)!=actual_table_word)return std::nullopt;
    const auto count=s16(related,0xb2f78);
    std::vector<std::array<std::uint8_t,0x8c>> rows;
    // A nonpositive actual count rejects every unsigned nonzero index. No
    // missing table bytes are manufactured. Positive counts require full rows.
    if(count>0) {
        if(!actual_table_word || table.size()<std::size_t(count)*0x8c)return std::nullopt;
        rows.resize(std::size_t(count));
        for(std::size_t i=0;i<rows.size();++i)std::copy_n(table.begin()+i*0x8c,0x8c,rows[i].begin());
    }
    const auto handle=s16(world,ui+0x1c84c4),resource_word=s16(related,0xb2f76);
    if(!current(s))return std::nullopt;
    return ResourceRows68(s,std::move(current),handle,resource_word,count,actual_table_word,std::move(rows));
}
std::optional<CnWorldConsumerSource::PanelOperand68>
CnWorldConsumerSource::ResourceRows68::lookup_operand(const CnPanelRecord68& record) const {
    if(!current())return std::nullopt;
    const auto b=record.logical_bytes();const auto index=u16(b,3);
    PanelOperand68 result{handle_,resource_word_,index,std::nullopt,std::nullopt,
        u32(b,5),std::uint32_t(b[9]),b[10]==1?0x69u:0x64u,std::int32_t(resource_word_)};
    if(index!=0 && std::int32_t(index)<=count_) {
        const auto word=std::uint64_t(table_word_)+(std::size_t(index)-1)*0x8c;
        if(word>std::numeric_limits<std::uint32_t>::max())return std::nullopt;
        result.actual_row_word=std::uint32_t(word);result.original_resource_row=rows_[index-1];
    }
    if(!current())return std::nullopt;
    return result;
}
}
