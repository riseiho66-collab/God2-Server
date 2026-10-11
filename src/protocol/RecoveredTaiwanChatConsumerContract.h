#pragma once
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
// TW world5C consumers475E00/47DE00: complete actual native envelope only.
// This read-only shape/stack-capacity contract supplies no sender mapping,
// permission, renderer handle, loaded graphics/window or cipher authority.
struct RecoveredTaiwanChatConsumerContract {
    class Reply {
    public:
        static constexpr std::size_t text_offset=13;
        Reply(const Reply&)=default;
        Reply& operator=(const Reply&)=default;
        // Retain immutable original storage in both handles after a transfer;
        // a moved-from shape never becomes an empty fictitious native record.
        Reply(Reply&& other) noexcept:record_(other.record_) {}
        Reply& operator=(Reply&& other) noexcept {record_=other.record_;return *this;}
        std::uint32_t actor() const noexcept {
            std::uint32_t value=0;
            for(unsigned i=0;i<4;++i)value|=std::uint32_t((*record_)[5+i])<<(8*i);
            return value; // Full native DWORD, never narrowed to renderer WORD.
        }
        std::uint8_t channel() const noexcept {return (*record_)[9]&0x7f;}
        std::uint8_t language_tag() const noexcept {return (*record_)[9]>>7;}
        // Includes all opaque3/4/10/11/12 bytes without guessed meanings.
        std::span<const std::uint8_t> header() const noexcept {return std::span<const std::uint8_t>(*record_).first(text_offset);}
        std::span<const std::uint8_t> bytes() const noexcept {return *record_;}
        std::string_view text() const noexcept {
            return {reinterpret_cast<const char*>(record_->data()+text_offset),record_->size()-text_offset-1};
        }
    private:
        friend struct RecoveredTaiwanChatConsumerContract;
        explicit Reply(std::span<const std::uint8_t> original)
            :record_(std::make_shared<const std::vector<std::uint8_t>>(original.begin(),original.end())) {}
        std::shared_ptr<const std::vector<std::uint8_t>> record_;
    };
    static std::optional<Reply> read_reply(std::span<const std::uint8_t> original) {
        // Variable record total must remain below native0xA00. Empty native
        // text may be structurally complete; body authority is separate.
        if(original.size()<14 || original.size()>=0xa00 || original[0]!=0x5c ||
           std::size_t(original[1])+256u*original[2]!=original.size() || original.back()!=0 ||
           std::find(original.begin()+Reply::text_offset,original.end()-1,0)!=original.end()-1)return std::nullopt;
        return Reply(original);
    }
    static constexpr std::size_t display_buffer_bytes=256;
    static constexpr std::size_t channel_prefix_bytes=3;
    static std::optional<std::uint8_t> plain_panel_selector(std::uint8_t channel) noexcept {
        // Actual475E00 aliases precede47DE00; wire8/9 are not table slots8/9.
        //47DC66 separately changes each loaded label's first byte to ESC.
        // This describes the selector only, never builds a label/resource.
        switch(channel) {
        case 0:case 8:return 0;
        case 1:return 1;
        case 2:case 9:return 2;
        case 3:return 3;
        case 5:return 5;
        case 6:return 6;
        default:return std::nullopt;
        }
    }
    static std::optional<std::size_t> world_plain_text_budget(std::uint8_t channel) noexcept {
        // Actual47DE00 stack local256 receives table prefix3 + supplied whole
        // text + NUL. Deduct the actual name/body prefix/suffix separately.
        if(plain_panel_selector(channel))return display_buffer_bytes-channel_prefix_bytes-1;
        // Board, structured, timestamp, global and13/18/default consumers have
        // distinct formatter/destination contracts, not this252-byte profile.
        return std::nullopt;
    }
};
}
