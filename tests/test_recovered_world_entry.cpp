#include "protocol/RecoveredWorldEntry.h"
#include "protocol/RecoveredWorldReady.h"
#include "protocol/RecoveredWorldStateCandidate.h"
#include <iostream>
#include <bit>
#include <limits>
#include <string>
#include <vector>

namespace {
void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }
std::vector<std::uint8_t> encode(std::span<const std::uint8_t> logical) {
    std::vector<std::uint8_t> frame{static_cast<std::uint8_t>(logical.size()+3),0};
    std::uint8_t checksum=static_cast<std::uint8_t>(frame[0]+2*0x3c),previous=0;
    for(auto b:logical) checksum=static_cast<std::uint8_t>(checksum+b+0x3c);
    for(std::size_t i=0;i<=logical.size();++i) {
        const auto plain=i<logical.size()?logical[i]:checksum;
        frame.push_back(static_cast<std::uint8_t>((plain^god2::recovered_zero_seed_key[i])+previous-3));
        previous=plain;
    }
    return frame;
}
void ready_assertions() {
    using Ready=god2::RecoveredWorldReady;
    const std::array<std::uint8_t,9> logical{0x1f,0,0x23,0,0x1c,0x34,0x12,1,0};
    for(const auto& groups:std::vector<std::vector<std::size_t>>{{9},{2,7},{4,5},{2,2,5}}) {
        std::vector<std::uint8_t> wire;std::size_t offset=0;
        for(auto size:groups) {
            const auto part=encode(std::span(logical).subspan(offset,size));
            wire.insert(wire.end(),part.begin(),part.end());offset+=size;
        }
        Ready whole(0x1234);
        require(whole.feed(wire)==Ready::Result::Complete,"Grouped world tail rejected");
        require(whole.config_flag()==1,"World tail config flag lost");
        require(whole.feed({})==Ready::Result::Rejected,"Repeated world tail accepted");
        Ready fragmented(0x1234);
        for(std::size_t i=0;i<wire.size();++i)
            require(fragmented.feed(std::span(wire).subspan(i,1))==
                (i+1==wire.size()?Ready::Result::Complete:Ready::Result::NeedMore),"Fragmented world tail rejected");
    }
    for(std::size_t index=0;index<logical.size();++index) {
        auto bad=logical;bad[index]^=2;
        Ready parser(0x1234);
        require(parser.feed(encode(bad))==Ready::Result::Rejected,"World tail hard constraint bypass");
    }
    auto bad_checksum=encode(logical);bad_checksum.back()^=1;
    Ready checksum(0x1234);
    require(checksum.feed(bad_checksum)==Ready::Result::Rejected,"World tail checksum bypass");
    // Native new-character entry emitted one heartbeat before the initializer.
    const auto early_tick=encode(std::array<std::uint8_t,2>{0x30,0});
    const auto tail=encode(logical);
    Ready fresh(0x1234);
    require(fresh.feed(early_tick)==Ready::Result::NeedMore,"Fresh pre-tail heartbeat rejected");
    require(fresh.feed(tail)==Ready::Result::Complete,"Fresh initializer after heartbeat rejected");
    Ready repeated_tick(0x1234);
    require(repeated_tick.feed(early_tick)==Ready::Result::NeedMore,"First pre-tail heartbeat rejected");
    require(repeated_tick.feed(early_tick)==Ready::Result::Rejected,"Repeated pre-tail heartbeat accepted");
    Ready malformed_tick(0x1234);
    require(malformed_tick.feed(encode(std::array<std::uint8_t,2>{0x30,1}))==Ready::Result::Rejected,
            "Malformed pre-tail heartbeat accepted");
    // Deterministic malformed-input corpus exercises bounded framing/state only.
    for(std::size_t size=0;size<65;++size) for(unsigned value=0;value<256;value+=7) {
        std::vector<std::uint8_t> malformed(size,static_cast<std::uint8_t>(value));
        Ready parser(0x1234);
        require(parser.feed(malformed)!=Ready::Result::Complete,"Malformed world tail accepted");
    }
}

