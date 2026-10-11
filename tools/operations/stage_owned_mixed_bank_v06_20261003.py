"""CUSTOM-0070 immutable qualify, schema45->46 clone stage and explicit apply.

Do not run a mode until root authorizes it. Stage modifies only a new owned
clone. Apply makes a fresh consistent backup, refuses active2592 clients, and
stops only the managed task. Never restore saves or run old45 after migration46.
Signature/asset protection remains deferred; this is only whole mixed-bank custody.
"""
import argparse
from contextlib import closing
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess

from tools.operations import native_armor_transfer_release_20261002 as prior
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import verify_frozen_chat_20260927 as frozen

ROOT=prior.ROOT
managed=prior.managed
sha=prior.sha
require=prior.require
read=prior.read
write=prior.write
PIN="925f15144c779e62183ecc69195c555576eaa8a318522e23ec97bb87d018daae"
OLD_PIN="4a309a8cbc2994b59f235fda008d299b7ba443e2c725edc517a545c3df49bf72"
CANDIDATE=ROOT/"build-owned-mixed-bank-20261003/Release/god2-server.exe"
CONTRACT=ROOT/"artifacts/research/owned-mixed-bank-0070/candidate-20261003/contract.json"
RUN=ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-06/run-result.json"
HARNESS=ROOT/"tools/strike_lab/private_owned_mixed_bank_v06_20261003.py"
HARNESS_PIN="7f28f8d5d05a2fa5c3c91c2fdf98e2c416a1fa81c3300ab3f17509424ed67204"
SHARD_HARNESS_PIN="98ed6327856316b750cd1a23103ef248b8bb93f8677d1346319eaaf797fab7c2"
FORMATTER_HARNESS_PIN="cb2deee7b965cd4867236d540897f6174ee14afc8ec7d65e9fb8ccf21c8f9ff3"
FORMATTER_PROOF=ROOT/"artifacts/research/owned-mixed-bank-0070/preparation-v03-20261003/qualification.json"
FORMATTER_PROOF_PIN="1244cf8584ddd674aa0d8c9cd060b10f314fb81f510ff1591d4ec07663811cb3"
COMPACT_PROOF=ROOT/"artifacts/research/owned-mixed-bank-0070/preparation-v04-20261003/qualification.json"
COMPACT_PROOF_PIN="5cecf6cd00b56a1a6bf1c2a81155f1ea03c80b29dd6630a9c11b7aec27456116"
SHARD_PROOF=ROOT/"artifacts/research/owned-mixed-bank-0070/preparation-v05-20261003/qualification.json"
SHARD_PROOF_PIN="2e3c79872f5e5d7ba5fd7a44a991d94baaa41facf7c7a07fdd6e1d0028361d2a"
SOURCE_HIT_PROOF=ROOT/"artifacts/research/owned-mixed-bank-0070/preparation-v06-20261003/qualification.json"
SOURCE_HIT_PROOF_PIN="b49943dce46f6ffdb92e50b22c95b483c8de8c0a116f597fe6fd3c95e73f9d6a"
LOG=ROOT/"artifacts/research/owned-mixed-bank-0070/root-ctest-01.log"
BUILD_LOG=ROOT/"artifacts/research/owned-mixed-bank-0070/root-build-02.log"
STAGE=ROOT/"artifacts/releases/owned-mixed-bank-20261003/clone-stage"
WEAPON_CACHE=ROOT/"artifacts/research/native-weapons-20260926/records.json"
WEAPON_CACHE_PIN="c42839db91f3bd8ff377fa7995cb0f421c3fabb961eb79f68ae3e9fd97ff18b3"
MED_CACHE=ROOT/"artifacts/research/owned-instance-trade-0069/native-med02-cache.json"
MED_CACHE_PIN="a0aa6832340d5b48b0943572e4fd18514af21775101f4162fe6fc72d085bfd1e"
NEW_TABLES={"character_bank_mixed_receipts"}
NEW_OBJECTS=NEW_TABLES|{"sqlite_autoindex_character_bank_mixed_receipts_1"}
REQUIRED={"storage_owned_mixed_bank_0070","storage_owned_mixed_bank_service_0070","storage_owned_mixed_bank_adapter_0070",
    "storage_owned_instance_trade_0069","storage_owned_instance_trade_service_0069",
    "storage_owned_instance_trade_adapter_0069","storage_owned_foreign_bank_0068",
    "storage_owned_foreign_bank_service_0068","storage_owned_foreign_bank_adapter_0068",
    "storage_owned_armor_bank_0067","storage_owned_armor_bank_adapter_0067","storage_owned_armor_bank_service_0067",
    "bank_items_repository","bank_service","recovered_trade","trade_repository","trade_service",
    "armor_slots","owned_armor_transfer","owned_bag_projection","owned_bank_trade_projection",
    "sqlite_armor_production_adapter","database","config","recovered_account_login","recovered_character_repository"}
TEST_SOURCES={"tests/storage_owned_mixed_bank_0070.cpp","tests/storage_owned_mixed_bank_service_0070.cpp","tests/storage_owned_mixed_bank_adapter_0070.cpp",
    "tests/storage_owned_instance_trade_0069.cpp","tests/storage_owned_instance_trade_service_0069.cpp",
    "tests/storage_owned_instance_trade_adapter_0069.cpp","tests/storage_owned_foreign_bank_adapter_0068.cpp"}
REGRESSION_TEST_SOURCES={'tests/test_recovered_trade.cpp', 'tests/test_bank_items_repository.cpp', 'tests/test_owned_bank_trade_projection.cpp', 'tests/test_owned_bag_projection.cpp', 'tests/storage_owned_armor_bank_0067.cpp', 'tests/storage_owned_armor_bank_adapter_0067.cpp', 'tests/storage_owned_foreign_bank_service_0068.cpp', 'tests/test_owned_armor_transfer.cpp', 'tests/test_bank_service.cpp', 'tests/test_database.cpp', 'tests/test_trade_repository.cpp', 'tests/test_config.cpp', 'tests/storage_owned_armor_bank_service_0067.cpp', 'tests/test_sqlite_armor_production_adapter.cpp', 'tests/test_recovered_character_repository.cpp', 'tests/storage_owned_foreign_bank_0068.cpp', 'tests/test_armor_slots.cpp', 'tests/test_trade_service.cpp', 'tests/test_recovered_account_login.cpp'}
NATIVE_EVIDENCE_PATHS={"artifacts/research/current-bank-mixed-instances-20261003/run02/native.json"}
UI_COUNTS={"pair65":36,"empty65":12,"deposit63":12,"withdraw64":12}
FAMILIES={"MED","EQU","TEQ","WPN","TWP","GEM"}
FAILED05_PINS={'C:\\Users\\risei\\Desktop\\God2\\God2-Server\\tools\\strike_lab\\private_owned_mixed_bank_v05_20261003.py': '98ed6327856316b750cd1a23103ef248b8bb93f8677d1346319eaaf797fab7c2', 'C:\\Users\\risei\\Desktop\\God2\\God2-Server\\artifacts\\playtests\\private-native-blackbox-owned-mixed-bank-20261003-05\\run-result.json': 'd28f7ba3335005bced72dea99684b48126516b00c71c2b7a7c6340578e4c0e54', 'C:\\Users\\risei\\Desktop\\God2\\God2-Server\\artifacts\\playtests\\private-native-blackbox-owned-mixed-bank-20261003-05\\ui-result.json': '498864d0091cc2e24119b6e026b24f49fc171823f002f5c38ba417d252da15a0'}

