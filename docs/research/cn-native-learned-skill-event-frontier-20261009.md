# 正式共用技能目錄來源與學習事件前沿（第196輪）

本輪完成同一 Application／SQLite 的技能目錄讀取器到 TW、CN 來源工廠的實際傳遞。修改5個既有 C++／header，不新增空介面；來源串接段186→187。這個來源供應增量沒有實作真正學習交易或完整施放流程，完整雙向玩法新增0，全遊戲分母及百分比仍未知。

## 實際正式來源串接

原 `SharedWorldHostPlan::Context` 與 `SharedServerPlan::Context` 只供應角色、地圖等來源，沒有同一資料庫的技能目錄。現在 Application 在既有初始化／遷移來源之後，直接把 `database.native_skill_catalog()` 的真正讀取器傳入兩版來源工廠。PHASE1沒有執行初始化、遷移或任何DB查詢。

- TW Context尾部新增 `const NativeSkillCatalog* native_skills`，既有aggregate可保留null來源缺席；正式Application傳實際getter地址。既有TW Factory的source(context)因此取得該讀取器，Owner保存相同pointer，bound Factory重用時的same(context)核對exact reader，拒絕換另一個目錄來源。
- CN保留既有8／9參數constructor：8參數委派9參數空host，9參數委派private implementation的null reader；新增public const-reference版本委派private pointer implementation。Application實際選用const-reference版本，existing plan.controllers的Context收到同一讀取器，既有make_native_login_controller_factory再把該Context交給source(context)。

真正修改的五檔為 Application.cpp、SharedWorldHostPlan.h、SharedTaiwanNativeWorldHostPlan.cpp及SharedCredentialServer.h/.cpp，完整原件共625,027B，實際diff另存。兩個header和CN server定義完整讀取；Application保存全文但只讀相關includes／startup／兩個呼叫／shutdown與全部diff；TW Plan Owner／Factory定點範圍讀取，不宣稱全Application玩法已分析。

這個reader借用同一SqliteDatabase的既有目錄及連線，使用者必須在game owner與實際store lifetime內使用；Context不是strong store ownership或Current證明。正常Application局部生命週期及原SqliteDatabase Impl析構順序另有具體來源context，沒有把靜態閱讀當成全部外部發行者的生命週期驗收。

CN仍必須提供真實固定582f的native provider，經 `CnSharedSkillCatalog::bind_actual_shared_store` 對全部453筆實際CN rows、source、完整110B和offset資格限定。TW dataset、TW-only client_mp_threshold與TW SkillBookCatalog不成為CN規則。新binding不查目錄、不import、建立schema、grant、學習技能或補造成功；也沒有在Main選用缺少真實供應者的plan。

## 真正事件歷史保持分開

History代理保存6段1,621B／492 instruction sites，全部retained。Root讀完整4D5B20與拆出的4D5B83 canonical C，以及entry／reset scan／return的全部實際data指令。canonical的99B／275B decompiler範圍與既有expanded原始CFG分開，不用全文C大小宣稱新原生函式覆蓋。

WORLD30的實際data分支先檢查signed BYTE絕對identifier及count<16，寫count-indexed inactive slot的身份／名字／5B，再對高identifier、body+11==1掃描既有row WORD。匹配才清該row+1F0技能count並early return；這段沒有清實體pointer／flag儲存。現有 `CnSubjectDeclaration30::native_effect` 已保存該分支，沒有另造等價reader。

WORLD34對原subject row追加bank-derived pointer和flag0；WORLD35比較同一原pointer並設flag3。Battle87維護獨立primary／secondary active list，primary auxiliary查的是row+5C／60，不能與WORLD row+1F0／258混為一個學習列表。同P／call／epoch的H20=U與H14=R保持195資格，mode1不重新attach。初始化清count、相同kind/id、原地址或bit15都不供應共同actor身份或學習／施放授權。

Native代理9段1,369B（4 complete1,047B／5 bounded322B）、362 instruction sites全retained。WORLD32只改名字、33只改row+40 BYTE；492E70初始化clear／count0／selectorFF不是收到技能移除請求。限定sender481440的三個metadata候選只到GUI邊界，沒有follow。沒有以這個限定搜索宣稱全遊戲沒有學習路徑。

兩個NUL literal共123B已包含於195完整固定PE，本輪另作定點提取及subset/hash比較，不算新code或opcode。GodUpdateSkillLevelUp debug字串實際屬S34／4D5E60；初版誤放S35的工具／event JSON全文及訂正diff保留。字串名稱不是真正server事件語义，也不證明共同神祇／寵物／玩家主鍵。

