#pragma once
#include "cn/protocol/CnTransport.h"
#include "cn/assets/CnClientGroupConfiguration.h"
#include <asio.hpp>
#include <deque>
#include <functional>
#include <memory>
#include <atomic>

namespace god2cn {
class CnTransportSession:public std::enable_shared_from_this<CnTransportSession> {
public:
    enum class Role {Account,World};
    // The application callback receives one decrypted aggregate, not one opcode.
    // Return acknowledgement only after processing on the serial game executor.
    using Completion=std::function<void(bool)>;
    using OnLogical=std::function<void(Bytes,Completion)>;
    using OnClosed=std::function<void()>;
    using OnEstablished=std::function<void()>;
    CnTransportSession(asio::ip::tcp::socket socket,asio::any_io_executor game_executor,
                       std::array<std::uint8_t,16> seed,Role role,
                       std::shared_ptr<const CnClientGroupConfiguration> client_configuration,OnEstablished established,
                       OnLogical logical,OnClosed closed);
    void start();
    void send(Bytes logical);
    // Complete native aggregates, in order, accepted into the bounded output
    // queue as one operation. No interleaving/splitting/reframing of records.
    // Completion runs on game_executor: queue acceptance, NOT socket delivery
    // or native-client success. Invalid/unqueueable batches close the transport.
    void send_batch(std::vector<Bytes> logical,Completion queued);
    // Queue exact native frames behind a strand-owned write barrier. Publish
    // runs once on game after encoding/capacity succeeds and BEFORE these
    // bytes can be written. False/throw closes without writing this batch.
    // Queued completion follows barrier release; it is not socket delivery.
    void send_batch_with_publication(std::vector<Bytes>,std::function<bool()> publish,Completion queued);
    // After the actual terminal reply batch's queue callback. Prevent new
    // ingress/output, drain already accepted writes, then perform existing
    // transport cleanup. Completion runs on game and reports local TCP write
    // completion, not peer receipt/native acceptance. A20-second operational
    // deadline, forced close/error or capacity failure reports false.
    void drain_and_close(Completion written);
    void close();
    Role role() const noexcept {return role_;}
    bool closing() const noexcept {return close_requested_.load(std::memory_order_acquire) ||
                                         drain_requested_.load(std::memory_order_acquire);}
private:
    enum class State {Created,AwaitChallenge,Established,Draining,Closed};
    void read_header();
    void receive_complete();
    void enqueue(Bytes wire);
    void write_next();
    void close_on_strand();
    struct PendingSend;
    void complete_send(const std::shared_ptr<PendingSend>&,bool);
    void complete_drain(const std::shared_ptr<PendingSend>&,bool);
    asio::ip::tcp::socket socket_;
    asio::strand<asio::any_io_executor> strand_;
    asio::any_io_executor game_executor_;
    asio::steady_timer idle_;
    CnTransport codec_;
    Role role_;
    std::shared_ptr<const CnClientGroupConfiguration> client_configuration_;
    OnLogical logical_;
    OnClosed closed_;
    OnEstablished established_;
    State state_=State::Created;
    std::array<std::uint8_t,2> header_{};
    Bytes input_;
    std::deque<std::shared_ptr<const Bytes>> output_;
    std::shared_ptr<const Bytes> publication_barrier_; // First held frame; strand only.
    std::size_t queued_bytes_=0;
    // Bound logical buffers waiting in the executor, in addition to wire output.
    std::atomic_size_t pending_sends_{0};
    std::atomic_bool close_requested_{false};
    std::atomic_bool drain_requested_{false};
    std::shared_ptr<PendingSend> drain_pending_; // Socket strand only.
    // Local integration lifecycle guard; does not change the native wire.
    std::uint64_t idle_generation_=0;
};
}
