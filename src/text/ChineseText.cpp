#include "text/ChineseText.h"
#include <algorithm>
#include <fstream>
#include <stdexcept>
#include <nlohmann/json.hpp>

namespace god2 {
namespace {
// Return the next UTF-8 boundary, rejecting overlong, surrogate and out-of-range forms.
std::size_t next(std::string_view text,std::size_t at) noexcept {
    if(at>=text.size()) return 0;
    const auto first=static_cast<unsigned char>(text[at]);
    if(first<0x80) return at+1;
    const auto width=first>=0xc2&&first<=0xdf?2u:
        first>=0xe0&&first<=0xef?3u:first>=0xf0&&first<=0xf4?4u:0u;
    if(!width || at+width>text.size()) return 0;
    for(unsigned i=1;i<width;++i)
        if((static_cast<unsigned char>(text[at+i])&0xc0)!=0x80) return 0;
    const auto second=static_cast<unsigned char>(text[at+1]);
    if((first==0xe0&&second<0xa0)||(first==0xed&&second>=0xa0)||
       (first==0xf0&&second<0x90)||(first==0xf4&&second>=0x90)) return 0;
    return at+width;
}
}
bool ChineseText::valid_utf8(std::string_view text) noexcept {
    for(std::size_t at=0;at<text.size();) {
        at=next(text,at);
        if(!at) return false;
    }
    return true;
}
void ChineseText::load(Dictionary& into,const std::filesystem::path& file) {
    std::ifstream input(file,std::ios::binary);
    if(!input) throw std::runtime_error("Cannot open Chinese dictionary: "+file.string());
    std::string line;
    while(std::getline(input,line)) {
        if(!line.empty() && line.back()=='\r') line.pop_back();
        const auto tab=line.find('\t');
        if(tab==std::string::npos || tab==0 || tab+1==line.size())
            throw std::runtime_error("Malformed Chinese dictionary: "+file.string());
        const auto end=line.find(' ',tab+1);
        auto key=line.substr(0,tab);
        auto value=line.substr(tab+1,end==std::string::npos?std::string::npos:end-tab-1);
        if(!valid_utf8(key) || !valid_utf8(value) || value.empty())
            throw std::runtime_error("Invalid Chinese dictionary UTF-8: "+file.string());
        into.max_key_bytes=std::max(into.max_key_bytes,key.size());
        into.entries.try_emplace(std::move(key),std::move(value));
    }
    if(!input.eof() || into.entries.empty())
        throw std::runtime_error("Incomplete Chinese dictionary: "+file.string());
}
ChineseText::ChineseText(const std::filesystem::path& root) {
    // OpenCC s2t/t2s config order: phrase dictionary has precedence over characters.
    load(traditional_,root/"STPhrases.txt");
    load(traditional_,root/"STCharacters.txt");
    load(simplified_,root/"TSPhrases.txt");
    load(simplified_,root/"TSCharacters.txt");
}
std::string ChineseText::convert(std::string_view utf8,ChineseLanguage target) const {
    if(!valid_utf8(utf8)) throw std::invalid_argument("Invalid UTF-8 text");
    const auto& dictionary=target==ChineseLanguage::Traditional?traditional_:simplified_;
    std::string result;
    result.reserve(utf8.size());
    for(std::size_t at=0;at<utf8.size();) {
        const auto first_end=next(utf8,at);
        std::size_t best_end=0;
        const std::string* best=nullptr;
        for(auto end=first_end;end && end-at<=dictionary.max_key_bytes;) {
            if(const auto it=dictionary.entries.find(std::string(utf8.substr(at,end-at)));
               it!=dictionary.entries.end()) { best_end=end;best=&it->second; }
            if(end==utf8.size()) break;
            end=next(utf8,end);
        }
        if(best) { result+=*best;at=best_end; }
        else { result.append(utf8.substr(at,first_end-at));at=first_end; }
    }
    return result;
}
std::string ChineseText::convert_dialogue_json(std::string_view source,ChineseLanguage target) const {
    auto dialogue=nlohmann::json::parse(source);
    if(!dialogue.is_object() || !dialogue.contains("text") || !dialogue["text"].is_string())
        throw std::invalid_argument("NPC dialogue text missing");
    dialogue["text"]=convert(dialogue["text"].get<std::string>(),target);
    if(dialogue.contains("options")) {
        if(!dialogue["options"].is_array()) throw std::invalid_argument("NPC dialogue options invalid");
        for(auto& option:dialogue["options"]) {
            if(!option.is_object() || !option.contains("text") || !option["text"].is_string())
                throw std::invalid_argument("NPC dialogue option text missing");
            option["text"]=convert(option["text"].get<std::string>(),target);
        }
    }
    return dialogue.dump();
}
}
