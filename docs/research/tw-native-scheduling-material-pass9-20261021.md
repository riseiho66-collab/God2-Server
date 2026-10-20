# 原服排程、回合與裝備／變身材料：pass9

日期：2026-10-21；基底 `fc1c7f5cc24ddb4b15589a3eb5d63cfb44e3ec94`。
本輪為 PHASE1 SOURCE_STATIC_ONLY。沒有編譯、執行測試、遊戲／VM、codec、
遊戲 SQL／schema、啟用或部署；測試原碼、代碼審查和正式靜態報告都不是實機驗收。
目前台服原件為 `God2.exe`，SHA256
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
原件、資源、帳號、存檔及既有149c來源釘選未修改。

## 裝備變更後的來源不一致：先拒絕不支援的配置

實際 Application C28 診斷路徑可以在裝備交易中更新外觀並回傳 DA，但沒有替
PvE 保留的完整初始2A、root40與 Catalog Fight profile 建立同代 successor。
舊世界 visibility flag 也不等於 PvE 已掛載。因此這個配置可使裝備後的 self DA、
世界顯示及下一次入戰使用不同來源；只補8-byte快取不足以修好整條生命週期。

本輪增加同一個純 `Config::validate_owned_pve_material_sources()`：JSON載入完畢
及 programmatic Application 初始化 DB／host 前，都拒絕
`owned_pve_rooms_enabled && diagnostic_owned_weapon_appearance`。
單獨初始 `owned_player_appearance` 與獨立非PvE診斷仍保留；沒有猜原生裝備映射。
這是提早拒絕尚未支援的組合，不是完成正常裝備功能。

[裝備來源與修改後複查](tw-equipment-appearance-source-pass9-20261021.md)涵蓋
真正 writer、bag move、防具／神獸、joint transaction、初始／返回材料及變身入口。
目前 src 的實際 appearance save caller 只有上述診斷 writer；公開 factory 要求
完整 issuer after-state，不能從道具編號自行造值。新增配置案例尚未執行；作者與
獨立審查者已核對載入／直接建構的相同檢查、合法邊界及 DB 前呼叫位置。

## 變身已找到真正實例來源及送出封包

[本輪裝備／變身 REA](tw-native-equipment-morph-producer-pass9-20261021.md)
追回 `4EAEF0` 對道具6285／6286／6289的選定一般確認分支：從完整20-byte inventory
instance 的 offset4 WORD 取得 ChangeDoll row key，完整48-byte本機 row 的
offset8文字指標用於確認顯示。來源不是只看道具名稱，也不是直接把道具 key 當變身 key。

state5確認後經 `4EA770 → 496720 → 4132E0` 送 C27：item key WORD、slot BYTE、
quantity/request BYTE。沒有送出該 instance WORD4、完整變身定義或完整 S1C／86/4。
服務端目前同形 C27 只處理各自已資格的 discard 域，沒有通用變身使用 handler；
不能因形狀相同而丟棄變身卡、推定消耗成功或生成猜測外觀。
原服資格、消耗、時效、目標、戰鬥限制及 response order 仍待真實來源。

ChangeDoll getter 的 high-water／首WORD比對亦不等於 row 存在或完整：count是
signed16，writer 有 parsed32 範圍檢查、WORD存入、重複row後寫及未初始化失敗值。
保留這些限制，不以零值、相同key、process pointer或舊149c decoded表替代目前來源。

## 檔名與裝備圖示上游有新證據，完整角色外觀仍缺生成者

原生 `455780` 確有22組候選檔名，經 `%scomm\%s` 交 `456130`；包括
`gamedata.csv`、`ChangeDollCard.csv`及另一欄literal候選。`531C10`選欄條件為
`WORD[59DFD8]==4 && WORD[59DFDA]==2`。本輪沒有追旗標setter或原生base-path
caller，也未decode檔案，不能由檔名宣稱當前section內容、語系流程或另一地區協定。

`49B850 → 49B720 → 459A60`取 metadata offset0x116／0x118的WORD，再到具體 inventory UI
resource；部分欄位是型別特有，slot42/43與其他裝備slot亦有不同路徑。
這證明圖示／文字來源，不證明 item→完整 HeroDoll packed components。
另一真正 caller `502570` 在選定完成狀態把 retained block
`world-owner+0xA7F2F40` 交 `501810`，並清 pending `+0xA7F2F44`。
下一個具體入口是該 block及pending的writer；不能假定它必定由裝備生成。

## 原服先手與回合仍保留證據邊界

[本輪回合生命週期 REA](tw-native-round-producer-pass9-20261021.md)補回真正caller：
`464910` 在 `46514E` 呼叫 `5109D0`，保留 CWar 到 Play+0xA7E05EC；
原生case4的 `465836` 從同欄呼叫 `5112C0`，之後 `4658D9` 呼叫 `515770`。
配置wrapper經malloc取得記憶體，沒有提供全區清零保證。結合既有current-aaf指令
證據，可確立每次選定入場路徑會設 `CWar+0xA9E9C64=0xFFFFFFFF` sentinel；
這不是原服回合值或reset-to-zero規則。相鄰+0xA9E9C68／+0xA9E9C6C仍未取得
完整初始化／alias writer，不能從配置推零值。失敗／不完整分析入口與後續修正均保留。
原生client的初始化、接收次序或動畫執行不等於原服先手比較、平手規則或回合計數生成。

既有成功append FIFO證據仍有5120-byte ring的容量前提；單次projection大小、
2560-byte logical frame及655360-byte aggregate上限都不是跨callback已消費ACK。
沒有憑此另造速度排序、遞增counter、技能優先級、RNG、timeout或pacing。
完整 S1C／86/4、裝備／變身後完整材料、S83 group／S88 counter產生者仍OPEN。

## 交付、審查與後續

每項改動後再次檢查相關源碼；新native研究由另一位審查者核對，root另核最終差異。
唯一正式靜態報告與精確SHA、REA關閉／CLI退出、作者／獨審及發布收據位於：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass9`。
不把本輪有限修正當完整遊戲接通或原服公式還原。

另以既有客戶端交接更新服務端WASM來源文件：沒有已驗收／部署endpoint或
三分流selected-channel橋接，不提供猜測URL。僅文件核對，沒有啟動gateway、
使用正式帳密或對其他chat發訊。完整宿主／聯合驗收仍待另外的集中階段。
另行暫停的完整目標與四小時Discord heartbeat維持暫停，本輪沒有恢復它們。
