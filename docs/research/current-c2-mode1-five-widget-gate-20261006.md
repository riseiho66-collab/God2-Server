# C2 mode1 的五個 UI 槽位門檻，2026-10-06

原生 verified mapped image SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。`B17A2` UI 事件呼叫、`CEDE0..CEF0A` 完整門檻與送包／本地失敗分支的原始 bytes、雜湊及有界反組譯保存於 `artifacts/integration/packet-connections-20261006/c2-mode1-five-widget-gate-v9.json`。沒有建置、測試、執行客戶端或部署。

此 C2S `C2` mode1 producer 要求五個 UI 槽位索引 `+232E74`、`+232DAE`、`+232DB0`、`+232DB2`、`+232DB4` 均非負，且每個槽位的狀態 byte 都含 `0x10`。通過才在 `CEEF6` 送出 logical9 的 C2；八位元組 body 只明確寫入首個 u16 的 mode=1，餘下原始位元組不能推定為零。未通過則走客戶端本地 `4983D0(2)` 分支，不送包。

這條事件沒有讀取 S2C `F5` 建立的 `UI+97C88`／`+97CA4`；後者只在 C2 mode2..6 的已定位來源分支使用。五個 UI 旗標只是客戶端可操作條件，不構成服務端持有權、交易效果或因果 S2C 回覆。正式來源保留 mode1 原始 body 並維持預設關閉的 C2 格式解析；Application 仍不處理。完整雙向遊戲路徑本輪新增0。
