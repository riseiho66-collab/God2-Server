# 研究記錄的現用範圍

自2026-10-18起，本服務端只開發台服原生PC與其網頁入口
`/tw/native`、`/tw/native-game`。現用規則以根目錄的
[AGENTS.md](../../AGENTS.md)、[台服封包串接目標](../PACKET_CONNECTION_GOAL_20261006.md)
及[台服清理記錄](taiwan-only-retirement-20261018.md)為準。

本目錄的日期文件保存當時的來源、推論及驗證限制。舊文中的陸服、
TW/CN、四個WebSocket入口、多版本共用目標與「繼續／保留」要求，
均屬已被最新台服範圍取代的歷史記錄，不是現用開發規則。不得據此
恢復退役的協議、工具、匯入器、來源契約、產生器或安裝副本。
歷史記錄提到的已移出路徑，也不是現用建置或執行依賴。

混合研究仍保留台服需要的原生證據、來源交接及已知缺口，故保留原文
而不改寫歷史結論。台服的繁簡顯示、CP950／CP936、`zh-TW`／`zh-CN`
語系測例與Windows時區名稱屬文字顯示功能；不能僅憑語系名稱判為
另一地區協議，也不能因此刪除台服字體、IME或文字資料。

來源與靜態記錄不代表目前二進位已完成建置、測試、部署或原生驗收；
本次清理未授權開啟或修改遊戲資料庫、帳號、角色與存檔。

技能／公式續追的現用來源界線見
[round455記錄](tw-skill-producers-and-source-identity-20261019.md)，接收上游、
指標別名更正與技能整筆複本見
[round456記錄](tw-combat-queue-authority-and-skill-copies-20261019.md)。
其後D5預設關閉接點及戰鬥來源到Winsock的閉合，見
[round457記錄](tw-d5-skill-selection-and-network-origin-20261019.md)。
FC窗口格式、D5確認鏈與無損槽數比對，見
[round458記錄](tw-fc-selection-window-and-confirmation-20261019.md)。
累計效果與HP套用的分支更正、kind／selector資格限制，見
[round459記錄](tw-battle-accumulator-application-boundary-20261019.md)。
C9技能狀態倒數公式、攻防／五行深追與HP清零旁支，見
[round460記錄](tw-formula-consumer-closure-and-status-countdown-20261019.md)。
C9快取初始化與mode2面板發出C56的來源，見
[round461記錄](tw-status-lifecycle-and-c56-slot-source-20261019.md)。
中毒current maxHP十分之一的精確C++／Lua來源與真正tick缺口，見
[round462記錄](tw-poison-exact-share-and-tick-frontier-20261019.md)。
原生累計效果的第一目標選取修正、逐筆消費與持續狀態儲存契約，見
[round463記錄](tw-status-owner-storage-and-consumption-20261019.md)。
瞬影三煞斬原生命中扣血與提前HP回覆的重複扣血修正，見
[round464記錄](tw-skill-deferred-hp-source-20261019.md)。
普通攻擊、完整kind0／1 renderer分流、復活與PK儲存／送出的HP政策，見
[round465記錄](tw-basic-skill-revival-hp-policy-20261019.md)。
kind2／3的目標與累計上下文、完整DWORD回合通知及牛轉仙界踏HP檢查，見
[round466記錄](tw-effect-kind-context-and-bulk-counter-20261019.md)。
效果outcome的主要動作／累計／自身旗標分流及kind2位置重排，見
[round467記錄](tw-effect-outcome-owner-and-kind2-remap-20261019.md)。
自身slot／狀態mask來源、正常死亡路徑更正及逐角色70格效果容量，見
[round468記錄](tw-self-status-owner-and-native-death-path-20261019.md)。
戰鬥自身識別值的World／2A來源與標準扣血signed WORD端點修正，見
[round469記錄](tw-battle-identity-and-signed-loss-boundary-20261019.md)。
標準延後扣血的signed DWORD目標資格與世界R0 alias writer，見
[round470記錄](tw-deferred-hp-signed-domain-and-identity-lifetime-20261019.md)。
實際Session原始2A sender資格、輸出FIFO失效與PK交接，見
[round471記錄](tw-world-identity-sender-fence-20261019.md)。
實際 Written primary86/5 的自身視角來源、友方非自身效果與失效回滾，見
[round472記錄](tw-battle-self-view-and-friendly-effects-20261019.md)。
原始量值別名、C9同次初始化來源與兩項過期frontier更正，以及實際技能owner缺口，見
[round473記錄](tw-combat-generation-frontier-20261019.md)及其同名JSON現用索引。
實際 CommonWorld 選神後的完整來源、學習 chronology 與 PK 成對延續，
以及初始化 secondary header／controls 的 REA 補查界線，見
[round474記錄](tw-written-selection-successors-20261019.md)及其同名JSON。
2026-09-20技能書研究中的448筆、149c... EXE及舊SKB381配對屬歷史來源，
不能直接當成現用453筆／aaf0... EXE／ef297... gamedata的技能書或公式證明。
現用453筆BIN已保留來源，不代表權威技能玩法與執行profile已完成切換。
