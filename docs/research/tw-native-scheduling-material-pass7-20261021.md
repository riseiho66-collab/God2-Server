# 原服回合排程、身份外觀與返回後資料接續：pass7

本輪新增兩條靜態 REA 證據，並修正實際正常世界／戰鬥返回的持有者檢查。
範圍為 PHASE1 SOURCE_STATIC_ONLY；沒有編譯、執行測試、遊戲／VM、codec、
遊戲 SQL／schema、匯入、啟用或部署。新增測試原碼仍待集中驗證，不能視為通過。
沒有更改原版 EXE、帳號、存檔、NPC／怪物世界位置或資料庫欄位。

## 本輪修正的實際缺口

原有正常世界判定多以相同 Session、INIT、位置及資料內容判定有效。
移動綁定若被移除後以相同值重新建立，這些值可能全部相同，舊操作便可能繼續。
另有 canonical learning／selection 的 OR 分支跳過僅在最後 material 分支內的
移動檢查，以及最早／最後一次 SQL observer 前後沒有核對同一移動綁定的路徑。

現在 `RecoveredMovementService` 在真正建立 Position 時持有私有記憶體 identity。
正常移動複製／更新保留 identity；remove／prepare 會建立另一個，不能以同值復活。
`WorldLocationObservation` 分別提供同一 binding 與同一 pose 的純觀察，
不授予移動、入場、物品或資料庫權限。這不是新增可調遊戲參數，也不寫進存檔。

`RecoveredNormalCompanionCurrent` 合併實際 Session／完整 owner／原 Written INIT、
phase、battle generation、移動 incarnation 及操作當時位置。Application 保留
原 holder 的 binding，在第一次來源 SQL 前與最後純檢查都核對；合法走動可以
取得新位置，不能藉新 capture 把已失效的 holder 洗成有效。

這條檢查接到初次寵物／神將資料發送、返回後 canonical 接續、C25／C26 技能書、
C67 神將選擇、C24／C28 寵物格交換及相關 WholeBag／銀行入口。
技能書與神將選擇的實際交易前後均帶入當次純檢查；若 COMMIT 已成功才失效，
保存結果仍是 durable，但不發布成功／新 successor、不重試或虛構 rollback。
共用世界繼續使用原有 presence 權限，不借用正常世界移動能力。
初次原始2A尚未真正 Written 時，原恢復 Tick 延後查來源，不將 Pending 誤判為
失效而斷線；也不先發布寵物／神將、重送2A或製造新的入場權限。

PvE／SOS 保留真正入場時的移動觀察，從 member 收集、戰鬥 continuation、
逐人返回封包、寵物與技能接續直到返回後場景補送持續核對。戰鬥階段使用既有
私有 PvE binding，不能誤套只容許正常 phase 的 helper；個別返回亦不重新要求
整個已關閉房間有效。詳細改動與未執行案例見
[返回後流程複查](tw-return-pet-skill-followup-pass7-20261021.md)。

## 原服排程：補強來源邊界，沒有冒充找出公式

[回合 producer 追查](tw-native-round-producer-followup-20261021.md)核對
269 個控制頁 displacement 命中、41 個包含函數與8個具體 LEA 路徑。
這些已知 out-parameter 寫入範圍沒有到達 latch6C；仍只取得既有清零／讀取，
未取得設為1的 writer。值流圖明確 truncated，不能升格為全程無 alias 證明。

主／副動作列確有實際 enable、顯示與 hit-selection 鏈；已審動態 disable 多屬
另外的道具／技能子視窗，不能推出原服 action9 的死亡／配對規則。
S86/5 additive flags、A-first 消耗及 pass6 K pulse 繼續保留。
S88 counter 的服務端 producer、先手速度比較、平手、優先級及 RNG 次序仍未知。
現有 CUSTOM 排程沒有改名為原服公式，也沒有用動畫固定槽掃描代替先攻規則。

## 身份／外觀：取得完整本機定義，仍不等於完整 wire producer

[身份與外觀 producer 追查](tw-native-identity-appearance-producer-followup-20261021.md)
取得 `45A1A0` 的26B EnyName 配置、條件、欄位、component packing 與零初始化來源。
有效 recipe 限成功非空配置、合法來源／count／token、所需 `%d` 轉換成功；
原函數未檢查 sscanf 回傳，不能把 malformed token 的未定結果改稱原生補零。

戰寵 WORD7 的三個分支及8000優先順序已追到兩套 lookup；C000 與8000可 alias，
不同分支亦可得到相同 metadata key 而選不同 EnyName 定義。
因此不強制 reference 等於 saved species key，不自選 canonical flag。
E3／FB 保存與 panel 刷新沒有證明會產生完整 S1C／86/4。
世界6F快取提供戰鬥側欄文字，也沒有證明它等於 S1C renderer 的文字來源。

目前 csvZ SHA 與舊 Catalog pin 不符；目前 loader 區間 SHA 亦不同。
這只證明 byte pin 不同，不證明解碼資料或公式語義改變。
本輪未執行 codec，不借用舊 dataset、不只替換 pin 字串。
完整身份旗標／status、裝備到 component、變身與 reference lineage、所有 opaque
及17B wire 尾端來源仍需真實 producer。現有完整材料要求沒有被移除。

## 審查與交付界線

每項修正都追相關入口、觀察者、最後交易 cut、durable 失效、成功發送與返回接續，
修改後再由另一位審查者及整合者檢查原碼。銀行缺少完整真實 host fixture，
不得以任造私有 receipt 當成實測；新增來源案例與靜態檢查亦不替代編譯／遊戲驗收。
完整來源 SHA、REA 收尾、審查、唯一正式靜態報告與發布收據放在
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass7`。
首個材料 non-TTY helper 的失敗與強制自有程序清理保留，後續正常 close 分開記錄。

下一個有意義的來源是目前 csvZ 的合法來源資格、loader 上游 parser、變身 reference
writer 及已裝備 metadata 到 component 的 writer；原服排程則仍需實際排序／counter
producer，重讀相同 consumer 不能填補。完整目標與四小時 Discord heartbeat 維持暫停。
