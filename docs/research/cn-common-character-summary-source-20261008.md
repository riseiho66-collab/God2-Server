# CN 共用角色名字 → 原生 07 摘要來源

本輪為 PHASE1 靜態檔案恢復及 C++ 來源串接。未建置、測試、執行客戶端／服務端／C++ 編碼器／Windows API，未讀取資料庫、遷移或部署。前輪版本握手來源成果保留；上一個單純進度回覆沒有新增串接，本輪重新從現有來源採取實際動作。

## 已有資料與原生邊界

實際 `RecoveredCharacterRepository::list_for_account` 是登入／選角使用的共用後端。SQLite 實作讀取 `recovered_characters` 的 ID、account、slot、完整 40-byte profile、name_bytes、created_at、name_codepage 和 streamer_privilege；既有 reader 比對 name_bytes 與 profile 的首段。Account 模型只有身分、帳號、password_hash 與 created_at，沒有原生 40-byte 帳號 metadata 或 16-byte billing。一般 Character 模型的 CUSTOM 預設值不能充當 CN 選角／權益資料。本輪只讀這些原始碼，沒有開啟 DB。

已定位的 CN 07 是 75 bytes：opcode、count、flags 及兩個 36-byte row。00481640 保存完整 74-byte payload，另將每個 row 的 NUL 結尾名字複製到本地 cache；00443640 從同一摘要的 row 名字供給 `%s` 面板文字。00443080 使用獨立外觀欄位及資源，不能從共用 profile 首段名字推導它们。新保存上述三個 pinned PE metadata envelope 的 primary bytes／assembly／navigation C，共 3,147 bytes；不是完整 CFG 或所有呼叫者閉合宣告。命名提示 `%…%` 分支沿用既有封存證據與 `CnCharacterSummary` helper，未改舊基準。

## 本輪實際來源產生端

新增 `SharedCommonCharacterSummarySource`。它在同一 game owner 上讀取完整共用 account roots，再交給實際 native metadata owner 準備帶有 account／target、非零 revision、完整 native 07 和有序 common character ID mapping 的 move-only 來源。mapping 的 native slot 仍由實際 07 取得，不由 common slot、名字或 ID 推算；active rows 是實際來源指定的子集合，沒有「帳號內全部可見」預設。

每個 row 必須明確選擇 `CommonIdentity` 或 `NativePromptMarker`。CommonIdentity 依實際 profile 原始名字和 name_codepage，沿用既有 `OwnedCharacterNameText` 的精確 round-trip 邊界：CP950／CP936 解碼成原始 Unicode，再編為 CN CP936。編碼未綁定的 0 只接受既有 ASCII 邊界；不猜 ACP。不轉繁簡、不做同名查表、不截字、不替換不可表示的字。這個共用模型目前支援的名字邊界是 14 encoded bytes；並未宣稱 CN 所有 15-byte／canonicalization 變體已串接。

產生端只覆寫 active row 的已知名字及一個 NUL。新 NUL 之後的原始 bytes、flags、row18、slot／轉生 bits、等級、職業、portrait、appearance、location 和 inactive row 全部來自並保留實際 native input，不建立零模板。NativePromptMarker 要求 native input 已有精確提示標記，保留其完整名字欄位；不從共用名字猜測更名權限。CommonIdentity 若投影結果會觸發提示標記，則拒絕，避免把普通名字投影偷偷變成命名流程。

實際 issuer 的必要 observing Current 會看到 source revision、完整 native input、完整 outgoing 07、全部有序 mapping 與精確 common roots。產生前後、Current 前後再次讀同一後端比對完整 roots；來源 stale 或缺失就不產生摘要。輸出直接形成既有 private `NativeSummary`，實際 A6 選角流程沿用完整 roots／native issuer 的 BeforePublish、QueueAccepted 和 NameSubmission 檢查與原有 publication barrier。這是 serial owner 的來源觀察，不是跨程序原子交易、官方可見性規則或網路送達證明。

## 登入流程接入

`SharedLoginSources.common_character_summaries` 是明確的可選來源設定，factory 只使用實際 `Context.characters`，不另開資料庫。支援現有完整 account supplier，或現有 issued-account Profile Prepare；所選 supplier 的 summaries 必須留空，組合流程接入此實際 producer。兩個來源同時出現會拒絕，而不是任選其一。issued-account 分支在原有 profile／CNG key 組裝前接入必要 summaries；原認證、billing、catalog、期限及 key 組裝規則不變。未選此設定時，既有 full-summary supplier 路徑維持。

這是共用角色名字 producer 1、既有 A6／07 source composition binding 1。新 opcode、phase binding、完整 owner chain、完整雙向路徑均為 0。全遊戲總數、完成數及百分比仍為 null。

## 尚未完成

實際 native 07 metadata／可見性／revision owner 仍未配置；這個 source 不憑共用名字補出外觀、位置或旗標。帳號 metadata40／billing16／權益／期限、group billing／load／location、完整世界入口供應端及正式 Application hosting 仍有缺口。命名規則、其他名字長度變體、durable receipt／跨程序重播與所有遊戲系統仍要繼續。

凍結的帳號存檔、認證、聊天、IME、頭像、字體、繁簡轉換、等級與客戶端／資源保持；未修改既有 SQLite reader、text codec、07 view、D3 mutation、wire layout 或資料表。TW／CN／PC／web／WSS、共用世界及全部玩法、數值擴充與背包 99 的完整目標持續 ACTIVE／INCOMPLETE。完成全部來源串接後才集中全面測試、修復與發布。
