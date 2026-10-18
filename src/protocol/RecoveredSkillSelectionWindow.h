#pragma once
#include "protocol/RecoveredSkillSelectionRequest.h"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <utility>
#include <vector>

namespace god2 {
// Current aaf0 WORLD FC:468AE0/468D2E ->4858B0/485C53 ->489DE0.
// Consumer receives logical+1: total-size WORD, secondary-byte-count WORD,
// primary identity WORDs, then secondary identity WORDs. Native copies may
// dereference unchecked definitions; this view preserves input, not safety or
// eligibility of those copies, learning authority, or guaranteed UI visibility.
struct RecoveredSkillSelectionWindow {
    static constexpr std::uint8_t opcode=0xfc;
    static constexpr std::size_t prefix_size=5;
    static constexpr bool runtime_emission_enabled=false;
    static constexpr bool runtime_mutation_enabled=false;
    static constexpr char image_sha256[]=
        "aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48";

    class Record {
    public:
        const std::vector<std::uint8_t>& raw() const noexcept {return raw_;}
        std::size_t secondary_word_count() const noexcept {
            return raw_.size()<prefix_size ? 0 : word(3)/2;
        }
        std::size_t primary_slot_count() const noexcept {
            if(raw_.size()<prefix_size || word(3)>raw_.size()-prefix_size)return 0;
            return (raw_.size()-prefix_size-word(3))/2;
        }
        std::optional<std::uint16_t> raw_primary_word(std::size_t ordinal) const noexcept {
            if(ordinal>=primary_slot_count())return std::nullopt;
            return word(prefix_size+2*ordinal);
        }
        std::optional<std::uint16_t> raw_secondary_word(std::size_t ordinal) const noexcept {
            if(ordinal>=secondary_word_count())return std::nullopt;
            const auto at=prefix_size+2*(primary_slot_count()+ordinal);
            if(at+1>=raw_.size())return std::nullopt;
            return word(at);
        }
        // Geometry only. Same count does not bind a Session/window generation,
        // authorize any identity, consume an issued window, save or send.
        bool matches_request_slot_count(const RecoveredSkillSelectionRequest::Request& request) const noexcept {
            const auto window_size=RecoveredSkillSelectionWindow::record_size(raw_);
            const auto request_size=RecoveredSkillSelectionRequest::record_size(request.raw());
            return window_size && *window_size==raw_.size() && request_size &&
                *request_size==request.raw().size() && primary_slot_count()==request.slot_count();
        }
        bool operator==(const Record&) const=default;
    private:
        friend struct RecoveredSkillSelectionWindow;
        explicit Record(std::vector<std::uint8_t> raw) noexcept:raw_(std::move(raw)) {}
        std::uint16_t word(std::size_t at) const noexcept {
            return static_cast<std::uint16_t>(std::uint16_t{raw_[at]}|
                (std::uint16_t{raw_[at+1]}<<8));
        }
        std::vector<std::uint8_t> raw_;
    };

    // Self-consistent, nonwrapped subset only; no guessed native count limit.
    // This accessor checks the prefix, not availability of the full payload.
    static std::optional<std::size_t> record_size(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()<prefix_size || raw[0]!=opcode)return std::nullopt;
        const auto size=std::size_t{raw[1]}|(std::size_t{raw[2]}<<8);
        const auto secondary=std::size_t{raw[3]}|(std::size_t{raw[4]}<<8);
        if(size<prefix_size || (size-prefix_size)%2 || secondary%2 ||
           secondary>size-prefix_size)return std::nullopt;
        return size;
    }
    static std::optional<Record> decode(std::span<const std::uint8_t> raw) {
        const auto size=record_size(raw);
        if(!size || *size!=raw.size())return std::nullopt;
        return Record(std::vector<std::uint8_t>(raw.begin(),raw.end()));
    }
    static std::vector<std::uint8_t> encode(const Record& record) {
        const auto size=record_size(record.raw());
        if(!size || *size!=record.raw().size())
            throw std::invalid_argument("Invalid or moved-from native FC window");
        return record.raw();
    }
};
}
