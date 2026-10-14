#pragma once
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <span>
#include <stdexcept>

namespace god2 {
// Current 654F7..65538 queues nine logical bytes, normally one 12-byte frame.
// Its outbound queue can already hold one native 30/0 heartbeat, producing a
// 14-byte frame. See world-ready-grouped-regression-v01 for current-client proof.
// Accept whole-record grouping across frames and TCP fragmentation, not arbitrary
// packet/order guesses. A completed tail does not certify rendered world entry.
class RecoveredWorldReady {
public:
    enum class Result { NeedMore, Complete, Rejected };
    explicit RecoveredWorldReady(std::uint64_t local_id):local_id_(static_cast<std::uint16_t>(local_id)) {
        if(!local_id || local_id>0x3fff) throw std::invalid_argument("Invalid world-ready local identity");
    }
    Result feed(std::span<const std::uint8_t> bytes) {
        if(terminal_ || bytes.size()>input_.size()-size_) return reject();
        std::copy(bytes.begin(),bytes.end(),input_.begin()+size_);size_+=bytes.size();
        while(size_-consumed_>=2) {
            const auto length=static_cast<std::size_t>(input_[consumed_])+256u*input_[consumed_+1];
            if(length<5 || length>14) return reject();
            if(size_-consumed_<length) return Result::NeedMore;
            const auto logical=RecoveredWorldFrame::decode(std::span(input_).subspan(consumed_,length));
            if(!logical) return reject();
            const auto& decoded=*logical;
            std::size_t at=0;
            const auto logical_size=length-3;
            while(at<logical_size) {
                // One pre-tail heartbeat may be its own frame or share the
                // native outbound queue with the following initializer records.
                if(stage_==0 && at==0 && logical_size-at>=2 && decoded[at]==0x30 && decoded[at+1]==0) {
                    if(pre_tail_tick_) return reject();
                    pre_tail_tick_=true;at+=2;
                    continue;
                }
                if(stage_<2) {
                    if(logical_size-at<2 || decoded[at]!=(stage_==0?0x1f:0x23) || decoded[at+1]!=0)
                        return reject();
                    at+=2;++stage_;
                } else if(stage_==2) {
                    if(logical_size-at!=5 || decoded[at]!=0x1c ||
                       decoded[at+1]+256u*decoded[at+2]!=local_id_ ||
                       decoded[at+3]>1 || decoded[at+4]!=0) return reject();
                    std::copy_n(decoded.begin()+at+1,4,context_payload_.begin());
                    config_flag_=decoded[at+3];at+=5;++stage_;
                } else return reject();
            }
            consumed_+=length;
            if(stage_==3) {
                if(consumed_!=size_) return reject();
                terminal_=true;return Result::Complete;
            }
        }
        return Result::NeedMore;
    }
    std::uint8_t config_flag() const noexcept { return config_flag_; }
    const std::array<std::uint8_t,4>& context_payload()const noexcept {return context_payload_;}
private:
    Result reject() noexcept { terminal_=true;return Result::Rejected; }
    std::uint16_t local_id_;
    // Maximum: four individually framed records (5 + 5 + 5 + 8).
    std::array<std::uint8_t,23> input_{};
    std::size_t size_=0,consumed_=0;
    unsigned stage_=0;
    std::uint8_t config_flag_=0;
    std::array<std::uint8_t,4> context_payload_{}; // Valid only after Complete; exact received C1C.
    bool pre_tail_tick_=false;
    bool terminal_=false;
};
}
