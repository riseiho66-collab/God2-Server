"""CUSTOM-0071 release helper with frozen build/native/current-client gates.

Fail closed unless the exact root-approved candidate/source/test/UI proofs match.
Only schema46->47 empty destruction receipts and one opt-in configuration key
are permitted. Never restore saves, downgrade schema or run925f after schema47.
Native27 cannot establish original bind, acquisition or ground-drop authority.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import struct

from tools.operations import native_armor_transfer_release_20261002 as prior
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import verify_frozen_chat_20260927 as frozen
from tools.operations import stage_owned_mixed_bank_v06_20261003 as accepted0070

ROOT=prior.ROOT
managed=prior.managed
require=prior.require
sha=prior.sha
read=prior.read
write=prior.write
OLD_PIN="925f15144c779e62183ecc69195c555576eaa8a318522e23ec97bb87d018daae"
DESIGN="CUSTOM-0071"
NATIVE=ROOT/"artifacts/research/current-discard-instances-20261003/run03/native.json"
NATIVE_PIN="6965aba323e3c1a52b68fc4acd8cbeba1b68c7c572dda4eeaf9cb53a1e95218e"
NATIVE_TOOL=ROOT/"tools/strike_lab/current_discard_instances_20261003.py"
NATIVE_TOOL_PIN="8caec0ce92a9d5d122bc745efc99b4ec67009e86a74f198c2120748ca4b14380"
HARNESS=ROOT/"tools/strike_lab/private_owned_instance_discard_20261003.py"
RUN=ROOT/"artifacts/playtests/private-native-blackbox-owned-instance-discard-20261003-01/run-result.json"
STAGE=ROOT/"artifacts/releases/owned-instance-discard-20261003/clone-stage"
SCHEMA_SOURCE=ROOT/"src/db/SqliteOwnedInstanceDiscardRepository.cpp"

# Exact root-built runtime/test closure and completed native UI artifacts.
# Every changed digest or incomplete proof is a refusal, never a bypass.
CANDIDATE=ROOT/'build-owned-instance-discard-20261003/Release/god2-server.exe'
PIN='f918809abcf77f1b296bdd174c7bb39071e1e41f217638a509dba6a7f5c8bcc4'
CONTRACT=ROOT/'artifacts/research/owned-instance-discard-0071/candidate-20261003/contract.json'
CONTRACT_PIN='00e03195737db7e74e273b405a4a0a60a23ea3e823af26df63190eb0ed3adb8c'
SOURCE_PINS={'src/core/Application.cpp': '2090ef5204bad10032ed8dfba2de2b094322820a4e61530236bf270f90e44511', 'src/core/Config.cpp': 'a6711a5ed1ceb440e7f60d16169a2f0ad929193b51223f043b09565d9471ee58', 'src/core/Config.h': 'eef4d253d3ac65d345cb2ca9e56677a4852142ab51a0cb95f269994ee7a13e84', 'src/db/Migration.cpp': '836a5222891fce4cb0c72219681487a00e57d246ce743bb23722e34bfe282f06', 'src/db/SqliteArmorSlotRepository.cpp': '1057f51348a088059ed7c0cca05ec99bf144cc1d6bcdd295c636d98b8ead99d7', 'src/db/SqliteArmorSlotRepository.h': '959837aaa044686f3af27e82f913b7edda42389c6478255a10559e09c12bea71', 'src/db/SqliteBankItemsRepository.cpp': '25379fac68277c575a2a7291eb96d246769a67941b560d2440b2cb735f49dab0', 'src/db/SqliteBankItemsRepository.h': '1f05a636b2d59d25bd04919082c0374fe02ecbf044852625d6e8f24dc9cc0ed9', 'src/db/SqliteDatabase.cpp': '3272dd335d0daaeba484e676245c7e2421e0aacbec9cfd2fdac4e859e8ebed4b', 'src/db/SqliteDatabase.h': '2680cb7c7836d04a5c63c7564995d80b0bcaae91f2a17fc2d8e2548229e83400', 'src/db/SqliteInventoryDiscard.cpp': '843b309c2e7d701568ed45073fa327af30c0d9687feed156dc33862c5cb4e910', 'src/db/SqliteOwnedArmorBankRepository.cpp': 'be66307687c2dd27526f4020e1ee7eaca456a99096fa83ea38e33bb58430f089', 'src/db/SqliteOwnedArmorBankRepository.h': '589b211f8760c5bdd990f7b3084de39bee12b7256b7efa46db3fff5202a6e1fe', 'src/db/SqliteOwnedForeignBankRepository.cpp': '5bf88edefc32e1506e2636440aa0e1183f4717583b9d097675e642219d1513d0', 'src/db/SqliteOwnedForeignBankRepository.h': 'a8fba8714ad5e817287697044902c23d156b8b8c0d401a68108e56511aaac504', 'src/db/SqliteOwnedInstanceDiscardRepository.cpp': 'c480019be772d5fe26240c9ddae38bc31bf9d3ca4f37f64797d155aa8d1332fb', 'src/db/SqliteOwnedInstanceDiscardRepository.h': '4d7d158b3a166c36fcf8eb58ab110f02d097f1811718268336131b3c911816d4', 'src/db/SqliteOwnedInstanceTradeRepository.cpp': '46d2b49dc100eb9dc5826670860a8c8668e4a04710d563af587daa75f49e1efc', 'src/db/SqliteOwnedInstanceTradeRepository.h': '4417be545c054944b6f3f770b6e18f78290cb5b5850a7af30865c3522d9d812a', 'src/db/SqliteOwnedMixedBankRepository.cpp': 'ecfee2f8e93bd17fdab6d6cc55680418c41f5a8854ccfff5e85c90811d1927fe', 'src/db/SqliteOwnedMixedBankRepository.h': 'cdabafe60497887ec86fd1b49079437a7e39d17f022a05fc927ca6f7fe03c0ee', 'src/db/SqliteTradeRepository.cpp': 'fa679894382c0a6b1261f34aa4d15a834ebc587a6b60761b0dac5e6407245cf5', 'src/db/SqliteTradeRepository.h': 'a6047f9b77e1e49692e90fa309c7a573ef6fb17422d69d170d9feb1fe0ed9b26', 'src/handlers/InventoryDiscardService.h': '34c88fed3512a103336a752557c73b316c60c248e729bd225f95730cfe2f7b6e', 'src/handlers/OwnedArmorBankService.cpp': '3a2133b281979841a2d3bd9e071dd310c462980463318a9096ab1e93d1ff9fd6', 'src/handlers/OwnedArmorBankService.h': '3a80ddb8514da114587f3617820e3d2af21d7793b612b0a7a37c8a79f8e39751', 'src/handlers/OwnedArmorTransferService.h': '64d7bd3eb0a08ec126d02dfc1f83e9d2e010a67ed8a3e6ec2df2c6ba057a52c7', 'src/handlers/OwnedBagMutationProof.h': '5e5a7d4df9518883609bfe8003ae3e7a2dbf58058d47a7004daa4b8d881b086f', 'src/handlers/OwnedBagProjectionService.h': 'e011acd7a60b45b2acecd37df1c6bb44b5d1127308b42966f6a343800f49f7d7', 'src/handlers/OwnedForeignBankService.cpp': '5363a9dbcdd71b4e2d4cef333d6d88157690c9d6409139605ee7fa083d29d9dd', 'src/handlers/OwnedForeignBankService.h': '03da43fda4de6469bd3512a6fc77081d60872bc83634811245ce3adf84bb43f6', 'src/handlers/OwnedInstanceDiscardService.cpp': '237ee9e4083a0798793ae482691be7e81ea62e9fdb179f3d37a4831c41353502', 'src/handlers/OwnedInstanceDiscardService.h': 'ab2e1ad95000186923d6cfbd85f0e757a8dbec8f18b6288d166f8e4791adf312', 'src/handlers/OwnedInstanceTradeService.cpp': 'b9ae732fcbd09e789844f1749625b40528753a1a4406c53cdf393b38d0e023b9', 'src/handlers/OwnedInstanceTradeService.h': '94eaf7767577afd462b5e04b6ff5d1f9c3be63e54fe31ffce9890f981f5f1cda', 'src/handlers/OwnedMixedBankService.cpp': '190ff3d13e1161dfd8be691197861835107b6da897b7220c287185ade88d0b42', 'src/handlers/OwnedMixedBankService.h': 'a18cf3ee38749ba869abd8e92541c96d37487124af95d8fffef96e6990b20b5f', 'src/handlers/RecoveredBankItemsService.cpp': '482eb25697e9ebd1b24d1ee3c51381662667207c4acb19377562e4f0dee61de1', 'src/handlers/RecoveredBankItemsService.h': 'bcb21b420f0bebb4e699954190e23ba47087022de7315ddace828fee85d5f154', 'src/handlers/RecoveredTradeService.cpp': '7e839f94b1e15d7d5604625ec9e725c7ee02e3a8c38d2d589fc69d2ea149d0b3', 'src/handlers/RecoveredTradeService.h': '1785d166d883623984aba70db8ef91bfef2f1c2da91cd789325f2dc5a2985bd3', 'src/protocol/RecoveredArmorSourceInstance.h': 'd27c50d8f1e41cc41fee0bd116cb6a3354e091b41a5ce65a71ef3fcc44a96239', 'src/protocol/RecoveredInventoryDiscard.h': 'b9e7b80513adb900c929044ec0ec8c0de27e1ece29de650ff36afe7a51d040b3', 'src/protocol/RecoveredInventoryProjection.h': 'c120a193477667a9fb7e73cd54baa07139c136e5a27243596cbf0120c1de3460', 'src/protocol/RecoveredWorldFrame.h': 'b602ba7a6c86d4cff700e4a65123e8dbdec64b1a2b60b28ae21dd3bf76523d1f'}
SUPPORT_PINS={'CMakeLists.txt': 'f5e36340e3d336d945c2bab673932c3a007b7082328deb895baec04f4073ab3c', 'artifacts/research/current-discard-instances-20261003/run03/native.json': '6965aba323e3c1a52b68fc4acd8cbeba1b68c7c572dda4eeaf9cb53a1e95218e', 'artifacts/research/native-armor-20261002/records.json': '488d82e13b3e427f35c7372b2cfd2e1e6a28b49ca62adca7a68ee2a6fb02f3bd', 'artifacts/research/native-weapons-20260926/records.json': 'c42839db91f3bd8ff377fa7995cb0f421c3fabb961eb79f68ae3e9fd97ff18b3', 'artifacts/research/owned-instance-trade-0069/native-med02-cache.json': 'a0aa6832340d5b48b0943572e4fd18514af21775101f4162fe6fc72d085bfd1e', 'tests/CMakeLists.txt': '1df740d8c07c273ca5954dbf6eed00bb991469d5ae71d29f0f0833dbeb986996', 'tools/strike_lab/current_discard_instances_20261003.py': '8caec0ce92a9d5d122bc745efc99b4ec67009e86a74f198c2120748ca4b14380'}
TEST_PINS={'tests/storage_owned_armor_bank_0067.cpp': 'fa6babbeb7562a24cfa468772e463cf386a5fd0c826101257c15daeefeaf3791', 'tests/storage_owned_armor_bank_adapter_0067.cpp': 'aa4e35c36dee025a45485885f0fa7e9c1ad70dd381bf75906150eb6ae5a75f26', 'tests/storage_owned_armor_bank_service_0067.cpp': '87d32a60afa66cddba25ac12ebb89a8798369f6d681c53698440b0f912c7c500', 'tests/storage_owned_foreign_bank_0068.cpp': 'f12ec6729d5752b05a9b5ca314b9cec864ec827ed23cea7cbdf2341c572546af', 'tests/storage_owned_foreign_bank_adapter_0068.cpp': '6e70e3be25038504189108b1834175673fe7fc7a988f3c9b4d366b75f72ce58f', 'tests/storage_owned_foreign_bank_service_0068.cpp': '86585450173940a2b56733d13b24b79e535d3929795d5b0bf2a9b8c4a7af6412', 'tests/storage_owned_instance_discard_0071.cpp': '22d72b69129d6244d814cac0e5de9708ac99a775dbee6c058aff509ce28a17a2', 'tests/storage_owned_instance_discard_adapter_0071.cpp': 'cfe47955e388b3eb6b6d5b4cdd68d0869cdd6c8fb20382536f4dc8684be9c793', 'tests/storage_owned_instance_discard_service_0071.cpp': '4c6bd4ce404c0dd0b0396dcf2a381b40cbaec6d85e355323dc2ad6f3d5e8ca4c', 'tests/storage_owned_instance_trade_0069.cpp': '7ecd894c4a6c4fe808869d8e5b88e3decf57579527f358e5cd8713f11eb89e3f', 'tests/storage_owned_instance_trade_adapter_0069.cpp': '2c595e7ea82c41cffe580662a25f422a61f1d76408ab5cf70daca393d871b13c', 'tests/storage_owned_instance_trade_service_0069.cpp': '567f01aec91030b202e5053db801ccb377cf561ea80196cbd3f7601069cfd172', 'tests/storage_owned_mixed_bank_0070.cpp': '85fa38ee4ab88003433065908160df04656ff4282f446110e20cbf879c57c1d5', 'tests/storage_owned_mixed_bank_adapter_0070.cpp': 'e5ea148bfb863e7dcda693f5e71e3bd8a255e1791ab723888fa8985e8728d1f2', 'tests/storage_owned_mixed_bank_service_0070.cpp': '3981dd4cce3edfab8130d41c7b3fa32bd26d75391a325ea2c27d50ff96513e42', 'tests/test_armor_slots.cpp': '92158c4bdb696cba73bbd3f9a936d6b70aff892d4cf0dcb0e1538aadd0fcd594', 'tests/test_bank_items_repository.cpp': '3eed8f259cec625a8c193ffed9658bb20ec31f4d6e9c91cda878a861247d2caa', 'tests/test_bank_service.cpp': '587bd39fbe129d35f60b36c7bf68d909142740a4d077b93b4e2bf9a2c8212f0b', 'tests/test_config.cpp': '7c8b33c8bf84e4b0d3982b81fabde7b26be217be61f289ba7f1c59ff7816522b', 'tests/test_database.cpp': 'a14386489f168b16ff6e784d6b9ffdccf5bddfc9ef4b2211a539125dcab2113c', 'tests/test_inventory_discard.cpp': 'c9a7c23f865766a656fc8baa6bb2501dfcc4afe54b38f54e89c64e3bdf07b6ea', 'tests/test_owned_armor_transfer.cpp': '1e74c63f17beffee0037ac4909dfa40199a7c280cedcb029dcf9924f4cfb324b', 'tests/test_owned_bag_projection.cpp': '57a913bb2798d905740b811cbe0f10193c1d8b37b630df577d1cf01165f3ff06', 'tests/test_owned_bank_trade_projection.cpp': 'fd74b355966351e92374a473a9903e0b0e28ec2f36f29c2463d9d10906c82c4c', 'tests/test_owned_weapon_transfer.cpp': 'e1ffe381b64177cca0c95d33c8e6ec2b5c28ab95856fb3e4be8c5d2325f16416', 'tests/test_recovered_account_login.cpp': '9c9d83545eb6fde22589df3fa674d8e7e7fa02a3181be675e65a813ef7b4c79b', 'tests/test_recovered_character_repository.cpp': 'cac9f64747519bdb8675f2228d554815632e5946a73cff3414ce1a0c83d0b751', 'tests/test_recovered_trade.cpp': 'b2d7f5f35f4514ffb7dda52182cde2b962f48a7aaab3f525f7961d2e60ecc455', 'tests/test_sqlite_armor_production_adapter.cpp': 'b4e9d49b83360db381f5a138d15bd4361050427695e8a529669d0ac91641d0f2', 'tests/test_trade_repository.cpp': 'b6a5a8be5150f51895f43ccda42e7f77f0bdd855d780f701b8fca9fc448f0f83', 'tests/test_trade_service.cpp': '3be70239adc58f8a6e682a2dd12f20261e3b296d7a335da20ec2dbb134e18a18', 'tests/test_weapon_slots.cpp': 'd538b9af726fa763e591dccf6a6713bcbd851727511dea4227f0e8e597a78c32'}
TEST_NAMES={'bank_items_repository', 'recovered_trade', 'armor_slots', 'trade_service', 'storage_owned_mixed_bank_adapter_0070', 'storage_owned_instance_discard_service_0071', 'storage_owned_mixed_bank_0070', 'recovered_character_repository', 'storage_owned_foreign_bank_0068', 'storage_owned_instance_discard_adapter_0071', 'storage_owned_instance_trade_adapter_0069', 'storage_owned_armor_bank_adapter_0067', 'storage_owned_mixed_bank_service_0070', 'owned_bank_trade_projection', 'trade_repository', 'storage_owned_foreign_bank_service_0068', 'storage_owned_armor_bank_service_0067', 'bank_service', 'storage_owned_instance_trade_0069', 'weapon_slots', 'storage_owned_instance_trade_service_0069', 'sqlite_armor_production_adapter', 'recovered_account_login', 'storage_owned_foreign_bank_adapter_0068', 'config', 'owned_armor_transfer', 'database', 'owned_weapon_transfer', 'owned_bag_projection', 'inventory_discard', 'storage_owned_instance_discard_0071', 'storage_owned_armor_bank_0067'}
CTEST_LOG=ROOT/'artifacts/research/owned-instance-discard-0071/root-ctest-02.log'
CTEST_LOG_PIN='69a1979369c7114e347919f09304ecb29c5493b8f27397c50189a2682fe8edab'
BUILD_LOG=ROOT/'artifacts/research/owned-instance-discard-0071/root-build-05.log'
BUILD_LOG_PIN='fe30ce2580ae43a0a053bd9035106600074ab1038e830456967eb738ad512d43'
HARNESS_PIN='1e6f83fac7a914ce3f2e1c11d1d2683615d3ee2f4293d1cfb67cf83c20b990b2'
PREDECESSOR_RELEASE=ROOT/'artifacts/releases/owned-mixed-bank-20261003/clone-stage/release.json'
PREDECESSOR_RELEASE_PIN='823170f3e4370a0f42174cd18993584b0b5eb6b47c18d8afda2fd837f4be00c3'
NEW_TABLES={"character_owned_instance_discard_receipts"}
NEW_OBJECTS=NEW_TABLES|{"sqlite_autoindex_character_owned_instance_discard_receipts_1"}
SCHEMA_SQL_PIN='ac96338978a9a0b688be0bff8f79b59208928fff9f0960bf0c2ac4efa0d4b41f'
MIGRATION_NAME="owned_instance_discard"
EVENT_METADATA_KEYS=('operation', 'identity', 'account', 'language', 'opcode', 'source', 'quantity', 'kind', 'representative', 'family', 'charges', 'confirmation_enabled', 'confirmation_action')
UI_GATE_FINAL=True
RUN_PIN="2ace3e5766aff6c5672f19beb9c87868ecb15adccc94160ef46b551db8948508"
UI_PIN="3d5bd7765d425eeee0164850decf9332a19b77d3adf7573fe8a30d13ce3a2a86"
FIXTURE_PIN="bc7549650e1237ea7be53547ca3d45a1c90d316372a48aee161e8b5df53d37df"
LOG_PIN="6d8dfa85b0074c607175d51d6f2dbbb6756de41f465a305f16f571012ec10f61"
VALIDATION=ROOT/"artifacts/research/owned-instance-discard-0071/root-validation-02.json"
VALIDATION_PIN="092ec618e9e09c6049b85cfdfadc375f7e6f75f6bdbd31f1695f1c18700d7cda"
PREPARATION=ROOT/"artifacts/research/owned-instance-discard-0071/private-native-blackbox-owned-instance-discard-preparation-20261003-02/root-preparation-proof.json"
PREPARATION_PIN="ff65256f4c4c85c32f1f5f547f87f720f19a31f437d2bb13298e4dbe8826c9c7"
LEDGER="character_owned_instance_discard_receipts"
OVERLAYS=("character_armor_slot_metadata","character_weapon_slot_metadata","character_teleport_gem_metadata")
OWNER_CONTRACT={6:(5,950),7:(6,936)}
REPRESENTATIVES={"EQU_HEAD":(1201,2,0),"EQU_BODY":(1001,2,0),"EQU_HAND":(1501,2,0),"EQU_SHOE":(1601,2,0),
    "TEQ_HEAD":(20201,26,0),"TEQ_BODY":(20001,26,0),"TEQ_HAND":(20501,26,0),"TEQ_SHOE":(20601,26,0),
    "WPN":(1,1,0),"TWP":(19001,25,0),"GEM1":(16055,8,1),"GEM10":(16055,8,10)}
SOURCE_SHA="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731"
CLIENT_SHA="c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575"
WEAPON_CLIENT_SHA="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98"
BLOB_COLUMNS={'accounts': [], 'battle_checkpoints': [], 'battle_reservations': [], 'battle_settlements': [], 'character_armor_slot_metadata': [2], 'character_bank_armor_metadata': [2], 'character_bank_armor_receipts': [], 'character_bank_balances': [], 'character_bank_foreign_metadata': [3], 'character_bank_foreign_receipts': [], 'character_bank_item_receipts': [], 'character_bank_item_slots': [], 'character_bank_mixed_receipts': [], 'character_bank_receipts': [], 'character_daily_quest_lists': [1], 'character_deities': [2, 3, 4], 'character_deity_selection': [], 'character_experience': [], 'character_fruit_quest_balances': [], 'character_fruit_quest_progress': [], 'character_owned_instance_discard_receipts': [8], 'character_owned_instance_trade_receipts': [], 'character_pet2_slots': [2, 3], 'character_player_appearance_snapshots': [1, 2], 'character_quest_journals': [1], 'character_resources': [], 'character_role_auxiliary_snapshots': [1], 'character_role_snapshots': [1], 'character_role_text': [1], 'character_teleport_gem_metadata': [2], 'character_trade_receipts': [], 'character_trade_wallets': [], 'character_weapon_slot_metadata': [2], 'characters': [], 'diagnostic_inventory_slots': [], 'diagnostic_quest_journal': [1], 'diagnostic_town_guide_progress': [], 'diagnostic_town_guide_reward': [], 'recovered_characters': [3, 4], 'recovered_positions': []}


def digest_pin(value,label):
    require(isinstance(value,str) and re.fullmatch(r"[0-9a-f]{64}",value) is not None,label+" not frozen")


def reject_reparse_chain(path):
    require(path.is_absolute(),"Evidence path must be absolute")
    for component in (*reversed(path.parents),path):
        info=os.lstat(component)
        require(not component.is_symlink() and not (getattr(info,"st_file_attributes",0)&0x400),
            "Evidence path contains symlink/junction/reparse point: "+str(component))


def evidence_root():
    expected=ROOT/"artifacts/playtests/private-native-blackbox-owned-instance-discard-20261003-01"
    require(RUN.parent==expected and RUN.name=="run-result.json","Fixed new discard run01 path differs")
    reject_reparse_chain(expected)
    require(expected.resolve(strict=True)==expected,"Discard evidence root resolves outside fixed lexical root")
    reject_reparse_chain(RUN)
    return expected


def event_metadata(event):
    require(isinstance(EVENT_METADATA_KEYS,tuple) and len(EVENT_METADATA_KEYS)>0,"Actual event metadata contract not frozen")
    return {key:event[key] for key in EVENT_METADATA_KEYS if key in event}


def resolve_event(index,reference):
    require(isinstance(reference,dict) and isinstance(reference.get("evidence"),dict),"Event reference missing")
    evidence=reference["evidence"]
    require(set(evidence)=={"path","sha256","bytes"},"Unexpected event evidence fields")
    relative=f"ui-events/event-{index:06d}.json"
    require(evidence["path"]==relative and type(evidence["bytes"]) is int and evidence["bytes"]>0,"Contiguous event path/bytes differs")
    digest_pin(evidence["sha256"],"Event SHA256")
    root=evidence_root();path=root/relative
    reject_reparse_chain(path)
    require(path.resolve(strict=True)==root/relative,"Event escaped fixed discard evidence root")
    require(path.stat().st_size==evidence["bytes"],"Event byte count differs")
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):digest.update(chunk)
    require(digest.hexdigest()==evidence["sha256"],"Event SHA256 differs")
    with path.open("r",encoding="utf-8") as stream:event=json.load(stream)
    require(isinstance(event,dict) and {key:value for key,value in reference.items() if key!="evidence"}==event_metadata(event),
        "Event index metadata differs from whole payload")
    return event


def evidence_file(name,pin=None):
    require(name in ("ui-result.json","fixture.json","server.log"),"Unexpected whole evidence file")
    path=evidence_root()/name;reject_reparse_chain(path)
    require(path.resolve(strict=True)==path,"Whole evidence lexical path differs")
    if pin is not None:digest_pin(pin,name);require(sha(path)==pin,"Frozen whole evidence changed: "+name)
    return path


def state_digest(state):
    digest=hashlib.sha256()
    # Streaming avoids another whole-snapshot JSON allocation.
    for piece in json.JSONEncoder(ensure_ascii=False,separators=(",",":"),sort_keys=True).iterencode(state):
        digest.update(piece.encode("utf-8"))
    return digest.hexdigest()


def overlay(state,identity,slot):
    values=[(table,row) for table in OVERLAYS for row in state[table] if row[:2]==[identity,slot]]
    require(len(values)<=1,"Selected owned overlay conflict")
    return values[0] if values else (None,None)


def native_full(state,value,identity):
    native=value["native"] if "native" in value else value
    account,language=OWNER_CONTRACT[identity]
    require((native["identity"],native["account"],native["language"])==(identity,account,language) and
        type(native["pid"]) is int and native["pid"]>0,"Actual native owner/account/language/PID differs")
    scalar={row[1]:row for row in state["diagnostic_inventory_slots"] if row[0]==identity}
    require(set(scalar)==set(range(50)) and [cell["slot"] for cell in native["bag"]]==list(range(50)),"Full50 physical coverage differs")
    for cell in native["bag"]:
        slot=cell["slot"];row=scalar[slot];raw=bytes.fromhex(cell["raw24"])
        require(len(raw)==24 and int.from_bytes(raw[:4],"little")==row[3],"Native count differs from SQL")
        # Inactive cells may retain their old upper18; occupied survivors must
        # preserve the entire opaque20, including every equipment cell.
        if row[3]:
            table,metadata=overlay(state,identity,slot)
            body=bytes.fromhex(metadata[2]) if table else struct.pack("<H",row[2])+bytes(18)
            require(len(body)==20 and raw[4:]==body and int.from_bytes(raw[4:6],"little")==row[2],"Native occupied full20 differs")
    return native


def peripheral_state(state,identity):
    names=sorted(name for name in state if name!=LEDGER and
        (name.startswith(("character_","diagnostic_","recovered_","battle_")) or name in ("characters","accounts")))
    require(set(names)==set(BLOB_COLUMNS)-{LEDGER},"Exact peripheral schema/type closure differs")
    result=[]
    for name in names:
        records=[]
        for row in state[name]:
            if name in (*OVERLAYS,"diagnostic_inventory_slots") and row[0]==identity:continue
            values=[]
            for index,value in enumerate(row):
                if value is None:typed=[5,None]
                elif type(value) is int:typed=[1,value]
                elif type(value) is float:typed=[2,value]
                elif index in BLOB_COLUMNS[name]:typed=[4,list(bytes.fromhex(value))]
                else:require(type(value) is str,"Unexpected SQL observation type");typed=[3,list(value.encode("utf-8"))]
                values.append(typed)
            records.append(values)
        result.append([name,json.dumps(records,ensure_ascii=False,separators=(",",":"))])
    return json.dumps(result,ensure_ascii=False,separators=(",",":"))


def receipt_state(state,identity):
    account,_=OWNER_CONTRACT[identity]
    scalar={row[1]:row for row in state["diagnostic_inventory_slots"] if row[0]==identity}
    require(set(scalar)==set(range(50)),"Receipt full50 capacity differs")
    armor=[];weapons=[];gems=[]
    for table,target in ((OVERLAYS[0],armor),(OVERLAYS[1],weapons),(OVERLAYS[2],gems)):
        for row in state[table]:
            if row[0]!=identity:continue
            slot=row[1];body=list(bytes.fromhex(row[2]));require(len(body)==20,"Receipt overlay not20 bytes")
            cell=scalar[slot]
            if table==OVERLAYS[0]:
                require(row[6:]==[SOURCE_SHA,CLIENT_SHA,"CUSTOM-0066"],"Armor source/client/design changed")
                target.append([slot,cell[2],cell[3],row[3],body,row[4],row[5],True,SOURCE_SHA,CLIENT_SHA,"CUSTOM-0066"])
            else:target.append([slot,body,row[3],row[4],row[5],row[6],row[7] if table==OVERLAYS[1] else "",row[-1]])
    return [account,identity,[[scalar[slot][2],scalar[slot][3],scalar[slot][4],scalar[slot][5]] for slot in range(50)],
        sorted(armor),sorted(weapons),sorted(gems),peripheral_state(state,identity)]


def verify_mutation(event,typed):
    before=event["before"];after=event["after"];identity=event["identity"];slot=event["source"];quantity=event["quantity"]
    account,language=OWNER_CONTRACT[identity]
    require((event["account"],event["language"],event["opcode"])==(account,language,39) and
        type(slot) is int and 0<=slot<30 and type(quantity) is int and quantity>0,"Actual native27 identity/request differs")
    require(set(before)==set(after),"Discard changed table set")
    cells=[row for row in before["diagnostic_inventory_slots"] if row[:2]==[identity,slot]]
    require(len(cells)==1,"Selected scalar not unique");old=cells[0]
    require(0<quantity<=old[3] and old[4]>0 and old[5:]==[SOURCE_SHA,"CUSTOM-0015"],"Selected scalar authority differs")
    table,row=overlay(before,identity,slot)
    if typed:require(quantity==old[3]==1 and table is not None,"Typed27 must destroy one complete instance")
    else:require(table is None and old[2]==3107 and slot==24 and quantity in (2,5),"Old0061 MED regression differs")
    expected=dict(before);expected["diagnostic_inventory_slots"]=[list(value) if value[:2]==[identity,slot] else value for value in before["diagnostic_inventory_slots"]]
    changed=next(value for value in expected["diagnostic_inventory_slots"] if value[:2]==[identity,slot])
    changed[3]-=quantity;changed[2]=old[2] if changed[3] else 0;changed[4]+=1
    if changed[3]==0:
        for name in OVERLAYS:expected[name]=[value for value in before[name] if value[:2]!=[identity,slot]]
    for name in before:
        if name!=LEDGER:require(after[name]==expected[name],"Independent exact discard delta failed: "+name)
    require(event["independently_expected"]==expected,"Harness plan differs from independent full-row plan")
    old_native=native_full(before,event["native_before"],identity);new_native=native_full(after,event["native_after"],identity)
    require(bool(old_native["option449E"]&0x10) is event["confirmation_enabled"],"Actual native confirmation option differs from scenario")
    raw_before=bytes.fromhex(old_native["bag"][slot]["raw24"]);raw_after=bytes.fromhex(new_native["bag"][slot]["raw24"])
    require(int.from_bytes(raw_after[4:6],"little")==changed[2] and raw_before[6:]==raw_after[6:],"Actual41 key/count/upper18 preservation differs")
    for index in range(50):
        if index!=slot:require(old_native["bag"][index]==new_native["bag"][index],"Native surviving cell changed")
    if typed:
        history=before[LEDGER];new=after[LEDGER]
        require(len(new)==len(history)+1 and new[:-1]==history,"Old exact destruction receipt history changed")
        receipt=new[-1];require(len(receipt)==17 and receipt==event["actual_receipt"],"Actual appended receipt differs")
        digest_pin(receipt[0],"Actual receipt")
        kind=OVERLAYS.index(table)+1
        require(receipt[1:14]==[account,identity,39,old[2],slot,1,kind,row[2],row[4],row[5],row[6],row[7] if kind in(1,2) else "",row[-1]] and
            receipt[16]==DESIGN,"Exact destruction full20/provenance authority differs")
        first=receipt_state(before,identity);last=receipt_state(expected,identity)
        require(json.loads(receipt[14])==first and json.loads(receipt[15])==last and
            event["before_expected"]==first and event["after_expected"]==last,"Independent typed peripheral/receipt state differs")
        return receipt[0],old[2],bytes.fromhex(row[2])
    require(after[LEDGER]==before[LEDGER] and event["actual_receipt"] is None,"MED must preserve typed receipt ledger")
    return None,old[2],None


def ui_gate(result,sources):
    require(UI_GATE_FINAL is True,"Actual NEW discard run not yet approved/frozen")
    for pin,label in ((RUN_PIN,"Run"),(UI_PIN,"UI"),(FIXTURE_PIN,"Fixture"),(LOG_PIN,"Actual server log")):digest_pin(pin,label)
    require(sha(RUN)==RUN_PIN,"Actual approved terminal run changed")
    require(result["accepted"] is True and result["runner_exit"]==0 and result["candidate_sha256"]==PIN and
        result["discard_harness_sha256"]==HARNESS_PIN and result["scope"]=="OWNED_INSTANCE_DISCARD_TYPED27_TW_CN_CUSTOM_TEST_ONLY","Actual new UI terminal success absent")
    for key in ("discard_harness_unchanged","runtime_sources_unchanged","frozen_files_unchanged","protected_processes_preserved",
        "desktop_owner_unchanged","exclusive2598_released","source_files_unchanged","candidate_unchanged","all_owned_processes_closed",
        "private_files_unchanged","all_private_images_closed"):
        require(result.get(key) is True,"Actual terminal guard absent: "+key)
    require(result["runtime_sources_before"]==result["runtime_sources_after"]==sources and result["before"]==result["after"] and
        result["desktop_owner_before"]==result["desktop_owner_after"] and result["frozen_files_before"]==result["frozen_files_after"],"Independent source/desktop equality differs")
    for path,digest in result["frozen_files_after"].items():require(sha(Path(path))==digest,"Frozen evidence/source changed: "+path)
    for name in (HARNESS,CONTRACT,NATIVE_TOOL):require(result["frozen_files_after"].get(str(name))==sha(name),"Required frozen evidence missing")
    fixture=read(evidence_file("fixture.json",FIXTURE_PIN));ui=result["ui"]
    ui_path=evidence_file("ui-result.json",UI_PIN)
    require(read(ui_path)==ui,"Terminal/UI receipt disagrees")
    require(ui["accepted"] is True and ui["all_clients_closed"] is True and ui["desktop_unchanged"] is True and
        ui["rendered_pixels_tested"] is False and not ui.get("cleanup_errors"),"Actual native UI scope/cleanup differs")
    require(ui["qualified"]["current_client_sha256"]==CLIENT_SHA and len(ui["qualified"]["regions"])==12,"Frozen native code regions differ")
    require(ui["event_evidence_format"]=="LOSSLESS_SHA256_EVENT_FILES_V1" and isinstance(ui["events"],list),"Actual lossless event index missing")
    counts={"typed_discard":48,"confirmation_cancel":24,"med_discard":4,"equipped_refusal":2,"trade_refusal":2,"relogin_full50":1}
    require(ui["scenario_counts"]==fixture["expected_counts"]==counts and fixture["source_contract"]==sources and
        fixture["candidate_sha256"]==PIN and fixture["formal_owned_weapon_transfers_enabled"] is False,"Actual fixed coverage/config contract differs")
    owners=fixture["owners"]
    require({owner["identity"]:(owner["account"],owner["page"]) for owner in owners}==OWNER_CONTRACT,"Actual TW/CN owners differ")
    definitions={};coverage=set();cancels=set();med=set();refusals=set();receipts=set();seen={key:0 for key in counts};relogin=None
    for owner in owners:
        require(len(owner["phases"])==2,"Two fixture generations required")
        for phase,values in enumerate(owner["phases"]):
            require(len(values)==12 and {row["representative"] for row in values}==set(REPRESENTATIVES),"Actual typed twelve-category fixture differs")
            for definition in values:
                require((definition["item"],definition["family"],definition["charges"])==REPRESENTATIVES[definition["representative"]],"Representative contract changed")
                key=(owner["identity"],definition["source"]);require(key not in definitions,"Duplicate fixture physical source")
                definitions[key]=(phase,definition)
    current=state_digest(ui["initial"]["db"]);gestures={identity:None for identity in OWNER_CONTRACT};completed_gestures={identity:None for identity in OWNER_CONTRACT}
    require({native["identity"] for native in ui["initial"]["native"]}==set(OWNER_CONTRACT),"Both initial native owners missing")
    for native in ui["initial"]["native"]:native_full(ui["initial"]["db"],native,native["identity"])
    for index,reference in enumerate(ui["events"]):
        event=resolve_event(index,reference);operation=event["operation"]
        if operation=="native27_input_checkpoint":
            identity=event["identity"];raw=bytes.fromhex(event["control_raw100"]);hits=event["point_hits"];registered=event["registered_hit24"]
            require(len(raw)==100 and raw[0] and len(registered)==6 and registered[0] and hits and
                int.from_bytes(raw[8:10],"little",signed=True)==event["hit_id"] and
                (hits[0]["widget"],hits[0]["index"],hits[0]["hit_id"],hits[0]["rect"])==
                (event["widget"],event["index"],event["hit_id"],registered[1:5]),"Actual registered native top hit differs")
            require(event["queue_length"]<=0xa00 and len(bytes.fromhex(event["queue"]))==event["queue_length"],"Actual native queue bounds differ")
            phase=event["phase"]
            if phase in ("after_source_hover","source_pressed"):
                source=event["index"];body=bytes.fromhex(event["source_native24"])
                require(0<=source<50 and len(body)==24 and int.from_bytes(body[:4],"little")>0 and
                    int.from_bytes(body[4:6],"little")==event["source_cached_key"],"Actual cached/owned native source differs")
                if phase=="after_source_hover":gestures[identity]={"source":source,"body":event["source_native24"],"pressed":False,"target":False}
                else:
                    gesture=gestures[identity];require(gesture is not None and gesture["source"]==source and gesture["body"]==event["source_native24"],"Native source press lost hover qualification")
                    if (identity,source) in definitions or source==24:require(event["selected_bag_source"]==source,"Actual typed/MED native press not selected")
                    gesture["pressed"]=True
            elif phase=="before_delete_release":
                gesture=gestures[identity];require(event["index"]==56 and gesture is not None and gesture["pressed"],"Actual control56 release lacks qualified source press")
                gesture["target"]=True
        elif operation=="actual_native27_drag":
            identity=event["identity"];gesture=gestures[identity]
            require(gesture is not None and gesture["pressed"] and gesture["target"] and event["source"]==gesture["source"] and
                event["source_native24"]==gesture["body"] and event["normal_release_posted"] is True,"Actual native drag/release evidence differs")
            completed_gestures[identity]=gesture;gestures[identity]=None
        elif operation=="normal_option_toggle":
            identity=event["identity"];a=event["before"];b=event["after"]
            require((a["identity"],b["identity"])==(identity,identity) and a["bag"]==b["bag"] and
                bool(b["option449E"]&0x10) is event["confirmation_enabled"] and
                (a["option449E"]^b["option449E"]) in (0,0x10),"Native ordinary confirmation option changed unrelated state")
        if operation in counts:
            seen[operation]+=1;before=event["before"];after=event["after"]
            require(state_digest(before)==current,"Whole saved event chain differs")
            if operation in ("typed_discard","med_discard"):
                typed=operation=="typed_discard";receipt,item,body=verify_mutation(event,typed)
                identity=event["identity"];key=(identity,event["source"])
                gesture=completed_gestures[identity];require(gesture is not None and gesture["source"]==event["source"],"Actual commit lacks completed normal native gesture")
                completed_gestures[identity]=None
                if typed:
                    require(key in definitions and key not in coverage,"Unscheduled/duplicate typed source")
                    phase,definition=definitions[key];coverage.add(key)
                    require(item==definition["item"] and body.hex()==definition["logical20"] and
                        (event["representative"],event["family"],event["charges"])==(definition["representative"],definition["family"],definition["charges"]) and
                        event["confirmation_enabled"] is bool(phase) and event["confirmation_action"]==("accept" if phase else "none"),"Actual category/generation/confirmation differs")
                    require(receipt not in receipts,"Repeated destruction receipt");receipts.add(receipt)
                    if phase:require(key in cancels,"Confirmation accept requires prior real cancel")
                else:
                    pair=(identity,event["quantity"]);require(pair not in med,"Duplicate MED coverage");med.add(pair)
                    require(event["confirmation_enabled"] is False,"MED confirmation differs")
            elif operation=="relogin_full50":
                require(relogin is None and before==after and event["old_clients_closed"] is True,"True relogin mutated SQL or repeated")
                require(len(event["old_client_pids"])==len(event["new_client_pids"])==2 and len(set(event["old_client_pids"]+event["new_client_pids"]))==4,"True close/relaunch requires four distinct PIDs")
                require({value["identity"] for value in event["native"]}==set(OWNER_CONTRACT),"Both relogin owners missing")
                for value in event["native"]:native_full(after,value,value["identity"])
                relogin={key:event[key] for key in ("old_client_pids","new_client_pids")}
            else:
                identity=event["identity"];account,language=OWNER_CONTRACT[identity]
                gesture=completed_gestures[identity];require(gesture is not None and gesture["source"]==event["source"],"Cancel/local suppression lacks completed normal native gesture")
                completed_gestures[identity]=None
                require(before==after and (event["account"],event["language"],event["opcode"])==(account,language,39) and
                    event["no27_request_sent"] is True,"Cancel/local suppression changed SQL or emitted27")
                a=native_full(before,event["native_before"],identity);b=native_full(after,event["native_after"],identity)
                require(a["bag"]==b["bag"] and b["confirmation_widget"] is None,"Cancel/suppression changed native bag or left confirmation")
                if operation=="confirmation_cancel":
                    key=(identity,event["source"]);require(key in definitions and key not in cancels and key not in coverage,"Cancel source repeated/out of order")
                    phase,definition=definitions[key];pending=event["pending_confirmation"];cancels.add(key)
                    require(phase==1 and event["confirmation_enabled"] is True and event["confirmation_action"]=="cancel" and
                        bool(a["option449E"]&0x10) and pending["bag"]==a["bag"] and
                        [pending["confirmation_mode"],pending["confirmation_item"],pending["confirmation_source"],pending["confirmation_quantity"]]==[5,definition["item"],event["source"],1] and
                        pending["confirmation_widget"] is not None,"Actual native confirmation/cancel source differs")
                else:
                    pair=(identity,operation);require(pair not in refusals,"Duplicate refusal coverage");refusals.add(pair)
                    require(event["scope"]=="ORIGINAL_CLIENT_LOCAL_SUPPRESSION_NOT_SERVER_REJECTION" and event["source"]==(30 if operation=="equipped_refusal" else 27),"Local suppression scope/source differs")
                    if operation=="trade_refusal":require(a["trade_active"]!=0 and a["trade_widget"] is not None and a["peer"] in set(OWNER_CONTRACT)-{identity},"Actual native active peer trade missing")
            current=state_digest(after)
        del event
    require(seen==counts and coverage==set(definitions) and cancels=={key for key,(phase,_) in definitions.items() if phase==1} and
        med=={(identity,quantity) for identity in OWNER_CONTRACT for quantity in (2,5)} and len(receipts)==48 and relogin is not None,"Exact independent typed/cancel/MED/refusal/relogin coverage differs")
    require(current==state_digest(ui["final"]["db"]),"Final SQL differs from complete event chain")
    require({value["identity"] for value in ui["final"]["native"]}==set(OWNER_CONTRACT),"Both final native owners missing")
    require([value["native"]["pid"] for value in ui["final"]["native"]]==relogin["new_client_pids"],"Final native PIDs differ from relaunch")
    for value in ui["final"]["native"]:native_full(ui["final"]["db"],value,value["identity"])
    pids=[result["server_pid"],result["runner_pid"],*relogin["old_client_pids"],*relogin["new_client_pids"]]
    require(len(set(pids))==6 and ui["owned_client_pids"]==relogin["old_client_pids"]+relogin["new_client_pids"] and
        result["owned_pid_terminal"]=={str(pid):{"pid_exists":False} for pid in pids},"Actual six owned PID cleanup differs")
    log=evidence_file("server.log",LOG_PIN).read_bytes()
    matches=re.findall(rb"OWNED_INSTANCE_DISCARD_REQUEST session_id=(\d+) character_id=(\d+) committed=(true|false) rejected=(true|false) CUSTOM-0071",log)
    markers=[tuple(value.decode("ascii") for value in match) for match in matches]
    require(len(markers)==48 and all(row[2:]==("true","false") for row in markers) and
        {identity:sum(int(row[1])==identity for row in markers) for identity in OWNER_CONTRACT}=={identity:24 for identity in OWNER_CONTRACT},"Actual48 application commits differ")
    require(MARKER.encode("ascii") in log,"Actual private discard startup marker absent")
    return dict(typed_discard=48,confirmation_cancel=24,med_discard=4,local_equipped_suppressions=2,local_trade_suppressions=2,
        true_dual_owner_relogins=1,event_shards_verified=len(ui["events"]),independent_full_row_receipt_native_verified=True,
        ui_sha256=UI_PIN,fixture_sha256=FIXTURE_PIN,server_log_sha256=LOG_PIN)


def qualify():
    for value,label in ((PIN,"Candidate"),(CONTRACT_PIN,"Contract"),(HARNESS_PIN,"Harness"),
        (PREDECESSOR_RELEASE_PIN,"Accepted0070 release"),(CTEST_LOG_PIN,"CTest"),(BUILD_LOG_PIN,"Build"),
        (SCHEMA_SQL_PIN,"Schema47")):digest_pin(value,label)
    require(all(isinstance(path,Path) for path in (CANDIDATE,CONTRACT,CTEST_LOG,BUILD_LOG,PREDECESSOR_RELEASE)),"Exact gate paths not frozen")
    require(isinstance(SOURCE_PINS,dict) and SOURCE_PINS and isinstance(TEST_PINS,dict) and TEST_PINS and
        isinstance(SUPPORT_PINS,dict) and SUPPORT_PINS and isinstance(TEST_NAMES,set) and TEST_NAMES,"Exact source/test/support closure not frozen")
    require(sha(CANDIDATE)==PIN and sha(CONTRACT)==CONTRACT_PIN and sha(HARNESS)==HARNESS_PIN,"Immutable candidate/contract/harness changed")
    predecessor=read(PREDECESSOR_RELEASE)
    require(sha(PREDECESSOR_RELEASE)==PREDECESSOR_RELEASE_PIN and predecessor["state"]=="INSTALLED" and
        predecessor["candidate_sha256"]==OLD_PIN,"Actual accepted0070 installed receipt differs")
    contract=read(CONTRACT)
    require(contract["design"]==DESIGN and contract["candidate_sha256"]==PIN and contract["predecessor_sha256"]==OLD_PIN and
        prior.checked_path(contract["candidate_path"])==CANDIDATE and
        (contract["schema_before"],contract["schema_after"])==(46,47),"Exact discard runtime contract differs")
    for field,pins in (("source_sha256",SOURCE_PINS),("test_sha256",TEST_PINS),("support_source_sha256",SUPPORT_PINS)):
        require(contract[field]==pins,"Root exact closure differs: "+field)
        for path,digest in pins.items():
            digest_pin(digest,path);require(sha(prior.checked_path(path))==digest,"Pinned file changed: "+path)
    require(sha(CTEST_LOG)==CTEST_LOG_PIN and sha(BUILD_LOG)==BUILD_LOG_PIN and contract["ctest_sha256"]==CTEST_LOG_PIN and
        contract["build_sha256"]==BUILD_LOG_PIN and contract["ctest_passed"]==len(TEST_NAMES) and set(contract["test_names"])==TEST_NAMES and
        prior.checked_path(contract["ctest_log"])==CTEST_LOG and prior.checked_path(contract["build_log"])==BUILD_LOG and
        contract["terminal_exit"]==0 and contract["terminal_build_session"]==contract["terminal_ctest_session"]==24076,"Actual terminal build/tests differ")
    require(sha(VALIDATION)==VALIDATION_PIN,"Root actual build/CTest validation changed")
    validation=read(VALIDATION)
    require(validation["state"]=="PASSED" and validation["sources_before"]==validation["sources_after"] and
        set(validation["tests"])==TEST_NAMES and len(validation["commands"])==2,"Complete actual compiled/tested closure absent")
    for command,log,pin in zip(validation["commands"],(BUILD_LOG,CTEST_LOG),(BUILD_LOG_PIN,CTEST_LOG_PIN)):
        require(command["exit_code"]==0 and command["log"]==log.name and command["log_sha256"]==pin,"Actual build/CTest exit not0")
    for path,digest in validation["sources_after"].items():require(sha(prior.checked_path(path))==digest,"Complete compiled/tested source changed: "+path)
    require(all(validation["sources_after"].get(path)==digest for pins in (SOURCE_PINS,TEST_PINS) for path,digest in pins.items()) and
        all(validation["sources_after"].get(path)==digest for path,digest in SUPPORT_PINS.items() if Path(path).name=="CMakeLists.txt"),
        "Runtime/test/build contract outside compiled/tested closure")
    prior.ctest_gate(CTEST_LOG,len(TEST_NAMES),TEST_NAMES)
    require(sha(PREPARATION)==PREPARATION_PIN,"Actual prerequisite/startup preparation proof changed")
    preparation=read(PREPARATION)
    require(preparation["accepted"] is True and preparation["scope"]=="ISOLATED_PREPARATION_AND_ACTUAL_STARTUP_ONLY_NOT_UI_ACCEPTANCE" and
        preparation["candidate_sha256"]==PIN and preparation["harness_sha256"]==HARNESS_PIN and preparation["startup_exit"]==0 and
        {row["identity"]:(row["account"],row["page"]) for row in preparation["owners"]}==OWNER_CONTRACT and
        all(preparation[key] is True for key in ("guide_and_paired_reward_qualified","guide_map28_synthetic_test_only","original_source_rows_preserved",
            "old_weapon_transfer_false_preserved","private2598_released","frozen_files_preserved")),"Actual preparation prerequisite/startup0 proof absent")
    require(sha(NATIVE)==NATIVE_PIN and sha(NATIVE_TOOL)==NATIVE_TOOL_PIN,"Frozen419 original/current native evidence changed")
    # Source pins freeze419's machine/code counts through its complete receipt.
    evidence_root();live=ui_gate(read(RUN),SOURCE_PINS)
    require(sha(managed.CLIENT)==contract["client_sha256"],"Protected original client changed")
    baseline=read(frozen.BASELINE)
    require(baseline["current_client_accepted"] is True and frozen.hashes()==baseline["source_sha256"],"Accepted frozen chat changed")
    return dict(candidate_sha256=PIN,client_sha256=contract["client_sha256"],source_sha256=SOURCE_PINS,
        test_sha256=TEST_PINS,support_source_sha256=SUPPORT_PINS,contract_sha256=CONTRACT_PIN,
        harness_sha256=HARNESS_PIN,native_run_sha256=sha(RUN),native_offline_sha256=NATIVE_PIN,
        ctest_sha256=CTEST_LOG_PIN,build_sha256=BUILD_LOG_PIN,root_validation_sha256=VALIDATION_PIN,
        root_preparation_sha256=PREPARATION_PIN,helper_sha256=sha(Path(__file__)),**live)


def schema_sql():
    text=SCHEMA_SOURCE.read_text("utf-8")
    found=re.search(r'SqliteOwnedInstanceDiscardRepository::schema\(\)\s*\{\s*return R"SQL\((.*?)\)SQL";',text,re.S)
    require(found is not None,"Exact new receipt schema extractor differs")
    sql=found.group(1);digest_pin(SCHEMA_SQL_PIN,"Schema47 SQL")
    require(hashlib.sha256(sql.encode()).hexdigest()==SCHEMA_SQL_PIN,"Schema47 SQL changed")
    return sql


def schema_gate(before,after,template=None):
    require(isinstance(NEW_TABLES,set) and NEW_TABLES and isinstance(NEW_OBJECTS,set) and NEW_TABLES<=NEW_OBJECTS and
        isinstance(MIGRATION_NAME,str) and MIGRATION_NAME,"Exact migration47 schema objects not frozen")
    require([row[0] for row in before["history"]]==list(range(1,47)),"Exact installed schema46 required")
    require(not NEW_TABLES.intersection(before["tables"]),"Discard receipt schema already installed")
    require(after["pragmas"]==before["pragmas"] and set(after["tables"])==set(before["tables"])|NEW_TABLES,"Unexpected tables/pragmas changed")
    require([row for row in after["schema"] if row[1] not in NEW_OBJECTS]==before["schema"],"Existing schema objects changed")
    added=[row for row in after["schema"] if row[1] in NEW_OBJECTS]
    require({row[1] for row in added}==NEW_OBJECTS and len(added)==len(NEW_OBJECTS),"Exact new47 object set differs")
    for name,state in before["tables"].items():
        if name!="schema_migrations":require(after["tables"][name]==state,"Existing typed saved rows/history changed: "+name)
    for name in NEW_TABLES:require(after["tables"][name]=={"rows":0,"sha256":hashlib.sha256(b"").hexdigest()},"Receipt/grant created during stage")
    require(after["history"][:-1]==before["history"] and len(after["history"])==47 and
        after["history"][-1][:3]==[47,MIGRATION_NAME,schema_sql()],"History differs beyond new47")
    if template is not None:require(after["schema"]==template["schema"] and after["history"][-1][:3]==template["history"][-1][:3],"Actual47 differs from accepted clone47")


def config_after(before):
    for name in ("owned_armor_transfers","owned_armor_bank","owned_foreign_bank","owned_instance_trade","owned_mixed_bank"):
        require(before["world"].get(name)=={"enabled":True},"Accepted predecessor flag differs: "+name)
    require(before["world"].get("owned_instance_discard") in (None,{"enabled":False}),"Discard flag already enabled or not qualified")
    require(before["world"].get("owned_weapon_transfers",{}).get("enabled",False) is False,"Frozen predecessor weapon flag must remain false")
    after=copy.deepcopy(before);after["world"]["owned_instance_discard"]={"enabled":True}
    return after


def candidate_run(config,args,log):
    require(sha(CANDIDATE)==PIN,"Candidate changed before clone execution")
    env=os.environ.copy();env["GOD2_LOG_FILE_ONLY"]="1";env.pop("GOD2_NATIVE_WORLD_RECORDS_LAB",None)
    with Path(log).open("wb") as stream:subprocess.run([str(CANDIDATE),"--config",str(config),*args],cwd=ROOT,env=env,
        stdout=stream,stderr=subprocess.STDOUT,timeout=40,check=True,creationflags=subprocess.CREATE_NO_WINDOW)


MARKER="OWNED_INSTANCE_DISCARD_ENABLED CUSTOM-0071 full_instance no_grants no_formula no_ground_drop"
PREDECESSOR_MARKERS=("OWNED_MIXED_BANK_ENABLED CUSTOM-0070 full_instance no_grants no_formula",
    "OWNED_INSTANCE_TRADE_ENABLED CUSTOM-0069 full_instance no_grants no_formula",
    "OWNED_FOREIGN_BANK_ENABLED CUSTOM-0068 full_instance no_grants no_formula")


def stage():
    gate=qualify();require(not STAGE.exists(),"Stage already exists; inspect it")
    require(sha(managed.ACTIVE)==OLD_PIN,"Actual installed predecessor differs")
    config=read(managed.CONFIG);new_config=config_after(config);database=Path(config["database"]["path"]).resolve()
    before=snapshots.capture(database);accepted0070.source_catalog_gate(database)
    require([row[0] for row in before["history"]]==list(range(1,47)),"Stage requires schema46")
    STAGE.mkdir(parents=True)
    managed.backup(database,STAGE/"accounts.before.db")
    require(snapshots.capture(STAGE/"accounts.before.db")==before and snapshots.capture(database)==before,"Saves changed during clone backup")
    managed.backup(STAGE/"accounts.before.db",STAGE/"town-diagnostic-accounts.db")
    clone=copy.deepcopy(new_config);clone["database"]["path"]=str(STAGE/"town-diagnostic-accounts.db");clone["logging"]["file"]=str(STAGE/"stage.log")
    with socket.socket() as reserve:reserve.bind(("127.0.0.1",0));port=reserve.getsockname()[1]
    clone["server"].update(host="127.0.0.1",port=port,character_port=0)
    write(STAGE/"stage-config.json",clone);write(STAGE/"server-config.after.json",new_config)
    candidate_run(STAGE/"stage-config.json",["--migrate-only"],STAGE/"migration.log")
    candidate_run(STAGE/"stage-config.json",["--run-for","1"],STAGE/"startup.log")
    require(all(marker in (STAGE/"stage.log").read_text("utf-8") for marker in (MARKER,*PREDECESSOR_MARKERS)),"Clone actual discard/predecessor routes did not activate")
    after=snapshots.capture(STAGE/"town-diagnostic-accounts.db");schema_gate(before,after);accepted0070.source_catalog_gate(STAGE/"town-diagnostic-accounts.db")
    require(read(managed.CONFIG)==config and sha(managed.ACTIVE)==OLD_PIN and snapshots.capture(database)==before,"Formal files/saves changed during stage")
    shutil.copy2(CANDIDATE,STAGE/"god2-server.candidate.exe");shutil.copy2(managed.ACTIVE,STAGE/"god2-server.before.exe");shutil.copy2(managed.CONFIG,STAGE/"server-config.before.json")
    write(STAGE/"save-before.json",before);write(STAGE/"save-stage.json",after)
    info=dict(gate,state="CLONE_STAGED_NOT_INSTALLED",database=str(database),production_executable_sha256=OLD_PIN,
        config_before_sha256=sha(managed.CONFIG),config_after_sha256=sha(STAGE/"server-config.after.json"),
        added_tables=sorted(NEW_TABLES),saved_rows_changed=0,grants=0,capacity_added=0)
    write(STAGE/"release.json",info);return info


def apply():
    gate=qualify();info=read(STAGE/"release.json")
    require(info["state"]=="CLONE_STAGED_NOT_INSTALLED" and all(info[key]==value for key,value in gate.items()),"Exact unchanged qualification/stage required")
    require(sha(managed.ACTIVE)==OLD_PIN==info["production_executable_sha256"] and sha(managed.CONFIG)==info["config_before_sha256"] and
        sha(managed.CLIENT)==info["client_sha256"],"Managed files changed since stage")
    require(sha(STAGE/"god2-server.candidate.exe")==PIN and sha(STAGE/"server-config.after.json")==info["config_after_sha256"],"Staged files changed")
    expected=config_after(read(managed.CONFIG));require(read(STAGE/"server-config.after.json")==expected,"Config delta exceeds discard flag")
    database=Path(info["database"]);before=read(STAGE/"save-before.json");template=read(STAGE/"save-stage.json")
    require(snapshots.capture(database)==before,"Formal saves changed; restage required");accepted0070.source_catalog_gate(database)
    pid=managed.listener();idle_backup=accepted0070.all_process_connections_idle(pid)
    managed.backup(database,STAGE/"accounts.at-install.db")
    require(snapshots.capture(STAGE/"accounts.at-install.db")==before and snapshots.capture(database)==before,"Fresh backup differs")
    require(managed.listener()==pid,"Managed process changed before stop")
    idle_stop=accepted0070.all_process_connections_idle(pid)
    prior.common.lifecycle.stop_managed_and_wait(pid)
    if snapshots.capture(database)!=before:
        managed.start();raise RuntimeError("Saves changed while stopping; installation not attempted")
    try:
        shutil.copy2(STAGE/"god2-server.candidate.exe",managed.ACTIVE);shutil.copy2(STAGE/"server-config.after.json",managed.CONFIG)
        env=os.environ.copy();env["GOD2_LOG_FILE_ONLY"]="1";env.pop("GOD2_NATIVE_WORLD_RECORDS_LAB",None)
        with (STAGE/"formal-migration.log").open("wb") as output:subprocess.run([str(managed.ACTIVE),"--config",str(managed.CONFIG),"--migrate-only"],cwd=ROOT,env=env,
            stdout=output,stderr=subprocess.STDOUT,timeout=40,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        schema_gate(before,snapshots.capture(database),template);accepted0070.source_catalog_gate(database)
        require(sha(managed.ACTIVE)==PIN and sha(managed.CONFIG)==info["config_after_sha256"] and sha(managed.CLIENT)==info["client_sha256"],"Installed files differ")
        formal_log=Path(expected["logging"]["file"]);log_before=formal_log.read_bytes() if formal_log.exists() else b""
        managed.start();managed.powershell("$deadline=(Get-Date).AddSeconds(20); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed listener not ready'}")
        new_pid=managed.listener();process=prior.formal_process_proof(new_pid);startup=prior.startup_log_gate(formal_log,log_before)
        appended=formal_log.read_bytes()[len(log_before):].decode("utf-8",errors="replace")
        require(all(marker in appended for marker in (MARKER,*PREDECESSOR_MARKERS)),"Actual formal discard/predecessor markers absent")
        actual=snapshots.capture(database);schema_gate(before,actual,template);accepted0070.source_catalog_gate(database)
        require(frozen.hashes()==read(frozen.BASELINE)["source_sha256"],"Frozen chat changed during install")
        runtime_after={path:sha(prior.checked_path(path)) for path in gate["source_sha256"]}
        require(runtime_after==gate["source_sha256"],"Installed source closure changed")
        proof=dict(process=process,prior_startup=startup,discard_marker=[line for line in appended.splitlines() if MARKER in line],
            runtime_sources_after=runtime_after,runtime_sources_unchanged=True,idle_before_fresh_backup=idle_backup,idle_immediately_before_stop=idle_stop)
        write(STAGE/"formal-startup-proof.json",proof);write(STAGE/"save-installed.json",actual)
        info.update(state="INSTALLED",server_pid=new_pid,installed_at=prior.common.now(),saved_rows_changed=0,grants=0,capacity_added=0,
            formal_startup_proof_sha256=sha(STAGE/"formal-startup-proof.json"));write(STAGE/"release.json",info);return info
    except BaseException as error:
        info.update(state="REPAIR_REQUIRED_SCHEMA47_COMPATIBLE_CANDIDATE_RETAINED",error=str(error),database_restored=False,old_executable_restored=False)
        write(STAGE/"release.json",info)
        if sha(managed.ACTIVE)==PIN:
            try:managed.start()
            except Exception:pass
        raise


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=("qualify","stage","apply"));args=parser.parse_args()
    result={"qualify":qualify,"stage":stage,"apply":apply}[args.mode]()
    print(json.dumps({key:result.get(key) for key in ("state","candidate_sha256","saved_rows_changed","grants","capacity_added")}))
