#include "core/ApplicationGameFrame.h"
#include <asio.hpp>
#include <array>
#include <cstdint>
#include <exception>
#include <functional>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

namespace {
using god2::ApplicationGameFrame;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class Exception,class F> bool refuses(F&& call){try{call();}catch(const Exception&){return true;}return false;}
struct Failure final:std::runtime_error {
    explicit Failure(unsigned tag):std::runtime_error("Synthetic frame failure"),tag(tag){}
    unsigned tag;
};
template<class F> bool failure_is(unsigned tag,F&& call){try{call();}catch(const Failure& error){return error.tag==tag;}return false;}
struct Lifetime {
    const std::thread::id owner=std::this_thread::get_id();
    bool alive=false,wrong_owner=false,used_after_retirement=false,net_joined=false,game_drained=false,tail=false;
    unsigned constructed=0,destroyed=0,callbacks=0;
    std::array<std::uint8_t,4> observed{};
};
struct ByteProbe {
    Lifetime& lifetime;
    std::array<std::uint8_t,4> bytes{0x10,0x32,0x54,0x76};
    explicit ByteProbe(Lifetime& value):lifetime(value){++lifetime.constructed;lifetime.alive=true;}
    ~ByteProbe(){++lifetime.destroyed;lifetime.alive=false;lifetime.wrong_owner|=std::this_thread::get_id()!=lifetime.owner;}
};
// The guard is declared AFTER the held frame. On an early host failure it
// naturally joins NET and drains GAME before lexical callbacks can disappear.
// No context.stop(), database, native codec or fabricated stop receipt exists.
struct NaturalDrain {
    asio::io_context& network;
    asio::io_context& game;
    Lifetime& lifetime;
    std::thread worker;
    std::exception_ptr network_failure,game_failure;
    bool joined=false,drained=false;
    static void run_to_empty(asio::io_context& context,std::exception_ptr& failure) noexcept{
        for(;;)try{context.restart();context.run();return;}catch(...){if(!failure)failure=std::current_exception();}
    }
    void join_network(){
        if(joined)return;
        if(worker.joinable())worker.join();else run_to_empty(network,network_failure);
        joined=true;lifetime.net_joined=true;
    }
    void finish(){
        join_network();if(drained)return;
        run_to_empty(game,game_failure);drained=true;lifetime.game_drained=true;
    }
    ~NaturalDrain(){finish();}
};

void lexical_callback_survives_natural_network_join(){
    Lifetime lifetime;asio::io_context game,network;
    std::function<void()>* borrowed=nullptr;
    std::thread::id actual_network;
    // Keep the coroutine lambda itself alive through finish/destruction, as
    // Application does; none of these references come from a temporary lambda.
    auto build=[&]() -> ApplicationGameFrame {
        ByteProbe local(lifetime);
        std::function<void()> callback=[&local,&lifetime]{
            lifetime.wrong_owner|=std::this_thread::get_id()!=lifetime.owner;
            lifetime.used_after_retirement|=!lifetime.alive||!lifetime.net_joined;
            local.bytes[2]^=0xff;lifetime.observed=local.bytes;++lifetime.callbacks;
        };
        borrowed=&callback;
        co_await ApplicationGameFrame::Hold{};
        lifetime.tail=lifetime.net_joined&&lifetime.game_drained&&lifetime.callbacks==1;
    };
    auto frame=build();
    NaturalDrain drain{network,game,lifetime};
    frame.require_held();
    require(borrowed&&lifetime.constructed==1&&lifetime.alive&&!lifetime.destroyed&&!lifetime.tail,
        "Startup did not retain the actual lexical callback/probe at hold");
    asio::post(network,[&,callback=borrowed]{
        actual_network=std::this_thread::get_id();
        asio::post(game,[callback]{(*callback)();});
    });
    drain.worker=std::thread([&]{NaturalDrain::run_to_empty(network,drain.network_failure);});
    drain.join_network();
    require(actual_network!=lifetime.owner&&network.stopped()&&lifetime.alive&&lifetime.callbacks==0&&!lifetime.destroyed,
        "NET did not join naturally before GAME or prematurely retired held locals");
    frame.require_held();drain.finish();
    if(drain.network_failure)std::rethrow_exception(drain.network_failure);
    if(drain.game_failure)std::rethrow_exception(drain.game_failure);
    require(game.stopped()&&lifetime.callbacks==1&&lifetime.observed==std::array<std::uint8_t,4>{0x10,0x32,0xab,0x76}&&
        lifetime.alive&&!lifetime.destroyed&&!lifetime.wrong_owner&&!lifetime.used_after_retirement,
        "Queued NET to GAME callback lost the held local bytes/owner before natural drain");
    frame.require_held();frame.finish_after_drain();
    require(lifetime.tail&&!lifetime.alive&&lifetime.destroyed==1&&!lifetime.wrong_owner,
        "Finishing after natural drain did not retire lexical locals once on GAME");
    require(refuses<std::logic_error>([&]{frame.require_held();})&&refuses<std::logic_error>([&]{frame.finish_after_drain();}),
        "Completed gameplay frame permitted repeated hold/finish");
}

void startup_and_tail_failures_retire_once(){
    Lifetime startup;
    auto before_hold=[&]() -> ApplicationGameFrame {
        ByteProbe local(startup);throw Failure(41);co_await ApplicationGameFrame::Hold{};
    };
    {
        auto frame=before_hold();
        require(startup.constructed==1&&startup.destroyed==1&&!startup.alive&&!startup.wrong_owner,
            "Early startup failure did not unwind its owned local");
        require(failure_is(41,[&]{frame.require_held();})&&failure_is(41,[&]{frame.finish_after_drain();})&&
            failure_is(41,[&]{frame.require_held();}),"Stored startup error was lost or replaced by a later phase error");
    }
    require(startup.destroyed==1,"Failed frame destruction repeated startup local cleanup");
    Lifetime tail;
    auto after_hold=[&]() -> ApplicationGameFrame {
        ByteProbe local(tail);co_await ApplicationGameFrame::Hold{};throw Failure(42);
    };
    {
        auto frame=after_hold();frame.require_held();require(tail.alive&&!tail.destroyed,"Tail fixture did not reach hold");
        require(failure_is(42,[&]{frame.finish_after_drain();})&&tail.destroyed==1&&!tail.alive&&!tail.wrong_owner&&
            failure_is(42,[&]{frame.require_held();})&&failure_is(42,[&]{frame.finish_after_drain();}),
            "Tail failure was not retained after owner cleanup");
    }
    require(tail.destroyed==1,"Failed tail frame destruction repeated local cleanup");
}

void one_hold_move_and_thread_boundaries(){
    static_assert(!std::is_copy_constructible_v<ApplicationGameFrame>&&!std::is_copy_assignable_v<ApplicationGameFrame>);
    static_assert(std::is_nothrow_move_constructible_v<ApplicationGameFrame>&&!std::is_move_assignable_v<ApplicationGameFrame>);
    Lifetime moved_lifetime;
    auto build=[&]() -> ApplicationGameFrame {ByteProbe local(moved_lifetime);co_await ApplicationGameFrame::Hold{};};
    {
        auto original=build();auto moved=std::move(original);
        require(refuses<std::logic_error>([&]{original.require_held();})&&refuses<std::logic_error>([&]{original.finish_after_drain();}),
            "Moved-from frame retained lifecycle authority");
        moved.require_held();unsigned foreign_refusals=0;
        std::thread foreign([&]{
            foreign_refusals+=refuses<std::logic_error>([&]{moved.require_held();});
            foreign_refusals+=refuses<std::logic_error>([&]{moved.finish_after_drain();});
        });foreign.join();
        require(foreign_refusals==2&&moved_lifetime.alive&&!moved_lifetime.destroyed,
            "Foreign thread accessed/resumed or retired actual owner locals");
        moved.require_held();moved.finish_after_drain();
    }
    require(moved_lifetime.destroyed==1&&!moved_lifetime.wrong_owner,"Move changed local cleanup ownership/count");
    Lifetime duplicate;
    auto twice=[&]() -> ApplicationGameFrame {
        ByteProbe local(duplicate);co_await ApplicationGameFrame::Hold{};co_await ApplicationGameFrame::Hold{};duplicate.tail=true;
    };
    {auto frame=twice();frame.require_held();require(refuses<std::logic_error>([&]{frame.finish_after_drain();})&&
        duplicate.destroyed==1&&!duplicate.alive&&!duplicate.tail,"Second hold silently suspended another lexical lifetime seam");}
    Lifetime absent;
    auto no_hold=[&]() -> ApplicationGameFrame {ByteProbe local(absent);co_return;};
    {auto frame=no_hold();require(refuses<std::logic_error>([&]{frame.require_held();})&&
        refuses<std::logic_error>([&]{frame.finish_after_drain();})&&absent.destroyed==1,"Completed startup with no hold was accepted");}
    Lifetime aborted;
    auto abort=[&]() -> ApplicationGameFrame {ByteProbe local(aborted);co_await ApplicationGameFrame::Hold{};aborted.tail=true;};
    {auto frame=abort();frame.require_held();}
    require(aborted.destroyed==1&&!aborted.tail&&!aborted.wrong_owner,"Held frame abort ran tail or lost owner cleanup");
}

void reentrant_finish_and_return_destructor_refuse(){
    ApplicationGameFrame* actual=nullptr;unsigned tail_refusals=0,destructor_refusals=0,destructions=0;
    bool reached_return=false,wrong_owner=false;std::exception_ptr unexpected;
    const auto owner=std::this_thread::get_id();
    struct ReturnProbe {
        std::function<void()> at_return;
        ~ReturnProbe(){at_return();}
    };
    auto build=[&]() -> ApplicationGameFrame {
        // co_return invokes return_void before this local destructor and final
        // suspension. Reentry here must be rejected throughout resume(), even
        // after the promise has recorded successful return; never query done()
        // on an actively executing coroutine or destroy that running frame.
        ReturnProbe local{[&]{
            ++destructions;wrong_owner|=std::this_thread::get_id()!=owner;
            try{
                destructor_refusals+=refuses<std::logic_error>([&]{actual->require_held();});
                destructor_refusals+=refuses<std::logic_error>([&]{actual->finish_after_drain();});
            }catch(...){unexpected=std::current_exception();}
        }};
        co_await ApplicationGameFrame::Hold{};
        tail_refusals+=refuses<std::logic_error>([&]{actual->require_held();});
        tail_refusals+=refuses<std::logic_error>([&]{actual->finish_after_drain();});
        reached_return=true;co_return;
    };
    auto frame=build();actual=&frame;frame.require_held();frame.finish_after_drain();
    if(unexpected)std::rethrow_exception(unexpected);
    require(reached_return&&tail_refusals==2&&destructor_refusals==2&&destructions==1&&!wrong_owner&&
        refuses<std::logic_error>([&]{frame.finish_after_drain();}),
        "Caught tail/return-destructor reentry resumed, destroyed or poisoned the actual cohort");
    unsigned abort_refusals=0,abort_destructions=0;bool abort_tail=false;
    auto abort=[&]() -> ApplicationGameFrame {
        ReturnProbe local{[&]{
            ++abort_destructions;wrong_owner|=std::this_thread::get_id()!=owner;
            try{
                abort_refusals+=refuses<std::logic_error>([&]{actual->require_held();});
                abort_refusals+=refuses<std::logic_error>([&]{actual->finish_after_drain();});
            }catch(...){unexpected=std::current_exception();}
        }};
        co_await ApplicationGameFrame::Hold{};abort_tail=true;
    };
    {auto abandoned=abort();actual=&abandoned;abandoned.require_held();}
    if(unexpected)std::rethrow_exception(unexpected);
    require(abort_refusals==2&&abort_destructions==1&&!abort_tail&&!wrong_owner,
        "Held-abort local destructor reentered a partially retired coroutine or ran its tail");
}
} // namespace

void test_application_game_frame(){
    lexical_callback_survives_natural_network_join();startup_and_tail_failures_retire_once();
    one_hold_move_and_thread_boundaries();reentrant_finish_and_return_destructor_refuse();
}
