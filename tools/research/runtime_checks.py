"""Mechanical consistency checks, never automatic certification of runtime claims."""
import struct
import pefile
from runtime_contract import decode_hex, require, GATES


def assess_bundle(bundle, *, resolved_counter_ids=frozenset()):
    manifest, files, events = bundle["manifest"], bundle["files"], bundle["events"]
    base, image_size = manifest["process"]["module_base"], manifest["process"]["image_size"]
    evidence = {kind: [e for e in events if e["type"] == kind] for kind in {e["type"] for e in events}}
    blockers = {gate: [] for gate in GATES}
    accepted_ids = {gate: [] for gate in GATES}

    def check_file(path, role):
        item = files[path]
        require(item["role"] == role, f"{path}: expected attachment role {role}")
        return item["data"]

    def memory(path, va, size):
        data = check_file(path, "memory_image")
        require(len(data) == image_size, "Mapped memory image must cover SizeOfImage exactly")
        offset = va - base
        require(0 <= offset and offset + size <= len(data), "Memory reference outside mapped image")
        return data[offset:offset + size]

    def pe_bytes(path, role, rva, size, executable=False):
        raw = check_file(path, role)
        pe = pefile.PE(data=raw, fast_load=True)
        try:
            require(pe.FILE_HEADER.Machine == 0x14c, "Analysis PE must be x86")
            sections = [s for s in pe.sections if s.VirtualAddress <= rva and rva + size <= s.VirtualAddress + s.SizeOfRawData]
            require(len(sections) == 1, "PE reference has no unique raw-backed section")
            section = sections[0]
            require(not executable or section.Characteristics & 0x20000000, "Code reference is not executable")
            offset = section.PointerToRawData + rva - section.VirtualAddress
            require(offset + size <= len(raw), "Truncated PE bytes")
            return raw[offset:offset + size], pe.OPTIONAL_HEADER.AddressOfEntryPoint
        finally:
            pe.close()

    def evaluate(gate, event_type, action):
        candidates = evidence.get(event_type, [])
        if not candidates:
            blockers[gate].append(f"Missing {event_type} evidence")
        for event in candidates:
            try:
                action(event)
                accepted_ids[gate].append(event["id"])
            except (ValueError, KeyError, UnicodeError, pefile.PEFormatError, struct.error) as error:
                blockers[gate].append(f"{event['id']}: {error}")

    def unpack(event):
        d = event["details"]
        before, after = decode_hex(d["before_hex"]), decode_hex(d["after_hex"])
        require(len(after) >= 8 and len(before) == len(after) and before != after, "Unpack transition needs changed before/after bytes")
        require(event["pc"] == d["to_va"] and d["from_va"] != d["to_va"], "Transition pc/target mismatch")
        require(base <= d["from_va"] < base + image_size, "Transition source outside client image")
        require(d["region_va"] <= d["to_va"] < d["region_va"] + len(after), "Transition target outside changed region")
        require(memory(d["memory_file"], d["region_va"], len(after)) == after, "Transition bytes disagree with captured memory")
        require(any(f["role"] == "unpacked_pe" and f["sha256"] != manifest["artifact_id"] for f in files.values()), "Missing distinct unpacked PE candidate")

    by_id = {event["id"]: event for event in events}

    def oep(event):
        d = event["details"]
        code = decode_hex(d["bytes_hex"])
        require(len(code) >= 8 and event["pc"] == base + d["rva"], "OEP needs bytes and runtime-base-relative pc")
        require(memory(d["memory_file"], event["pc"], len(code)) == code, "OEP bytes disagree with memory")
        disk, entry = pe_bytes(d["unpacked_file"], "unpacked_pe", d["rva"], len(code), True)
        require(disk == code and entry == d["rva"], "Dump entry/code disagrees with observed candidate")
        continuation = [by_id[eid] for eid in d["continued_event_ids"]]
        require(all(e["seq"] > event["seq"] and e["thread_id"] == event["thread_id"]
                    and e["type"] in ("function_enter", "function_exit", "call") for e in continuation),
                "Continuation must follow candidate on same thread")
        transitions = [by_id[eid] for eid in accepted_ids["unpack"]]
        require(any(t["seq"] <= event["seq"] and t["thread_id"] == event["thread_id"]
                    and t["details"]["memory_file"] == d["memory_file"] for t in transitions), "No preceding linked unpack transition")

    resolved_slots = {}
    network_exports = set()

    def iat(event):
        d = event["details"]
        observed = struct.unpack("<I", memory(d["memory_file"], base + d["iat_rva"], 4))[0]
        require(observed == d["target_va"], "IAT memory slot differs from resolved address")
        module = pefile.PE(data=check_file(d["module_file"], "module_pe"), fast_load=True)
        try:
            module.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
            require(module.FILE_HEADER.Machine == 0x14c, "Export module must be x86")
            directory = getattr(module, "DIRECTORY_ENTRY_EXPORT", None)
            require(directory is not None and module.get_string_at_rva(directory.struct.Name).decode("ascii").casefold()
                    == d["module_name"].casefold(), "Export module name disagrees with observation")
            exports = getattr(getattr(module, "DIRECTORY_ENTRY_EXPORT", None), "symbols", [])
            matches = [symbol for symbol in exports if (symbol.ordinal == d["symbol"] if type(d["symbol"]) is int
                       else symbol.name == d["symbol"].encode("ascii"))]
            require(len(matches) == 1 and not matches[0].forwarder, "Export unresolved/ambiguous/forwarded; require explicit final module evidence")
            require(d["module_base"] + matches[0].address == d["target_va"], "Export VA does not match runtime target")
            export_name = matches[0].name.decode("ascii") if matches[0].name else None
        finally:
            module.close()
        repaired = pefile.PE(data=check_file(d["repaired_file"], "repaired_pe"), fast_load=True)
        try:
            repaired.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
            rows = [(desc, imp) for desc in getattr(repaired, "DIRECTORY_ENTRY_IMPORT", []) for imp in desc.imports
                    if imp.address - repaired.OPTIONAL_HEADER.ImageBase == d["iat_rva"]]
            require(len(rows) == 1, "Repaired IAT slot missing or ambiguous")
            desc, imp = rows[0]
            symbol = imp.ordinal if imp.import_by_ordinal else imp.name.decode("ascii")
            require(desc.dll.decode("ascii").casefold() == d["module_name"].casefold() and symbol == d["symbol"], "Repaired descriptor does not match export observation")
        finally:
            repaired.close()
        key = (d["repaired_file"], d["iat_rva"])
        require(key not in resolved_slots or resolved_slots[key] == d["target_va"], "Contradictory IAT resolutions")
        resolved_slots[key] = d["target_va"]
        if d["module_name"].casefold() in ("ws2_32.dll", "wsock32.dll"):
            network_exports.add((d["target_va"], export_name))

    def quality(event):
        d = event["details"]
        code = decode_hex(d["bytes_hex"])
        require(len(code) >= 8 and d["instruction_count"] > 0, "Missing disassembly probe")
        require(len(check_file(d["disassembly_file"], "disassembly")) > 0, "Empty disassembly attachment")
        actual, entry = pe_bytes(d["image_file"], "repaired_pe", d["rva"], len(code), True)
        require(actual == code, "Disassembly bytes differ from repaired image")
        candidates = [by_id[eid] for eid in accepted_ids["oep"]]
        require(any(e["details"]["rva"] == entry for e in candidates), "Repaired entry not supported by OEP evidence")
        require(any(pe_bytes(d["image_file"], "repaired_pe", entry, len(decode_hex(e["details"]["bytes_hex"])), True)[0]
                    == decode_hex(e["details"]["bytes_hex"]) for e in candidates if e["details"]["rva"] == entry),
                "Repaired entry bytes differ from OEP observation")
        pe = pefile.PE(data=files[d["image_file"]]["data"], fast_load=True)
        try:
            spans = []
            for section in pe.sections:
                start, size = section.PointerToRawData, section.SizeOfRawData
                require(start + size <= len(files[d["image_file"]]["data"]), "Truncated analysis section")
                if size:
                    require(start >= pe.OPTIONAL_HEADER.SizeOfHeaders, "Analysis section overlaps headers")
                    require(all(start + size <= lo or start >= hi for lo, hi in spans), "Overlapping raw sections")
                    spans.append((start, start + size))
            pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
            slots = [imp.address - pe.OPTIONAL_HEADER.ImageBase for desc in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []) for imp in desc.imports]
            require(slots and all((d["image_file"], slot) in resolved_slots for slot in slots), "Not every repaired import has runtime/export evidence")
            require(not pe.get_warnings(), "Analysis image retains parser warnings requiring review")
        finally:
            pe.close()

    evaluate("unpack", "unpack_transition", unpack)
    evaluate("oep", "oep_candidate", oep)
    evaluate("iat", "import_resolved", iat)
    evaluate("quality", "analysis_probe", quality)
    network = evidence.get("socket_send", []) + evidence.get("socket_receive", [])
    if not network:
        blockers["network"].append("Missing socket send/receive observations")
    for event in network:
        if (event["details"]["target_va"], event["details"]["api"]) not in network_exports:
            blockers["network"].append(f"{event['id']}: API target/name lacks resolved Winsock import evidence")
        else:
            accepted_ids["network"].append(event["id"])
    require(set(resolved_counter_ids) <= {e["id"] for e in evidence.get("counter_evidence", [])}, "Unknown resolved counter-evidence ID")
    for event in evidence.get("counter_evidence", []):
        if event["id"] not in resolved_counter_ids:
            blockers[event["details"]["gate"]].append(f"Counter evidence {event['id']}: {event['details']['reason']}")
    common = []
    if manifest["schema_version"] < 2:
        common.append("Legacy capture lacks measured working-copy identity and handling metadata")
    elif manifest["provenance"]["handling"]["redacted"]:
        common.append("Redacted capture cannot establish full runtime-image proof")
    if manifest["provenance"]["source_kind"] != "runtime":
        common.append("Synthetic input cannot satisfy real-client gates")
    if not any(f["role"] == "raw_trace" and f["data"] for f in files.values()):
        common.append("Missing nonempty native debugger/instrumentation trace")
    gates = {}
    previous = None
    for gate in GATES:
        reasons = common + blockers[gate]
        if previous is not None and gates[previous]["status"] == "BLOCKED":
            reasons.append(f"Prerequisite {previous} blocked")
        gates[gate] = {"status": "BLOCKED" if reasons else "READY_FOR_REVIEW", "blockers": reasons,
                       "evidence_ids": accepted_ids[gate], "verified": False}
        previous = gate
    return {"classification": "Research / Partial Compatibility", "trust": "UNREVIEWED",
            "artifact_id": manifest["artifact_id"], "gates": gates,
            "note": "Readiness checks consistency only; native trace, tool provenance and execution semantics require independent review."}
