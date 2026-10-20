#pragma once
#include <filesystem>
#include <iosfwd>
#include <optional>
#include <span>

namespace god2 {
struct Config;
struct WebServerPlan;
// Explicit Main hosting options, not a native destination or a channel grant.
struct WebMainOptions {
    using Argument=std::filesystem::path::string_type;
    std::filesystem::path config_path="config/server.json";
    std::filesystem::path web_config_path;
    unsigned run_for_seconds{};
    bool help{};
    // Pure parser. Arguments include argv[0]; no file/DB/logger/network access.
    static std::optional<WebMainOptions> parse(std::span<const Argument>);
    // Preserve native Windows Unicode argv only after explicit web opt-in.
    static std::optional<WebMainOptions> parse_if_requested(int argc,char** argv);
    static void write_help(std::ostream&);
};
// Static single-G Main prerequisites only. Real bound destinations remain in
// Application; this does not build a three-world factory or open any listener.
void validate_web_main_host(const Config&,const WebServerPlan&);
}
