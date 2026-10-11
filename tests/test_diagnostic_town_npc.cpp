#include "protocol/DiagnosticTownNpc.h"
#include <iostream>
#include <string>
#include <charconv>
#include <string_view>

static std::uint32_t number(std::string_view input) {
    std::uint32_t value{};
    const auto [end, error] = std::from_chars(input.data(), input.data()+input.size(), value);
    if(error != std::errc{} || end != input.data()+input.size())
        throw std::invalid_argument("Expected an unsigned 32-bit integer");
    return value;
}

int main(int argc,char** argv) {
    try {
        if(argc!=4) return 2;
        const auto record=god2::DiagnosticTownNpc::logical(
            number(argv[1]), number(argv[2]), number(argv[3]));
        constexpr char digits[]="0123456789abcdef";
        for(auto byte:record) std::cout<<digits[byte>>4]<<digits[byte&15];
        std::cout<<'\n';
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
