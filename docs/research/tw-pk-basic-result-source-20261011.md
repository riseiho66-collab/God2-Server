# TW279：房間持有的基本攻擊結果來源

本輪新增 `OwnedTaiwanPkBasicResultSource`，由真正 `OwnedPkRoomState` 私有房間中的 Ticket、目前單一 Battle 及 repository Ready round 產生 fresh 83/1 與 88 模板。`resolve_collected_basic` 接續既有雙指令原子結算與兩位玩家的相對視角投影，取代此限定分支需要呼叫者提供完整 raw 模板的依賴。這是尚未由 Application 掛載的來源增量；沒有完成整條 PK、技能、原生驗收或 TW100%。

## 新的原生追查

固定 mapped image SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`，3,174,400 bytes，RVA 對應檔案 offset。只選讀 verified=true 封存輸入，沒有恢復整個歷史建置樹。外部證據在 `C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-result-contract-279`。

native worker 沿完整限定 516AE0→52C520 的 basic1/scalar3 路徑及其直接 scalar handlers，沒有發現 raw4 直接讀取或顯式封包指標轉交。first-batch cleanup、資源與後續繪製函式的 global/context alias 邊界仍開放。source worker 區分 basic1 與 scalar3：basic1 指定語意路徑不讀 R13/R14；scalar3 會使用兩者。佇列與 current scratch 仍完整複製 15 bytes，不能稱為全客戶端忽略、原廠 padding 或原服必定填零。

review worker 追到 88 counter 的 current/首次 previous seed、C2S0B latch 及 readiness 分支。initial FFFFFFFF 時會種入 counter；並沒有證明每輪 current 自動變 previous。current==seed 的路徑可能不等 readiness event 再送 0B；current!=seed 的限定事件路徑另要求 signed DWORD 差值非負。因此 initial0 下的正值 1..INT32_MAX 有明確分支意義，但 counter=round 仍是 CUSTOM 選擇，不是恢復原廠回合公式。特殊 flag、latch、有效 actor、queue 及 readiness event 條件仍依所選分支適用。

計時更正亦保留：88 handler 本身未重設 timebase，不代表整體不會更新；dispatcher drain 的 5145EA..5145F0 呼叫 timeGetTime 並寫入 Battle+A9E9C10。不能將 handler 局部觀察擴張成全域時序結論。raw118 的限定 display mask 與全域 alias 限制另在 review receipt，沒有宣稱所有 bits 都無用。

root 追查 caller 515770 的完整本體與 dispatcher 5140C0 的指定區段，確認 group marker/flag 是 caller loop 的保留局部值，並非每次 83 都重新建立。首次 marker=-1 時取 scratch R3；同 group 才處理/pop 83，不同 group 暫停 drain。88 在本批次 flag 非零時留在 queue；flag 清除後才進入 handler。這不是原服 group 產生公式或 renderer 完整性證明。

後續 root 完整追查 manager 52AC20..52AE51 與 52AF90..52B025。52AC2E..52AC30 對 BYTE boundary 加一，52AC4F..52AC51 在 group255 溢位時略過 actor scan。因此首版 modulo128 的 0..255 配對被修正為 modulo127 的 0..253；首版完整 source epoch 保留，未隱藏修正。52AC20 的選擇、actor state 及後續 rendering 並未因此全部恢復。529020 只有局部前段讀取，不能算完整 readiness closure。

## 真正來源與結算界線

新 helper 沒有公開 factory 或 caller scalar capability，只有 RoomState friend 可呼叫。它要求實際 active LegacyCustom battle、正確 room ID、同 Battle revision 的 Ready round、兩個已保存 basic intents，以及精確的 owned appearances/players/vitals/initial contexts/grants/combat source graph。角色只能是 canonical 0/14、controller 必須為實際 Pair 角色；本分支限物理、零 MP 成本、單一對手 basic，不將技能語意借用為 basic。

兩位玩家的 CUSTOM-0111 private initial contexts 必須分別等於 retained owned player/vital graph，並保留完整 initial88 counter0、reset placeholders 與對應初始 HP/MP。只有 genuine legacy Ticket 並不足以取得此分支。Max HP/MP 與完整 vitality templates 必須一致；戰鬥中的 current HP/MP 則由房間目前的單一 Battle 投影，不能以原存檔 HP/MP 覆蓋。commit 後不呼叫 prebattle world Current 來冒充 battle authority。

`resolve_collected_basic` 先讀 actual Ready round，建立新 source，再將完整 round document 帶到私有 shared resolver 比對重讀結果；資料改變就拒絕使用舊 source。既有 repository settle 的完整 checkpoint/round/readset/outbox fence 與 staged Battle 提交界線保留。原有接受完整模板的 `resolve_collected` 行為保持原樣，兩者共用私有實作。

明示 CUSTOM-0117 選擇如下：83 R4/basic R13/R14 為零；group 依明確 server order 取每輪兩個相異值，range0..253、每127輪循環；88 counter 為 checked positive round≤INT32_MAX，溢位拒絕；raw117..120 為零，friendly1..13 為 reset placeholders，own slot0 HP/MP 最後由真實結果覆寫。這些是獨立具名的序列化與 queue 政策，不是原服值、全域 unused 欄位或已確認 native acceptance。

實際 order、next control masks 與 pure/non-reentrant Battle Rule 仍由權威 server/Lua owner 提供，不從 initial masks、hit target、client counter 或抵達順序推導。既有 signed16 loss fail-closed 不放寬，不截斷 64 位數值來假裝完成擴充；完整 TW/CN/web 64 位封包與顯示目標仍須完成。沒有新增 86 grant、89 terminal、技能所有權、存檔結算或世界返回。

## 證據與帳務

三份 native receipts 各自封存，計數只針對其具名限定區段，不能相加成全遊戲原生覆蓋率：native seal `305a1747d559ce7a4dfc325a280b127bc7b9369ffdae6eea32372873f497d2fc`；source seal `9f6c423649178058cd0f71e17545ae8675eeee6a0b7252f79eab5eab8bd8562e`；review native audit seal `c20f0e576e6d91aa985d52bbedf444669bb6a1e174f214f5df4c639679aa600b`。reviewer 另審實際新 C++ source，終端 pins 由 root receipt 記錄，避免反向引用循環。

root 初次 114210 capture 從指令中間開始，不作有效 code 範圍；1143C4 tail 只資格化至 11460E，後方 jump table data 排除。caller 資格化至 115C82，後方 NOP 排除。manager group-start 只至 12B025，後方鄰接函式與 NOP 分別排除；group-end 至 12AE51，後方 lea padding 排除。探索 raw copies 完整保存，不能把線性解碼總 bytes 宣稱為 CFG closure。

本輪 C++ 既有一檔修改、新增一檔，限定 fresh basic result producer 來源一條；新 opcode0、新完整雙向玩法路徑0。mixed source segments261→262、CUSTOM114→115、reviewed groups26不變。TW C2S候選156／世界parser74（局部來源50、控制11、未接13）；S2C252（fixed230、variable22）、回覆48／推播11／gated4；battle110／specialized9、86selector7／case6、83action23／projection2 不變。TW未掛載關聯38／去重34、CN93／71亦不變。CN歷史 C2S156／S2C phase opcode280／length253 是不同範圍。

尚缺完整 Application/Lua turn owner 與實際 input dispatch、技能 fresh83、later-round grants/control masks、native89/terminal存檔/世界返回/重連及完整玩法盤點。全遊戲完整路徑分母與百分比仍未知。web v74 僅收到 peer metadata，未讀取並核對其 commit/source，保留 pending，沒有新增 ACK 或整合 credit。未執行 build/compiler/tests/runtime/native/VM/codec/game DB SQL/migration/activation/deployment。