def qualify():
    require(isinstance(PIN,str) and re.fullmatch(r"[0-9a-f]{64}",PIN) is not None,"Root frozen candidate PIN not yet set")
    require(sha(CANDIDATE)==PIN,"Candidate differs from reviewed immutable build")
    require(isinstance(HARNESS_PIN,str) and re.fullmatch(r"[0-9a-f]{64}",HARNESS_PIN) is not None and sha(HARNESS)==HARNESS_PIN,"Reviewed NEW v06 harness changed or not yet frozen")
    for path,digest in FAILED05_PINS.items():require(sha(Path(path))==digest,"Failed v05 evidence changed: "+path)
    contract=read(CONTRACT)
    require(contract["candidate_sha256"]==PIN and contract["design"]=="CUSTOM-0070" and
        contract["predecessor_sha256"]==OLD_PIN and prior.checked_path(contract["candidate_path"])==CANDIDATE and
        (contract["schema_before"],contract["schema_after"])==(45,46),"Runtime contract differs")
    sources=contract["source_sha256"]
    require(isinstance(sources,dict) and len(sources)==36,"Exact runtime36 contract required")
    for path,digest in sources.items():require(sha(prior.checked_path(path))==digest,"Runtime changed: "+path)
    for field,paths in (("test_sha256",TEST_SOURCES),("regression_test_sha256",REGRESSION_TEST_SOURCES)):
        require(set(contract[field])==paths,"Exact accepted tests required: "+field)
        for path,digest in contract[field].items():require(sha(prior.checked_path(path))==digest,"Accepted test changed: "+path)
    require(contract.get("ctest_passed")==26 and prior.checked_path(contract["ctest_log"])==LOG and
        prior.checked_path(contract["build_log"])==BUILD_LOG and contract["ctest_sha256"]==sha(LOG) and
        contract["build_sha256"]==sha(BUILD_LOG),"Missing exact terminal26/build proof")
    prior.ctest_gate(LOG,26,REQUIRED)
    require(set(contract["native_evidence"])==NATIVE_EVIDENCE_PATHS and contract.get("native_offline_cases")==2232,"Native offline qualification differs")
    for path,digest in contract["native_evidence"].items():require(sha(prior.checked_path(path))==digest,"Accepted native evidence changed: "+path)
    require(sha(FORMATTER_PROOF)==FORMATTER_PROOF_PIN,"Exact legacy receipt formatter evidence changed")
    formatter=read(FORMATTER_PROOF)
    require(formatter["status"]=="EXACT_FAILED_AND_ACCEPTED_RECEIPT_FORMATTERS_PASS_NOT_UI_RUN" and formatter["no_ui_started"] is True and
        formatter["candidate_sha256"]==PIN and formatter["harness_sha256"]==FORMATTER_HARNESS_PIN and formatter["runtime_sources"]==sources and
        formatter["armor_before_and_independent_after_exact"] is True and formatter["armor_full_saved_rows_exact"] is True and
        formatter["frozen_before"]==formatter["frozen_after"],"Legacy0067/0068 source formatter qualification absent")
    require(len(formatter["foreign_accepted_checks"])==24 and all(row["after_exact"] is True for row in formatter["foreign_accepted_checks"]) and
        formatter["plain_withdraw_source_bool_verified_against_writer"] is True,"Accepted foreign/MED formatter evidence incomplete")
    for path,digest in formatter["frozen_after"].items():require(sha(Path(path))==digest,"Legacy formatter source/evidence changed: "+path)
    require(sha(COMPACT_PROOF)==COMPACT_PROOF_PIN,"Lossless compact checkpoint proof changed")
    compact=read(COMPACT_PROOF)
    require(compact["status"]=="LOSSLESS_COMPACT_ROUNDTRIP_PASS_NOT_UI_RUN" and compact["no_ui_started"] is True and
        compact["candidate_sha256"]==PIN and compact["harness_sha256"]=="86566863540099d4286da9f0ee0111ccc505a5f0287aca23fc73e54109edc1cf" and compact["runtime_sources"]==sources and
        compact["exact_structural_roundtrip"] is True and compact["all_events_and_fields_preserved"] is True and
        compact["checkpoint_seconds"]==30 and compact["failure_final_force"] is True and
        (compact["server_bound_seconds"],compact["runner_bound_seconds"])==(1500,1480) and
        compact["failed_run_terminal_exit"]==1 and compact["owned_terminal"] and all(row.get("pid_exists") is False for row in compact["owned_terminal"].values()),"Exact lossless v04 preparation/previous cleanup proof absent")
    for field in ("original","original_copy","compact"):
        require(sha(Path(compact[field+"_path"]))==compact[field+"_sha256"],"Lossless compact original/proof artifact changed: "+field)
    require(compact["original_sha256"]==compact["original_copy_sha256"] and compact["frozen_before"]==compact["frozen_after"],"Failed original JSON/source evidence changed")
    for path,digest in compact["frozen_after"].items():require(sha(Path(path))==digest,"Compact proof source/evidence changed: "+path)
    require(sha(SHARD_PROOF)==SHARD_PROOF_PIN,"Exact lossless event-file qualification changed")
    shards=read(SHARD_PROOF)
    require(shards["status"]=="LOSSLESS_EVENT_FILES_ROUNDTRIP_PASS_NOT_UI_RUN" and shards["no_ui_started"] is True and
        shards["candidate_sha256"]==PIN and shards["harness_sha256"]==SHARD_HARNESS_PIN and shards["runtime_sources"]==sources and
        shards["event_evidence_format"]=="LOSSLESS_SHA256_EVENT_FILES_V1" and shards["event_count"]==211 and
        all(shards.get(field) is True for field in ("exact_event_order","exact_structural_roundtrip_each_event","original_non_event_fields_equal","all_events_and_fields_preserved","event_index_metadata_equal","append_immediately_atomic_file_then_index","event_payload_not_retained_in_index","failure_final_force")) and
        (shards["checkpoint_seconds"],shards["server_bound_seconds"],shards["runner_bound_seconds"])==(30,1500,1480),"Complete ordered/lossless event-file proof absent")
    require(shards["frozen_before"]==shards["frozen_after"] and len(shards["events"])==211,"Lossless event proof source/order count differs")
    for index,event in enumerate(shards["events"]):
        require(event["number"]==index and event["path"]==f"ui-events/event-{index:06d}.json" and event["exact_structural_roundtrip"] is True and event["index_metadata_equal"] is True,"Lossless event proof ordering/payload differs")
    for field in ("original","index"):require(sha(Path(shards[field+"_path"]))==shards[field+"_sha256"],"Lossless original/index proof artifact changed")
    for path,digest in shards["frozen_after"].items():require(sha(Path(path))==digest,"Lossless shard proof source/evidence changed: "+path)
    require(sha(SOURCE_HIT_PROOF)==SOURCE_HIT_PROOF_PIN,"Exact source-hit preflight evidence changed")
    source_hit=read(SOURCE_HIT_PROOF)
    require(source_hit["status"]=="SOURCE_HIT_STATIC_AND_EXISTING_EVIDENCE_PASS_NOT_UI_RUN" and source_hit["no_ui_started"] is True and
        source_hit["candidate_sha256"]==PIN and source_hit["harness_sha256"]==HARNESS_PIN and source_hit["runtime_sources"]==sources and
        all(source_hit.get(key) is True for key in ("run05_source_hit_not_captured","run05_exact_obscurer_not_claimed","predicate_exact_hit_pass","predicate_obscurer_rejected","predicate_wrong_registered_id_rejected","single_repoint_before_press_only_sql_and_request_unchanged_guard","complete_source_layout_and_raw_registered_cache_retained","mandatory_source_press_selected_not_relaxed","source_selected_full24_and_cached_key_match_qualified_sql","source_failure_releases_source_not_destination","single_repoint_normal_source_release_and_clear_no_sql_or_request_change")) and
        source_hit["frozen_before"]==source_hit["frozen_after"],"Exact source-only hover/hit qualification absent")
    require(sha(Path(source_hit["existing_accepted_native_geometry_path"]))==source_hit["existing_accepted_native_geometry_sha256"],"Accepted source-hit geometry evidence changed")
    for path,digest in source_hit["frozen_after"].items():require(sha(Path(path))==digest,"Source-hit preflight provenance changed: "+path)

    evidence_root()  # Reject lexical directory aliases before reading RUN.
    live=ui_gate(read(RUN),sources)
    require(sha(managed.CLIENT)==contract["client_sha256"],"Production client changed")
    baseline=read(frozen.BASELINE)
    require(baseline["current_client_accepted"] is True and frozen.hashes()==baseline["source_sha256"],"Frozen accepted chat baseline changed")
    return {"candidate_sha256":PIN,"client_sha256":contract["client_sha256"],"source_sha256":sources,
        "contract_sha256":sha(CONTRACT),"native_run_sha256":sha(RUN),"harness_sha256":sha(HARNESS),
        "ctest_sha256":sha(LOG),"build_sha256":sha(BUILD_LOG),"helper_sha256":sha(Path(__file__)),
        "ctest_passed":26,"legacy_formatter_proof_sha256":sha(FORMATTER_PROOF),"lossless_compact_proof_sha256":sha(COMPACT_PROOF),"lossless_event_file_proof_sha256":sha(SHARD_PROOF),"source_hit_preflight_proof_sha256":sha(SOURCE_HIT_PROOF),**live}


