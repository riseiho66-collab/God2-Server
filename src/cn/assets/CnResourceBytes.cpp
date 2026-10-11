#include "cn/assets/CnResourceBytes.h"
#include <array>
#include <bitset>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <optional>
#include <ctime>
#include <utility>
#ifdef _WIN32
#include <Windows.h>
#endif

namespace god2cn {
namespace {
std::vector<std::uint8_t> read_open_asset_stream(std::ifstream& input,std::size_t max_encoded_bytes) {
    const std::streamoff length=input.tellg();
    if (length<0) throw std::runtime_error("CN asset file length unavailable");
    const auto size=static_cast<std::uintmax_t>(length);
    if (size>max_encoded_bytes || size>static_cast<std::uintmax_t>(std::numeric_limits<std::streamsize>::max()))
        throw std::length_error("CN asset file exceeds input budget");
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(size));
    input.seekg(0);
    if (!bytes.empty() && !input.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size())))
        throw std::runtime_error("CN asset file read incomplete");
    if (input.peek()!=std::char_traits<char>::eof() || input.bad())
        throw std::runtime_error("CN asset file changed during read");
    return bytes;
}
#ifdef _WIN32
std::optional<std::int64_t> native_modified_seconds(const std::filesystem::path& path) {
    WIN32_FILE_ATTRIBUTE_DATA data{};
    if (!GetFileAttributesExW(path.c_str(),GetFileExInfoStandard,&data)) return std::nullopt;
    //00582A04 uses the modification FILETIME.00582BB7's conversion failure
    // stores zero;005822A2/00582318/00582370 produce local mktime64 seconds.
    FILETIME local_file{};
    SYSTEMTIME probe{},utc{},local{};
    if (!FileTimeToLocalFileTime(&data.ftLastWriteTime,&local_file) ||
        !FileTimeToSystemTime(&local_file,&probe)) return std::int64_t{0};
    if (!FileTimeToSystemTime(&data.ftLastWriteTime,&utc) ||
        !SystemTimeToTzSpecificLocalTime(nullptr,&utc,&local))
        throw std::runtime_error("CN native resource timestamp conversion unavailable");
    if (local.wYear<1900) return std::int64_t{0};
    if (local.wYear<1970) throw std::runtime_error("CN native resource timestamp outside supported era");
    std::tm value{};
    value.tm_year=local.wYear-1900; value.tm_mon=local.wMonth-1; value.tm_mday=local.wDay;
    value.tm_hour=local.wHour; value.tm_min=local.wMinute; value.tm_sec=local.wSecond;
    value.tm_isdst=-1;
    const auto seconds=_mktime64(&value);
    if (seconds==-1) throw std::runtime_error("CN native resource timestamp unavailable");
    return seconds;
}
#endif
}
CnSelectedResource read_cn_preferred_resource(const std::filesystem::path& plain,std::size_t budget) {
    auto wrapped=plain; wrapped+="Z";
    if (std::filesystem::exists(wrapped)) {
        auto bytes=read_cn_asset_file(wrapped,budget);
        if (bytes.size()>=2 && bytes[0]==0x05 && bytes[1]==0x16)
            return {std::move(wrapped),std::move(bytes)};
    }
    return {plain,read_cn_asset_file(plain,budget)};
}
CnSelectedResource read_cn_rom_resource(const std::filesystem::path& original,std::size_t budget) {
    auto candidate=original;
    const auto filename=original.filename().native();
    if(filename.size()<4)throw std::invalid_argument("CN ROM short filename branch unqualified");
    if(filename[filename.size()-4]==static_cast<std::filesystem::path::value_type>('.'))candidate+="Z";
    std::ifstream probe(candidate,std::ios::binary|std::ios::ate);
    if(probe) {
        auto bytes=read_open_asset_stream(probe,budget);
        if(bytes.size()>=2 && bytes[0]==5 && bytes[1]==0x16)return {std::move(candidate),std::move(bytes)};
        // The supplied .romz can also be a plain file. The immutable read is
        // already the exact fallback input; do not add an extraZ suffix.
        if(candidate==original)return {original,std::move(bytes)};
    }
    return {original,read_cn_asset_file(original,budget)};
}
CnSelectedResource read_cn_mbd_resource(const std::filesystem::path& plain,std::size_t budget) {
    auto wrapped=plain; wrapped+="Z";
    bool use_wrapped=!std::filesystem::exists(plain);
    if (!use_wrapped) {
#ifdef _WIN32
        const auto z_time=native_modified_seconds(wrapped);
        const auto plain_time=native_modified_seconds(plain);
        // Native skips refresh when either GetStatus fails; equal keeps plain.
        use_wrapped=z_time && plain_time && *z_time>*plain_time;
#else
        throw std::runtime_error("CN native MBD timestamp selection requires Windows");
#endif
    }
    const auto& chosen=use_wrapped ? wrapped : plain;
    auto bytes=read_cn_asset_file(chosen,budget);
    if (use_wrapped && (bytes.size()<2 || bytes[0]!=0x05 || bytes[1]!=0x16))
        throw std::invalid_argument("CN selected MBD Z wrapper unavailable");
    return {chosen,std::move(bytes)};
}
std::vector<std::uint8_t> read_cn_asset_file(const std::filesystem::path& path,
    std::size_t max_encoded_bytes) {
    std::ifstream input(path,std::ios::binary|std::ios::ate);
    if (!input) throw std::runtime_error("CN asset file unavailable");
    return read_open_asset_stream(input,max_encoded_bytes);
}
std::optional<std::vector<std::uint8_t>> try_read_cn_plain_map_file(
    const std::filesystem::path& path,std::size_t max_encoded_bytes) {
    std::ifstream input(path,std::ios::binary|std::ios::ate);
    if(!input)return std::nullopt;
    return read_open_asset_stream(input,max_encoded_bytes);
}
std::vector<std::uint8_t> decode_cn_resource(std::span<const std::uint8_t> bytes,
    std::size_t max_plain_bytes) {
    if (bytes.size() < 2 || bytes[0] != 0x05 || bytes[1] != 0x16) {
        if (bytes.size() > max_plain_bytes) throw std::length_error("CN plain resource exceeds budget");
        return {bytes.begin(), bytes.end()};
    }
    if (bytes.size() < 7) throw std::invalid_argument("CN compressed resource header truncated");
    const auto expected = std::uint32_t(bytes[2]) | (std::uint32_t(bytes[3]) << 8) |
        (std::uint32_t(bytes[4]) << 16) | (std::uint32_t(bytes[5]) << 24);
    if (expected > max_plain_bytes) throw std::length_error("CN decoded resource exceeds budget");
    // Native initializes the first FEE bytes only. Never invent values for an
    // uninitialized back-reference, even if the local C++ array is zeroed.
    std::array<std::uint8_t, 4096> ring{};
    std::bitset<4096> initialized;
    for (std::size_t i=0; i<0xfee; ++i) { ring[i]=0x20; initialized.set(i); }
    std::size_t cursor=0xfee, offset=7;
    std::uint32_t flags=0;
    std::vector<std::uint8_t> plain;
    plain.reserve(expected);
    const auto append = [&](std::uint8_t value) {
        if (plain.size() >= expected) throw std::invalid_argument("CN resource exceeds declared length");
        plain.push_back(value);
        ring[cursor]=value;
        initialized.set(cursor);
        cursor=(cursor+1)&0xfff;
    };
    while (offset < bytes.size()) {
        flags >>= 1;
        if ((flags&0x100)==0) {
            flags=bytes[offset++]|0xff00;
            if (offset==bytes.size()) break;
        }
        const auto first=bytes[offset++];
        if ((flags&1)!=0) { append(first); continue; }
        // Native exits to its declared-length check if token byte2 is absent.
        if (offset==bytes.size()) break;
        const auto second=bytes[offset++];
        const std::size_t position=first|((second&0xf0)<<4);
        const std::size_t length=(second&0xf)+3;
        for (std::size_t i=0; i<length; ++i) {
            const auto source=(position+i)&0xfff;
            if (!initialized.test(source))
                throw std::invalid_argument("CN resource references uninitialized native bytes");
            append(ring[source]);
        }
    }
    if (plain.size()!=expected) throw std::invalid_argument("CN decoded resource length mismatch");
    return plain;
}
}
