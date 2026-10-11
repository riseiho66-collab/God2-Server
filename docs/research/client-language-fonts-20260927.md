# 客戶端依語言選用字體

## 2026-10-06 目前狀態：已依使用者要求還原原生字型

取消微軟正黑體／微軟雅黑及自訂自然比例：正式God2.exe的00532918與00538DC6
已回復原生CreateFontIndirectA／CreateFontA，與目前保留的原生God2.unpacked.exe
相同位置位元組一致。僅改12 bytes，其餘客戶端位元組保留；.fontcfg區段保留，
這兩個入口不再呼叫它。主播樣式、IME、繁簡轉換及CN客戶端均未改動。
下列發布/啟用狀態為歷史；CUSTOM-0055目前停用，後續不得自行重套。
恢復前完整EXE、候選與紀錄：`../../artifacts/releases/native-font-restore-20261006`。
本輪未建置、啟動遊戲或執行畫面驗收。下次正常啟動採原生字型呼叫。

使用者指定：繁體使用微軟正黑體，簡體使用微軟雅黑；主播特權聊天訊息加粗，
普通玩家不加粗。名字沿用正常字重。這是自訂外觀，不是還原原生數值。

## 實作範圍

客戶端原本兩個 GDI 字型建立呼叫：

* `00532918` → `CreateFontIndirectA`。
* `00538DC6` → `CreateFontA`，所屬完整函式 `00538D70`。

新增內嵌 `.fontcfg` C++ 區段，兩個呼叫轉成 Unicode `CreateFontIndirectW`。
沿用原生高度、寬度、字重與其他樣式，僅依該程序的 `GetACP()` 選定字族和字集：
936 → Microsoft YaHei / GB2312_CHARSET；950 → Microsoft JhengHei /
CHINESEBIG5_CHARSET。兩個語言程序互不修改對方的字型或 Windows 全域設定。

主播訊息現有 `FW_BOLD` 繪製區段會繼承新字族；普通聊天沒有進入該粗體區段。
未替換圖檔內既有文字，未修改登入、中文輸入流程、聊天封包與服務端資料。

## 建置和驗證

* `../Launcher-src/launcher-native/src/Support/ClientFonts.cpp`
* `../Launcher-src/launcher-native/tools/Build-ClientFonts.py`
* `tools/strike_lab/private_client_fonts_20260927.py`

建置以已部署主播版本 SHA256
`fd6cc7d07ad494fdeafc25640b6f5edff0bf31e1af15c5f5dba529bc9f67766f` 為基底，
只在隔離候選中變更兩處呼叫、PE 區段表與測試埠。
實際 Windows 字型以 `GetTextFaceW` 查驗，而非僅檢查要求的字串。
繁體 Windows 回傳本地名稱「微軟正黑體」，英文名稱與本地名稱均是合法別名。

隔離驗收使用同一 EXE、兩個 Locale Emulator 語言設定與兩個角色，
保留帳號原有資料。完整通過與正式部署結果以本檔後續記錄及 release receipt 為準；
不得用建置成功代替簡繁雙開與普通／特權聊天驗收。

## 已部署驗收

`artifacts/playtests/private-client-fonts-20260927-03/run-result.json` 完整通過。
同一個候選 EXE 的兩個程序分別回報：

* 繁體 CP950：實際字族「微軟正黑體」，原始字重 0（FW_DONTCARE，未要求粗體）。
* 簡體 CP936：實際字族 Microsoft YaHei，原始字重 0。

雙方互收「中文123／中文456」，可見聊天環及歷史環、原生泡泡皆通過。
三種主播樣式及特權 0 恢復普通聊天通過；渲染計數與截圖一併留存。
測試程序已關閉、輸入桌面未切換，正式 DB、EXE 與隔離候選於測試期間保持原樣。

正式發布：`artifacts/releases/client-fonts-20260927-01/verification.json`。
唯一正式 `God2.exe` 的 SHA256 為
`7a541b63c7333ef3790640ebfbd17d7e5c4dfedd80c8d14b0c38cdad6cca23bf`。
登入器 `/verify-client` 回傳 0；服務端 PID31624 維持運作，未改動帳號或存檔。
本機實測不等於已在另一台 Windows 10 實機驗收。

## 使用者要求還原

使用者認為新字體過扁，已還原部署前的 God2.exe，SHA256 fd6cc7d07ad494fdeafc25640b6f5edff0bf31e1af15c5f5dba529bc9f67766f。主播圖標、訊息粗體與配色保留，登入器驗證通過，服務端與資料庫未修改。CUSTOM-0055 現已停用，不得於後續發布自行重新套用。

## 後續明確要求：重新採用自然比例版本

使用者其後明確要求繁體用微軟正黑體、簡體用微軟雅黑，並要求正常比例。
本次重新啟用使用 `lfWidth=0`、`lfHeight=-12`，取代舊版強制寬 6／高 12 的配置。
`private-vector-fonts-20260927-06` 驗收通過後已發布至
`artifacts/releases/streamer-vector-natural-fonts-20260927-01`。
該版兩程序實際字族與字寬高均驗證，主播訊息 `GetTextMetricsW.tmWeight=700`，
一般名稱 `tmWeight=400`。頭頂圖標也補上自己的角色物件區。

後續淺黑外框／亮紅設定與最新發布證據見
`streamer-vector-natural-fonts-20260927.md`。先前的「停用」是歷史狀態，
使用者此次明確指示已重新授權自然比例版本；不得還原成被否決的固定寬度版本。
