#pragma once
#include <cstdint>
#include <functional>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>
namespace god2 {
// GAME-only ephemeral publication custody, not a party rule or SQL receipt.
// Every actual model writer uses one Scope; nested entry poisons its parent
// even when no model write occurs. Monotonic epoch prevents same-value ABA.
class OwnedPartyPublicationGuard {
public:
    class Scope {
    public:
        explicit Scope(OwnedPartyPublicationGuard& owner):owner_(owner),parent_(owner.active_),epoch_(owner.epoch_) {
            if(parent_)parent_->poisoned_=true;
            owner_.active_=this;
        }
        ~Scope(){owner_.active_=parent_;}
        Scope(const Scope&)=delete;Scope& operator=(const Scope&)=delete;
        bool current() const {
            if(owner_.stopped_ || poisoned_ || owner_.epoch_!=epoch_ || owner_.active_!=this)return false;
            for(const auto& witness:witnesses_)if(!witness())return false;
            return !owner_.stopped_ && !poisoned_ && owner_.epoch_==epoch_ && owner_.active_==this;
        }
        template<class Model,class PurePublish> bool publish_if(Model& target,Model next,PurePublish other) {
            if(!current())return false;
            if(owner_.epoch_==std::numeric_limits<std::uint64_t>::max()){owner_.stop();return false;}
            static_assert(noexcept(target=std::move(next)));
            static_assert(noexcept(other()));
            // The paired publisher must be a callback-free memory CAS. No
            // provider, allocation or observer is permitted after this cut.
            if(!other())return false;
            ++owner_.epoch_;epoch_=owner_.epoch_;
            target=std::move(next);return true;
        }
        template<class Model> bool publish(Model& target,Model next) {
            return publish_if(target,std::move(next),[]() noexcept {return true;});
        }
        void require_current() const {if(!current())throw std::runtime_error("Party publication source changed during callback");}
    private:
        friend class OwnedPartyPublicationGuard;
        OwnedPartyPublicationGuard& owner_;Scope* parent_;std::uint64_t epoch_;bool poisoned_=false;
        std::vector<std::function<bool()>> witnesses_;
    };
    void observe(std::function<bool()> pure_current) {
        if(!pure_current || !pure_current())throw std::runtime_error("Party source is unavailable");
        if(active_)active_->witnesses_.push_back(std::move(pure_current));
    }
    bool current() const {return !stopped_ && (!active_ || active_->current());}
    std::uint64_t source_epoch() const noexcept {return source_epoch_;}
    bool source_current(std::uint64_t captured) const noexcept {return !stopped_ && source_epoch_==captured;}
    void invalidate() noexcept {
        if(active_)active_->poisoned_=true;
        if(epoch_==std::numeric_limits<std::uint64_t>::max() || source_epoch_==std::numeric_limits<std::uint64_t>::max())stop();
        else {++epoch_;++source_epoch_;}
    }
    void stop() noexcept {stopped_=true;if(active_)active_->poisoned_=true;}
private:
    Scope* active_=nullptr;
    std::uint64_t epoch_=1;
    std::uint64_t source_epoch_=1; // Ready/registry incarnation; own model publication does not retire it.
    bool stopped_=false;
};
}
