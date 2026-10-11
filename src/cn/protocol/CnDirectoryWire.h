#pragma once
#include "cn/protocol/CnTransport.h"
#include "cn/protocol/CnDirectoryReceiver.h"
#include "cn/protocol/CnDirectorySelection.h"
#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <optional>
#include <stdexcept>

namespace god2cn {
// Pinned CN0050E3B0/00515680 producers and0048FCC0 ->00511620/
// 005118E0 consumers. Evidence: cn-native-directory-owner-01. This bounded
// view covers selectors19/23/24 only; their business names are still unknown.
// It neither recovers directory permissions nor manufactures any native data.
class CnDirectoryWire {
public:
    static constexpr std::size_t request_size=9,page_request_size=3;
    static constexpr std::size_t summary_size=25,page_header_size=9,row_size=40;
    enum class Channel:std::uint8_t {Selector19=0x19,Selector23=0x23,Selector24=0x24};
    enum class Operation {Refresh94,PageA4};
    struct Request {
        Channel channel;
        Operation operation;
        Bytes record; // Exact bytes, including unwritten94 padding; not control authority.
        std::optional<std::uint32_t> cursor;
        std::optional<int> page_direction;
        // Context for the actual shared owner: UI fields are not carried by
        // this request and must never be reconstructed as permissions.
        std::vector<CnDirectorySelection::Origin> known_refresh_origins(bool native_mode_bit0) const {
            if(operation!=Operation::Refresh94)return {};
            return CnDirectorySelection::known_origins(native_mode_bit0,static_cast<std::uint8_t>(channel));
        }
        std::optional<CnDirectorySelection::Producer> refresh_producer(bool native_mode_bit0) const {
            if(operation!=Operation::Refresh94)return std::nullopt;
            return CnDirectorySelection::producer(native_mode_bit0,static_cast<std::uint8_t>(channel));
        }
    };
    struct Row {
        std::array<std::uint8_t,row_size> bytes;
        struct Mode1Display {
            std::uint16_t wins,losses,draws;
            //005137B0 prints this native sum under ProgramMsg865's total
            // column. Do not add draws or use this presentation as PvP rules.
            std::uint32_t total_matches;
            // Native fourth-column label is積分, but005137B0 prints the
            // very same WORD34 as wins. No independent points field recovered.
            std::uint16_t points_label_value;
        };
        //005118E0 uses this byte as the destination slot, not array ordinal.
        std::uint8_t native_index() const {return bytes[32];}
        //0050EB00 ->ProgramMsg444/865/446/153 headers,00515F80 mode1/2F,
        //005137B0 row renderer. Mode1: player text, affiliated洞府 text,
        // wins/losses/draws. These display strings are never common IDs or
        // proof that a洞府 is the same entity as a particular guild model.
        // Evidence added in cn-directory-display-fields-01. Mode0 meanings
        // and native result issuance/sorting/scoring remain unqualified.
        std::span<const std::uint8_t,16> first_text_bytes() const {return std::span<const std::uint8_t,16>(bytes.data(),16);}
        std::span<const std::uint8_t,16> second_text_bytes() const {return std::span<const std::uint8_t,16>(bytes.data()+16,16);}
        std::uint16_t displayed_word(unsigned field) const {
            if(field>=3)throw std::out_of_range("CN directory displayed word");
            return le16(bytes,34+field*2);
        }
        std::optional<Mode1Display> mode1_display(bool native_mode_bit0) const {
            if(!native_mode_bit0)return std::nullopt;
            const auto wins=displayed_word(0),losses=displayed_word(1),draws=displayed_word(2);
            return Mode1Display{wins,losses,draws,std::uint32_t{wins}+losses,wins};
        }
    };
    struct Page {
        Channel channel;
        std::uint32_t cursor; // B0payload4 ->owner cursor ->later94payload4.
        std::vector<Row> rows;
        Bytes record;
        bool rows_within_initial_clear(bool native_mode_bit0) const {
            const auto view=CnDirectoryReceiver::read(record,native_mode_bit0);
            return view && view->rows_within_initial_clear();
        }
    };
    struct Summary {
        Channel channel;
        std::array<std::uint8_t,24> payload; // Full opaque native header; no missing values filled.
        Bytes record;
        struct Mode1PersonalDisplay {
            // Signed DWORD formatting in005131A0, not recovered counter bounds
            // or a formula deriving results from common battle outcomes.
            std::int32_t wins,losses,draws,points_label_value;
        };
        std::optional<Mode1PersonalDisplay> mode1_personal_display(bool native_mode_bit0) const {
            if(!native_mode_bit0 || channel!=Channel::Selector19)return std::nullopt;
            // AE subtype08 copy ->base30E74+16; displayed+20/24/28
            // corresponds to payload4/8/12.0051325F also passes+20 to the
            // literal積分 label. Keep payload0..3/16..23 opaque, not a score.
            const auto wins=std::bit_cast<std::int32_t>(le32(payload,4));
            return Mode1PersonalDisplay{wins,
                std::bit_cast<std::int32_t>(le32(payload,8)),std::bit_cast<std::int32_t>(le32(payload,12)),
                wins};
        }
    };
    static std::optional<Channel> channel(std::uint8_t value) {
        switch(value) {
        case 0x19:return Channel::Selector19;
        case 0x23:return Channel::Selector23;
        case 0x24:return Channel::Selector24;
        default:return std::nullopt;
        }
    }
    static std::optional<Request> read_request(std::span<const std::uint8_t> record) {
        if(record.size()==request_size && record[0]==0x94) {
            const auto selected=channel(record[1]);if(!selected)return std::nullopt;
            return Request{*selected,Operation::Refresh94,Bytes(record.begin(),record.end()),le32(record,5),std::nullopt};
        }
        if(record.size()==page_request_size && record[0]==0xa4) {
            const auto selected=channel(record[1]);
            if(!selected || (record[2]!=0xff && record[2]!=1))return std::nullopt;
            return Request{*selected,Operation::PageA4,Bytes(record.begin(),record.end()),std::nullopt,
                record[2]==0xff?-1:1};
        }
        return std::nullopt;
    }
    static std::optional<Page> read_page(std::span<const std::uint8_t> record) {
        // The B0consumer receives record+1, beginning with the uint16 total
        // BlockSize.005118E0's native assertion for selector11 is BlockSize-9
        // ==count*40. Dispatcher framing applies that same length at opcode+1.
        // This source owner's three channels exist in both native modes.
        // Other recovered B0consumer selectors are available through the
        // separate receiver view; no corresponding backend is implied here.
        const auto receiver=CnDirectoryReceiver::read(record,false);if(!receiver)return std::nullopt;
        const auto selected=channel(record[3]);if(!selected)return std::nullopt;
        Page result{*selected,le32(record,5),{},Bytes(record.begin(),record.end())};
        result.rows.reserve(record[4]);
        for(std::size_t offset=page_header_size;offset<record.size();offset+=row_size) {
            Row row;std::copy_n(record.begin()+offset,row_size,row.bytes.begin());result.rows.push_back(row);
        }
        return result;
    }
    static std::optional<Summary> read_summary(std::span<const std::uint8_t> record) {
        if(record.size()!=summary_size || record[0]!=0xae)return std::nullopt;
        std::optional<Channel> selected;
        switch(record[1]) {
        case 8:selected=Channel::Selector19;break;
        case 11:selected=Channel::Selector23;break;
        case 12:selected=Channel::Selector24;break;
        default:return std::nullopt;
        }
        Summary result{*selected,{},Bytes(record.begin(),record.end())};
        std::copy(record.begin()+1,record.end(),result.payload.begin());return result;
    }
private:
    static std::uint16_t le16(std::span<const std::uint8_t> bytes,std::size_t offset) {
        return static_cast<std::uint16_t>(bytes[offset]|(std::uint16_t{bytes[offset+1]}<<8));
    }
    static std::uint32_t le32(std::span<const std::uint8_t> bytes,std::size_t offset) {
        return std::uint32_t{bytes[offset]}|(std::uint32_t{bytes[offset+1]}<<8)|
            (std::uint32_t{bytes[offset+2]}<<16)|(std::uint32_t{bytes[offset+3]}<<24);
    }
};
}
