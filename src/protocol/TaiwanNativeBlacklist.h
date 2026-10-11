#pragma once
#include <algorithm>
#include <cstdint>
#include <cstddef>
#include <optional>
#include <span>
#include <string_view>
#include <utility>
#include <vector>
namespace god2 {
// Same149c C89/8A and S A5/A4 shapes only. Row DWORD is a contact-row
// namespace, never a common character ID or permission. C89's unused stack
// tail after the first NUL is retained, not required to be zero.
struct TaiwanNativeBlacklist {
    static constexpr std::uint8_t add_opcode=0x89,remove_opcode=0x8a;
    static constexpr std::size_t add_size=17,remove_size=5;
    class Request {
    public:
        bool adding() const noexcept {return logical_[0]==add_opcode;}
        const std::vector<std::uint8_t>& logical() const noexcept {return logical_;}
        std::string_view name() const noexcept {
            return adding()?std::string_view(reinterpret_cast<const char*>(logical_.data()+1),name_size_):std::string_view{};
        }
        std::uint32_t row_id() const noexcept {
            return adding()?0:std::uint32_t(logical_[1])|(std::uint32_t(logical_[2])<<8)|
                (std::uint32_t(logical_[3])<<16)|(std::uint32_t(logical_[4])<<24);
        }
    private:
        friend struct TaiwanNativeBlacklist;
        Request(std::vector<std::uint8_t> bytes,std::size_t name_size)
            :logical_(std::move(bytes)),name_size_(name_size) {}
        std::vector<std::uint8_t> logical_;
        std::size_t name_size_;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) {
        if(bytes.size()==remove_size && bytes[0]==remove_opcode)
            return Request(std::vector<std::uint8_t>(bytes.begin(),bytes.end()),0);
        if(bytes.size()!=add_size || bytes[0]!=add_opcode)return {};
        const auto end=std::find(bytes.begin()+1,bytes.end(),0);
        const auto count=std::size_t(end-(bytes.begin()+1));
        if(end==bytes.end() || !count || count>14)return {};
        return Request(std::vector<std::uint8_t>(bytes.begin(),bytes.end()),count);
    }
    static std::optional<std::vector<std::uint8_t>> added(std::uint32_t row,std::string_view name) {
        if(!row || row==0xffffffffu || name.empty() || name.size()>14 || name.find('\0')!=name.npos)return {};
        std::vector<std::uint8_t> bytes(21,0);bytes[0]=0xa5;
        for(unsigned i=0;i<4;++i)bytes[i+1]=std::uint8_t(row>>(8*i));
        std::copy(name.begin(),name.end(),bytes.begin()+5);return bytes;
    }
    static std::optional<std::vector<std::uint8_t>> removed(std::uint32_t row) {
        if(!row || row==0xffffffffu)return {};
        std::vector<std::uint8_t> bytes(5);bytes[0]=0xa4;
        for(unsigned i=0;i<4;++i)bytes[i+1]=std::uint8_t(row>>(8*i));return bytes;
    }
};
}
