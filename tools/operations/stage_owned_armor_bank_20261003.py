"""CUSTOM-0067 immutable candidate qualification and production-save clone stage.

Stage mutates only an owned clone. Apply requires the exact qualified staged
candidate, no active players and a fresh backup. Never restore old saves or
launch the schema42 executable against upgraded schema43 data.
"""
import argparse,copy,json,hashlib,shutil,socket,subprocess,os
from pathlib import Path
from tools.operations import native_armor_transfer_release_20261002 as prior
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import verify_frozen_chat_20260927 as frozen
ROOT=prior.ROOT
managed=prior.managed
sha=prior.sha
require=prior.require
read=prior.read
write=prior.write
PIN="5e7f999e038fd6dad63a714be8e5352f765a973599f860880a17855848126dd1"
CANDIDATE=ROOT/"build-owned-armor-bank-20261003/Release/god2-server.exe"
CONTRACT=ROOT/"artifacts/research/owned-armor-bank-0067/candidate-20261003/contract.json"
RUN=ROOT/"artifacts/playtests/private-native-blackbox-owned-armor-bank-20261003-03/run-result.json"
HARNESS=ROOT/"tools/strike_lab/private_owned_armor_bank_20261003.py"
LOG=ROOT/"artifacts/research/owned-armor-bank-0067/ctest-final-20261003.log"
STAGE=ROOT/"artifacts/releases/owned-armor-bank-20261003/clone-stage"
NEW_TABLES={"character_bank_armor_metadata","character_bank_armor_receipts"}
NEW_OBJECTS=NEW_TABLES|{"sqlite_autoindex_character_bank_armor_metadata_1","sqlite_autoindex_character_bank_armor_receipts_1","bank_armor_insert_guard","bank_armor_update_guard"}
REQUIRED={"storage_owned_armor_bank_0067","storage_owned_armor_bank_adapter_0067","storage_owned_armor_bank_service_0067","bank_items_repository","bank_service","armor_slots","owned_armor_transfer","owned_bag_projection","owned_bank_trade_projection","sqlite_armor_production_adapter","database","config","recovered_account_login","recovered_character_repository"}
def qualify():
    require(sha(CANDIDATE)==PIN,"Candidate differs")
    c=read(CONTRACT);require(c["candidate_sha256"]==PIN,"Runtime contract differs")
    for path,digest in c["source_sha256"].items():require(sha(prior.checked_path(path))==digest,"Runtime changed: "+path)
    prior.ctest_gate(LOG,14,REQUIRED)
    r=read(RUN);require(r.get("accepted") is True and r.get("runner_exit")==0 and r["candidate_sha256"]==PIN,"Actual native UI receipt failed")
    for k in ("source_files_unchanged","candidate_unchanged","all_owned_processes_closed","private_files_unchanged","all_private_images_closed","bank_swap_harness_unchanged","runtime20_unchanged","frozen_files_unchanged","protected_processes_preserved","desktop_owner_unchanged","exclusive2598_released"):
        require(r.get(k) is True,"Actual native guard absent: "+k)
    require(r["runtime20_before"]==r["runtime20_after"]==c["source_sha256"],"Native UI not same runtime24")
    require(r["bank_swap_harness_sha256"]==sha(HARNESS),"Native harness changed")
    require(r["before"]==r["after"] and r["frozen_files_before"]==r["frozen_files_after"],"Protected native files changed")
    for path,digest in r["frozen_files_after"].items():require(sha(Path(path))==digest,"Native evidence changed: "+path)
    require(r["owned_pid_terminal"] and all(v["pid_exists"] is False for v in r["owned_pid_terminal"].values()),"Native cleanup incomplete")
    u=r["ui"];require(u["accepted"] is True and u["desktop_unchanged"] and u["all_clients_closed"],"UI scope failed")
    require([(n["identity"],n["language"]) for n in u["final"]["native"]]==[(4,950),(5,936)],"TW CP950/CP936 owner coverage absent")
    armor=[e for e in u["events"] if e["operation"]=="armor_committed"]
    med=[e for e in u["events"] if e["operation"] in ("0x63","0x64","0x65")]
    require(len(armor)==12 and len(med)==20,"Actual mutation coverage differs")
    for owner in (4,5):
        a=[e for e in armor if e["identity"]==owner]
        require([(e["opcode"],e["source"],e["destination"]) for e in a]==[(99,0,4),(99,1,5),(101,4,5),(101,4,5),(100,4,0),(100,5,1)] and all(e["full20_verified"] is True for e in a),"Armor per-owner full20 coverage differs")
        require(sum(e["after"]["native"]["identity"]==owner for e in med)==10,"MED owner coverage differs")
    require(len(u["final"]["db"]["receipts"])==20,"MED durable receipt coverage differs")
    require(sha(managed.CLIENT)==c["client_sha256"],"Production client changed")
    require(read(frozen.BASELINE)["current_client_accepted"] is True and frozen.hashes()==read(frozen.BASELINE)["source_sha256"],"Frozen accepted chat baseline changed")
    return {"candidate_sha256":PIN,"client_sha256":c["client_sha256"],"source_sha256":c["source_sha256"],"native_run_sha256":sha(RUN),"harness_sha256":sha(HARNESS),"ctest_sha256":sha(LOG),"armor_commits":12,"med_commits":20,"ctest_passed":14}
