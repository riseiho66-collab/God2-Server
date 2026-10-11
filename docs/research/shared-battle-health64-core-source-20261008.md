# 共用戰鬥 HP64 來源串接（20261008-shared-battle-health64-core-source）

接續前輪 HP64 資源儲存，將 Battle 本體、計算回傳與 checkpoint 連接到完整值。這是使用者授權的數值擴充來源，不是新恢復的官方戰鬥公式或已完成的原生封包。

BattleActor HP／最大 HP、CombatRuleResult.damage、BattleHit.damage／hp_loss、RevivalInput.target_max_hp、RevivalResult.hp、BattleRevivalResult.hp_gain 改為 uint64。MP、雙攻雙防、技能百分比、目標、身分、遮罩及原生等級保留原欄位寬度。絕對 HP 和正傷害表示範圍為非負 signed64，與目前 SQLite INTEGER 相容；這不選定 HP／傷害遊戲上限，也不套用仙幣上限。

BattleNumericProfile 明確區分 LegacyCustom 與 ExtendedHealth64。既有三參數建構呼叫仍選 LegacyCustom，保留 actor HP、MP、攻防及 damage 的既有 CUSTOM 範圍和 DWORD 運算。ExtendedHealth64 由可信服務端明確選擇，才允許 HP／damage 超過舊 1m 限制；MP 與攻防規則尚未扩充。不得從台／陸服、語系或輸入數值自行推定數值設定。

ExtendedHealthAmount::apply 直接使用 ExtendedBattleDeltaAmount 的有號變化。負值以 magnitude 與目前 HP 的較小值扣除；正值以 magnitude 與剩餘空間的較小值加回，避免乘法、加法、負號溢位，包括 magnitude 處理 INT64_MIN。Battle::act 驗證正 damage 可表示後轉為 signed64 負值，保留實際 hp_loss；revive 驗證規則回傳與 owned maxHP 後使用正變化。舊設定仍使用原 RecoveredBattleDelta::apply；apply_native_deltas 不接受 ExtendedHealth64，原 WORD／DWORD 累積不是擴充數值格式。

兩條操作都先建立 staged snapshot，完整呼叫規則、編碼，確定回覆非空才以 noexcept snapshot／RNG 指派提交；HP64 不改動身分、revision、目標、資源消耗、勝方與 callback 純度要求。可信規則或編碼器沒有授權、完整發送或儲存的替代作用。

checkpoint 版本 1 保留原九個鍵與十欄 actor layout，HP 仍依 uint32 解碼並受原 CUSTOM 範圍限制。版本 2 增加 numeric_profile="extended-health64"，HP／最大 HP 依 uint64 解碼。restore 要求版本與設定一致，保留 RNG runtime 身分、狀態、勝方、拓撲、revision、大小、canonical document 等檢查。版本 1 canonical bytes 相容目前屬靜態來源推論，沒有執行證明。不要默默將旧檔改寫版本 2。

實際 diagnostic-v1 儲存 writer、reader、terminal settlement 明確要求版本 1／LegacyCustom；PK 讀取與交換要求同樣設定及前後不變。初始 PK checkpoint 原先已與可信三參數 Battle 的完整 checkpoint 比較。新增 codec 支援不會單獨批准 PK／診斷大數值玩法；新的權威角色與 profile admission、政策、schema、回復及遷移仍需接入。

LuaEngine 的既有 combat.lua／revival.lua 不變。既有 bounded 入參／輸出檢查先於轉型；damage／revival HP 轉為已檢查的 uint64，MP32 保留；revival 的寬 maxHP 先拒絕舊範圍外值，再投影至舊 Lua 入參。二進位至少 53 位有效精度為 source static_assert，不是已建置結果。未提供精確大整數 Lua 戰鬥新公式，不能稱全鏈路 HP64 完成。

實際 native 回覆 helper 收到完整 uint64 hp_loss 再檢查 signed16 呈現範圍；HP 的原 DWORD 寫入與 bulk88 先取得 checked native_hp_dword 投影。Application 的三處 raw86／88 寫入、PK absolute／bulk、手冊、技能及復活回覆同樣保留舊封包大小與 bits，不截斷、不夾值、不以零替代。這些檢查不是最終數值擴充封包，台陸服物件、producer／consumer、顯示與網頁精確傳輸仍 OPEN。

ThousandBulls::presentation_losses 保留原碼；本輪未發現實際遊戲來源呼叫該 helper，工具與測試來源仍是舊範圍，不把未使用 helper 算成已接通分支。未修改既有 CUSTOM 公式、原生字體、文字轉換、聊天、認證或存檔內容。

三名子代理分别處理真實 codec、Lua 邊界及實際回覆 writer，保存修改前／後來源、實際閱讀範圍與封存。並行觀察不是同一時間的快照，早期觀察保留，最終來源另有當前雜湊。根代理保留 before924 及前輪 158 封存，不更新歷史基準。

目前仍需接上精確 wide Lua／原生規則、role authority、供給、正式 numeric profile／schema 遷移、雙版原生與 web 寬數值回覆及显示。全遊戲 phase／state／variant 分母、Application 正式挂入及其餘玩法、最後全面測試與可恢復發布仍未完成。新增完整雙向路徑、phase binding、opcode 均為 0，百分比 null。本輪僅來源修改、靜態閱讀與檔案帳目，無 build、tests、原生／C++／Lua 執行、DB／SQL 存取、遷移或部署。