## 存檔／物品消耗的單次交易缺口

Store代理新讀具體SharedPrebornChoices::receive／publish：81只保存scope/mask，83退休原pending後單次apply，再postcommit prepare／qualify／held-release。WindowSource仍只把apply交給必要實際供應者；該callback不是已實作學習持久化。

實際 `SqliteCompanionRepository::store_deity` 使用自己BEGIN IMMEDIATE／revision CAS／readback／COMMIT；DiagnosticSupplyService的物品消耗使用另一個 `commit_inventory_resources` 交易。各自的原子性不代表兩次呼叫能成為「學習＋技能書扣除＋durable event」單一交易。具體fixture writer、CUSTOM診斷consume與圖示指派都保留來源標籤，不代替CN原生學習規則。Root另讀store_deity與供應use／Transaction源文字，沒有執行SQL。

接續必須找真正native取得／變更事件、common owned subject／actor mapping和原規則結果，在同一store transaction保存learned revision、book custody／消耗與durable replay／event。再從同一實際提交結果供應完整有序WORLD34／35或battle87／86，完成MP、item、target／range／formation、一次結算、完整回覆與Main。這些仍OPEN，不能直接把兩個獨立commit接起來當完成。

## 本輪計數

| 範圍 | 目前值 | 增量 |
|---|---:|---:|
| TW／CN C2S已觀察opcode聯集 | 各156，phase／variants未列齊 | 0 |
| TW S2C世界長度表支援 | 252＝230固定＋22變長 | 0 |
| TW S2C戰鬥索引 | 110＝9特殊＋101預設 | 0 |
| CN S2C分階段 | 帳號6／世界206／戰鬥68，共280 | 0 |
| TW battle83 action／86 selector | 23／7，限定前沿不是全部變體 | 0 |
| Endpoint紀錄／source groups | 958／28 | 0 |
| 來源串接段 | 187 | +1 |
| C++新增／修改 | 0／5 | 同reader兩版factory來源 |
| 新原生code／完整雙向玩法 | 0／0 | 0 |
| 全遊戲路徑分母／完成率 | 未知／null | 未建立分母 |

網頁ack195、Root checkpoint v17、Runtime v10、Command v6及契約五份新完整epoch另存；四個指定hash相符。Root只現讀對應API／sourceCorrections／gaps／reset／metadata／GUI／執行界線等具體sections，不把700KB完整physicalFunctions保存當作獨立PE全讀。54F360不一律關閉primary／formation，flags&28時是refresh，551030(0)才有formationclose；FightEny CSV7→rowWORD4→actorDB4低10位仍屬client metadata，非怪物HP／雙攻雙防或servergrant。完整God／secondary／controller／unknownA9712Ctrue1／GUI仍OPEN。已依既有所有者授權回覆196 source ACK並保存exactdraft及成功actual tool threadId receipt，195 ACK和v9初版保持，不宣稱共同驗收。網頁與TW／CN仍走同一權威核心與資料表；共用64位數值及明確wire／object／飄字、仙幣僅99999999999、qualified stack99、原等級／字型／繁簡轉換／凍結功能與全部遊戲目標不縮減。

本輪整個Desktop/God2 capacity-before-final-account現讀44,239,460,058B／297439 files，無不可讀，明確不follow junction／symlink。網頁v17的48,998,042,374B／334243是未resolved去重的recursive-stat口徑，兩份原件分開保留，不偷偷當同一容量基準。後續大型中間輸出放專案外，仍保留整個專案<50,000,000,000B方向；完成交付後另取current容量。

fresh before1403及完整prior195的2611封存成員保留。Root5全文／diff、三代理實際原件與錯誤訂正epochs、當前來源帳本及唯一round報告另存本輪目錄。Native代理seal列90成員但漏了nested retained195/seal.json：Root獨立完整inventory為92檔，另存完整歷史seal並核對它精確等於195實際seal／固定hash，保留原代理seal不改，不接受其他未列成員。Store代理own-tool的discovery_role預設字串另附actual path／copy／hash資格補述，並不當peer玩法來源。PHASE1只有文本、原件、hash、PE／Capstone靜態恢復與檔案帳務：沒有建置、测试、native／C++／Lua／codec／API／runtime、DB／SQL執行、遷移、部署或155／52F330／52F170重試。全部來源串接後才集中全面驗證、修復與發布。
