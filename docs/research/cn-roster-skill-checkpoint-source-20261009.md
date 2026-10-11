# 第207輪：原順序角色／技能 checkpoint 來源接入

這是使用者「從本輪開始算起，5輪之後結束並停止工作」的第5輪：203、204、205、206、207。本輪完整帳本、報告、封存及交接完成後暫停目標模式，不開始208；之後需要使用者明確恢復。本輪只做靜態原生研究及來源串接，沒有建置、測試、原生執行、封包模擬、DB、SQL、服務重啟或部署。

新增 CnRosterSkillCheckpointSource.h/.cpp，修改 SharedSubjectRosterPublication.h/.cpp。來源保留 WORLD30/31/32/33/39/34/35 混合原順序，在各連續技能區段提供實際 before-image checkpoint；不能把34/35抽出後跨角色更新套用同一舊快照。每筆技能記錄必須由 checkpoint 唯一覆蓋，索引及順序精確，不能重疊、漏接、倒序或跨非技能記錄；實際供應者可以因既有640筆來源投影預算拆分連續技能區段，不能自造新狀態或版本。640是操作預算，不是原生遊戲上限。

所有借用 records、aligned definitions、checkpoints 在呼叫外部 Current 前複製持有；投影包含原始索引及206的完整16列資料階段。同共用技能資源庫逐筆比對 kind/id/offset/hash/fullraw；來源指標保留強生命週期，immutable projection、原始分幀與實際事件在 BeforeQueue 和 QueueAccepted 都保留。選擇此契約必須顯式提供額外原生 checkpoint owner；既有共用 post-commit Qualify 仍必要。缺失技能來源不能降級用舊快照，不選擇此契約時不能夾帶 checkpoint。

原生保留968 bytes／283條指令，全數沿用既有證據，本輪新增原生位元組0。30先寫 inactive row；duplicate inline 分支只清 active matchingrow primarycount 後返回，負值30在正常追加後才更新選取。31使用 signextended ID、第一個 matching row；34/35使用 zeroextended ID、所有 matching rows。32/33/39沒有 subject ID，依當時 selected row（或原生 null-selection no-op）執行。這些差异決定實際供應者必須資格化中間的 reset/selection/row/revision，不能把來源 Current 當整段原生效果证明。

206投影內未知 log/UI callback、selected35 pending-table 及可能角色重綁的條件保留；本輪沒有展開 GUI、formatter、glyph 或容量流程。真正共用學習交易、保存、持久重播、WORLD-to-battle 技能 materializer、Main issuer及實際 per-run checkpoint供應者仍未接入。checkpoint 是真實事件持有的不可變 before-image 契約，沒有宣稱客戶端同時處於多個未來狀態，也不要求運作時讀取客戶端記憶體。Socket queue accepted 只是本機排隊接受，不能算客戶端已處理或原生 ACK。新增完整雙向路線0。

來源增量：新增C++2份、修改C++2份；部分來源段196→197。完整遊戲分母與完成百分比仍未知（null）；來源段、opcode與 endpoint 都不能算完整遊戲路線。

| 範圍 | 本輪最新數量 | 計數含義 |
|---|---:|---|
| TW C2S | 156 | 已觀測opcode聯集：151 generic＋5 supplemental，6分支 |
| CN C2S | 156 | 已觀測opcode，階段／變體仍未全定 |
| TW WORLD S2C | 252有效／256表項 | 230固定、22變長、4不支援 |
| TW BATTLE S2C | 110 | 9 special、101 default；83 action23、86 selector7 |
| CN S2C | 280階段項 | account6、world206、battle68 |
| 雙版 endpoint 索引 | 958 | 端點索引，非完整路線 |
| TW WORLD parser | 65／已審閱42 | 64.6%只適用此有限parser審閱範圍 |
| TW reply/control/unconnected | 43／10／13 | reply為下界，不是完整回覆總數 |
| CN receiver context | 14／已資格化12 | 47DE70、4812B0仍未知 |
| CN未hosting phase binding | 93／71不同值 | 原生階段來源，非完整路線 |
| TW未hosting phase binding | 10／10不同值 | 原生階段來源，非完整路線 |
| partial owner chain | 38 | CN35＋TW3，未hosting |
| 部分來源段 | 197 | 本輪＋1，不等同遊戲功能完成 |
| 本輪完整雙向路線增量 | 0 | 共用權威與正式issuer仍有缺口 |
| 全遊戲總數／完成度 | 未知／未知 | 不以局部解析或拒絕測試冒充 |

保留前206與更早帳本、帳號存檔、聊天、IME、認證、頭像、原生EXE／字體與繁簡轉換。共用表預設，只有已證明儲存不相容才 `_tw`／`_cn`；仙幣99,999,999,999、共用64位數域、合格堆疊99、等級不改的未完需求不變。整個 God2 目錄容量上限50,000,000,000 bytes，原生PE只原地雜湊，不恢復大型歷史樹。

實際 before 既有publisher2、第一候選4、最終4及實際依賴均完整保存；不更改206缺失候選原件的歷史紀錄。兩個子代理都在207停止。根封存及catalog207完整封存後，另存實際目標API paused回條與容量交接；不建立自動恢復工作。

下次需使用者恢復後才可接續：實際共用已提交混合角色事件與 per-run immutable checkpoint供應者，資格化中間資料／選取及未知 callbacks，再接真實學習／技能書權威交易、保存、重播與正式issuer。全部TW/CN/web路線完成後才集中全面測試、修復、發布。
