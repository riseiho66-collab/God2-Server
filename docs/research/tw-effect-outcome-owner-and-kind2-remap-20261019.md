# 台服效果結果狀態的owner與kind2位置重排（round467）

本輪修正既有Battle可信結果接口對敵方kind1累計效果的錯誤生死比對，並追到
主要動作與效果各自索引、實際死亡反應及客戶端自身旗標的分流。另以新REA
確認kind2的5251A0是位置／顯示重排鏈，不能當成通用自補血公式。

## 來源與範圍

現用TW EXE SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆BIN仍為`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整原始bytes、CFG、REA與source收據外存於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/effect-owner-source-round467/`。
重用已有合格函數證據；只有缺失的原生函數／分支另做REA。

## raw outcome不是每筆效果的HP判定

action0D非零WORD11的kind1接收，52C520僅在selector0由52CB8E讀raw BYTE14，
經52BFC0映為狀態並存至`5E8[n-1]`，其中n是主要動作的source239。
其他已解析selector1..5／7／8／9／20經52CBCC將`5E8[i]`清0，不讀raw14；
i是累計效果source2C4配置的entry。selector20仍被核心拒絕，沒有藉此放行。

但上游516AE0的action0D分支517142仍讀raw14，再於517163傳給5169F0，
之後517183才進52C520。5169F0先要求selected target為side0及client自身slot，
再對raw14<=33分派；raw0設client+A9E9C74 bit0，raw28清bit0，raw255安全返回。
因此「indexed數值storage不使用」不等於「整個客戶端沒讀」或畫面等價。
35條原始指令及完整switch另以REA核對，Evidence：
`ev_09fa5bf1e4d66146a90e5d65229978893b4f61c6cc4c77099b1580818dbdba5d`。
旗標的完整owner／玩法意義仍未閉合，不能猜成死亡、異常狀態或命中資格。
round468補到86/3狀態mask、86/5與1C的自身slot writer，以及正常死亡路徑
自行設定DB8的證據，見
[後續記錄](tw-self-status-owner-and-native-death-path-20261019.md)。
`owner/owner-index-kind1-conclusion-v2.json`保留16函數、5389條原始指令與連續
caller資格；5169F0新REA已close且terminal exit0。不同研究支線可能重疊，
這些指令數不是全EXE去重覆蓋率。

## 實際核心修正與保留邊界

RecoveredBattleDelta新增`kind1_accumulator_reads_target_outcome`，精確表示
52C520中kind1且selector0會讀該byte，沒有把名稱擴張為全客戶端讀取判定。
raw bytes、mask、selector及量的運算保持。

Battle對敵方side1（所選mask target14..27）的非零selector，不再按raw14
要求0／28或將它與HP生死比較：5169F0在該側提前返回，後續kind1 storage
也不讀raw14。原本敵方HP100、MP50收到selector9／MP−30／raw0會被錯拒；
現在得到HP100、MP20。selector1..5／7／8亦遵守同一已證明的分流。
這裡的side是該raw record的原生視角，不能把共同戰鬥的canonical side直接
代入另一viewer；若重新投影使side1變side0，必須另核對自身slot與旗標政策。
目前實際NativeDelta診斷owner是單一原生視角；paired PK未經此結果接口。

友方side0（0..13）可能包含client自身slot，現有Battle沒有該獨立slot owner，
所以保留既有raw0／28及HP一致檢查。這是尚未閉合來源的保守邊界，不宣稱
原生對每個友方都讀同一旗標。selector0在兩側也維持既有檢查；kind2／3、
selector20、來源控制權、revision、actor存在與原子提交限制保持。

回歸來源比較敵方selector1..5／7／8／9在raw0／28／255下的完整checkpoint，
包含HP／MP／revision／RNG；保留raw roundtrip。另檢查友方raw0非致死／255
及selector0既有不一致值仍不呼encoder、不發布狀態。這些是數值及來源案例，
尚未執行，不代表完整原版視覺或原服效果權限驗收。

## 主要動作target與效果target仍需分開

source239的n與source2C4的i不能互換。kind1 selector0的outcome寫到主要
動作最後一個slot，並不自動屬於當筆0D的packed effect target62E[i]。
524820的後段以source239枚舉base target23A[j]，525041..525056取這些target，
再讀5E8[j]與55C[j]決定是否經5250F0／526430設死亡狀態。
普通522FB0則使用primary235與5E8[0]。這補到outcome真正消費者，而不是
僅從位移猜測關係。

52B870的kind1會先按destination+1EA==9等資格跳過，HP加量後不會僅因HP0
自動呼526430；52BC50也沒有這個推導。Battle以HP決定陣營淘汰仍屬
CUSTOM-0007，不能冒稱原生1EA／死亡狀態已完整恢復。selector0目前的單筆
HP一致抽象也未取得任意n／i／mask的完整owner，仍是明確待接路徑。

`scope/native-delta-host-source-audit-v1.json`確認實際Application診斷回覆為
主要BASIC（source0→14、量0）、HP0D（−30）、MP0D（source0→0、−10），
再收尾BASIC（source14→0、量0），共四筆60 logical bytes，並非孤立0D。
兩筆kind1各有獨立2C4 entry；先前「第二筆MP覆寫第一筆HP」的候選假設已
撤回，不作為修正依據。kind2／3的n−1尾寫與kind1不同，仍不能放寬。

下一步需把base target清單、n／i、初始化／reset世代、播放owner及自身slot
接成一個有來源的上下文，再擴充完整結果與持續效果的原子結算。單純把
額外vector塞入checkpoint，或將HP0當1EA==9，都不能補齊這些權限。

## 5251A0不是通用自補血consumer

kind2中非ID69..71的路徑選5251A0。其六項substate switch與直接鏈顯示：
source25A／268的值用作packed position（除14／餘14），重排六層actor指標、
side／slot及manager2F4成員遮罩；WORD28A[0]交526120作文字顯示。
5297D0按kind2／id／side查姿態表59CED0／59CF28，再交41BF30。

限定鏈未見把received amount加減HP／MP，也未見R13／R14 outcome消費。
其中529870呼叫要求state13h或0，不能借用其state9／12的HP清零旁支。
原始直接鏈共重核1585指令；完整限制與四項decompiler warnings見
`self-skill/self-skill-native-conclusion-v1.json`。
新REA Evidence：
`ev_ac1cbb913eeffa9ead7899b88ebd9fd82f013dce415db70a843da1d58e5c785f`、
`ev_deabcada39456aa5f861d94a434be57d577f331326523bc175033ac5d3b76de6`。
兩個session已close且terminal exit0；分析PE的13個原始sections不變，
90個analyst seeds不是原始caller，映像沒有執行。

這只資格化所選kind2位置／顯示鏈，不證明全EXE沒有治療公式或間接副作用。
不將kind2套入現有敵方scalar hit，也不因接收端先改成source就猜成自補血。

## 驗證與尚未恢復

獨立靜態review保留早期版本及上游旗標發現後的修正版本；唯一正式盤點、
來源、容量與publication收據外存。分類仍沿用v29，完整玩法新增0，分母與
完成率仍null，goal active。原始傷害／治療生成、命中／閃避／暴擊、減傷、
五行相剋／抗性、持續狀態owner與tick及全部台服雙向路徑仍待續追。
PHASE1未建置、測試、執行target／VM／codec、遊戲DB SQL、遷移、啟用或部署。
