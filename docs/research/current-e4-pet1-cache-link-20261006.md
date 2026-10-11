# 原生 S2C E4 與 E3 戰寵快取共用列

本輪對釘定映像 SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` 作靜態切片，保留原始 bytes／指令及 bonus switch table 於 [`e4-pet1-cache-link-v3.json`](../../artifacts/integration/packet-connections-20261006/e4-pet1-cache-link-v3.json)。此前 `current-e4-bidirectional-20261006.md` 已釘定 C2S logical2 的 operation0..3 與獨立 S2C logical17；本輪恢復 S2C 接收端的具體客戶端快取身分及欄位。

`E3` 戰寵快照 consumer `A2B70` 限槽位 42..44，並以 `A29A0` 檢查 metadata key。其 `A2BAF..A2BC7` 把 13 個 DWORD 複製到 `UI+9E50+slot*52`。S2C `E4` consumer `A3180` 同樣以 `A2980` 限槽位 42..44，算出 `UI+A6D8+(slot-42)*52`，檢查該列 `+1C` 的 metadata key、列 `+26` 的 slot，再經 `A29A0` 查 metadata。因 `9E50+42*52=A6D8`，兩條計算在三個槽位上指向**同一快取列**。這是 E4 對已存在 E3 戰寵狀態的條件式 delta，不是一般任意 UI 更新。

設 `P` 為 S2C E4 opcode 後的 16-byte body。通過既有列條件時，原生 `A31D2..A3281` 寫入：

| E4 body | 既有 E3 列 | 已見用途 |
|---|---|---|
| `WORD P+0` | `+2` | 最大 HP |
| `WORD P+2` | `+6` | 最大 MP |
| `DWORD P+4` bits 0..11／12..23 | `+8`／`+C` 低 12 位 | 物理攻擊／物理防禦 |
| `DWORD P+4` 高 BYTE | 列索引 | 戰寵槽位 42..44 |
| `DWORD P+8` bits 0..11／12..23 | `+10`／`+14` 低 12 位 | 法術攻擊／法術防禦 |
| `DWORD P+8` 高 BYTE | 加點分流 | 0..3 時分別增加力量／體質／智力／速度 bonus；大於 3 時跳過該增加 |
| `WORD P+C` | `+24` | 剩餘點數 |
| `P+E..F` | — | 本接收切片未讀；保留原始位元組 |

低 12 位以外的既有 E3 打包屬性與五行位元在四個攻防 DWORD 中保留。`RecoveredE4Control::UpdateView` 現提供上述唯讀欄位，原始 17 bytes 仍可完整保留；codec 不執行伺服器狀態變更或發送。

C2S E4 的四個 operation0..3 與 S2C E4 的 bonus 分流0..3 範圍相同，這是進一步追因果的強線索，**仍不足以證明一對一回覆**。C2S 不帶槽位、instance 或 revision；服務端必須由已授權的玩家／戰寵狀態推得目標，恢復原始加點條件與計算、Lua 規則、原子儲存及真實 S2C producer 後才能接入 Application。既有 E3／FB 存檔、凍結功能與正式服務均未改動。本輪新增完整串接路徑 0；未 build、測試、客戶端執行或部署。
