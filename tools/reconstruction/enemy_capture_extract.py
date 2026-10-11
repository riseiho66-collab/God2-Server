"""Offline observation extraction, never a monster stat/repertoire authority.

Input is caller-exported, transport-decoded, PRE-DISPATCH S2C JSONL. This tool
does not attach a process, connect, decrypt traffic, query a server, or import
gameplay fixtures. Capture-origin/build declarations are preserved as claims.
See artifacts/research/enemy-capture-plan-20261006/README.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


IMAGE_SHA256 = "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"
SKILL_SHA256 = "7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51"
ORIGINS = {"OWN_SERVER_CUSTOM", "CUSTOM_TEST_NOT_NATIVE", "OFFICIAL_PASSIVE_USER_DECLARED", "UNKNOWN"}
MAX_INPUT = 32 * 1024 * 1024
MAX_RECORDS = 100000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def le(data: bytes, offset: int, size: int = 2) -> int:
    return int.from_bytes(data[offset:offset + size], "little")


def text(value, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ValueError(f"Missing/bounded {label}")
    return value


def definitions(path: Path | None) -> dict[tuple[int, int], dict]:
    if path is None:
        return {}
    if path.stat().st_size != 112660:
        raise ValueError("Skill definition source size mismatch")
    raw = path.read_bytes()
    if sha(raw) != SKILL_SHA256 or raw[:4] != b"1.03":
        raise ValueError("Skill definition source/build mismatch; baseline not refreshed")
    out = {}
    for bank in range(4):
        count = le(raw, 4 + bank * 0x6E04, 4)
        if count != (121, 129, 87, 111)[bank]:
            raise ValueError("Skill definition bank count mismatch")
        for skill_id in range(1, count + 1):
            offset = 8 + bank * 0x6E04 + (skill_id - 1) * 110
            row = raw[offset:offset + 110]
            if len(row) != 110 or row[:2] != bytes((skill_id, bank)):
                raise ValueError("Skill definition identity mismatch")
            out[(bank, skill_id)] = {"source_sha256": sha(raw),
                                   "offset": offset, "row_sha256": sha(row)}
    return out


def extract(input_path: Path, skill_path: Path | None = None) -> dict:
    if input_path.stat().st_size > MAX_INPUT:
        raise ValueError("Capture exceeds bounded input size")
    raw_input = input_path.read_bytes()
    lines = raw_input.decode("utf-8-sig").splitlines()
    if not lines or len(lines) > MAX_RECORDS + 1 or any(not line.strip() for line in lines):
        raise ValueError("Missing capture header, blank lines, or record-count bound")
    header = json.loads(lines[0])
    if header.get("kind") != "capture" or header.get("schema") != "enemy-passive-jsonl-v1":
        raise ValueError("Explicit capture header required")
    origin = header.get("origin")
    if origin not in ORIGINS:
        raise ValueError("Explicit allowed capture origin required")
    stage = header.get("stage")
    if stage != "decoded_s2c_pre_dispatch_logical":
        if stage != "isolated_native_consumer_logical_input" or origin != "CUSTOM_TEST_NOT_NATIVE":
            raise ValueError("PRE-DISPATCH decoded capture or explicitly CUSTOM native-consumer input required")
    if header.get("native_image_sha256") != IMAGE_SHA256:
        raise ValueError("Build contract mismatch; reverse engineer new build instead")
    capture_id = text(header.get("capture_id"), "capture_id")
    session = text(header.get("session_id"), "session_id (pseudonym, not account/credential)")
    source = text(header.get("source_evidence"), "source evidence")
    catalog = definitions(skill_path)
    actors, lifetimes, observations, unbound = {}, [], [], []
    battle_serial = 0
    battle = None
    sequence = -1
    skipped = {}

    def event(item: dict, data: bytes) -> dict:
        return {"sequence": item["sequence"], "timestamp": item.get("timestamp"),
                "raw_hex": data.hex(), "record_sha256": sha(data),
                "dump_evidence": item.get("dump_evidence"),
                "capture_origin": origin, "capture_id": capture_id,
                "source_stage": stage,
                "source_evidence": source, "official_origin_verified": False}

    def bound(position: int, observation: dict) -> None:
        observation["position"] = position
        actor = actors.get(position)
        if actor is None or battle is None:
            observation["binding"] = None
            unbound.append(observation)
            return
        observation["binding"] = {"lifetime_id": actor["lifetime_id"],
            "position": position, "basis": "ordered stream since latest 1C in explicit battle boundary",
            "complete_lifecycle_coverage_proven": False}
        observations.append(observation)
        actor["observations"].append(observation)

    for line_number, line in enumerate(lines[1:], 2):
        item = json.loads(line)
        seq = item.get("sequence")
        if not isinstance(seq, int) or isinstance(seq, bool) or seq <= sequence:
            raise ValueError(f"Line {line_number}: strictly increasing integer sequence required")
        sequence = seq
        if item.get("kind") == "boundary":
            if item.get("event") not in {"disconnect", "battle_end", "capture_gap", "position_invalidated"}:
                raise ValueError(f"Line {line_number}: unknown lifecycle boundary")
            if item["event"] == "position_invalidated":
                position = item.get("position")
                if not isinstance(position, int) or isinstance(position, bool) or not 0 <= position < 28:
                    raise ValueError("Invalid explicitly invalidated actor position")
                actors.pop(position, None)
            else:
                actors.clear()
                battle = None
            continue
        if item.get("kind") != "record" or item.get("direction") != "S2C":
            raise ValueError(f"Line {line_number}: S2C record or explicit boundary required; no C2S credentials")
        value = item.get("hex")
        if not isinstance(value, str) or len(value) > 8192:
            raise ValueError("Missing/bounded logical hex")
        data = bytes.fromhex(value)
        if not data:
            raise ValueError("Empty logical record")
        op = data[0]
        if op == 0x82:
            if len(data) != 9:
                raise ValueError("Malformed logical battle entry 82")
            battle_serial += 1
            battle = f"{session}:{battle_serial}"
            actors.clear()
        elif op == 0x1C:
            if len(data) != 45 or data[1] >= 28:
                raise ValueError("Malformed logical participant identity 1C")
            variant = le(data, 5)
            actor = {"lifetime_id": f"{capture_id}:{battle}:{seq}:{data[1]}",
                     "battle_id": battle, "position": data[1], "side": data[1] // 14,
                     "slot": data[1] % 14, "identity_observation": event(item, data),
                     "displayed_level": data[2], "identity_word_opaque_species_semantics": le(data, 3),
                     "variant_word": variant,
                     "normal_display_key": {"area": data[9], "scene": le(data, 11),
                                             "ordinal": le(data, 7)} if variant == 0x0400 and data[1] >= 14 else None,
                     "server_monster_template_id": None,
                     "intrinsic_four_stats": None, "five_elements": None,
                     "physical_magical_attack_defense": {
                         "physical_attack": None, "magical_attack": None,
                         "physical_defense": None, "magical_defense": None,
                         "origin": "UNKNOWN_NO_WILD_IDENTITY_BOUND_SOURCE"},
                     "complete_carried_skills": None,
                     "observations": []}
            lifetimes.append(actor)
            if battle is not None:
                actors[data[1]] = actor  # Every 1C replaces, never merges by name/art/key.
        elif op == 0x86 and len(data) == 17 and data[1] in (0, 1):
            if data[2] >= 28:
                raise ValueError("Invalid vital actor position")
            observation = event(item, data)
            observation.update(type="transmitted_vitals", resource="HP" if data[1] == 0 else "MP",
                               maximum=le(data, 5, 4), current=le(data, 9, 4),
                               native_actor_write_supported=data[1] == 0 or data[2] < 14,
                               intrinsic_unbuffed_base_stat_proven=False)
            bound(data[2], observation)
        elif op == 0x83 and len(data) == 15 and data[1] in (3, 0x17):
            if data[2] >= 28:
                raise ValueError("Invalid skill-association actor position")
            pair = (data[12], data[11])
            observation = event(item, data)
            observation.update(type="received_skill_action" if data[1] == 3 else "received_skill_association",
                               action=data[1], skill_bank=pair[0], skill_id=pair[1],
                               same_build_definition=catalog.get(pair),
                               definition_lookup_performed=skill_path is not None,
                               full_repertoire_proven=False, successful_effect_proven=False)
            bound(data[2], observation)
        elif op == 0x83 and len(data) == 15 and data[1] == 0x0D:
            observation = event(item, data)
            bits = le(data, 9)
            observation.update(type="received_result_candidate", source_position=data[2],
                               target_masks=[le(data, 5), le(data, 7)],
                               signed_amount=bits if bits < 0x8000 else bits - 65536,
                               nonzero_accumulator_branch=le(data, 11) != 0,
                               selector=data[13], target_outcome=data[14],
                               damage_formula_proven=False, intrinsic_attribute_inversion_proven=False)
            # No fabricated skill->effect association across ambiguous action/marker streams.
            if data[2] >= 28:
                raise ValueError("Invalid result actor position")
            bound(data[2], observation)
        else:
            skipped[f"{op:02X}"] = skipped.get(f"{op:02X}", 0) + 1

    return {"schema": "enemy-passive-observations-v1", "capture_id": capture_id,
            "input_sha256": sha(raw_input), "capture_origin": origin,
            "source_stage": stage, "transport_capture": stage == "decoded_s2c_pre_dispatch_logical",
            "official_origin_verified": False, "claimed_native_image_sha256": IMAGE_SHA256,
            "source_evidence": source, "source_catalog_sha256": SKILL_SHA256 if skill_path else None,
            "participant_lifetimes": lifetimes, "unbound_observations": unbound,
            "bound_observation_count": len(observations), "unhandled_opcode_counts": skipped,
            "complete_game_or_monster_coverage": False,
            "unrecovered_enemy_fields": {
                "constitution": None, "strength": None, "intelligence": None, "speed": None,
                "physical_attack": None, "magical_attack": None,
                "physical_defense": None, "magical_defense": None,
                "metal": None, "wood": None, "water": None, "fire": None, "earth": None,
                "complete_carried_skills": None,
                "origin": "UNKNOWN_NO_WILD_IDENTITY_BOUND_SOURCE"},
            "limits": ["Header/source/origin/build claims require independent capture provenance",
                       "Missing capture/lifecycle messages may invalidate lifetime joins",
                       "Side is a slot convention, not proof of wild monster classification",
                       "HP values are transmitted current/max, not guaranteed unbuffed template values",
                       "Observed action or cache pair is not complete carried repertoire",
                       "Unknown four stats/elements/attack/defense remain null; no damage inversion",
                       "Unhandled messages are counted, never relabeled as absent enemy attributes"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skill-source", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve() == args.input.resolve():
        parser.error("Output must be new; input/history never overwritten")
    result = extract(args.input, args.skill_source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
