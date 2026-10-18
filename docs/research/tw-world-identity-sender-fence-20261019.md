# 台服世界身分輸出資格的失效處理（round471）

本輪將原始normal2A的sender資格接到實際Session輸出FIFO。後續真正的2A／CF record
或無法完整判讀的輸出在排入時撤銷舊資格；相同原始bytes再送一次不能恢復。
這是本機sender custody檢查，不代表遠端R0、同一World配置、selfslot或客戶端採納。

## 來源與既有缺口

現用God2.exe SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆技能BIN保持
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整靜態證據、原始bytes、review與逐輪收據在
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/world-identity-sender-round471/`。

round469／470已證：named2A的body0 low14寫World R0；Main於戰鬥初始化前擷取當時R0，
複製到B+48；82 context_a/b是另外欄位。CF的46B3A8經415690尋找**另一筆獨立2A record**，
46B405才重寫R0，不是從CF body中搜尋2A子字串。2A logical是37 bytes，CF是177 bytes。
全域R0 aliases、World配置epoch及外掛／間接路徑仍未完整閉合。

原Session只保存原始2A已完整寫入、原始Entry指標、完整owner與normal初始化生命週期。
同一Entry保持current時，generic world sender仍可排出後續2A／CF或opaque bytes，
卻沒有單獨的sender資格失效記錄。正常world handoff本已撤銷ready lease／transport，
不是本輪要修的缺陷；也未宣稱已重現特定玩家錯綁。

## 單向狀態與真正輸出佇列

每個私有Entry持有獨立TaiwanWorldIdentityWriteFence；不共用actor-status epoch，
不以角色id、lease或公開的actor scalar代替原始Entry。狀態只允許：

| 狀態 | 合格轉移 |
|---|---|
| Unbound | exact original Write被真正FIFO接納後，進BaselineQueued |
| BaselineQueued | 同一原始Write完整完成後，進BaselineWritten |
| BaselineWritten | 可供本機sender資格檢查；沒有重新初始化捷徑 |
| Revoked | 終態；失敗、取消、重送、重複或延遲completion均不能恢復 |

原始normal2A的private Write marker必須在append_write前設定。中央sink先檢查
原始Entry、完整原始frame與該Write的custody，才建立baseline；generic送出相同bytes
沒有這個marker，只會構成後續alias輸出。撤銷在queue insertion前完成，配置失敗、
取消或尚未實際送達都不能讓舊資格重新有效；延遲的原始Written亦不能復活它。

已存在live原始Entry時，後續輸出按完整外層frame與logical record邊界判讀。
含2A或CF即撤資格；截斷、不支援或無法完整解出的輸出亦保守撤資格，輸出bytes本身不吞掉。
普通完整record body中的2A／CF值不當作opcode。1C、86/5與PK bootstrap按其完整record
邊界處理，不因同號的另一phase語義而被誤判成世界R0 writer。

CharacterSelected的postbaseline、InWorld與InBattle均不豁免後續輸出；
auth／選角回覆在沒有live原始Entry時不被重解成WORLD並授予資格。
所用既有ServerRecords表提供server grammar邊界，並未證明所有recognized opcode
在現用EXE所有phase都不改R0；「沒有已知alias」不等於全域harmless。

## PK讀取與權威交接

NormalWorldInitialization新增唯讀sender資格查詢；既有entry_written與整份
normal_world_initialization_current生命週期、原始frame／tail及其他資源來源不變。
NativeIdentity observe/current與QualifiedSceneHandle PK capture額外要求該資格，
保留完整64位元Session／帳號／角色／generation與獨立1..FFF handle，不截斷或重綁。

Preparing／Held直到commit前由真正Session source反覆核對。既有held bootstrap已在FIFO，
先於它的alias已使來源失效，後到的alias排在它之後；commit後依原設計承接private
committed hold、完整owner tuple與實際Written／outbox，不能繼續以prebattle Current
自毀已接管的battle。後續alias仍撤銷未來再次capture的舊世界資格。

正常PK bootstrap是82、appearance86、1C、HP／MP86、88的合格序列，不含2A／CF，
因此不因自己的入場bytes誤撤世界資格。世界sender fence不補造B+51自身slot、86/5權限、
出手／回合權限、友方累計效果或native ACK。

## Battle queue的額外界線

本輪重核5140C0：514315取head opcode，51431C/415840取完整record長度，
514327以第三參數0呼叫51D3D0，因此51432D只peek/copy，並不移動head。
51D444/51D487須advance flag非0才更新ring+8；不能把完整copy誤推為consume。
default與後續其他advance仍需完整caller證據，Net到此local queue的producer／phase路由
亦開放；2A／CF不能宣稱必定保留或必定丟棄。InBattle撤sender資格是保守來源處理，
不是已證明該wire record在遠端重寫R0。

## 回歸來源與驗證限制

純helper案例涵蓋原始Write狀態、完整多frame／多record判讀、body同值、真2A／CF、
opaque／截斷、取消、失敗及延遲Written不得復活。實際Session socket案例核對原始
選角／tail／normal初始化、完整64位元身分、一般輸出、PK Held阻塞FIFO及實際commit／Written
交接；不能以單獨helper測例冒充真正Session接線。
socket案例使用合成owner／bootstrap fixture，未覆蓋完整InvitationService資料庫與玩法授權；
延遲原始completion的確定順序由純CAS案例覆蓋，不能宣稱已強迫socket重現該時序。

獨立靜態review、唯一正式盤點與source／storage／publication收據外存。
PHASE1未建置、執行測試、客戶端、VM、codec、遊戲DB SQL、遷移、啟用或部署。
這些案例是回歸原始碼，不是測試通過或native驗收。
技能傷害／治療、命中／閃避／暴擊、攻防／五行與持續tick生成公式仍待真正來源。
完整玩法新增0，全遊戲完成分母／百分比unknown/null，goal active。
