# 台服延後扣血的有號域與世界身分生命週期（round470）

本輪修正標準戰鬥結果公開介面的表示契約：原生86能保存完整DWORD HP，
不代表稍後的83扣血也能正確計算所有DWORD值。核心64位元與絕對HP封包保持原範圍。
原生世界身分的alias writer、sender custody及原始公式producer亦繼續追查；
尚未把這些研究當作完整玩法或遠端採納證明。

## 現用原檔與靜態證據

TW God2.exe SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆技能BIN維持
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整證據、REA、review與唯一正式盤點在
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/battle-owner-source-round470/`。

`formulas/native-deferred-hp-domain-v1.json` SHA256：
`726a6d2c85b4e2960ea1a0de20ac85f778657b86914fa620bada35d490eb55b6`，
重新核對七函數、2,379條目前原檔指令，未重新執行VM或客戶端。

## 收到DWORD與有號扣血是兩條不同契約

51729A/51729D取86的logical DWORD5/9，5172AB呼叫52D840；actor查找成功後，
52D86C直接存current到DE8，52D875直接存max到DF0。這些寫入在display handle gate前，
沒有INT32_MAX限制。敵方52D8C0/52D956走相同writer。constructor51FDE0的零填充
範圍[DB0,DE8)不包含DE8/DF0，也不提供任何隱含的有號安全預設。

BASIC52364A與一般技能524D72把收到的WORD量MOVSX成signed DWORD後交528A70。
528A79先做DWORD ADD；528A7F是JNS，檢查結果的sign flag，不是overflow檢查。
結果有號負數即528A81寫HP=0。否則528A93/528A95以signed JLE比較結果和DF0，
超過時528A97把完整raw max寫回。將WORD8000解為−32768本身正確，問題在HP域。

下表為原始指令的手算反例，並非本輪遊戲／VM實測：

| current / max（hex） | 扣32768的數學結果 | 原生所選分支與寫入 |
|---|---:|---|
| 00009C40 / 80000000 | 7232 | sum正數，但大於signed max；寫80000000，反而加血 |
| 90000000 / 90000000 | 2415886336 | sum最高位為1，直接清成0 |
| 80000000 / 80000000 | 2147450880 | sum正數，signed max比較卻把HP恢復80000000 |
| 7FFFFFFF / 7FFFFFFF | 2147450879 | sum與max均在非負signed域，正確寫7FFF7FFF |

在0<=current<=max<=INT32_MAX且delta∈[-32768,0]時，數學sum介於−32768與INT32_MAX，
不會溢出signed32；negative分支正好floor0，nonnegative分支與max比較亦正確。
這是所選負量consumer的一致表示條件，不是原版整體HP上限，也不證明正向治療溢位規則。

## 實際來源修正

RecoveredBattleAttackPresentation::require_deferred_hp_target在完整uint64值上檢查
非零max、max<=INT32_MAX、current<=max，先檢查再轉換。標準PK對兩個收件者的
既有renderer分類做完整preflight，只檢查本次受擊target；另一角色的高max不變成全局上限。
special526890的現有scalar outcome不加該量，仍以HP86絕對值更新，不套這個限制。

實際Application診斷encoder僅在animations=true、標準BASIC／kind0或1的id1路徑
檢查；animations=false的絕對HP86路徑不改。手動功能僅BASIC分支增加相同檢查。
format-only helper仍不持有HP狀態，註解明確要求stateful caller先核對target。

不改native_hp_dword、不改ExtendedHealthAmount／BattleNumericProfile、不改DB存檔或
64位元核心、不選較小的玩法上限、不截斷、不新增假的大數值native profile。
formal126/150及manual126既有bridge限制保持；其完整高HP域需另行資格，不因本輪放寬。
目前owned PK room與Lua owner明確限定LegacyCustom，Battle該profile maxHP<=1,000,000；
因此本輪修的是公開Extended/template wire契約，沒有宣稱已重現現用玩家的高HP錯誤。

回歸原始碼涵蓋INT32_MAX邊界、80000000／90000000／FFFFFFFF高max、低current加血反例、
兩個出手方向與PK視角、一般／特殊renderer、獨立高source max、寬值截斷拒絕；
真正Extended Battle::act經手動BASIC encoder拒絕後，完整checkpoint／HP／MP／revision／RNG
保持，改以既有絕對DWORD encoder重試等於相同seed的新Battle。這些案例沒有執行。

## 世界R0的alias writer與owner交接

`identity/native-identity-lifetime-conclusion-v1.json` SHA256：
`6cccd88cf4b49e10820e9284182f20f05c05a0c033e1cd497473cf80c5b2acd6`，
共核對13函數、6,717條目前原檔指令；新兩函數REA與分析handle均已關閉。

上一輪證明B+48由Main擷取當前World R0；本輪發現CF世界交接的真實alias writer：
46B3E2取W+1539683C的指標，46B3EB呼叫468120，46B3F0取剛取得的2A body0，
46B3FD AND3FFF後46B405寫[R]。468120只重設R+15F/160/164及[R+168,R+4028)，
不清R0；後續明確寫入才是本次身分替換。只掃exact displacement的store會漏掉這條鏈。

468160的468763八格表已展開，46876A..4687A1補充分支只寫DWORD R+24
（依分支為7、0、1、2、3、4、5、6），不重寫R0。另取得並關閉
501810／502210的兩函數REA，直接body為R的呈現欄位更新，未見R0直接store；
opaque子呼叫與WORLD外掛714200仍開放，不能因此宣稱全局只有這幾個writer。
4643B0的46453A另有REP STOSD清[R,R+469C)，確實包含R0；40E070／40EF49
目前僅為caller byte candidates，未證同一實際W，不將它們直接套成現用玩家重入事件。

實際PK admission在進InBattle後明確改用committed hold與完整owner tuple，
不依賴已失效的prebattle Current；正常world handoff同步釋放presence／transport／delivery，
原ready lease失效，不是已證缺陷。仍待加固的是任意合法world sender後續輸出2A/CF時，
原始normal2A Written來源未有獨立的R0 sender incarnation。應只撤銷這個世界alias資格，
保留其他NormalInit資源契約，並區分phase與自己的original2A；不能把同號world1C或
battle86/5一律視為R0 writer。此接線尚未實作，也沒有解鎖友方效果／selfslot／turn authority。

## 原始公式與驗證界線

技能量的526120顯示上游仍是5251A0讀source28A[0]，已核對的52B619 writer來自
收到的logical WORD9；收到結果的HP算式不是原始技能傷害／治療生成公式。
命中／閃避／暴擊、攻防／五行、抗性與持續tick仍待真正producer／alias來源。
round469歷史label range59D8C4的描述也與實際+5E選59D8D4區別；數值%d／CRT與
BASIC59D968邊界證據不受影響，舊receipt保持原樣。

本輪獨立靜態審查與唯一正式盤點完成後封存source／storage／publication收據。
PHASE1未建置、執行測試、target／VM／codec、遊戲DB SQL、遷移、啟用或部署。
新增完整玩法數0；全遊戲分母／完成百分比unknown/null，goal active。
