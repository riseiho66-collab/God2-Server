#pragma once
#include "cn/protocol/CnTransport.h"
#include "cn/protocol/CnDirectorySelection.h"
#include "cn/protocol/CnDirectoryReceiver.h"
#include <cstddef>
#include <optional>

namespace god2cn {
//0050E3B0 refresh94 and AF ->00511290 tag1 ->00512C50/00513C40.
// Evidence:cn-generic-directory-owner-01. F9/tag2, B0, unrelated S2C94
// and D1 are different contracts. This supplies no rank data or permissions.
class CnGenericDirectoryWire {
public:
    static constexpr std::size_t request_size=9,page_header_size=9;
    struct Request {
        std::uint8_t selector;
        std::uint32_t cursor;
        Bytes record; // Includes actual three unwritten padding bytes, never zero filled.
        std::vector<CnDirectorySelection::Origin> known_origins() const {
            return CnDirectorySelection::known_origins(false,selector);
        }
    };
    static bool covered_refresh_selector(std::uint8_t selector) {
        // This bounded source branch covers native mode0 explicit origins
        // using94 withoutD1 and without a specialized B0consumer layout.
        // Other callers/variants are pending, not globally forbidden packets.
        const auto source=CnDirectorySelection::producer(false,selector);
        return selector<=0x2d && source.sends94 && !source.sendsD1 &&
            source.cursor_kind==CnDirectorySelection::CursorKind::GenericSelectorField &&
            !CnDirectoryReceiver::layout(selector,false) &&
            !CnDirectorySelection::known_origins(false,selector).empty();
    }
    static std::optional<Request> read_request(std::span<const std::uint8_t> record) {
        if(record.size()!=request_size || record[0]!=0x94 || !covered_refresh_selector(record[1]))return std::nullopt;
        return Request{record[1],le32(record,5),Bytes(record.begin(),record.end())};
    }
    class Page {
    public:
        std::uint8_t selector() const {return record_[3];}
        std::uint8_t count() const {return record_[4];}
        std::uint32_t cursor() const {return le32(record_,5);}
        std::size_t stride() const {return selector()==0x14?24:20;}
        std::uint32_t native_cache_offset() const {
            return selector()==0x14?0x301c4:0x22d08+std::uint32_t{selector()}*0x3f0;
        }
        std::size_t native_copy_bytes() const {return record_.size()-1;}
        std::optional<std::span<const std::uint8_t>> row(unsigned number) const {
            if(number>=count())return std::nullopt;
            return record_.subspan(page_header_size+number*stride(),stride());
        }
        std::optional<std::span<const std::uint8_t,16>> row_text(unsigned number) const {
            const auto bytes=row(number);if(!bytes)return std::nullopt;
            return std::span<const std::uint8_t,16>(bytes->data(),16);
        }
        std::optional<std::uint32_t> row_value_bits(unsigned number) const {
            const auto bytes=row(number);if(!bytes)return std::nullopt;
            return le32(*bytes,16); // Native raw DWORD; business meaning is selector specific.
        }
        std::optional<std::uint16_t> special_displayed_word(unsigned number) const {
            if(selector()!=0x14)return std::nullopt;
            const auto bytes=row(number);if(!bytes)return std::nullopt;
            return static_cast<std::uint16_t>((*bytes)[20]|(std::uint16_t{(*bytes)[21]}<<8));
        }
        //0050EB00 clears generic header/rows as a46-slot region, each0x3F0.
        // It does not prove the special14 array's capacity. Only normal pages
        // get this local initialized-region guard; the real owner must separately
        // qualify special14 storage/strings and all native/business constraints.
        std::optional<bool> fits_initialized_generic_slot() const {
            if(selector()==0x14)return std::nullopt;
            return native_copy_bytes()<=0x3f0;
        }
        std::span<const std::uint8_t> record() const {return record_;}
    private:
        friend class CnGenericDirectoryWire;
        explicit Page(std::span<const std::uint8_t> record):record_(record){}
        std::span<const std::uint8_t> record_; // Borrowed, retain caller's complete actual bytes.
    };
    static std::optional<Page> read_page(std::span<const std::uint8_t> record) {
        if(record.size()<page_header_size || record.size()>CnTransport::max_logical || record[0]!=0xaf ||
           record[3]>0x2d || std::size_t(record[1]|(std::uint16_t{record[2]}<<8))!=record.size())return std::nullopt;
        const auto stride=record[3]==0x14?24u:20u;
        if(record.size()!=page_header_size+std::size_t{record[4]}*stride)return std::nullopt;
        return Page{record}; // Receiver view is broader than this source owner's explicit producers.
    }
private:
    static std::uint32_t le32(std::span<const std::uint8_t> bytes,std::size_t offset) {
        return std::uint32_t{bytes[offset]}|(std::uint32_t{bytes[offset+1]}<<8)|
            (std::uint32_t{bytes[offset+2]}<<16)|(std::uint32_t{bytes[offset+3]}<<24);
    }
};
}
