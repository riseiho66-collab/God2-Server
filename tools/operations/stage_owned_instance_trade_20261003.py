"""CUSTOM-0069 immutable qualify, schema44->45 clone stage and explicit apply.

Do not run a mode until root authorizes it. Stage modifies only a new owned
clone. Apply makes a fresh consistent backup, refuses active2592 clients, and
stops only the managed task. Never restore saves or run old44 after migration45.
Signature/asset protection remains deferred; this is only owned-instance trade custody.
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
PIN="4a309a8cbc2994b59f235fda008d299b7ba443e2c725edc517a545c3df49bf72"
OLD_PIN="2172c96919473225af845abc42ceae08ae7db98c3e50fbff711614a2938c7089"
CANDIDATE=ROOT/"build-owned-instance-trade-20261003/Release/god2-server.exe"
CONTRACT=ROOT/"artifacts/research/owned-instance-trade-0069/candidate-20261003/contract.json"
RUN=ROOT/"artifacts/playtests/private-native-blackbox-owned-instance-trade-20261003-01/run-result.json"
HARNESS=ROOT/"tools/strike_lab/private_owned_instance_trade_20261003.py"
LOG=ROOT/"artifacts/research/owned-instance-trade-0069/root-ctest-02.log"
BUILD_LOG=ROOT/"artifacts/research/owned-instance-trade-0069/root-build-03.log"
STAGE=ROOT/"artifacts/releases/owned-instance-trade-20261003/clone-stage"
WEAPON_CACHE=ROOT/"artifacts/research/native-weapons-20260926/records.json"
WEAPON_CACHE_PIN="c42839db91f3bd8ff377fa7995cb0f421c3fabb961eb79f68ae3e9fd97ff18b3"
MED_CACHE=ROOT/"artifacts/research/owned-instance-trade-0069/native-med02-cache.json"
MED_CACHE_PIN="a0aa6832340d5b48b0943572e4fd18514af21775101f4162fe6fc72d085bfd1e"
NEW_TABLES={"character_owned_instance_trade_receipts"}
NEW_OBJECTS=NEW_TABLES|{"sqlite_autoindex_character_owned_instance_trade_receipts_1"}
REQUIRED={"storage_owned_instance_trade_0069","storage_owned_instance_trade_service_0069",
    "storage_owned_instance_trade_adapter_0069","storage_owned_foreign_bank_0068",
    "storage_owned_foreign_bank_service_0068","storage_owned_foreign_bank_adapter_0068",
    "storage_owned_armor_bank_0067","storage_owned_armor_bank_adapter_0067","storage_owned_armor_bank_service_0067",
    "bank_items_repository","bank_service","recovered_trade","trade_repository","trade_service",
    "armor_slots","owned_armor_transfer","owned_bag_projection","owned_bank_trade_projection",
    "sqlite_armor_production_adapter","database","config","recovered_account_login","recovered_character_repository"}
TEST_SOURCES={"tests/storage_owned_instance_trade_0069.cpp","tests/storage_owned_instance_trade_service_0069.cpp",
    "tests/storage_owned_instance_trade_adapter_0069.cpp","tests/storage_owned_foreign_bank_adapter_0068.cpp"}
REGRESSION_TEST_SOURCES={'tests/test_recovered_trade.cpp', 'tests/test_bank_items_repository.cpp', 'tests/test_owned_bank_trade_projection.cpp', 'tests/test_owned_bag_projection.cpp', 'tests/storage_owned_armor_bank_0067.cpp', 'tests/storage_owned_armor_bank_adapter_0067.cpp', 'tests/storage_owned_foreign_bank_service_0068.cpp', 'tests/test_owned_armor_transfer.cpp', 'tests/test_bank_service.cpp', 'tests/test_database.cpp', 'tests/test_trade_repository.cpp', 'tests/test_config.cpp', 'tests/storage_owned_armor_bank_service_0067.cpp', 'tests/test_sqlite_armor_production_adapter.cpp', 'tests/test_recovered_character_repository.cpp', 'tests/storage_owned_foreign_bank_0068.cpp', 'tests/test_armor_slots.cpp', 'tests/test_trade_service.cpp', 'tests/test_recovered_account_login.cpp'}
NATIVE_EVIDENCE_PATHS={'artifacts/research/current-trade-instances-20261003/consumer-boundary-controls-v02.json', 'artifacts/research/current-trade-instances-20261003/run01/native.json'}
UI_COUNTS={"open29":5,"cancel2D":2,"settle":2,"offer2A":56,"durability_reopen":1,"relogin_full50":1}
SETTLE_GUARDS=("independent_plan_verified","full50_verified","provenance_preserved","equipped_preserved",
    "other_players_unchanged","receipt_verified","physical_revisions_verified","whole_instance_conservation")

def qualify():
    require(isinstance(PIN,str) and re.fullmatch(r"[0-9a-f]{64}",PIN) is not None,"Root frozen candidate PIN not yet set")
    require(sha(CANDIDATE)==PIN,"Candidate differs from reviewed immutable build")
    contract=read(CONTRACT)
    require(contract["candidate_sha256"]==PIN and contract["design"]=="CUSTOM-0069" and
        contract["predecessor_sha256"]==OLD_PIN and prior.checked_path(contract["candidate_path"])==CANDIDATE and
        (contract["schema_before"],contract["schema_after"])==(44,45),"Runtime contract differs")
    sources=contract["source_sha256"]
    require(isinstance(sources,dict) and len(sources)==32,"Exact runtime32 contract required")
    for path,digest in sources.items():require(sha(prior.checked_path(path))==digest,"Runtime changed: "+path)
    for field,paths in (("test_sha256",TEST_SOURCES),("regression_test_sha256",REGRESSION_TEST_SOURCES)):
        require(set(contract[field])==paths,"Exact accepted tests required: "+field)
        for path,digest in contract[field].items():require(sha(prior.checked_path(path))==digest,"Accepted test changed: "+path)
    require(contract.get("ctest_passed")==23 and prior.checked_path(contract["ctest_log"])==LOG and
        prior.checked_path(contract["build_log"])==BUILD_LOG and contract["ctest_sha256"]==sha(LOG) and
        contract["build_sha256"]==sha(BUILD_LOG),"Missing exact terminal23/build03 proof")
    prior.ctest_gate(LOG,23,REQUIRED)
    require(set(contract["native_evidence"])==NATIVE_EVIDENCE_PATHS and contract.get("native_offline_cases")==4072,"Native offline qualification differs")
    for path,digest in contract["native_evidence"].items():require(sha(prior.checked_path(path))==digest,"Accepted native evidence changed: "+path)

    result=read(RUN)
    require(result.get("accepted") is True and result.get("runner_exit")==0 and result["candidate_sha256"]==PIN,"Actual native UI receipt failed")
    require(result.get("scope")=="OWNED_INSTANCE_TRADE_FULL20_TW_CN_CUSTOM_TEST_ONLY","Wrong native UI acceptance scope")
    for key in ("source_files_unchanged","candidate_unchanged","all_owned_processes_closed",
        "private_files_unchanged","all_private_images_closed","trade_harness_unchanged","control_layouts_verified",
        "runtime_sources_unchanged","frozen_files_unchanged","protected_processes_preserved",
        "desktop_owner_unchanged","exclusive2598_released"):
        require(result.get(key) is True,"Actual native guard absent: "+key)
    require(result["runtime_sources_before"]==result["runtime_sources_after"]==sources,"UI not same runtime32")
    require(result["trade_harness_sha256"]==sha(HARNESS),"Native harness changed")
    require(result["before"]==result["after"] and result["frozen_files_before"]==result["frozen_files_after"],"Protected native files changed")
    for path,digest in result["frozen_files_after"].items():require(sha(Path(path))==digest,"Native evidence changed: "+path)
    terminal=result.get("owned_pid_terminal")
    require(isinstance(terminal,dict) and terminal and all(row.get("pid_exists") is False for row in terminal.values()),"Native cleanup incomplete")
    ui=result["ui"]
    require(ui["accepted"] is True and ui["desktop_unchanged"] is True and ui["all_clients_closed"] is True and
        ui.get("unrelated_saved_rows_preserved") is True,"UI scope failed")
    require([(row["identity"],row["language"]) for row in ui["final"]["native"]]==[(4,950),(5,936)],"TW/CN owner coverage absent")
    require(ui.get("scenario_counts")==UI_COUNTS,"Exact live two-direction scenario counts differ")
    for operation,count in UI_COUNTS.items():require(sum(event["operation"]==operation for event in ui["events"])==count,"Actual UI event coverage differs: "+operation)
    settlements=[event for event in ui["events"] if event["operation"]=="settle"]
    require({event["requester"] for event in settlements}=={4,5},"Both requesting owners not settled")
    for event in settlements:
        require(all(event.get(name) is True for name in SETTLE_GUARDS),"Settlement full-owner/native/receipt proof incomplete")
        require("committed=true rejected=false CUSTOM-0069" in event["application_marker"],"Actual Application commit marker absent")
        raw=event["receipt"];owner=event["requester"];peer=9-owner
        require(raw[1:5]==[owner,owner,peer,peer] and raw[-1]=="CUSTOM-0069","Actual receipt owner/design differs")
        receipt=event["actual_receipt"]
        for field in ("before","after","offers"):
            actual=receipt[field+"_state"];actual=json.loads(actual) if isinstance(actual,str) else actual
            require(actual==event[field+"_expected"],"Independent settlement receipt mismatch: "+field)
    cancellations=[event for event in ui["events"] if event["operation"]=="cancel2D"]
    require({event["requester"] for event in cancellations}=={4,5} and all(event.get("all_saved_rows_unchanged") is True and
        event.get("full_native_restored") is True for event in cancellations),"Both cancellation full restoration proofs absent")
    offered=[event for event in ui["events"] if event["operation"]=="offer2A"]
    require(all(event.get("full20_verified") is True for event in offered) and
        all(sum(event["source"]==owner for event in offered)==28 for owner in (4,5)),"Both owners' full20 native offers absent")
    durable=[event for event in ui["events"] if event["operation"]=="durability_reopen"][0]
    require(durable.get("full50_verified") is True and durable["before"]==durable["after"],"Durability reopen mutated saves or omitted full50")
    relogin=[event for event in ui["events"] if event["operation"]=="relogin_full50"][0]
    require(relogin.get("owners")==[4,5] and relogin.get("languages")=={"4":950,"5":936} and
        all(relogin.get(key) is True for key in ("old_clients_closed","both_owner_saved_equal","full20_verified","full50_verified")) and
        relogin["before"]==relogin["after"]==durable["after"],"Real dual-owner relogin restoration incomplete")
    old_pids=relogin["old_client_pids"];new_pids=relogin["new_client_pids"]
    require(len(old_pids)==len(new_pids)==2 and len(set(old_pids+new_pids))==4 and
        all(type(pid) is int and pid>0 for pid in old_pids+new_pids),"Two real client generations required")
    require(ui.get("owned_client_pids")==old_pids+new_pids,"Owned client PID history incomplete")
    expected_terminal={str(pid) for pid in old_pids+new_pids+[result["server_pid"],result["runner_pid"]]}
    require(len(expected_terminal)==6 and set(terminal)==expected_terminal,"All six owned PID terminal proofs required")
    require([(row["identity"],row["native"]["language"],row["native"]["pid"]) for row in relogin["native"]]==
        [(4,950,new_pids[0]),(5,936,new_pids[1])],"Actual new-PID TW/CN observations differ")
    wallets={row[0]:row[1] for row in relogin["after"]["character_trade_wallets"]}
    for observation in relogin["native"]:
        owner=observation["identity"];cells=observation["full50"]
        require([cell["slot"] for cell in cells]==list(range(50)),"Relogin did not observe every physical cell")
        require(observation["native"]["purse"]==wallets[owner],"Relogin native wallet differs from saved wallet")
        for cell in cells:
            require(cell.get("valid") is True,"Relogin native cell validation failed")
            raw=bytes.fromhex(cell["raw24"]);scalar=cell["sql_scalar"]
            require(len(raw)==24,"Relogin native physical cell not full24")
            quantity=int.from_bytes(raw[:4],"little")
            if scalar is None:
                # Native41 leaves inactive bytes behind. Absent capacity is
                # observed as count0, never granted or fabricated as a row.
                require(quantity==0 and cell["expected20"] is None,"Absent relogin cell became occupied")
                continue
            require(scalar[0]==owner and scalar[1]==cell["slot"] and quantity==scalar[3] and
                int.from_bytes(raw[4:6],"little")==scalar[2],"Relogin explicit scalar/key/count differs")
            if scalar[3] and cell["expected20"] is not None:
                require(raw[4:]==bytes.fromhex(cell["expected20"]),"Relogin lost complete owned20 bytes")
    require(len(ui["final"]["db"]["character_owned_instance_trade_receipts"])==
        len(ui["initial"]["db"]["character_owned_instance_trade_receipts"])+2,"Two durable owned-instance receipts required")
    require(sha(managed.CLIENT)==contract["client_sha256"],"Production client changed")
    baseline=read(frozen.BASELINE)
    require(baseline["current_client_accepted"] is True and frozen.hashes()==baseline["source_sha256"],"Frozen accepted chat baseline changed")
    return {"candidate_sha256":PIN,"client_sha256":contract["client_sha256"],"source_sha256":sources,
        "contract_sha256":sha(CONTRACT),"native_run_sha256":sha(RUN),"harness_sha256":sha(HARNESS),
        "ctest_sha256":sha(LOG),"build_sha256":sha(BUILD_LOG),"helper_sha256":sha(Path(__file__)),
        "trade_settlements":2,"trade_cancellations":2,"trade_offers":56,"true_dual_owner_relogins":1,"ctest_passed":23}

def schema_sql():
    source=(ROOT/"src/db/SqliteOwnedInstanceTradeRepository.cpp").read_text("utf-8")
    match=re.search(r'SqliteOwnedInstanceTradeRepository::schema\(\)\{return R"SQL\((.*?)\)SQL";',source,re.S)
    require(match is not None,"Pinned schema45 SQL extractor changed")
    return match.group(1)

def schema_gate(before,after,template=None):
    require([row[0] for row in before["history"]]==list(range(1,45)),"Exact installed schema44 required")
    require(not NEW_TABLES.intersection(before["tables"]),"Owned instance trade already installed")
    require(after["pragmas"]==before["pragmas"],"Clone pragmas changed")
    require(set(after["tables"])==set(before["tables"])|NEW_TABLES,"Unexpected new tables")
    require([row for row in after["schema"] if row[1] not in NEW_OBJECTS]==before["schema"],"Existing schema objects changed")
    added=[row for row in after["schema"] if row[1] in NEW_OBJECTS]
    require({row[1] for row in added}==NEW_OBJECTS and len(added)==len(NEW_OBJECTS),"Exact new45 objects missing")
    for name,state in before["tables"].items():
        if name!="schema_migrations":require(after["tables"][name]==state,"Existing typed rows/receipts changed: "+name)
    for name in NEW_TABLES:require(after["tables"][name]=={"rows":0,"sha256":hashlib.sha256(b"").hexdigest()},"Custody grant/receipt during stage")
    require(after["history"][:-1]==before["history"] and len(after["history"])==45 and
        after["history"][-1][:3]==[45,"owned_instance_trade",schema_sql()],"History differs outside exact45")
    if template is not None:require(after["schema"]==template["schema"] and after["history"][-1][:3]==template["history"][-1][:3],"Actual45 differs from clone45")

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
        before["world"].get("owned_foreign_bank")=={"enabled":True},"Accepted armor/foreign bank predecessor required")
    require(before["world"].get("owned_instance_trade") in (None,{"enabled":False}),"Owned instance trade already enabled or unqualified config")
    after=copy.deepcopy(before);after["world"]["owned_instance_trade"]={"enabled":True};return after

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
    require([row[0] for row in before["history"]]==list(range(1,45)),"Stage requires installed schema44")
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
    require(all(marker in (STAGE/"stage.log").read_text("utf-8") for marker in ("OWNED_INSTANCE_TRADE_ENABLED CUSTOM-0069 full_instance no_grants no_formula","OWNED_FOREIGN_BANK_ENABLED CUSTOM-0068 full_instance no_grants no_formula")),"Clone trade or accepted foreign bank route did not activate")
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
    expected=config_after(read(managed.CONFIG));require(read(STAGE/"server-config.after.json")==expected,"Config changed outside owned instance trade flag")
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
        marker="OWNED_INSTANCE_TRADE_ENABLED CUSTOM-0069 full_instance no_grants no_formula"
        require(marker in appended and "OWNED_FOREIGN_BANK_ENABLED CUSTOM-0068 full_instance no_grants no_formula" in appended,"Actual formal trade or accepted foreign bank route did not activate")
        actual=snapshots.capture(database);schema_gate(before,actual,template);source_catalog_gate(database)
        require(frozen.hashes()==read(frozen.BASELINE)["source_sha256"],"Frozen chat changed during installation")
        proof={"process":process,"prior_startup":startup,"trade_marker":[line for line in appended.splitlines() if marker in line],
            "idle_before_fresh_backup":idle_before_backup,"idle_immediately_before_stop":idle_before_stop}
        write(STAGE/"formal-startup-proof.json",proof);write(STAGE/"save-installed.json",actual)
        info.update(state="INSTALLED",server_pid=new_pid,installed_at=prior.common.now(),saved_rows_changed=0,grants=0,capacity_added=0,
            formal_startup_proof_sha256=sha(STAGE/"formal-startup-proof.json"));write(STAGE/"release.json",info);return info
    except BaseException as error:
        info.update(state="REPAIR_REQUIRED_SCHEMA45_COMPATIBLE_CANDIDATE_RETAINED",error=str(error),database_restored=False,old_executable_restored=False)
        write(STAGE/"release.json",info)
        if sha(managed.ACTIVE)==PIN:
            try:managed.start()
            except Exception:pass
        raise

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=("qualify","stage","apply"));args=parser.parse_args()
    result={"qualify":qualify,"stage":stage,"apply":apply}[args.mode]()
    print(json.dumps({key:result.get(key) for key in ("state","candidate_sha256","trade_settlements","trade_cancellations","trade_offers","saved_rows_changed","grants","capacity_added")}))
