# 共用戰鬥寬數值 Lua 來源串接（20261008-shared-battle-lua64-source）

接續前輪 Battle HP64，將實際規則呼叫接至精確 Lua 整數。原生公式恢復與自訂數值擴充分開；本輪的 CUSTOM-0090 是使用者授權的既有 CUSTOM-0006／0017 數值擴充，不是官方戰鬥規則或陸服玩法資格。

BattleNumericProfile 移至共用 header，CombatRuleInput 與 RevivalInput 以最後一個欄位傳遞明確設定，預設仍 LegacyCustom。Battle::act 與 revive 從自身 snapshot 傳入設定，LuaEngine 不從角色、版本、語系或數值猜測。未知設定直接拒絕。RecoveredBattleService 的可信 Policy 同樣帶預設 LegacyCustom 設定；bind 在登錄前要求 Battle 與 Policy 設定一致，其餘身分、狀態、技能、成本、回覆與 checkpoint 條件保留。

LegacyCustom 保留原 actor HP／攻防 1m 範圍、combat.lua 的原計算與最終 1m 限制，以及復活原 maxHP 入參範圍。ExtendedHealth64 的攻防欄位仍 uint32，可使用完整表示範圍；這是明確擴充路徑的表示能力，不授予任何原生角色或怪物新屬性。MP 及技能百分比仍保留原欄位與已有限制。ctor／restore 使用相同條件，保存格式仍是先前版本 1／2。

ExtendedHealth64 的 combat_damage 真實呼叫新 combat_health64.lua。依既有 CUSTOM-0006 次序，以整數乘法及 //100 求 scaled attack／defense、最低 damage、critical predicate 及 critical floor；係數與次序不改，新設定不套用舊 1m 最終截值。uint32 stats、power≤10000、defense factor≤100、critical multiplier≤1000 使最大中間乘積 429496729500000，低於 signed64 表示範圍。這是來源推導，未執行測試或 Lua。

所有新入參明確以 lua_Integer 傳入。exact_calculation_integer 要求 Lua 5.4 的 signed64 integer，先檢查實際 integer subtype，再讀取 lua_Integer、恢復 stack、檢查非負與指定範圍後轉成 uint64。新傷害／HP 不經 double 或 catalog_selector；即使浮點數數值看似整數也不接受。MP 回傳先檢查原範圍再轉 uint32，damage callback 不得改動明確成本，critical 必須 boolean。

ExtendedHealth64 的 revival 真實呼叫未改的 revival.lua：寬 maxHP 先檢查 1..INT64_MAX，以精確整數傳入，HP 回傳仍是既有 HP1／MP66 投影，且檢查 HP≤owned maxHP。原描述資料、執行／時序及資格仍屬 CUSTOM-0017，不把書面描述升格為原生執行公式，也不自創新復活技能或回復比例。

docs/custom-designs.json 新增 CUSTOM-0090，分欄保留數值擴充、舊公式、舊截值、新設定、復活及權威來源。前 87 個紀錄保留；新紀錄明示沒有 production／native TW-CN-web 啟用，測試未執行，完整 balance／原生來源／客戶端驗收待後續階段。HP／傷害／EXP 遊戲上限尚未選定，仙幣 99,999,999,999 不套用到其他欄位，原生等級不改。

本輪未改 Application 的既有呼叫與政策，沒有把新設定掛入 PK 或 diagnostic-v1 儲存。實際 admission、角色／怪物權威值、原生技能定義、新保存政策、schema 與回復、TW／CN／網頁的 producer／consumer／物件與飄字仍須串接。新 Lua 能力或可信設定一致性不是完整雙向路徑。

三名子代理處理實際 Lua 整數入口、可信 binding 與來源歸屬／保存政策依賴；保留 before926、前輪 159 的封存、真實來源副本及實際閱讀範圍。只完成來源與靜態檔案帳目，沒有 C++／Lua／原生執行、build、tests、DB／SQL 存取、遷移、部署或重啟。所有遊戲路徑接通後才全面測試與修復；新增 phase、opcode、完整雙向路徑為 0，完整分母與百分比仍未知。