def schema_gate(before,after):
    require([h[0] for h in before["history"]]==list(range(1,43)),"Stage requires exact installed schema42")
    require(after["pragmas"]==before["pragmas"],"Clone pragmas changed")
    require(set(after["tables"])==set(before["tables"])|NEW_TABLES,"Unexpected clone table changes")
    require([s for s in after["schema"] if s[1] not in NEW_OBJECTS]==before["schema"],"Existing schema objects changed")
    require({s[1] for s in after["schema"] if s[1] in NEW_OBJECTS}==NEW_OBJECTS,"Missing exact43 objects")
    for name,state in before["tables"].items():
        if name!="schema_migrations":require(after["tables"][name]==state,"Saved rows changed: "+name)
    for name in NEW_TABLES:require(after["tables"][name]=={"rows":0,"sha256":hashlib.sha256(b"").hexdigest()},"Custody grant during stage")
    require(after["history"][:-1]==before["history"] and len(after["history"])==43 and after["history"][-1][:2]==[43,"owned_armor_bank_instances"],"History outside43 changed")
def stage():
    gate=qualify();require(not STAGE.exists(),"Stage already exists; inspect it")
    config=read(managed.CONFIG);require(config["world"].get("owned_armor_transfers")=={"enabled":True},"Existing armor transport required")
    require(config["world"].get("owned_armor_bank") in (None,{"enabled":False}),"Bank already enabled or unqualified config")
    database=Path(config["database"]["path"]);before=snapshots.capture(database);prior.source_catalog_gate(database)
    STAGE.mkdir(parents=True)
    managed.backup(database,STAGE/"accounts.before.db")
    require(snapshots.capture(STAGE/"accounts.before.db")==before,"Live save changed while making consistent backup; restage")
    managed.backup(STAGE/"accounts.before.db",STAGE/"town-diagnostic-accounts.db")
    after_config=copy.deepcopy(config);after_config["world"]["owned_armor_bank"]={"enabled":True}
    clone=copy.deepcopy(after_config);clone["database"]["path"]=str(STAGE/"town-diagnostic-accounts.db");clone["logging"]["file"]=str(STAGE/"stage.log")
    with socket.socket() as reserve:reserve.bind(("127.0.0.1",0));port=reserve.getsockname()[1]
    clone["server"].update(host="127.0.0.1",port=port,character_port=0)
    write(STAGE/"stage-config.json",clone);write(STAGE/"server-config.after.json",after_config)
    env=os.environ.copy();env["GOD2_LOG_FILE_ONLY"]="1";env.pop("GOD2_NATIVE_WORLD_RECORDS_LAB",None)
    for args,name in ((["--migrate-only"],"migration.log"),(["--run-for","1"],"startup.log")):
        with (STAGE/name).open("wb") as log:subprocess.run([str(CANDIDATE),"--config",str(STAGE/"stage-config.json"),*args],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=40,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    require("OWNED_ARMOR_BANK_ENABLED" in (STAGE/"stage.log").read_text("utf-8"),"Application did not activate clone route")
    after=snapshots.capture(STAGE/"town-diagnostic-accounts.db");schema_gate(before,after);prior.source_catalog_gate(STAGE/"town-diagnostic-accounts.db")
    require(read(managed.CONFIG)==config,"Formal config changed during clone stage")
    shutil.copy2(CANDIDATE,STAGE/"god2-server.candidate.exe");shutil.copy2(managed.ACTIVE,STAGE/"god2-server.before.exe");shutil.copy2(managed.CONFIG,STAGE/"server-config.before.json")
    write(STAGE/"save-before.json",before);write(STAGE/"save-stage.json",after)
    result=dict(gate,state="CLONE_STAGED_NOT_INSTALLED",database=str(database),production_executable_sha256=sha(managed.ACTIVE),config_before_sha256=sha(managed.CONFIG),config_after_sha256=sha(STAGE/"server-config.after.json"),added_tables=sorted(NEW_TABLES),saved_rows_changed=0,grants=0)
    write(STAGE/"release.json",result);return result
def apply():
    gate=qualify();info=read(STAGE/"release.json");require(info["state"]=="CLONE_STAGED_NOT_INSTALLED","Exact staged release required")
    require(all(info[k]==v for k,v in gate.items()),"Qualification changed after stage")
    require(sha(managed.ACTIVE)==info["production_executable_sha256"] and sha(managed.CONFIG)==info["config_before_sha256"] and sha(managed.CLIENT)==info["client_sha256"],"Managed files changed since stage")
    require(sha(STAGE/"god2-server.candidate.exe")==PIN and sha(STAGE/"server-config.after.json")==info["config_after_sha256"],"Staged files changed")
    before_config=read(managed.CONFIG);expected=copy.deepcopy(before_config);expected["world"]["owned_armor_bank"]={"enabled":True}
    require(read(STAGE/"server-config.after.json")==expected,"Config changed outside qualified bank flag")
    database=Path(info["database"]);before=read(STAGE/"save-before.json");require(snapshots.capture(database)==before,"Save changed; restage required")
    pid=managed.listener() # Existing managed gate requires no established clients.
    require(prior.formal_process_proof(pid)["pid"]==pid,"Actual formal process differs")
    managed.backup(database,STAGE/"accounts.at-install.db")
    require(snapshots.capture(STAGE/"accounts.at-install.db")==before and snapshots.capture(database)==before,"Fresh backup differs")
    prior.common.lifecycle.stop_managed_and_wait(pid)
    if snapshots.capture(database)!=before:
        managed.start();raise RuntimeError("Save changed while stopping; no installation attempted")
    try:
        shutil.copy2(STAGE/"god2-server.candidate.exe",managed.ACTIVE)
        shutil.copy2(STAGE/"server-config.after.json",managed.CONFIG)
        env=os.environ.copy();env["GOD2_LOG_FILE_ONLY"]="1";env.pop("GOD2_NATIVE_WORLD_RECORDS_LAB",None)
        with (STAGE/"formal-migration.log").open("wb") as log:subprocess.run([str(managed.ACTIVE),"--config",str(managed.CONFIG),"--migrate-only"],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=40,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        after=snapshots.capture(database);schema_gate(before,after);template=read(STAGE/"save-stage.json")
        require(after["schema"]==template["schema"] and after["history"][-1][:3]==template["history"][-1][:3],"Installed schema differs from accepted clone")
        prior.source_catalog_gate(database)
        require(sha(managed.ACTIVE)==PIN and sha(managed.CONFIG)==info["config_after_sha256"] and sha(managed.CLIENT)==info["client_sha256"],"Installed files differ")
        formal_log=Path(expected["logging"]["file"]);log_before=formal_log.read_bytes() if formal_log.exists() else b""
        managed.start()
        managed.powershell("$deadline=(Get-Date).AddSeconds(20); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed listener not ready'}")
        new_pid=managed.listener();process=prior.formal_process_proof(new_pid)
        startup=prior.startup_log_gate(formal_log,log_before)
        appended=formal_log.read_bytes()[len(log_before):].decode("utf-8",errors="replace")
        require("OWNED_ARMOR_BANK_ENABLED CUSTOM-0067 full_instance no_grants no_formula" in appended,"Actual formal bank route did not activate")
        actual=snapshots.capture(database);schema_gate(before,actual)
        require(actual["schema"]==template["schema"],"Formal startup altered staged schema")
        prior.source_catalog_gate(database)
        proof={"process":process,"prior_startup":startup,"bank_marker":[line for line in appended.splitlines() if "OWNED_ARMOR_BANK_ENABLED" in line]}
        write(STAGE/"formal-startup-proof.json",proof);write(STAGE/"save-installed.json",actual)
        info.update(state="INSTALLED",server_pid=new_pid,installed_at=prior.common.now(),saved_rows_changed=0,grants=0,formal_startup_proof_sha256=sha(STAGE/"formal-startup-proof.json"))
        write(STAGE/"release.json",info);return info
    except BaseException as error:
        info.update(state="REPAIR_REQUIRED_SCHEMA43_COMPATIBLE_CANDIDATE_RETAINED",error=str(error),database_restored=False,old_executable_restored=False)
        write(STAGE/"release.json",info)
        if sha(managed.ACTIVE)==PIN:
            try:managed.start()
            except Exception:pass
        raise
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=("qualify","stage","apply"));args=parser.parse_args();r={"qualify":qualify,"stage":stage,"apply":apply}[args.mode]();print(json.dumps({k:r.get(k) for k in ("state","candidate_sha256","armor_commits","med_commits","saved_rows_changed","grants")}))
