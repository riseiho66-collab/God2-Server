#pragma once
#include <coroutine>
#include <exception>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
// CUSTOM-0159: retain one actual Application gameplay cohort's lexical locals
// across the host event loop. Transport facades never own this frame. The host
// must keep its coroutine lambda, repositories and other borrowed sources alive
// and resume only after natural NET join AND the remaining GAME loop drain.
// A stop observation alone does not satisfy that caller contract.
class ApplicationGameFrame final {
    enum class Phase {Building,Holding,Finishing,Complete,Failed};
public:
    struct Hold final {};
    struct promise_type {
        const std::thread::id thread=std::this_thread::get_id();
        Phase phase=Phase::Building;
        bool resume_active=false; // Includes return_void and local destruction.
        std::exception_ptr failure;
        ApplicationGameFrame get_return_object() noexcept {
            return ApplicationGameFrame(std::coroutine_handle<promise_type>::from_promise(*this));
        }
        std::suspend_never initial_suspend() const noexcept {return {};}
        std::suspend_always final_suspend() const noexcept {return {};}
        void return_void() noexcept {phase=Phase::Complete;}
        void unhandled_exception() noexcept {failure=std::current_exception();phase=Phase::Failed;}
        struct Awaiter {
            promise_type& promise;
            bool invalid=false;
            bool await_ready() const noexcept {return false;}
            bool await_suspend(std::coroutine_handle<promise_type>) noexcept {
                if(promise.phase!=Phase::Building){invalid=true;return false;}
                promise.phase=Phase::Holding;
                return true; // Pure nonthrowing first hold, after startup readiness.
            }
            void await_resume() const {
                if(invalid)throw std::logic_error("Application gameplay frame may hold exactly once");
            }
        };
        Awaiter await_transform(Hold) noexcept {return {*this};}
        // No other awaitable may silently add another lifetime/suspension seam.
        template<class T> void await_transform(T&&)=delete;
    };
    ApplicationGameFrame(const ApplicationGameFrame&)=delete;
    ApplicationGameFrame& operator=(const ApplicationGameFrame&)=delete;
    ApplicationGameFrame(ApplicationGameFrame&& other) noexcept
        :frame_(std::exchange(other.frame_,{})) {
        if(frame_&&(frame_.promise().thread!=std::this_thread::get_id()||executing()))std::terminate();
    }
    ApplicationGameFrame& operator=(ApplicationGameFrame&&)=delete;
    ~ApplicationGameFrame() {
        if(!frame_)return;
        if(frame_.promise().thread!=std::this_thread::get_id()||executing())std::terminate();
        // Reentrant cleanup sees an empty owner, never a partly destroyed frame.
        const auto retiring=std::exchange(frame_,{});
        retiring.destroy(); // Exceptional abort is never a clean-drain claim.
    }
    void require_held() const {
        owner();
        if(frame_.promise().failure)std::rethrow_exception(frame_.promise().failure);
        if(frame_.promise().phase!=Phase::Holding||frame_.done())
            throw std::logic_error("Application gameplay cohort did not reach its owned hold");
    }
    // GAME-only host orchestration, not client/native transfer authority.
    void finish_after_drain() {
        require_held();
        frame_.promise().phase=Phase::Finishing;
        frame_.promise().resume_active=true;
        frame_.resume();
        frame_.promise().resume_active=false;
        if(frame_.promise().failure)std::rethrow_exception(frame_.promise().failure);
        if(!frame_.done()||frame_.promise().phase!=Phase::Complete)
            throw std::logic_error("Application gameplay frame did not finish after drain");
    }
private:
    explicit ApplicationGameFrame(std::coroutine_handle<promise_type> frame) noexcept:frame_(frame){}
    bool executing() const noexcept {
        return frame_.promise().resume_active;
    }
    void owner() const {
        if(!frame_||frame_.promise().thread!=std::this_thread::get_id()||executing())
            throw std::logic_error("Application gameplay frame requires its actual GAME owner");
    }
    std::coroutine_handle<promise_type> frame_;
};
}
