#pragma once
#include <charconv>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string_view>
namespace god2cn::detail {
inline bool space(unsigned char c) { return c==' ' || c=='\t' || c=='\r' || c=='\n' || c=='\v' || c=='\f'; }
class CnAssetTokens {
public:
    explicit CnAssetTokens(std::span<const std::uint8_t> bytes)
        : bytes_(reinterpret_cast<const char*>(bytes.data()),bytes.size()) {}
    std::string_view next() {
        skip();
        const auto begin=position_;
        while (position_<bytes_.size() && !space(static_cast<unsigned char>(bytes_[position_]))) {
            if (bytes_[position_]=='\0') throw std::invalid_argument("CN model resource embedded NUL");
            ++position_;
        }
        if (begin==position_) throw std::invalid_argument("CN model resource missing token");
        return bytes_.substr(begin,position_-begin);
    }
    void expect(std::string_view expected) {
        const auto token=next();
        if (token.size()!=expected.size()) throw std::invalid_argument("CN model resource section mismatch");
        for (std::size_t i=0; i<token.size(); ++i) {
            const auto lower=[](unsigned char c) { return c>='A' && c<='Z' ? c+('a'-'A') : c; };
            if (lower(static_cast<unsigned char>(token[i]))!=lower(static_cast<unsigned char>(expected[i])))
                throw std::invalid_argument("CN model resource section mismatch");
        }
    }
    std::int32_t integer() {
        auto token=next();
        if (!token.empty() && token.front()=='+') {
            token.remove_prefix(1);
            if (!token.empty() && (token.front()=='-' || token.front()=='+'))
                throw std::invalid_argument("CN model resource invalid integer sign");
        }
        if (token.empty()) throw std::invalid_argument("CN model resource missing integer");
        std::int32_t value{};
        const auto result=std::from_chars(token.data(),token.data()+token.size(),value,10);
        if (result.ec!=std::errc{} || result.ptr!=token.data()+token.size())
            throw std::invalid_argument("CN model resource invalid integer");
        return value;
    }
    std::size_t count() {
        const auto value=integer();
        // Remaining byte count bounds allocation before any count-driven loop.
        if (value<0 || static_cast<std::size_t>(value)>bytes_.size()-position_)
            throw std::invalid_argument("CN model resource invalid record count");
        return static_cast<std::size_t>(value);
    }
    std::size_t remaining() const noexcept { return bytes_.size()-position_; }
    // Native MDT reads optional ROM/action integers with fgets after the
    // required fields. Do not let those optional fields consume the next row.
    std::string_view line_remainder() {
        const auto begin=position_;
        while (position_<bytes_.size() && bytes_[position_]!='\n') {
            if (bytes_[position_]=='\0') throw std::invalid_argument("CN asset line contains NUL");
            ++position_;
        }
        const auto line=bytes_.substr(begin,position_-begin);
        if (position_<bytes_.size()) ++position_;
        return line;
    }
    bool empty() { skip(); return position_==bytes_.size(); }
    void finish() { skip(); if (position_!=bytes_.size()) throw std::invalid_argument("CN model resource trailing data"); }
private:
    void skip() { while (position_<bytes_.size() && space(static_cast<unsigned char>(bytes_[position_]))) ++position_; }
    std::string_view bytes_;
    std::size_t position_=0;
};
}
