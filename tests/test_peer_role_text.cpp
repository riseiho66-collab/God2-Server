#include "handlers/RecoveredPeerRoleText.h"
#include "text/LegacyChineseCodec.h"
#include <iostream>
#include <stdexcept>

using namespace god2;
namespace {
void check(bool value) {if(!value)throw std::runtime_error("Peer role text contract check failed");}
RecoveredRoleText::Text field(std::string_view value) {
    if(value.size()>15)throw std::invalid_argument("Test text bound");
    RecoveredRoleText::Text result{};std::copy(value.begin(),value.end(),result.begin());return result;
}
StoredRoleText saved(std::string_view bytes,std::uint16_t page) {
    return {field(bytes),LegacyChineseCodec::decode(bytes,page==936),page,7};
}
RecoveredRemoteActor::Record spawn(std::uint16_t page) {
    RecoveredRemoteActor::LogicalRecord value{};
    for(std::size_t i=0;i<value.size();++i)value[i]=static_cast<std::uint8_t>(i*3u+11u);
    value[0]=0x6f;value[1]=7;value[2]=static_cast<std::uint8_t>(value[2]&0xf0);
    value[4]=static_cast<std::uint8_t>((value[4]&~2u)|(page==936?2u:0u));
    for(const auto at:{29u,45u,61u}) {std::fill_n(value.begin()+at,16,0);value[at]='P';value[at+1]=static_cast<std::uint8_t>(at);}
    return RecoveredRemoteActor::parse_logical(value).value();
}
void preserved(const RecoveredRemoteActor::Record& before,const RecoveredRemoteActor::Record& after) {
    const auto a=RecoveredRemoteActor::encode_logical(before),b=RecoveredRemoteActor::encode_logical(after);
    for(std::size_t i=0;i<a.size();++i)if(i<45 || i>=61)check(a[i]==b[i]);
    check(before.identity()==after.identity() && before.x()==after.x() && before.y()==after.y());
}
void reject(const auto& action) {
    bool failed=false;try{action();}catch(const std::invalid_argument&){failed=true;}check(failed);
}
}
int main() {
    for(const std::uint16_t page:std::array<std::uint16_t,2>{950,936}) {
        auto source=spawn(page);check(RecoveredRemoteRoleText::source_codepage(source)==page);
        for(std::size_t n=0;n<=15;++n) {
            const auto text=field(std::string(n,'A'));
            const auto updated=RecoveredRemoteRoleText::with_source_text(source,text);check(updated.has_value());preserved(source,*updated);
            const auto bytes=RecoveredRemoteActor::encode_logical(*updated);check(std::equal(text.begin(),text.end(),bytes.begin()+45));
            for(const std::uint16_t receiver:std::array<std::uint16_t,2>{950,936}) {
                const auto row=saved(std::string(n,'A'),page);const auto snapshot=row;
                const auto result=RecoveredPeerRoleText::per_recipient(source,row,receiver);
                preserved(source,result.spawn);check(result.displayed && result.recipient_text==text && row==snapshot);
            }
        }
        auto bad=field("good");bad[15]=1;check(!RecoveredRemoteRoleText::with_source_text(source,bad));
        bad=field("good");bad[7]=1;check(!RecoveredRemoteRoleText::with_source_text(source,bad));
        const auto absent=RecoveredPeerRoleText::per_recipient(source,std::nullopt,page);
        preserved(source,absent.spawn);check(!absent.displayed && absent.recipient_text==field(""));
        auto invalid=saved("good",page);invalid.utf8="different";
        const auto denied=RecoveredPeerRoleText::per_recipient(source,invalid,page);preserved(source,denied.spawn);
        check(!denied.displayed && !denied.recipient_text);
        const auto blank=RecoveredRemoteActor::encode_logical(denied.spawn);check(std::all_of(blank.begin()+45,blank.begin()+61,[](auto x){return x==0;}));
        reject([&]{RecoveredPeerRoleText::per_recipient(source,std::nullopt,65001);});
    }
    for(const std::uint16_t page:std::array<std::uint16_t,2>{950,936}) {
        check(!NativePeerRoleTextCodec::project(std::string(16,'A'),page,page));
        check(!NativePeerRoleTextCodec::project(std::string("A\0B",3),page,page));
        check(!NativePeerRoleTextCodec::project("\x81",page,page));
        check(!NativePeerRoleTextCodec::project("ABC",0,page));
        check(!NativePeerRoleTextCodec::project("ABC",page,0));
    }
#ifdef _WIN32
    // These expected bytes are independently observed by the original native
    // NLS pipeline oracle, including its intended script conversion.
    check(NativePeerRoleTextCodec::project("\xb4\xfa\xb8\xd5",950,936)==std::string("\xb2\xe2\xca\xd4")); // 測試 -> 测试
    check(NativePeerRoleTextCodec::project("\xb2\xe2\xca\xd4",936,950)==std::string("\xb4\xfa\xb8\xd5"));
    check(NativePeerRoleTextCodec::project("\xd7\xa8",936,950)==std::string("\xb1\x4d")); // 专 -> 專
    const auto traditional=saved("\xb4\xfa\xb8\xd5",950);
    auto projected=RecoveredPeerRoleText::per_recipient(spawn(950),traditional,936);
    check(projected.displayed && projected.recipient_text==field("\xb2\xe2\xca\xd4"));preserved(spawn(950),projected.spawn);
    const auto serialized=RecoveredRemoteActor::encode_logical(projected.spawn);
    check(std::equal(traditional.text.begin(),traditional.text.end(),serialized.begin()+45));
    const auto simplified=saved("\xb2\xe2\xca\xd4",936);
    projected=RecoveredPeerRoleText::per_recipient(spawn(936),simplified,950);
    check(projected.displayed && projected.recipient_text==field("\xb4\xfa\xb8\xd5"));preserved(spawn(936),projected.spawn);
    // A row that cannot be represented in the shared6F source page must remain
    // saved and be hidden for this record, without altering primary/flag/third.
    const auto only936=saved("\xd7\xa8",936);const auto exact=only936;
    projected=RecoveredPeerRoleText::per_recipient(spawn(950),only936,950);
    check(!projected.displayed && !projected.recipient_text && only936==exact);preserved(spawn(950),projected.spawn);
#endif
    std::cout<<"Peer secondary role text projection PASS\n";
}
