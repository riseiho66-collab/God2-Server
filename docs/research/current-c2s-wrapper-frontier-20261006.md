# C2S22／31／68 呼叫邊界與另一個 35 raw 變體候選

基於同一 verified mapped image
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。
有界原始 bytes、指令、`68A30` 分流表及 `.text` 直接 E8 掃描
保存在 `artifacts/integration/packet-connections-20261006/c2s-wrapper-frontier-v1.json`。
本輪只做靜態逆向和來源註記；未執行客戶端、build、測試或部署。

`68A30` 依輸入 `1F..35` 經 `68AC0` byte selector 與
`68AAC` 目標表分流。此區間只有 `1F→1F 00`、
`22→22 00`、`23→23 00`、`35→35+16-byte body` 四個
非 default 分支。對 `35`，`68A87..68AA3` 將16-byte
local buffer 傳給原生 queue `132E0`，但在本地只明確寫入
**body offset8..11 = `FF FF FF FF`**；其餘12個 payload bytes
沒有由此函式初始化。不能把它記成全 `FF` 控制包，也不能
套用現有 `RecoveredBattleCommand` 的 action1／2／0B parser。
在 `.text` 中未找到直接 E8 呼叫 `68A30`；這不排除間接調用，
但目前**可達性和狀態均未證明**，只登記靜態 raw 變體候選。

`BF433..BF471` 的 C2S31 直呼先對三個既有 UI row 各檢查
bit8；任何一個命中就離開，通過後用 `961A0(31,1)` 入列
`31 00` 並接續多項本地清理。這些 row 不是服務端權限資料。
`C3750..C39BD` 有四處 `961A0(68,1)` 呼叫，受 UI 控制
與選取 row 的 bit10 等不同條件限制；包裝器本身還會依
`+8AA4C/+F4` 低兩位改走本地訊息路徑。因此不是每個
呼叫點都會真的送出 `68 00`。`22／31／68` 的服務端功能、
階段及真正 S2C 因果回覆仍未知；同號 S2C 不能直接配對。

正式來源僅在 `RecoveredBattleCommand` 註明額外35候選與拒絕
混淆的邊界；沒有為22／31／68裝入空 handler或任意 ACK。
下一步需要沿 `68A30` 的間接呼叫／事件註冊，以及31／68
發送前後的世界狀態與原生 S2C consumer，建立可授權的路徑。

後續對 verified mapped image 的 `.text` 進一步掃描 E8/E9、
near/short 條件跳轉至 `68A30`，並在整個映像尋找其絕對 VA
DWORD，都沒有找到入邊。這只收窄**靜態可見**呼叫來源；
計算出的函式位址、間接 call 或動態事件註冊仍可能存在。
因此不提升35 raw 候選的可達性或完成狀態。

## 2026-10-06 correction to the C2S31 tail-only count

The earlier "three UI rows" count above was limited to the `BF433..BF471`
tail. The full aligned native function `BF300..BF505` first requires one
selected row's `0x10` flag, then checks **six** rows' `0x08` flags before
calling the wrapper. Preserve the earlier wording as historical scope; use
`current-wrapper-ui-gates-20261006.md` and
`wrapper-ui-context-static-v3.json` for the current gate inventory. This
correction changes producer-gate evidence, not server connectivity counts.