def receipt_state(owner,identity):
    scalar=lambda r:[r[2],r[3],r[4],r[5]]
    bag=[None]*50
    for row in owner["diagnostic_inventory_slots"]:bag[row[1]]=scalar(row)
    vault=[None]*300
    for row in owner["character_bank_item_slots"]:vault[row[1]]=scalar(row)
    ordered=lambda name:sorted(owner[name],key=lambda row:row[1])
    armorbag=[[r[1],int.from_bytes(bytes.fromhex(r[2])[:2],"little"),1,r[3],list(bytes.fromhex(r[2])),r[4],r[5],True] for r in ordered("character_armor_slot_metadata")]
    armorvault=[[r[1],list(bytes.fromhex(r[2])),*r[3:9]] for r in ordered("character_bank_armor_metadata")]
    weapons=[[r[1],list(bytes.fromhex(r[2])),*r[3:9]] for r in ordered("character_weapon_slot_metadata")]
    gems=[[r[1],list(bytes.fromhex(r[2])),*r[3:7],"",r[7]] for r in ordered("character_teleport_gem_metadata")]
    foreign=[[r[1],r[2],list(bytes.fromhex(r[3])),*r[4:12]] for r in ordered("character_bank_foreign_metadata")]
    require(all(row is not None for row in vault),"Full300 owned vault missing")
    return [identity,identity,bag,vault,armorbag,armorvault,weapons,gems,foreign]


def owned_metadata(owner,storage,slot):
    if storage=="bag":
        rows=[row[2] for table in ("character_armor_slot_metadata","character_weapon_slot_metadata","character_teleport_gem_metadata") for row in owner[table] if row[1]==slot]
    else:
        rows=[row[2] for row in owner["character_bank_armor_metadata"] if row[1]==slot]+[row[3] for row in owner["character_bank_foreign_metadata"] if row[1]==slot]
    require(len(rows)<=1,"Native owned overlay conflict")
    return bytes.fromhex(rows[0]) if rows else None


