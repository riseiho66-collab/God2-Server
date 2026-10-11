#pragma once
#include "packet_codec.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <array>
#include <future>
#include <set>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace god2_probe {
namespace candidate_detail {
using Json = nlohmann::json;
inline void require(bool condition) {
    if (!condition) throw std::invalid_argument("invalid crypto recovery request");
}
inline std::string string_field(const Json& object, const char* name) {
    require(object.contains(name) && object.at(name).is_string());
    auto value = object.at(name).get<std::string>();
    require(value.size() <= 1024);
    return value;
}
inline unsigned integer(const Json& value, unsigned maximum) {
    require(value.is_number_integer());
    if (value.is_number_unsigned()) {
        const auto n = value.get<std::uint64_t>();
        require(n <= maximum);
        return static_cast<unsigned>(n);
    }
    const auto n = value.get<std::int64_t>();
    require(n >= 0 && static_cast<std::uint64_t>(n) <= maximum);
    return static_cast<unsigned>(n);
}
inline std::vector<std::uint8_t> hex(const Json& object, const char* name,
                                     std::size_t maximum) {
    require(object.contains(name) && object.at(name).is_string());
    const auto& text = object.at(name).get_ref<const std::string&>();
    require(text.size() % 2 == 0 && text.size() <= maximum * 2);
    auto digit = [](char c) -> unsigned {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        throw std::invalid_argument("invalid crypto recovery hex");
    };
    std::vector<std::uint8_t> bytes;
    bytes.reserve(text.size() / 2);
    for (std::size_t i = 0; i < text.size(); i += 2)
        bytes.push_back(static_cast<std::uint8_t>(digit(text[i]) * 16 + digit(text[i + 1])));
    return bytes;
}
struct Packet {
    std::vector<std::uint8_t> wire, known;
    bool has_known = false, has_opcodes = false, state_ok = true;
    std::array<bool, 256> opcodes{};
    std::vector<std::pair<unsigned, unsigned>> constants;
    std::string before, after;
};
enum Rejection { Length, Header, Checksum, Known, Opcode, State, Bounds, Count };
struct Candidate {
    unsigned offset = 0, feedback = 0, position = 0, previous = 0;
    unsigned sequence = 0, bytes = 0, before_position = 0, before_feedback = 0;
    bool oracle = false;
    std::array<std::uint8_t, max_frame> plain{};
};
struct Batch {
    std::vector<Candidate> survivors;
    std::array<unsigned, Count> rejected{};
    std::vector<unsigned> survived_by_packet;
};
inline Batch search(unsigned begin, unsigned end,
                    const std::array<std::uint8_t, 256>& key,
                    const std::vector<Packet>& packets) {
    Batch batch;
    batch.survived_by_packet.resize(packets.size());
    batch.survivors.reserve(end - begin);
    for (unsigned seed = begin; seed < end; ++seed) {
        Candidate candidate;
        candidate.offset = candidate.position = seed / 256;
        candidate.feedback = candidate.previous = seed % 256;
        batch.survivors.push_back(candidate);
    }
    unsigned packet_index = 0;
    for (const auto& packet : packets) {
        std::size_t kept = 0;
        for (auto& candidate : batch.survivors) {
            int rejection = -1;
            const auto length = packet.wire.size();
            if (length < 4 || length > max_frame) rejection = Bounds;
            else if (packet.wire[1] & 0x80) rejection = Header;
            else if (packet.wire[0] + 256U * packet.wire[1] != length) rejection = Length;
            else if (!packet.state_ok) rejection = State;
            if (rejection < 0) {
                std::array<std::uint8_t, 256> rotated{};
                for (unsigned i = 0; i < 256; ++i) rotated[i] = key[(candidate.position + i) & 255];
                const auto decoded = decode(packet.wire, rotated, candidate.previous);
                if (decoded.status <= 0) rejection = Checksum;
                else if (packet.has_known && !std::equal(packet.known.begin(), packet.known.end(), decoded.plain.begin()))
                    rejection = Known;
                else if (packet.has_opcodes && !packet.opcodes[decoded.plain[2]]) rejection = Opcode;
                else {
                    for (const auto& [offset, value] : packet.constants) {
                        if (offset >= length) { rejection = Bounds; break; }
                        if (decoded.plain[offset] != value) { rejection = Known; break; }
                    }
                }
                if (rejection < 0) {
                    candidate.before_position = candidate.position;
                    candidate.before_feedback = candidate.previous;
                    candidate.plain = decoded.plain;
                    candidate.oracle = candidate.oracle || packet.has_known;
                    ++candidate.sequence;
                    candidate.bytes += static_cast<unsigned>(length - 2);
                }
            }
            if (rejection >= 0) ++batch.rejected[static_cast<std::size_t>(rejection)];
            else batch.survivors[kept++] = candidate;
        }
        batch.survivors.resize(kept);
        batch.survived_by_packet[packet_index++] = static_cast<unsigned>(kept);
        if (!kept) break;
    }
    return batch;
}
inline Json direction(const std::array<std::uint8_t, 256>& key,
                      const std::vector<Packet>& packets, unsigned workers) {
    std::vector<std::future<Batch>> tasks;
    for (unsigned i = 0; i < workers; ++i)
        tasks.push_back(std::async(std::launch::async, [&, i] {
            return search(65536U * i / workers, 65536U * (i + 1) / workers, key, packets);
        }));
    Batch total;
    total.survived_by_packet.resize(packets.size());
    for (auto& task : tasks) {
        auto batch = task.get();
        for (unsigned i = 0; i < Count; ++i) total.rejected[i] += batch.rejected[i];
        for (unsigned i = 0; i < packets.size(); ++i)
            total.survived_by_packet[i] += batch.survived_by_packet[i];
        total.survivors.insert(total.survivors.end(), batch.survivors.begin(), batch.survivors.end());
    }
    std::set<std::vector<std::uint8_t>> distinct;
    for (const auto& packet : packets) distinct.insert(packet.wire);
    Json stats = {{"tested", 65536}, {"survivors", total.survivors.size()}};
    constexpr const char* names[] = {"rejected_length", "rejected_header", "rejected_checksum",
        "rejected_known_plaintext", "rejected_opcode", "rejected_state", "rejected_bounds"};
    for (unsigned i = 0; i < Count; ++i) stats[names[i]] = total.rejected[i];
    Json result = {{"stats", stats}, {"candidate_count", total.survivors.size()},
        {"truncated", total.survivors.size() > 256}, {"serialization_limit", 256},
        {"packet_count", packets.size()}, {"distinct_packet_count", distinct.size()},
        {"candidates", Json::array()}, {"verified", false}, {"fresh_runtime_established", false}};
    result["rounds"] = Json::array();
    unsigned previous_count = 65536;
    for (unsigned i = 0; i < packets.size(); ++i) {
        result["rounds"].push_back({{"packet_index",i},{"tested",previous_count},
            {"survivors",total.survived_by_packet[i]}});
        previous_count = total.survived_by_packet[i];
    }
    const auto& last = packets.back();
    for (std::size_t i = 0; i < (std::min)(std::size_t{256}, total.survivors.size()); ++i) {
        const auto& c = total.survivors[i];
        result["candidates"].push_back({{"feedback", c.feedback}, {"key_offset", c.offset},
            {"checksum_pass", true}, {"length_pass", true}, {"header_pass", true},
            {"opcode_plausible", true}, {"opcode_constraint_applied",
                std::any_of(packets.begin(), packets.end(), [](const Packet& p) { return p.has_opcodes; })},
            {"known_plaintext_match", c.oracle}, {"cross_packet_score", distinct.size()},
            {"state_consistent", true}, {"packets_survived", c.sequence},
            {"sequence", c.sequence}, {"bytes_consumed", c.bytes},
            {"state_before", last.before}, {"state_after", last.after},
            {"directional_state", {{"key_offset", c.position}, {"feedback", c.previous},
                {"sequence", c.sequence}, {"bytes_consumed", c.bytes},
                {"state_before", {{"key_offset", c.before_position}, {"feedback", c.before_feedback}}},
                {"state_after", {{"key_offset", c.position}, {"feedback", c.previous}}}}},
            {"plaintext_redacted", true}, {"verified", false}});
    }
    Json differential = {{"current_packet_index", packets.size() - 1},
        {"first_differing_offset", nullptr}, {"need_next_real_constraint", true}};
    if (total.survivors.empty()) differential["status"] = "no_survivors";
    else if (last.wire.size() == 176) differential["status"] = "REDACTED_CREDENTIAL_FRAME";
    else {
        differential["status"] = "equivalent_plaintext";
        for (std::size_t offset = 0; offset < last.wire.size(); ++offset) {
            if (std::any_of(total.survivors.begin() + 1, total.survivors.end(), [&](const Candidate& c) {
                return c.plain[offset] != total.survivors.front().plain[offset];
            })) {
                differential["status"] = "plaintext_differs";
                differential["first_differing_offset"] = offset;
                break;
            }
        }
    }
    differential["next_distinguishing_key_index"] = nullptr;
    if (total.survivors.size() > 1) {
        const auto& first = total.survivors.front();
        bool equivalent = true;
        for (const auto& c : total.survivors)
            equivalent = equivalent && c.feedback == first.feedback;
        for (unsigned index = 0; index < 256; ++index) {
            if (std::any_of(total.survivors.begin()+1,total.survivors.end(),[&](const Candidate& c) {
                return key[(c.offset+index)&255] != key[(first.offset+index)&255];
            })) {
                differential["next_distinguishing_key_index"] = index;
                equivalent = false;
                break;
            }
        }
        if (equivalent) {
            differential["status"] = "mathematically_equivalent_states";
            differential["need_next_real_constraint"] = false;
        }
    }
    if (total.survivors.size() == 1) {
        differential["status"] = "unique";
        differential["need_next_real_constraint"] = false;
    }
    result["differential"] = differential;
    return result;
}
} // namespace candidate_detail

