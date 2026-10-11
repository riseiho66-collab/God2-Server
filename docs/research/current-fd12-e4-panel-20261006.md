# S2C FD subtype12 與 C2S E4 的上游 UI 狀態

本輪只讀釘定原生映像 SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。分派、switch table、case 與旗標複製的原始 bytes 在 [`fd12-e4-panel-frontier-v1.json`](../../artifacts/integration/packet-connections-20261006/fd12-e4-panel-frontier-v1.json)。`S2C FD` 是 u16 可變長度、多 subtype opcode；這裡只恢復 subtype12 所需的最小已讀前綴，不把它與既有每日面板 subtype2 混合。

WORLD case `69245` 以識別值 `FD` 呼叫 `858B0`。該函式只在識別值等於 `FD` 時，以 logical byte3 作 subtype index；switch table 的 index12 指向 `85BBE`。`S2C FB／FC` 雖也呼叫 `858B0`，傳入的識別值不同，**不進這個 FD subtype switch**。這修正本輪初查時把共用第一跳誤當成 FB／FC 旗標來源的推論。

設 `L` 為含 opcode 的 logical record。subtype12 case 最遠讀到 `L[25]`，因此目前可安全描述的最小長度為 26 bytes；原始 server producer 的精確長度及其尾段仍未知。`RecoveredFDE4Panel` 只在宣告的 u16 logical 長度等於實際大小、subtype=12、長度至少26時保留完整 bytes，不生成封包或啟用發送。

| logical offset | 原生使用 |
|---|---|
| `L[4..21]` | `4955D0` 在展示模式非零時複製18 bytes 到 UI `+26108..+26119` |
| `L[22]` | 非零走 `4955D0`，並設定本地 `+26127=1`；零走 `495D50(1)`，設定另一按鈕旗標 `+26128=1` |
| `L[23]` | `4955D0` 在非零展示模式下讀取的八位選項遮罩，展開到 `+26129..+26130` |
| `L[24]` | 選擇 `495E10(0/1)`，更新 `+26124`；零值使該旗標為1 |
| `L[25]` | 選擇 `495F40(0/1)`，更新 `+26126`；零值使該旗標為1 |

這些 UI 旗標是 C2S E4 producer 的本地門檻：operation0 讀 `+26128`，operation1/2 讀 `+26124/+26126` 並要求 `+26127==0`，operation3 掃八個選項旗標。`FD12` 因此是 E4 操作可用性的**上游呈現狀態**；它沒有證明原始服務端對選項、戰寵 owner、slot 或成本的權威，也沒有證明 C2S E4 任一操作對應同號 S2C E4 delta。尤其當 `L[22]==0` 時，此切片不清空原先八個選項旗標，不能推斷未觀察的 UI 狀態。

下一步須找出 subtype12 的原始 server producer／完整資料語意，以及 C2S E4 不帶槽位時的已發 offer、已持有 E3/FB instance 與 revision 綁定，再接 C++20 狀態／存檔、Lua 規則及真正回覆。本輪僅接入可讀前綴 codec，完整功能路徑新增0；未 build、測試、client 執行或部署。

## Continued native item-key trace

The [pinned v2 instructions](../../artifacts/integration/packet-connections-20261006/fd12-item-key-frontier-v2.json) show that FD12 logical bytes 4..21 are nine little-endian WORD item-definition keys. Routine 956B0 reads UI+26108+2*index and passes each key to the existing item-definition lookup 459A60, then reads definition fields +116/+118 for UI display. Routine 957F0 selects all nine slots or two six-slot subsets or a three-slot subset according to local UI flags; routine 96070 also selects WORDs from this array. These values are item-definition keys used for presentation, not nine pet attributes. Their item identities, award/cost rules, original server offer authority, exact FD12 length and any E4 request/reply causality remain open. RecoveredFDE4Panel::displayed_item_key(i) exposes only the proven read-only WORD. No build, tests, client run or deployment were performed.
