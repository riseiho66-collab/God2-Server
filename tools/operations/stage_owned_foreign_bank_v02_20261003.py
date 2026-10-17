# Legacy receipt identifiers retain their schema spelling; both cases are the
# Taiwan client using Traditional CP950 or Simplified CP936, not regional protocols.
"""CUSTOM-0068 immutable qualify, schema43->44 clone stage and explicit apply.

Do not run a mode until root authorizes it. Stage modifies only a new owned
clone. Apply makes a fresh consistent backup, refuses active2592 clients, and
stops only the managed task. Never restore saves or run old43 after migration44.
Signature/asset protection remains deferred; this is only bank transport.
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
PIN="2172c96919473225af845abc42ceae08ae7db98c3e50fbff711614a2938c7089"
OLD_PIN="5e7f999e038fd6dad63a714be8e5352f765a973599f860880a17855848126dd1"
CANDIDATE=ROOT/"build-owned-foreign-bank-20261003/Release/god2-server.exe"
CONTRACT=ROOT/"artifacts/research/owned-foreign-bank-0068/candidate-20261003/contract.json"
RUN=ROOT/"artifacts/playtests/private-native-blackbox-owned-foreign-bank-20261003-02/run-result.json"
HARNESS=ROOT/"tools/strike_lab/private_owned_foreign_bank_v02_20261003.py"
LOG=ROOT/"artifacts/research/owned-foreign-bank-0068/root-ctest-qualified.log"
BUILD_LOG=ROOT/"artifacts/research/owned-foreign-bank-0068/root-build-qualified.log"
STAGE=ROOT/"artifacts/releases/owned-foreign-bank-20261003/clone-stage-v02"
WEAPON_CACHE=ROOT/"artifacts/research/native-weapons-20260926/records.json"
WEAPON_CACHE_PIN="c42839db91f3bd8ff377fa7995cb0f421c3fabb961eb79f68ae3e9fd97ff18b3"
NEW_TABLES={"character_bank_foreign_metadata","character_bank_foreign_receipts"}
NEW_OBJECTS=NEW_TABLES|{"sqlite_autoindex_character_bank_foreign_metadata_1",
    "sqlite_autoindex_character_bank_foreign_receipts_1","bank_foreign_insert_guard",
    "bank_foreign_update_guard","bank_armor_foreign_insert_guard","bank_armor_foreign_update_guard"}
REQUIRED={"storage_owned_foreign_bank_0068","storage_owned_foreign_bank_service_0068",
    "storage_owned_foreign_bank_adapter_0068","storage_owned_armor_bank_0067",
    "storage_owned_armor_bank_adapter_0067","storage_owned_armor_bank_service_0067",
    "bank_items_repository","bank_service","armor_slots","owned_armor_transfer",
    "owned_bag_projection","owned_bank_trade_projection","sqlite_armor_production_adapter",
    "database","config","recovered_account_login","recovered_character_repository"}
TEST_SOURCES={"tests/storage_owned_foreign_bank_0068.cpp",
    "tests/storage_owned_foreign_bank_service_0068.cpp","tests/storage_owned_foreign_bank_adapter_0068.cpp"}

def qualify():
    require(sha(CANDIDATE)==PIN,"Candidate differs from reviewed immutable build")
    contract=read(CONTRACT)
    require(contract["candidate_sha256"]==PIN and contract["design"]=="CUSTOM-0068","Runtime contract differs")
    sources=contract["source_sha256"]
    require(isinstance(sources,dict) and len(sources)==28,"Exact runtime28 contract required")
    for path,digest in sources.items():require(sha(prior.checked_path(path))==digest,"Runtime changed: "+path)
    require(set(contract["test_sha256"])==TEST_SOURCES,"Exact new storage/service/adapter tests required")
    for path,digest in contract["test_sha256"].items():require(sha(prior.checked_path(path))==digest,"Accepted test changed: "+path)
    require(contract.get("ctest_passed")==17 and prior.checked_path(contract["ctest_log"])==LOG and
        contract["ctest_sha256"]==sha(LOG) and contract["build_sha256"]==sha(BUILD_LOG),"Missing exact terminal17/build proof")
    prior.ctest_gate(LOG,17,REQUIRED)
    result=read(RUN)
    require(result.get("accepted") is True and result.get("runner_exit")==0 and result["candidate_sha256"]==PIN,
        "Actual native UI receipt failed")
    require(result.get("scope")=="FOREIGN24_ARMOR12_MED20_TW_CN_CUSTOM_TEST_ONLY","Wrong native UI acceptance scope")
    for key in ("source_files_unchanged","candidate_unchanged","all_owned_processes_closed",
        "private_files_unchanged","all_private_images_closed","bank_swap_harness_unchanged",
        "runtime_sources_unchanged","frozen_files_unchanged","protected_processes_preserved",
        "desktop_owner_unchanged","exclusive2598_released"):
        require(result.get(key) is True,"Actual native guard absent: "+key)
    require(result["runtime_sources_before"]==result["runtime_sources_after"]==sources,"UI not same runtime28")
    require(result["bank_swap_harness_sha256"]==sha(HARNESS),"Native harness changed")
    require(result["before"]==result["after"] and result["frozen_files_before"]==result["frozen_files_after"],"Protected native files changed")
    for path,digest in result["frozen_files_after"].items():require(sha(Path(path))==digest,"Native evidence changed: "+path)
    terminal=result.get("owned_pid_terminal")
    require(isinstance(terminal,dict) and terminal and all(row.get("pid_exists") is False for row in terminal.values()),"Native cleanup incomplete")
    ui=result["ui"]
    require(ui["accepted"] is True and ui["desktop_unchanged"] is True and ui["all_clients_closed"] is True,"UI scope failed")
    require([(row["identity"],row["language"]) for row in ui["final"]["native"]]==[(4,950),(5,936)],"TW CP950/CP936 owner coverage absent")
    foreign=[event for event in ui["events"] if event["operation"]=="foreign_committed"]
    armor=[event for event in ui["events"] if event["operation"]=="armor_committed"]
    med=[event for event in ui["events"] if event["operation"] in ("0x63","0x64","0x65")]
    refusals=[event for event in ui["events"] if event["operation"]=="foreign_cross_domain_rejected"]
    require((len(foreign),len(armor),len(med),len(refusals))==(24,12,20,4),"Actual native mutation/refusal coverage differs")
    for owner in (4,5):
        own_foreign=[event for event in foreign if event["identity"]==owner]
        own_armor=[event for event in armor if event["identity"]==owner]
        own_refusals=[event for event in refusals if event["identity"]==owner]
        require(len(own_foreign)==12 and {event["opcode"] for event in own_foreign}=={99,100,101} and
            all(event.get("full20_verified") is True for event in own_foreign),"Foreign per-owner full20 coverage absent")
        require([(event["opcode"],event["source"],event["destination"]) for event in own_armor]==
            [(99,0,4),(99,1,5),(101,4,5),(101,4,5),(100,4,0),(100,5,1)] and
            all(event["full20_verified"] is True for event in own_armor),"Armor per-owner regression differs")
        require(sum(event["after"]["native"]["identity"]==owner for event in med)==10,"MED per-owner coverage differs")
        require(len(own_refusals)==2 and all(event["opcode"]==101 and event.get("all_saved_rows_unchanged") is True and
            event.get("whole_db_unchanged") is True and event.get("native_full20_preserved") is True and
            event.get("full_native_restored") is True and event.get("application_rejected") is True and
            event.get("peer_unchanged") is True for event in own_refusals),"Mixed65 saved/native restoration proof missing")
    require(ui.get("matrix_counts")=={str(owner):{"foreign_committed":12,"armor_committed":6,
        "foreign_cross_domain_rejected":2,"0x63":3,"0x64":4,"0x65":3} for owner in (4,5)},"Exact two-owner UI matrix missing")
    require(len(ui["final"]["db"]["receipts"])==20,"MED durable receipt coverage differs")
    require(sha(managed.CLIENT)==contract["client_sha256"],"Production client changed")
    baseline=read(frozen.BASELINE)
    require(baseline["current_client_accepted"] is True and frozen.hashes()==baseline["source_sha256"],"Frozen accepted chat baseline changed")
    return {"candidate_sha256":PIN,"client_sha256":contract["client_sha256"],"source_sha256":sources,
        "contract_sha256":sha(CONTRACT),"native_run_sha256":sha(RUN),"harness_sha256":sha(HARNESS),
        "ctest_sha256":sha(LOG),"build_sha256":sha(BUILD_LOG),"helper_sha256":sha(Path(__file__)),
        "foreign_commits":24,"armor_commits":12,"med_commits":20,"mixed_refusals":4,"ctest_passed":17}

def schema_sql():
    source=(ROOT/"src/db/SqliteOwnedForeignBankRepository.cpp").read_text("utf-8")
    match=re.search(r'SqliteOwnedForeignBankRepository::schema\(\)\{return R"SQL\((.*?)\)SQL";',source,re.S)
    require(match is not None,"Pinned schema44 SQL extractor changed")
    return match.group(1)

def schema_gate(before,after,template=None):
    require([row[0] for row in before["history"]]==list(range(1,44)),"Exact installed schema43 required")
    require(not NEW_TABLES.intersection(before["tables"]),"Foreign custody already installed")
    require(after["pragmas"]==before["pragmas"],"Clone pragmas changed")
    require(set(after["tables"])==set(before["tables"])|NEW_TABLES,"Unexpected new tables")
    require([row for row in after["schema"] if row[1] not in NEW_OBJECTS]==before["schema"],"Existing schema objects changed")
    added=[row for row in after["schema"] if row[1] in NEW_OBJECTS]
    require({row[1] for row in added}==NEW_OBJECTS and len(added)==len(NEW_OBJECTS),"Exact new44 objects missing")
    for name,state in before["tables"].items():
        if name!="schema_migrations":require(after["tables"][name]==state,"Existing typed rows/receipts changed: "+name)
    for name in NEW_TABLES:require(after["tables"][name]=={"rows":0,"sha256":hashlib.sha256(b"").hexdigest()},"Custody grant/receipt during stage")
    require(after["history"][:-1]==before["history"] and len(after["history"])==44 and
        after["history"][-1][:3]==[44,"owned_foreign_bank_instances",schema_sql()],"History differs outside exact44")
    if template is not None:require(after["schema"]==template["schema"] and after["history"][-1][:3]==template["history"][-1][:3],"Actual44 differs from clone44")

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

def config_after(before):
    require(before["world"].get("owned_armor_transfers")=={"enabled":True} and
        before["world"].get("owned_armor_bank")=={"enabled":True},"Already accepted armor bank required")
    require(before["world"].get("owned_foreign_bank") in (None,{"enabled":False}),"Foreign bank already enabled or unqualified config")
    after=copy.deepcopy(before);after["world"]["owned_foreign_bank"]={"enabled":True};return after

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
    require([row[0] for row in before["history"]]==list(range(1,44)),"Stage requires installed schema43")
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
    require("OWNED_FOREIGN_BANK_ENABLED CUSTOM-0068 full_instance no_grants no_formula" in (STAGE/"stage.log").read_text("utf-8"),"Clone route did not activate")
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
    expected=config_after(read(managed.CONFIG));require(read(STAGE/"server-config.after.json")==expected,"Config changed outside foreign flag")
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
        marker="OWNED_FOREIGN_BANK_ENABLED CUSTOM-0068 full_instance no_grants no_formula"
        require(marker in appended,"Actual formal foreign bank route did not activate")
        actual=snapshots.capture(database);schema_gate(before,actual,template);source_catalog_gate(database)
        require(frozen.hashes()==read(frozen.BASELINE)["source_sha256"],"Frozen chat changed during installation")
        proof={"process":process,"prior_startup":startup,"foreign_marker":[line for line in appended.splitlines() if marker in line],
            "idle_before_fresh_backup":idle_before_backup,"idle_immediately_before_stop":idle_before_stop}
        write(STAGE/"formal-startup-proof.json",proof);write(STAGE/"save-installed.json",actual)
        info.update(state="INSTALLED",server_pid=new_pid,installed_at=prior.common.now(),saved_rows_changed=0,grants=0,capacity_added=0,
            formal_startup_proof_sha256=sha(STAGE/"formal-startup-proof.json"));write(STAGE/"release.json",info);return info
    except BaseException as error:
        info.update(state="REPAIR_REQUIRED_SCHEMA44_COMPATIBLE_CANDIDATE_RETAINED",error=str(error),database_restored=False,old_executable_restored=False)
        write(STAGE/"release.json",info)
        if sha(managed.ACTIVE)==PIN:
            try:managed.start()
            except Exception:pass
        raise

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=("qualify","stage","apply"));args=parser.parse_args()
    result={"qualify":qualify,"stage":stage,"apply":apply}[args.mode]()
    print(json.dumps({key:result.get(key) for key in ("state","candidate_sha256","foreign_commits","armor_commits","med_commits","mixed_refusals","saved_rows_changed","grants","capacity_added")}))