def native_full(owner,native,identity,language):
    require(native["identity"]==identity and native["language"]==language and type(native["pid"]) is int and native["pid"]>0,"Actual native owner/language/PID mismatch")
    for storage,table,length in (("bag","diagnostic_inventory_slots",50),("vault","character_bank_item_slots",300)):
        cells=native[storage];saved={row[1]:row for row in owner[table]}
        require([cell["slot"] for cell in cells]==list(range(length)),"Actual native physical cell coverage missing: "+storage)
        if storage=="vault":require(set(saved)==set(range(300)),"Saved vault capacity missing")
        for cell in cells:
            slot=cell["slot"];raw=bytes.fromhex(cell["raw"]);require(len(raw)==24,"Actual native cell not24 bytes")
            count=int.from_bytes(raw[:4],"little") if storage=="bag" else raw[0]
            row=saved.get(slot)
            if row is None:
                require(storage=="bag" and count==0,"Absent native capacity occupied")
                continue
            require(row[0]==identity and count==row[3] and int.from_bytes(raw[4:6],"little")==row[2],"Native count/key differs from explicit owned scalar")
            if storage=="vault":require(raw[1]==slot%50 and raw[2:4]==bytes(2),"Native vault source-slot24 prefix differs")
            if row[3]:
                body=owned_metadata(owner,storage,slot)
                if body is None:body=row[2].to_bytes(2,"little")+bytes(18)
                require(raw[4:]==body,"Native full20 record lost source/provenance bytes")
            elif storage=="vault":require(raw[4:]==bytes(20),"Empty full48 vault projection not empty")
    require(native["purse"]==owner["character_trade_wallets"][0][1] and native["bank"]==owner["character_bank_balances"][0][1],"Actual native currency changed")


def independent_swap(before,source,destination):
    require(2<=source<50 and 2<=destination<50 and source!=destination,"Live65 cell domain mismatch")
    expected=copy.deepcopy(before)
    cells={row[1]:row for row in before["character_bank_item_slots"]};a=cells[source];b=cells[destination]
    require(0<a[3]<=127,"Live65 source whole count invalid")
    for slot,incoming,physical in ((source,b,a),(destination,a,b)):
        row=next(row for row in expected["character_bank_item_slots"] if row[1]==slot)
        row[2:4]=incoming[2:4];row[4]=physical[4]+1;row[5]=incoming[5] if incoming[3] else physical[5]
    for table,index in (("character_bank_armor_metadata",2),("character_bank_foreign_metadata",3)):
        selected=[copy.deepcopy(row) for row in before[table] if row[1] in (source,destination)]
        expected[table]=[row for row in expected[table] if row[1] not in (source,destination)]
        for row in selected:
            row[1]=destination if row[1]==source else source;row[index+1]=cells[row[1]][4]+1;expected[table].append(row)
        expected[table].sort(key=repr)
    return expected


def actual_family(owner,slot):
    row=next(row for row in owner["character_bank_item_slots"] if row[1]==slot)
    if not row[3]:return "EMPTY"
    body=owned_metadata(owner,"vault",slot)
    if body is None:
        require(row[2]==3107,"Actual mixed UI plain cell is not fixture MED02")
        return "MED"
    require(len(body)==20 and int.from_bytes(body[:2],"little")==row[2],"Actual owned20 source key differs")
    names={2:"EQU",26:"TEQ",1:"WPN",25:"TWP",8:"GEM"}
    require(body[2]&63 in names,"Actual owned20 native family differs")
    return names[body[2]&63]


def verify_mixed_event(event):
    owner=event["identity"];source=event["source"];destination=event["destination"];require(event["opcode"]==101 and event["wire65_marker"]==1 and event.get("receipt_state_verified") is True,"Native65 marker/receipt differs")
    before=event["before"];expected=independent_swap(before,source,destination);after=event["after"]
    require(event["ordered_pair"]==[actual_family(before,source),actual_family(before,destination)],"Actual source/destination families differ from declared UI pair")
    if event["kind"]=="empty_forward":require(destination==49 and source!=49,"Actual forward empty65 direction differs")
    elif event["kind"]=="empty_reverse":require(source==49 and destination!=49,"Actual reverse empty65 direction differs")
    require(expected==event["independently_expected"],"Independent whole mixed swap differs")
    for table in expected:
        if not table.endswith("receipts"):require(expected[table]==after[table],"Whole swap changed preserved rows: "+table)
    raw=event["receipt"];actual_count=next(row[3] for row in before["character_bank_item_slots"] if row[1]==source)
    require(event["whole_qty"]==actual_count and raw[1:8]==[owner,owner,101,0,source,destination,actual_count] and raw[-1]=="CUSTOM-0070","Actual whole quantity/owner receipt differs")
    require(json.loads(raw[8])==receipt_state(before,owner) and json.loads(raw[9])==receipt_state(expected,owner),"Actual exact complete receipt differs from independent before/after")
    old=before["character_bank_mixed_receipts"];new=after["character_bank_mixed_receipts"]
    require(sorted(new,key=repr)==sorted(old+[raw],key=repr),"Actual mixed receipt not exact one addition")
    for table in before:
        if table.endswith("receipts") and table!="character_bank_mixed_receipts":require(before[table]==after[table],"Mixed65 changed prior receipt ledger")

def verify_transport_event(event):
    owner=event["identity"];opcode=event["opcode"];source=event["source"];destination=event["destination"]
    require(opcode in (99,100),"Existing transfer opcode differs")
    source_table="diagnostic_inventory_slots" if opcode==99 else "character_bank_item_slots"
    target_table="character_bank_item_slots" if opcode==99 else "diagnostic_inventory_slots"
    before=event["before"];after=event["after"]
    previous=next(row for row in before[source_table] if row[1]==source)
    remaining=next(row for row in after[source_table] if row[1]==source)
    target_before=next(row for row in before[target_table] if row[1]==destination)
    target_after=next(row for row in after[target_table] if row[1]==destination)
    quantity=previous[3]-remaining[3]
    require(target_before[3]==0 and 0<quantity<=previous[3] and target_after[2:4]==[previous[2],quantity] and remaining[4]==previous[4]+1 and target_after[4]==target_before[4]+1,"Actual existing63/64 quantity/revision differs")
    raw=event["receipt"]
    require(raw[1:8]==[owner,owner,opcode,0,source,destination,quantity] and raw[-1] in ("CUSTOM-0065","CUSTOM-0067","CUSTOM-0068"),"Actual existing-route receipt differs")
    if raw[-1] in ("CUSTOM-0067","CUSTOM-0068"):
        states=[receipt_state(saved,owner) for saved in (before,event["independently_expected"])]
        if raw[-1]=="CUSTOM-0067":
            # Frozen0067 writer order is bag armor, weapons, gems, vault
            # armor. It is not a truncated NEW mixed receipt array.
            states=[[*state[:5],state[6],state[7],state[5]] for state in states]
        require([json.loads(raw[8]),json.loads(raw[9])]==states,"Exact legacy instance receipt before/after differs")
    else:
        def plain_state(saved):
            parts=[]
            for vault,slot in ((opcode==100,source),(opcode==99,destination)):
                row=next(row for row in saved["character_bank_item_slots" if vault else "diagnostic_inventory_slots"] if row[1]==slot)
                parts.append(":".join(str(value) for value in [int(vault),slot,*row[2:6],"CUSTOM-0015"])+";")
            return "".join(parts)
        require([raw[8],raw[9]]==[plain_state(before),plain_state(event["independently_expected"])],"Exact legacy MED receipt before/after differs")
    require(before["character_bank_mixed_receipts"]==after["character_bank_mixed_receipts"],"Existing63/64 mutated mixed65 receipt history")

