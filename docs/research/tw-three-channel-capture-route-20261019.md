# 原始公會回覆內容與台服選角路由（2026-10-19）

本輪501是使用者指定的最後一輪。完成唯一正式靜態盤點、提交與推送後，暫停完整目標及本任務4-discord排程，不自動開始502；完整台服目標保留，不標完成。其他任務排程不屬本次操作。

## 實際 Session 修正

沿用 CUSTOM-0159。前輪500修補 standalone qualified async sender；本輪處理其同一 actual Session 內的 original-run capture。舊碼只驗header/length，最終codec驗證無法證明有效密文內的logical還是原始那筆公會回覆。

Impl::capture_reply_push 在任何配置或supplier前，把有界borrowed logical及expected full64 tuple複製到自己的bounded storage。encoding guard提前，將正在呼叫的framer移到GAME局部持有；invalidate/finish不能析構仍在執行的callable。provider只看另外一份owned mutable copy，無法藉const_cast改原caller storage。

provider返回的原wire也先複製到私有bounded storage；用目前已實作的fixed-zero codec驗完整checksum與exact原logical，不接受換body／opcode、其他cipher或改動輸入。原封包位元組保留，不在NET末端轉碼。profile／decoder／Reservation及vector reserve配置後，都以原capture/window、GAME身分、full64 delivery tuple與source flag重查；sole acceptance callback只在不再配置的Frame commit才移交。既有producer reservation、整批失敗、一次ACK、FIFO／original slices與晚取消旗標延續。

既有C++測試來源新增6種second-push失敗：body、opcode、checksum、synthetic foreign cipher、provider修改輸入、呼叫中的capture失效。第一筆push有效也不能漏送或回成功；兩筆acceptance都只能依原次序false一次，拋錯不能阻止後者。callable lifetime probe檢查invalidate時仍活著、退出後只釋放一次。沒有執行這些測試或建置；靜態審查不算原版client驗收。

## 本輪 current Taiwan REA

God2.exe SHA256 aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48。兩個target均關閉，4個原始函數已取得組語與反編譯資料；41235E實際位於412310。第一批未辨識40B490／40BA00的失敗收據完整保留，後以新的analyst-only入口標記分析副本辨識；原13節內容及節標頭不變。synthetic730200／730205的callers不是原客戶端呼叫者。完整外部收據為three-channel-capture-route-round501/findings-v1.json。

| 原始位置 | 已觀察資料流 |
| --- | --- |
| 40B490 → 4147D0 | Main把+178CE0的rawlist指標、+8F4/+B40原生words與容量2交給既有07接收函數。成功後，把原L transport Main+15E84的BYTE+4200複製到原G transport Main+15E88的BYTE+4200。不能直接把+4200當codec+8。 |
| 40BA00 → 414C50 | MOVSX讀selected WORD+178CE4，乘36後讀rawlist+15的BYTE，再AND7，與Main+178CF6/+178D0E的兩份原生credential buffer交給G transport選角builder。這是角色token，並非分流身分。 |
| 414C50 | 保留兩個bounded16字串與token；在上述0..7來源中，4..7轉0。原1A builder仍是38 logical／41 wire，marker4及未寫入stack尾端仍依既有grammar保留，不新增常數或角色名替代帳密。 |
| 412310內41235E | 以rawlist+15+i*36的low3匹配選角token；路由只讀BYTE rawlist+22+i*36，也就是raw row W32的低位元組。以非零BYTE比對已配置的10×10 route/alias位置，再取配置IPv4、WORD port與兩個physical indices。找不到則回null／empty host。 |

因此07 token、route low byte、A6/copied bytes都不能授予channel/world權限；真實分流仍須原L選線發行、實際bound G endpoint及私有handoff血緣相符。consumer閉包仍不供應原服07／full2A／Entered選值。

尚待下一次使用者明確恢復後續追：408310..40852E renderer、07／2A length-table slots、40B490／40BA00真實caller/state roots、414D20後續、+4200完整用途、current與149c相關code/table lineage，以及真正native producers／Main。不得把未分析部分或空factory算完整玩法。

持久save／PK recovery／target admission、可信Web G、六向切換、全技能公式與遊戲系統、MySQL完整後端／無損轉換等完整目標仍未完成。手寫JS依C++／WASM功能完整移植驗收逐批退役；本輪未改客戶端。

PHASE1 source/static only：沒有build、test、Lua/native/VM/codec/game執行、game DB SQL、schema／migration、import/export、activation或deployment。分母與完成率仍unknown/null。暫停是使用者停止要求，並非宣告完成或遇到不可解阻擋。
