#pragma once
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Original complete logical records. No request/reply pairing or stat names.
template<std::uint8_t Opcode,std::size_t Size>
class CnWorldConsumerRecord {
public:
    static std::optional<CnWorldConsumerRecord> parse_logical(std::span<const std::uint8_t> bytes) {
        if(bytes.size()!=Size || bytes[0]!=Opcode)return std::nullopt;
        CnWorldConsumerRecord result;
        std::copy(bytes.begin(),bytes.end(),result.bytes_.begin());return result;
    }
    std::span<const std::uint8_t> logical_bytes() const noexcept {return bytes_;}
    std::span<const std::uint8_t> payload() const noexcept {return {bytes_.data()+1,Size-1};}
private:
    CnWorldConsumerRecord()=default;
    std::array<std::uint8_t,Size> bytes_;
};
using CnOwnedRowRecord31=CnWorldConsumerRecord<0x31,29>;
using CnPanelRecord68=CnWorldConsumerRecord<0x68,13>;
using CnFixedPanelRecord6D=CnWorldConsumerRecord<0x6d,29>;

struct CnPanelHeader6D {
    std::array<std::uint8_t,28> original_payload;
    std::uint32_t page_cursor,page_count;
    static CnPanelHeader6D from_record(const CnFixedPanelRecord6D& record) {
        const auto bytes=record.payload();
        CnPanelHeader6D result;
        std::copy(bytes.begin(),bytes.end(),result.original_payload.begin());
        result.page_cursor=0;
        const auto count=std::uint32_t(bytes[4]&0x7f);
        result.page_count=std::max(std::uint32_t(1),(count+9)/10);
        return result;
    }
    //0052AF60 can read retained entries beyond the copied28B for larger counts.
    // This header cannot supply those entries, text resources or UI visibility.
};
}
