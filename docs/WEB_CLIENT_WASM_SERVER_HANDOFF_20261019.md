# C++／WASM 網頁客戶端與台服服務端核對（2026-10-19）

本文件來自實際源碼核查；客戶端由 God2-WebClient-Main 持續修改，本輪只讀、不凍結也不修改對方工作樹。核查快照及每檔雜湊保存在外部 client-source-observation-v2.json；不能把快照當成整個移動中工作樹的建置驗收。

## 改寫與 JS 退役

架構已變為 C++20 瀏覽器平台介面＋C++20 遊戲核心，一起編譯為 WebAssembly。Emscripten 自動橋接只留在忽略的 build/，不手改或提交；不增加手寫 JS／TS 或把 JS 解譯器藏進 WASM。
核查時 migration.json 為209模組：21核心部分移植、188排隊、0完整驗收、0已退役；另有417份凍結參考／工具腳本。這些數量不是遊戲完成率。使用者要求逐步移除 JS：每項 C++ 對應及宿主、資源、完整流程與原生行為驗證完成後，移除舊入口、匯入、發布清單及源碼，保留 Git 歷史；不可先刪掉未移植功能。
現行上傳規則允許驗證過的里程碑推送既有 Private 開發分支；舊版『全部完成才推送』敘述不再是現行限制。本輪未提交或推送客戶端。
既有 LastTest.log 記錄 MSVC6/6、WASM3/3 通過；本輪沒有重跑。既有瀏覽器宿主測試不是帳密／WebSocket／完整遊玩驗收。正式 host/main.cpp 仍顯示未連線，尚未組合 LoginDriver、完整 WorldPort／WorldSession 與遊戲流程。

## 現行傳輸契約

| 項目 | 實際來源與界線 |
| --- | --- |
| Account/L | /tw/native，僅轉送 Application 實際持有的 Account 監聽器 |
| Character/world/G | /tw/native-game，現行只指向單一已持有 G；三分流可信選線橋接尚未完成 |
| 入口 | WebServerPlan 是明確 overload；普通 src/main.cpp 仍呼叫 run_server(config,seconds)，未掛載 gateway |
| 載荷 | masked binary WS／continuation 承載不變的原生位元組串流；message不等於原生packet，不加JSON遊戲協定 |
| 子協定 | 客戶端 attributes.protocols=nullptr；gateway不回覆Sec-WebSocket-Protocol或extension |
| 原生界線 | logical0xA00、frame0xA03；WireStream有半包／合包，chunk上限1MiB |
| 連線 | L/G各自Transport，只fork manifest，不共用已接受seed/key；服務端現用明確固定零種子 recovered profile |
| 限額 | host必須提供Origin、session、IP、速率、queue、message及timeout；message<=16MiB、queue>=65546 |
| 背壓 | browser→native等待async_write；native→browser預留65546並暫停讀取；單次native讀取最多65536 |
| 瀏覽器送出 | binary，bufferedAmount上限1MiB；每Transport有私有generation/token與連線狀態 |
| WS／WSS | 客戶端遠端要求WSS，WS限loopback／localhost；gateway僅loopback明文WS，公開TLS反代／憑證與部署未驗收 |
| 身分 | Origin不是登入或玩法權限；反代來源IP限額不等於真實玩家IP限額 |
| 目的地 | 只由已持有listener的bound endpoint建立，不接受任意瀏覽器host／port／query；目前不能提供已部署URL或猜預設port |

語言改寫不改PC原生封包欄位、順序、權威核心、帳號與存檔。Gateway不解密、不驗證帳號、不改opcode；服務端仍是C++／Lua權威。編碼公式同族的源碼比對不代表實際seed／manifest／登入互通已驗收。

## 具體缺口與後續串接

