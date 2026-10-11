#include "protocol/RecoveredRemoteActor.h"
#include "protocol/DiagnosticRemoteActor.h"
#include "protocol/RecoveredWorldEntry.h"
#include <stdexcept>
#include <type_traits>
#include <iostream>

void require(bool value) { if(!value) throw std::runtime_error("Remote actor codec regression"); }
template<class Codec>
void event_bounds(std::uint8_t opcode) {
    static_assert(!std::is_default_constructible_v<typename Codec::Record>);
    static_assert(!Codec::runtime_emission_enabled);
    typename Codec::LogicalRecord bytes{};bytes[0]=opcode;
    for(std::size_t n=0;n<bytes.size();++n)
        require(!Codec::parse_logical(std::span(bytes).first(n)));
    std::array<std::uint8_t,Codec::logical_size+1> oversized{};oversized[0]=opcode;
    require(!Codec::parse_logical(oversized));
    for(unsigned op=0;op<256;++op) {
        bytes[0]=static_cast<std::uint8_t>(op);
        require(Codec::parse_logical(bytes).has_value()==(op==opcode));
    }
    bytes[0]=opcode;
    for(std::size_t offset=1;offset<bytes.size();++offset)for(unsigned v=0;v<256;++v) {
        auto changed=bytes;changed[offset]=static_cast<std::uint8_t>(v);
        const auto parsed=Codec::parse_logical(changed);require(parsed.has_value());
        require(Codec::encode_logical(*parsed)==changed);
    }
    const auto owned=Codec::parse_logical(bytes);require(owned.has_value());
    for(std::uint64_t id=0;id<=65535;++id) {
        const auto changed=Codec::with_identity(*owned,id);require(changed.has_value());
        require(changed->identity()==id);
        auto expected=bytes;expected[1]=static_cast<std::uint8_t>(id);
        expected[2]=static_cast<std::uint8_t>(id>>8);
        require(Codec::encode_logical(*changed)==expected);
    }
    require(!Codec::with_identity(*owned,65536));
    require(!Codec::with_identity(*owned,~std::uint64_t{0}));
    bytes.fill(0xff);
    require(Codec::encode_logical(*owned)[0]==opcode);
}
int main() {
    using Codec=god2::RecoveredRemoteActor;
    static_assert(!std::is_default_constructible_v<Codec::Record>);
    static_assert(!Codec::runtime_emission_enabled);
    try {
        const auto text_source=Codec::parse_logical(god2::DiagnosticRemoteActor::logical(0,0)).value();
        const auto original=Codec::encode_logical(text_source);
        for(unsigned value=1;value<256;++value) for(std::size_t length=0;length<=15;++length) {
            std::array<std::uint8_t,15> input;input.fill(static_cast<std::uint8_t>(value));
            const auto field=std::span<const std::uint8_t>(input).first(length);
            const auto changed=Codec::with_text_fields(text_source,{field,field,field});
            require(changed.has_value());
            const auto bytes=Codec::encode_logical(*changed);
            for(std::size_t i=0;i<bytes.size();++i) {
                if(i<29 || i>=77) require(bytes[i]==original[i]);
                else require(bytes[i]==((i-29)%16<length ? value : 0));
            }
            require(Codec::parse_logical(bytes).has_value());
        }
        for(std::size_t index=0;index<3;++index) {
            std::array<std::span<const std::uint8_t>,3> fields{};
            std::array<std::uint8_t,16> oversized;oversized.fill('X');
            fields[index]=oversized;
            require(!Codec::with_text_fields(text_source,fields));
            std::array<std::uint8_t,3> embedded{'A',0,'B'};
            fields[index]=embedded;
            require(!Codec::with_text_fields(text_source,fields));
        }
        require(Codec::encode_logical(text_source)==original);
        for(unsigned language=0;language<2;++language) {
            const auto spawn=god2::DiagnosticRemoteActor::logical(0,language);
            const auto record=Codec::parse_logical(spawn);require(record.has_value());
            require(record->identity()==7 && record->x()==18 && record->y()==12);
            require(spawn[4]==language*2 && spawn[21]==1 && spawn[27]==0x81);
            const auto move=god2::RecoveredRemoteActorMove::parse_logical(god2::DiagnosticRemoteActor::logical(1,language));
            require(move && move->identity()==7 && move->x()==19 && move->y()==12 && move->state()==0);
            const auto removed=god2::RecoveredRemoteActorRemove::parse_logical(god2::DiagnosticRemoteActor::logical(2,language));
            require(removed && removed->identity()==7);
        }
        for(unsigned value=0;value<=0xffff;++value) {
            const bool allowed=value==0 || value==1 || value==0x100 || value==0x200 || value==0x400 || value==0x800 || value==0x1000;
            bool rejected_status=false;
            try {
                const auto logical=god2::DiagnosticRemoteActor::status(static_cast<std::uint16_t>(value));
                const auto parsed=god2::RecoveredRemoteActorMove::parse_logical(logical);
                require(allowed && parsed && parsed->state()==value && parsed->identity()==7 && parsed->x()==18 && parsed->y()==12);
            } catch(const std::invalid_argument&) { rejected_status=true; }
            require(rejected_status!=allowed);
        }
        bool rejected=false;
        try { (void)god2::DiagnosticRemoteActor::logical(3,0); } catch(const std::invalid_argument&) { rejected=true; }
        require(rejected);
        rejected=false;
        try { (void)god2::DiagnosticRemoteActor::logical(0,2); } catch(const std::invalid_argument&) { rejected=true; }
        require(rejected);
        using Move=god2::RecoveredRemoteActorMove;
        using Remove=god2::RecoveredRemoteActorRemove;
        event_bounds<Move>(0x5e);event_bounds<Remove>(0x73);
        Move::LogicalRecord move{};move.fill(0xff);move[0]=0x5e;
        const auto moved=Move::parse_logical(move);require(moved.has_value());
        require(moved->identity()==65535 && moved->state()==65535);
        require(moved->x()==2047 && moved->y()==2047);
        const std::uint32_t target=19u|(12u<<11)|(0x7fu<<25);
        for(unsigned i=0;i<4;++i)move[9+i]=static_cast<std::uint8_t>(target>>(8*i));
        const auto targeted=Move::parse_logical(move);require(targeted.has_value());
        require(targeted->x()==19 && targeted->y()==12);
        require(Move::encode_logical(*targeted)==move);
        Remove::LogicalRecord removed{0x73,0xff,0xff,0xab,0xcd};
        const auto removal=Remove::parse_logical(removed);require(removal.has_value());
        require(removal->identity()==65535 && Remove::encode_logical(*removal)==removed);
        Codec::LogicalRecord bytes{};bytes[0]=0x6f;
        bytes[1]=0xff;bytes[2]=0x3f;
        const std::uint32_t packed=(86u<<2)|(71u<<17)|3u;
        for(unsigned i=0;i<4;++i)bytes[13+i]=static_cast<std::uint8_t>(packed>>(8*i));
        const auto parsed=Codec::parse_logical(bytes);require(parsed.has_value());
        require(parsed->identity()==4095 && parsed->x()==86 && parsed->y()==71);
        require(Codec::encode_logical(*parsed)==bytes);
        for(std::uint64_t x=0;x<=32767;++x) {
            const auto y=32767-x;
            const auto positioned=Codec::with_position(*parsed,x,y);require(positioned.has_value());
            require(positioned->x()==x && positioned->y()==y && positioned->identity()==parsed->identity());
            auto expected=bytes;
            const auto point=static_cast<std::uint32_t>(3|(x<<2)|(y<<17));
            for(unsigned i=0;i<4;++i)expected[13+i]=static_cast<std::uint8_t>(point>>(8*i));
            require(Codec::encode_logical(*positioned)==expected);
        }
        for(const auto outside:{32768ull,65536ull,~0ull}) {
            require(!Codec::with_position(*parsed,outside,0));
            require(!Codec::with_position(*parsed,0,outside));
        }
        for(unsigned first=0;first<7;++first)for(unsigned second=0;second<7;++second) {
            auto body=god2::RecoveredWorldEntry::historical_body;
            body[13]=static_cast<std::uint8_t>((body[13]&0x1f)|(first<<5));
            body[15]=static_cast<std::uint8_t>((body[15]&0x1f)|(second<<5));
            const auto projected=Codec::with_normal_world_components(*parsed,body);
            require(projected.has_value());
            const auto result=Codec::encode_logical(*projected);
            auto expected=bytes;
            expected[2]=static_cast<std::uint8_t>((expected[2]&0x3f)|((body[2]&3)<<6));
            expected[3]=static_cast<std::uint8_t>((expected[3]&0xe0)|((body[2]>>2)&0x1f));
            expected[6]=static_cast<std::uint8_t>((expected[6]&0x80)|body[6]);
            expected[79]=body[34];expected[80]=body[35];
            std::copy_n(body.begin()+12,8,expected.begin()+21);
            require(result==expected);
            require(projected->identity()==parsed->identity() && projected->x()==parsed->x() && projected->y()==parsed->y());
            for(std::size_t n=0;n<body.size();++n)
                require(!Codec::with_normal_world_components(*parsed,std::span(body).first(n)));
            body[32]=1;require(!Codec::with_normal_world_components(*parsed,body));
            body[32]=0;body[33]=1;require(!Codec::with_normal_world_components(*parsed,body));
            body[33]=0;body[6]=128;require(!Codec::with_normal_world_components(*parsed,body));
        }
        std::array<std::uint8_t,37> oversized_body{};
        require(!Codec::with_normal_world_components(*parsed,oversized_body));
        for(unsigned selector=0;selector<128;++selector) {
            auto body=god2::RecoveredWorldEntry::historical_body;
            body[2]=static_cast<std::uint8_t>(selector|0x80);
            body[6]=static_cast<std::uint8_t>(selector);
            auto flagged=bytes;flagged[2]|=0xc0;flagged[3]=0xff;flagged[4]=0xff;flagged[6]=0xff;
            const auto original=Codec::parse_logical(flagged);require(original.has_value());
            const auto projected=Codec::with_normal_world_components(*original,body);require(projected.has_value());
            const auto result=Codec::encode_logical(*projected);
            require(((result[2]>>6)|((result[3]&0x1f)<<2))==selector);
            require((result[3]&0xe0)==0xe0 && result[4]==0xff && result[6]==(selector|0x80));
            for(const auto offset:{77,78}) {
                auto special=flagged;special[offset]=1;
                const auto record=Codec::parse_logical(special);require(record.has_value());
                require(!Codec::with_normal_world_components(*record,body));
            }
        }
        for(std::uint64_t id=0;id<=4095;++id) {
            const auto changed=Codec::with_identity(*parsed,id);require(changed.has_value());
            require(changed->identity()==id);
            auto expected=bytes;expected[1]=static_cast<std::uint8_t>(id);
            expected[2]=static_cast<std::uint8_t>((expected[2]&0xf0)|(id>>8));
            require(Codec::encode_logical(*changed)==expected);
        }
        for(const auto id:{4096ull,16383ull,65536ull,~0ull})
            require(!Codec::with_identity(*parsed,id));
        for(std::size_t n=0;n<bytes.size();++n) require(!Codec::parse_logical(std::span(bytes).first(n)));
        std::array<std::uint8_t,82> oversized{};oversized[0]=0x6f;
        require(!Codec::parse_logical(oversized));
        for(unsigned op=0;op<256;++op) {
            auto changed=bytes;changed[0]=static_cast<std::uint8_t>(op);
            require(Codec::parse_logical(changed).has_value()==(op==0x6f));
        }
        for(const auto offset:{29u,45u,61u}) {
            auto changed=bytes;
            std::fill_n(changed.begin()+offset,16,0xff);
            require(!Codec::parse_logical(changed));
            for(unsigned end=0;end<16;++end) {
                changed[offset+end]=0;
                const auto valid=Codec::parse_logical(changed);require(valid.has_value());
                require(Codec::encode_logical(*valid)==changed);
                changed[offset+end]=0xff;
            }
        }
        for(unsigned offset=1;offset<81;++offset)for(unsigned value=0;value<256;++value) {
            auto changed=bytes;changed[offset]=static_cast<std::uint8_t>(value);
            const auto record=Codec::parse_logical(changed);require(record.has_value());
            require(Codec::encode_logical(*record)==changed);
        }
        bytes.fill(0xff);
        require(Codec::encode_logical(*parsed)[0]==0x6f);
        std::cout<<"Remote actor owning codec/bounds passed; emission disabled\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
