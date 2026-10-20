#pragma once
#include <filesystem>
#include <iosfwd>
#include <optional>
#include <cstdint>
namespace god2 {
class OwnedBankCapacityOperator final {
public:
    struct Options {
        bool provision=false,help=false;
        std::filesystem::path config_path="config/server.json",manifest_path,output_path;
        std::uint64_t account=0,character=0;
    };
    static std::optional<Options> parse_if_requested(int,char**);
    static void write_help(std::ostream&);
    static int run(const Options&);
};
}
