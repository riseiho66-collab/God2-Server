# 台服握手來源與非同步推送一致性（2026-10-19）

本輪沿用 CUSTOM-0159，追查目前 Taiwan EXE 的實際連線握手，並修補已接入 Application 的 qualified async guild/bootstrap/name 推送。前輪499已有角色退場占用保護；本輪沒有把單一封包修正當成完整三分流或全遊戲完成。

## REA 原始證據

原始 God2.exe SHA256：aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48。
重用已釘選的分析衍生 PE；原13節內容與各節標頭逐位元相同。分析檔新增 synthetic entrypoint／section，整體 PE 標頭並不相同；synthetic caller 不當原始呼叫者。完整收據在外部 native-seed-round500/findings-v1.json，4批18個函數全部完成並關閉。沒有啟動遊戲或執行 codec。

| 原始位址 | 觀察 |
| --- | --- |
| 411D30 → 410500 | 實際 connect 成功後初始化 codec。時間來源經547EB0／547D72供應 PRNG state；547D7F 的32位回圈為 s*343FD+269EC3，取(s>>16)&7FFF，初始16 bytes只存AL。 |
| 410500 | 擴展初始種子後，DWORD+0/+4=1，+8/+C=0，receive cursors清零。這些種子會在收到遠端16 bytes後覆寫。 |
| 410E20 → 410D20／410BC0／410B50／410AF0 | connect 呼叫等待參數20000；實際socket讀完整frame，再從payload cursor取16 bytes。只有exact16成功才繼續。410BC0分開讀LE16 header、遮罩8000 length flag、拒絕> BFF。 |
| 410570 | 四個DWORD完整覆寫this+2420..242C，再呼叫既有410490擴展。不是用本機初始random值永久代替遠端種子。 |
| 410E9A後 → 410900／4108E0／410930 | 寫DWORD+8=1、+C=1、+0=0。重用497的410910可知+8控制收送加密；僅由setter不能替+C指定完整語意。 |
| 410ED0 → 4105B0／4105C0 | 回應body長度固定16，位址是this+2520的derived16區域。410420由key/table生成該區域；不是原樣回送收到的16 bytes。 |
| 410ED0 → 410A90／410B80／send | 用當時codec產生的同一wire與長度送到實際socket，之後410950寫DWORD+4=0。 |

沿用497已有的 key expansion／bias、checksum、收送cipher、envelope證據，不重跑那些函數。本輪只讀偽碼與組語；低階型別／calling convention及未建模回傳仍以組語與資料流為準，不把反編譯C當可編譯原始碼。

服務端 RecoveredSeedExchange 目前只送all-zero16的19-byte hello，並比對既有固定19-byte derived-proof回應；其後各parser／sender／wire fence仍使用既有固定zero key。這是已實作的單一profile，沒有新增任意種子協商。原生握手來源被追出，不等於已在本輪執行並核算現行zero table／bias／proof，或完成目前客戶端互通驗收。

## 實際修正

Session::send_qualified_world_records_with_acceptance 的 standalone async 分支原先只驗header／length。相同長度但不同logical、損壞checksum或其他cipher的wire，可能被當成原推送接受，再形成具有錯誤內容的custody metadata。

現在在GAME保留profile呼叫前的私有original logical；provider回傳後用現用fixed-zero decoder驗完整checksum並逐byte比對原件，也拒絕provider修改傳入span。snapshot配置後、呼叫profile前，以及decode／immutable wire配置後、NET post前，都重查原private INIT、output、full64 tuple、native binding及source liveness。失敗只settle(false)一次並依既有RAII退回reservation。

成功時保留provider的原wire，沒有NET末端轉碼或另選fallback。NET只拿immutable wire／原私有output receipt與pure atomic cancellation。active original-run capture的早return分支未改，仍由原profile／finalresponse驗證及原FIFO custody負責。Enqueued仍不是Written、原版client ACK或Gameplay成功。

既有C++測試來源新增同長wrong body／opcode、checksum、synthetic alternate cipher、provider修改輸入，以及超過producer容量的反覆拒絕後接valid原wire／onceACK恢復。這些測試未建置、未執行；未新增Python或產品JS。

## 仍待接通的真實來源

07／2A Offer → writer → stored reader → Session 的HostPlan接線已存在，但src內兩個Offer::from_actual_source尚無實際生產者。common profile40、saved position、NPC/資源表只能供應各自有證據的欄位，不能決定未知raw07 flags／route／opaque與完整raw40。再加wrapper不會補足資料。

部分Offer／Handoff仍釘149c mapped image。現有manifest只證99c→aaf0的名片修補，不證149c／5fcf→99c的完整相關code/data lineage；本輪沒有更換hash常數放行。

目前可重用485的current4147D0完整07 receiver（74 bytes複製、36-byte stride、W19 low3、flags low1→transport+4200）與480的current468160完整2A initializer。下一最小trace是current40B490的Main rawlist／L→G flags、40BA00→414C50 token、41235E所在route W32 consumer、408310..40852E renderer及兩個length-table slot；consumer閉包仍不能冒充原服producer選值。

其他OPEN：全部parser／prefab／logical sender與wire fences共用的真正Session profile、壓縮完整語意、完整Main／Entered supplier、MDT／MDL野外geometry、PK持久復原／各系統save／目標分流admission、可信Web G目的地及六向切換。手寫JS依C++／WASM完整移植驗收逐批退役；本輪未修改客戶端。

PHASE1維持：沒有build、test、Lua/native/VM/codec/game執行、game DB SQL、schema／migration、import/export、activation或deployment。完整遊戲分母與完成率仍為unknown/null；完整目標保持active。使用者在本輪要求「下一輪結束後停止工作」，依序完成下一輪501後暫停。
