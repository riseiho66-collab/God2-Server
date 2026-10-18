# 台服客戶端名片錯誤處理補丁（CUSTOM-0157）

`tw_name_card_guard.cpp` 是 C++20 離線產生器，與服務端核心分開編譯。
只接受完整 SHA256 鎖定的現用台服 EXE，新增 `.cardfix` 的兩處防護，
保留入口、data directories、字型／IME／技能及所有不相關原始位元組。
原 optional-header CheckSum 保留，不把它當成完整性證明；完整性使用 SHA256。

```powershell
cmake -S tools/client_compat -B build-map-transfer-repair/client-compat -A x64
cmake --build build-map-transfer-repair/client-compat --config Release -- /m:2
build-map-transfer-repair/client-compat/Release/god2-tw-name-card-guard.exe --client-exe C:/Users/risei/Desktop/God2/God2/God2.exe --output-root C:/Users/risei/Desktop/God2/God2-Server/artifacts/releases/tw-name-card-guard-20261018
```

輸出為 `God2.before.exe`、`God2.name-card-guard.exe` 及 `manifest.json`；
來源客戶端不會被改寫。未知雜湊、非預期 PE／call-site、既有輸出目錄均拒絕。
新目錄先完整寫入工具自有 pending 目錄，成功後才發布。

經原始機器碼黑箱驗證後，使用 `Install-TwNameCardGuard.ps1`，
參數 `CandidateExe`、`OriginalBackup`、`BlackBoxReport`、`ReceiptPath` 都需明確指定。
安裝器檢查測試收據與三份檔案的 SHA256，獨占開啟現用客戶端後才寫入；
寫入失敗會在同一檔案鎖內回復原始 bytes。
不開資料庫、不重啟服務端、不新增名片網站、不傳送實際帳密或暱稱。

原版 REA 證據、測試界線及交付結果見
`docs/research/tw-name-card-crash-20261018.md`。
