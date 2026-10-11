# 第205輪：CN 主技能第一筆序號的原生資料條件

本輪是203至207共五輪中的第3輪。目標仍active，207完成後暫停並停止子代理，不開始208。本輪是靜態原生來源與C++串接，沒有建置、測試、原生／codec／runtime、DB／SQL操作或部署。

004D3B60的完整67B純資料leaf已由第200輪保存，今輪保留原件与精確原始SHA，不重算新恢復bytes；004DA630的第204輪type2 caller68B也保留。今輪new bounded native bytes為0，retained為135B；新增的是此前未接入共用操作輸入的Current-qualified firstlookup→gate來源。

原生gate先讀UI+430A8的role再讀role+D0，沒有role-null guard。只檢查selected row不為null、ordinal為signed nonnegative、row+258+4*ordinal的pointer不為null；不檢查count、flags、bank或Current。之後要求definition BYTE67非零，definition unsigned WORD42小於等於role+64的完整unsigned DWORD；unsigned比較包含等號。原生沒有對這些欄位提供server learned/cast權限，欄位玩法語義仍不冒稱MP、耗費或戰鬥能力。

CnWorldPrimarySkillSource新增project_actual_first_primary_gate，把既有完整DWORD kind／id的first physical ordinal投影與這個原生gate連起來。它只接004D2B50→004D3B60的first-match組合，沒有對任意ordinal提供未限定的原生gate。完整owned選中row／bank及Current是獨立来源資格；原生leaf本身沒有這些檢查。第一筆為ordinal0仍正常處理；qualified -1結果變成false，不另尋後面的重複項目。沒有截斷參數、讀auxiliary list或將flags當優先權。

PrimaryGate owns原始lookup、第一筆definition pointer、BYTE67、WORD42、inline DWORD64及predicate。DWORD64由完整角色來源的counter order index1取得，不是selected-row2C／30。這些是已擁有的raw值，native gate在BYTE67為0時不會求值WORD42／counter64，不能把retained數值記錄冒稱原生當次分支已讀。Current在投影前後確認，同source reentry／stale皆終止，外層null資格失敗與合格false分開。

CnPrebornSkillChoiceSource只有選用actual primary supplier才一次投影並保存gate和same lookup ordinal；absence仍未知。保留每個request word的高／低byte投影、原始順序與重複，沒有冒稱它們來自004DA630的signed-WORD mode table。predicatefalse只是owned來源事實，不拒絕UI選擇、不賦予或撤銷common技能權限。只有failed Current才拒絕來源，沒有退回同key目錄或geometry假裝成功。既有Window把owned facts送到實際共用操作／post-commit delivery，不在commit後重用obsolete Current。

本輪修改4個C++來源檔、新增來源區段1，累計195。新完整雙向gameplay route仍為0；實際Main、learned actor、書籍custody／扣除、持久交易／durable event／原生回覆及WORLD→battle primary materializer仍有缺口。未修改原生EXE、字體、繁簡轉換、等級、帳號存檔或凍結功能。

| 範圍 | 本輪結束數量 | 計數範圍 |
|---|---:|---|
| TW C2S opcode observed union |156|151 generic＋5 supplemental／6 branches|
| CN C2S opcode observed union |156|本輪無新增opcode|
| TW WORLD S2C length entries |252／256|230 fixed＋22 variable、4 unsupported|
| TW BATTLE S2C indexed entries |110|9 special＋101 default；83 actions23／86 selectors7|
| CN S2C phase entries |280|account6／world206／battle68|
| CN receiver contexts |14、12有具體限定|47DE70／4812B0仍unknown|
| TW WORLD parser review |42／65＝64.6%|只有這個parser範圍的review比例|
| partial owner chains |38|CN35／TW3；不是fullroutes|
| endpoint rows／source groups |958／28|不是全遊戲總數|
| partial source segments |195|194→195|
| 本輪新增完整雙向玩法route |0|來源predicate不算可玩完成|
| 全遊戲完整路徑總數／百分比 |unknown／null|全方向、狀態、變體、deferred分母未完整|

下一步追實際主技能正向寫入端及4DA630 mode-table來源，不再把既有raw leaf當新發現。共用學習、custody、扣書、save／durable、精確回覆、實際store lifecycle／Main issuer、TW／CN／web數值64與stack99及其餘雙向玩法仍待接。全部来源完成後才全面測試、修復及發布；本次停止點仍207。
