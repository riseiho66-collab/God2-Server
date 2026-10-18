# 台服公式consumer續追與C9技能狀態倒數（round460）

本輪找到完整的**客戶端技能狀態倒數顯示公式**，新增C9無損C++視圖與
mode3倒數計算。另往下閉合攻防／五行轉送及累計效果尾端，發現受條件控制
的HP清零旁支。它們都不是原服傷害、暴擊、抗性或DoT量的生成公式。
上一輪kind／selector20權威結算限制維持；完整玩法新增0。

## 現用來源與方法

TW EXE SHA256：`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆BIN：`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整證據根目錄：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/formula-consumer-closure-round460/`。
三條獨立靜態支線使用既有REA6.5.0公開launcher／Ghidra，原始sections保留，
新增analyst CALL不是原始caller，分析映像均未執行。skill-bank v20有94個seed，
SHA256為`90d38ecbbf0ac3989ea313eed307ddafbbc8c792ffc6de5172a8694f12d6848c`。

REA Evidence：

- role-deep六函數：`ev_1efa515598a08bfa40843537af9cace61b9afda9cd30f288a9385c15d4dca6ed`。
- amount-tail四函數：`ev_0be5bf686b4be960dcf47e66d5a496372a0c20b88823239a2ed19314a9ed1fc3`。
- skill-bank五函數：`ev_4b11a0f0435ce44687dbd623c080789d6422e7a907cc34756bdd4d07fbde66a4`。

完整偽碼、原始指令與close回覆外存。新helper先AST／語法檢查後單次執行；
amount-tail v4的tuple錯誤原件／失敗紀錄保留，修正另建v5，沒有重跑失敗版本。
所有語意主張以原始bytes／限定CFG為準，不以偽碼成功數或候選數替代驗收。

## C9的實際來源與9-byte格式

目前WORLD根468AE0的原始表46B5D4，第C9項為46B2C6，46B2CE呼叫4E72F0，
輸入指標是logical+1。4012D0的原始長度leaf為`B8 09 00 00 00 C3`。
另一個原始caller519832也呼叫相同receiver；本輪只保留其call bytes，沒有
藉此宣稱整個battle dispatcher或所有狀態均已閉合。

| logical位移 | 原始欄位 |
|---|---|
| 0 | C9 |
| 1 | mode BYTE |
| 2／3 | definition kind／id BYTE |
| 4 | 未命名opaque BYTE |
| 5..8 | 收到的DWORD；mode3顯示時解為毫秒 |

4E72F0查role+44B8的三個20-byte entries。相同definition identity可更新既有entry；
否則在kind<4且找到空指標slot時建立entry。definition指標仍來自role+4474，
算式為base+kind*6E04+id*110-106，不能直接當BIN file offset。
entry+4存mode，+8存收到的DWORD，+C存本地timeGetTime；+10存圖示descriptor
查表結果再加**0x0A**的字串指標。後者不是收到的數值倍率或十六進位+10。
三slot滿載、definition來源／有效性及其他清理者仍是實際caller／生命周期缺口。

## 已閉合的倒數顯示公式

4827E3呼叫4E8910。該reader讀winmm.dll!timeGetTime（IAT5707BC），
對同三個entries的mode3採用以下32-bit機器語意：

```text
R = signed32((origin_ms + received_duration_bits - now_ms) mod 2^32)
S = trunc_toward_zero(R / 1000)
M = trunc_toward_zero(S / 60)
H = trunc_toward_zero(M / 60)
顯示：名稱 H : (M % 60) : (S % 60)
文字可見 iff R > 0
```

4E89AD／AF判定的是原始剩餘**毫秒R**，不是已截斷的秒數。因此0<R<1000
仍顯示00秒。原格式`%s %02d:%02d:%02d`中的02是最小寬度；H不取%24，
也不縮窄成BYTE／WORD，正數DWORD上界可顯示596小時。
先運算再判R是否非正，負值的signed商／餘數不會顯示。
mode0跳過，mode1／2顯示儲存字串；此reader對其他非零mode也走字串分支，
但圖示reader4E8600只准1..3。不能替未知mode發明通用規則。

到期只清文字，不清entry、技能definition或start，不更新HP，也不觸發DoT。
這不是server epoch、任務倒數、技能資格、狀態永久移除或每回合扣補量。
`role-deep/world-status-timer-qualified-v1.json`保留124條選定原始指令、
signed除法、clock import與格式bytes；後面的屬性分配UI分支未借來作timer證據。

新增`RecoveredRoleSkillStatus.h`以owning array保留全部9 bytes，解析只檢查
opcode與完整長度，不刪零值／未知模式／不明identity。mode3的`countdown`
接收caller提供的本地origin與now，使用unsigned32 wrap、安全int64有號映射、
C++20截斷／餘數，回傳remaining_ms及時分秒；`text_visible`只看remaining_ms>0。
此純資料／計算視圖不讀clock、不占slot、不發送、不保存或消費effect。
取得正確slot的接收時間與generation仍由caller保證；收到C9不代表一定被client存入。
獨立來源／指令／代數複核外存，沒有執行C++、測試或遊戲。

## 技能bank與攻防／五行深追

本輪從六處精確role+4474來源續追，而非再掃同一批EC4位移。
fresh REA核對4AA660／4AA830／4E72F0／4FEBC0／51B8C0：前兩者是既有技能
指標清單／旗標更新，4FEBC0建立另一份UI指標清單，51B8C0從選定容器回傳
skill pointer。這些是整筆definition的地址與identity鏈，不是+46倍率reader。
S34／世界技能事件／舊preborn相關發現標為既有研究的current再綁定；
不恢復退役地區的owner或玩法。v2 helper的新增timer位移候選仍沿用舊reason
標籤，實際結構資格以operand與`status-dispatch-v1.json`的更正為準。

九個真正role第一參數父callee的新深度掃描展開22個直接subcall、1347條
限定CFG指令，未見+94..B4直接欄位reader。完整role轉交4E72DF→4AC070仍是
HP／MP裁切與面板比例；4A870A→50CE10只傳role內字串；4E868C→4E62F0
只傳identity查固定12×66-byte descriptor。這不是全EXE無公式的證明。
4AC070偽碼遺失x87資訊而顯示`__ftol(0)`，不能當零公式；原始FILD／FIDIV／
FMUL浮點100與截斷呼叫才是這條顯示計算的依據。

另稽核50份現用來源，含31份Lua：所讀範圍未把未知+46或+4C..64提升為
原生命中／暴擊／傷害／治療係數。WORD42仍只是client MP門檻，Lua戰鬥仍
標CUSTOM-0006／0090。舊381技能書／24描述的raw70a4／decoded75c3與
現用raw ef297身分不同；舊研究新增日期警示，原描述、數字與證據保留。

## 累計效果尾端與真正HP清零旁支

52D9F0→508F50→508E70更新顯示快取與血條尺寸；51DE40處理source+700的
ACT文字控制項。其圖形／resource／global vtable callees仍未全部閉合，
不能概括為所有後續call都沒有HP副作用。

新的條件旁支是523E12→52B870成功返回後，source+5E8==9、packed target
+1EA!=9，且kind符合指定分支時，523E99呼526430。kind1保留packed target，
kind2才改成source；kind3跳過這一支。此前一次把kind1也讀為改source的
摘要已立即更正，原摘要與正確branch bytes均保留在receipt。

526430還依actor+DB8 bit0決定是否保留requested state9；缺此bit會轉成0／95h。
保留9才可經529870→5299F5將選定actor+DE8清零。529870另有state12h清零
條件，但未從本523E支線綁到，不能賦予猜測的玩法名稱。
同筆kind1／selector20接收在52CBCC把+5E8[index]清成0，不能將此state9
旁支當selector20一般HP公式；同slot／同receive generation仍須資格化。

兩consumer／兩caller限定CFG沒有直接清B60／B64／2C4，不能證明只結算一次。
播放+233會推進，但generation、完整reset、producer與保存仍缺。
因此保留round459限制，沒有用這條旁支猜測新的server傷害或狀態結算。

## 盤點與尚未完成項目

C9登記為independent S2C format，v29只新增此分類，原始native rows保持。
歷史149c...格式索引與本輪aaf0...函數證據分開保存，非全量current reinventory。
唯一正式靜態報告與source/storage receipts外存。完整玩法與部署新增0，
全遊戲分母與完成率維持null，goal保持active。
命中／暴擊、傷害／治療producer、減傷、五行相剋／抗性及真正DoT生命週期仍缺。
中毒扣當前maxHP十分之一是使用者規則，未把UI倒數誤作其週期。
PHASE1未建置、測試、執行target／VM／codec、遊戲DB SQL、遷移、啟用或部署。
