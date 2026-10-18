# 原始公式生成端與現用技能來源（round473）

本輪追查量值指標別名、戰鬥C9來源與真正權威技能呼叫，修正兩個過期的待查位置。
沒有找到新的原始傷害／治療／週期公式，亦沒有因此修改數值規則、啟用狀態或授予技能。
現用精簡索引見同名 JSON；後續先查索引的缺失輸入，避免重新分析已閉合的顯示／接收函數。

## 原始量值寫入與接收邊界

現用 God2.exe SHA256 為
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`；
453筆 BIN 為
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
本輪完整證據在
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/combat-source-frontier-round473/`。

量值別名審查重新核對17個既有CFG、4,204筆原始指令：

| 同一物件的路徑 | 實際操作 | 不能推論的項目 |
|---|---|---|
| 51FF4C→51FF7F | 從actor+28A起REP STOSD清56 bytes | 傷害生成、14目標或施放資格 |
| 524C52→stack10→524D72→528A70 | 指標游標讀signed WORD，逐項套用 | 原始攻防／技能係數運算 |
| 526DE5→stack24→526E1E→528A70 | 特定type77讀signed WORD後套用 | 通用治療／kind2／3公式 |
| 52C845→52C860→52B619 | 收到logical83 WORD9後不乘倍率地寫actor28A | 原服送出前如何算出該WORD |

EC4指標轉交manager+A7FBC78的已知快取也未提供新係數reader。
有限literal掃描不能排除computed base、whole-object copy、間接呼叫或其他同owner別名；
相同位移出現在另一種物件，不能接成同一技能來源。

round457已將這條客戶端上游閉合至Winsock recv：socket frame經transport解碼，
成為logical record，再進519370／51D4E0戰鬥queue。logical bytes不是加密socket bytes。
round470將logical83 WORD9之前列為下一位置，應理解為**原服送出結果前的計算**，
不是尚未找出的客戶端socket producer。不能再把重查recv算成新的公式研究。
原本的外部receipt保留不改寫，本輪新增更正與連續來源證據。

真正可推進的量值來源，必須展示同owner的屬性／技能係數／狀態／五行輸入，如何經確切
位寬、比較順序、取整與裁切，寫進28A或送出的結果；或取得原服務端producer。
只有結果封包與不完整輸入，不能唯一反推原始公式。未知WORD+46仍不能命名為命中率。

## C9的同次初始化來源與已知清除

C9支線重新核對9個選定函數、3,004筆指令。當次Main初始化把D8=U傳入5112C0，
51131A保存B+20=U；519370分派C9到51982D，519832以該U將logical+1交4E72F0。
4E72F0當次讀U+86888的目前role O，操作O+44B8的三個20-byte entry。
logical DWORD5只複製到entry+8；timeGetTime只提供本地origin，不生成週期或HP／MP量。

round461早已證明：既有definition kind/id可更新entry；mode0不釋放slot；mode3到期只清文字。
named2A的指定條件及NULL分支可清O到O+4504的整體範圍，包含全部60 bytes狀態entry。
4E7CAB／4A97EC替換U+86888則改變之後選用的O，並非清除兩個物件。
round470把這些特定caller／已知bulk clear列成未分析，現在明確更正。

這只閉合選定初始化與handler，不證明永久相同World配置、目前epoch或全部後續writer。
真正DoT仍缺同generation非顯示計時觸發、量值生成、疊加／解除與原子結算來源。
RecoveredRoleSkillStatus繼續format-only，兩個runtime開關仍為false。
中毒仍保留使用者指定的當前maxHP/10精確商餘數，未自行決定有餘數時的取整或tick。

## 真正可用的戰鬥來源與未掛載的技能來源

實際owned PK普通攻擊使用保存資源／四攻防值、明示BasicParameters、Battle::act與
Lua CUSTOM-0006；ExtendedHealth64另有CUSTOM-0090。這些不是原服攻防／暴擊公式。
Lua module cache與同一game executor讓單次resolver／多hit採同一VM；hot reload後續回合
採新VM是既有行為，本輪未將其臆定為缺陷，也未擅加戰鬥全程鎖定舊公式的政策。

現有formal自製126／150有實際掛載路徑：同一選定owned deity的目前技能readset、
完整bootstrap／87 Written、明示action／encoder與帶該readset的checkpoint／資源CAS。
另一條真正Written學習publication已接normal-init PK player／companion的來源延續，
但formal施放路徑沒有消費該publication handle，不能把兩條線說成已合併的施放授權。
已掛載的自製owner不等於一般C35 WorldOwner；PK native basic dispatcher仍拒絕skill。

src目前沒有SharedTaiwanNativeSkillCommandSource::WorldOwner的具體實作；
issued_primary_skills／with_native_skills也沒有實際supplier caller。
Application轉送optional callback不會自行補出owner。453筆完整定義與client MP threshold
不是server charge、學習／出手授權或已可施放453筆技能的證明。
Historical448／Installed453來源選擇、保存資料及現用設定未改動。

下一段實際接線先需要同一真實initializer／rebuild事件的完整16-row material，包含inactive
tails、selector、雙control／actor及必要secondary，再綁定真正輸出與Written來源。
保存的S34學習表、一次87／86/5或BattleSelfView僅有的self slot，都不能代替這整份來源。
後續WorldOwner仍須提供已學／控制／grant／原生或明示自訂規則、費用、結算與完整回覆。
普通PvE encounter也仍有真正spawn／encounter assignment缺口，不能用診斷怪物替代。

## 限制與逐輪盤點

兩份native審查重用並逐byte核對既有REA／CFG；沒有新合格函數時，不為湊數新增REA。
同名JSON保留可機讀的現用缺口、證據雜湊與後續所需資料；不把未知欄位升格成公式。
本輪只補C9來源註解與研究索引，runtime行為未改。
獨立靜態審查、唯一正式盤點、來源／容量／publication收據外存。
PHASE1未建置、測試、target／VM／codec、遊戲DB SQL、schema、遷移、啟用或部署。
新原始公式0、完整玩法新增0，全遊戲分母／完成率unknown/null，goal active。
