# CUSTOM-0051：推定收集任務的純狀態規則與原子計畫

日期：2026-09-27。狀態：**純C++模型與單元驗證完成；本子任務未接Application、
未建立migration、未部署，未做當前客戶端驗收。** 原始任務判定／獎勵規則
不能由這個validator反向證明。註冊索引、四份來源recipe與storage adapter由主線整合。

## 檔案與責任

- `src/game/InferredQuestRules.h`：header-only C++20，namespace
  `god2::InferredQuestRules`。
- `tests/test_inferred_quest_rules.cpp`：獨立main；沒有SQLite、network或client依賴。
- 舊`Quest.h`與`QuestRepository.h`仍是placeholder，本輪不改其共享介面。

現有`SqliteQuestJournalRepository`儲存CUSTOM-0041的15-DWORD**展示快照**；
packed高WORD是文字selector，不能轉成已接受／完成狀態。既有
`DiagnosticQuestConversation::consume_after_commit`提供可沿用的commit後
消耗對话綁定模式。`SqliteInventoryMove`已要求owned explicit row、revision
CAS及transaction rollback；本模型也不把不存在的背包列當成空槽。

## 最小整合API

```cpp
namespace q = god2::InferredQuestRules;
q::Result candidate = q::plan_accept(rule, snapshot, {account, character});
q::Result submission = q::plan_submit(rule, snapshot, {account, character});
// Inside the same DB transaction, after re-reading every row/read condition:
if (!q::revalidate(rule, current_snapshot, *submission.plan)) reject_stale();
```

`Result`有`Error`與`optional<Plan>`；失敗永遠沒有部分plan。函式不改輸入，
不寫DB，不grant物品，不發wire。Plan保存action、quest id、rule revision、
authority、完整`expected`／`after` snapshot及`exact_rewards`。accept的reward
payload保持空；submit原樣保留宣告的payload，包括所有20-byte instance尾端與證據。

純validator輸入是**server可信規則與同一transaction讀到的owned state**；
不能把client送來的JSON/opaque word直接反序列化為可信Rule或Snapshot。
`revalidate`還會重新計算plan與結果全文相等，拒絕改過獎勵的Plan，以及任一
read-set變化；這仍不能取代真正的資料庫transaction與owner查驗。

## 明確欄位來源，未知不完成

每個`Fact<T>`含optional value及`Evidence { Origin, reference }`。
Origin只有`NativeVerified`、`CustomInferred`、`SyntheticTest`可識別，
Unknown、非法enum、缺值、空reference皆不合格。

一般呼叫預設`Evaluation::OwnedRulesOnly`，拒絕所有SyntheticTest欄位。
隔離單元測試須顯式傳`Evaluation::IsolatedSyntheticTest`。文字reference不是
自動證据認證：來源SHA／版本／列／語義與recipe合法性必須由主線loader核對。

| 欄位 | 契約 |
|---|---|
|Rule.authority|穩定CUSTOM-NNNN＋policy reference；此實作為CUSTOM-0051|
|id／revision|id有Fact；revision正值，最多SQLite signed64上限|
|level|已知minimum/maximum；不存在的level條件須明確給出完整允許範圍及policy來源|
|completed_prerequisites|已知的完整vector；明確空vector與未知不同；不能含本任務、0或重複|
|repeat|目前只實作Once；其他enum拒絕|
|collect_objective_complete|必須已知true；不能省略未知的kill/timer/branch條件後假完成|
|requirements|非空且每個item、quantity、consume、match都有Fact；相同item重複規則拒絕以免重算／重扣|
|rewards|currency、experience、reputation、完整stack vector分別有Fact；0／空必須明確指定|
|reward stack|精確20-byte instance＋1..127count，各自有Fact；不自行產生品質／class／附加bytes|

本子任務沒有填入任何原始任務ID、材料數量、level或獎勵數字。測試的900000等
ID與60001等item、17 currency均明確合成。另四個reputation-only測試只檢驗
`+1名聲，currency/experience/items皆明確0`的機制；不冒稱已恢復四份原始recipe。

## 狀態與CUSTOM政策

Snapshot包括owner、`quest_history_complete`、`mutation_admitted`、已保存Role、
獨立quest progress map和30個optional bag rows。這兩個bool是repository／route
完成真實查驗後的輸入，不是由client聲稱。

- owner兩ID非0且精確相等。沒有完整任務歷史或Role就拒絕，不seed。
- Role只包含本判定所需level、currency、experience、reputation、revision。
  不計算升級／growth／HPMP，也不清除未出現在這個view中的角色欄位。
- Accept：符合level與完成前置、當前任務不存在時，插入Accepted/revision1、
  accepted_rule_revision及design_id；不扣料、不發獎。
