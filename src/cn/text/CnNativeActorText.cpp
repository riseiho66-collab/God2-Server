#include "cn/text/CnNativeActorText.h"
#include <utility>
#ifdef _WIN32
#include <windows.h>
#endif

namespace god2cn {
CnNativeActorText::Projection::Projection(CnRemoteActor::LogicalRecord source,State state,
    std::array<std::string,3> expected):source_(source),state_(std::move(state)),expected_(std::move(expected)) {}
bool CnNativeActorText::Projection::current(const CnRemoteActor::Record& record) const {
    const auto before=CnRemoteActor::parse_logical(source_);
    const auto now=CnRemoteActor::encode_logical(record);
    const bool matches=before && before->identity()==record.identity() && before->native_language_tag()==1 &&
        record.native_language_tag()==1 && std::equal(source_.begin()+29,source_.begin()+77,now.begin()+29);
    return matches && state_.actual_native_text_revision && state_.actual_unicode_capability && state_.actual_conversion_latch &&
        state_.qualified_receiver_environment_current && state_.qualified_receiver_environment_current();
}
std::optional<CnNativeActorText::Projection> CnNativeActorText::prepare(const CnRemoteActor::Record& record,State state) {
    const auto bytes=CnRemoteActor::encode_logical(record);
    if(record.native_language_tag()!=1 || !state.actual_native_text_revision || !state.actual_unicode_capability ||
       !state.actual_conversion_latch || !state.qualified_receiver_environment_current ||
       !state.qualified_receiver_environment_current())return std::nullopt;
#ifdef _WIN32
    std::array<std::string,3> expected;
    for(std::size_t field=0;field<3;++field) {
        const auto at=29+16*field;
        const auto first=bytes.begin()+at,end=std::find(first,first+16,0);
        if(end==first+16)return std::nullopt;
        const std::string input(reinterpret_cast<const char*>(bytes.data()+at),static_cast<std::size_t>(end-first));
        //0053F880 exact successful order/parameters. Keep flags0, default-char
        // pointersNULL and ANSI LCMapStringA; the strict shared display codec
        // or LCMapStringW is not an equivalent replacement for this native path.
        const auto query=MultiByteToWideChar(936,0,input.c_str(),-1,nullptr,0);
        if(query<=0 || query>1024 || query*2>1024)return std::nullopt;
        std::array<char,1024> mapped;
        const auto mapping=LCMapStringA(0x804,0x04000000,input.c_str(),-1,mapped.data(),query*2);
        if(mapping<=0 || mapping>query*2 || mapped[static_cast<std::size_t>(mapping-1)]!=0)return std::nullopt;
        std::array<wchar_t,1024> wide;
        const auto decoded=MultiByteToWideChar(936,0,mapped.data(),-1,wide.data(),query);
        if(decoded<=0 || decoded>query || wide[static_cast<std::size_t>(decoded-1)]!=0)return std::nullopt;
        const auto output_size=WideCharToMultiByte(950,0,wide.data(),-1,nullptr,0,nullptr,nullptr);
        if(output_size<=0 || output_size>16)return std::nullopt;
        std::array<char,16> output;
        const auto written=WideCharToMultiByte(950,0,wide.data(),-1,output.data(),output_size,nullptr,nullptr);
        if(written!=output_size || output[static_cast<std::size_t>(written-1)]!=0)return std::nullopt;
        const auto nul=std::find(output.begin(),output.begin()+written,0);
        if(nul!=output.begin()+written-1)return std::nullopt;
        expected[field].assign(output.data(),static_cast<std::size_t>(written-1));
    }
    // No guessed native latch writes/error UI. All success branches retained
    // their supplied nonzero gate; real owner must still qualify its revision.
    if(!state.qualified_receiver_environment_current())return std::nullopt;
    return Projection(bytes,std::move(state),std::move(expected));
#else
    // No locale/iconv/OpenCC approximation of native Windows NLS behavior.
    return std::nullopt;
#endif
}
}
