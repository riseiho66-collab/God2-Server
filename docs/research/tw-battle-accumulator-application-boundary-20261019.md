# 台服累計效果套用邊界與播放計數續追（round459）

本輪修正一個具體來源資格缺口：接收端的累計欄位運算，不能直接當成
所有原生分支的HP／MP結算。現用客戶端的selector20會繞過兩個直接scalar
更新call；kind2／3另改變套用actor或量的符號。服務端保留原始解析與累計
視圖，在整批權威結算前拒絕這些尚未完整串接的變體。沒有猜測替代公式。

## 來源與方法

現用TW EXE為`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
完整證據位於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/status-lifecycle-round459/`。
使用既有REA6.5.0公開launcher及Ghidra；vitals的v18分析映像SHA256為
`51ef0b9b7024be5f0feb13c58d5b1ce5e896f33a6f324a00fcd590519903ac57`。
13個原始sections不變，93個analyst CALL不是原始caller，分析映像未執行。

四函數REA為518A90／52D360／52BC50／52B870，Evidence：
`ev_686bc320b04008e9046dc4397c8ca469f7363b0384a939dfa7f546efe4a66381`。
完整偽碼、組語及close回覆保留。52BC50／52B870偽碼有removed-unreachable
警告，關鍵分支另以原始bytes與有限CFG核對，不能將偽碼當作全執行驗收。
新外部helper均先AST／語法檢查後單次執行，沒有新增專案Python。

## selector20的累計與套用是兩個階段

在83/action0D、非零logical WORD11的所選接收分支，ESI是logical+1。
52CB16讀payload BYTE+C，也就是logical BYTE13的selector。
原始兩層表52CCAC／52CC98將20導向52CB47：sign-extended logical WORD9
直接取代source indexed DWORD+B60。52CB75／78再將同一selector存入
source BYTE+5A2[index]。接收端的replacement運算仍由
`RecoveredBattleDelta::accumulate`原樣保留。

真正後續consumer有不同條件：

| consumer | 原始分支 | 直接scalar call的結果 |
|---|---|---|
| 52B870 indexed | 52BB43讀+5A2[index]；52BB4A比較14h；52BB63跳52BBEA | selector20繞過528A70與528AC0 |
| 52BC50 scalar | 52BE90比較+5A2與14h；52BEAD跳52BF40 | selector20繞過528A70與528AC0 |

這兩條分支仍做文字格式化及尾端52D9F0／51DE40呼叫。本輪限定結論是
**繞過所選consumer的直接HP／MP scalar更新**，不是所有間接callee都沒有
副作用，也不命名此效果的真正玩法。其他未綁定caller／狀態仍開放。

舊`current_damage_formula.py`的第三階段從獨立12BB84入口開始，刻意略過
中間formatting路徑。它能證明該live-in下的scalar算術，卻也略過了52BB4A
的selector20分支。因此舊selector20數例不是原始收到封包後自然走到HP更新
的證據。歷史helper與結果保留，不能回頭改寫成完整連續執行。

## 非零WORD11也不是單一套用模式

52CAEA／EE將payload WORD+A（logical WORD11）存到source+4D0[index]。
52CABA的所選接收分支只按1／2／3進入這段indexed建立流程。

- kind1使用packed target查找後的actor。
- kind2在52B9A5將consumer目標改為source；52BC50的52BD26也有相同改向。
- kind3的52BA0E對indexed HP累計量取負，另有actor／播放條件。

只看收到的量與target mask，無法替代這些模式。新增
`accumulator_kind_bits()`無損讀logical WORD11，保留未知非零值；解析器與
accumulator運算不因權威結算的限制而刪除原始變體。

`Battle::apply_native_deltas`在完整validation loop新增kind!=1及selector20
拒絕；此時尚未進入任何target更新、encode、checkpoint或publication。
`RecoveredBattleService`原本先複製Battle、成功後才commit，故整批含有
不支援變體時不會先提交前面的合法結果。既有一般分支未改成猜測的新算法。

這是縮小錯誤的來源資格範圍，不是kind1玩法全部閉合。原生mode1另要求
target lookup／renderer handle有效，且52BA90的target+1EA狀態會影響是否套用；
服務端尚未完整對應這些欄位與生命周期。不能用HP為0替代原始state9。

現有C++回歸檔補入混合batch的拒絕案例，核對不呼encoder、不改snapshot或
checkpoint；同時保留kind2／3／FFFF raw roundtrip與原accumulator案例。
**本輪沒有建置或執行這些測試**，只有來源與原始bytes的靜態複核。

## 88快照與K來源界線

timer支線新展開529020的nested renderer table5295FC，有限CFG為411指令，
沒有未展開跳轉。state13按renderer type與definition ID選不同callee；524820
只是其中一條。state11到522FB0，state81另到5244F0，不能共用一個播放consumer。
真正的兩個counter consumer入口為522FB0／524820，有限CFG分別1281／732
指令；最近padding對應的522F60／524750是相鄰短函數，不能借作相同entry。
52357B／524DC7的actor+277遞減用於pending hit完成後的死亡／受擊反應。
52A8D0六個command lowBYTE值01／03／0E／0F／12／17共用copy/increment277，
但未逐一閉合全部incoming來源。這不是DoT、技能剩餘回合或再次扣血公式。
舊死亡counter結論保持；新增的是目前aaf0原始entry與nested route的再綁定。
兩次REA Evidence為`ev_7a9af071345165d965338d17e10067453d97c3b5e7e8ab486d7c89702493aa8b`、
`ev_7faa32cca8875c3088dc9b906129895cb44ebdb5098254af61b5034cf181e846`，
完整warnings／close／source範圍見`timer/timer-status-lifecycle-conclusion-v1.json`。

目前518A90將收到logical DWORD1存入狀態／計數欄位，並將logical BYTE118
複製到owner+A9E9C84。52D360則對side0十四個slot，把logical DWORD5+8*i／
9+8*i原樣寫actor+DE8／DEC，再刷新顯示；沒有在此計算最大值或成長。
518A90更新本地面板時，max HP／MP來自既有actor+DF0／DF4，而非此88封包。
這是目前EXE的來源再綁定，不當成新恢復的升級／技能公式。

K線新增interior入口排查：143個branch byte候選中135個是既有函數內跳轉，
另外8個落在已確認指令內部；沒有新外部direct caller。519631→519E10是
獨立八指令leaf；看似0051A0E8的pointer實為44418B的E8／rel32 bytes。
468160部分CFG581指令中，4687FE將battle subobject存入stack傳入的外部
物件+4504；EBP不是battle／outer owner。精確4504只見此store，468763
switch及computed aliases仍未閉合，不能推論沒有非零K writer。
`k-frontier/k-frontier-conclusion-v1.json`保留原始bytes與限制。

## 剩餘範圍與盤點

命中／閃避／暴擊門檻、技能傷害／治療producer、攻防減傷、五行相剋／抗性，
以及真正DoT實例／回合遞減仍未恢復完整公式。中毒扣當前maxHP十分之一
是使用者規則，不能由播放計數或收到量重新宣稱為逆向發現。

PHASE1維持source/static：沒有建置、測試、遊戲／native／VM／codec、遊戲DB
SQL、遷移、啟用或部署。完整玩法新增0，分母與完成率仍為null。
本輪唯一正式靜態盤點使用v28 frontier；round458的v27失敗原件保持，
本輪的新盤點不算重跑或抹除那次失敗。盤點結果及storage receipt另存外部。
