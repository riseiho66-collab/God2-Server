# TW 戰鬥欄位與每條連線的世界生命週期來源

本輪 `20261008-tw-battle-state-source` 延續全遊戲 TW／CN／網頁服務端目標。三名代理分別新增角色控制欄位視圖、管理控制欄位視圖，及實際 Session 世界入口的每連線 factory 呼叫。六個 C++ 檔案有來源增量：新增兩個 header、修改四個既有來源。這是 PHASE1 來源工作，沒有建置、測試、原生執行、資料庫存取、部署或客戶端驗收。

## 本輪實際來源

`RecoveredBattleActorControl.h` 保存完整 15 bytes，只涵蓋 S2C `83/02`、`83/0C`。欄位為原始 action、source BYTE、logical+3 operand、logical+5/+7 的兩個 WORD mask；其餘原始 bytes 保留。原生 source 範圍 0..27 有定點指令證據；不借用攻擊 01/03 的單目標、敵方、非空 mask 或傷害限制。共同 setup 條件成立時寫 actor+1E7/+1E9；02 分支再寫 +1EB=03，0C 的 setup 分支直接返回。這不是防禦、逾時、復活或官方伺服器規則的證明。08 只保存研究證據，不納入新增欄位視圖。

`RecoveredBattleManagerControl.h` 保存完整 17 bytes 的 `86/selector2`。logical+3 為 mode；mode1 才讀 logical+5 的原始 attachment index。index<2 和非空 pointer 只控制 attachment cleanup，index>=2 仍進 side1 迴圈，因此不可加上 index<2 的封包拒絕規則。mode2 走全部 primary actor reset helper；其他 mode 在已追的 bounded handler 不呼叫這兩個 helper。logical+2 保持 opaque，未證明為 actor 位置。mode1/2 原生線索先前已有，本輪新增的是欄位視圖來源，原生 helper 新發現數為 0。

兩個視圖的 runtime emission／mutation 都為 false；沒有 issuer、排程、遊戲權限、狀態更新或實際服務端回包 caller。不能算完成雙向戰鬥路徑。既有 86/3、4、5 的來源定位只是補充：3 的完整權威 caller 未證明；4 的 ordinary appearance 及 5 的 primary grant 有 CUSTOM-0086 呼叫位置，但不能當作官方權限與時序。6 雖與 0 共用 case，side0／side1 的 native consumer 不同，仍不授權 alias 為 HP 更新。

`Session::RecoveredCharacterHandlers` 尾端新增 `common_world_lifecycle_factory`。既有 handler descriptor 會由 TcpServer 複製給多條連線，因此 mutable Binding 必須由每條 Session 自行建立。constructor 只檢查組態，不執行 factory；實際 selected character 與完整 world frame 產生後，在 game executor 呼叫一次 factory，取得完整 prepared／ready hooks，再走原有 prepared、尾端 ready 與 cleanup 順序。factory 与 direct hooks 不能同時由外部配置，空 hooks 或重入不會作成功回退。

`SharedTaiwanWorldLifecycle::factory` 捕捉真正的 shared presence、visibility 與 mandatory Entered owner，並在每條 Session 的呼叫位置建立 fresh Binding。既有 Binding／hooks 的 native lease、activation、實際 InWorld 狀態與 disconnect cleanup 邏輯保留。沒有加上空 Entered=true、假位置或只改 state 的捷徑。

## 仍缺少的正式世界來源

Application 尚未配置這個新 factory。現有 legacy world-ready 呼叫時 Session 仍為 CharacterSelected；共用 lifecycle 要求真正 scene publication 後的 InWorld。還缺持久位置／revision、scene revision、raw cell／previous direction、native 完整 5D 與逐收件者 6F／5E／73 資料來源。舊 Movement ack(sequence)、配置的初始座標／revision0 和 DiagnosticRemoteActor 模板不能替代這些正式資料。SharedServerPlan::Context 尚未提供同一份 TW／CN presence／visibility，也不能宣稱 Main 已啟用共用原生世界。

## 證據與計數

保留上一輪完整 30 筆 TW 戰鬥 subdispatch inventory，僅另存本輪 annotation；不覆寫舊基準。83 的 23 個 action 值、86 的 7 個 selector 值仍有狀態、caller、queue 與 producer 缺口。mapped native image `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`、unpacked PE `5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`、已安裝字體還原版的既有基準是不同 epoch；不得互換驗收資格。

本輪新 opcode／phase binding／完整雙向路徑均為 0。兩個新增欄位視圖涵蓋既知三個 subcase（83/02、0C、86/2）；Session factory 的實際呼叫接線新增一處，尚未完成 Application hosting。

已盤點 TW C2S 156 個候選值、S2C 252 個長度表值；CN C2S 156 個候選值、S2C 280 個分階段 endpoint。這些數字的計數範圍不同，不相加當全遊戲封包總數。完整遊戲路徑分母與完成百分比維持 unknown／null；未把 parser、raw view、CUSTOM 子路徑或拒絕路徑當全遊戲完成。

來源／原生 bytes／讀取區段／各階段副本與缺失 before 紀錄位於 `artifacts/integration/packet-connections-20261006/tw-battle-state-source-01`。上一輪封存全檔、before942、凍結檔與每個 agent seal 都納入本輪靜態來源帳本。繼續追正式資料 owner／世界 hosting，再追所有原生 producer-consumer 狀態變體；全部來源串接完成後才集中測試、修復与發布。
