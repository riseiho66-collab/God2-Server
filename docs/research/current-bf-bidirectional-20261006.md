# 當前原生 BF 的三處 C2S 發送與獨立 S2C 接收

同 build verified mapped image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。
原始 bytes、邊界、E8 目標和長度／世界分派表見
`artifacts/integration/packet-connections-20261006/bf-bidirectional-static-v1.json`。
此輪是靜態來源工作，沒有建置、測試、客戶端執行、資料庫寫入或部署。

原生 `.text` 的 `842E4`、`CFC87`、`CFE77` 都直接呼叫 queue
`132E0`，傳入 opcode BF 和 8-byte body，故 C2S logical size 為 9。
`842E4` 讀取 UI child `+3AE48` 暫存的八個位元組，是對話框確認路徑；
另兩處從選定記錄和 UI 狀態構造本地 body。
`current-daily-quest-lifecycle-20260927.md` 已把每日面板的購買按鈕
`15/2C` 與確認對話框32連到 BF，但它不授權價格、存量、成本、
交易或任意其他 BF 變體。此輪純 codec 保留原樣八位元組，不把
所有 producer 強制解釋為同一種購買。

S2C BF 在原生長度表為 29-byte logical；世界 dispatch `6B22B`
走獨立的 `472680` 路徑。相同 opcode 不證明這是上述任一請求的
回覆；S2C body 欄位和 consumer 的遊戲效果還需要進一步還原。

正式來源新增 `RecoveredBFRequest` 雙方向純格式與獨立
`RecoveredWorldRecords`／`Session` 預設 false 解析旗標。
`Application` 沒有開啟或處理它；持有商品及貨幣、原生價格與交易規則、
Lua、SQLite 原子狀態、S2C 因果回覆及失敗重試都未接通。
因此 BF 在封包帳本是**格式與停用解析**，不是已完成的遊戲分支。

後續已追出 S2C BF 依賴先前 S2C BE 建立的 UI 分區列表及格位。
消費器欄位與邊界詳見 `current-bf-s2c-panel-20261006.md`；
此依賴仍不構成 C2S BF 購買與 S2C BF 更新的因果配對。
