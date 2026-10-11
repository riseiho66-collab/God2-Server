#pragma once
#include <filesystem>
#include <string>
#include <string_view>
#include <unordered_map>

namespace god2 {
enum class ChineseLanguage { Traditional, Simplified };

// CUSTOM-0029: UTF-8 OpenCC dictionary conversion for server-owned text.
// Script conversion is distinct from translation of meaning or native wire encoding.
class ChineseText {
public:
    explicit ChineseText(const std::filesystem::path& dictionary_root);
    std::string convert(std::string_view utf8,ChineseLanguage target) const;
    std::string convert_dialogue_json(std::string_view json,ChineseLanguage target) const;
    static bool valid_utf8(std::string_view utf8) noexcept;
private:
    struct Dictionary {
        std::unordered_map<std::string,std::string> entries;
        std::size_t max_key_bytes=0;
    };
    Dictionary traditional_,simplified_;
    static void load(Dictionary& into,const std::filesystem::path& file);
};
}
