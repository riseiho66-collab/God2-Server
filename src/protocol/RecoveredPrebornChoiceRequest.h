#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace god2 {
// Shared TW/CN C2S staged-choice structural grammar only.
// Same149c 4FEEC0 queues 4FF230(C81), then 4FECD0(C83);
// pinned CN preborn534810 queues the same2B81/3+2N83 layouts.
// Actual CN splitter/receiver delegates here while retaining its own value
// adapter, phase/issuer/operation/reply. Separate from C28 and S2C battle83.
// C83's complete initialized layout requires stable native source counts,
// readable pointers and sufficient output storage; the native sender supplies
// no universal count bound. Structural acceptance grants no phase or action.
struct RecoveredPrebornChoiceRequest {
    static constexpr std::uint8_t mask_opcode=0x81,words_opcode=0x83;
    class Mask {
    public:
        using LogicalRecord=std::array<std::uint8_t,2>;
        const LogicalRecord& raw() const noexcept {return raw_;}
        std::uint8_t mask() const noexcept {return raw_[1];}
        bool operator==(const Mask&) const=default;
    private:
        friend struct RecoveredPrebornChoiceRequest;
        explicit Mask(LogicalRecord raw):raw_(raw) {}
        LogicalRecord raw_;
    };
    class Words {
    public:
        const std::vector<std::uint8_t>& raw() const noexcept {return raw_;}
        std::size_t word_count() const noexcept {return raw_.size()<3?0:(raw_.size()-3)/2;}
        std::optional<std::uint16_t> word_at(std::size_t index) const noexcept {
            if(index>=word_count())return std::nullopt;
            const auto at=3+2*index;
            return static_cast<std::uint16_t>(std::uint16_t{raw_[at]}|
                (std::uint16_t{raw_[at+1]}<<8));
        }
        bool operator==(const Words&) const=default;
    private:
        friend struct RecoveredPrebornChoiceRequest;
        explicit Words(std::span<const std::uint8_t> raw):raw_(raw.begin(),raw.end()) {}
        // Exact self-length and every ordered raw WORD, including zero and
        // duplicates. Actual pointer namespace/issuer/rights remain separate.
        std::vector<std::uint8_t> raw_;
    };
    static std::optional<std::size_t> request_size(std::span<const std::uint8_t> rest) noexcept {
        if(rest.empty())return std::nullopt;
        if(rest[0]==mask_opcode)
            return rest.size()>=2?std::optional<std::size_t>{2}:std::nullopt;
        if(rest[0]!=words_opcode || rest.size()<3)return std::nullopt;
        const auto size=std::size_t(rest[1])+(std::size_t(rest[2])<<8);
        if(size<3 || (size-3)%2 || size>rest.size())return std::nullopt;
        return size;
    }
    static std::optional<Mask> decode_mask(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=2 || raw[0]!=mask_opcode)return std::nullopt;
        return Mask(Mask::LogicalRecord{raw[0],raw[1]});
    }
    static std::optional<Words> decode_words(std::span<const std::uint8_t> raw) {
        if(raw.empty() || raw[0]!=words_opcode)return std::nullopt;
        const auto size=request_size(raw);
        if(!size || *size!=raw.size())return std::nullopt;
        return Words(raw);
    }
};
}
