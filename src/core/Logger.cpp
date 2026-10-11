#include "core/Logger.h"
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/rotating_file_sink.h>
#include <cstdlib>
#include <stdexcept>
#include <string_view>
#include <vector>
namespace god2 {
void initialize_logger(const std::filesystem::path& file, const std::string& level) {
    if(!file.parent_path().empty()) std::filesystem::create_directories(file.parent_path());
    auto disk=std::make_shared<spdlog::sinks::rotating_file_sink_mt>(file.string(), 5*1024*1024, 3);
    // A detached server must not let a blocked stdout sink stall the game executor.
    // Keep console output for interactive runs unless the operator selects file-only logging.
    const char* file_only=std::getenv("GOD2_LOG_FILE_ONLY");
    const bool disk_only=file_only && std::string_view(file_only)=="1";
    std::vector<spdlog::sink_ptr> sinks;
    if(!disk_only)
        sinks.push_back(std::make_shared<spdlog::sinks::stdout_color_sink_mt>());
    sinks.push_back(disk);
    const auto severity=spdlog::level::from_str(level);
    if(severity==spdlog::level::off && level!="off") throw std::runtime_error("Unknown logging level");
    for(const auto* channel : {"server","network","session","packet","opcode","database","lua","world","reverse","error"}) {
        auto logger=std::make_shared<spdlog::logger>(channel,sinks.begin(),sinks.end());
        logger->set_level(severity); logger->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%n] [%l] %v");
        logger->flush_on(disk_only?spdlog::level::info:spdlog::level::warn);
        spdlog::register_logger(logger);
    }
    spdlog::set_default_logger(spdlog::get("server"));
}
}
