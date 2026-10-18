#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <utility>
#include <vector>

namespace god2 {
// Current aaf0 client48A610 ->4132E0: D5, logical-size WORD, raw identity WORDs.
// N comes from copy-object+D456, not its current selected count+D458.
// This is the self-consistent, nonwrapped logical-record subset. The producer
// has no proved N cap; its stack geometry is not a server skill-count limit.
// Shape/identity bytes grant no learning, ownership, casting, save or reply.
struct RecoveredSkillSelectionRequest {
    static constexpr std::uint8_t opcode=0xd5;
    static constexpr std::size_t prefix_size=3;
    static constexpr bool runtime_emission_enabled=false;
    static constexpr bool runtime_mutation_enabled=false;
    static constexpr char image_sha256[]=
        "aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48";

    class Request {
    public:
        const std::vector<std::uint8_t>& raw() const noexcept {return raw_;}
        std::size_t slot_count() const noexcept {
            return raw_.size()<prefix_size ? 0 : (raw_.size()-prefix_size)/2;
        }
        // Keep zero, duplicate and unrecognized identities. In copied source
        // rows the low/high bytes are id/kind; no profile or grant is inferred.
        std::optional<std::uint16_t> raw_identity_word(std::size_t ordinal) const noexcept {
            if(ordinal>=slot_count())return std::nullopt;
            const auto at=prefix_size+2*ordinal;
            return static_cast<std::uint16_t>(std::uint16_t{raw_[at]}|
                (std::uint16_t{raw_[at+1]}<<8));
        }
        bool operator==(const Request&) const=default;
    private:
        friend struct RecoveredSkillSelectionRequest;
        explicit Request(std::vector<std::uint8_t> raw) noexcept:raw_(std::move(raw)) {}
        std::vector<std::uint8_t> raw_;
    };

    // Prefix inspection only; the batch caller must check available bytes.
    static std::optional<std::size_t> record_size(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()<prefix_size || raw[0]!=opcode)return std::nullopt;
        const auto size=std::size_t{raw[1]}|(std::size_t{raw[2]}<<8);
        if(size<prefix_size || (size-prefix_size)%2!=0)return std::nullopt;
        return size;
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> raw) {
        const auto size=record_size(raw);
        if(!size || *size!=raw.size())return std::nullopt;
        return Request(std::vector<std::uint8_t>(raw.begin(),raw.end()));
    }
    static std::vector<std::uint8_t> encode(const Request& request) {
        const auto size=record_size(request.raw());
        if(!size || *size!=request.raw().size())
            throw std::invalid_argument("Invalid or moved-from native D5 record");
        return request.raw();
    }
};
}
