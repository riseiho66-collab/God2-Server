#include "text/ChineseText.h"
#include "text/LegacyChineseCodec.h"
#include <stdexcept>
#include <string>
#include <iostream>
#include <nlohmann/json.hpp>

int run() {
    using god2::ChineseLanguage;
    using god2::ChineseText;
    int assertion=0;
    const auto check=[&](bool value) { if(!value) throw std::runtime_error("Chinese text check failed: "+std::to_string(assertion)); ++assertion; };
    const ChineseText converter(std::filesystem::path(GOD2_SOURCE_DIR)/"resources/opencc");
    const auto traditional=converter.convert("汉字游戏",ChineseLanguage::Traditional);
    check(traditional=="漢字遊戲");
    const auto simplified=converter.convert("漢字遊戲",ChineseLanguage::Simplified);
    check(simplified=="汉字游戏");
    check(converter.convert("GOD2 123 /lang",ChineseLanguage::Simplified)=="GOD2 123 /lang");
    const auto dialogue=nlohmann::json::parse(converter.convert_dialogue_json(
        R"({"npc":42,"text":"欢迎遊戲","options":[{"id":7,"text":"开始遊戲"}]})",
        ChineseLanguage::Traditional));
    check(dialogue["npc"]==42 && dialogue["text"]=="歡迎遊戲" &&
        dialogue["options"][0]["id"]==7 && dialogue["options"][0]["text"]=="開始遊戲");
    check(ChineseText::valid_utf8("繁體 / 简体"));
    check(!ChineseText::valid_utf8(std::string("\xc0\xaf",2)));
    const auto traditional_wire=god2::LegacyChineseCodec::encode("漢字遊戲",false);
    const auto simplified_wire=god2::LegacyChineseCodec::encode("汉字游戏",true);
    check(god2::LegacyChineseCodec::decode(traditional_wire,false)=="漢字遊戲");
    check(god2::LegacyChineseCodec::decode(simplified_wire,true)=="汉字游戏");
    check(god2::LegacyChineseCodec::encode(
        converter.convert(god2::LegacyChineseCodec::decode(traditional_wire,false),
            ChineseLanguage::Simplified),true)==simplified_wire);
    const auto unavailable=god2::LegacyChineseCodec::encode_display(
        converter.convert("遊戲‧",ChineseLanguage::Simplified),true);
    check(unavailable.bytes==god2::LegacyChineseCodec::encode("游戏?",true));
    check(unavailable.replacements==1 && !unavailable.truncated);
    const auto bounded=god2::LegacyChineseCodec::encode_display(std::string(300,'a'),false);
    check(bounded.bytes==std::string(254,'a') && bounded.truncated && !bounded.replacements);
    const auto boundary=god2::LegacyChineseCodec::encode_display(std::string(253,'a')+"漢",false);
    check(boundary.bytes==std::string(253,'a') && boundary.truncated);
    bool invalid_rejected=false;
    try { (void)god2::LegacyChineseCodec::encode_display(std::string("\xc0\xaf",2),true); }
    catch(const std::invalid_argument&) { invalid_rejected=true; }
    check(invalid_rejected);
    invalid_rejected=false;
    try { (void)god2::LegacyChineseCodec::encode_display(std::string("a\0b",3),true); }
    catch(const std::invalid_argument&) { invalid_rejected=true; }
    check(invalid_rejected);
    try { (void)converter.convert(std::string("\xed\xa0\x80",3),ChineseLanguage::Traditional); }
    catch(const std::invalid_argument&) { return 0; }
    throw std::runtime_error("Invalid UTF-8 accepted");
}
int main() {
    try { return run(); }
    catch(const std::exception& error) {
        std::cerr<<error.what()<<'\n';
        return 1;
    }
}