// Original149c/currentc5d8 native157D0(30) +654F7..65538 + codec flush.
// Proven grouping of existing native records; no new opcode or login bypass.
void grouped_tick_ready_assertions() {
    using Ready=god2::RecoveredWorldReady;
    std::uint64_t partitions_checked=0;
    for(std::uint8_t flag:{0,1}) {
        const std::array<std::uint8_t,11> logical{0x30,0,0x1f,0,0x23,0,0x1c,4,0,flag,0};
        const std::array<std::uint8_t,14> native=flag==0 ?
            std::array<std::uint8_t,14>{0x0e,0,0x2d,0x2d,0x1c,0x1c,0x20,0x20,0x19,0x1d,1,0xfd,0xfd,0xa9} :
            std::array<std::uint8_t,14>{0x0e,0,0x2d,0x2d,0x1c,0x1c,0x20,0x20,0x19,0x1d,1,0xfe,0xfe,0xaa};
        require(encode(logical)==std::vector<std::uint8_t>(native.begin(),native.end()),
                "Pinned current native Tick+initializer codec vector changed");
        Ready native_parser(4);
        require(native_parser.feed(native)==Ready::Result::Complete,"Native14-byte Tick+initializer rejected");
        require(native_parser.config_flag()==flag,"Native14-byte language flag lost");
        // All eight contiguous groupings of four indivisible native records.
        const std::array<std::size_t,4> record_sizes{2,2,2,5};
        for(unsigned group_mask=0;group_mask<8;++group_mask) {
            std::vector<std::uint8_t> wire;std::size_t offset=0,group_size=0;
            for(unsigned record=0;record<4;++record) {
                group_size+=record_sizes[record];
                if(record==3 || (group_mask&(1u<<record))) {
                    const auto frame=encode(std::span(logical).subspan(offset,group_size));
                    wire.insert(wire.end(),frame.begin(),frame.end());offset+=group_size;group_size=0;
                }
            }
            require(offset==11 && wire.size()==14+3*std::popcount(group_mask),"Four-record grouping width changed");
            if(group_mask==7) require(wire.size()==23,"Four separate native records must use23 wire bytes");
            // Every TCP cut partition, including one chunk, every single cut,
            // mixed frame-header/record cuts, and byte-by-byte fragmentation.
            const auto partitions=std::uint32_t{1}<<(wire.size()-1);
            for(std::uint32_t cuts=0;cuts<partitions;++cuts) {
                Ready fragmented(4);std::size_t begin=0;
                for(std::size_t end=1;end<=wire.size();++end) {
                    if(end!=wire.size() && !(cuts&(std::uint32_t{1}<<(end-1)))) continue;
                    require(fragmented.feed(std::span(wire).subspan(begin,end-begin))==
                        (end==wire.size()?Ready::Result::Complete:Ready::Result::NeedMore),
                        "Native Tick+tail TCP partition rejected or completed early");
                    begin=end;
                }
                require(fragmented.config_flag()==flag,"Grouped fragmented language flag lost");
                ++partitions_checked;
            }
            // Every grouped frame's checksum must remain enforced.
            for(std::size_t frame=0;frame<wire.size();) {
                const auto length=wire[frame]+256u*wire[frame+1];
                auto bad=wire;bad[frame+length-1]^=1;
                Ready checksum(4);
                require(checksum.feed(bad)==Ready::Result::Rejected,"Grouped frame checksum bypass");
                frame+=length;
            }
        }
        // Reject duplicate, middle and trailing Tick; it is only stage0 once.
        const std::vector<std::vector<std::uint8_t>> misplaced{
            {0x30,0,0x30,0,0x1f,0,0x23,0,0x1c,4,0,flag,0},
            {0x1f,0,0x30,0,0x23,0,0x1c,4,0,flag,0},
            {0x1f,0,0x23,0,0x30,0,0x1c,4,0,flag,0},
            {0x1f,0,0x23,0,0x1c,4,0,flag,0,0x30,0},
            {0x30,0,0x23,0,0x1f,0,0x1c,4,0,flag,0},
            {0x30,0,0x1f,0,0x1c,4,0,flag,0,0x23,0}};
        for(const auto& bad:misplaced) {
            Ready rejected(4);require(rejected.feed(encode(bad))==Ready::Result::Rejected,
                "Duplicate/mid/tail Tick or initializer order accepted");
        }
        const auto tick=encode(std::array<std::uint8_t,2>{0x30,0});
        Ready duplicate(4);require(duplicate.feed(tick)==Ready::Result::NeedMore,"Standalone Tick rejected");
        require(duplicate.feed(native)==Ready::Result::Rejected,"Separate plus combined duplicate Tick accepted");
        Ready trailing(4);require(trailing.feed(native)==Ready::Result::Complete,"Native grouped tail rejected");
        require(trailing.feed(tick)==Ready::Result::Rejected,"Tick after completed initializer accepted");
        // Mutations of every strict record field, identity and language bytes.
        for(std::size_t index=0;index<logical.size();++index) {
            auto bad=logical;bad[index]^=2;
            Ready rejected(4);require(rejected.feed(encode(bad))==Ready::Result::Rejected,
                "Native grouped field/id/flag constraint bypass");
        }
        auto bad_flag=logical;bad_flag[9]=2;
        Ready flag_parser(4);require(flag_parser.feed(encode(bad_flag))==Ready::Result::Rejected,"Grouped invalid language accepted");
        auto partial_record=encode(std::span(logical).first(1));
        Ready partial(4);require(partial.feed(partial_record)==Ready::Result::Rejected,"Tick split across logical frames accepted");
        auto bad_length=std::vector<std::uint8_t>(native.begin(),native.end());bad_length[0]=15;
        Ready overflow(4);require(overflow.feed(bad_length)==Ready::Result::Rejected,"Unsupported frame length accepted");
        Ready truncated(4);require(truncated.feed(std::span(native).first(native.size()-1))==Ready::Result::NeedMore,
            "Incomplete native frame was completed or rejected prematurely");
    }
    for(const auto identity:{0ull,0x4000ull,std::numeric_limits<std::uint64_t>::max()}) {
        bool rejected=false;try {(void)Ready(identity);}catch(const std::invalid_argument&) {rejected=true;}
        require(rejected,"Invalid ready owner identity accepted");
    }
    std::cout<<"Native grouped Tick TCP partitions checked="<<partitions_checked<<'\n';
}

