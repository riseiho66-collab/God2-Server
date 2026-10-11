# 補給 HP64 與正式入口依賴（20261008）

本輪修改四個實際遊戲來源檔：SupplyRule.h、LuaEngine.cpp、DiagnosticSupplyService.h/.cpp。補給 HP、maxHP、restoreHP 使用 uint64；MP 保留原欄位與 signed32 邊界。明確的 ExtendedHealth64 設定才走寬值分支，預設仍為 LegacyCustom。數值可表示範圍不是新訂遊戲上限；只有仙幣已指定 99,999,999,999，等級不改。

LuaEngine::supply 對寬 HP 輸入檢查非負 signed64 範圍、存量不超過最大值，六個欄位以 lua_Integer 傳入既有 supply.lua。回傳 HP/MP 要求實際 Lua 整數型別及原有增量界限，保留死亡不復活、僅實際恢復才消耗的規則。supply.lua 未改；CUSTOM-0091 只延伸 CUSTOM-0016 的表示能力，MED02 的已聲明恢復量沿用 CUSTOM-0050 來源，沒有新造物品、恢復數字或官方公式。

服務端可信 Policy 選擇設定。寬值補給需要明確提供純 logical projector；缺少 projector、未知設定或 LegacyCustom 搭配 projector 均在進入解碼與基準讀取前拒絕。projector 收到完整修改後物品槽及資源，只產出 logical bytes，不得傳送、寫入或重入。logical 資料需非空且符合既有 RecoveredWorldFrame 上限；回覆資料配置與編碼完成後，才進入原有 inventory/resources CAS 交易。原有槽位、物品、來源雜湊、revision、整份資源基準及交易內 pending-battle 保護沿用。

LegacyCustom 保留物品槽更新與 RoleVitals 順序。現有框架是已恢復的 TW zero-seed native26 範圍；加入 projector 不代表 CN 框架、寬值原生封包、物件欄位或飄字已完成。現有工廠仍給 LegacyCustom，Application、PK、diagnostic-v1 及資料庫 schema 未啟用寬值。舊 role maxHP 的 DWORD 相等條件及資料庫 CHECK 仍需後續可恢復遷移，不能繞過。

正式 CN 入口另有實際生命週期缺口：main.cpp 呼叫普通 run_server，未選擇原生 controller factory。SharedCredentialServer 在 listener bind 後、start 前呼叫 plan.controllers；SharedListenerRegistry::observe 在 start 前無可用 endpoint。因此日後來源工廠必須保留同一 registry 與 configuration，將 Directory::from_source/from_catalog 延至 account Prepare 執行時取得當前 listener，不能在工廠建立時假造 active snapshot。Stored account 的實際權限、native summary 對應，以及世界 Reserve 所需 native offer、actor handle、presence/current/release 等來源仍需實際擁有者供應；JSON flags 不能代替這些來源。

三個子代理分別處理精確 Lua 分支、補給交易與回覆投影、CUSTOM 來源與正式入口依賴。本輪只做來源修改、讀取、差異與雜湊帳目，未執行 C++、Lua、原生程式、API、伺服器、資料庫、建置或測試，也未部署。新增完整雙向路線、opcode 及 phase binding 均為零；全遊戲分母和完成百分比仍未知。
