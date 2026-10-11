#pragma once
#include "cn/protocol/CnTransport.h"
#include <cstddef>
#include <optional>

namespace god2cn {
// Complete selector branch matrix for this one pinned005118E0 B0consumer.
// This does not qualify other world receivers, all directory gameplay, native
// issuance, or a client allocation capacity. Evidence: cn-directory-receiver-matrix-01.
class CnDirectoryReceiver {
public:
    enum class Owner {Player,Indirect1C85A8};
    enum class HighIndex {GrowFromLastRow,ReplaceFromLastRow};
    struct Layout {
        std::uint8_t selector;
        Owner owner;
        std::uint32_t row_base,metadata_base;
        // row_base indexes a40byte header as index0. Rows begin atindex1.
        // metadata_base owns cached high-index/page/pages/cursor at+0/4/8/12;
        // late selectors share metadata even when their row_base differs.
        HighIndex high_index;
        std::uint8_t pages_written;
        std::uint32_t receive_clear_bytes; //21/22 clear data rows before each B0.
        std::uint32_t initial_cleared_row_bytes; // Actual0050EB00 clear, not allocation size.
    };
    inline static constexpr std::array<Layout,18> layouts{{
        {0x11,Owner::Player,0x2e228,0x2e228,HighIndex::GrowFromLastRow,4,0,4000},
        {0x12,Owner::Player,0x2f1f0,0x2f1f0,HighIndex::GrowFromLastRow,4,0,4000},
        {0x15,Owner::Player,0x3067c,0x3067c,HighIndex::GrowFromLastRow,4,0,0x7e0},
        {0x16,Owner::Player,0x36554,0x36554,HighIndex::GrowFromLastRow,4,0,2000},
        {0x17,Owner::Player,0x345c4,0x345c4,HighIndex::GrowFromLastRow,4,0,4000},
        {0x18,Owner::Player,0x3558c,0x3558c,HighIndex::GrowFromLastRow,4,0,4000},
        {0x19,Owner::Player,0x30e74,0x30e74,HighIndex::GrowFromLastRow,4,0,2000},
        {0x1b,Owner::Player,0x3166c,0x3166c,HighIndex::GrowFromLastRow,4,0,4000},
        {0x21,Owner::Player,0x32634,0x32634,HighIndex::ReplaceFromLastRow,2,4000,4000},
        {0x22,Owner::Player,0x335fc,0x335fc,HighIndex::ReplaceFromLastRow,2,4000,4000},
        {0x23,Owner::Player,0x36d4c,0x36d4c,HighIndex::GrowFromLastRow,4,0,2000},
        {0x24,Owner::Indirect1C85A8,0x469c,0x469c,HighIndex::GrowFromLastRow,4,0,2000},
        {0x27,Owner::Indirect1C85A8,0xb560,0xb560,HighIndex::ReplaceFromLastRow,2,0,2000},
        {0x28,Owner::Indirect1C85A8,0xb560,0xb560,HighIndex::ReplaceFromLastRow,2,0,2000},
        {0x2a,Owner::Indirect1C85A8,0xbd30,0xb560,HighIndex::ReplaceFromLastRow,2,0,2000},
        {0x2b,Owner::Indirect1C85A8,0xbd30,0xb560,HighIndex::ReplaceFromLastRow,2,0,2000},
        {0x2c,Owner::Indirect1C85A8,0xc500,0xb560,HighIndex::ReplaceFromLastRow,2,0,2000},
        {0x2d,Owner::Indirect1C85A8,0xc500,0xb560,HighIndex::ReplaceFromLastRow,2,0,2000}
    }};
    static std::optional<Layout> layout(std::uint8_t selector,bool native_mode_bit0) {
        if(native_mode_bit0 && selector!=0x19 && selector!=0x23 && selector!=0x24)return std::nullopt;
        for(const auto& candidate:layouts)if(candidate.selector==selector)return candidate;
        return std::nullopt;
    }
    class Page {
    public:
        const Layout& layout() const {return layout_;}
        std::uint8_t count() const {return record_[4];}
        std::uint32_t cursor() const {return std::uint32_t{record_[5]}|(std::uint32_t{record_[6]}<<8)|
            (std::uint32_t{record_[7]}<<16)|(std::uint32_t{record_[8]}<<24);}
        std::optional<std::span<const std::uint8_t,40>> row(unsigned number) const {
            if(number>=count())return std::nullopt;
            return std::span<const std::uint8_t,40>(record_.data()+9+40*number,40);
        }
        // Bounded source publication region recovered from real initializer.
        // Native receiver itself does not check these indices.0overwrites its
        // header; an index outside this clear is unresolved, not proven invalid
        // for every other possible native variant. Do not call this capacity.
        bool rows_within_initial_clear() const {
            const auto complete_rows=layout_.initial_cleared_row_bytes/40;
            for(unsigned number=0;number<count();++number) {
                const auto index=(*row(number))[32];
                if(!index || index>complete_rows)return false;
            }
            return true;
        }
        std::span<const std::uint8_t> record() const {return record_;}
    private:
        friend class CnDirectoryReceiver;
        Page(Layout layout,std::span<const std::uint8_t> record):layout_(layout),record_(record){}
        Layout layout_;
        std::span<const std::uint8_t> record_; // Borrowed; caller retains actual complete record.
    };
    static std::optional<Page> read(std::span<const std::uint8_t> record,bool native_mode_bit0) {
        if(record.size()<9 || record.size()>CnTransport::max_logical || record[0]!=0xb0 ||
           std::size_t(record[1]|(std::uint16_t{record[2]}<<8))!=record.size() ||
           record.size()!=9+40*std::size_t{record[4]})return std::nullopt;
        const auto selected=layout(record[3],native_mode_bit0);if(!selected)return std::nullopt;
        return Page{*selected,record};
    }
};
}
