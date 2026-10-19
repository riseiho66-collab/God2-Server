#pragma once
#include "net/Session.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <utility>
#include <vector>

namespace god2 {
class LegacyTaiwanOwnedDeitySelectionRegistry;
class LegacyWorldReply;

// One actual decoded prefix frame. The private emission follows its original
// complete source frame; logical bytes alone cannot manufacture that source.
class LegacyWorldReplyFrame final {
public:
    LegacyWorldReplyFrame(const LegacyWorldReplyFrame&)=delete;
    LegacyWorldReplyFrame& operator=(const LegacyWorldReplyFrame&)=delete;
    LegacyWorldReplyFrame(LegacyWorldReplyFrame&& other) noexcept
        :logical_(std::move(other.logical_)),emission_(other.emission_) {other.emission_.reset();}
    LegacyWorldReplyFrame& operator=(LegacyWorldReplyFrame&& other) noexcept {
        if(this!=&other){logical_=std::move(other.logical_);emission_=other.emission_;other.emission_.reset();}
        return *this;
    }
    const std::vector<std::uint8_t>& logical()const noexcept{return logical_;}
private:
    friend class Session;
    friend class LegacyWorldReply;
    LegacyWorldReplyFrame(std::vector<std::uint8_t> logical,
            const std::optional<Session::WorldCallbackSelectionEmission>& emission)
        :logical_(std::move(logical)),emission_(emission) {}
    std::vector<std::uint8_t> logical_;
    std::optional<Session::WorldCallbackSelectionEmission> emission_;
};

// Local legacy dispatcher return only. Plain bytes remain plain. A private
// C67 producer is the sole tag origin; append/split preserve that occurrence
// without reconstructing it from matching bytes or changing the old sender.
class LegacyWorldReply final {
public:
    LegacyWorldReply(std::vector<std::uint8_t> wire):wire_(std::move(wire)) {}
    LegacyWorldReply(const LegacyWorldReply&)=delete;
    LegacyWorldReply& operator=(const LegacyWorldReply&)=delete;
    LegacyWorldReply(LegacyWorldReply&&)noexcept=default;
    LegacyWorldReply& operator=(LegacyWorldReply&&)noexcept=default;
    const std::vector<std::uint8_t>& wire()const noexcept{return wire_;}
    bool empty()const noexcept{return wire_.empty();}
    std::size_t size()const noexcept{return wire_.size();}
    bool has_emissions()const noexcept{return !ranges_.empty();}

    void append(LegacyWorldReply child) {
        if(child.wire_.size()>wire_.max_size()-wire_.size() ||
           child.ranges_.size()>ranges_.max_size()-ranges_.size())
            throw std::length_error("Legacy reply append exceeds storage bounds");
        const auto base=wire_.size();
        auto next_wire=wire_;auto next_ranges=ranges_;
        next_wire.insert(next_wire.end(),child.wire_.begin(),child.wire_.end());
        next_ranges.reserve(ranges_.size()+child.ranges_.size());
        for(const auto& range:child.ranges_) {
            if(range.wire_offset>=child.wire_.size())throw std::logic_error("Legacy child tag outside source wire");
            next_ranges.emplace_back(range.emission,base+range.wire_offset);
        }
        wire_.swap(next_wire);ranges_.swap(next_ranges); // Both complete candidates precede mutation.
    }

    std::optional<std::vector<LegacyWorldReplyFrame>> split_frames() && {
        std::vector<LegacyWorldReplyFrame> result;std::size_t next=0;
        for(std::size_t offset=0;offset<wire_.size();) {
            if(wire_.size()-offset<2)return {};
            const auto length=std::size_t(wire_[offset])+256u*wire_[offset+1];
            if(length<4 || length>wire_.size()-offset)return {};
            const auto frame=std::span<const std::uint8_t>(wire_).subspan(offset,length);
            auto logical=RecoveredWorldFrame::decode(frame);if(!logical)return {};
            std::optional<Session::WorldCallbackSelectionEmission> emission;
            if(next<ranges_.size()) {
                const auto& range=ranges_[next];
                if(range.wire_offset<offset)return {};
                if(range.wire_offset==offset) {
                    const auto& expected=range.emission.expected_wire();
                    if(expected.size()!=length || !std::equal(expected.begin(),expected.end(),frame.begin()) ||
                       logical->size()!=29 || logical->front()!=0x31)return {};
                    emission.emplace(range.emission);++next;
                }
                // Tags identify complete frames. No interior offset, duplicate
                // source frame or encrypted-byte-to-logical offset guess.
                if(next<ranges_.size() && ranges_[next].wire_offset<offset+length)return {};
            }
            result.push_back(LegacyWorldReplyFrame(std::move(*logical),emission));offset+=length;
        }
        if(next!=ranges_.size())return {};
        wire_.clear();ranges_.clear(); // Successful consuming split cannot hand off the same tags again.
        return result;
    }

    // Old raw APIs may extract only genuinely untagged replies. The actual
    // Session final handoff is the separate friend that binds private ranges.
    std::vector<std::uint8_t> take_plain_wire() && {
        if(has_emissions())throw std::logic_error("Raw legacy reply would discard causal emission");
        return std::move(wire_);
    }
private:
    friend class Session;
    friend class LegacyTaiwanOwnedDeitySelectionRegistry;
    struct Range {
        Session::WorldCallbackSelectionEmission emission;
        std::size_t wire_offset;
        Range(const Session::WorldCallbackSelectionEmission& source,std::size_t offset)
            :emission(source),wire_offset(offset) {}
    };
    explicit LegacyWorldReply(const Session::WorldCallbackSelectionEmission& emission)
        :wire_(emission.expected_wire()) {
        const auto logical=RecoveredWorldFrame::decode(wire_);
        if(wire_.size()!=32 || !logical || logical->size()!=29 || logical->front()!=0x31)
            throw std::logic_error("Private selection emission is not its complete S31 frame");
        ranges_.emplace_back(emission,0);
    }
    std::vector<std::uint8_t> wire_;
    std::vector<Range> ranges_;
};
}