class BruteCandidateEngine {
public:
    static nlohmann::json recover(const nlohmann::json& request) {
        using namespace candidate_detail;
        require(request.is_object());
        const auto session = string_field(request, "session_id");
        require(!session.empty());
        const auto model = string_field(request, "model");
        require(model == "packet_reset");
        std::array<std::array<std::uint8_t, 256>, 2> keys{};
        for (unsigned d = 0; d < 2; ++d) {
            const auto bytes = hex(request, d == 0 ? "tx_key_hex" : "rx_key_hex", 256);
            require(bytes.size() == 256);
            std::copy(bytes.begin(), bytes.end(), keys[d].begin());
        }
        require(request.contains("packets") && request.at("packets").is_array());
        require(!request.at("packets").empty() && request.at("packets").size() <= 256);
        std::array<std::vector<Packet>, 2> packets;
        std::array<bool, 2> oracle{};
        for (const auto& value : request.at("packets")) {
            require(value.is_object());
            const auto name = string_field(value, "direction");
            require(name == "C2S" || name == "S2C");
            const unsigned d = name == "C2S" ? 0 : 1;
            Packet p;
            p.wire = hex(value, "wire_hex", max_frame);
            p.before = string_field(value, "state_before");
            p.after = string_field(value, "state_after");
            if (!packets[d].empty()) p.state_ok = packets[d].back().after == p.before;
            if (value.contains("expected_state_before"))
                p.state_ok = (string_field(value, "expected_state_before") == p.before) && p.state_ok;
            if (value.contains("known_plaintext_hex")) {
                p.known = hex(value, "known_plaintext_hex", max_frame);
                require(p.known.size() == p.wire.size() && p.known.size() >= 4);
                p.has_known = oracle[d] = true;
            }
            if (value.contains("allowed_opcodes")) {
                const auto& ops = value.at("allowed_opcodes");
                require(ops.is_array() && ops.size() <= 256);
                p.has_opcodes = true;
                for (const auto& opcode : ops) p.opcodes[integer(opcode, 255)] = true;
            }
            if (value.contains("constants")) {
                const auto& constants = value.at("constants");
                require(constants.is_array() && constants.size() <= max_frame);
                for (const auto& constant : constants) {
                    require(constant.is_object() && constant.contains("offset") && constant.contains("value"));
                    p.constants.emplace_back(integer(constant.at("offset"), max_frame - 1),
                                             integer(constant.at("value"), 255));
                }
            }
            packets[d].push_back(std::move(p));
        }
        Json result = {{"session_id", session}, {"model", model}, {"verified", false},
            {"CRYPTO_RECOVERED", false}, {"fresh_runtime_established", false},
            {"hypothesis_only", true}, {"state_labels_are_caller_assertions", true},
            {"packet_reset_static_supported", true}, {"shared_direction_object_assumed", false},
            {"hypothesis", "Static evidence supports per-packet reset; searched initial offset/feedback are candidate hypotheses, not fresh-runtime verification"},
            {"directions", Json::object()}};
        if (!oracle[0] || !oracle[1]) {
            result["status"] = "INSUFFICIENT_CONSTRAINTS";
            result["reason"] = "At least one exact plaintext oracle is required per direction";
            return result;
        }
        const unsigned workers = (std::clamp)(std::thread::hardware_concurrency(), 4U, 8U);
        result["workers"] = workers;
        bool unique = true, empty = false;
        for (unsigned d = 0; d < 2; ++d) {
            auto report = direction(keys[d], packets[d], workers);
            const auto count = report.at("candidate_count").get<std::size_t>();
            unique = unique && count == 1 && report.at("distinct_packet_count").get<unsigned>() >= 2;
            empty = empty || count == 0;
            result["directions"][d == 0 ? "C2S" : "S2C"] = std::move(report);
        }
        result["status"] = empty ? "NO_CANDIDATES" : unique ? "UNIQUE_CANDIDATE" : "AMBIGUOUS";
        return result;
    }
};
inline nlohmann::json recover_candidates(const nlohmann::json& request) {
    return BruteCandidateEngine::recover(request);
}
} // namespace god2_probe
