# 第320輪：裝備與既有入場快照共同保存

補上319所找到的具體交易缺口：新增三份完整資料的同connection原子保存，並連到既有held DA publication。修改7個C++檔、新增1個C++檔；新的來源同步edge只計1，完整玩法branch/opcode/雙向route新增0。沒有建置、SQL或遊戲執行。

## 實際呼叫鏈

在same Application Context明確選owned_equipment_entry_transaction，要求inventory/equipment/entry的actual reader與writer identity相等、同account/character sources、同connection及game owner。舊two-writer constructor不變，worlds預設null；沒有Main或schema opt-in。真實rules owner提供WithEntryBefore與WithEntryState及mandatory EntryIssuer，replace_with_entry_from_issuer接完整三tuple。

三writer guards下own BEGIN IMMEDIATE，先資格11個actual main tables與case-insensitive TEMP name/tbl_name，再讀共同root/current saved position/no-open-battle及全expected raw population。Prepared/BeforeWrite/BeforeCommit要求完整equal next，callback禁止SQL/transaction操作、reader/writer重入、yield/pump/send。三store的stage在同一outertransaction，完整readback及全roots/pose核對後，immutable EntryCommitted配置在only COMMIT之前；失敗依Transaction RAII全部rollback。提交後不callback/read/retry/allocate。

Entry repository增加friend/private validate_change/stage_replace及joint-only issuer_active reader guard；existing publicwriter method/schema保留原source行為。Old joint.cpp完全未改。Private stage沿既有fullrow SQL/revisionCAS/changed-row1/readback，不publicreceipt、不own nestedtransaction。

## 完整來源與允許變動的欄位

API只接受already-existing完整149c zero-seed2A40B與完整owner inventory/equipment1215B。Source提供完整nextframe，沒有DA→2A builder。Expected entry可以較current DA舊，才能補同步差額；next entry的8component／transformWORD／兩rawscalar必須等真正next DA。Actor比equipment.scene handle與DA WORD，不能等同common64 character ID。

除了decodedlogical13..20與33..36，其餘logical全部逐byte凍結為expected；selectors、opaque、identity、area/scene、kind、pose不變。Expected/next root與savedposition也完整相等。這不是recover equip rule、grant item、猜原B0/B4/B8、fresh profile/defaultbody或firstentry。來源資格仍由mandatory完整original rule/phase/resource issuer提供，沒有成功空handler。

## 持久來源接到原生更新

owned_equipment_entry_publication_factory只接EntryCommitted並保持整個token。SharedTaiwanNativeEquipmentPublicationSource的新create保存joint_entry_committed，source current選committed_current(EntryCommitted)；該overload於one consistent read scope比較三完整tuple及joint/private writer identities，不用兩個獨立public Current湊原子性。原visibility的Prepare/BeforePublish/AfterPublish/queue completion沿同supplier核對實際lease/currentposition，實際DA仍取full equipment tail，不重新造bytes。

既有one/two-store publication與舊defaults保持。COMMIT後來源若stale，只能阻止後續delivery，不能撤銷已持久資料。網路配送與儲存並非同一原子交易，不聲稱native ACK、local-self/CN mixedfanout或已可重新登入。Old private normal-entry/PK receipts不重新mint；actual rule owner須資格合法phase及時機。

## 尚未完成

C28真正equip mutation規則與full original next frame/material supplier、fresh2A original packed selectors/opaque、Entered/full6F/worldpublication仍缺。StoredEntry Source仍有scope.character==actor_handle的既有join，newstorage只保持handle與common64分開，不替該未完成入場映射作證。所有全遊戲玩法/phase/state/variant分母仍未追完，不能把本storage edge當整個入場或整個遊戲100%。

TW C2S156 candidates；world74＝部分50/control11/未接13，67.6%只計部分world parser。S2C252＝230fixed/22variable，nondefault206/default46、reply48/push11/gated4/未分類117；battle110/specialized9，86selectors7/cases6，83actions23/projections2/outside21。TW chains3/bindings38 unique34。CN historical C2S156、S2C phase280/length253是不同scope，chains35/bindings93 unique71，本輪無增量。Mixed282/groups26/pending10/CUSTOM135保持。Wholegame封包數、完整路徑分母、TW及整體百分比null。

CUSTOM-0092新增source_extension_20261012_round320 provenance，其原keys/規則與其他134records保持；它是custom internal storage coordination，不升格native equip或CN gameplay。7modified/1added均只source，原帳號存檔/auth/chat/IME/頭像/原字體/繁簡轉換/client binaries、common tables、TW/CN/web、shared64/coin99999999999/stack99/原level保留。CMake既有GLOB_RECURSE納入新cpp，沒有configure/build。

No build/compiler/tests/runtime/native/VM/emulator/resourcecodec/gameDBSQL/migrate/activate/deploy。SQL只是新增source字串，沒有执行。Heavy before/candidate/reports/evidence外置God2；incoming webv112僅metadata，wire契約未改，本root未作本次ACK/adoption或使用peer94%估計。

## 固定證據

外部包：`C:\Users\risei\.codex\artifact-archives\god2-server\20261012\tw-owned-equipment-entry-atomic-source-320`。完整current bounded packages與actual nested seals保留；partial historical/peer copies不是全oldpackage。

```json
{
  "entry-writer": {
    "completion_percent": null,
    "cpp_files_modified": 2,
    "fullroute_increment": 0,
    "input_bytes": 57869,
    "input_count": 7,
    "native_increment": 0,
    "opcode_increment": 0,
    "round": 320,
    "source_credit_owner": "parent integrated connected three-population chain; no independent duplicate credit",
    "raw_seal_sha256": "3fb389de2fb323cc2c375ed2e4fdf9834fd1a80626ea762e8d4752e56144e010",
    "canonical_closure_sha256": "6570a54bc84f18134714204d90e4524ae4e88d7b90355c05dbefbf1beb4a83b0",
    "closure_members": 14,
    "closure_bytes": 74266
  },
  "joint-entry": {
    "source_files_added": 1,
    "source_files_modified": 1,
    "owned_source_files": 2,
    "new_atomic_source_edge": 1,
    "new_native_methods": 0,
    "new_native_opcodes": 0,
    "new_complete_routes": 0,
    "gameplay_acceptance": false,
    "builds_run": 0,
    "tests_run": 0,
    "sql_run": 0,
    "raw_seal_sha256": "8b62bfb580c15bfc882b5cdbaeb0ee7b01839f3e1e35072aa84438b18a0a7b1a",
    "canonical_closure_sha256": "6b34527119caf86a0ce6f086c8e9929179b93230fa4f31515337df3a2782f9d4",
    "closure_members": 32,
    "closure_bytes": 413242
  }
}
```
