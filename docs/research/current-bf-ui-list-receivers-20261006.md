# BF 來源列表的原生 S2C EE／F3，2026-10-06

同版 verified native image SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` 的長度葉、WORLD 分派、consumer 原始 bytes 與有界反組譯保存在 `artifacts/integration/packet-connections-20261006/bf-ui-list-receivers-v4.json`。本輪沒有建置、測試、客戶端執行、正式資料庫操作或部署。

S2C `EE` 在長度表是可變長，WORLD `690EE→CDF90`。它的 logical header 為 9 bytes：opcode、total_size:u16、小欄位:u16、三個列群數量 `logical[5]／[6]／[8]` 和 `logical[7]` 類別。類別1..4會將 UI 模式設為偶數0/2/4/6。後面是三群相接的6-byte列；原生 consumer 檢查 `total_size-9 == 6×(三群數量和)`，然後將列逐筆複製到 `UI+96980`，正是 C2S BF 偶數模式 `CFE77` 選取的6-byte列表。原生遇長度不符只記診斷仍繼續；本端 source codec 為了不發出不一致封包而嚴格限制。該列表在下一個 UI 欄位前最多容納90筆。

S2C `F3` 也是可變長，WORLD `69112→CE290`。相同 header 的類別1..4設 UI 模式為奇數1/3/5/7，三群數量仍在 logical[5]／[6]／[8]。第一群每筆為8-byte前綴，前綴 byte4 是 N，後接 N 個 u16 和 N 個 u8；原生展開時把 key/value 寫入48-byte目的列起始、N個u16寫在列+8、N個u8寫在列+34。第二及第三群各是6-byte壓縮列，展開至48-byte目的列的 key/value 與少數狀態欄位。目的列表 `UI+96BA4` 正是 C2S BF 奇數模式 `CFC87` 使用的來源。下一個 UI 欄位前最多容納106筆；N>14會越過48-byte目的列。原生 consumer 對可變長資料先複製到約0x800-byte本地區域，沒有充分的發送安全保證；本端 codec 限制長度、列數與逐筆展開邊界。

鄰近的 S2C `F5` 是固定29-byte，WORLD `69100→CE140`，更新相關的 `UI+97C84/97CA0` 記錄；S2C `EF` 是固定3-byte，WORLD `69124→D19A0`，更新 `UI+9697A` 數量。兩者均未填入上述兩個列陣列，不能把它們併作 EE/F3 的列來源；其完整遊戲語義與回覆因果仍待追。

`src/protocol/RecoveredBFSourceLists.h` 提供 EE/F3 的 raw-preserving decode 與有界 encode，尚未接入 Application。這證明 `BF` 的兩種 UI 選取 key/value 是由服務端發來的 EE/F3 列表提供，**不**證明它們屬於 S2C BE/BF 的50格面板，也不證明 BF 交易的持有權、成本、結果、錯誤或回覆。沒有權威列表產生路徑及完整 C2S BF 事務，新增完整雙向遊戲路徑仍為0。