1. 客戶端完整 WorldPort prepare／bind_entry／Main、WorldSession、原生操作／時鐘／FP、渲染與UI、戰鬥、音訊及清理仍待接線。純核心、離線資源或空白GPU入口不能算可玩。
2. 新 Credentials::create 僅接受0x21..0x7e ASCII，username<=23 bytes、password<=131 bytes。服務端 RecoveredC2S0002 為176-byte frame／173-byte logical，含L opcode4或G opcode0；帳號位於logical1..23、24為NUL，密碼25..155、156為NUL；167維持0xc8，165..166設定word<1000。RecoveredAccountLogin保留原始帳號位元組成namespaced hex，驗證原始密碼位元組；不強制UTF8／CP950／CP936，不自動轉換非ASCII身分。只有整個帳號皆ASCII才做舊相容case-fold，不能改Big5／GBK尾碼。因此新版入口目前無法送出既有非ASCII帳密。需由客戶端接原生輸入／編碼的無損byte builder，不可改服務端身分、放寬原生欄寬或截斷。UI實際編碼要由原生輸入來源確立，不能由顯示簡繁猜測。
3. LoginDriver目前固定account_endpoint／game_endpoint；三分流選擇尚未對應WS世界目的地。Application對三分流TwWorld Web route明確拒絕。必須綁定實際L發行的選擇／名單血緣、真實bound G與角色占用；A6／07 route bytes本身不是channel authority，不可猜新增query或任意TCP代理。
4. 私有generation避免本機舊回呼碰新Session，但不等於網路重放防護、完整存檔交接或WASM防逆向完成。round497只有callback-clean03；失敗角色占用quarantine、PK持久復原、目標入場與六向切換仍OPEN。
5. 全來源接通後才依集中驗證階段聯測：L/G握手、非ASCII帳密、選角入場、多分頁帳號、半包合包、WS背壓／關閉／重連、六向切換及原版功能與體感。

本輪遵守服務端PHASE1：未建置、執行測試、codec、遊戲、正式帳密、DB SQL、schema、migration或部署。只讀客戶端交接 integration/WASM_SERVER_HANDOFF_20261019.md；沒有向其他chat發送訊息。純源碼可確立的比對不製造REA執行，未知原生規則仍須依既定REA流程追查。

## 2026-10-21 登入／WorldSession 來源交接增量

客戶端提交 `253477a871a2402e5fb1bd0ddd5abdd83a0f3ed7` 的兩份交接文件與相關
C++ 來源已只讀核對；來源快照位於服務端外部 pass8/coordination 存檔。
Login ready 後有界非同步 FIFO 交 WorldPort，bound／pending 分離，首次 Main
由 Login 私有同步一次性訪問發行。WorldSession 依既有原生長度表處理同 frame
多記錄，73 保留 Remote→Enemy mirror，真正記錄邊界的 S03 退休後段；重入場2A
不重建 Main。這些是來源接線，沒有變更台服原生 bytes、CP950 ready 或 L/G binary WS。

客戶端回報 MSVC7/7、WASM3/3與55項契約檢查，但使用 mock account/game port、
EntryPort與manager handler；服務端沒有重跑。完整真實 EntryPort、地圖／NPC／Main
prefix、Application transaction及正式 host 組合仍未完成，不能宣稱實服登入入場。
後續「接真實地圖／NPC／Main」要求不會把這些 mock 改標為真正來源。

服務端目前只核對源碼：普通 Main 仍未選 WebServerPlan overload，TwWorld web
route 仍只具單一已持有 G 目的地，三分流仍要求尚未完成的可信 selected-channel
bridge。沒有本輪部署或實際 listener／TLS 檢查可證明測試 endpoint 存在，因此
目前沒有可提供或可宣稱已驗收的 L/G WebSocket URL；不猜 port，也不掃描或借用
正式服務。這不表示已證明其他程序沒有啟動，而是本輪沒有該執行證據。

可信選線與完整角色占用、失敗隔離、目標入場和六向切換缺口繼續保留。
集中聯測的前提是雙方完成實際宿主／EntryPort／Application、服務端受控 gateway
掛載與 endpoint 發行、選線及角色占用來源，並另行進入獲准的集中驗證階段。
之後才測真正 L/G、半包／合包、原生編碼、多分頁、背壓／關閉／重連、分流及
原版體感。未使用正式帳密；沒有因交接啟動服務、DB、codec、遊戲或部署。
