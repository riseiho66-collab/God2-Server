#pragma once
#include <filesystem>
#include <iosfwd>
#include <optional>
namespace god2 {
// Explicit process-local data operator, never a native gameplay command.
class TaiwanSkillImportOperator final {
public:
    struct Options {
        std::filesystem::path config_path="config/server.json";
        std::filesystem::path client_root;
        bool help=false;
    };
    // Absence of the ASCII opt-in returns null without changing legacy CLI
    // argument/path handling. Only this mode takes actual Windows wide paths.
    static std::optional<Options> parse_if_requested(int argc,char** argv);
    static void write_help(std::ostream&);
    static int run(const Options&);
private:
    TaiwanSkillImportOperator()=delete;
};
}
