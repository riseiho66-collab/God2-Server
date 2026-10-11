#include "protocol/RecoveredMovement.h"
#include <algorithm>
#include <charconv>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <system_error>
#include <vector>

namespace {
using Movement=god2::RecoveredMovement;
constexpr Movement::Frame zero_wire{0x0a,0x00,0x2b,0x2b,0xfd,0xfd,0xfd,0xfd,0xfd,0x51};
constexpr Movement::Frame mixed_wire{0x0a,0x00,0x2b,0x5f,0x43,0xdc,0x75,0xa7,0x3e,0x92};
static_assert([] {
    for(std::size_t i=0;i<8;++i) if(god2::recovered_zero_seed_key[i]!=0) return false;
    return true;
}(),"Movement fixtures require the statically known zero-seed key prefix");

void require(bool value,const char* message) {
    if(!value) throw std::runtime_error(message);
}
void expect_request(std::span<const std::uint8_t> wire,const Movement::Request& expected) {
    const auto request=Movement::parse(wire);
    require(request.has_value(),"Movement frame rejected");
    require(request->x==expected.x && request->y==expected.y &&
            request->sequence==expected.sequence && request->opaque_tail==expected.opaque_tail,
            "Movement fields changed");
}

// Independent fixture construction: the known key prefix is zero for this frame.
Movement::Frame fixture(Movement::Frame plain) {
    unsigned checksum=0;
    for(std::size_t i=0;i+1<plain.size();++i) checksum+=plain[i]+0x3cu;
    plain.back()=static_cast<std::uint8_t>(checksum);
    auto wire=plain;
    for(std::size_t i=2;i<plain.size();++i)
        wire[i]=static_cast<std::uint8_t>(plain[i]+(i==2?0:plain[i-1])-3);
    return wire;
}

int hex_digit(char c) {
    if(c>='0' && c<='9') return c-'0';
    if(c>='a' && c<='f') return c-'a'+10;
    if(c>='A' && c<='F') return c-'A'+10;
    return -1;
}
std::optional<Movement::Frame> read_hex(std::string_view text) {
    if(text.size()!=20) return std::nullopt;
    Movement::Frame frame{};
    for(std::size_t i=0;i<frame.size();++i) {
        const auto high=hex_digit(text[2*i]),low=hex_digit(text[2*i+1]);
        if(high<0 || low<0) return std::nullopt;
        frame[i]=static_cast<std::uint8_t>(high*16+low);
    }
    return frame;
}
std::optional<std::uint8_t> read_sequence(std::string_view text) {
    unsigned value=0;
    const auto result=std::from_chars(text.data(),text.data()+text.size(),value);
    if(result.ec!=std::errc{} || result.ptr!=text.data()+text.size() || value>255)
        return std::nullopt;
    return static_cast<std::uint8_t>(value);
}

std::vector<std::uint8_t> batch_fixture(std::span<const std::uint8_t> logical) {
    const auto length=logical.size()+3;
    std::vector<std::uint8_t> plain{static_cast<std::uint8_t>(length),static_cast<std::uint8_t>(length>>8)};
    plain.insert(plain.end(),logical.begin(),logical.end());
    unsigned checksum=0;
    for(auto byte:plain) checksum+=byte+0x3cu;
    plain.push_back(static_cast<std::uint8_t>(checksum));
    auto wire=plain;
    for(std::size_t i=2;i<plain.size();++i)
        wire[i]=static_cast<std::uint8_t>((plain[i]^god2::recovered_zero_seed_key[(i-2)%256])+
                                        (i==2?0:plain[i-1])-3);
    return wire;
}

void batch_assertions() {
    std::vector<std::uint8_t> logical{0x2e,0x34,0x12,0xcd,0xab,255,0x42,0x2e,255,255,0,0,0,0};
    const auto wire=batch_fixture(logical);
    // Length 17, two complete records, then one checksum, all within the zero prefix.
    require(wire==std::vector<std::uint8_t>{0x11,0,0x2b,0x5f,0x43,0xdc,0x75,0xa7,0x3e,0x6d,
                0x2a,0xfb,0xfc,0xfd,0xfd,0xfd,0x27},"Two-record wire fixture changed");
    const auto batch=Movement::parse_batch(wire);
    require(batch && batch->size()==2,"Two-record batch rejected");
    require((*batch)[0].x==0x1234 && (*batch)[0].y==0xabcd && (*batch)[0].sequence==255 &&
            (*batch)[0].opaque_tail==0x42 && (*batch)[1].x==65535 && (*batch)[1].y==0 &&
            (*batch)[1].sequence==0 && (*batch)[1].opaque_tail==0,"Batch fields changed");
    require(!Movement::parse(wire),"Single-record API accepted a batch");
    logical[7]=0x5d;
    require(!Movement::parse_batch(batch_fixture(logical)),"Invalid second opcode partially accepted");
    auto bad_crc=wire;bad_crc.back()^=1;
    require(!Movement::parse_batch(bad_crc),"Batch checksum bypass");
    auto bad_length=wire;bad_length[1]=1;
    require(!Movement::parse_batch(bad_length),"Batch header length mismatch accepted");
    require(!Movement::parse_batch({}),"Empty input accepted");
    require(!Movement::parse_batch(batch_fixture({})),"Empty logical batch accepted");
    logical.pop_back();
    require(!Movement::parse_batch(batch_fixture(logical)),"Partial record accepted");
    auto concatenated=wire;concatenated.insert(concatenated.end(),wire.begin(),wire.end());
    require(!Movement::parse_batch(concatenated),"Concatenated frames accepted");
    for(std::size_t length=0;length<wire.size();++length)
        require(!Movement::parse_batch(std::span(wire).first(length)),"Truncated batch accepted");

    logical.clear();
    constexpr std::size_t max_records=Movement::max_logical_size/7;
    static_assert(max_records==365);
    for(std::size_t i=0;i<max_records;++i) {
        const std::array<std::uint8_t,7> record{0x2e,static_cast<std::uint8_t>(i),
            static_cast<std::uint8_t>(i>>8),255,255,static_cast<std::uint8_t>(i),static_cast<std::uint8_t>(255-i)};
        logical.insert(logical.end(),record.begin(),record.end());
    }
    const auto maximum_wire=batch_fixture(logical);
    const auto maximum=Movement::parse_batch(maximum_wire);
    require(maximum && maximum->size()==max_records,"Maximum batch rejected");
    for(std::size_t i=0;i<max_records;++i)
        require((*maximum)[i].x==i && (*maximum)[i].y==65535 &&
                (*maximum)[i].sequence==static_cast<std::uint8_t>(i) &&
                (*maximum)[i].opaque_tail==static_cast<std::uint8_t>(255-i),"Cyclic key or batch fields changed");
    auto bad_last=maximum_wire;bad_last.back()^=1;
    require(!Movement::parse_batch(bad_last),"Maximum batch checksum bypass");
    logical[logical.size()-7]=0x5d;
    require(!Movement::parse_batch(batch_fixture(logical)),"Invalid final opcode partially accepted");
    logical[logical.size()-7]=0x2e;
    logical.insert(logical.end(),{0x2e,0,0,0,0,0,0});
    require(!Movement::parse_batch(batch_fixture(logical)),"366-record oversized batch accepted");
    logical.resize(Movement::max_logical_size);
    require(!Movement::parse_batch(batch_fixture(logical)),"Logical limit with partial record accepted");
}

void periodic_assertions() {
    const std::array<std::uint8_t,5> native_tick{5,0,0x2d,0x2d,0x22};
    const auto tick=Movement::parse_world_batch(native_tick);
    require(tick && tick->ticks==1 && tick->movements.empty(),"Current 30 00 rejected");
    require(!Movement::parse_batch(native_tick),"Movement-only API accepted tick");
    const std::vector<std::uint8_t> logical{0x30,0,0x2e,18,0,12,0,1,0xa5,0x30,0};
    const auto periodic_mixed_wire=batch_fixture(logical);
    const auto mixed=Movement::parse_world_batch(periodic_mixed_wire);
    require(mixed && mixed->ticks==2 && mixed->movements.size()==1 &&
            mixed->movements[0].x==18 && mixed->movements[0].y==12 &&
            mixed->movements[0].sequence==1 && mixed->movements[0].opaque_tail==0xa5,
            "Mixed periodic queue fields changed");
    require(!Movement::parse_batch(periodic_mixed_wire),"Movement-only API accepted mixed queue");
    for(const auto& bad:std::vector<std::vector<std::uint8_t>>{
            {},{0x30},{0x30,1},{0x30,0,0},{0x30,0,0x2e},
            {0x2e,18,0,12,0,1,0xa5,0x30,1},{0x31,0}})
        require(!Movement::parse_world_batch(batch_fixture(bad)),"Invalid periodic batch accepted");
    for(std::size_t size=0;size<native_tick.size();++size)
        require(!Movement::parse_world_batch(std::span(native_tick).first(size)),"Truncated tick accepted");
    for(std::size_t i=0;i<native_tick.size();++i) {
        auto bad=native_tick;bad[i]^=1;
        require(!Movement::parse_world_batch(bad),"Corrupt tick accepted");
    }
    std::vector<std::uint8_t> maximum;
    for(std::size_t i=0;i<Movement::max_logical_size/2;++i) maximum.insert(maximum.end(),{0x30,0});
    const auto many=Movement::parse_world_batch(batch_fixture(maximum));
    require(many && many->ticks==1280 && many->movements.empty(),"Maximum tick batch rejected");
    maximum.insert(maximum.end(),{0x30,0});
    require(!Movement::parse_world_batch(batch_fixture(maximum)),"Oversized tick batch accepted");
}

void assertions() {
    batch_assertions();
    periodic_assertions();
    expect_request(zero_wire,{0,0,0,0});
    expect_request(mixed_wire,{0x1234,0xabcd,255,0x42});
    require(Movement::encode({0,0,0,0})==zero_wire,"Zero request wire changed");
    require(Movement::encode({0x1234,0xabcd,255,0x42})==mixed_wire,"Mixed request wire changed");
    require(Movement::ack(0)==Movement::AckFrame{5,0,0x5a,0x5a,0x4f},"ACK zero wire changed");
    require(Movement::ack(255)==Movement::AckFrame{5,0,0x5a,0x59,0x4d},"ACK 255 wire changed");

    for(unsigned tail=0;tail<256;++tail) for(unsigned sequence:{0u,255u})
        for(unsigned x:{0u,1u,32768u,65535u}) for(unsigned y:{0u,1u,32768u,65535u}) {
            const Movement::Request expected{static_cast<std::uint16_t>(x),static_cast<std::uint16_t>(y),
                static_cast<std::uint8_t>(sequence),static_cast<std::uint8_t>(tail)};
            const auto wire=fixture({10,0,0x2e,
                static_cast<std::uint8_t>(x),static_cast<std::uint8_t>(x>>8),
                static_cast<std::uint8_t>(y),static_cast<std::uint8_t>(y>>8),
                expected.sequence,expected.opaque_tail,0});
            expect_request(wire,expected);
            require(Movement::encode(expected)==wire,"Fixture encoder mismatch");
        }

    for(unsigned sequence=0;sequence<256;++sequence) {
        const auto wire=Movement::ack(static_cast<std::uint8_t>(sequence));
        const auto opcode=static_cast<std::uint8_t>(wire[2]+3);
        const auto body=static_cast<std::uint8_t>(wire[3]+3-opcode);
        const auto checksum=static_cast<std::uint8_t>(wire[4]+3-body);
        require(wire[0]==5 && wire[1]==0 && opcode==0x5d && body==sequence &&
                checksum==static_cast<std::uint8_t>(5+0x5d+sequence+4*0x3c),"ACK frame mismatch");
        require(!Movement::parse(wire),"ACK accepted as movement");
        expect_request(mixed_wire,{0x1234,0xabcd,255,0x42});
    }

    for(std::size_t length=0;length<zero_wire.size();++length)
        require(!Movement::parse(std::span(zero_wire).first(length)),"Truncated frame accepted");
    for(std::size_t length:{11u,20u,256u}) {
        std::vector<std::uint8_t> wire(length,0);
        std::copy(zero_wire.begin(),zero_wire.end(),wire.begin());
        if(length==20) std::copy(zero_wire.begin(),zero_wire.end(),wire.begin()+10);
        require(!Movement::parse(wire),"Trailing bytes or multiple frames accepted");
    }
    for(std::size_t i:{0u,1u,9u}) for(unsigned bit=0;bit<8;++bit) {
        auto wire=mixed_wire;wire[i]^=static_cast<std::uint8_t>(1u<<bit);
        require(!Movement::parse(wire),"Corrupt length or checksum accepted");
    }
    // Change one decoded body byte while retaining the old checksum. Arbitrary
    // ciphertext flips can cancel in this additive checksum and are not all detectable.
    auto stale_checksum=mixed_wire;++stale_checksum[3];++stale_checksum[4];
    require(!Movement::parse(stale_checksum),"Changed body with stale checksum accepted");
    for(unsigned opcode=0;opcode<256;++opcode) {
        if(opcode==0x2e) continue;
        require(!Movement::parse(fixture({10,0,static_cast<std::uint8_t>(opcode),0,0,0,0,0,0,0})),
                "Wrong opcode with valid checksum accepted");
    }
    require(read_hex("0A002B5F43DC75A73E92")==mixed_wire,"Uppercase hex rejected");
    for(std::string_view text:{"","0","0a002b5f43dc75a73e9g","0a002b5f43dc75a73e9200"," 0a002b5f43dc75a73e92"})
        require(!read_hex(text),"Invalid hex accepted");
    require(read_sequence("0")==0 && read_sequence("255")==255,"Sequence endpoints rejected");
    for(std::string_view text:{"","-1","+1","256","1x"," 1","1 ","99999999999999999999"})
        require(!read_sequence(text),"Invalid sequence accepted");
}
}

int main(int argc,char** argv) {
    try {
        if(argc==3 && std::string_view(argv[1])=="--decode") {
            const auto frame=read_hex(argv[2]);
            require(frame.has_value(),"Invalid movement hex");
            const auto request=Movement::parse(*frame);
            require(request.has_value(),"Invalid movement frame");
            std::cout<<request->x<<' '<<request->y<<' '<<static_cast<unsigned>(request->sequence)
                     <<' '<<static_cast<unsigned>(request->opaque_tail)<<'\n';
        } else if(argc==3 && std::string_view(argv[1])=="--ack") {
            const auto sequence=read_sequence(argv[2]);
            require(sequence.has_value(),"Invalid sequence");
            constexpr char digits[]="0123456789abcdef";
            for(auto byte:Movement::ack(*sequence)) std::cout<<digits[byte>>4]<<digits[byte&15];
            std::cout<<'\n';
        } else {
            require(argc==1,"Expected --decode HEX or --ack sequence");
            assertions();
            std::cout<<"Recovered movement assertions passed\n";
        }
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
    return 0;
}
