# 當前原生 E4 同號雙向格式與未接的業務路徑

同日續查：S2C `E4` 的「既有 UI row」現已定位為 `E3` 戰寵快照
共用的槽位 `42–44` 快取列，欄位包括最大 HP／MP、雙攻雙防、
剩餘點數與四維加點計數。詳見
`docs/research/current-e4-pet1-cache-link-20261006.md`。原本「同號
不證明 C2S 操作的回覆」的邊界仍成立。

來源為 verified mapped image
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。
原始呼叫、位元組與有界反組譯在
`artifacts/integration/packet-connections-20261006/e4-bidirectional-static-v1.json`。
本輪只做靜態來源與格式編輯；沒有 build、測試、客戶端執行、
正式資料庫寫入或部署。

原生 C2S `E4` 的四個直接 queue 呼叫分別在 `95BB3`、
`95BFC`、`95C46`、`95B1B`，排入**2-byte logical**：
`E4,operationBYTE`，觀察值依序 `0／1／2／3`。
`95B30..95C53` 先依 UI 控制、`+26124/+26126/+26127/+26128`
等本地狀態決定是否發0／1／2；`95AFE` 的分支可能發3。
這些 UI 位元不是伺服器的 owner、成本或效果授權，
操作值尚無原生業務動詞證據。

不同方向的 S2C `E4` 長度表為**17-byte logical**，世界 dispatch
`691C7` 將 body16 傳給 `4A3180`。該 consumer 先從
`body DWORD+4` 的高位元組取得查找鍵，經既有 UI row 條件
後更新其多個欄位；不存在／條件不合時不更新。這只證明
接收格式和本地既有記錄的條件式投影。**同號不證明它是
C2S E4 任一操作的回覆**，也不證明原始服務端狀態或收益規則。

正式來源新增 `RecoveredE4Control` 的 C2S2-byte 原始 codec 和
S2C17-byte 原始 codec。`RecoveredWorldRecords` 與 `Session`
另有 `e4_controls` 獨立旗標，預設 false；`Application` 不設定
亦不處理，故不會改變既有凍結功能或正式服務。
仍缺各操作前置、被選實例及 owner/revision、Lua 遊戲規則、
持久化、真正 S2C 回覆／推送與重登重試時序。
本輪 E4 只能列為**格式及停用解析來源，功能未接通**。
