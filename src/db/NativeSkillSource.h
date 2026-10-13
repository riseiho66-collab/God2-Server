#pragma once
#include <cstdint>
#include <string>

namespace god2 {
struct NativeSkillSource {
    std::string dataset_id;
    std::string source_path;
    std::string source_sha256;
    std::string decoded_sha256;
    std::string native_image_sha256;
    std::string source_section;
    std::string loader_rva;
    std::string lookup_rva;
    std::int64_t row_count = 0;

    bool operator==(const NativeSkillSource&) const = default;
};
}
