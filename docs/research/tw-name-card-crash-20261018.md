# 台服人物／好友名片閃退

使用者回報的入口是人物／好友選單的「名片」，並非背包道具。
本次工作只處理這個入口的客戶端失敗路徑，不宣稱好友／交換名片系統完整。

## 原版證據

現用 `God2/God2.exe` SHA256：
`99cde6b666101c0702d712a1a15bf4d83f225a1a521a9c601bd32a6e42debe25`。

REA Ghidra 針對逐頁取自此 EXE 的分析映像恢復下列流程。分析映像只有
46,080 bytes，合成 PE 標頭與 export seeds 不屬於原版符號，不能執行。
原頁逐頁 SHA256、原始 import 覆蓋及完整證據保存在外部
`C:/Users/risei/.codex/artifact-archives/god2-server/20261018/gm-name-card/`。

- `0040E3B0` 的視窗訊息 `040C` 分支位於 `0040E9D0`。
  它複製 `[main+0434]+06C8` 的 URL，並組成包含 account、遊戲暱稱及
  server name 的名片 POST。`0040EAB0` 呼叫 `00410120`，再呼叫 `0040FE70`。
- `0040FE70` 在 `0040FF14` 呼叫 `InternetCrackUrlA`，忽略其失敗結果。
  原程式直接 `_strdup(lpszHostName)`，在 `0040FF3C` 按主機名稱長度寫 NUL；
  空／非法網址可因此寫到 NULL 附近。`00548129` 確認是空輸入返回 NULL
  的 strdup 類函數，不能誤認為單純 size-based malloc。
- `00410120` 已有 HTTP 失敗時返回 NULL 的正常分支，但呼叫者
  `0040EAB5` 未檢查 NULL／空回應便繼續 tokenizer／字串比較，必須一起防護。
- 舊檔 `God2.1DD5ED32D25EEAD.crash.dmp` 的異常是 `C0000005`，
  EIP `0040FF3C`、寫入位址 `00000001`。此檔時間早於本次回報，不能單憑此檔
  宣稱已捕捉使用者本次操作。主模組大小／timestamp 相符不等於完整記憶體雜湊相同。
  限定讀取舊 dump 的參數／返回位址後，確認當時 URL 長度為 0，返回位置
  `0041016C` 與上游 `0040EAB5` 都吻合；未輸出 URL、帳密或暱稱內容。
- `Data2/Client.csvZ` 只有 ClientVersion／SinaErrMsg，沒有 URL；
  `[main+0434]+06C8` 的設定載入來源尚未恢復，不能杜撰設定鍵或官方端點。

REA pseudocode evidence：
`ev_4104c4de774484d0f850afca356cba53023702aabff4a9b9457203c3b3aa48d3`、
`ev_81757499f29a9af0cc6760ebd9e7fe00f715f44a150bd0846175d41d85aaf0d7`、
`ev_be376bb8158db6a16a03d0330a1d9beabaa36b3bf738532011eb779855c78ee8`、
`ev_0757bf2e08855cbff86f0f1fc23dbad8d22612ed9cf115346c8bb28f888bbb37`。

## 修正界線

修補工具只接受上述完整 SHA256 與原始 call-site bytes，離線產生候選 EXE。
防護網址解析失敗及缺少必要 host/path 指標時，按原函數呼叫慣例返回失敗；
HTTP 回應為 NULL 或空字串時，轉到原名片分支的退出位置。
有效結果保留原流程，不新增名片服務端點，也不把實際帳密／暱稱傳往外站。
本修正不改封包、正式資料庫、角色存檔、字型、輸入法或地圖資源。

## 集中驗證與交付結果

2026-10-18 完成 C++20 獨立工具編譯及候選產生。候選／已安裝客戶端 SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
新增 `.cardfix` RX section（RVA `0031A000`）的 108 bytes 防護碼，檔案只增加
512 bytes；原檔範圍內變更 34 bytes，均在兩個跳轉位置及明列的 PE 標頭白名單內。

外部 `name-card-native-blackbox-v1.json`：**21 項通過**，SHA256
`ebffc748adae1036e2d88ecdbde0d4a0f9f4e6d20e4dbb4a9ede6f2e108af967`。
七種輸入各測 `0040FE70`、`00410120` 及名片分支三層原始 x86 機器碼：

| 輸入 | 原版 | 修補版 |
|---|---|---|
| 空網址、非法網址、相對網址 | `0040FF3C` 記憶體錯誤 | 原名片分支安全退出 |
| HTTP／HTTPS 請求失敗 | NULL 進入原回應解析位置 | 安全退出 |
| HTTP 空回應 | 進入原回應解析位置 | 安全退出 |
| 正常非空回應 | 進入原回應解析位置 | 同一路徑、API 參數及回傳狀態一致 |

測試以 Unicorn 執行原始機器碼，使用合成帳號／GM 字串、受限 CRT／HTTP stubs。
唯一真實 WinINet 呼叫為本機 `InternetCrackUrlA` 解析，不實際連線；
比較 host/path/body/header 雜湊、port/flags、callee-saved 暫存器及堆疊回復。
正常回應測到原 tokenizer 呼叫前，不能延伸宣稱整個網站／瀏覽器功能已驗證。
此外，錯誤來源 SHA 與既有輸出目錄的拒絕測試通過；Windows `SEC_IMAGE`
映像映射及映射後防護 bytes 核對通過，沒有執行客戶端入口。

19:07:58 以獨占檔案鎖安裝到現用 `God2/God2.exe`，寫後完整 SHA256 核對成功。
交付收據位於
`artifacts/releases/tw-name-card-guard-20261018/installed.json`；
同目錄 `God2.before.exe` 為唯一此次原檔回復基準，`manifest.json` 是離線產生時的收據。
安裝與收據寫入並非同一個原子交易，應以實際客戶端 SHA256 和交付收據共同核對。

本輪依使用者指定完成內部黑箱測試，未在遊戲視窗中實際點擊名片，也未驗證
外部網站可用性或串接一個新的名片網站。沒有開啟玩家資料庫、重啟服務端、
更動登入設定或讀取真實帳密。下一次正常啟動客戶端使用此防護。
