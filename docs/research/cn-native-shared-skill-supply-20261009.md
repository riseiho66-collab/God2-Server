# CN actual shared skill catalog supply — round197

本輪將固定版本 CN 技能定義供應，接到同一個 Application SQLite reader 所建立的 CN 服務端工廠。修改 `SharedCredentialServer.h/.cpp` 兩個既有來源檔：來源串接段187→188，完整雙向玩法新增0。目錄定義不等於玩家已學習技能、施放權限或原生公式；全遊戲分母及百分比仍未知。

## 實際來源鏈

第196輪已由 Application 傳入 `database.native_skill_catalog()`。本輪在既有 `SharedServerPlan` 尾端加入明確選用的 `native_skill_definitions` 原生 provider；它只能是 `CnNativeSkillCatalog::read_actual_source` 產生、持有固定版本完整資源的物件。沒有預設路徑、revision、Current、TW替代或自動import。

CN private constructor 在實際 endpoints/budgets/角色檢查後、建立 verifier/listener 及呼叫 `plan.controllers(Context)` 之前，使用這個確切 reader 呼叫既有 `CnSharedSkillCatalog::bind_actual_shared_store`。選用 provider 卻沒有 reader、缺少任一必要資料、provenance 或完整110B不符，都不能建立這個 host。工廠於 constructor 被呼叫，不能等到 `start()` 才供應目錄。

既有 bind 對四類125／130／87／111，共453個宣告的定義逐筆比對 pinned dataset、來源 envelope、ordinal、offset、record SHA、110B原文、kind與ID。它沒有另作 COUNT(*) 排除未被使用的額外行，也不是跨全部lookup的資料庫交易快照；精確總行數與原子匯入由既有明確import處理。此輪不執行任何lookup、C++或SQL。

資格限定的目錄存於 `State::cn_native_skills`，宣告在 controllers/connections 前，讓它在那些成員析構後才釋放；目錄強持有原生provider。Context尾端傳入同一個 shared_ptr，實際 source factory 應複製進其供應者，不能留下臨時 Context 或 endpoint 參考。共享 SQLite reader/connection 仍由 Application 擁有，必須活到既有 game-owner drain 完成；shared_ptr 不會延長資料庫壽命。

工廠返回後、listener start 前、game-owner accept 的seed前後與 verified controller入口會觀察 provider Current。失效不能開始或繼續此處的登入工作；未選用 provider 的舊 constructor／aggregate 路徑保留原本行為。Current不是整個資料庫epoch：每次後續catalog lookup仍比對實際該行，後續世界／戰鬥供應者仍需其完整 Current／authority。要求供應者觀察不泵事件、不重入、不修改共享store，並不宣稱任意外部callback已被完整reentry fence保護。

## 儲存及權限邊界

既有 `SqliteDatabase::import_cn_native_skill_catalog` 是同connection明確資料匯入入口，要求migrated DB、無外層交易、真current pinned provider；先持有453個原始定義，再在單一 BEGIN IMMEDIATE內核對 migration5、foreign keys、來源與精確行數，寫入／讀回全部資料後COMMIT。既有精確資料可idempotent成功，部分／orphan／衝突不被取代。本輪不從constructor、登入、預設migration或Main呼叫它，不取得任何玩家存檔或生產DB內容。

沒有把 `NativeSkillRecord` 的TW-only MP accessor改當CN規則。沒有建立學習技能／扣技能書／持久化事件交易，也沒有自動將 WORLD34／35 清單更新映射至獨立戰鬥87列表。實際共同角色／subject identity、native學習issuer、Lua規則、扣除成本及單次結算、完整回包和Main選用仍OPEN。

## 本輪帳本

| 範圍 | 目前盤點 | 本輪增量 |
|---|---|---:|
| TW／CN C2S已觀察opcode聯集 | 各156；phase／variants未列齊 | 0 |
| TW S2C世界長度表支援 | 252＝230固定＋22變長 | 0 |
| TW S2C戰鬥索引 | 110＝9特殊＋101預設 | 0 |
| CN S2C分階段 | 帳號6／世界206／戰鬥68，共280 | 0 |
| TW83 action／86 selector已盤點子分支 | 23／7；不是全狀態分母 | 0 |
| Endpoint紀錄／source groups | 958／28 | 0 |
| 來源串接段 | 188 | +1 |
| C++／header | 新增0／修改2 | 2既有檔 |
| 新原生code／完整雙向玩法 | 0／0 | 0 |

本輪三個子代理分工釐清 provider資格、server owner／例外邊界、same-store import/lifetime；來源原件與各自唯讀研究單獨封存。研究與source接線不等於部署／原生客戶端驗收。保持原生字體、繁簡轉換、帳號存檔、聊天IME等凍結功能；TW／CN／web、共用64位元完整數值路徑、stack99與共享資料表目標不縮減。未建置、執行、測試、操作資料庫或部署。

## 同輪網頁來源交接

收到 web peer 的 v18 checkpoint、runtime v11、commands v7／v7.1；四份真實完整命名報告按其提供的SHA保留。Root閱讀其接線／API／缺口等限定欄位，沒有把內含physical windows當作本輪獨立PE恢復，也沒有執行client模組。

新交接明確區分552870／5540B0六格伙伴選擇窗，與552CB0／5542E0五格alternate技能窗。歷史用詞保留，由此加註；S87 flag4000已接的是client alternate received state與GUI，第二actor/context／553960 logical page*15對display page*5／C35送出仍OPEN。553A50當前primary descriptor不是Role持久化技能列；S83的DF8／EC4前段也沒有完整cast／God／RTG／shadow／239++及結算，仍recordConsumed:false。這些client指標、圖示、旗標與來源ACK不成為服務端學習／施放權限；本輪不新增opcode或完整玩法。

peer記錄49,152,444,461B採recursive stat、無resolved-path dedup；Root本輪容量記錄採regular file logical bytes、略過junction／symlink。兩種範圍分別保存，不混成同一計數、不偷偷更新舊基準；此轮沒有恢復歷史客戶端、建置樹或PE大份副本。
