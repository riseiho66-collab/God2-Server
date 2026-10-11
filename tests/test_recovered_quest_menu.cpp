#include "protocol/RecoveredQuestDialogue.h"
#include <charconv>
#include <iostream>
#include <string_view>
int main(int argc,char** argv) {
    using Codec=god2::RecoveredQuestDialogue;
    if(argc==4) {
        std::uint32_t args[3]{};
        for(unsigned i=0;i<3;++i) {
            const std::string_view text(argv[i+1]);
            const auto result=std::from_chars(text.data(),text.data()+text.size(),args[i]);
            if(result.ec!=std::errc{} || result.ptr!=text.data()+text.size())return 2;
        }
        const auto packet=Codec::kunlun_knowledge_menu(args[0],args[1],args[2]);if(!packet)return 2;
        for(const auto byte:*packet)std::cout<<"0123456789abcdef"[byte>>4]<<"0123456789abcdef"[byte&15];
        std::cout<<'\n';return 0;
    }
    if(argc!=1)return 2;
    for(const auto request:{0u,1u,0x1234u,65535u})for(const auto context:{0u,0x9au,255u}) {
        const auto record=Codec::kunlun_knowledge_menu(request,context,2995);
        if(!record || (*record)[0]!=0x7a || (*record)[1]!=28 || (*record)[2]!=0 ||
           (*record)[3]!=4 || (*record)[4]!=context || ((*record)[5]+256u*(*record)[6])!=request ||
           (*record)[7]!=0x9a || (*record)[8]!=5)return 1;
        for(unsigned i=9;i<28;++i)if((*record)[i]!=0)return 1;
    }
    for(const auto count:{0u,1000u,2994u,2996u,32767u,65536u})
        if(Codec::kunlun_knowledge_menu(0,0,count))return 1;
    if(Codec::kunlun_knowledge_menu(65536,0,2995) || Codec::kunlun_knowledge_menu(0,256,2995))return 1;
    std::cout<<"PASS source-bound knowledge menu fields and width rejection\n";return 0;
}
