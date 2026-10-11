# 當前原生 S2C WORLD 第一跳與 GM 工具橋接

本輪只對釘定 SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` 的原生映像作靜態追蹤。前輪路徑帳本未分類的 152 個有長度、WORLD 非預設 S2C 入口中，145 個在有界分派片段內有直接 `call`，7 個（`00 03 3A 40 5A 6C 72`）沒有；共定位 153 個不同直接呼叫目標、9 個被多處呼叫的目標。這只是第一跳工作佇列，直接呼叫不等於遊戲功能，片段內沒有 `call` 也不等於沒有 consumer。原始逐入口證據在 [`s2c-unclassified-first-hops-v1.json`](../../artifacts/integration/packet-connections-20261006/s2c-unclassified-first-hops-v1.json)。

其中 `7B 7C 7D 7E 7F 80 81 F6` 共用 WORLD 分派 `6AD6D`，進入 `6B9D0` 的 opcode switch。原生字串為 `GM Tools FS2`；該函式依 opcode 配置轉送長度，然後走形如向外部視窗送 `0x4A` 訊息及 COPYDATA 結構的路徑。匯入函式身分尚未獨立解析，所以「視窗訊息橋接」是由呼叫形狀推論；外部視窗是否存在、能否接收與如何解讀均未證。精確分支位址及 bytes 在 [`s2c-gm-tool-bridge-v1.json`](../../artifacts/integration/packet-connections-20261006/s2c-gm-tool-bridge-v1.json)。

| S2C opcode | 邏輯長度 | 橋接 payload 長度 |
|---|---:|---:|
| `7B` | 41 | 40 |
| `7C` | 29 | 28 |
| `7D` | 25 | 24 |
| `7E` | 25 | 24 |
| `7F` | 17 | 16 |
| `80` | 25 | 24 |
| `81` | 261 | 260 |
| `F6` | 29 | 28 |

這八個 opcode 的原生長度及外部橋接分類已進入路徑帳本，但 S2C payload 欄位、伺服器 producer、外部工具行為及任何 C2S 因果關係均未合格。它們不是已串接的遊戲功能，也不能從原生封包盤點刪掉。本輪沒有 build、測試、客戶端執行、正式服務變更或資料庫寫入。
