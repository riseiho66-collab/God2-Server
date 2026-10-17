#include "db/NativePetRoomSourceCatalog.h"
#include "db/SqliteSupport.h"
#include <array>
#include <span>
#include <string_view>
#include <utility>

namespace god2 {
namespace {
std::vector<std::uint8_t> hex(std::string_view text) {
    auto digit=[](char c)->unsigned {
        if(c>='0' && c<='9')return static_cast<unsigned>(c-'0');
        if(c>='a' && c<='f')return static_cast<unsigned>(c-'a'+10);
        throw DatabaseError("Invalid pinned PetRoom source hex");
    };
    if(text.size()%2)throw DatabaseError("Odd pinned PetRoom source hex");
    std::vector<std::uint8_t> out;out.reserve(text.size()/2);
    for(std::size_t i=0;i<text.size();i+=2)
        out.push_back(static_cast<std::uint8_t>((digit(text[i])<<4)|digit(text[i+1])));
    return out;
}
constexpr char item_inventory_sha256[]="3c21cc86d1072aafc6fa24fc80644a9d093454bfc45e66bf49829123cc9ae9bc";
constexpr char category_inventory_sha256[]="e75442ce039273f6dd3cf1af88c8b72853af444145bf2d3969102c4f6d4890c3";
constexpr char category_record_sha256[]="de24fac6aece10ade1df6b6412401069c7a137d325ac3b38c3f5244eb6f660ef";
// Supplemental historical locations; the unchanged v1 raw-source pins below
// retain SQLNULL. These offsets have their own source_locations_sha256 proof.
const std::array<std::uint32_t,22> historical_decoded_offsets{{
    673207,673321,673437,673555,673671,673844,674010,674176,674342,674508,674674,674852,675018,675184,675350,675516,675696,675848,676000,676178,676355,676558
}};
const auto category_record=hex("353530312c363430302c5350492caf53aeedb944a8e32ca5bca4c0c3fe2cb6c7b065c45faf5d2cc1f4a8adadbbc46c2ca540acc9a661b9cf2cac56a6e2c5f8c0592cafe0a44fa4f4b4b92cadbba4f52caca1b0caa5ceb7cfa4f52cae76ae7ba55cafe0bcfaab7e2cb1a1a448b860aca1b0ca2cb874bdcfb860aca1b0ca2cb773a67eaca1b0ca2cb867c5e7a55ba6a8b944a8e32caf53aeedab48afc82ca46ac059b7d3a8cfa5ce2cbed4c364addcae772cbed4c364c2e0a5cda4a62ca8bec37aa5db2ca843a4e9a5f4b0c8b944a8e3a5ce");
// These22 normalized raw records preserve every CP950 octet and empty field.
// Record decoded offsets and full396 output were not retained; no values are invented.
const std::array<NativePetRoomSourceRecord,22> pinned{{
    {6177,517,8695,26,std::nullopt,"6d55282ac1e674630fc097cdca79e03904bba939703d84e9ed6e9989eb784b15",hex("363137372c302c53706930313637372c35353637352ca445bea4adb72c3130302c312ca55fa4e8a5aec37ea9d0b6a1ad49b4bab944a8e32ca569a5cea8d3a7f3b4aba55fa4e8a5aec37ea9d0b6a1ad49b4ba2c2c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6178,518,8696,26,std::nullopt,"b63517c4b184541f283c07e485881ccd3f02f035059cb89a44261fa65d46f0fc",hex("363137382c302c53706930313637382c35353637362cab6eac76aefcc5792c3130302c312ca55fa4e8a5aec37ea9d0b6a1ad49b4bab944a8e32ca569a5cea8d3a7f3b4aba55fa4e8a5aec37ea9d0b6a1ad49b4ba2c2c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6179,519,8697,26,std::nullopt,"95edfbbb85887a0443601c655938c6c88c42a722982f167c0748defdd1460006",hex("363137392c302c53706930313637392c35353637372cae4cabc2a669a4f5a4732c3130302c312ca55fa4e8a5aec37ea9d0b6a1ad49b4bab944a8e32ca569a5cea8d3a7f3b4aba55fa4e8a5aec37ea9d0b6a1ad49b4ba2c2c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6180,520,8698,26,std::nullopt,"c570acc4888c3e5e9ce30ec985863c744c6e59075c07745f8072acb21fe027d6",hex("363138302c302c53706930313638302c35353637382ca55fb7a5b7a5a5fa2c3130302c312ca55fa4e8a5aec37ea9d0b6a1ad49b4bab944a8e32ca569a5cea8d3a7f3b4aba55fa4e8a5aec37ea9d0b6a1ad49b4ba2c2c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6183,521,8699,26,std::nullopt,"084863b7d04cb6877ef0e51b579e851f2077da6402bce42412e1a4276a5d243b",hex("363138332c31322c53706930313638332c35353937362cafaba550b867c5e7b4ceb4cebf7d28a470292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b27635a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72ca4a3a569a673a44aac7daddc2c2c2c302c312c302c302c302c312c302c312c312c312c302c302c30")},
    {6184,522,8700,26,std::nullopt,"b4e78a23b9d9645649ebd8c35ba360f55c4b0a6d3595d5930d6107dee79e4ad3",hex("363138342c31322c53706930313638342c35353937312cafaba550b867c5e7b4ceb4cebf7d4c563128314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763130a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6185,523,8701,26,std::nullopt,"4c0e94f734f7f6073840beb644696beea05cbbaee01716cdfdb7ccc71c9e9fec",hex("363138352c31322c53706930313638352c35353937322cafaba550b867c5e7b4ceb4cebf7d4c563228314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763230a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6186,524,8702,26,std::nullopt,"306a73c603d8c6d4f91cd34d8de0801476bc3a54122d639798713c5112f888b6",hex("363138362c31322c53706930313638362c35353937332cafaba550b867c5e7b4ceb4cebf7d4c563328314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763330a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6187,525,8703,26,std::nullopt,"74f43746a6a3534ed8baf0a226ee87a6040e82016b0913f8a145a42eb457dffa",hex("363138372c31322c53706930313638372c35353937342cafaba550b867c5e7b4ceb4cebf7d4c563428314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763430a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6188,526,8704,26,std::nullopt,"00add5c262755d95679f1e70858cdece0c89285a50c0c0fd26c5bc4e6acb74dc",hex("363138382c31322c53706930313638382c35353937352cafaba550b867c5e7b4ceb4cebf7d4c563528314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763530a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6189,527,8705,26,std::nullopt,"7046e23389d51511242771ae45d3f436c02ae8f7d2bd5c278136a95ac2e7a5b3",hex("363138392c31322c53706930313638392c35353937312cafaba550b867c5e7b4ceb4cebf7d4c563128314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763130a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72ca4a3a569a673a44aac7daddc2c2c2c302c312c302c302c302c312c302c312c312c312c302c302c30")},
    {6190,528,8706,26,std::nullopt,"a25f962951d2a0861db9f00ef2c59772c80acd4bb9cfce6089064c5f28354e20",hex("363139302c31322c53706930313639302c35383032352cafaba550b867c5e7b4ceb4cebf7d4c563628314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763630a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6191,529,8707,26,std::nullopt,"3b517be6e3892f740b646aa6cb1af6d485471cdc7a0ce6cd6246d4c41e18e63c",hex("363139312c31322c53706930313639312c35383032352cafaba550b867c5e7b4ceb4cebf7d4c563728314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763730a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6192,530,8708,26,std::nullopt,"4049bec2af507faba75daf4e5445a157c9e476a982579e45d52871b3af80116b",hex("363139322c31322c53706930313639322c35383032352cafaba550b867c5e7b4ceb4cebf7d4c563828314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763830a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6193,531,8709,26,std::nullopt,"5972164dd60fb31e9c5ca55c1cee4bdb0a57bfa3bc4bea52453ab2de312a602f",hex("363139332c31322c53706930313639332c35383032352cafaba550b867c5e7b4ceb4cebf7d4c563928314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763930a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c2c2c2c302c312c302c302c302c312c312c312c312c312c302c302c30")},
    {6194,532,8710,26,std::nullopt,"277e4119275a4ddcbb21c2eb7d0bde3e5f6f1eb1318bd149e9ba4eac4d118ac6",hex("363139342c31322c53706930313639342c33353032352c5baca15d5bafab5db867c5e7b34abf7c4c563728314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b2763730a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72ca4a3a569a673a44aac7daddc2c2c2c302c312c302c302c302c312c302c312c312c312c302c302c30")},
    {6195,533,8711,26,std::nullopt,"c54f1422ab3625862c56d7675f19d2b640fc1b814aadc42677511c07d0c49d9a",hex("363139352c31322c53706930313639352c33363035342c5baca15d5ba4485db867c5e7b6bcaec64c563728314852292c3130302c312ca448aaabbed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40aab1ae61bed4b0abb867c5e7adc8aec4b2763830a2482ca4a3a569a673a44aac7daddc2c2c2c2c302c312c302c302c302c312c302c312c312c312c302c302c30")},
    {6196,534,8712,26,std::nullopt,"99ec347e16d96b6e14a6e733fa16aa631725e767c8235cb62f0ce873f4ee225a",hex("363139362c31322c53706930313639362c33353032332c5baca15d5bc3645db867c5e7bf7daa474c563728314852292c3130302c312cbed4c364bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40bed4c364bed4b0abb867c5e7adc8aec4b2763730a2482ca4a3a569a673a44aac7daddc2c2c2c2c302c312c302c302c302c312c302c312c312c312c302c302c30")},
    {6197,535,8713,26,std::nullopt,"b251e2e173e1ea391f543357ac2d90f542a981a967610d4a10460af7c55334b9",hex("363139372c31322c53706930313639372c35303037322c5ba55badc85d5bafab5db867c5e7455828314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b276313130a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c28a4a3a569a673ac7daddc292c2c2c302c312c302c302c302c312c302c312c312c312c302c302c30")},
    {6198,536,8714,26,std::nullopt,"43e78c46a10dcfdef9679d72d44aec2730d9062b35c76ae50f69505dd48af50f",hex("363139382c31322c53706930313639382c33363035342c5b5649505d5bafab5db867c5e7455828314852292c3130302c312cafaba550bed4b0abb867c5e7a55ba6a8b944a8e32c31a470aec9a4bab4a3aa40afaba550bed4b0abb867c5e7adc8aec4b276313230a2482ca8ccb7d3a6b3a558b3f5afaba550aabab5a5afc5a4c0b074b867c5e72c28a4a3a569a673ac7daddc292c2c2c302c312c302c302c302c312c302c312c312c312c302c302c30")},
    {6199,537,8715,26,std::nullopt,"1767904f1cc507a37f6e115aaab3b7019a01e0f1cdcb0a5e8dd2286ccc762e11",hex("363139392c31322c53706930313639392c34303232362cacf5a751b4abb867c5e73830a24828314852292c3130302c352c31a470aec9b4a3aa40aab1ae61bed4b0abb867c5e7adc8aec4b2763830a2482caabdb1b5a8cfa5cea141adabbdc6a8cfa5cea569b2d6bf6eaec9b6a12ca569bb50b6a7a5fab971b27ea142ab6cb671b971b27ea440b05fa8cfa5ce2cb54caa6bbb50a175b867c5e7b4a3aa404ea248a176a440a8d6a8cfa5ce2c2c2c383432382c312c302c302c302c302c302c312c302c312c302c302c30")},
    {6200,538,8716,26,std::nullopt,"5b3325aecc7da3768013710a94ad36ddd2475fd79b49b8d9da4c110ed0e4604f",hex("363230302c31322c53706930313730302c34303232362cacf5a751b4abb867c5e7313030a24828314852292c3130302c312c31a470aec9b4a3aa40aab1ae61bed4b0abb867c5e7adc8aec4b276313030a2482caabdb1b5a8cfa5cea141adabbdc6a8cfa5cea569b2d6bf6eaec9b6a12ca569bb50b6a7a5fab971b27ea142ab6cb671b971b27ea440b05fa8cfa5ce2cb54caa6bbb50a175b867c5e7b4a3aa404ea248a176a440a8d6a8cfa5ce2c2c2c383432382c312c302c302c302c302c302c312c302c312c302c302c30")},
}};
std::vector<std::uint8_t> blob(sqlite_detail::Statement& row,int index) {
    const auto b=row.blob(index,1,4096);return {b.begin(),b.end()};
}
void bind(sqlite_detail::Statement& row,int index,const char* text) {
    row.bind(index,std::string(text));
}
std::vector<std::span<const std::uint8_t>> source_fields(const NativePetRoomSourceRecord& source) {
    // Only lookup()'s base-pin-verified source records reach this projection. In these
    // normalized rows every comma is a delimiter, and no NUL/CR/LF is retained
    // inside a field. Native451BE0 has no quote/escape/codepage transformation.
    const std::span<const std::uint8_t> raw(source.normalized_cp950_record);
    std::vector<std::span<const std::uint8_t>> fields;
    std::size_t start=0;
    for(std::size_t i=0;i<=raw.size();++i) {
        if(i<raw.size() && (raw[i]==0 || raw[i]==0x0a || raw[i]==0x0d))
            throw DatabaseError("PetRoom text source contains a line/NUL boundary");
        if(i==raw.size() || raw[i]==0x2c) {
            fields.push_back(raw.subspan(start,i-start));start=i+1;
        }
    }
    if(fields.size()!=26 || source.field_count!=26)
        throw DatabaseError("PetRoom text source field count differs");
    return fields;
}
NativePetRoomDefinitionText project_text(NativePetRoomSourceRecord source) {
    const auto fields=source_fields(source);
    // Native451AE0 copies the entire token+NUL before459420 forces BYTE2D/53=0.
    // These pins' token4/7 lengths fit38 bytes; reject larger input rather than
    // treating the native unbounded copy as a generally safe truncation rule.
    if(fields[4].size()>37 || fields[7].size()>37)
        throw DatabaseError("PetRoom text exceeds qualified native string buffers");
    std::vector<std::uint8_t> name(fields[4].begin(),fields[4].end());
    std::vector<std::uint8_t> caption(fields[7].begin(),fields[7].end());
    std::vector<std::uint8_t> description;
    for(std::size_t i=8;i<=12;++i) {
        if(fields[i].empty())continue;
        // Native common tail appends LF between nonempty tokens, then forces
        // temp[BDh]=0 after its unbounded copies. The finite pins fit both its
        // 256-byte token temporary and189-byte final meaningful string.
        if(fields[i].size()>255 || description.size()+fields[i].size()+
           (description.empty()?0u:1u)>189)
            throw DatabaseError("PetRoom description exceeds qualified native buffers");
        if(!description.empty())description.push_back(0x0a);
        description.insert(description.end(),fields[i].begin(),fields[i].end());
    }
    return {std::move(source),std::move(name),std::move(caption),std::move(description)};
}
std::uint32_t finite_decimal(std::span<const std::uint8_t> field) {
    // All exact pins use1..5 ASCII digits. Conditional native%d input/count/
    // classification semantics are separate from this checked source arithmetic.
    if(field.empty() || field.size()>5)throw DatabaseError("PetRoom scalar source shape differs");
    std::uint32_t value=0;
    for(const auto byte:field) {
        if(byte<'0' || byte>'9')throw DatabaseError("PetRoom scalar source is not finite ASCII decimal");
        const auto digit=static_cast<std::uint32_t>(byte-'0');
        if(value>(0x7fffffffu-digit)/10u)throw DatabaseError("PetRoom scalar exceeds signed32 conversion");
        value=value*10u+digit;
    }
    return value;
}
NativePetRoomDefinitionScalars project_scalars(NativePetRoomSourceRecord source) {
    const auto fields=source_fields(source);
    const auto dword0=finite_decimal(fields[5]),dword4=finite_decimal(fields[6]);
    const auto word114=static_cast<std::uint16_t>(finite_decimal(fields[3])&0xffffu);
    const auto word112=static_cast<std::uint16_t>(finite_decimal(fields[13])&0xffffu);
    std::uint8_t byte11A=0,byte11B_low4=0;
    for(unsigned i=0;i<8;++i)
        byte11A=static_cast<std::uint8_t>(byte11A|((finite_decimal(fields[14+i])&1u)<<i));
    for(unsigned i=0;i<4;++i)
        byte11B_low4=static_cast<std::uint8_t>(byte11B_low4|((finite_decimal(fields[22+i])&1u)<<i));
    // All8 bits of11A are directly written;11B's upper4 are preserved by native
    // code and are deliberately excluded. No RomMaps/default11C/396 is supplied.
    return {std::move(source),dword0,dword4,word114,word112,byte11A,byte11B_low4};
}
std::array<std::pair<std::uint16_t,std::uint16_t>,57> rom_map_ranges(
    const std::vector<NativeRomMapSourceRecord>& records) {
    if(records.size()!=57)throw DatabaseError("Complete RomMaps source required");
    std::array<std::pair<std::uint16_t,std::uint16_t>,57> ranges{};
    // records() already validates every raw pin. Convert all57 before searching,
    // retaining the actual token0 slot relation for this exact ordered dataset.
    // This does not model arbitrary duplicate/invalid slots or failed row reads.
    for(std::size_t i=0;i<records.size();++i) {
        const auto& record=records[i];
        const std::span<const std::uint8_t> raw(record.normalized_record);
        std::vector<std::span<const std::uint8_t>> fields;
        std::size_t first=0;
        for(std::size_t j=0;j<=raw.size();++j) {
            if(j<raw.size() && (raw[j]==0 || raw[j]=='\r' || raw[j]=='\n'))
                throw DatabaseError("RomMaps source contains a line delimiter");
            if(j==raw.size() || raw[j]==',') {
                fields.push_back(raw.subspan(first,j-first));first=j+1;
            }
        }
        if(fields.size()!=5 || record.source_record_index!=i || record.slot_index!=i ||
           finite_decimal(fields[0])!=i || fields[3].size()>127)
            throw DatabaseError("RomMaps finite source shape differs");
        ranges[i]={static_cast<std::uint16_t>(finite_decimal(fields[1])&0xffffu),
                   static_cast<std::uint16_t>(finite_decimal(fields[2])&0xffffu)};
        // token3 fits the native128-byte path destination; token4 remains raw
        // evidence only and is not consumed by actual459EF0.
    }
    return ranges;
}
// Byte stores reproduce the selected native physical layout without host
// endianness, packed-struct aliasing or treating metadataDWORD0 as a source key.
void store_record_word(std::array<std::uint8_t,396>& bytes,std::size_t offset,std::uint16_t value) {
    bytes[offset]=static_cast<std::uint8_t>(value);
    bytes[offset+1]=static_cast<std::uint8_t>(value>>8u);
}
void store_record_dword(std::array<std::uint8_t,396>& bytes,std::size_t offset,std::uint32_t value) {
    for(unsigned i=0;i<4;++i)bytes[offset+i]=static_cast<std::uint8_t>(value>>(8u*i));
}
void copy_record_string(std::array<std::uint8_t,396>& bytes,std::size_t offset,
                        const std::vector<std::uint8_t>& text,std::size_t capacity) {
    // The native copies precede forced end bytes and do not have these guards.
    // These finite-source bounds preserve their actual meaningful text+NUL.
    if(text.size()>=capacity || offset>bytes.size() || capacity>bytes.size()-offset)
        throw DatabaseError("PetRoom conditional record string exceeds qualified region");
    for(std::size_t i=0;i<text.size();++i)bytes[offset+i]=text[i];
    bytes[offset+text.size()]=0;
}
NativePetRoomDefinitionRecordSource project_record_source(
    NativePetRoomDefinitionResource resource,NativePetRoomDefinitionText text) {
    // Value initialization is explicitly conditional on the original successful
    // zero-allocation/selector0 premises, not an observed current record buffer.
    NativePetRoomDefinitionRecordSource result{std::move(resource),std::move(text),{}};
    auto& bytes=result.conditional_record_bytes;
    const auto& scalars=result.source_resource.source_scalars;
    store_record_dword(bytes,0x000,scalars.metadata_dword0); // token5
    store_record_dword(bytes,0x004,scalars.metadata_dword4); // token6
    copy_record_string(bytes,0x008,result.source_text.definition_name_cp950,38);
    bytes[0x02d]=0; //459473 forces this byte after the whole token4+NUL copy
    copy_record_string(bytes,0x02e,result.source_text.caption_cp950,38);
    bytes[0x053]=0; //45949D forces this byte after the whole token7+NUL copy
    copy_record_string(bytes,0x054,result.source_text.description_cp950,190);
    // No forced recordBYTE111 write: native forces scratch[BDh], then copies
    // the meaningful description+NUL; remaining bytes retain allocated zero.
    store_record_word(bytes,0x112,scalars.metadata_word112);
    store_record_word(bytes,0x114,scalars.metadata_word114);
    store_record_word(bytes,0x116,result.source_resource.metadata_word116);
    store_record_word(bytes,0x118,0xffffu);
    bytes[0x11a]=scalars.metadata_byte11A;
    if((scalars.metadata_byte11B_low4&0xf0u)!=0)
        throw DatabaseError("PetRoom conditional scalar low4 shape differs");
    bytes[0x11b]=scalars.metadata_byte11B_low4; // preserved high4 conditional initial0
    // Selector0 skips category-specific stores:11C..18B retains conditional0.
    return result;
}
void source_schema(sqlite3* db,bool require_both) {
    sqlite_detail::Statement objects(db,
        "SELECT type,name FROM main.sqlite_schema WHERE name IN('native_raw_item_source_sets',"
        "'native_raw_item_source_rows') OR (type='trigger' AND tbl_name IN("
        "'native_raw_item_source_sets','native_raw_item_source_rows'))");
    unsigned tables=0;
    while(objects.row()) {
        if(objects.text(0)!="table")throw DatabaseError("PetRoom source table/view/trigger collision");
        ++tables;
    }
    if(tables>2 || (require_both && tables!=2))throw DatabaseError("PetRoom source tables unavailable");
}
struct ReadScope {
    sqlite3* db;bool owned,committed=false;
    explicit ReadScope(sqlite3* value):db(value),owned(sqlite3_get_autocommit(db)!=0) {
        if(owned)sqlite_detail::execute(db,"BEGIN");
    }
    ~ReadScope(){if(owned && !committed)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owned)sqlite_detail::execute(db,"COMMIT");committed=true;}
};
}
NativePetRoomSourceCatalog::NativePetRoomSourceCatalog(sqlite3* db):db_(db) {
    if(!db_)throw DatabaseError("Null PetRoom source connection");
}
std::vector<NativePetRoomSourceRecord> NativePetRoomSourceCatalog::read() const {
    ReadScope scope(db_);source_schema(db_,true);
    // Explicit main qualification prevents TEMP/ATTACH shadow-source fallback.
    // One seed/join statement keeps counts, envelope and every row coherent and
    // exposes orphan rows even when this dataset's source envelope is absent.
    sqlite_detail::Statement rows(db_,
        "SELECT (SELECT count(*) FROM main.native_raw_item_source_sets WHERE dataset_id=?1),"
        "(SELECT count(*) FROM main.native_raw_item_source_rows WHERE dataset_id=?1),"
        "s.version_scope,s.source_file,s.encoded_sha256,s.decoded_sha256,s.parser_image_sha256,"
        "s.item_inventory_sha256,s.category_inventory_sha256,s.family,s.source_bank_rows,"
        "s.category_ordinal,s.category_line,s.category_decoded_offset,s.category_record_sha256,"
        "s.category_record,s.range_low,s.range_high,s.record_count,s.encoding,s.authority,s.catalog_sha256,"
        "r.native_key,r.source_record_index,r.source_line,r.field_count,r.decoded_offset IS NULL,"
        "r.record_sha256,r.normalized_record,r.family,r.authority,s.dataset_id,r.dataset_id,s.inventory_rows "
        "FROM (SELECT 1) seed LEFT JOIN main.native_raw_item_source_sets s ON s.dataset_id=?1 "
        "LEFT JOIN main.native_raw_item_source_rows r ON r.dataset_id=s.dataset_id ORDER BY r.native_key");
    bind(rows,1,dataset_id);
    std::vector<NativePetRoomSourceRecord> result;
    while(rows.row()) {
        if(rows.integer(0)==0 && rows.integer(1)==0) {
            if(!result.empty() || rows.row())throw DatabaseError("Ambiguous empty PetRoom source");
            scope.finish();return {};
        }
        if(rows.integer(0)!=1 || rows.integer(1)!=22 || result.size()>=pinned.size() ||
           rows.text(2)!="TW149c_HISTORICAL_TEXT" || rows.text(3)!=source_file ||
           rows.text(4)!=encoded_sha256 || rows.text(5)!=decoded_sha256 ||
           rows.text(6)!=parser_image_sha256 || rows.text(7)!=item_inventory_sha256 ||
           rows.text(8)!=category_inventory_sha256 || rows.text(9)!="SPI" ||
           rows.integer(10)!=737 || rows.integer(11)!=9 || rows.integer(12)!=20 ||
           rows.integer(13)!=1213 || rows.text(14)!=category_record_sha256 ||
           blob(rows,15)!=category_record || rows.integer(16)!=6177 || rows.integer(17)!=6200 ||
           rows.integer(18)!=22 || rows.text(19)!="CP950_NORMALIZED_RECORD" ||
           rows.text(20)!=authority || rows.text(21)!=catalog_sha256 || rows.integer(26)!=1 ||
           rows.text(29)!="SPI" || rows.text(30)!=authority ||
           rows.text(31)!=dataset_id || rows.text(32)!=dataset_id || rows.integer(33)!=16127)
            throw DatabaseError("PetRoom raw source provenance/count mismatch");
        NativePetRoomSourceRecord value{rows.number<std::uint16_t>(22),rows.number<std::uint32_t>(23),
            rows.number<std::uint32_t>(24),rows.number<std::uint32_t>(25),std::nullopt,
            rows.text(27),blob(rows,28)};
        // Exact byte/value comparison validates the complete pin; the stored
        // fingerprint or a stored record hash alone cannot qualify changed bytes.
        if(value!=pinned[result.size()])throw DatabaseError("PetRoom raw source record differs from pin");
        result.push_back(std::move(value));
    }
    if(result.size()!=pinned.size())throw DatabaseError("Incomplete PetRoom raw source");
    scope.finish();return result;
}
bool NativePetRoomSourceCatalog::populated() const {return !read().empty();}
std::optional<NativePetRoomSourceRecord> NativePetRoomSourceCatalog::lookup(std::uint16_t key) const {
    const auto records=read();
    for(std::size_t i=0;i<records.size();++i)if(records[i].native_key==key) {
        auto result=records[i];
        result.decoded_offset=historical_decoded_offsets[i];
        result.source_location_sha256=source_locations_sha256;
        return result;
    }
    return {};
}
std::optional<NativePetRoomDefinitionText> NativePetRoomSourceCatalog::lookup_definition_text(std::uint16_t key) const {
    auto source=lookup(key);
    if(!source)return {};
    return project_text(std::move(*source));
}
std::optional<NativePetRoomDefinitionScalars> NativePetRoomSourceCatalog::lookup_definition_scalars(std::uint16_t key) const {
    auto source=lookup(key);
    if(!source)return {};
    return project_scalars(std::move(*source));
}
std::optional<NativePetRoomDefinitionResource> NativePetRoomSourceCatalog::lookup_definition_resource(std::uint16_t key) const {
    ReadScope scope(db_);
    // Both nested readers borrow this same connection/transaction view. A
    // missing source dataset cannot become the native no-range-match sentinel,
    // and an absent SPI key cannot skip the other complete source validation.
    const auto maps=NativeRomMapSourceCatalog(db_).records();
    if(maps.empty() || !populated())throw DatabaseError("Installed SPI and RomMaps sources required");
    const auto ranges=rom_map_ranges(maps);
    auto scalars=lookup_definition_scalars(key);
    if(!scalars) {scope.finish();return {};}
    std::uint16_t word116=0xffffu;
    std::optional<NativeRomMapSourceRecord> matched;
    const auto icon=scalars->metadata_word114;
    // Actual459FC0 uses signedWORD count57 and unsigned inclusiveWORD ranges.
    // Only AX is copied by459943; its first slot result is not a gameplay ID.
    for(std::size_t i=0;i<ranges.size();++i) {
        if(icon>=ranges[i].first && icon<=ranges[i].second) {
            word116=static_cast<std::uint16_t>(i);matched=maps[i];break;
        }
    }
    NativePetRoomDefinitionResource result{std::move(*scalars),word116,std::move(matched)};
    scope.finish();return result;
}
std::optional<NativePetRoomDefinitionRecordSource> NativePetRoomSourceCatalog::lookup_definition_record_source(std::uint16_t key) const {
    ReadScope scope(db_);
    // Resource validates both complete installed datasets before even an
    // absent-key return. Every nested read borrows this same transaction view.
    auto resource=lookup_definition_resource(key);
    if(!resource) {scope.finish();return {};}
    auto text=lookup_definition_text(key);
    if(!text || text->source_record!=resource->source_scalars.source_record)
        throw DatabaseError("PetRoom conditional resource/text source mismatch");
    auto result=project_record_source(std::move(*resource),std::move(*text));
    scope.finish();return result;
}
void NativePetRoomSourceCatalog::import_pinned_source(sqlite3* db) {
    if(!db || !sqlite3_get_autocommit(db))throw DatabaseError("PetRoom source import requires own transaction");
    sqlite_detail::Transaction transaction(db);
    source_schema(db,false);
    // Common source tables use dataset namespaces. No duplicate content
    // table or common gameplay identity is manufactured from this native key.
    sqlite_detail::execute(db,
        "CREATE TABLE IF NOT EXISTS main.native_raw_item_source_sets("
        "dataset_id TEXT PRIMARY KEY,version_scope TEXT NOT NULL,source_file TEXT NOT NULL,"
        "encoded_sha256 TEXT NOT NULL,decoded_sha256 TEXT NOT NULL,parser_image_sha256 TEXT NOT NULL,"
        "item_inventory_sha256 TEXT NOT NULL,category_inventory_sha256 TEXT NOT NULL,family TEXT NOT NULL,"
        "source_bank_rows INTEGER NOT NULL,category_ordinal INTEGER NOT NULL,category_line INTEGER NOT NULL,"
        "category_decoded_offset INTEGER NOT NULL,category_record_sha256 TEXT NOT NULL,category_record BLOB NOT NULL,"
        "range_low INTEGER NOT NULL,range_high INTEGER NOT NULL,record_count INTEGER NOT NULL,"
        "encoding TEXT NOT NULL,authority TEXT NOT NULL,catalog_sha256 TEXT NOT NULL,inventory_rows INTEGER NOT NULL)");
    sqlite_detail::execute(db,
        "CREATE TABLE IF NOT EXISTS main.native_raw_item_source_rows("
        "dataset_id TEXT NOT NULL,native_key INTEGER NOT NULL,source_record_index INTEGER NOT NULL,"
        "source_line INTEGER NOT NULL,field_count INTEGER NOT NULL,decoded_offset INTEGER,"
        "record_sha256 TEXT NOT NULL,normalized_record BLOB NOT NULL,family TEXT NOT NULL,authority TEXT NOT NULL,"
        "PRIMARY KEY(dataset_id,native_key),FOREIGN KEY(dataset_id) REFERENCES native_raw_item_source_sets(dataset_id))");
    NativePetRoomSourceCatalog catalog(db);
    if(catalog.populated()) {transaction.commit();return;}
    {
        sqlite_detail::Statement source(db,
            "INSERT INTO main.native_raw_item_source_sets VALUES("
            "?1,'TW149c_HISTORICAL_TEXT',?2,?3,?4,?5,?6,?7,'SPI',737,9,20,1213,?8,?9,6177,6200,22,"
            "'CP950_NORMALIZED_RECORD',?10,?11,16127)");
        bind(source,1,dataset_id);bind(source,2,source_file);bind(source,3,encoded_sha256);
        bind(source,4,decoded_sha256);bind(source,5,parser_image_sha256);
        bind(source,6,item_inventory_sha256);bind(source,7,category_inventory_sha256);
        bind(source,8,category_record_sha256);source.bind_blob(9,category_record);
        bind(source,10,authority);bind(source,11,catalog_sha256);source.done();
    }
    for(const auto& value:pinned) {
        sqlite_detail::Statement row(db,
            "INSERT INTO main.native_raw_item_source_rows VALUES(?1,?2,?3,?4,?5,NULL,?6,?7,'SPI',?8)");
        bind(row,1,dataset_id);row.bind(2,static_cast<std::int64_t>(value.native_key));
        row.bind(3,static_cast<std::int64_t>(value.source_record_index));
        row.bind(4,static_cast<std::int64_t>(value.source_line));
        row.bind(5,static_cast<std::int64_t>(value.field_count));row.bind(6,value.record_sha256);
        row.bind_blob(7,value.normalized_cp950_record);bind(row,8,authority);row.done();
    }
    // Validate the actual inserted whole dataset before committing the source
    // transaction; any exception rolls back schema/data created by this call.
    if(!catalog.populated())throw DatabaseError("PetRoom source import did not qualify");
    transaction.commit();
}
}
