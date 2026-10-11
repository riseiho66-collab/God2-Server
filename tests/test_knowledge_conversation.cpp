#include "handlers/RecoveredKnowledgeConversation.h"
#include <iostream>
#include <stdexcept>

int main() {
    unsigned checks=0;
    const auto check=[&](bool value){++checks;if(!value)throw std::runtime_error("Knowledge lifecycle rejected");};
    god2::RecoveredKnowledgeConversation service;
    check(!service.open(0,1,1,0,0,2995));check(!service.open(1,0,1,0,0,2995));
    check(!service.open(1,1,0,0,0,2995));check(!service.open(1,1,1,65536,0,2995));
    check(!service.open(1,1,1,0,256,2995));check(!service.open(1,1,1,0,0,1000));
    for(unsigned choice=0;choice<7;++choice)for(unsigned tail=0;tail<256;++tail) {
        const auto id=1+choice*256+tail;
        check(service.open(id,42,43,0x1234,0x9a,2995).has_value());
        check(!service.open(id,42,43,0x1235,0x9a,2995));
        god2::RecoveredQuestAction::Request action{0x1234,static_cast<std::uint16_t>(choice),0x9a,static_cast<std::uint8_t>(tail)};
        check(!service.consume(id,41,43,action));check(!service.consume(id,42,44,action));
        auto bad=action;bad.request_word=0x1235;check(!service.consume(id,42,43,bad));
        bad=action;bad.context_byte=0x9b;check(!service.consume(id,42,43,bad));
        for(const auto invalid:{7,8,32767,65535}) {
            bad=action;bad.reply_word=static_cast<std::uint16_t>(invalid);
            check(!service.consume(id,42,43,bad));
        }
        const auto accepted=service.consume(id,42,43,action);
        check(accepted && *accepted==choice);check(!service.consume(id,42,43,action));
        service.remove(id);check(!service.contains(id));check(!service.consume(id,42,43,action));
    }
    check(!service.consume(99999,1,2,{0,0,0,0}));
    check(service.open(99999,1,2,0,0,2995).has_value());
    service.remove(99999);check(service.open(99999,3,4,65535,255,2995).has_value());
    check(!service.close(99999,3,5));check(!service.close(99999,2,4));
    check(service.close(99999,3,4));check(!service.close(99999,3,4));
    check(!service.consume(99999,3,4,{65535,0,255,255}));
    check(!service.open(99999,3,4,65535,255,2995));
    std::cout<<"Knowledge conversation checks passed: "<<checks<<'\n';
}