void assertions() {
    using Entry=god2::RecoveredWorldEntry;
    for(std::uint64_t id:{1ull,217ull,16383ull}) {
        const auto plain=Entry::decoded(id),wire=Entry::wire(id);
        require(plain[0]==40 && plain[1]==0 && plain[2]==42,"World entry envelope changed");
        require((plain[3]+256u*plain[4])%16384==id,"World identity changed");
        require(std::equal(plain.begin()+5,plain.end()-1,Entry::historical_body.begin()+2),"Opaque legacy fields changed");
        std::uint8_t previous=0,checksum=static_cast<std::uint8_t>(40+2*0x3c);
        for(std::size_t i=2;i<wire.size();++i) {
            previous=static_cast<std::uint8_t>(wire[i]+3-previous)^god2::recovered_zero_seed_key[i-2];
            require(previous==plain[i],"World entry codec mismatch");
            if(i+1<wire.size()) checksum=static_cast<std::uint8_t>(checksum+previous+0x3c);
        }
        require(checksum==plain.back(),"World entry checksum mismatch");
    }
    for(std::uint64_t id:{0ull,16384ull,std::numeric_limits<std::uint64_t>::max()}) {
        bool rejected=false;
        try { (void)Entry::wire(id); } catch(const std::invalid_argument&) { rejected=true; }
        require(rejected,"Aliased world identity accepted");
    }
    for(unsigned first=0;first<=6;++first) for(unsigned second=0;second<=6;++second) {
        std::array<std::uint8_t,40> profile{};
        profile[32]=static_cast<std::uint8_t>(first);
        profile[36]=static_cast<std::uint8_t>((second<<5)|0x1f);
        const auto plain=Entry::decoded(1,profile),wire=Entry::wire(1,profile);
        require(Entry::wire(1,profile,17,13)==wire,"Default coordinates changed existing world fixture");
        require(Entry::wire(1,profile,17,13,2,15,2)==wire,"Explicit baseline map changed existing world fixture");
        auto expected=Entry::decoded(1);
        expected[16]=static_cast<std::uint8_t>((expected[16]&0x1f)|(first<<5));
        expected[18]=static_cast<std::uint8_t>((expected[18]&0x1f)|(second<<5));
        expected[23]=profile[36]&0xe7;expected[24]=0;expected[25]=profile[38];expected[26]=profile[39];
        require(std::equal(plain.begin(),plain.end()-1,expected.begin()),"Unowned world body bits changed");
        require(encode(std::span(plain).subspan(2,37))==std::vector<std::uint8_t>(wire.begin(),wire.end()),"Projected variant checksum/codec mismatch");
    }
    for(auto field:{32u,36u}) {
        std::array<std::uint8_t,40> profile{};profile[field]=field==32?7:0xe0;
        bool rejected=false;
        try { (void)Entry::wire(1,profile); } catch(const std::invalid_argument&) { rejected=true; }
        require(rejected,"Invalid world variant accepted");
    }
    for(const auto map:std::array{std::array<std::uint16_t,3>{0,4,0},
                                 std::array<std::uint16_t,3>{17,4,0},
                                 std::array<std::uint16_t,3>{2,1024,0},
                                 std::array<std::uint16_t,3>{2,4,4}}) {
        bool rejected=false;
        try { (void)Entry::wire(1,{},110,110,map[0],map[1],map[2]); }
        catch(const std::invalid_argument&) { rejected=true; }
        require(rejected,"Invalid map field was truncated");
    }
    for(const auto coordinates:std::array{std::array<std::uint16_t,2>{32768,0},
                                         std::array<std::uint16_t,2>{0,65535}}) {
        bool rejected=false;
        try { (void)Entry::wire(1,{},coordinates[0],coordinates[1]); }
        catch(const std::invalid_argument&) { rejected=true; }
        require(rejected,"Oversized restored position was truncated");
    }
}
}
int main(int argc,char** argv) {
    try {
        assertions();
        ready_assertions();
        grouped_tick_ready_assertions();
        const auto state=god2::RecoveredWorldStateCandidate::wire();
        require(encode(god2::RecoveredWorldStateCandidate::historical_logical)==
                std::vector<std::uint8_t>(state.begin(),state.end()),"World state codec mismatch");
        if(argc==2 && std::string(argv[1])=="--dump-state") {
            constexpr char digits[]="0123456789abcdef";
            for(auto byte:state) std::cout<<digits[byte>>4]<<digits[byte&15];
            std::cout<<'\n';return 0;
        }
        if((argc==3 || argc==5 || argc==7 || argc==9 || argc==10) && std::string(argv[1])=="--dump") {
            std::array<std::uint8_t,40> profile{};
            if(argc>=5) {
                const auto first=std::stoul(argv[3]),second=std::stoul(argv[4]);
                require(first<=6 && second<=6,"Expected variants 0..6");
                profile[32]=static_cast<std::uint8_t>(first);profile[36]=static_cast<std::uint8_t>(second<<5);
            }
            const auto x=argc>=7?std::stoul(argv[5]):17,y=argc>=7?std::stoul(argv[6]):13;
            require(x<=0x7fff && y<=0x7fff,"Coordinates must fit 15 bits");
            const auto area=argc>=9?std::stoul(argv[7]):2,scene=argc>=9?std::stoul(argv[8]):15;
            const auto kind=argc==10?std::stoul(argv[9]):2;
            require(kind<=65535,"Kind argument exceeds uint16");
            require(area<=65535 && scene<=65535,"Map arguments exceed uint16");
            const auto wire=argc>=9?god2::RecoveredWorldEntry::wire(std::stoull(argv[2]),profile,
                static_cast<std::uint16_t>(x),static_cast<std::uint16_t>(y),
                static_cast<std::uint16_t>(area),static_cast<std::uint16_t>(scene),static_cast<std::uint16_t>(kind)):
                argc==7?god2::RecoveredWorldEntry::wire(std::stoull(argv[2]),profile,
                static_cast<std::uint16_t>(x),static_cast<std::uint16_t>(y)):
                argc==3?god2::RecoveredWorldEntry::wire(std::stoull(argv[2])):
                god2::RecoveredWorldEntry::wire(std::stoull(argv[2]),profile);
            constexpr char digits[]="0123456789abcdef";
            for(auto byte:wire) std::cout<<digits[byte>>4]<<digits[byte&15];
            std::cout<<'\n';
        } else {
            require(argc==1,"Expected --dump local_id");
            std::cout<<"Recovered world entry assertions passed\n";
        }
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
}
