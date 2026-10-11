# 同版原生 S2C BE 建立列表／BF 更新格位

續前次 C2S BF 請求盤點；本輪只恢復另一方向的列表及更新消費器。
verified mapped image SHA256 為
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`，
原始 bytes、長度表、world dispatch 及有界反組譯在
`artifacts/integration/packet-connections-20261006/bf-s2c-panel-static-v2.json`。
沒有執行客戶端、測試、建置、正式資料庫或服務更新。

S2C `BE` 長度表回傳可變長 `-2`，世界 `6B219→472560`。
logical bytes 為 `BE, total_size:u16LE, count:u8, region:u8,
row[count][24]`，因此 `total_size=5+24×count`。原 consumer
對宣告長度與此公式不合的分支只記診斷後繼續；本端 codec 才嚴格
拒絕不一致資料。原 v1 靜態摘要把這項比較寫成必須成立，
現以 v2 更正，舊原始 bytes 證據保留。
在 state byte `+855ED==2` 才處理，將 region 存在 `+839A4`、
清除該 region 的 1200-byte UI 區（50×24），再逐列以 row byte1
作格位索引。它複製 row bytes4..23 到格位 bytes4..23，並將
row bytes0..1 存入格位 bytes0..1；本地欄位用途尚未完整定位。

S2C `BF` 為固定 29-byte，世界 `6B22B→472680`。body byte0
必須匹配已存 region；body byte5 是格位，body bytes8..27 的
20-byte 資料覆寫該格位 bytes4..23，body bytes4..5 覆寫格位
bytes0..1。只見更新**已建立區域**的客戶端呈現；未見它從零
建立列表。欄位與 C2S BF 的購買事務因果關係依然未證。

這兩個 consumer 的區域／格位檢查部分只是診斷紀錄，後續索引
寫入仍可發生。正式來源 `RecoveredBFPanel` 提供精確 raw
列表／更新 codec 與發送前的記憶體索引界線：region0..5、
slot0..49、BE row count≤50。這只是防止本端產生越界呈現資料，
沒有給商品、貨幣、價格、交易或 S2C 發包授權。`Application`
仍無 BE/BF 發送路徑，C2S BF 的解析旗標仍預設 false。
