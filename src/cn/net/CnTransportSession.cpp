#include "cn/net/CnTransportSession.h"
#include "cn/protocol/CnAccountWire.h"
#include <stdexcept>
#include <chrono>
#include <utility>

namespace god2cn {
struct CnTransportSession::PendingSend {
    Completion callback;
    asio::executor_work_guard<asio::any_io_executor> game_work;
    std::atomic_bool posted{false};
    PendingSend(Completion done,const asio::any_io_executor& game)
        :callback(std::move(done)),game_work(asio::make_work_guard(game)) {}
};
CnTransportSession::CnTransportSession(asio::ip::tcp::socket socket,asio::any_io_executor game_executor,
    std::array<std::uint8_t,16> seed,Role role,std::shared_ptr<const CnClientGroupConfiguration> configuration,
    OnEstablished established,OnLogical logical,OnClosed closed):
    socket_(std::move(socket)),strand_(asio::make_strand(socket_.get_executor())),game_executor_(std::move(game_executor)),
    idle_(strand_),codec_(seed),role_(role),client_configuration_(std::move(configuration)),
    logical_(std::move(logical)),closed_(std::move(closed)),established_(std::move(established)) {
    if(!logical_ || !closed_ || !established_)throw std::invalid_argument("CN session requires complete application callbacks");
    if(role_!=Role::Account && role_!=Role::World)throw std::invalid_argument("CN endpoint role lacks native version evidence");
    if(!client_configuration_ || !client_configuration_->network_version() ||
       *client_configuration_->network_version()!=CnAccountWire::native_config_version)
        throw std::invalid_argument("CN selected client config lacks qualified account network version");
}
void CnTransportSession::start() {
    asio::dispatch(strand_,[self=shared_from_this()] {
        if(self->state_!=State::Created)return;
        self->state_=State::AwaitChallenge;
        self->enqueue(self->codec_.seed_frame());self->read_header();
    });
}
void CnTransportSession::read_header() {
    if(state_==State::Closed || state_==State::Draining || closing())return;
    idle_.expires_after(state_==State::AwaitChallenge?std::chrono::seconds(20):std::chrono::seconds(120));
    const auto generation=++idle_generation_;
    idle_.async_wait([self=shared_from_this(),generation](const asio::error_code& ec) {
        if(!ec && generation==self->idle_generation_)self->close_on_strand();
    });
    asio::async_read(socket_,asio::buffer(header_),asio::bind_executor(strand_,
      [self=shared_from_this()](const asio::error_code& ec,std::size_t) {
        if(ec || self->state_==State::Closed){self->close_on_strand();return;}
        if(self->closing() || self->state_==State::Draining)return;
        const std::size_t size=self->header_[0]+256u*self->header_[1];
        if(size<4 || size>CnTransport::max_wire || (self->state_==State::AwaitChallenge && size!=19)) {
            self->close_on_strand();return;
        }
        self->input_.resize(size);self->input_[0]=self->header_[0];self->input_[1]=self->header_[1];
        asio::async_read(self->socket_,asio::buffer(self->input_.data()+2,size-2),asio::bind_executor(self->strand_,
          [self](const asio::error_code& error,std::size_t) {
            if(error || self->state_==State::Closed){self->close_on_strand();return;}
            if(self->closing() || self->state_==State::Draining)return;
            self->receive_complete();
          }));
      }));
}
void CnTransportSession::receive_complete() {
    if(state_==State::Draining || state_==State::Closed || closing())return;
    try {
        if(state_==State::AwaitChallenge) {
            if(!codec_.accepts_challenge(input_)){close_on_strand();return;}
            state_=State::Established;
            // Same actual selected config$296 ->low BYTE40 used by account.
            // 0047FE30 waits for account 01/40; 00448F20 and related
            // world callers wait for 01/240 before producing login records.
            // Queue this before application output so wire order is native.
            enqueue(codec_.encode_server_frame(role_==Role::Account?
                Bytes{0x01,*client_configuration_->network_version(),0x00}:CnAccountWire::world_version_reply()));
            if(state_==State::Closed)return;
            asio::post(game_executor_,[self=shared_from_this()] {
                try {self->established_();}catch(...) {self->close();}
            });
            read_header();return;
        }
        auto logical=codec_.decode_client_frame(input_);
        // One outstanding game batch per session. No socket read resumes until
        // the authoritative consumer finishes; UI/DB/Lua never run on this strand.
        auto once=std::make_shared<bool>(false);
        Completion completion=[weak=weak_from_this(),once](bool accepted) {
            if(auto self=weak.lock())asio::post(self->strand_,[self,once,accepted] {
                if(*once)return;*once=true;
                if(self->state_==State::Closed)return;
                if(!accepted){self->close_on_strand();return;}
                if(self->state_==State::Draining || self->closing())return;
                self->read_header();
            });
        };
        asio::post(game_executor_,[self=shared_from_this(),logical=std::move(logical),completion=std::move(completion)]() mutable {
            try {self->logical_(std::move(logical),completion);}catch(...) {completion(false);}
        });
    } catch(...) {close_on_strand();}
}
void CnTransportSession::send(Bytes logical) {
    std::vector<Bytes> batch;batch.push_back(std::move(logical));
    send_batch(std::move(batch),{});
}
void CnTransportSession::complete_send(const std::shared_ptr<PendingSend>& pending,bool accepted) {
    if(pending->posted.exchange(true,std::memory_order_acq_rel))return;
    try {
        asio::post(game_executor_,[self=shared_from_this(),pending,accepted] {
            pending->game_work.reset();
            auto done=std::move(pending->callback);
            if(done)try {done(accepted && !self->closing());}catch(...) {self->close();}
        });
    }catch(...) {pending->posted.store(false,std::memory_order_release);throw;}
}
void CnTransportSession::send_batch(std::vector<Bytes> logical,Completion queued) {
    auto pending=std::make_shared<PendingSend>(std::move(queued),game_executor_);
    const auto frames=logical.size();
    if(closing()) {complete_send(pending,false);return;}
    if(!frames || frames>256) {close();complete_send(pending,false);return;}
    for(const auto& bytes:logical)
        if(bytes.empty() || bytes.size()>CnTransport::max_logical) {close();complete_send(pending,false);return;}
    auto count=pending_sends_.load(std::memory_order_relaxed);
    do {
        if(count>256-frames){close();complete_send(pending,false);return;}
    } while(!pending_sends_.compare_exchange_weak(count,count+frames,std::memory_order_relaxed));
    try {
        asio::post(strand_,[self=shared_from_this(),logical=std::move(logical),frames,pending] {
            self->pending_sends_.fetch_sub(frames,std::memory_order_relaxed);
            if(self->state_!=State::Established || self->closing()) {
                self->complete_send(pending,false);return;
            }
            try {
                if(self->output_.size()>256-frames)throw std::length_error("CN batch queue frame capacity");
                // Prepare all encryption/allocations before publishing any of
                // this batch. Codec framing remains the original native form.
                auto next=self->output_;
                std::size_t total=0;
                for(const auto& bytes:logical) {
                    auto wire=std::make_shared<const Bytes>(self->codec_.encode_server_frame(bytes));
                    if(wire->size()>1024*1024-self->queued_bytes_-total)
                        throw std::length_error("CN batch queue byte capacity");
                    total+=wire->size();next.push_back(std::move(wire));
                }
                const bool idle=self->output_.empty();
                self->output_.swap(next);self->queued_bytes_+=total;
                if(idle)self->write_next();
                self->complete_send(pending,true);
            } catch(...) {
                self->close_on_strand();self->complete_send(pending,false);
            }
        });
    } catch(...) {
        pending_sends_.fetch_sub(frames,std::memory_order_relaxed);
        close();
        complete_send(pending,false);
        throw;
    }
}
void CnTransportSession::send_batch_with_publication(
    std::vector<Bytes> logical,std::function<bool()> publish,Completion queued) {
    if(!publish || !queued)throw std::invalid_argument("CN publication callbacks required");
    auto pending=std::make_shared<PendingSend>(std::move(queued),game_executor_);
    const auto frames=logical.size();
    if(closing()) {complete_send(pending,false);return;}
    if(!frames || frames>256) {close();complete_send(pending,false);return;}
    for(const auto& bytes:logical)
        if(bytes.empty() || bytes.size()>CnTransport::max_logical) {close();complete_send(pending,false);return;}
    auto count=pending_sends_.load(std::memory_order_relaxed);
    do {
        if(count>256-frames){close();complete_send(pending,false);return;}
    } while(!pending_sends_.compare_exchange_weak(count,count+frames,std::memory_order_relaxed));
    try {
        asio::post(strand_,[self=shared_from_this(),logical=std::move(logical),frames,pending,
                           publish=std::move(publish)]() mutable {
            self->pending_sends_.fetch_sub(frames,std::memory_order_relaxed);
            if(self->state_!=State::Established || self->closing() || self->publication_barrier_) {
                self->close_on_strand();self->complete_send(pending,false);return;
            }
            try {
                if(self->output_.size()>256-frames)throw std::length_error("CN publication frame capacity");
                auto next=self->output_;std::size_t total=0;
                std::shared_ptr<const Bytes> first;
                for(const auto& bytes:logical) {
                    auto wire=std::make_shared<const Bytes>(self->codec_.encode_server_frame(bytes));
                    if(wire->size()>1024*1024-self->queued_bytes_-total)
                        throw std::length_error("CN publication byte capacity");
                    if(!first)first=wire;
                    total+=wire->size();next.push_back(std::move(wire));
                }
                // Existing writes may finish, but write_next stops at this
                // first held frame. Later normal sends cannot overtake it.
                self->publication_barrier_=std::move(first);
                self->output_.swap(next);self->queued_bytes_+=total;
                asio::post(self->game_executor_,[self,pending,publish=std::move(publish)]() mutable {
                    bool ready=false;
                    try {ready=!self->closing() && publish();}catch(...) {}
                    try {
                        asio::post(self->strand_,[self,pending,ready] {
                            try {
                                if(!ready || self->state_!=State::Established || self->closing() ||
                                   !self->publication_barrier_) {
                                    self->close_on_strand();self->complete_send(pending,false);return;
                                }
                                const bool head=!self->output_.empty() && self->output_.front()==self->publication_barrier_;
                                self->publication_barrier_.reset();
                                if(head)self->write_next(); // No prior write is active at the held head.
                                self->complete_send(pending,true);
                            }catch(...) {self->close_on_strand();self->complete_send(pending,false);}
                        });
                    }catch(...) {self->close();self->complete_send(pending,false);}
                });
            }catch(...) {self->close_on_strand();self->complete_send(pending,false);}
        });
    }catch(...) {
        pending_sends_.fetch_sub(frames,std::memory_order_relaxed);
        close();complete_send(pending,false);throw;
    }
}
void CnTransportSession::complete_drain(const std::shared_ptr<PendingSend>& pending,bool written) {
    if(pending->posted.exchange(true,std::memory_order_acq_rel))return;
    try {
        asio::post(game_executor_,[self=shared_from_this(),pending,written] {
            pending->game_work.reset();
            auto done=std::move(pending->callback);
            // Closing is intentional here. Local completed writes stay true
            // even if the peer subsequently disconnects or cleanup has run.
            if(done)try {done(written);}catch(...) {self->close();}
        });
    }catch(...) {pending->posted.store(false,std::memory_order_release);throw;}
}
void CnTransportSession::drain_and_close(Completion written) {
    if(!written)throw std::invalid_argument("CN terminal write completion required");
    auto pending=std::make_shared<PendingSend>(std::move(written),game_executor_);
    if(close_requested_.load(std::memory_order_acquire) ||
       drain_requested_.exchange(true,std::memory_order_acq_rel)) {
        complete_drain(pending,false);return;
    }
    try {
        asio::post(strand_,[self=shared_from_this(),pending] {
            try {
                if(self->state_!=State::Established || self->close_requested_.load(std::memory_order_acquire) ||
                   self->pending_sends_.load(std::memory_order_acquire)!=0 || self->publication_barrier_) {
                    self->complete_drain(pending,false);self->close_on_strand();return;
                }
                self->state_=State::Draining;self->drain_pending_=pending;
                self->idle_.expires_after(std::chrono::seconds(20));
                const auto generation=++self->idle_generation_;
                self->idle_.async_wait([self,generation](const asio::error_code& ec) {
                    if(!ec && generation==self->idle_generation_)self->close_on_strand();
                });
                // An existing async_write already owns a nonempty queue's front.
                // Never start a second write against that same buffer.
                if(self->output_.empty())self->write_next();
            }catch(...) {self->complete_drain(pending,false);self->close_on_strand();}
        });
    }catch(...) {
        close();complete_drain(pending,false);throw;
    }
}
void CnTransportSession::enqueue(Bytes wire) {
    if(closing() || state_==State::Draining || state_==State::Closed){close_on_strand();return;}
    // Operational bounds, not claimed original game rules.
    if(output_.size()>=256 || queued_bytes_+wire.size()>1024*1024){close_on_strand();return;}
    auto buffer=std::make_shared<const Bytes>(std::move(wire));queued_bytes_+=buffer->size();
    output_.push_back(buffer);if(output_.size()==1)write_next();
}
void CnTransportSession::write_next() {
    if(state_==State::Closed)return;
    if(output_.empty()) {
        if(state_==State::Draining) {
            auto pending=std::move(drain_pending_);
            if(pending)complete_drain(pending,true);
            close_on_strand();
        }
        return;
    }
    if(publication_barrier_ && output_.front()==publication_barrier_)return;
    const auto buffer=output_.front();
    asio::async_write(socket_,asio::buffer(*buffer),asio::bind_executor(strand_,
      [self=shared_from_this(),buffer](const asio::error_code& ec,std::size_t) {
        if(ec || self->state_==State::Closed){self->close_on_strand();return;}
        self->queued_bytes_-=buffer->size();self->output_.pop_front();self->write_next();
      }));
}
void CnTransportSession::close(){
    if(close_requested_.exchange(true,std::memory_order_acq_rel))return;
    asio::post(strand_,[self=shared_from_this()]{self->close_on_strand();});
}
void CnTransportSession::close_on_strand() {
    close_requested_.store(true,std::memory_order_release);
    if(state_==State::Closed)return;state_=State::Closed;++idle_generation_;
    auto pending=std::move(drain_pending_);
    if(pending)complete_drain(pending,false);
    asio::error_code ignored;idle_.cancel(ignored);socket_.shutdown(asio::ip::tcp::socket::shutdown_both,ignored);socket_.close(ignored);
    publication_barrier_.reset();output_.clear();queued_bytes_=0;
    asio::post(game_executor_,[self=shared_from_this()] {try {self->closed_();}catch(...) {}});
}
}
