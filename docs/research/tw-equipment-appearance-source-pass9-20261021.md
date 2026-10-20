# 裝備、世界外觀與 PvE 材料來源：pass9

日期：2026-10-21；基底 `fc1c7f5cc24ddb4b15589a3eb5d63cfb44e3ec94`。
本輪 PHASE1 SOURCE_STATIC_ONLY；沒有編譯、測試、game／VM、codec、遊戲 SQL、
schema、部署或實際帳號操作。下列流程是源碼可達分析，不能當作玩家重現紀錄。

## 證實的配置與生命周期缺口

`owned_pve_rooms` 原先可以與 `diagnostic_owned_weapon_appearance` 共啟用。
後者經 `owned_weapon_transfers` 的 C28 selection 進入 CUSTOM-0047
`fixture_after`，在同一裝備交易內更新 `character_player_appearance_snapshots`
並回傳 DA。它只支援明示的兩份合成測試實例，並非已恢復的原服武器外觀映射。

PvE 的角色材料則由完整 Catalog、目前 root40 與原來 Written2A 資格。
這條 C28 診斷 writer 沒有替該原始 INIT 或 Catalog Fight profile 提供完整合法
successor。PvE 的正常 visibility 又不等於 `player_presence_enabled` 的兩個舊
診斷 flag；只開 PvE 時，舊 writer 甚至不會因 PvE 已有 Presence 就更新該 cached6F。
因此 self DA、世界顯示和下一次入戰可能使用不同代的材料。即使另開舊診斷
visibility，仍沒有 Catalog／INIT 的完整 successor；不能以補一份8-byte copy
宣稱整條裝備或變身來源已接好。

本輪補 `Config::validate_owned_pve_material_sources()` 這個純相容性檢查：
只拒絕 PvE 與這個 runtime 診斷外觀 writer 同時啟用。JSON loader 在所有 flag
解析完畢後呼叫；programmatic Application 在資料庫初始化／host 建構前呼叫
同一方法。檢查不讀資料庫、不修改設定、不建立 Session 或猜外觀資料。

這是把**不支援的組合早拒絕**，不是完成裝備到 Fight／世界外觀的原生生成。
單獨的 `owned_player_appearance` 初次完整2A來源仍可與 PvE 共存；實際入戰
仍須符合 Catalog 完整 root／entry 材料。未啟用 PvE 的原 CUSTOM-0047 診斷
功能保留。沒有為所有裝備／防具 flag 新增無證據的互斥。

## 等價入口與來源邊界

搜尋 src 的實際 `player_appearance().save` 與 `fixture_after` callers，runtime
writer 只有上述 Application C28 分支。C24 武器 bag move 只搬 bag 兩格，不走
`PrepareExtra` 外觀更新；防具／神獸舊搬移明示不提供外觀或能力公式。這些未完成
的 native equip 功能不能因本次 gate 就標成完成，但也不是另一個已證實會改 DA
並沿舊 PvE profile 的 writer。

CUSTOM-0092 的 joint transaction 與 entry transaction 是另一條來源：必須由真正
issuer 提供完整 inventory／native equipment，appearance-only entry 同步還要求
原有完整 entry，固定其他全部位元並核 after2A 與 afterDA。沒有從 item key、
metadata、物品名稱自動造 DA。公開 source factory、receipt 與 publication 不等於
已安裝原服裝備規則；正常 retained-world PvE 亦明確不借 shared-common-world plan。

`SharedTaiwanNativeEquipmentPublicationSource` 保留實際 writer 的完整 committed
token；entry 版本不降級為兩個 store。`SharedActorVisibility` 的台服 DA publication
保留 wire-history receipt，並明說 retained initial6F 不是目前完整 actor cache。
它沒有把 remote4FC130 的效果誤當完整8-byte快取更新。

`RecoveredVisibility::prepare_appearance` 的確會把完整 `Fields.components` 寫到
伺服器 cached6F，但它在 Application 的唯一實際外觀 caller 是 CUSTOM-0047
`fixture_after`，使用明示合成 after-state。這不是原生 remote DA consumer 的
記憶體模擬，也不是149c `SharedActorVisibility` publication；兩者不能混稱。
原生 remote4FC130 僅修改 odd-byte 高3 bits 的既有證據不證明 item→完整 fresh6F
producer。沒有修改已凍結診斷映射或把該映射提升為 native authority。

## 變身與當前原件

`TaiwanNativeTransformCards` 仍明釘149c executable、舊 decoded／encoded 資源。
`SharedTaiwanNativeWorldEntryOfferSource` 對 card target 核實際 scene 的 image、
decoded、encoded provenance 與 ordinal occurrence。當前 aaf0 的 ChangeDoll
reader／48-byte 本機定義新證據不能透過只換一個 SHA 借用舊內容。

本輪 source lane 沒有發現另一條正常 PvE runtime morph writer；沒有據此新增
猜測 decoder、schema 或 transformation defaults。原生455780／49B850／裝備 selector
與完整 identity／appearance producer 的進展由獨立 native lane 保存，未知仍為未知。

新 native lane 另證實變身道具6285／6286／6289的 UI confirmation 會從真正20-byte
instance 的+4 WORD 選 ChangeDoll row；`4EAEF0`／`45C060` 的 row48 字串用於
確認顯示。state5確認後 `4EA770 → 496720 → 4132E0(0x27,...,4)` 只送 item
key WORD／slot BYTE／count BYTE，沒有傳 morph key 或完整 identity。引用本輪
`native-material/morph-selection-and-ui-child-dataflow-pass9-v4.json`
（`ev_cdfd88dde4aca8f6d6ceddfafbd795e98fb4e47127e748fa7f315ea3d7ca52aa`）、
`assembly-transform-instance-key-and-confirmation-state-pass9-v7.json`、
`confirmed-item-wire-and-active-pet-source-selection-pass9-v7.json` 與
`assembly-confirmed-item-request-source-pass9-v8.json`；原始證據 SHA 另封作者收據。

服務端 C27 的歷史型別名為 `RecoveredInventoryDiscard`，現有 host 僅資格各自的
scalar／typed discard 域，沒有上述變身 item-use handler 或第二個 appearance
writer。普通 MED02 scalar 域限已釘的3101..3200 recovery declarations／既有少數
map或fruit；typed discard 另有 weapon／armor／gem／beast 完整來源門檻。
不能因同一 wire 形狀就把新 confirmation 當作已授權丟棄或已完成變身。變身使用、
消耗、資格及完整外觀 after-state 仍未實作／未證；本輪不擴大既有 destructive域。

## SOURCE 案例、複查與限制

`test_config.cpp` 增加未執行案例：有效 JSON 的 PvE＋initial appearance 可載入；
PvE＋runtime 診斷外觀 writer 必須以精確共用 gate 訊息拒絕；同一 typed Config
的 programmatic 檢查亦拒絕；關掉 writer 或關掉 PvE 仍保留原合法邊界。
既有 JSON fixture 先證明其餘 prerequisites 有效，避免把無關配置錯誤當成此項修正。

Application 使用同一純方法的實際 DB 前位置另做源碼複查；沒有建立完整
Application／真實 Session／裝備 SQL observer／客戶端 host fixture。案例尚未執行，
不能宣稱測試通過或裝備、變身、返回後顯示已完成遊戲驗收。
