#include "protocol/RecoveredQuestRewardNotice.h"
#include <charconv>
#include <cstdio>
#include <stdexcept>
#include <string_view>

using Notice = god2::RecoveredQuestRewardNotice;
static void require(bool ok) { if (!ok) throw std::runtime_error("reward notice test failure"); }
static std::uint64_t number(std::string_view text) {
    std::uint64_t value{};
    const auto result = std::from_chars(text.data(), text.data()+text.size(), value);
    if(result.ec != std::errc{} || result.ptr != text.data()+text.size())
        throw std::invalid_argument("decimal argument");
    return value;
}
int main(int argc, char** argv) {
    try {
        if(argc == 4 && std::string_view(argv[1]) == "--dump") {
            const auto id = number(argv[2]);
            if(id != 626 && id != 644) throw std::invalid_argument("message id");
            const auto wire = Notice::logical(static_cast<Notice::Kind>(id), number(argv[3]));
            for(const auto byte : wire) std::printf("%02x", static_cast<unsigned>(byte));
            std::puts(""); return 0;
        }
        if(argc != 1) throw std::invalid_argument("arguments");
        for(const auto kind : {Notice::Kind::Reputation, Notice::Kind::Experience}) {
            for(const std::uint64_t amount : {1ULL, 9ULL, 10ULL, 400ULL, 1500ULL, 2000ULL, 3000ULL,
                                            999999999999999ULL}) {
                const auto wire=Notice::logical(kind, amount);
                const auto id=static_cast<std::uint16_t>(kind);
                require(wire[0]==2 && wire[1]==(id&255) && wire[2]==(id>>8));
                require(!wire[3] && !wire[4] && !wire[21] && !wire[22]);
                unsigned end=5; while(end<21 && wire[end]) ++end;
                require(end<21 && end>5);
                require(number(std::string_view(reinterpret_cast<const char*>(wire.data()+5),end-5))==amount);
                for(unsigned i=end;i<21;++i)require(!wire[i]);
            }
            for(const std::uint64_t bad : {0ULL,1000000000000000ULL,UINT64_MAX}) {
                bool rejected=false;
                try { (void)Notice::logical(kind,bad); } catch(const std::invalid_argument&) { rejected=true; }
                require(rejected);
            }
        }
        bool rejected=false;
        try { (void)Notice::logical(static_cast<Notice::Kind>(27),1); }
        catch(const std::invalid_argument&) { rejected=true; }
        require(rejected);
        std::puts("PASS reward notice codec"); return 0;
    } catch(const std::exception& e) { std::fprintf(stderr,"%s\n",e.what()); return 1; }
}
