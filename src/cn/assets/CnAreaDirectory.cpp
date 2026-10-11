#include "cn/assets/CnAreaDirectory.h"
#include <algorithm>
#include <stdexcept>

namespace god2cn {
std::optional<std::string_view> CnAreaDirectory::Entry::filename() const noexcept {
    const auto begin=native_record.begin()+1;
    const auto end=std::find(begin,native_record.end(),0);
    if (end==begin || end==native_record.end()) return std::nullopt;
    return std::string_view(reinterpret_cast<const char*>(native_record.data()+1),
        static_cast<std::size_t>(end-begin));
}
CnAreaDirectory CnAreaDirectory::read(std::span<const std::uint8_t> bytes) {
    constexpr std::array<std::uint8_t,8> header{'C','A','N',' ','v','1','.','0'};
    if (bytes.size()<12 || !std::equal(header.begin(),header.end(),bytes.begin()))
        throw std::invalid_argument("CN CAN header unavailable");
    std::size_t offset=8;
    const auto dword=[&]() {
        if (bytes.size()-offset<4) throw std::invalid_argument("CN CAN count truncated");
        const auto value=std::uint32_t(bytes[offset])|(std::uint32_t(bytes[offset+1])<<8)|
            (std::uint32_t(bytes[offset+2])<<16)|(std::uint32_t(bytes[offset+3])<<24);
        offset+=4;
        return value;
    };
    const auto count=dword();
    // Native pointer table+1270..166F and area table+106C..126B each hold256.
    // Refuse unsafe native overflow, without inventing a protocol failure code.
    if (count>256 || count>(bytes.size()-offset)/64)
        throw std::invalid_argument("CN CAN entries incomplete or outside native storage");
    CnAreaDirectory result;
    for (std::uint32_t i=0; i<count; ++i) {
        Entry entry;
        std::copy_n(bytes.begin()+offset,64,entry.native_record.begin());
        offset+=64;
        result.entries_.push_back(entry);
    }
    const auto area_count=dword();
    if (area_count>256 || area_count>(bytes.size()-offset)/2)
        throw std::invalid_argument("CN CAN area indices incomplete or outside native storage");
    for (std::uint32_t i=0; i<area_count; ++i) {
        result.area_indices_.push_back(static_cast<std::uint16_t>(bytes[offset]|(std::uint16_t(bytes[offset+1])<<8)));
        offset+=2;
    }
    // The native reader stops after the area table; preserve remaining bytes.
    result.trailing_.assign(bytes.begin()+offset,bytes.end());
    return result;
}
const CnAreaDirectory::Entry* CnAreaDirectory::lookup(std::uint16_t area) const noexcept {
    if (area>=area_indices_.size()) return nullptr;
    const auto index=area_indices_[area];
    return index<entries_.size()?&entries_[index]:nullptr;
}
}
