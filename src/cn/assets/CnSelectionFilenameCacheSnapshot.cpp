#include "cn/assets/CnSelectionFilenameCacheSnapshot.h"
#include <algorithm>
#include <utility>

namespace god2cn {
namespace {
std::uint32_t dword(std::span<const std::uint8_t> bytes,std::size_t at) {
    std::uint32_t result=0;
    for(unsigned i=0;i<4;++i)result|=std::uint32_t(bytes[at+i])<<(i*8);
    return result;
}
bool native_name(std::string_view value) {
    return !value.empty() && value.size()<256 &&
        std::all_of(value.begin(),value.end(),[](unsigned char c) {return c!=0;});
}
unsigned char lower_ascii(unsigned char c) {
    return c>='A' && c<='Z'?static_cast<unsigned char>(c+('a'-'A')):c;
}
bool equal_ascii_name(std::string_view a,std::string_view b) {
    if(a.size()!=b.size())return false;
    for(std::size_t i=0;i<a.size();++i)
        if(lower_ascii(static_cast<unsigned char>(a[i]))!=lower_ascii(static_cast<unsigned char>(b[i])))
            return false;
    return true;
}
}
CnSelectionFilenameCacheSnapshot::CnSelectionFilenameCacheSnapshot(Scope scope,
    std::uint32_t count,std::uint32_t capacity,std::uint32_t preload,
    std::vector<std::string> names,Current current)
    :scope_(scope),count_(count),capacity_(capacity),preload_(preload),
     active_names_(std::move(names)),current_(std::move(current)) {}
std::optional<CnSelectionFilenameCacheSnapshot> CnSelectionFilenameCacheSnapshot::read_native_owner(
    std::uint32_t ui_word,std::uint32_t pool_word,std::span<const std::uint8_t> ui,
    std::span<const std::uint8_t> pool,const std::vector<CnSelectionNativeNameBuffer>& buffers,
    std::uint32_t compare_word,std::span<const std::uint8_t> compare_flag,
    std::uint64_t revision,Current current) {
    if(!ui_word || !pool_word || !compare_word || compare_flag.size()!=4 || dword(compare_flag,0)!=0 ||
       !revision || !current || ui.size()<0x1792d0 || pool.size()<0x410)
        return std::nullopt;
    const Scope scope{ui_word,pool_word,dword(ui,0x16174),compare_word,revision};
    if(!scope.rom_bank_word || dword(ui,0x1792cc)!=pool_word || !current(scope))return std::nullopt;
    const auto count=dword(pool,0x404),capacity=dword(pool,0x408),preload=dword(pool,0x40c);
    // Physical pointer table is256 entries. Constructor proves initial22,
    // not an always22 runtime value. Other unsafe native states are unqualified.
    if(!capacity || capacity>256 || count>capacity || preload>capacity || buffers.size()!=capacity)
        return std::nullopt;
    std::vector<std::string> names;names.reserve(count);
    for(std::size_t index=0;index<buffers.size();++index) {
        const auto& buffer=buffers[index];
        if(!buffer.native_buffer_word || dword(pool,4+index*4)!=buffer.native_buffer_word)
            return std::nullopt;
        // Inactive allocations have no proven string contents; do not read,
        // clear or manufacture them. Only validate their actual pointer binding.
        if(index>=count)continue;
        if(buffer.bytes.size()!=256)return std::nullopt;
        const auto end=std::find(buffer.bytes.begin(),buffer.bytes.end(),0);
        if(end==buffer.bytes.end())return std::nullopt;
        std::string name(reinterpret_cast<const char*>(buffer.bytes.data()),
            static_cast<std::size_t>(end-buffer.bytes.begin()));
        if(!native_name(name))return std::nullopt;
        // Two supplied snapshots of the same actual allocation cannot disagree.
        for(std::size_t prior=0;prior<index;++prior)
            if(buffers[prior].native_buffer_word==buffer.native_buffer_word &&
               buffers[prior].bytes!=buffer.bytes)return std::nullopt;
        names.push_back(std::move(name));
    }
    if(!current(scope))return std::nullopt;
    return CnSelectionFilenameCacheSnapshot(scope,count,capacity,preload,std::move(names),std::move(current));
}
bool CnSelectionFilenameCacheSnapshot::current() const {
    return current_ && current_(scope_);
}
std::optional<CnSelectionFilenameOperand> CnSelectionFilenameCacheSnapshot::probe_native_filename(
    std::string_view name) const {
    if(!native_name(name) || !current())return std::nullopt;
    auto kind=count_<capacity_?CnSelectionFilenameOperand::Kind::LoadRequired:
        CnSelectionFilenameOperand::Kind::CapacityUnqualified;
    auto slot=count_;
    for(std::size_t index=0;index<active_names_.size();++index) {
        if(equal_ascii_name(name,active_names_[index])) {
            kind=CnSelectionFilenameOperand::Kind::ExistingName;
            slot=static_cast<std::uint32_t>(index);break;
        }
    }
    if(!current())return std::nullopt;
    return CnSelectionFilenameOperand{kind,scope_.revision,scope_.rom_bank_word,slot};
}
std::optional<std::uint32_t> CnSelectionFilenameCacheSnapshot::restore_preload_count_operand() const {
    if(!current())return std::nullopt;
    return preload_;
}
}