- Submit：要求Accepted且同rule revision/design id；level／前置再驗。
  Completed一律拒絕，完成次數恰1；不支持daily reset或可重複任務。
- 角色、進度與slot revisions範圍1..INT64_MAX；需要寫入但已到上限即拒絕。
- `(design_id, quest_id, rule_revision)`必須由主線儲存為**不可變的規則版本**。
  更換任何predicate／payload必須換revision，已有接受狀態需顯式遷移；
  不能用相同revision偷偷換獎勵。此模型沒有自行計算或驗證外部rule檔hash。

### 收集與背包

Submit要求30列皆明確存在；這是完整capacity/read-set政策，不會自動分配槽位。
Slot count上限**127**，遵守現有server inventory契約；不是宣稱原服stack cap。
item=0 iff count=0；空槽不得殘留instance。每列revision與provenance必須存在。

兩種顯式匹配方式：

1. `ScalarOnly`：item ID相同且row.instance為null；不碰同ID的20-byte實例overlay。
2. `ExactInstance`：item ID和全部20bytes都相同；不忽略opaque尾端或退回template匹配。

同ID需求不得重複，避免重疊selector或consume／hold互相抵消。每種需求先驗
總量，consume=true才按slot0..29順序扣除；false為明確「持有即可」policy。
部分扣料保留全部instance/provenance；扣空清item/count/instance但保留原來源追溯。

精確reward stacks按宣告順序放入最低的明確空槽，亦可使用剛扣空的槽。
**不做stack merge，不拆分、不抽獎，不創建未知metadata。** 容量不足、未知
reward或任一overflow都不返回plan，輸入狀態保持不變。同一槽扣料再放獎勵
僅按final row差異增加revision一次。未改變的slot不增加revision，但仍在read set。

### 精確資源獎勵

currency、experience、reputation用uint64讀取與加法前界限檢查，保存上限
INT64_MAX；沒有浮點與截斷。任一非零增加才將Role revision加1，三者都0則
Role完全不變。名聲+1沒有伴隨currency/item/grant。這個上限是SQLite儲存
限制；原服貨幣上限、EXP單位／升級、名聲門檻仍須來源資格化。adapter還須
驗證自身schema／native projection能表示結果，否則在commit前拒絕。

## Repository／route必須完成的原子步驟

1. route驗證當前session owner、world ready、位置/NPC/issued conversation，
   並排除battle／pending door／混合mutating record；不能用journal或D8 opaque
   值授權任務。
2. 在單一transaction中讀owner、相關任務完整歷史、Role、30bag rows與全部
   instance overlays；把scalar/instance合併成互斥view，不能將「沒讀overlay」
   當成ScalarOnly。
3. 重算或`revalidate`，再CAS進度、所有寫入slot、資源與durable once/reward
   receipt。當前absence也要保護：accept以unique owned quest key插入；任何
   affected-row-count異常、owner/前置/read-set變化、projection不可表示均rollback。
4. 只在commit成功後消耗session對話綁定並送已驗證native projection。網路失敗
   不重發獎勵；reconnect依保存after-state還原。任一失敗不提供假成功提示。

`exact_rewards`是storage domain payload，不是自創packet。不要把20-byte
instance直接當未知S2C獎勵封包；使用現有合格inventory/resource展示契約。

## 驗證與註冊建議

獨立MSVC x86 Release，`/std:c++20 /EHsc /W4 /WX /O2 /DNDEBUG`，**103 checks PASS**。
用明確throw gate，NDEBUG不會移除檢查；沒有建共用core。

```powershell
$testOut=Join-Path $env:TEMP 'god2-inferred-quest-rules-20260927'
New-Item -ItemType Directory -Path $testOut -Force | Out-Null
# 在VS x86 Developer Command Prompt，repository root執行：
cl /nologo /std:c++20 /EHsc /W4 /WX /O2 /DNDEBUG /I src tests\test_inferred_quest_rules.cpp /Fo"%TEMP%\god2-inferred-quest-rules-20260927\quest.obj" /Fe"%TEMP%\god2-inferred-quest-rules-20260927\quest.exe"
```

涵蓋owner、level、前置、accept無grant、未接受、重复once、資料缺失、unknown
reward/predicate、完整opaque instance、跨槽扣料、滿包純失敗／剛清空槽重用、
各revision/CAS與tampered plan、128count拒絕、currency/reputation溢位，以及
四份名聲only fixture。

主線CMake需先從TEST_SOURCES glob排除此獨立main，再新增
`inferred-quest-rules` executable、src include path、cxx_std_20及同名CTest。
本子任務沒有修改CMake。單元成功只代表模型契約，未代替balance審核、實際
storage交易、TCP重登入或當前原始client驗收。
