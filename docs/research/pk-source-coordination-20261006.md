# 原生 PK 邀請來源協調器

狀態：**SOURCE_INCOMPLETE_SHARED_ROOM_REQUIRED**。這是一條繼續建設中的
來源路徑，不能列為完整 PK、成功實戰或已串通封包。所有正式設定
保持未變更，新增旗標預設 false。本輪沒有建置、測試、客戶端執行、
SQLite 安裝／寫入或正式部署。

## 原生格式与已接入來源

原始指令／雜湊依 `artifacts/research/enemy-native-fields-20261006/frontier-v3.json`。
mapped SHA256 為 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`。

- `RecoveredPk69` 解碼原生45-byte C2S69；+1/+5 DWORD、+9/+25兩個16-byte
  字串區、+41 control0..3、+42..44清零。每區必須含 NUL，以免原生
  strlen/memcpy 跨區。right-click producer 970A0 的兩個 NULL 引數
  明確限定本輪初次邀請之字串全零。
- 原生 S2C8A 的兩DWORD及字串由84620存入UI，回覆970A0會交換
  +1/+5和+9/+25兩組 context。control1接受、2拒絕、3忙碌。
  `RecoveredPk69::expected_reply` 保留這個交換。不是8B／8C。
- `RecoveredWorldRecords` 加入預設關閉的69完整批次解析分支，透過
  `Session::RecoveredCharacterHandlers::pk_invitations` 傳遞至 Session。
- `Application` 獨立解析雙方 live session/account/character、ready、
  WORLD generation、battle generation、完整位置與 revision；目標
  character 多重 session 歧義拒絕。新服務與原聊天／認證／存檔功能
  的行為分開。只在旗標啟用時進行新路徑及 Lua 規則。
- `OwnedPkInvitationService` 維護一人至多一個提議的雙方綁定，準備
  room reservation 後才通知。重登／斷線／可能移動或場景切換時失效；
  每次新操作與世界收包前淘汰過期或已變更 offer。沒有 timer UI 關閉
  封包的原生證據，不捏造它。

## CUSTOM-0086 與原生未解部分

原生 server PK 距離／权限／費用／期限與 room admission 規則未恢復。
CUSTOM-0086 限兩個 distinct、同場景、ready、未被交易／舊未結算戰鬥／
場景轉移阻擋的角色，Lua 僅再限制資格；C++ 不允許 Lua 授予身分。
提議時限60秒為自訂的伺服器 transient lease，非原生期限。位置
revision、WORLD 和 battle generation 都要相同，不因走回原座標借用舊提議。

S2C8A 的 FAC70 由 ID+1查既有場景角色的名字；兩個字串在已追到的
wrapper 是保存／回傳的 context。此來源用受信 room reservation 的
id／generation 各轉 base36（uint64最多13字元＋NUL）放入兩個16-byte
context。這是明确的自訂 replay binding，不能說是官方 nonce 欄位或
角色名稱。回覆必須精確匹配交換後的 context 與兩個live身分，不能
只匹配 ID 而接受前一輪同樣角色的遲到答覆。authority 必須保證
reservation tuple 跨重啟不重用；此協調器不能自行給它可信來源。

初次69→8A的回覆配對與8A未被wrapper讀取的最後四個bytes保持零，
同樣是明示CUSTOM配對；沒有冒稱已取得官方S2C8A封包。兩個字串區
有native讀／寫格式證據，完整語義仍未恢復。transport submit 不等於
enqueue接受或客戶端ACK；真正69答覆還要符合当前狀態。

## 接續工作的真正缺口

`RoomAuthority` 是準備／重新讀取／共同提交／取消四個必要入口的
抽象合約；**Application 的 pk_rooms 目前不存在實作**。因此即使
手動開啟新旗標，沒有room權威也不發布邀請、不切換 InBattle、不
發82、不更改HP／技能／存檔。不能以這些拒絕當功能完成。

接受分支必須由單一共用 room 實作提交成功才消耗 proposal。下一步
需要實際做到：

1. 原生1C的玩家身份／variant／兩側外觀建構，雙方相對位置及82 context。
   不能把既有0x0400 EnyName怪物fixture當另一個PK角色；也不能把
   diagnostic歷史world外觀當當前角色。
2. 雙方已持有能力／資源／技能的來源與 readset、共用 actor/turn state。
   native來源未取得的雙攻雙防／技能計算須保持明示 CUSTOM，不捏造真值。
3. 同一room的35命令／83結果／86更新與兩側映射、存檔共同CAS、斷線與
   重登、結束及回世界。不可綁兩份各自獨立的 RecoveredBattleService
   就聲稱共享權威。
4. 把真实 RoomAuthority 接入Application，確實生成來源已限定的兩套
   初始化，然後才把69分支轉入「限定功能來源已接」分類。完整PK和
   全遊戲功能仍待繼續；測試和原生驗收依使用者要求延後。

此次世界解析數55→56，69列入「功能仍缺」；已登錄來源分支41與
回覆opcode下限41保持不變。尚未把8A加進已接通回覆清單。

## 同輪新增玩家身份初始化靜態相依

`pk-identity-static-frontier.json` 保留原始 bytes/hash與反組譯，沒有
執行原生指令。115D85/115D8A用 `(variant>>13)&3`，11662C四項表為
115DF1、116149、115DF1、11608B。索引1（包括0x2000）直接去116149，
因此不会走0x0400正常怪物的 EnyName查找。

115CEA先呼叫11E6E0(side,slot,0)，此函式只檢查side<2、slot<14、
subindex<6，從 manager+38+4*(subindex+6*(slot+14*side))取指標。
它不建立／配置actor。116149直接讀這個actor+1A，然後把14 DWORD
metadata拷貝至actor+DB0。全新PK角色若尚無此指標，不能直接照
diagnostic1C2000模板發送而聲稱初始化完成。

下一個原生相依是82後的actor前置建立與身分／外觀綁定。115C90
prefix和11E6E0 lookup仅定位了這個相依，沒有把完整consumer成功、
真實player初始化或雙方PK接受當成已取得。

## 續輪：正常82 actor指標來源與兩視角投影

上一段的「actor前置來源尚待追查」已由既有交接與本輪原始靜態指令
補足指標這一層。`current-battle-initializer-20260919.md` 原紀錄保留；
本輪新證據為 `pk-player-initialization-static-contract.json` 的11個
原始span。111424呼叫11FC40，11FC8E將inline arena地址寫入manager+38
的每一指標，依2×14×6迴圈產生168項；這不是11E6E0自行配置actor。
正常82初始化因此有actor指標前置來源，但renderer handle仍是另一層。

1C2000若handle=-1會在116166之後進入錯誤分支。已存外觀必須先透過
86/4建立主元件。1144C8→1177C0的引數是logical+1，故position為
logical+2、mode為+3、完整8-byte appearance為+4..11，ordinary mode1
特殊WORD判斷在logical+13，不可少加opcode偏移。

新增來源 `RecoveredBattlePlayerAppearance` 只接受17-byte86/4、
position0..27、mode1且特殊WORD為零的分支，保留全部17 bytes。
新增 `RecoveredPkEntryProjection` 準備兩份原生視角，先82，接兩個
86/4外觀，再接各人的1C/HP、本人的MP、88與86/5。每個視角本人0、
對手14；side1 MP不會被原生寫入，因此不捏造對手MP顯示。owned88
數值必須匹配本人資源，其餘friendly槽為空；timer/context/grant全
由caller提供，不從roomID猜82欄位，也不使用觀戰lowFF模式。

身份fullWORD與world role cache的低12-bit身分必須一致、兩人不同，
variant必須是玩家index1而非0400怪物。全部原始身份／外觀／vital
bytes由受信來源提供，投影只變更已定位的position bytes，保留其餘
位元；本輪沒有實作world DA到battle外觀的猜測轉換或新增範例快照。

`RoomAuthority::prepare` 的reservation現須攜帶不可任意構造的
`RecoveredPkEntryProjection::Prepared`，且兩個character與live pair
相同。只有id／generation、沒有兩套已準備entry的reservation不能
發布邀請。Prepared只是格式及視角準備，不證明其來源取得、資源
成功載入、renderer建立或原生接受。

共用RoomAuthority、真實owned輸入取得、canonical35/83/86戰鬥、雙方
能力／技能權威、存檔CAS和結束／重登仍待接入。Application pk_rooms
仍無實作、旗標仍false。本輪未執行測試／VM／客戶端、live DB或部署。
世界解析56、限定已接來源41、回覆下限41、控制10、未接通業務5
保持不變，不把純格式／Prepared物件當成功PK。

## 續輪：單一共用戰鬥與雙方持久化後端

新增 `OwnedPkRoomState` 與 `SqliteOwnedPkRoomRepository` 的實際來源，
補足先前完全缺少的共同房間狀態／儲存層，尚未接成完整 PK 功能。
`Application::pk_rooms` 仍為空：此後端不是 `RoomAuthority` 的替代
空實作，沒有把 durable outbox 入列宣稱為 Session 入戰或 socket 接受。

儲存另用 CUSTOM-0086 version1 的四個 opt-in 表，保留原 migration
與舊單人戰鬥 reservation/checkpoint，`SqliteDatabase` 新增明確 installer
和同連線 factory。來源核對精確 feature DDL／版本及非預期 trigger；
本輪沒有呼叫 installer、開啟正式 DB 或修改設定。沒有任何初始資料
匯入、人物／怪物／技能／能力授予。

`prepare` 在同一 SQLite BEGIN IMMEDIATE 中比對兩個 account/character
的完整資源、角色原始25 bytes及revision、完整位置及revision、舊未
結算戰鬥，並鎖定兩個角色與session。AUTOINCREMENT 房間 ID 的已返回
紀錄永久保留，跨普通重啟不重用；generation=1與唯一ID一起形成
context。舊 DB 還原需要新的 namespace，不能借用先前ID；啟動恢復
尚未實作，不能據此啟用。完整 live generation／profile 原證據重讀
仍由未完成的 adapter 負責，SHA256字串只是一個 readset 綁定。

Prepared 現保留已定位 HP／MP 原始數值和等級。每個人的 entry／
canonical actor／saved resources／saved role 必須一致；沒有用假定
數值改寫原始 packet。canonical actors 固定位置0與14，controller
各自綁定角色身分；雙攻雙防必須由外部可信 profile 明確提供，後端
只依既有 Battle 邊界拒絕超寬值，未猜算能力或攜帶技能。

啟用儲存狀態會在一筆交易內，保存 ONE 共用 checkpoint 與 TWO 原始
入場 outbox。共用 state 每間房只有一個 mutable Battle；動作在副本
計算並準備雙方視角，完整雙人 readset與共同 revision CAS、checkpoint
及兩份 outbox 同筆成功後才公布記憶體狀態。不允許加演員或更換
controller／攻防／最大資源。兩份上一輪傳輸提交尚未回報時拒絕
下一次持久動作，避免未送回覆持續累積；這不是客戶端回合 ACK。

本後端的 HP／MP 變更限 battle-local checkpoint，不寫角色資源／
經驗／角色／錢包。這是階段性 CUSTOM 狀態政策，原生 PK 消耗與
獎懲未恢復，並非已完成 production sparring／balance。Finished
checkpoint 保留兩個持有鎖；沒有假89／24、斷線即清除或自动結算。
reserved abandon 只釋放本 ticket 的兩個鎖，保留ID與原readset；
清理失敗保持鎖定，不偽裝完成。outbox 的 submitted 只表示未來
exact-identity queue callback 接受，不表示送达／render／native ACK。

真正缺口：owned identity／appearance／82／88／grant與能力技能
profile 原始輸入；profile 變更的即時CAS；RoomAuthority 接到雙方
Session 入戰及精確 enqueue callback；35完整技能／輪替／回合
relative-side83／86回覆；結束、saved resource／獎懲政策、斷線與
重登恢復；其它 WORLD writer 與新 owner locks 的整合。缺任一項
都不能發布69邀請。旗標false、未測試／建置／啟用／部署；本輪
WORLD56／來源C2S41／S2C下限41／control10／gap5 全部差額0。

## 續輪：原生35選擇到共同結果的雙視角回覆

新增 `RecoveredPkRelativeView`，以原生2×14 positions交換兩個side，
同一映射用於 C2S viewer→canonical 的目標 masks 與 S2C canonical→
viewer 的施放者／目標位置。房間 canonical角色仍是0與14；每名
玩家看到自己的角色0、另一人14。此映射是 CUSTOM-0086 視角政策，
不是client欄位授權，也不是官方PK規則。

新增 `RecoveredBattleAttackPresentation`，保留完整15-byte raw83
模板，限定普通83/1與scalar attack83/3、kind0/1、非零skill ID、
非友軍单目标與已定位selector/outcome分支。只改已定位source、
兩組target masks、signed16實際HP loss與0死／28生 outcome。
group、其餘未解bytes和id/kind保持原始輸入；不以診斷零模板當
角色來源。真正loss>32767在共同儲存提交前拒絕，不截短數值或
把高傷害說成已支援。critical特別顯示／多效果／83其它action未解。

新增 `RecoveredPkActionProjection`，以同一權威 BattleActionResult
產生兩套 logical83/86/88。HP變化與雙方目前值來自同一checkpoint；
MP扣除只向施放者的本人view發86/1，另一人不收到不適用的敵方MP
寫入。bulk只更新owned slot0的目前HP/MP，其餘friendly槽必須空；
原始counter不得是FFFFFFFF且不從revision推算，group/counter需
由未完成的回合控制提供fresh原始模板。没有自动附加86/5授權或
89結果；不存在native ACK成功的宣稱。

新增 `RecoveredPkCommandSelection`，匹配既有native35 basic或完整
skill continuation序列；client actor/side flag/context必須符合
伺服器已持有的view policy。basic及owned attack skill的參數從
明確server政策來，不讀incoming id後自动授予技能。skill key包含
kind與id，kind3治療／復活不送入damaging Battle::act；kind2維持
未解。拒絕跨header序列、重複／空／不存在／已死／友方目標與混合
receipt，原生0B/action2由未完成的ordered lifecycle另接。0/150的
全side遮罩仍只限現有parser已辨識的CUSTOM技能，而不是全技能擴張。

`OwnedPkRoomState::act_native` 已加入上述完整 backend 呼叫鏈：
trusted live caller的session/account/character/WORLD generation/入戰後
battle generation必須匹配房間，incoming selection經view反向映射
才交ONE共同Battle，兩份原生投影成功後才做雙方readset／checkpoint
CAS＋durable outbox。revision是未來turn adapter的server permit，
不是C2S輸入；profile digest也必須由真正provider現讀，它本身不能
證明技能所有權。這一來源仍未安裝到Application，不是完成35路徑。

新增原始8-span靜態證據 `pk-action-view-static-contract.json`，保留
Native35 side flag由A/B controls產生、context=actor+3C、83除14與
target mask、basic／skill dispatch table、signed display／outcome
table及group比較。僅反組譯原始bytes，没有执行native或測試。
該v1先保留「敵方PLAYER skill cache前置來源OPEN」：後續研究若取得
補充，另存續證，不把舊文件說成已包含後來證據。

未接齊：真實owned profile／appearance／context與counter/group
輸入，雙方Session admission＋exact enqueue callback，真正round
permit／0B／timeout／grant，全部技能效果／terminal／存檔政策／
重登；尚未啟用、測試或部署。69和35均維持未接通，WORLD56／限定
C2S41／S2C下限41／control10／gap5 本輪仍差額0。

### 同輪新增的敵方83技能快取續證

子代理獨立 `frontier-v4-pk-skill-cache.json/.md` 保存原始11 spans
和兩階段23項switch DATA，補足上方v1的 cache 前置缺口：正常
11439C→116AE0中，action3先116CF5取同一施放actor、116DC1按收到
id/kind放入DF8；資源關聯分支合流117152，同次117183→12C520→
12C731才掃描此cache。没有side0/local-owner限制，side1 PLAYER可
用這筆**已觀測技能**。1C side1則仍在116363跳過自有50項copy。
保留原v1，沒有把較晚取得的前置證據寫進舊基準。

global definition位址使用ID stride110十進位、kind stride0x6E04。
cache只掃0..50；全51項都非matching時，原JBE允slot51寫入並alias
EC4，是原生滿邊界，不能當第52格或server持有技能容量。kind2的
额外targetlist、kind3效果與action0x17多效果沒有泛推到scalar attack。

`act_native` 的非零kind0/1技能另現讀同連線 NativeSkillCatalog
current dataset，要求對應definition確實存在且mapped-image SHA
匹配本build；共同checkpoint transaction再次比較完整definition
snapshot。catalog只提供client呈現membership，owned skill政策仍
必須來自真實server持有資料；client MP threshold不當server扣費。
不猜造缺少definition，不改catalog、client asset或凍結客戶端。
完整敵方攜帶列表、雙攻雙防／四維／五行與原公式仍UNKNOWN。

## 續輪20261006-pk-round-collection：持久通知／授權／雙人指令收集

本節更新前輪立即 `act_native` 的來源行為；保留前輪敘述與唯一輪次
證據，不把前輪實作說成已含新的持久回合。現在用 `submit_native`。

既有原生來源 `current-battle-command-gate-20260919.md` 定位86/5→
117590主控制A和119200清除A/B；0B由115A59..115AD8在本地counter／
latch條件下產生，11925E設latch，admitted88清除latch。0B不等於
已復原的官方server回合ACK。82 context_a是原生B+3C的本地時間／
context storage，不拿room ID、custom nonce或round revision填它。
原生接收格式與CUSTOM伺服器排程分開。

新增 `RecoveredBattlePlayerGrant`，完整保留17-byte86/5，限定logical3
等於1、logical4等於0（單一owned slot0 primary），不擴張bit1／高
nibble。`RecoveredPkEntryProjection::prepare_waiting`仍先作完整
raw entry一致性建構，從雙方stream移出末尾原始grant，保留各自
raw grant和82 command context給房間。不更改歷史logical建構入口。
新room admission必須用waiting entry以及明確build-qualified初始
0B masks，禁止猜測初始目標。不能先授权再被初始0B清空，令角色
失去後續輸入控制。實际Session入場仍未安裝。

新增 `OwnedPkRound`，CUSTOM-0086來源政策：InitialControl→Grants→
Collect→Ready→ResultsControl／Terminal。雙人各一份通知、送出
grant狀態、canonical intent；revision、grant_epoch、battle_revision
各自分開。允較快peer在自身grant queue callback已提交後先保存
intent；Ready仍需兩個queue callback和兩份intent。只接受兩名owned
slot0各攻擊唯一對方，參數來自明確server policy，不補技能、數值或
傷害公式。每次改動先stage copy，bounded revision和canonical JSON
資料shape在來源拒絕錯誤值，並不是執行測試。官方收集、先後順序、
逾時防禦、回合標號和終局規則尚未復原。下一輪結果控制及terminal
目前只有純value transition，尚無可用的durable resolver呼叫。

SQLite新增獨立 `owned_pk_round_feature`／`owned_pk_room_rounds`，
version1 CUSTOM-0086；明確installer、exact DDL/version/no-trigger
source guard，舊四表DDL與base migration不變。新activation同一
transaction存ONE checkpoint、兩份waiting entry outbox及初始phase。
phase CAS比完整canonical document、phase revision和shared battle
revision，并重讀雙方saved role/resources/position與member鎖。通知
只要求自身對應入場／結果outbox已提交，兩人都通知後才產生grant。
`GrantDelivery.epoch`獨立於普通outbox revision，必須使用不同callback；
這仍只是queue接受，不能當socket送達／native rendering／官方ACK。
缺完整adapter時不發布8A／82，不安裝schema或改Session狀態。

`submit_native`重讀live caller身份與generations、profile digest，
server permit使用shared battle revision加grant epoch，native actor／
side／context須與Prepared一致。由原選擇器選basic或完整kind0/1
攻擊，保存battle-local canonical action，不執行damage。技能definition
保留完整NativeSkillRecord和所有NativeSkillSource欄位、raw bytes、
索引／offset／SHA；同SQLite transaction再查catalog full snapshot。
客戶端definition membership不代表真正持有／扣費／原始傷害規則。

舊trusted `act`／`advance`在含persistent round的room會拒絕提交，
不能繞過雙方收集；下一輪須把兩份intent、明確Lua／server先後政策、
兩套native結果、最後88與phase一起原子提交。尚缺第二action死亡取消
政策、fresh group/counter/下一輪grant來源、0B replay與ordered Session
permit、action2/timeout、terminal WORLD重入／存檔及重啟恢復。
phase已持久化並不表示restart恢復adapter已完成。

來源未建置、測試、native執行、schema安裝、正式DB改動或部署。
本輪WORLD56／有限定來源分支C2S41／S2C回覆下限41／控制10／未接5，
全部既有count差額0。41/56=73.2%只表示**世界解析opcode至少一條限定
分支的來源覆蓋**，不代表opcode全用途／完整route／全遊戲完成率。
全遊戲总包種、完成route分母与百分比仍UNKNOWN；69／35仍未接通。

## 續輪20261006-pk-paired-settlement：雙方intent原子結算來源

上一輪已持久收集兩個owned intent，本輪新增結算但仍是尚未接線的
CUSTOM-0086共用PK子路徑。`OwnedPkRoomState::resolve_collected`只在
phase Ready且checkpoint revision吻合時工作。呼叫端必須給明確
server／Lua決定的順序0,1或1,0、每位施放者本輪的雙視角原始83/86/88
模板、下一次0B的原始遮罩及Battle::Rule。C2S抵達先後、raw83 group
與88 counter都不能選出手順序，也不會拿revision生成opaque bytes。
這個順序政策／首擊致命後取消另一動作是明示CUSTOM，不冒稱原始PK
先攻／同時結算／逾時規則。真正profile／policy／fresh templates provider
和Lua規則線仍未接到Application。

Battle在room local copy上按提供的順序執行。若第一擊讓戰鬥結束，
第二個已收的intent保留作審計但不執行；若仍可戰鬥，第二動作繼續。
任何傷害、MP、raw presentation或第二動作錯誤都在持久化之前中止，
不發半回合結果。`RecoveredPkActionProjection`新增明確的
`emit_cycle_bulk`控制，第一個非致命動作只發兩視角的83及實際86；
最後一個動作才附88，反映最終同一Battle的owned slot0 HP/MP。
首擊即致命時它就是最後一個動作，也附88。兩個action的raw模板
分別由呼叫端提供，group／counter的真正原始來源仍需復原。

`SqliteOwnedPkRoomRepository::settle`在**同一SQLite transaction**
重讀雙owner role/resources/position/member鎖、完整phase document與
checkpoint，要求前一輪兩份outbox均已有queue submission，重讀兩個
kind0/1 NativeSkillRecord全文以鎖定definition。對比actor topology、
controller、四攻防與max HP/MP，只容許battle-local HP/MP變化；
BattleCheckpointCodec要求有合法active／finished結果及RNG。phase
Ready→ResultsControl或Terminal由既有value transition嚴格推導，
共同checkpoint允一或兩次動作rev；然後CAS更新phase與checkpoint，
插入兩份結果outbox，再commit。任一步失敗就不發布in-memory Battle。
終局鎖保留，沒有89、世界重入、獎勵或角色存檔更新；`read_round`
可辨識finished＋Terminal供後續adapter檢查。舊`advance`對含round的
room仍拒絕，不能繞過雙方收集。

`pending_grants`目前只容許第一輪：第二輪fresh原始grant／counter、
0B的客戶端生產條件尚未有權威來源，不能重用第一輪raw bytes。這
使PK**仍未完整串連**，也不代表已能遊玩。尚缺Session ordered
receipts／replay處理、true profile、Lua出手政策、PvE、所有技能、
原生終局及重啟恢復。

本輪只是來源編輯及靜態盤點；依owner階段要求未建置、未測試、
未執行原生客戶端、未安裝schema、未碰正式資料庫也未部署。世界
C2S parser56／至少一限定source branch41（73.2%限定覆蓋）／
S2C reply下限41／control10／gap5，相對上輪計數全為0。
全遊戲封包總數與串接完成率仍UNKNOWN。