def verify_relogin_event(result,ui,event):
    old_pids=event["old_client_pids"];new_pids=event["new_client_pids"]
    require(len(old_pids)==len(new_pids)==2 and len(set(old_pids+new_pids))==4 and all(type(pid) is int and pid>0 for pid in old_pids+new_pids),"Two actual client PID generations required")
    require(ui["owned_client_pids"]==old_pids+new_pids and event["before"]==event["after"]==ui["final"]["db"] and all(event.get(key) is True for key in ("full20_verified","full50_verified","full300_verified")),"Actual dual-owner relogin save restoration failed")
    require([(row["identity"],row["language"],row["pid"]) for row in event["native"]]==[(4,950,new_pids[0]),(5,936,new_pids[1])],"Real relogin native owner/PID/language differs")
    for row in event["native"]:native_full(event["after"][str(row["identity"])],row,row["identity"],row["language"])
    terminal=result["owned_pid_terminal"];pids=old_pids+new_pids+[result["server_pid"],result["runner_pid"]]
    require(len(set(pids))==6 and set(terminal)=={str(pid) for pid in pids} and all(row.get("pid_exists") is False for row in terminal.values()),"Exact six owned PID terminal proofs required")


def reject_reparse_chain(path):
    require(path.is_absolute(),"Evidence path must be absolute")
    # Inspect the original lexical path before any resolve follows an alias.
    # Windows junctions are reparse points even when is_symlink() is false.
    for component in (*reversed(path.parents),path):
        info=os.lstat(component)
        require(not component.is_symlink() and not (getattr(info,"st_file_attributes",0)&0x400),"Evidence path contains symlink/junction/reparse point: "+str(component))


def evidence_root():
    expected=ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-06"
    require(RUN.parent==expected and RUN.name=="run-result.json","Fixed repository-owned run06 path differs")
    reject_reparse_chain(expected)
    require(expected.resolve(strict=True)==expected,"Original run06 path resolves outside fixed repository-owned root")
    reject_reparse_chain(RUN)
    return expected


def resolve_event(index,reference):
    require(isinstance(reference,dict) and isinstance(reference.get("evidence"),dict),"Event evidence reference missing")
    evidence=reference["evidence"]
    require(set(evidence)=={"path","sha256","bytes"},"Unexpected event evidence fields")
    expected=f"ui-events/event-{index:06d}.json"
    require(evidence["path"]==expected and type(evidence["bytes"]) is int and evidence["bytes"]>0 and
        isinstance(evidence["sha256"],str) and re.fullmatch(r"[0-9a-f]{64}",evidence["sha256"]) is not None,"Strict contiguous event path/size/hash differs")
    root=evidence_root();path=root/expected
    reject_reparse_chain(path)
    require(path.resolve(strict=True)==root/expected,"Event evidence path escaped its fixed run06 root")
    require(path.stat().st_size==evidence["bytes"],"Event evidence byte length differs")
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):digest.update(chunk)
    require(digest.hexdigest()==evidence["sha256"],"Event evidence SHA256 differs")
    with path.open("r",encoding="utf-8") as stream:event=json.load(stream)
    require(isinstance(event,dict) and {key:value for key,value in reference.items() if key!="evidence"}==event_metadata(event),"Event lightweight metadata differs from complete payload")
    return event


# Metadata tuple is frozen against the NEW writer before the live gate opens.
EVENT_METADATA_KEYS=('operation','identity','language','opcode','source','destination','page','kind','ordered_pair','same_id_different_tail_verified','whole_qty','wire65_marker','native65_marker')

def event_metadata(event):
    require(EVENT_METADATA_KEYS is not None,"NEW v05 event metadata contract not frozen")
    return {key:event[key] for key in EVENT_METADATA_KEYS if key in event}


