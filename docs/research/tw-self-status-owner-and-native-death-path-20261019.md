# 台服自身狀態owner、死亡路徑與70格效果容量（round468）

本輪按現用原生陣列的70格容量，修正可信結果核心原有的整批64筆限制；
另外追清自身slot的多個writer與正常死亡路徑，保留尚未有owner的友方限制。
未由狀態mask猜測命中／暴擊或新增狀態封包。

## 現用來源

TW EXE SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆BIN維持`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整原始bytes、REA、CFG、review與收據外存於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/effect-self-owner-round468/`。

## 70格是逐角色儲存容量

52C520在source239=n為0時，重置該actor的effect index2C4及下列70格span：

| 欄位 | 原始span／元素 | 重置值 |
|---|---|---|
| kind | 4D0..55C，70 WORD | FFFF |
| HP／MP累計量 | B60..D90，70組8-byte pair | 0 |
| kind low byte | 55C..5A2，70 BYTE | 0 |
| selector | 5A2..5E8，70 BYTE | 0 |
| outcome | 5E8..62E，70 BYTE | 0 |

packed target62E另有70 BYTE，lazy reset不清它；每個新entry會先寫其target
再消費。最後有效index69的HP／MP是D88／D8C，exclusive end為D90；
kind最後WORD在55A，packed target最後BYTE在673。
52CADB及52BC14把2C4視為signed WORD；70仍是正數，consumer按index遞增。
`receive/native-effect-capacity70-v1.json`重核1544條限定原始指令，沒有找到
此鏈上的64比較；這不是對全EXE或原服發送數量的全域宣告。

原Battle的整批64筆限制可追至初始private import，未找到獨立原生或玩法
政策依據。現RecoveredBattleDelta公開唯讀indexed_capacity=70，Battle先按
最多28角色×70檢查整批上界，再在完整validation loop按source逐一計數，
任何source超過70即在更新／encoder／checkpoint之前拒絕。既有kind1資格、
selector20拒絕、來源控制權、actor、revision及outcome邊界保持。

這個容量不授予技能／回合權限，也不證明原服發過70筆。若client在同一
generation已收到i筆，剩餘實際容量是70−i；本接口的完整受信交換仍須由
caller保證起點與世代。數量檢查不能補造此上下文。實際Application診斷
producer仍是兩筆效果，Service的單一authorized source限制也保持。
原生frame的0xA00 logical上限不改；較大核心批次仍須合法分frame並通過
既有Service framing檢查，不能用1960筆容量繞過傳輸限制。

回歸來源涵蓋65／70筆同source、兩個受控source各70筆、合法frame大小，
以及第71筆令整批在encoder前拒絕、checkpoint／RNG不變。案例沒有執行，
不代表完整原生queue／一次消費或原服發送權限驗收。

## 主要動作與效果的重置世代

`receive/receive-generation-context-v1.json`重核14函數、5132原始指令。
實際BASIC prime經52C640→52C86F／52C87C→52C88B才增加n，故
prime→HP i0→MP i1會保存兩筆獨立entry，不會每筆0D重置前一量。
普通BASIC後段用primary235及5E8[0]；一般技能按j<n讀base23A[j]及5E8[j]。
i與n不能互換。packed target採side bit7／slot low4，不能把flat position14
直接當作其原始stored BYTE；其他opaque bits亦不能猜成額外座標。

whole ordered generation、主要action／target、初始i、播放owner及重播權限
仍要由真正來源取得。52BC50在本輪全部13原始sections的absolute pointers
及.text direct E8／E9掃描沒有caller；這是有限negative證據，不是全域不存在。
已綁定的indexed consumer仍是523E12／524FB8→52B870，不能任選另一consumer。

## 自身slot不只由控制通知設定

`flags/self-flags-owner-conclusion-v1.json`重核13函數、3008條原始指令。
已證實的client+51 writer包括：

- 5112C0初始化時設FF。
- 517590處理86/5：primary bit0時，以logical BYTE4低nibble更新自身slot。
- 515C90處理1C actor identity的所選合格分支：side0，且logical WORD3等於client DWORD48時，
  516382以position%14更新自身slot。

第三項是45-byte S2C **1C**，不是81；handler的EBX是完整logical pointer，
所以identity欄位是WORD3，不能套用其他handler的payload+1變成WORD4。
client+48的實際identity owner仍須另追，不能直接以角色DB id代入或截斷。
上述四個新REA函數及兩個工作階段均已close；warnings及原始callers外存。

Policy.client_actor／client_side只比對C2S欄位，actor_position另對應權威Battle
角色。既有pose publication是cosmetic，prepared grant亦不等於Written或
原生採用。現NativeDeltaLab一般沒有專用的self-view receipt，因此本輪不把
這些值當成自身slot權限，也不放寬友方效果。

若串接專用來源，至少需保留實際final bootstrap完整wire、原Session／帳號／
角色／battle generation及WorldResponseWrite狀態，並在任何1C、86/5、重新
進場／綁定時失效或重新解析。只保留最初86/5會留下stale slot；本地完整
寫入亦不能宣稱原生ACK。paired PK重排視角仍須自己的資格，不能挪用此slot。
具體來源稽核見`scope/native-delta-self-view-source-audit-v1.json`。

## 狀態mask與正常死亡路徑的更正

517480處理86/3，若logical DWORD5 bit0有值，先把完整DWORD正規化成1。
匹配side0自身slot時更新client+A9E9C74；52C3E0另在actor查找及signed handle
資格通過後，把相同mask寫actor+DB8，並複製logical WORD3到actor+278。這是收到的狀態遮罩／參數，沒有計算
傷害、暴擊機率或倍率。限定exact operand掃描未找到獨立input gate reader，
仍不能推論沒有別名／間接reader，也不能將自身cache當作回合權限。

51FDE0初始化會清[actor+DB0,actor+DE8)，DB8初值為0。這不代表正常死亡
缺一筆86/3：正常requested type9經526430時，5266F8自行寫DB8=1，
526726設1EA=9，之後最末bit0檢查通過，52678A→529870→5299F5將HP清0。
原本已是1EA==9的early gate及59h復活是另外分支，不能概括為所有狀態皆同。

round460的末端DB8檢查描述因此補上更正：不能把末端條件誤推成必須先有
外部status writer，也不應新增多餘86/3。既有攻擊／技能／復活回覆及保存
bytes維持。原先將5169F0稱作visual preloading的註解也更正為self-status
flag updates，避免把真實狀態寫入當成只有顯示。

## 驗證與剩餘工作

獨立靜態review、唯一正式盤點與source／storage／publication收據外存。
沿用v29分類，完整玩法新增0，全遊戲分母／完成率仍null，goal active。
來源容量、self-slot custody與native received-state不等於原始傷害／治療、
命中／閃避／暴擊、攻防減傷、五行／抗性或持續效果生成公式；這些仍待追。
PHASE1未建置、測試、執行target／VM／codec、遊戲DB SQL、遷移、啟用或部署。
