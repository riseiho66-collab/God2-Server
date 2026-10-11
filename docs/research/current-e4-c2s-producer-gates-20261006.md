# 原生 C2S E4 的四條 UI producer 分支

同日續查：這些 UI 旗標的已知上游是 **S2C FD subtype12**；
`FB／FC` 雖共用第一跳 `858B0`，但不進 FD 的 subtype switch。
見 `docs/research/current-fd12-e4-panel-20261006.md`。

本輪只讀釘定原生映像 SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。有界指令與 bytes 在 [`e4-producer-gates-v5.json`](../../artifacts/integration/packet-connections-20261006/e4-producer-gates-v5.json)。S2C E4 已定位為既有 E3 戰寵列的條件式 delta，見 `current-e4-pet1-cache-link-20261006.md`；本輪追的是另一方向的發送門檻。

外層 `82B56..82B74` 只有在事件控制 ID 等於分派 owner 的 `+232E0E` 時，才對 UI 物件呼叫 `95B30`。此值是**控制 ID**，沒有證據可作戰寵槽位或實例身分。`95B30` 在相應事件旗標下送出 operation0/1/2；operation3 位於另一段相鄰函式的複合 UI 流程。每筆皆是 logical2 `E4,operationBYTE`：

| operation | 原生 queue RVA | 可見本地條件 |
|---|---|---|
| `0` | `95BB3` | UI `+26128 == 1`；先呼 `95D50(0)`，該函式將此旗標清為 0，再發 `E4 00` |
| `1` | `95BFC` | UI `+26124 == 1` 且 `+26127 == 0` |
| `2` | `95C46` | UI `+26126 == 1` 且 `+26127 == 0` |
| `3` | `95B1B` | 另一段複合旗標／訊息流程後，掃 UI `+26129..+26130` 八 bytes；任一非零時發 `E4 03` |

operation3 上游 `95A49..95ADE` 依多個 UI 旗標選分支並顯示本地訊息，`95AE3..95AFE` 才檢查八個選項旗標；它不是與前三個按鈕相同的單一門檻。因此 C2S `0..3` 和 S2C E4 的四維 bonus 分流 `0..3` **不能僅憑數值相同推定一對一因果**。這四條 producer 也都沒有傳送 pet slot、metadata key、instance 或 revision；目前尚未證明服務端應由哪個 owner-bound 戰寵狀態推得操作目標。

`RecoveredE4Control` 保留原始 operation，世界 parser 仍預設關閉；Application 沒有 E4 狀態變更、Lua 規則、原子儲存或 S2C 發送。要接完整路徑，先釘定 UI 選取與服務端擁有的 E3/FB 實例關係，再找原始加點／效果規則及真正 producer。這輪新增完整路徑 0；沒有 build、測試、客戶端執行或部署。
