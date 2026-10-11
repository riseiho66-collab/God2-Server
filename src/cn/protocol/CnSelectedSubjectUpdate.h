#pragma once
#include "cn/protocol/CnWorldConsumerRecords.h"
#include <variant>
#include <vector>

namespace god2cn {
// Pinned WORLD33/39 act on the CURRENT selected row at UI+430A8 ->role+D0.
// Neither record identifies a subject; common recipient/selection/order must
// be qualified by the actual owner. These are original widths, not numeric64.
class CnSelectedSubjectUpdate final {
public:
    using FlagRecord=CnWorldConsumerRecord<0x33,2>;
    using PairRecord=CnWorldConsumerRecord<0x39,17>;
    using Row=std::array<std::uint8_t,0x3ec>;
    struct Flag33 {
        std::uint8_t native_row_byte40;
        struct Icon {
            std::uint8_t native_control;
            std::int32_t native_resource_index;
        };
        //004D3E30: only with actual signed UI handle>=0, group1D. High bits
        //are retained in row40 but do not select these four native UI icons.
        std::array<Icon,4> native_icon_operands() const noexcept {
            return {{Icon{0x1a,(native_row_byte40&8)?7:-1},
                     Icon{0x1b,(native_row_byte40&4)?8:-1},
                     Icon{0x1c,(native_row_byte40&2)?9:-1},
                     Icon{0x1d,(native_row_byte40&1)?10:-1}}};
        }
    };
    struct Pairs39 {
        std::uint32_t native_row_dword2C,native_row_dword30;
        std::uint16_t native_row_word34,native_row_word36;
        std::array<std::uint8_t,4> unconsumed_payload_bytes; //6/7/14/15.
        //Native control4 supplies DWORD bits to literal "%d/%d". This is
        //signed presentation, distinct from the preserved unsigned raw bits.
        std::array<std::int32_t,2> native_control4_decimal_arguments() const noexcept {
            return {std::bit_cast<std::int32_t>(native_row_dword2C),
                    std::bit_cast<std::int32_t>(native_row_dword30)};
        }
        //Control5 MOVZX WORD arguments are positive signed32 values.
        std::array<std::int32_t,2> native_control5_decimal_arguments() const noexcept {
            return {native_row_word34,native_row_word36};
        }
    };
    using Fields=std::variant<Flag33,Pairs39>;
    struct Projection {Row original_row,projected_row;};
    static std::optional<CnSelectedSubjectUpdate> read(std::span<const std::uint8_t> bytes) {
        if(const auto record=FlagRecord::parse_logical(bytes))return CnSelectedSubjectUpdate(*record);
        if(const auto record=PairRecord::parse_logical(bytes))return CnSelectedSubjectUpdate(*record);
        return std::nullopt;
    }
    std::vector<std::uint8_t> record_bytes() const {
        return std::visit([](const auto& record) {
            const auto bytes=record.logical_bytes();return std::vector<std::uint8_t>(bytes.begin(),bytes.end());
        },record_);
    }
    Fields native_fields() const noexcept {
        if(const auto flags=std::get_if<FlagRecord>(&record_))return Flag33{flags->payload()[0]};
        const auto bytes=std::get<PairRecord>(record_).payload();
        const auto word=[bytes](std::size_t at) {
            return std::uint16_t(bytes[at])|(std::uint16_t(bytes[at+1])<<8);
        };
        const auto dword=[&word](std::size_t at) {
            return std::uint32_t(word(at))|(std::uint32_t(word(at+2))<<16);
        };
        return Pairs39{dword(0),dword(8),static_cast<std::uint16_t>(word(4)),
            static_cast<std::uint16_t>(word(12)),{bytes[6],bytes[7],bytes[14],bytes[15]}};
    }
    // Read-only operand projection from an actual NONNULL selected row. No
    // zero row/default selection or gameplay mutation is manufactured. Native
    // null selection returns without row/UI updates; actual owner handles it.
    Projection project_actual_selected_row(const Row& actual_row) const noexcept {
        Projection result{actual_row,actual_row};const auto fields=native_fields();
        if(const auto flags=std::get_if<Flag33>(&fields))result.projected_row[0x40]=flags->native_row_byte40;
        else {
            const auto& pairs=std::get<Pairs39>(fields);
            const auto put_word=[&](std::size_t at,std::uint16_t value) {
                result.projected_row[at]=std::uint8_t(value);result.projected_row[at+1]=std::uint8_t(value>>8);
            };
            const auto put_dword=[&](std::size_t at,std::uint32_t value) {
                put_word(at,std::uint16_t(value));put_word(at+2,std::uint16_t(value>>16));
            };
            put_dword(0x2c,pairs.native_row_dword2C);put_dword(0x30,pairs.native_row_dword30);
            put_word(0x34,pairs.native_row_word34);put_word(0x36,pairs.native_row_word36);
        }
        return result;
    }
private:
    explicit CnSelectedSubjectUpdate(FlagRecord record):record_(record) {}
    explicit CnSelectedSubjectUpdate(PairRecord record):record_(record) {}
    std::variant<FlagRecord,PairRecord> record_;
};
}
