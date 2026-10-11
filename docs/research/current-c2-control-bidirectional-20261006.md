# C2 雙方向分離：F5 面板控制與獨立 UI 更新，2026-10-06

同版 verified native image SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。C2S 原始 bytes、三處直接 queue caller、七項 UI jump table 見 `artifacts/integration/packet-connections-20261006/orange-shop-c2-controls-v7.json`；獨立 S2C 長度表、WORLD 分派與 consumer 見 `artifacts/integration/packet-connections-20261006/c2-same-opcode-receiver-v8.json`。本輪沒有建置、測試、客戶端執行或部署。

C2S `C2` logical 9 bytes、body 8 bytes。原生直接 queue 點 `CEEF6`、`D01F8`、`D0300`；後者是多個 UI case 共用的送包點。已觀察六個 mode u16：

| mode | 生產者來源 | 已寫入 body 欄位 |
|---|---|---|
| 1 | `CEEF6` 的另一個 UI 旗標門檻 | +0 u16=1；其餘原生局部範圍未賦值 |
| 2 | `D0300` 共用點 | +0=2、+4=`F5` type7 建立的 `UI+97C88`、+6=選定 bit 序號 |
| 3 | 兩個 UI case，`D0300` | +0=3、+4=`F5` type8 的 `UI+97CA4`、+6=`FFFF` 或 `0001` |
| 4 | `D0300` | +0=4、+4=`F5` type7 的 `UI+97C88` |
| 5 | `D0300` | +0=5 |
| 6 | `D01F8` | +0=6、+4=`F5` type8 的 `UI+97CA4`；+97CA6另存於本地狀態 |

mode1的上游 `CEDE0..CEF0A` 另要求五個 UI 槽位有效且均有 `0x10` 旗標；完整證據見 `current-c2-mode1-five-widget-gate-20261006.md`。此模式不讀 F5 欄位，不能冒稱同一 OrangeShop 交易。mode2..6 的 F5 欄位關係是原生資料來源，不等於 C2 的服務端操作權限或回覆因果。多個 body 位置在送出前沒有明確寫入；`RecoveredC2Control` 保留全部原始8位元組，新增預設關閉的 WORLD 格式解析，但 Application 不啟用或處理 C2。

S2C 同號 `C2` 是固定 logical 3 bytes，WORLD `6B261→C2E20`。bounded consumer 不讀取兩個 body 位元組，轉而刷新 `8AA20/8AA24`、`232DF8` 一類 UI 狀態，未見對上述 F5／OrangeShop 欄位的處理。正式來源以獨立 `RecoveredS2CC2Update` codec 保留兩個 opaque bytes，沒有建立同號的請求回覆關係，也沒有發包。C2S mode1的持有情境、mode2..6的操作效果、所需 owner/列表/選取狀態、Lua、持久化及真正 S2C 結果仍缺；新增完整遊戲路徑0。
