#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>
// PRIVATE NATIVE_CLIENT_DISPLAY_MODEL_ONLY. Not server relationship authority.
namespace native_relation_private {
using Byte=std::uint8_t;
using Name=std::array<Byte,16>;
enum class ClientIntent:Byte { propose_alliance=1, declare_war=5, remove_alliance=8, remove_war=9 };
// Original EBF92 loads ProgramMsg9/192/193/194/195/196/797/798 into
// 597EC0, stride8. F0D50 renders raw_type&7F through that exact table.
// These are client display kinds, not original server consent/timing rules.
enum class DisplayKind:Byte {
  empty=0, alliance=1, alliance_invitation=2, invited_to_alliance=3,
  defense=4, attack=5, war_declaration=6, declared_against=7
};
struct Action { Byte subtype{};Name name{}; friend bool operator==(const Action&,const Action&)=default; };
struct Row { std::uint32_t opaque_id{};Byte raw_type{};std::array<Byte,3> opaque{};Name name{}; friend bool operator==(const Row&,const Row&)=default; };
inline std::optional<ClientIntent> intent(const Action&a) {
  switch(a.subtype){case 1:case 5:case 8:case 9:return static_cast<ClientIntent>(a.subtype);default:return std::nullopt;}
}
inline std::optional<Action> decode76(std::span<const Byte>b) {
  if(b.size()!=18||b[0]!=0x76)return std::nullopt;Action a;a.subtype=b[1];for(unsigned i=0;i<16;++i)a.name[i]=b[i+2];return a;
}
inline std::array<Byte,18> encode76(const Action&a) {std::array<Byte,18>b{};b[0]=0x76;b[1]=a.subtype;for(unsigned i=0;i<16;++i)b[i+2]=a.name[i];return b;}
inline std::uint32_t read_id(std::span<const Byte>b) {return std::uint32_t(b[0])|(std::uint32_t(b[1])<<8)|(std::uint32_t(b[2])<<16)|(std::uint32_t(b[3])<<24);}
inline void put_id(std::span<Byte>b,std::uint32_t id) {for(unsigned i=0;i<4;++i)b[i]=Byte(id>>(i*8));}
inline std::optional<Row> decode95(std::span<const Byte>b) {
  if(b.size()!=25||b[0]!=0x95)return std::nullopt;Row r;r.opaque_id=read_id(b.subspan(1));r.raw_type=b[5];for(unsigned i=0;i<3;++i)r.opaque[i]=b[i+6];for(unsigned i=0;i<16;++i)r.name[i]=b[i+9];return r;
}
inline std::array<Byte,25> encode95(const Row&r) {std::array<Byte,25>b{};b[0]=0x95;put_id(std::span<Byte>(b).subspan(1),r.opaque_id);b[5]=r.raw_type;for(unsigned i=0;i<3;++i)b[i+6]=r.opaque[i];for(unsigned i=0;i<16;++i)b[i+9]=r.name[i];return b;}
inline std::optional<std::uint32_t> decode96(std::span<const Byte>b) {if(b.size()!=5||b[0]!=0x96)return std::nullopt;return read_id(b.subspan(1));}
inline std::array<Byte,5> encode96(std::uint32_t id) {std::array<Byte,5>b{};b[0]=0x96;put_id(std::span<Byte>(b).subspan(1),id);return b;}
inline Byte display_type(const Row&r){return r.raw_type&0x7f;}
inline bool display_flag(const Row&r){return (r.raw_type&0x80)!=0;}
inline std::optional<DisplayKind> display_kind(const Row&r){
  const auto kind=display_type(r);if(kind>7)return std::nullopt;
  return static_cast<DisplayKind>(kind);
}
// F0DF3..F0E1C passes record+5,+6,+7 (logical6,7,8) to the literal
// "%2d/%2d %02d:00" at1966C4. The fields display month/day/hour. There is
// no year, minute, timezone, expiry or countdown unit in this observation.
// Preserve all raw BYTE values; calendar validation belongs to a qualified
// future server scheduling policy, not the native wire codec.
struct DateDisplay {Byte month{},day{},hour{};bool operator==(const DateDisplay&)const=default;};
inline DateDisplay date_display(const Row&r){return {r.opaque[0],r.opaque[1],r.opaque[2]};}
// EE7ED..EE826 chooses native76/8 for exact raw kinds1..3 and76/9 for
// exact raw kinds4..7. Unlike rendering, this UI decision DOES NOT mask80.
// This only predicts the client's request; it never supplies SQL authority.
inline std::optional<ClientIntent> removal_intent(const Row&r){
  switch(r.raw_type){
    case 1:case 2:case 3:return ClientIntent::remove_alliance;
    case 4:case 5:case 6:case 7:return ClientIntent::remove_war;
    default:return std::nullopt;
  }
}
// Exact bounded native95/96 data mutation prefix. Does not model sorting/render.
class DisplayCache {
  std::vector<Row> rows_;
  void erase_swap(std::size_t i){rows_[i]=rows_.back();rows_.pop_back();}
 public:
  explicit DisplayCache(std::vector<Row> r={}):rows_(std::move(r)){}
  const auto& rows()const{return rows_;}
  bool receive95(const Row&r) {
    if(rows_.size()>=50)return false; // Native cap BEFORE duplicate lookup.
    std::size_t i=0;while(i<rows_.size()&&rows_[i].opaque_id!=r.opaque_id)++i;
    if(i==rows_.size()||r.raw_type==6||r.raw_type==7){rows_.push_back(r);return true;}
    if(r.raw_type==0){erase_swap(i);return true;}
    rows_[i]=r;
    if(r.raw_type==4||r.raw_type==5)for(++i;i<rows_.size();++i)
      if(rows_[i].opaque_id==r.opaque_id&&(rows_[i].raw_type==6||rows_[i].raw_type==7))erase_swap(i);
    return true;
  }
  bool receive96(std::uint32_t id) {for(std::size_t i=0;i<rows_.size();++i)if(rows_[i].opaque_id==id){erase_swap(i);return true;}return false;}
};
}