def ui_gate(result,sources):
    require(result.get("accepted") is True and result.get("runner_exit")==0 and result["candidate_sha256"]==PIN,"Actual native UI receipt failed")
    require(result.get("scope")=="MIXED_BANK_SIX_FAMILIES_36_ORDERED_EACH_TW_CN_CUSTOM_TEST_ONLY","Wrong NEW mixed-bank acceptance scope")
    for key in ("source_files_unchanged","candidate_unchanged","all_owned_processes_closed","private_files_unchanged","all_private_images_closed","bank_swap_harness_unchanged","runtime_sources_unchanged","frozen_files_unchanged","protected_processes_preserved","desktop_owner_unchanged","exclusive2598_released"):
        require(result.get(key) is True,"Actual native guard absent: "+key)
    require(result["runtime_sources_before"]==result["runtime_sources_after"]==sources,"UI not same runtime36")
    require(result["bank_swap_harness_sha256"]==sha(HARNESS),"NEW harness changed")
    require(result["before"]==result["after"] and result["frozen_files_before"]==result["frozen_files_after"],"Protected native files changed")
    for path in (ROOT/"tools/strike_lab/private_owned_mixed_bank_20261003.py",ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-01/run-result.json",ROOT/"tools/strike_lab/private_owned_mixed_bank_v02_20261003.py",ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-02/run-result.json",ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-02/ui-result.json",ROOT/"tools/strike_lab/private_owned_mixed_bank_v03_20261003.py",ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-03/run-result.json",ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-03/ui-result.json",ROOT/"tools/strike_lab/private_owned_mixed_bank_v04_20261003.py",COMPACT_PROOF,ROOT/"tools/strike_lab/private_owned_mixed_bank_v05_20261003.py",ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-05/run-result.json",ROOT/"artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-05/ui-result.json"):
        require(str(path) in result["frozen_files_after"],"Failed earlier run evidence not frozen: "+str(path))
    for path,digest in result["frozen_files_after"].items():require(sha(Path(path))==digest,"Native evidence changed: "+path)
    ui=result["ui"]
    require(ui["accepted"] is True and ui["desktop_unchanged"] is True and ui["all_clients_closed"] is True and ui.get("unrelated_saved_rows_preserved") is True,"Actual mixed UI scope failed")
    qualified=ui["qualified"]
    require(qualified["current_client_sha256"]==sha(managed.CLIENT) and qualified["weapon_source_rows"]==1259 and qualified["weapon_records_sha256"]==WEAPON_CACHE_PIN and len(qualified["regions"])==28,"Actual native code/source qualification absent")
    require(ui.get("matrix_counts")=={"4":UI_COUNTS,"5":UI_COUNTS},"Each language actual36pair/12empty/12deposit/12withdraw coverage missing")
    languages={4:950,5:936}
    require([(row["identity"],row["language"]) for row in ui["final"]["native"]]==list(languages.items()),"TW/CN owner coverage absent")
    require(ui.get("event_evidence_format")=="LOSSLESS_SHA256_EVENT_FILES_V1","Whole event evidence index format differs")
    require(isinstance(ui["events"],list),"Ordered event index missing")
    languages={4:950,5:936}
    guards=("full20_verified","full50_verified","full300_verified","physical_revision_verified","provenance_verified","receipt_state_verified","independent_plan_verified","quantity_conservation","whole_instance_conservation","equipped_preserved","peer_unchanged","other_players_unchanged")
    coverage={owner:{"pair65":0,"empty65":0,"deposit63":0,"withdraw64":0} for owner in languages}
    pairs={owner:set() for owner in languages};forward={owner:set() for owner in languages};reverse={owner:set() for owner in languages}
    same_id={owner:0 for owner in languages};med_stack={owner:False for owner in languages};receipts=set();relogin_count=0
    for index,reference in enumerate(ui["events"]):
        event=resolve_event(index,reference);operation=event["operation"]
        if operation in ("mixed_committed","transport_committed"):
            owner=event["identity"]
            require(owner in languages and event["language"]==languages[owner] and all(event.get(key) is True for key in guards),"Actual full-owner native event guards absent")
            native_full(event["after"],event["native"],owner,languages[owner])
            receipt=event["receipt"][0];require(receipt not in receipts,"Repeated actual native mutation receipt")
            receipts.add(receipt)
            if operation=="mixed_committed":
                verify_mixed_event(event);kind=event["kind"];pair=tuple(event["ordered_pair"])
                if kind=="ordered_pair":
                    coverage[owner]["pair65"]+=1;pairs[owner].add(pair)
                    if pair==("WPN","WPN"):
                        a=owned_metadata(event["before"],"vault",event["source"]);b=owned_metadata(event["before"],"vault",event["destination"])
                        require(event.get("same_id_different_tail_verified") is True and a is not None and b is not None and a[:2]==b[:2] and a[2:]!=b[2:],"Actual same-ID WPN before key/tail proof absent")
                        same_id[owner]+=1
                elif kind=="empty_forward":coverage[owner]["empty65"]+=1;forward[owner].add(pair)
                elif kind=="empty_reverse":coverage[owner]["empty65"]+=1;reverse[owner].add(pair)
                else:require(False,"Unexpected native65 scenario kind")
                if actual_family(event["before"],event["source"])=="MED" and next(row[3] for row in event["before"]["character_bank_item_slots"] if row[1]==event["source"])>1:med_stack[owner]=True
            else:
                verify_transport_event(event)
                coverage[owner]["deposit63" if event["opcode"]==99 else "withdraw64"]+=1
        elif operation=="relogin_full50_full300":
            relogin_count+=1;verify_relogin_event(result,ui,event)
        del event
    require(coverage=={owner:UI_COUNTS for owner in languages} and len(receipts)==144 and relogin_count==1,"Exact144mutation/96mixed+48transport/true relogin coverage missing")
    for owner in languages:
        require(pairs[owner]=={(a,b) for a in FAMILIES for b in FAMILIES} and forward[owner]==reverse[owner]=={(a,"EMPTY") for a in FAMILIES},"Actual six-family36ordered/12empty matrix missing")
        require(same_id[owner]==1 and med_stack[owner],"Actual both-owner same-ID WPN/MEDstack coverage missing")
        before=ui["initial"]["db"][str(owner)];after=ui["final"]["db"][str(owner)]
        require(len(after["character_bank_mixed_receipts"])==len(before["character_bank_mixed_receipts"])+48,"Exactly48 whole65 durable receipts per owner required")
    return {"mixed_committed":96,"transport_committed":48,"true_dual_owner_relogins":1,"event_shards_verified":len(ui["events"])}


def schema_sql():
    source=(ROOT/"src/db/SqliteOwnedMixedBankRepository.cpp").read_text("utf-8")
    match=re.search(r'SqliteOwnedMixedBankRepository::schema\(\)\{return R"SQL\((.*?)\)SQL";',source,re.S)
    require(match is not None,"Pinned schema46 SQL extractor changed")
    return match.group(1)

def schema_gate(before,after,template=None):
    require([row[0] for row in before["history"]]==list(range(1,46)),"Exact installed schema45 required")
    require(not NEW_TABLES.intersection(before["tables"]),"Mixed bank already installed")
    require(after["pragmas"]==before["pragmas"],"Clone pragmas changed")
    require(set(after["tables"])==set(before["tables"])|NEW_TABLES,"Unexpected new tables")
    require([row for row in after["schema"] if row[1] not in NEW_OBJECTS]==before["schema"],"Existing schema objects changed")
    added=[row for row in after["schema"] if row[1] in NEW_OBJECTS]
    require({row[1] for row in added}==NEW_OBJECTS and len(added)==len(NEW_OBJECTS),"Exact new46 objects missing")
    for name,state in before["tables"].items():
        if name!="schema_migrations":require(after["tables"][name]==state,"Existing typed rows/receipts changed: "+name)
    for name in NEW_TABLES:require(after["tables"][name]=={"rows":0,"sha256":hashlib.sha256(b"").hexdigest()},"Custody grant/receipt during stage")
    require(after["history"][:-1]==before["history"] and len(after["history"])==46 and
        after["history"][-1][:3]==[46,"owned_mixed_bank",schema_sql()],"History differs outside exact46")
    if template is not None:require(after["schema"]==template["schema"] and after["history"][-1][:3]==template["history"][-1][:3],"Actual46 differs from clone46")

