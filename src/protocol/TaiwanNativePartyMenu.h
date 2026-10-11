#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>
namespace god2 {
// Same149c native shapes. Selectors and post-NUL bytes are opaque, not rights.
struct TaiwanNativePartyMenu {
    struct Request {
        std::vector<std::uint8_t> logical;
        std::uint8_t opcode() const noexcept {return logical[0];}
        std::uint16_t target() const noexcept {return logical.size()==5?static_cast<std::uint16_t>(std::uint16_t{logical[1]}|(std::uint16_t{logical[2]}<<8)):0;}
        std::array<std::uint8_t,24> query() const {
            std::array<std::uint8_t,24> out{};
            if(logical.size()==25)std::copy_n(logical.begin()+1,24,out.begin());
            return out;
        }
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> in) {
        if(in.empty())return {};
        const auto op=in[0];
        if(op==0x8e || op==0x8f) {
            if(in.size()!=25)return {};
            const auto end=std::find(in.begin()+3,in.end(),0);
            if(end==in.end() || end-(in.begin()+3)>20)return {};
        } else if(op==0x8d) {if(in.size()!=2 || (in[1]!=1 && in[1]!=2))return {};}
        else if(op==0x92) {if(in.size()!=2 || (in[1]!=0xff && in[1]!=1))return {};}
        else if(op==0x90 || op==0x91) {if(in.size()!=5)return {};}// Preserve full caller/pointer highWORD; not a nonce.
        else return {};
        return Request{std::vector<std::uint8_t>(in.begin(),in.end())};
    }
    struct DetailRow {
        std::uint8_t level,status;
        std::array<std::uint8_t,4> photo;
        std::string name;
    };
    static std::optional<std::vector<std::uint8_t>> detail(std::uint16_t target,std::span<const DetailRow> rows) {
        if(!target || rows.empty() || rows.size()>4)return {};
        const auto size=7+22*rows.size();std::vector<std::uint8_t> out(size,0);
        out[0]=0xab;out[1]=static_cast<std::uint8_t>(size);out[2]=static_cast<std::uint8_t>(size>>8);
        out[3]=static_cast<std::uint8_t>(target);out[4]=static_cast<std::uint8_t>(target>>8);out[5]=static_cast<std::uint8_t>(rows.size());
        // CUSTOM-0098 canonical opaque header0; supplied status is presentation,
        // never a recovered official online/profession permission policy.
        for(std::size_t i=0;i<rows.size();++i) {
            const auto& row=rows[i];const auto at=7+22*i;
            if(row.name.empty() || row.name.size()>14 || row.name.find('\0')!=row.name.npos)return {};
            out[at]=row.level;out[at+1]=row.status;std::copy(row.photo.begin(),row.photo.end(),out.begin()+at+2);
            std::copy(row.name.begin(),row.name.end(),out.begin()+at+6);
        }
        return out;
    }
    static std::optional<std::vector<std::uint8_t>> withdrawn(std::uint16_t target) {
        if(!target)return {};
        return std::vector<std::uint8_t>{0xa8,static_cast<std::uint8_t>(target),static_cast<std::uint8_t>(target>>8)};
    }
    static std::optional<std::vector<std::uint8_t>> description(std::uint16_t target,const std::array<std::uint8_t,22>& raw) {
        const auto end=std::find(raw.begin(),raw.end(),0);
        if(!target || end==raw.end() || end-raw.begin()>20)return {};
        std::vector<std::uint8_t> out(27,0);out[0]=0xa9;out[1]=static_cast<std::uint8_t>(target);out[2]=static_cast<std::uint8_t>(target>>8);
        // CUSTOM-0099 flags remain0. Only text through NUL is copied by native;
        // caller must separately qualify the old retained destination tail.
        std::copy(raw.begin(),end+1,out.begin()+4);return out;
    }
    struct Row {
        std::uint16_t native_actor;
        std::uint8_t level,profession;
        std::array<std::uint8_t,22> description;
        std::string name;
    };
    static std::optional<std::vector<std::uint8_t>> list(std::span<const Row> rows) {
        if(rows.size()>6)return {};
        const auto size=5+44*rows.size();std::vector<std::uint8_t> out(size,0);
        out[0]=0xa7;out[1]=static_cast<std::uint8_t>(size);out[2]=static_cast<std::uint8_t>(size>>8);
        // CUSTOM-0097 canonical opaque header/flags0; not recovered rule.
        out[4]=static_cast<std::uint8_t>(rows.size());
        for(std::size_t i=0;i<rows.size();++i) {
            const auto& row=rows[i];const auto at=5+44*i;
            if(!row.native_actor || row.name.empty() || row.name.size()>14 || row.name.find('\0')!=row.name.npos ||
               std::find(row.description.begin(),row.description.end(),0)==row.description.end())return {};
            out[at]=static_cast<std::uint8_t>(row.native_actor);out[at+1]=static_cast<std::uint8_t>(row.native_actor>>8);
            out[at+3]=row.level;std::copy(row.description.begin(),row.description.end(),out.begin()+at+4);
            out[at+26]=row.profession;std::copy(row.name.begin(),row.name.end(),out.begin()+at+27);
        }
        return out;
    }
};
}
