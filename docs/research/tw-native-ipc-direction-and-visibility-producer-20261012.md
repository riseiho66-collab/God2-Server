# 第310輪：原生 IPC 方向與角色旗標產生端

本輪延續第309輪的實際註冊回呼及角色池呼叫鏈。只做靜態原生恢復與來源追查；沒有修改遊戲 C++、執行客戶端、測試、存取遊戲資料庫或部署。以下 Windows 訊息編號與遊戲網路 opcode 分開記錄。

## 描述資料的方向

目前定位到的 `46B9D0` 產生端，從原生 S2C 接收分派取得資料，建立三個 DWORD 的區域描述結構，透過 `SendMessageA` 的訊息 `4A` 轉送。它先用 `FindWindowA` 查找標題 **GM Tools FS2**，經過 `55CA7C` wrapper，最後讀返回物件的 `+1C` 作為傳送目標。中間 `5616C5` 有 guarded virtual `+8C` 回呼，不能宣稱最後 handle 必定仍等於原始查找結果。

遊戲註冊的視窗類別則是第309輪的 **XianJieWndClass**，建立結果保存在 `6F4CA0`。因此這是具有外部工具 lookup 的 outgoing IPC 路徑，尚未證明目前目標視窗或接收行為；不能替代尚未找到的遊戲視窗輸入來源，也不能把工具端未取得的接收、回傳或儲存邏輯算成完整遊戲路徑。

八個 opcode 與 GM 標題轉送早已記錄於 `current-s2c-first-hop-and-gm-bridge-20261006.md`；本輪不重新計入新 opcode 或宣稱全域新發現。此次追查補的是原始 PE 的匯入函式身分、真實 entry／呼叫鏈、區域描述資料生命期及中間 wrapper 的回呼邊界；歷史文件仍保留其當時尚未獨立解析匯入的範圍。

描述結構的區域生命期、固定長度及原始資料指標，以本輪封存的實際指令、匯入項及字串位元組為準。同步傳送的區域生命期不證明接收工具會複製、保留或正確處理資料；也沒有取得真正的 Timer36 `U18` 供應者或目前全域 cleanup pointer 的設定者。

## 角色旗標的產生端

新追到 `466B00 → 4820A0 → 4F4B50` 的實際呼叫。外層 world owner 與其 `A7F2F6C` 子物件是不同基址；`4820A0` 使用子物件的事件欄位，不能把它的 `86888`、`232DBC` 直接當作接收端 Main 的相同偏移。

`4820A0` 向 `504620` 傳入 local WORD／BYTE 欄位的位址，之後以 caller 的返回值與這些欄位選定 `4F4B50` 分派。本輪只追到 `504620` 先將 output WORD 設為 -1、BYTE 設為0的入口；它後段如何產生事件仍未完整恢復，不能把初始化當成事件權威。selector10 的分支在指定 BYTE flags 條件成立時切換實際物件 `449E` 的 bit2，再計算完整 DWORD 的 0／1，傳給 global `6F4CA0` 的訊息 `403`。實際 API CALL 在 `4F4E58`；先前定位用的 `4F4E52` 是 `PUSH 403`。這不證明目前 OS 目標 handle 或已接收訊息。

這個 `wParam` 是 scalar 旗標。註冊回呼傳給 root method 的是原始 `wParam` **stack slot 的位址**；接收端讀該 slot 的 DWORD，並非把 scalar0／1 解參照成地址。之後才進入第309輪的 `467DF0 → 4FC6E0` 角色池呼叫鏈。

這條追查補上呼叫者、物件基址、事件選擇、旗標運算及實際視窗傳送。它不是網路 opcode403，也沒有提供完整 `6F` 81B 角色紀錄內 opaque DWORD9／DWORD17 的服務端原始來源。遠端 128 槽／stride268 與另一個 256 槽／stride1D8 物件池仍分開。

另一條實際網路來源是既有 S2C **1B**：原始表 `46B5D4` 的1B cell指向 `46AE4D`，跳過opcode後呼叫 `4F5030`。它以 body WORD 寫入上述子物件所持物件的 `449C..449D`；這不是對旗標 BYTE `449E` 的直接寫入。後段跨過 opaque 子呼叫才讀取 `449E` bit2，並於 `4F50D5` 傳送同一種本地訊息403，不能宣稱1B已供給或保持該旗標。它不是鄰近的82 case；不能只靠連續反組譯位置判定 opcode。這補上網路consumer至本地通知的資料路由，但仍未取得449E物件的完整生命期、1B服務端producer與玩法規則，完整雙向路徑增量維持0。

## 正式來源在哪裡仍需供應者

| 階段 | 實際來源位置 | 已存在的條件式接點 | 仍缺的內容 |
|---|---|---|---|
| 啟動 | `main.cpp:86`、`Application.cpp:7309` | 現行 main 呼叫無 plan 的 overload | 實際完整 world source factory 的選擇 |
| 同一遊戲核心 | `Application.cpp:641`、HostPlan Factory | 同一 Context／資料庫 reader-writer／game owner | 實際原生來源與生命周期 |
| 世界入口 | WorldEntryOfferSource、HostPlan `scene_entry_offer` | NPCList／EnyName → 必要 SceneSupply → 原 writer CAS | 完整2A資源、狀態、opaque 欄位與 issuer |
| 初始場景 | WorldEntered、Session `send_common_world_entry_with_publication` | 完整 aggregate／每個6F邊界、held write、install／visibility publish | 完整原生場景 bytes、實際 Current／install owner |
| Ready | WorldLifecycle、WorldEntered outward completion | delivery identity、外向發布、transport binding、cancel | 所有完整來源的共同組合與後續玩法 |