def source_catalog_gate(database):
    prior.source_catalog_gate(database)
    require(sha(WEAPON_CACHE)==WEAPON_CACHE_PIN,"Pinned native1259 source cache changed")
    expected=read(WEAPON_CACHE)
    require(len(expected)==2 and len(expected[0])==2 and len(expected[1])==1259,"Weapon source namespace incomplete")
    rows=[]
    for item in expected[1]:
        values=list(item)
        for index in (6,8):values[index]=bytes.fromhex(values[index])
        rows.append(tuple(values))
    with closing(prior.sqlite3_connect_readonly(database)) as db:
        db.execute("BEGIN")
        require(tuple(db.execute("SELECT * FROM native_weapon_sources ORDER BY family"))==tuple(tuple(item) for item in expected[0]) and
            tuple(db.execute("SELECT * FROM native_weapon_rows ORDER BY family,item_id"))==tuple(rows),"Native WPN/TWP raw+parsed catalog changed")
        require(db.execute("PRAGMA quick_check").fetchall()==[("ok",)] and not db.execute("PRAGMA foreign_key_check").fetchall(),"Native catalog integrity failed")
    require(sha(MED_CACHE)==MED_CACHE_PIN,"Pinned original71 MED02 cache changed")
    expected_med=read(MED_CACHE)
    require(len(expected_med["source"])==9 and len(expected_med["rows"])==71,"Original MED02 source incomplete")
    med_rows=[]
    for item in expected_med["rows"]:
        values=list(item)
        for index in (5,6):values[index]=bytes.fromhex(values[index])
        med_rows.append(tuple(values))
    with closing(prior.sqlite3_connect_readonly(database)) as db:
        db.execute("BEGIN")
        require(tuple(db.execute("SELECT * FROM native_data_sources WHERE dataset_id=?",(expected_med["source"][0],)))==
            (tuple(expected_med["source"]),) and tuple(db.execute("SELECT * FROM native_med02_recovery_declarations WHERE dataset_id=? ORDER BY source_record_index",
            (expected_med["source"][0],)))==tuple(med_rows),"Original MED02 raw records/tooltips/declarations changed")


def config_after(before):
    require(before["world"].get("owned_armor_transfers")=={"enabled":True} and
        before["world"].get("owned_armor_bank")=={"enabled":True} and
        before["world"].get("owned_foreign_bank")=={"enabled":True} and
        before["world"].get("owned_instance_trade")=={"enabled":True},"Accepted armor/foreign bank predecessor required")
    require(before["world"].get("owned_mixed_bank") in (None,{"enabled":False}),"Owned mixed bank already enabled or unqualified config")
    after=copy.deepcopy(before);after["world"]["owned_mixed_bank"]={"enabled":True};return after

def candidate_run(config,args,log):
    require(sha(CANDIDATE)==PIN,"Candidate changed before clone execution")
    env=os.environ.copy();env["GOD2_LOG_FILE_ONLY"]="1";env.pop("GOD2_NATIVE_WORLD_RECORDS_LAB",None)
    with Path(log).open("wb") as output:subprocess.run([str(CANDIDATE),"--config",str(config),*args],cwd=ROOT,env=env,
        stdout=output,stderr=subprocess.STDOUT,timeout=40,check=True,creationflags=subprocess.CREATE_NO_WINDOW)

def all_process_connections_idle(pid):
    # The character listener can use a dynamic port. Checking only2592 misses
    # its players, so inspect every socket owned by the actual managed process.
    require(type(pid) is int and pid>0,"Invalid managed PID")
    process_before=prior.formal_process_proof(pid)
    result=json.loads(managed.powershell(
        "$ErrorActionPreference='Stop'; $rows=@(Get-NetTCPConnection -OwningProcess "+str(pid)+
        " -ErrorAction Stop); @{pid="+str(pid)+";connections=@($rows|ForEach-Object { @{local_address=$_.LocalAddress;local_port=[int]$_.LocalPort;remote_address=$_.RemoteAddress;remote_port=[int]$_.RemotePort;state=[string]$_.State;pid=[int]$_.OwningProcess} })}|ConvertTo-Json -Depth 5 -Compress").stdout)
    require(result.get("pid")==pid and isinstance(result.get("connections"),list),"All-port connection proof missing")
    rows=result["connections"]
    require(all(row.get("pid")==pid for row in rows),"Connection ownership differs")
    require(any(row.get("state")=="Listen" for row in rows),"Managed process has no listener")
    require(not any(row.get("state") in {"Established","SynReceived","SynSent"} for row in rows),
        "Active or connecting players on a managed port; installation refused")
    require(prior.formal_process_proof(pid)==process_before,"Managed process changed during all-port proof")
    return {"process":process_before,"connections":rows,"all_ports_idle":True}

def stage():
    gate=qualify();require(not STAGE.exists(),"Stage already exists; inspect it")
    require(sha(managed.ACTIVE)==OLD_PIN,"Installed predecessor executable differs")
    config=read(managed.CONFIG);after_config=config_after(config);database=Path(config["database"]["path"]).resolve()
    before=snapshots.capture(database);source_catalog_gate(database)
    require([row[0] for row in before["history"]]==list(range(1,46)),"Stage requires installed schema45")
    STAGE.mkdir(parents=True)
    managed.backup(database,STAGE/"accounts.before.db")
    require(snapshots.capture(STAGE/"accounts.before.db")==before and snapshots.capture(database)==before,"Save changed during clone backup; restage")
    managed.backup(STAGE/"accounts.before.db",STAGE/"town-diagnostic-accounts.db")
    clone=copy.deepcopy(after_config);clone["database"]["path"]=str(STAGE/"town-diagnostic-accounts.db");clone["logging"]["file"]=str(STAGE/"stage.log")
    with socket.socket() as reserve:reserve.bind(("127.0.0.1",0));port=reserve.getsockname()[1]
    clone["server"].update(host="127.0.0.1",port=port,character_port=0)
    write(STAGE/"stage-config.json",clone);write(STAGE/"server-config.after.json",after_config)
    candidate_run(STAGE/"stage-config.json",["--migrate-only"],STAGE/"migration.log")
    candidate_run(STAGE/"stage-config.json",["--run-for","1"],STAGE/"startup.log")
    require(all(marker in (STAGE/"stage.log").read_text("utf-8") for marker in ("OWNED_MIXED_BANK_ENABLED CUSTOM-0070 full_instance no_grants no_formula","OWNED_INSTANCE_TRADE_ENABLED CUSTOM-0069 full_instance no_grants no_formula","OWNED_FOREIGN_BANK_ENABLED CUSTOM-0068 full_instance no_grants no_formula")),"Clone mixed-bank/trade/accepted foreign bank routes did not activate")
    after=snapshots.capture(STAGE/"town-diagnostic-accounts.db");schema_gate(before,after);source_catalog_gate(STAGE/"town-diagnostic-accounts.db")
    require(read(managed.CONFIG)==config and sha(managed.ACTIVE)==OLD_PIN and snapshots.capture(database)==before,"Formal files/save changed during clone stage")
    shutil.copy2(CANDIDATE,STAGE/"god2-server.candidate.exe");shutil.copy2(managed.ACTIVE,STAGE/"god2-server.before.exe");shutil.copy2(managed.CONFIG,STAGE/"server-config.before.json")
    write(STAGE/"save-before.json",before);write(STAGE/"save-stage.json",after)
    info=dict(gate,state="CLONE_STAGED_NOT_INSTALLED",database=str(database),production_executable_sha256=OLD_PIN,
        config_before_sha256=sha(managed.CONFIG),config_after_sha256=sha(STAGE/"server-config.after.json"),
        added_tables=sorted(NEW_TABLES),saved_rows_changed=0,grants=0,capacity_added=0)
    write(STAGE/"release.json",info);return info

