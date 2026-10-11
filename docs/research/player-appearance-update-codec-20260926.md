# 普通玩家 DA 外觀更新：C++ wire 與原生消費端資格

2026-09-26。原生證據限目前 `God2.exe` SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`。

## 本次完成

- `src/protocol/RecoveredPlayerAppearanceUpdate.h`：S2C DA 固定15 bytes。
  保留完整16-bit actor（不套3FFF遮罩）、16-bit transform key、兩個原始
  scalar，以及完整8-byte packed component block。寬值輸入先驗證再縮窄；
  decode 拒絕錯opcode、截短及尾隨bytes。
- `tests/test_player_appearance_update.cpp`：嚴格大小、寬度、未遮罩身份、
  variant bits、完整component與encode/decode資格。CLI可輸出真正C++ wire。
- `tests/research/test_player_appearance_update_native.py`：45組C++輸出直接
  寫入原生消費端memory，涵蓋self／已存在remote／不存在remote，身份包含
  4001與FFFF，prior selector 0／27／91。原生dispatch執行至461270入口或
  46B517 missing-actor ignore；完整input canary、actor manager、scalar與
  component參數均驗證。另重跑既有49個native routing/setter/persistence案例。
- CMake/CTest已註冊 `player_appearance_update` 與
  `player_appearance_update_native`；Release build與2/2 CTest通過。
  子代理獨立正常與`-O` Python 3/3通過；root再用正式build target正常及
  `-O`重測通過。

## 世界武器資源另一次進展

`current_weapon_selector_authority_20260926.py`先前共用VM消耗單調heap，
第三個案例請求15MiB時超出固定128MiB fixture額度。新增精確配置診斷後，
改為四個獨立未快取VM案例，未提高heap或單次配置界線。原生461270完整
return、原生HeroDoll cache/path、四個實際ROM資源handle及input/output
canary均通過；正常與`-O`輸出完全相同。

結果：`artifacts/research/native-weapons-20260926/selector-authority.json` 與
`selector-authority-optimized.json`。每個VM的weapon handle3僅為該次bank
ordinal；不是固定物品／外觀ID，也不是原服WPN映射。

另交付 `current-weapon-mapping-fields-20260926.md`：16組WPN/TWP原生
parser差分，正常／`-O`通過且输出相同。source columns1/2/30/31均未被
標準definition parser讀取；26～29只影響已知數值欄位。source column1
各種值的完整原始row、hex及行號已保存供追其其他consumer，沒有據此猜外觀。

## 尚未完成與啟用狀態

這是原生wire／consumer與資源層資格，**不是正式穿裝功能完成**。
本次沒有變更Application、正式資料庫、活動服務端EXE、玩家存檔或客戶端。
普通武器轉移正式開關仍關閉，既有隔離28／24驗收資格保留。

仍需補齊：

1. owned WPN key／instance到DA weapon packed selector的原生映射；
2. 相同角色的權威完整after-state、其他component/scalar保留與持久化；
3. 完整DA self／remote refresh tail及實際客戶端接受；
4. 穿裝合法條件與攻防加成結算，經2C更新的資格；
5. 非零transform eligibility及資源條件（本次codec保留欄位，不認證資源）。

來源與邊界詳見 `current-weapon-appearance-20260926.md`、
`current-weapon-selector-authority-20260926.md`。
整體目標仍active；約11%僅規劃估算，不是封包覆蓋或可玩百分比。