`QueueReleased` 只表示 held frame 已放入可送出的佇列；不是 socket 寫入完成、客戶端 ACK 或原生驗收。`ExplicitNoInitialReply` 是供應者必須明確選定且具實際 install／current／visibility 的另一種決定；不能拿空資料或無條件成功回呼補掉缺失的原生場景。

HMD `Model` 的模型位置與可選 script/object 欄位，與 NPCList 的 area／scene／resource code 屬不同資料命名空間。本輪所讀的解析來源沒有建立 model occurrence → NPC runtime record → 每日任務目的地的關聯；相同的座標欄位名稱不能授權 NPC 傳送、費用或獎勵。這是限定來源的缺口，沒有宣稱整個客戶端或資產中不存在關聯。

## 來源範圍與進度

證據包位於外部封存 `tw-native-message-producer-and-world-route-310`。各工作包完整檔案雜湊、原生 entry／PE／decode、限定人工閱讀區段、舊資料重疊及失敗查找分列；完整 byte capture 不代表整個 client/callgraph 已人工讀完。

990 個原有 `src` 檔案未變更。C++／新 opcode／新串接來源分支／完整雙向路徑增量均為0；全遊戲路徑分母与百分比仍未知。既有台服世界解析範圍74＝部分來源50／控制11／未接通13，不能用50／74當全遊戲完成度。CN、網頁、shared64、原生字體、文字轉換及凍結功能維持既有範圍。

網頁同伴 v102 的 commit／CI／容量數字只保存為收到的交接訊息，沒有在本輪取得或執行該 client、回傳 ACK、採用來源或據此宣稱共同 wire／native 驗收通過。

下一步沿 `1B → 4F5030 → 4F55F0／4F5670` 與實際物件 constructor／生命周期追 `449E` 寫入者。另以 `55B42F／5463B5` 的 release／allocation 邊界與全域 initializer／writer 釐清 cleanup pointer；舊 `55AD35` 的 pointer-header decrement 形狀不證明它是遊戲 Timer36 供應者，也不據此宣稱已識別 library class。繼續追真正遊戲視窗 `4A` 輸入者、完整2A／6F發行者；GM 工具轉送與 local visibility 旗標不得填入未取得的遊戲權威資料。

## Qualified evidence capsule

Static archive and selected-native metrics, separate from completed gameplay.

```json
{
  "native-descriptor": {
    "qualified_spans": 6,
    "bytes": 527,
    "sites": 142,
    "new_selected_spans_vs_reference": 4,
    "new_bytes": 357,
    "new_sites": 98,
    "explicit_overlap_bytes": 170,
    "overlap_sites": 44,
    "data_slices": 29,
    "data_bytes": 159,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "399613f85c265d5c88d1668f502e2c684c6810cd21cb6ed64357180cb1208c12",
    "canonical_closure_sha256": "97f1c92ccfac488c24e05b47212faadd5e1a7d90206dbdf0d18c2c04b6f40343",
    "closure_members": 102,
    "closure_bytes": 7037510,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  },
  "native-producer": {
    "qualified_code_intervals": 10,
    "qualified_code_bytes": 1540,
    "qualified_instruction_sites": 434,
    "unique_qualified_code_bytes": 1540,
    "new_local_bytes_vs_captured_306_binding_307_payload_context_309_actor_callback_qualified_bounds": 1376,
    "explicit_overlap_bytes": 164,
    "overlap_detail": "466B00..466B1C 28B from307 payload;468AE0..468B68 136B from307 context. Other historical/exploratory coverage not claimed globally new.",
    "qualified_data_slices": 8,
    "qualified_data_bytes": 130,
    "global_historical_novelty_claim": false,
    "new_source_branches": 0,
    "new_opcode_values": 0,
    "new_full_routes": 0,
    "completion_credit": 0,
    "completion_percentage": null,
    "raw_seal_sha256": "26bf1acc4b88d1ae10ebb152c5ae6507a65818d20c7898092174b638ca5d74c2",
    "canonical_closure_sha256": "a4a4e01356761307168140caa48ccfe7656e32b5fb35e075ead0aba428655cb3",
    "closure_members": 206,
    "closure_bytes": 7644432,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  },
  "source-world": {
    "complete_inputs": 15,
    "input_bytes": 1039959,
    "raw_seal_sha256": "ccb7dbe71e4ee065facbaa7ac91d5dc8262ad57dff88f1e1d8bbf1466599c2ec",
    "canonical_closure_sha256": "438da0079620dbf630b39dfca4cb549fd453a943e521a092c5226ad59c087946",
    "closure_members": 19,
    "closure_bytes": 1054600,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  }
}
```