def apply():
    gate=qualify();info=read(STAGE/"release.json")
    require(info["state"]=="CLONE_STAGED_NOT_INSTALLED" and all(info[key]==value for key,value in gate.items()),"Exact unchanged qualification/stage required")
    require(sha(managed.ACTIVE)==info["production_executable_sha256"]==OLD_PIN and
        sha(managed.CONFIG)==info["config_before_sha256"] and sha(managed.CLIENT)==info["client_sha256"],"Managed files changed since stage")
    require(sha(STAGE/"god2-server.candidate.exe")==PIN and sha(STAGE/"server-config.after.json")==info["config_after_sha256"],"Staged files changed")
    expected=config_after(read(managed.CONFIG));require(read(STAGE/"server-config.after.json")==expected,"Config changed outside owned mixed bank flag")
    database=Path(info["database"]);before=read(STAGE/"save-before.json");template=read(STAGE/"save-stage.json")
    require(snapshots.capture(database)==before,"Formal saves changed; restage required");source_catalog_gate(database)
    pid=managed.listener();idle_before_backup=all_process_connections_idle(pid)
    managed.backup(database,STAGE/"accounts.at-install.db")
    require(snapshots.capture(STAGE/"accounts.at-install.db")==before and snapshots.capture(database)==before,"Fresh backup differs")
    require(managed.listener()==pid,"Managed PID or active clients changed before stop")
    idle_before_stop=all_process_connections_idle(pid)
    prior.common.lifecycle.stop_managed_and_wait(pid)
    if snapshots.capture(database)!=before:
        managed.start();raise RuntimeError("Save changed while stopping; no installation attempted")
    try:
        shutil.copy2(STAGE/"god2-server.candidate.exe",managed.ACTIVE);shutil.copy2(STAGE/"server-config.after.json",managed.CONFIG)
        env=os.environ.copy();env["GOD2_LOG_FILE_ONLY"]="1";env.pop("GOD2_NATIVE_WORLD_RECORDS_LAB",None)
        with (STAGE/"formal-migration.log").open("wb") as output:subprocess.run([str(managed.ACTIVE),"--config",str(managed.CONFIG),"--migrate-only"],cwd=ROOT,env=env,
            stdout=output,stderr=subprocess.STDOUT,timeout=40,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        schema_gate(before,snapshots.capture(database),template);source_catalog_gate(database)
        require(sha(managed.ACTIVE)==PIN and sha(managed.CONFIG)==info["config_after_sha256"] and sha(managed.CLIENT)==info["client_sha256"],"Installed files differ")
        formal_log=Path(expected["logging"]["file"]);log_before=formal_log.read_bytes() if formal_log.exists() else b""
        managed.start();managed.powershell("$deadline=(Get-Date).AddSeconds(20); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed listener not ready'}")
        new_pid=managed.listener();process=prior.formal_process_proof(new_pid);startup=prior.startup_log_gate(formal_log,log_before)
        appended=formal_log.read_bytes()[len(log_before):].decode("utf-8",errors="replace")
        marker="OWNED_MIXED_BANK_ENABLED CUSTOM-0070 full_instance no_grants no_formula"
        require(marker in appended and "OWNED_INSTANCE_TRADE_ENABLED CUSTOM-0069 full_instance no_grants no_formula" in appended and "OWNED_FOREIGN_BANK_ENABLED CUSTOM-0068 full_instance no_grants no_formula" in appended,"Actual formal mixed-bank/trade/accepted foreign bank routes did not activate")
        actual=snapshots.capture(database);schema_gate(before,actual,template);source_catalog_gate(database)
        require(frozen.hashes()==read(frozen.BASELINE)["source_sha256"],"Frozen chat changed during installation")
        runtime_after={path:sha(prior.checked_path(path)) for path in gate["source_sha256"]}
        require(runtime_after==gate["source_sha256"],"Installed runtime36 source proof changed")
        proof={"process":process,"prior_startup":startup,"mixed_bank_marker":[line for line in appended.splitlines() if marker in line],
            "runtime_sources_after":runtime_after,"runtime_sources_unchanged":True,
            "idle_before_fresh_backup":idle_before_backup,"idle_immediately_before_stop":idle_before_stop}
        write(STAGE/"formal-startup-proof.json",proof);write(STAGE/"save-installed.json",actual)
        info.update(state="INSTALLED",server_pid=new_pid,installed_at=prior.common.now(),saved_rows_changed=0,grants=0,capacity_added=0,
            formal_startup_proof_sha256=sha(STAGE/"formal-startup-proof.json"));write(STAGE/"release.json",info);return info
    except BaseException as error:
        info.update(state="REPAIR_REQUIRED_SCHEMA46_COMPATIBLE_CANDIDATE_RETAINED",error=str(error),database_restored=False,old_executable_restored=False)
        write(STAGE/"release.json",info)
        if sha(managed.ACTIVE)==PIN:
            try:managed.start()
            except Exception:pass
        raise

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=("qualify","stage","apply"));args=parser.parse_args()
    result={"qualify":qualify,"stage":stage,"apply":apply}[args.mode]()
    print(json.dumps({key:result.get(key) for key in ("state","candidate_sha256","mixed_committed","saved_rows_changed","grants","capacity_added")}))
