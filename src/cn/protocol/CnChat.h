#pragma once
#include "cn/protocol/CnTransport.h"
#include <algorithm>
#include <array>
#include <optional>
#include <stdexcept>
#include <string>

namespace god2cn {
// CN producer 004B1706 -> 00481440. CN receiver 0048FCC0 case 0x5c,
// 005485F0 case 0x5c. This is not imported Taiwan packet evidence.
struct CnChat {
    struct Request {
        std::uint8_t channel{};
        std::uint8_t claimed_language_tag{};
        std::uint8_t reserved{};
        // Byte5 word varies by producer/channel; not proven to be a player ID.
        std::uint16_t opaque_word{};
        std::string text;
    };
    static std::optional<Request> parse(std::span<const std::uint8_t> record) {
        if(record.size()<9 || record.size()>262 || record[0]!=0x2f ||
            static_cast<std::size_t>(record[1])+256u*record[2]!=record.size() || record.back()!=0 ||
            record[7]==0 || std::find(record.begin()+7,record.end()-1,0)!=record.end()-1)return std::nullopt;
        Request result{static_cast<std::uint8_t>(record[3]&0x7f),static_cast<std::uint8_t>(record[3]>>7),
            record[4],static_cast<std::uint16_t>(record[5]+256u*record[6]),{}};
        result.text.assign(record.begin()+7,record.end()-1);return result;
    }
    // Only a complete native record may supply the still-opaque header. This
    // supports recipient text projection, not construction of a guessed reply.
    class Reply {
    public:
        static constexpr std::size_t text_offset=13;
        // 0047D8D0 rejects variable logical records >=0xA00.
        static constexpr std::size_t max_text_bytes=0x9ff-text_offset-1;
        std::uint32_t actor() const {
            std::uint32_t value=0;
            for(unsigned i=0;i<4;++i)value|=std::uint32_t(record_[5+i])<<(8*i);
            return value;
        }
        std::uint8_t channel() const {return record_[9]&0x7f;}
        std::uint8_t language_tag() const {return record_[9]>>7;}
        std::string_view text() const {
            return {reinterpret_cast<const char*>(record_.data()+text_offset),record_.size()-text_offset-1};
        }
        Bytes replace_text(std::string_view text,std::uint8_t consumer_language_tag) const {
            if(text.size()>max_text_bytes || text.find('\0')!=std::string_view::npos || consumer_language_tag>1)
                throw std::invalid_argument("CN native chat reply text bounds");
            Bytes result(record_.begin(),record_.begin()+text_offset);
            result.insert(result.end(),text.begin(),text.end());result.push_back(0);
            result[1]=static_cast<std::uint8_t>(result.size());
            result[2]=static_cast<std::uint8_t>(result.size()>>8);
            result[9]=static_cast<std::uint8_t>(channel()|(consumer_language_tag<<7));
            // Preserve bytes3..4, actor5..8 and bytes10..12 verbatim.
            return result;
        }
    private:
        friend struct CnChat;
        explicit Reply(std::span<const std::uint8_t> record):record_(record.begin(),record.end()){}
        Bytes record_;
    };
    static std::optional<Reply> read_reply(std::span<const std::uint8_t> record) {
        if(record.size()<14 || record.size()>=0xa00 || record[0]!=0x5c ||
           static_cast<std::size_t>(record[1])+256u*record[2]!=record.size() || record.back()!=0 ||
           std::find(record.begin()+13,record.end()-1,0)!=record.end()-1)return std::nullopt;
        return Reply(record);
    }
};
}
