# 台服瞬影三煞斬延後扣血與提前HP回覆修正（round464）

本輪修正CUSTOM-0058的實際回覆錯誤：每筆83/03之後附帶扣血後的86/0，
客戶端會先寫入結算後HP，再於原生刀術命中事件扣一次。正式及手動126技能
現只送每目標一筆83，保留施法者MP及屏障後88快照。傷害係數、費用、選敵、
分身與玩家存檔不改；這不是新恢復的原服傷害公式。

## 來源、工具與界線

現用TW EXE SHA256：`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆BIN仍為`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
現存God2ShunyingClone.dll為
`8d1ec1c4d31af24fe3ff99f8bc452c714f73b327933049d677d891ea61d4a823`，
與2026-09-30部署記錄的接受版本相同；本輪未執行或修改DLL／客戶端。
clone_hooks.cpp的來源將126的preload與result同時映至原生kind0/id8；
clone_visuals.cpp只處理視覺，未提供另一次HP結算或抵銷提前86的修正。

完整外部證據：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/skill-producer-round464/`。
使用既有REA／Ghidra與原始bytes，沒有執行target、Lua／VM、codec或遊戲DB。
分析PE保留原始sections，新增analyst CALL不是原始caller，映像未執行。
新helper先AST／語法檢查再單次執行；v1欄位KeyError原件保留，另建v2修正。

## 連續接收、儲存及真正HP寫入

沿用證據重新對目前EXE核對：5140C0在同組83後繼續排空相鄰86；
遇到所選group／85／88屏障才結束drain，5145DB再呼52AC20排程播放。
因此把HP86排在83的bytes後面，不代表它等到動畫命中後才套用。
88另受514538的pending-83旗標保留，尚未呼518A90或consume queue即離開；
529020的原生播放gate返回非零後才恢復drain。非零亦可能來自既有10秒watchdog，
不能把此gate稱為所有命中事件成功或跨重連的一次消費保證。詳見
`native/skill-88-gate-followup-v1.json`。

新的86/0鏈為517230：friendly直接到52D840，enemy經52D8C0在52D956
呼同一writer。52D864讀current參數，52D86C直接寫actor+DE8；52D868讀max，
52D875寫+DF0。這是即時絕對HP，不是只更新面板。86/6另有分支，不借用本結論。

原生刀術kind0/id8由529181呼524820。接收時52B619把收到WORD9保存至
source+28A[index]；播放state4的命中事件逐entry取該signed WORD，
524D72的MOVSX後，524D79呼528A70。後者528A79加到target+DE8，
依既有符號／max規則裁切，528A9F再寫DE8。這是真正HP變更，不只是浮字。

例如初始HP150，服務端本次扣80，結算為70。舊回覆先令client HP=70，
原生命中再扣80，錯成0；新回覆讓client從150於命中扣80，得到70。
死亡仍由原本outcome0及播放流程處理，不用提前HP0代替動畫的扣血。

03/17每次receiver只保留首個mask目標，連續singleton記錄依序增加+239並保存
23A目標、28A量與224結果。現有兩自製技能都已每目標送一筆，不需合併或
改成多bit單筆。每目標只計算一次傷害，MP仍由Battle對整次cast扣一次。

本輪新REA五函數，兩session均close且terminal exit0：
`ev_cc4ac145e767ccd8413588e2db94945aa27e89bd87249938701bc2b2065a9d1c`、
`ev_a9594c046933f4413baf986e55b4540872414274783cf11c8814801f31926a44`。
334條新指令及2317條沿用指令逐bytes核對，完整warnings／來源／CFG見
`native/skill-native-conclusion-v1.json`與`native/skill-receive-playback-static-v2.json`。

## 真正實作與靜態回歸

ShunyingSanshazhanReply保留friendly MP86/1，取消每目標HP86/0。
DiagnosticShunyingManual僅在skill=true的126路徑取消HP86；BASIC原有回覆保持。
兩路徑仍先檢查target max/current HP可無損投影DWORD，不因少發86而放行
不可表示的狀態。所有失敗仍在Battle snapshot／RNG提交及checkpoint callback前。

回歸來源涵蓋雙方1／2／3目標、每筆15-byte83、精確負80／負10、緊接88、
死亡outcome與HP超DWORD拒絕；保留BASIC的153-byte83/86/88案例。
`scope/test-source-review-v1.json`完成三檔獨立靜態複核，沒有編譯或執行測試。
手動錄影126的9999浮字token沒有另一個HP owner；其原生clamp仍處理overkill。

牛轉仙界踏150原先已因四段自製HP timeline省略HP86，該路線不改。
普通攻擊、PK與復活有不同consumer；本輪不能把native8的結論擴大至它們。
早期source audit對全部動畫路線移除HP86的條件式提議已由最終review縮正。
未證明的BIN+46／+4C..64仍未當成傷害、治療或暴擊參數，既有CUSTOM公式保留。

PHASE1只做來源／靜態：未建置、測試、native／VM／codec、遊戲DB SQL、
遷移、啟用或部署。唯一正式報告沿用v29分類，沒有增加parser或完整玩法數，
全遊戲分母與完成率仍null。中毒觸發、原始命中／暴擊、傷害／治療producer、
減傷、五行／抗性與其持續狀態交易仍開放，未以本次扣血時序修正冒稱恢復。
