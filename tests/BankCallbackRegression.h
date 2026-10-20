#pragma once
#include <array>
#include <cstdint>
#include <cstring>
#include <sqlite3.h>
#include <stdexcept>
#include <string_view>

// Source-only regression additions for the PHASE1 bank lifecycle correction.
// Each harness copies its hook before invoking it, so clearing a one-shot hook
// never destroys the currently executing callable. These cases are not run here.
namespace god2_test {
inline void bank_check(bool condition,const char* message){if(!condition)throw std::runtime_error(message);}
template<class Service,class Handle>
auto bank_revoke_on_receipt(sqlite3* db,Service& service,Handle handle,std::uint64_t session=77){
    struct State{Service* service;std::uint64_t session;bool hit=false;} state{&service,session};
    bank_check(sqlite3_trace_v2(db,SQLITE_TRACE_STMT,[](unsigned,void* opaque,void*,void* sql)->int{
        auto& state=*static_cast<State*>(opaque);
        if(!state.hit&&sql&&std::strstr(static_cast<const char*>(sql),"SELECT account_id,character_id,operation")){
            state.hit=true;state.service->disconnect(state.session);
        }
        return 0;
    },&state)==SQLITE_OK,"Bank receipt observer registration failed");
    struct Clear{sqlite3* db;~Clear(){sqlite3_trace_v2(db,0,nullptr,nullptr);}} clear{db};
    auto result=handle();bank_check(state.hit,"Bank postwrite receipt observer was not exercised");return result;
}
template<class Harness,class Seed,class Rows,class Handle>
void bank_callback_regressions(Seed seed,Rows rows,Handle handle){
    for(const auto stage:{"lookup","permit","receipt","eligible","plain","weapon"})
    for(unsigned failure=0;failure<4;++failure){
        Harness h;seed(h);h.open();const auto before=rows(h);unsigned hits=0;
        h.callback=[&](std::string_view at){if(at!=stage)return;++hits;h.callback={};
            if(failure==0)h.service.disconnect(77);
            else if(failure==1){try{h.open();}catch(...){} }
            else if(failure==2){try{handle(h);}catch(...){} }
            else throw 7;
        };
        const auto result=handle(h);h.callback={};
        bank_check(hits==1&&result.rejected&&!result.committed&&rows(h)==before,"Bank callback refusal failed exact rollback");
        if(failure!=3)bank_check(result.batches.empty(),"Poisoned bank operation emitted stale projection");
        const auto replay=handle(h);
        bank_check(replay.rejected&&!replay.committed&&rows(h)==before,"Bank callback failure retained lease");
    }
    for(const auto stage:{"lookup","permit","weapon"}){
        Harness h;seed(h);const auto before=rows(h);unsigned hits=0;bool threw=false;
        h.callback=[&](std::string_view at){if(at!=stage)return;++hits;h.callback={};h.service.disconnect(77);};
        try{h.open();}catch(...){threw=true;}h.callback={};
        bank_check(threw&&hits==1&&rows(h)==before,"Bank open recreated revoked context");
        const auto result=handle(h);bank_check(result.rejected&&!result.committed,"Revoked open retained lease");
    }
    for(unsigned failure=0;failure<3;++failure){
        Harness h;seed(h);h.open();const auto before=rows(h);unsigned hits=0;
        h.callback=[&](std::string_view at){if(at!="renew")return;++hits;h.callback={};
            if(failure==0)h.service.disconnect(77);
            else if(failure==1){try{h.open();}catch(...){} }
            else throw 7;
        };
        const auto result=handle(h);h.callback={};const auto durable=rows(h);
        bank_check(hits==1&&result.committed&&!result.rejected&&durable!=before,"Postcommit callback falsely reported rollback");
        bank_check(failure==2?!result.batches.empty():result.batches.empty(),"Bank renewal response ignored poison state");
        const auto replay=handle(h);bank_check(replay.rejected&&!replay.committed&&rows(h)==durable,"Postcommit callback retained lease");
    }
    Harness h;seed(h);h.open();const auto before=rows(h);++h.peer->session;
    const auto result=handle(h);bank_check(result.rejected&&!result.committed&&result.batches.empty()&&rows(h)==before,"Mismatching returned session granted bank authority");
}
}
