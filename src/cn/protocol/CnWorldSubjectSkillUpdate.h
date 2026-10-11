#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Pinned WORLD0048FCC0 cases34/35 ->004D5E60/004D5CC0, size4.
// This scope does not install BATTLE's same opcode values or infer C2S pairs.
struct CnWorldSubjectSkillUpdate {
    enum class Form:std::uint8_t {Native34=0x34,Native35=0x35};
    struct Record {
        Form form;
        std::array<std::uint8_t,4> raw;
        std::uint8_t subject_identifier() const {return raw[1];}
        std::uint8_t kind() const {return raw[2];}
        std::uint8_t definition_id() const {return raw[3];}
    };
    // Preserve malformed semantic operands too: only the frame is parsed.
    // ID0 reaches a native assertion branch, not a server-granted skill.
    static std::optional<Record> read(std::span<const std::uint8_t> record) {
        if(record.size()!=4 || (record[0]!=0x34 && record[0]!=0x35))return std::nullopt;
        return Record{static_cast<Form>(record[0]),{record[0],record[1],record[2],record[3]}};
    }
    // Actual authority supplies every operand after rule/save/replay settlement.
    // A native subject byte is not a common character ID or a selection slot.
    static std::optional<Record> make(Form form,std::uint8_t actual_native_subject,
        std::uint8_t actual_kind,std::uint8_t actual_definition_id) {
        const auto op=static_cast<std::uint8_t>(form);
        const std::array<std::uint8_t,4> raw={op,actual_native_subject,actual_kind,actual_definition_id};
        return read(raw);
    }
};
}
