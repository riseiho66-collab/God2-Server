#include "cn/assets/CnAppearanceResources.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <utility>

namespace god2cn {
namespace {
//004234F0 comma-first, then LF; no quote escaping. Native rt collapses CRLF.
// Reject NUL/oversize fields/lines rather than reproduce unsafe truncation or
// native overflow. These are qualification limits, not recovered server rules.
std::vector<std::string> native_lines(std::span<const std::uint8_t> raw) {
    std::vector<std::string> result;
    std::string line;
    for(std::size_t i=0;i<raw.size();++i) {
        const auto c=raw[i];
        if(c==0 || c==0x1a)throw std::invalid_argument("CN appearance CSV native text variant unqualified");
        if(c=='\r' && i+1<raw.size() && raw[i+1]=='\n')continue;
        line.push_back(static_cast<char>(c));
        if(line.size()>4095)throw std::length_error("CN appearance CSV exceeds native data line buffer");
        if(c=='\n') {result.push_back(std::move(line));line.clear();}
    }
    if(!line.empty())result.push_back(std::move(line));
    return result;
}
std::vector<std::string_view> fields(std::string_view line,unsigned count) {
    std::vector<std::string_view> result(count);
    std::size_t at=0;
    for(unsigned i=0;i<count;++i) {
        auto end=line.find(',',at);
        if(end==std::string_view::npos)end=line.find('\n',at);
        if(end==std::string_view::npos)break; // Native clears remaining fields.
        if(end-at>379)throw std::length_error("CN appearance CSV field exceeds native buffer");
        result[i]=line.substr(at,end-at);at=end+1;
    }
    return result;
}
bool scan_space(unsigned char c) {return c==' ' || c=='\t' || c=='\r' || c=='\n' || c=='\v' || c=='\f';}
//00423270 ->0041FA50("%d"): decimal prefix, failed conversion returns0.
// Out-of-int32 scanf behavior is unqualified, rather than host-dependent UB.
std::int32_t integer(std::string_view text) {
    std::size_t at=0;while(at<text.size() && scan_space(static_cast<unsigned char>(text[at])))++at;
    bool negative=false;
    if(at<text.size() && (text[at]=='-' || text[at]=='+'))negative=text[at++]=='-';
    const auto begin=at;
    std::uint64_t value=0;
    const std::uint64_t limit=negative?2147483648ULL:2147483647ULL;
    while(at<text.size() && text[at]>='0' && text[at]<='9') {
        const unsigned digit=static_cast<unsigned>(text[at++]-'0');
        if(value>(limit-digit)/10)throw std::invalid_argument("CN appearance CSV integer overflow unqualified");
        value=value*10+digit;
    }
    if(at==begin)return 0;
    return static_cast<std::int32_t>(negative?-static_cast<std::int64_t>(value):static_cast<std::int64_t>(value));
}
std::string lower_ascii(std::string_view text) {
    std::string result;
    for(const unsigned char c:text) {
        if(c<0x20 || c>=0x7f)throw std::invalid_argument("CN appearance key/path native encoding unqualified");
        result.push_back(static_cast<char>(c>='A' && c<='Z'?c+('a'-'A'):c));
    }
    return result;
}
std::filesystem::path relative_path(std::string_view text) {
    std::u8string path;
    for(const unsigned char c:text) {
        if(c<0x20 || c>=0x7f || c==':')throw std::invalid_argument("CN appearance resource path unqualified");
        path.push_back(static_cast<char8_t>(c=='\\'?'/':c));
    }
    const std::filesystem::path result(path);
    if(result.empty() || result.is_absolute() || result.has_root_path())
        throw std::invalid_argument("CN appearance relative resource path unavailable");
    for(const auto& part:result)if(part=="..")throw std::invalid_argument("CN appearance resource path escapes root");
    return result;
}
}
CnAppearanceRowSelection::CnAppearanceRowSelection(std::shared_ptr<const CnAppearanceResources> profile,
    std::array<CnHeroDollResourceRow,4> parts,CnDriverResourceRow driver,
    std::array<std::filesystem::path,4> paths,std::optional<std::filesystem::path> driver_path,std::uint8_t auxiliary,
    SourceRecord source)
    :profile_(std::move(profile)),parts_(std::move(parts)),driver_(std::move(driver)),
     part_paths_(std::move(paths)),driver_path_(std::move(driver_path)),auxiliary_(auxiliary),source_(std::move(source)) {}
CnSelectionAppearanceRows::CnSelectionAppearanceRows(std::shared_ptr<const CnAppearanceResources> profile,
    std::array<CnHeroDollResourceRow,4> parts,std::array<std::filesystem::path,4> paths,
    CnCharacterSummary source,unsigned row,RowStage stage,std::array<std::uint8_t,36> consumer)
    :profile_(std::move(profile)),parts_(std::move(parts)),paths_(std::move(paths)),
     source_(std::move(source)),row_(row),stage_(stage),consumer_row_(consumer) {}
std::shared_ptr<const CnAppearanceResources> CnAppearanceResources::read(const std::filesystem::path& root,
    std::size_t encoded_budget,std::size_t plain_budget) {
    if(!root.is_absolute())throw std::invalid_argument("CN appearance root must be explicit and absolute");
    auto profile=std::shared_ptr<CnAppearanceResources>(new CnAppearanceResources(root));
    constexpr std::array<const char*,2> names{"HeroDoll.csv","Drv.csv"};
    for(unsigned i=0;i<2;++i) {
        auto& file=profile->files_[i];
        file.selected=read_cn_preferred_resource(root/"Data2"/"Patch"/names[i],encoded_budget);
        file.decoded=decode_cn_resource(file.selected.encoded_bytes,plain_budget);
    }
    const auto hero_lines=native_lines(profile->files_[0].decoded);
    if(hero_lines.empty() || hero_lines[0].size()>511)throw std::invalid_argument("CN HeroDoll header unavailable");
    const auto header=fields(hero_lines[0],7);
    const auto first=integer(header[2]),total=integer(header[4]);
    if(first<2 || static_cast<std::size_t>(first-1)>hero_lines.size() || total<0)
        throw std::invalid_argument("CN HeroDoll header range unavailable");
    for(std::size_t line=static_cast<std::size_t>(first-1);line<hero_lines.size();++line) {
        const auto columns=fields(hero_lines[line],7);
        if(columns[0].empty() || columns[1].empty())continue;
        if(profile->hero_.size()>=static_cast<std::size_t>(total))
            throw std::invalid_argument("CN HeroDoll actual rows exceed declared count");
        const auto key=lower_ascii(std::string(columns[0])+std::string(columns[1]));
        const auto filename=lower_ascii(columns[3]);
        if(key.size()>9 || filename.size()>29)
            throw std::invalid_argument("CN HeroDoll native fixed row strings unqualified");
        if(!filename.empty())(void)relative_path(filename);
        const auto index=profile->hero_.size();
        profile->hero_.push_back({line+1,index,key,filename,static_cast<std::uint8_t>(integer(columns[5]))});
        profile->key_rows_.insert_or_assign(key,index); //00423960 CMapStringToPtr operator[].
    }
    if(profile->hero_.size()!=static_cast<std::size_t>(total))
        throw std::invalid_argument("CN HeroDoll actual/declared row count differs");
    const auto driver_lines=native_lines(profile->files_[1].decoded);
    if(driver_lines.empty() || driver_lines[0].size()>511)throw std::invalid_argument("CN driver header unavailable");
    const auto driver_header=fields(driver_lines[0],8);
    const auto driver_first=integer(driver_header[2]);
    if(driver_first<2 || static_cast<std::size_t>(driver_first-1)>driver_lines.size())
        throw std::invalid_argument("CN driver header range unavailable");
    //004885B0 accepts indices0..91:92 slots, regardless of assertion text91.
    // Field0 checks nonempty; it does not select destination row by numeric ID.
    for(std::size_t line=static_cast<std::size_t>(driver_first-1);line<driver_lines.size();++line) {
        const auto columns=fields(driver_lines[line],8);
        if(columns[0].empty())continue;
        if(profile->drivers_.size()==92)throw std::invalid_argument("CN driver table beyond recovered fixed slots");
        if(columns[1].size()>15)throw std::invalid_argument("CN driver filename overlaps native cached handle");
        if(!columns[1].empty())(void)relative_path(columns[1]);
        CnDriverResourceRow row{line+1,profile->drivers_.size(),std::string(columns[0]),std::string(columns[1]),
            static_cast<std::uint16_t>(integer(columns[2])),static_cast<std::uint16_t>(integer(columns[3])),{}};
        for(unsigned i=0;i<4;++i)row.fields4_to7[i]=static_cast<std::uint16_t>(integer(columns[i+4]));
        profile->drivers_.push_back(std::move(row));
    }
    return profile;
}
const CnHeroDollResourceRow& CnAppearanceResources::lookup(std::uint8_t category,unsigned slot,
    std::uint8_t family,std::uint8_t variant,std::uint8_t act) const {
    constexpr std::array<std::uint8_t,15> head{0,0,9,1,5,5,2,6,6,3,7,7,4,8,8}; //007EDE9C.
    constexpr std::array<std::uint8_t,3> face{0,1,1}; //007EDEAC.
    constexpr std::array<char,4> letters{'b','f','h','w'}; //00886130.
    if(slot>=letters.size() || act>=3)throw std::invalid_argument("CN appearance slot/ActType outside recovered branch");
    if(slot==0)family=static_cast<std::uint8_t>(family+act*3); // Native BH byte arithmetic.
    else if(slot==1)family=face[act];
    else if(slot==2) {
        const auto index=static_cast<unsigned>(family)*3+act;
        if(index>=head.size())throw std::invalid_argument("CN head family literal range unqualified");
        family=head[index];
    }
    //004237F0:"r%d%c%d%02d", all numeric inputs zero-extended bytes.
    auto key=std::string("r")+std::to_string(static_cast<unsigned>(category)+1)+letters[slot]+
        std::to_string(static_cast<unsigned>(family));
    if(variant<10)key+='0';
    key+=std::to_string(static_cast<unsigned>(variant));
    const auto found=key_rows_.find(key);
    if(found==key_rows_.end())throw std::invalid_argument("CN HeroDoll actual lookup row missing: "+key);
    return hero_[found->second];
}
CnAppearanceRowSelection CnAppearanceResources::select(std::uint8_t driver,std::uint8_t auxiliary,
    const std::array<std::uint8_t,8>& raw,CnAppearanceRowSelection::SourceRecord source) const {
    if(driver>=drivers_.size())throw std::invalid_argument("CN actual driver row unavailable; native default0 not qualified");
    const auto& driver_row=drivers_[driver];
    const auto act=static_cast<std::uint8_t>(driver_row.act_type_word); //004882E0 low byte ->004237F0.
    std::array<CnHeroDollResourceRow,4> parts;
    const auto& head=lookup(static_cast<std::uint8_t>(raw[4]&15),2,static_cast<std::uint8_t>(raw[4]>>4),
        static_cast<std::uint8_t>(raw[5]&31),act);
    const auto base=head.face_variant_base;
    const auto face_variant=base<2?base:static_cast<std::uint8_t>(base+(raw[3]&31)); //00423CB0 BYTE.
    std::array<std::filesystem::path,4> paths;
    for(unsigned slot=0;slot<4;++slot) {
        auto family=static_cast<std::uint8_t>(raw[slot*2]>>4);
        auto variant=static_cast<std::uint8_t>(raw[slot*2+1]&31);
        if(slot==1)variant=face_variant;
        else if(slot==3 && driver>=1) {family=8;variant=0;}
        parts[slot]=lookup(static_cast<std::uint8_t>(raw[slot*2]&15),slot,family,variant,act);
        if(parts[slot].native_filename.empty())throw std::invalid_argument("CN selected HeroDoll filename unavailable");
        paths[slot]=root_/"Data2"/"Rom"/"RoleDoll"/relative_path(parts[slot].native_filename);
    }
    std::optional<std::filesystem::path> driver_path;
    if(!driver_row.native_filename.empty())driver_path=root_/"Data2"/"Rom"/"Drv"/relative_path(driver_row.native_filename);
    return CnAppearanceRowSelection(shared_from_this(),std::move(parts),driver_row,std::move(paths),std::move(driver_path),auxiliary,std::move(source));
}
std::optional<CnAppearanceRowSelection> CnAppearanceResources::select_normal_initial(const CnWorldEntry::BeginPlay& entry) const {
    if(entry.alternate_appearance_resource_key_raw())return std::nullopt;
    return select(entry.mount_driver_selector_raw(),entry.auxiliary_appearance_selector_raw(),entry.appearance_components_raw(),entry);
}
std::optional<CnAppearanceRowSelection> CnAppearanceResources::select_ordinary_remote(const CnRemoteActor::Record& record) const {
    if(record.alternate_appearance_resource_key_raw())return std::nullopt;
    return select(record.mount_driver_resource_selector_raw(),record.auxiliary_resource_selector_raw(),record.appearance_components_raw(),record);
}
std::optional<CnSelectionAppearanceRows> CnAppearanceResources::select_native_summary(
    const CnCharacterSummary& summary,unsigned index,CnSelectionAppearanceRows::RowStage stage) const {
    const auto row=summary.character(index);
    if(!row)return std::nullopt;
    if(stage!=CnSelectionAppearanceRows::RowStage::ReceivedBeforePanel &&
       stage!=CnSelectionAppearanceRows::RowStage::AfterPanel)
        throw std::invalid_argument("CN selection local row stage unqualified");
    const auto raw=stage==CnSelectionAppearanceRows::RowStage::ReceivedBeforePanel?
        row->row_bytes():row->selection_panel_row_bytes();
    //0044315C/004431BF push literal0 for every preview lookup. The head
    // row's face base is read at00443197; add at004431B1 is BYTE arithmetic.
    const auto& head=lookup(static_cast<std::uint8_t>(raw[28]&15),2,
        static_cast<std::uint8_t>(raw[28]>>4),static_cast<std::uint8_t>(raw[29]&31),0);
    const auto base=head.face_variant_base;
    const auto face=base<2?base:static_cast<std::uint8_t>(base+(raw[27]&31));
    std::array<CnHeroDollResourceRow,4> parts;
    std::array<std::filesystem::path,4> paths;
    for(unsigned slot=0;slot<4;++slot) {
        const auto variant=slot==1?face:static_cast<std::uint8_t>(raw[25+slot*2]&31);
        parts[slot]=lookup(static_cast<std::uint8_t>(raw[24+slot*2]&15),slot,
            static_cast<std::uint8_t>(raw[24+slot*2]>>4),variant,0);
        if(parts[slot].native_filename.empty())
            throw std::invalid_argument("CN selection HeroDoll filename unavailable");
        paths[slot]=root_/"Data2"/"Rom"/"RoleDoll"/relative_path(parts[slot].native_filename);
    }
    return CnSelectionAppearanceRows(shared_from_this(),std::move(parts),std::move(paths),summary,index,stage,raw);
}
}
