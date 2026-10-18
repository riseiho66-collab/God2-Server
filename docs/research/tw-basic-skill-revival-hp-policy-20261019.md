# 台服普通攻擊、技能與復活HP回覆分流（round465）

本輪將普通攻擊及目前一般技能回覆接到正確的原生HP消費方式，並同步修正
真正共用PK的producer、Session檢查、fresh結算及retained讀取。不能把所有
83後的HP86一律刪除：兩類技能renderer及復活的HP權責不同。

## 原始來源與完整kind0／1分派

現用EXE為`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`，
453筆BIN仍為`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整原始指令、REA與來源複核外存於
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/basic-revival-source-round465/`。

普通83/01的WORD9經52C615／52C626傳給52B060，52B3CD存至source+286。
所選non82h正常命中路徑，5235F8確認動畫完成，52363E先將substate轉0Ah，
52364A以MOVSX讀+286，523655呼528A70真正改target+DE8；另一播放分支
52388F／52389A也做同一signed HP套用。不是只有浮字，也不是0D累計量替代。
同組86/0會在排程命中前直接寫結算後HP，故普通攻擊亦不得重送此提前值。

529020對全部BYTE定義ID的kind0／1分派已閉合，不採逐ID擴增白名單：

| 定義範圍 | 實際consumer | 目前scalar回覆的HP權責 |
|---|---|---|
| kind0 ID96..103 | 526890 | 保留絕對HP86 |
| kind1 ID3、11、19、27、35、43、89..93 | 526890 | 保留絕對HP86 |
| 其餘kind0／1非零ID | 524820 | 原生命中套用signed WORD，省略提前HP86 |
| 普通BASIC1 | 522FB0 | 原生命中套用signed WORD，省略提前HP86 |

上表只適用既有codec的skill R13=0、R14=0／28。571610原表分別將0／28
映為type9／0；52C0C0可能保留舊死亡9，仍只在{0,9}。526890僅在526E16
判type77h後，526E1E讀signed 28A，再於526E25呼528A70；type0／9走
526E3D→526430而不加收到量，type9另可清死亡HP。故19個特殊kind/id組合
仍需要絕對HP更新。R14=34→77h與R14=27→59h不能套用此固定語法政策。

`basic/basic-special-policy-conclusion-v1.json`核對6018條原始指令列及mapper。
526890曾因平行追查時序重複分析一次，原件保留但不計第二份進度；最終政策
引用共同復活支線的完整CFG。分析PE原始sections不變，analyst CALL非原始caller。

## 復活的不同權責

目前diagnostic_revival_effect實際發83/action03、kind3/id8，並非action05。
它經internal13h、529020的kind3路徑、526890 type59，再由526430的dead9
條件進5267C0。該函數恢復遮罩／狀態、清1DE、更新DB8及呼529870(target,0,1)。
所選route未把收到的amount1加到HP，不能把普通傷害的刪HP86政策搬進復活。
因此真正復活的caster MP86、target HP86與88保持；只有其BASIC死亡前奏取消
重複的提前HP0。HP1／MP66仍屬CUSTOM-0017，不冒稱本輪恢復原服復活公式。

復活四函數新REA：
`ev_427f25bf1b0cf47091ac95ba6f3d16f0e173454682659c102e9cc8c54d32503e`。
2508條原始指令重核；session已close且terminal exit0。完整限定範圍、callee
及warnings見`revival/revival-native-conclusion-v1.json`，不宣稱全EXE沒有其他HP writer。

## 真正source整合與儲存契約

RecoveredBattleAttackPresentation新增`requires_absolute_hp_update`，按完整原生
分派選類，parse／原始bytes及權限保持。PK projection依該類決定是否送target
HP86；actor／max/current HP、signed-short loss、兩視角與單次MP規則仍檢查。
Application目前BASIC及kind0／1,id1的動畫回覆省HP86；無動畫路徑仍送絕對HP，
兩路均保留native DWORD檢查。Manual的BASIC／126同樣以命中改HP。

PK已實際經Application→SqliteDatabase backend→Publication→RoomState→projection
→paired outbox→Session串接。共用檢查接收一／兩組動作及final88，terminal另需
canonical89；最小格式由舊3／4筆改為2／3筆。own MP僅准source0及position0，
禁止重複source／非primary target。特殊絕對HP技能與一般延後HP可合法混合。

fresh settle在任何SQL之前嚴格檢查每動作的原生HP政策及terminal旗標。
retained入口另接受「整份舊格式的每組HP86」，不接受只對部分延後類動作插入
舊HP86的混合。read_round、terminal resources、RoomState current及Session
都明確用retained判定，私有來源、exact row／Written／身分／checkpoint比較不變。
原始saved blobs、schema、checkpoint與角色資源不改；這是讀取相容，沒有把舊
outbox重寫成新格式，也不能宣稱舊格式重新播放已有新的native驗收。
CUSTOM-0126僅更新rederive來源說明，activation／schema安裝狀態不改。

新增獨立C++回歸來源與CMake目標，涵蓋510個kind0／1 ID的類別、兩視角、MP、
native合法混合、舊格式唯讀、拒絕混合舊政策、最小終局、目標／source及尾端損壞。
既有Manual／復活前奏案例改為136／511 bytes並保留精確傷害、死亡及receipt規則。
獨立靜態review見`scope/round465-independent-static-review-v1.json`；未建置或執行測試。

新helper均先AST／語法檢查再單次執行。Application換行修復v1因偵測含兩條
舊context而在寫入前停止，v2只修14條新增行；舊原件及失敗原因保留。
唯一正式靜態盤點沿用v29分類；新增完整玩法0，全遊戲分母／完成率仍null。
PHASE1未執行build／tests／target／VM／codec／遊戲DB SQL／遷移／啟用／部署。
原始命中、暴擊、傷害／治療生成、減傷、五行／抗性及中毒tick仍各自開放；
本輪恢復的是收到量的消費與正確回覆權責，不是這些原始生成公式。
