#pragma once
#include "cn/protocol/CnTransport.h"
#include <algorithm>
#include <bit>
#include <cstddef>
#include <optional>

namespace god2cn {
// D1(25/26) ->required actual owner ->F9/tag2 ->00511290/514060/5142D0.
// Evidence:cn-special-directory-owner-01. F9 is fixed2105bytes, not a
// variable count*stride packet. NPC appearance keys are not common/world IDs.
class CnSpecialDirectoryWire {
public:
    static constexpr std::size_t request_size=3,reply_size=2105,header_size=5;
    enum class Selector:std::uint8_t {Display25=0x25,Display26=0x26};
    struct Request {
        Selector selector;
        std::uint8_t native_page; // Actual wire byte, never an entitlement or common index.
        Bytes record;
    };
    struct NpcNameSlot {
        std::uint16_t selector;
        std::array<std::uint8_t,16> native_name;
    };
    struct NpcNameEvidence {
        std::uint64_t source_revision;
        std::int16_t native_max_selector; // Actual resource+124E0 signed bound.
        std::vector<NpcNameSlot> slots; // Fully supplied build-qualified consumed names, not defaults.
    };
    static std::optional<Request> read_request(std::span<const std::uint8_t> record) {
        if(record.size()!=request_size || record[0]!=0xd1 || (record[1]!=0x25 && record[1]!=0x26))return std::nullopt;
        return Request{static_cast<Selector>(record[1]),record[2],Bytes(record.begin(),record.end())};
    }
    class Page {
    public:
        Selector selector() const {return static_cast<Selector>(record_[1]);}
        std::uint8_t native_page() const {return record_[2];}
        std::uint8_t count() const {return record_[3];}
        std::size_t stride() const {return selector()==Selector::Display25?84:56;}
        std::optional<std::span<const std::uint8_t>> row(unsigned number) const {
            if(number>=count())return std::nullopt;
            return record_.subspan(header_size+number*stride(),stride());
        }
        //25 stops before copying the first row whose DWORD4 is0. Its
        // WORD4 name selector alone is not that sentinel. Remaining record
        // bytes stay retained; native stops copying rather than skipping it.
        unsigned consumed_rows() const {
            if(selector()==Selector::Display26)return count();
            unsigned number=0;
            while(number<count() && le32(*row(number),4)!=0)++number;
            return number;
        }
        std::optional<std::uint16_t> npc_name_selector(unsigned number) const {
            if(selector()!=Selector::Display25 || number>=consumed_rows())return std::nullopt;
            const auto bytes=*row(number);
            return static_cast<std::uint16_t>(bytes[4]|(std::uint16_t{bytes[5]}<<8));
        }
        std::optional<std::int32_t> display26_last_column_bits(unsigned number) const {
            if(selector()!=Selector::Display26)return std::nullopt;
            const auto bytes=row(number);if(!bytes)return std::nullopt;
            return std::bit_cast<std::int32_t>(le32(*bytes,52)); // Native signed%d presentation, no reward rule.
        }
        // Actual0050EB00 clears146 display rows/names. page1 begins at
        // indirect+57C4/4EA4 or8FF4, despite decoder indexing page*25 from
        // lower bases4F90/4D14/8A7C. Do not normalize that one-page offset.
        bool within_initial_clear() const {
            return native_page()!=0 && (std::size_t{native_page()}-1)*25+consumed_rows()<=146;
        }
        bool consumed_text_regions_terminated() const {
            for(unsigned number=0;number<consumed_rows();++number) {
                const auto bytes=*row(number);
                if(selector()==Selector::Display25) {
                    if(!terminated(bytes.subspan(8,20)) || !terminated(bytes.subspan(28,16)) ||
                       !terminated(bytes.subspan(44,36)))return false;
                }else if(!terminated(bytes.subspan(1,15)) || !terminated(bytes.subspan(17,15)) ||
                         !terminated(bytes.subspan(33,15)))return false;
            }
            return true; // Native printf widths are not bounds; actual owner still qualifies meaning/issuance.
        }
        bool npc_names_qualified(const NpcNameEvidence& names) const {
            if(selector()!=Selector::Display25 || !names.source_revision)return false;
            for(unsigned number=0;number<consumed_rows();++number) {
                const auto key=*npc_name_selector(number);
                if(names.native_max_selector<0 || key>names.native_max_selector)return false;
                const NpcNameSlot* found=nullptr;
                for(const auto& slot:names.slots)if(slot.selector==key) {
                    if(found)return false;found=&slot;
                }
                if(!found || !terminated(found->native_name))return false;
            }
            return true; // Structural consumed-name proof; build/source authority is mandatory with the owner.
        }
        std::span<const std::uint8_t> record() const {return record_;}
        std::span<const std::uint8_t> trailing_bytes() const {
            return record_.subspan(header_size+std::size_t{count()}*stride());
        }
    private:
        friend class CnSpecialDirectoryWire;
        explicit Page(std::span<const std::uint8_t> record):record_(record){}
        std::span<const std::uint8_t> record_; // Borrowed; retain complete2105bytes including unused tail.
    };
    static std::optional<Page> read_page(std::span<const std::uint8_t> record) {
        if(record.size()!=reply_size || record[0]!=0xf9 || (record[1]!=0x25 && record[1]!=0x26))return std::nullopt;
        const auto stride=record[1]==0x25?84u:56u;
        if(header_size+std::size_t{record[3]}*stride>record.size())return std::nullopt;
        return Page{record}; // Source byte-bound qualifier, not native capacity or official count limit.
    }
private:
    static bool terminated(std::span<const std::uint8_t> bytes) {
        return std::find(bytes.begin(),bytes.end(),std::uint8_t{0})!=bytes.end();
    }
    static std::uint32_t le32(std::span<const std::uint8_t> bytes,std::size_t offset) {
        return std::uint32_t{bytes[offset]}|(std::uint32_t{bytes[offset+1]}<<8)|
            (std::uint32_t{bytes[offset+2]}<<16)|(std::uint32_t{bytes[offset+3]}<<24);
    }
};
}
