# TW273：由私有玩家與生命值來源產生完整初次 S82／S88

本輪在 TW149c、PHASE1「全部串接後才測試」範圍內，補上前一輪仍由呼叫端提供的完整 S82／S88 入場材料。新的 opt-in factory 只接受兩份私有玩家收據、兩份私有生命值收據及已核對的 Fight catalog；它內部產生兩名收件者各自的完整 9-byte S82、121-byte S88 與既有 CUSTOM-0110 初次 S86/5。原本接受完整模板的 factory、舊 Prepared 路徑與其 readset 保持原有語義。

這是 CUSTOM-0111 服務端初次入場政策及具體來源串接，不是恢復官方服務端 producer。原生消費者的位寬、欄位流向與普通初始化指標來源，和服務端選定的值，必須分開閱讀。Application 的 `pk_rooms` 尚未安裝；完整 C69／C35／技能／結果／世界返回／重連路徑未完成。沒有進行編譯、測試、native、codec、遊戲 DB／SQL 執行、啟用或部署。

## 真正的來源與身分

`OwnedTaiwanPkInitialContextSource::Observation` 私有持有 exact `OwnedTaiwanPkPlayerEntrySource::Observation` 與 `OwnedTaiwanPkVitalSource::Observation`，並要求兩者的私有 Combat 收據相等。它保留完整 82 與 88 byte arrays；`context()`／`bulk()` 只將已保留的完整位元組轉回既有 typed codec。收據不能由呼叫端的數字、布林值、hash 或字串來源標籤建構。

玩家來源繼承 TW269 的完整 root、原名、實際已存 secondary text、revision、收件者 CP950／CP936 與 lossless conversion；生命值繼承 TW271／TW268 的實際保存 HP／maxHP／MP／maxMP 及完整 SQL material。TW267 appearance 收據持有實際 Session、私有 NormalWorldInitialization、current-on-game／Written 證據、common ready lease、完整 world/inventory/equipment、目前位置與實際 Session battle generation。來源仍限制既有 native identity 與 common character 的 exact join；不截低位、不重綁別名、不創造角色或存檔。

`observe` 先比較 private Combat 身分、核對 Player Current 和 Vital Current，再構造完整封包，最後再次核對 Current。新 factory 產生兩份來源後，調用 TW272 既有初次授權 factory；回傳前要求每份 context source 的 Player／Vital 與 Prepared 中保留的 exact 私有收據相等，再重查全部來源及全部玩家的 Current。最後玩家 Current 包含完整 title／root／combat／appearance，避免把較早一次的文字核對誤當最後共同來源切面。

`uses_connection` 與 RESERVED `stored_current_in_room_transaction` 轉接兩份具體私有來源，沒有加入呼叫端 qualifier。Current 只在實際 game owner、SQL scope 外運行；closed stored 只借用實際 room transaction，不能在交易內呼叫 Session／presence／joint Current 或另開讀取交易。入場後的 ACTIVE material 仍採既有 immutable snapshot 政策，不要求角色回到先前 WORLD lease。

## S82 的完整政策

| logical 欄位 | 新來源 | 性質與限制 |
|---|---|---|
| opcode 0 | 82 | 既有 recovered wire layout |
| DWORD 1..4／contextA | 私有 TW267 captured Session `battle_generation + 1` | CUSTOM-0111；非零、完整值不大於 UINT32_MAX，超域拒絕，不 wrap／hash／截低位 |
| DWORD 5..8／contextB | `0x00001400` | CUSTOM-0111 完整政策值 |
| contextB BYTE0 | 0 | 非 observer 的選定域；不是 duration |
| contextB BYTE1 | 20 | 明示 unsigned 20-second 初次 native window 值，不是恢復官方時限 |
| contextB HIGHWORD | 0 | 明示完整序列化政策；native copy 已知，其他全域用途未封閉 |

真正實作 `Session::commit_native_pk_entry` 在兩端私有 hold 均有效且 shared room 已 activate 後，才將 Session 改為 InBattle。既有 `set_state` 在成功跨越 battle boundary 時增加 battle generation；因此新 contextA 引用的是 exact private receipt 所綁定的下一次 Session battle generation，不是任意 caller context。factory 拒絕 prebattle generation 大於或等於 UINT32_MAX，沒有為了塞入 DWORD 而縮窄。

此值只在 exact Session／account／character／private initialization／common lease 的作用域內使用。不同 Session 可以有相同 contextA；取消後尚未入場的另一次準備也可能產生相同值。它不是密碼學 nonce、全球 room ID、持久化序號或獨立 replay authority。真正權限仍需要完整 room ticket/readset、viewer、Session 與 world/battle generations、phase、own-entry submitted barrier，以及既有收據生命週期。不能僅憑回傳相同 DWORD 就准許攻擊、技能或入場。

已核對的 native 接收流將 S82 contextA 複製到 Battle context storage；ordinary C35 的限定 actions 及正常 targets 0..27 可條件式回傳它。超範圍 mask 計算可別名到 context bytes，其他分支也會改欄位，故不是所有 C35 都無條件 echo。local `timeGetTime` 是獨立 clock，不把 contextA 稱為 native timestamp。其全域 native 意義未封閉；此政策也不宣稱 contextA 是 music seed 或任何其他已恢復的音樂／場景公式。外部 peer metadata 未形成 build-matched 原始證據，沒有據此更改 wire 或給予恢復進度。S82 contextB BYTE1 原樣 unsigned 複製為 0..255；零仍為零，沒有補 20 的原生預設。這次 20 是明示政策，不能從舊 diagnostic 常數或後續 S88 reset 偷渡成 original rule。

## S88 的完整政策與十四個指標

每個收件者的 121-byte S88 都由其 own private Vital 來源產生，位置是該收件者 friendly slot0，而非共用 Battle 的 canonical side14。DWORD counter（logical1..4）選定 0，避開未初始化 sentinel FFFFFFFF；counter0 不是 battle revision、room generation、grant epoch、native ACK 或 replay 序列。服務端的兩次初始通知與後續 grant epochs 仍由既有 OwnedPkRound 獨立管理。

logical5..12 的第一組 HP／MP，完整來自 exact private271 checked DWORD current values。其餘 slot1..13 的 26 個 DWORD 值選定 0，限普通雙玩家入場的 empty friendly placeholders。maxHP／maxMP 不在此 bulk，而由 TW271 完整 ordinary86/0／86/1 帶入；不補 max1、不捏造 opponent MP、不把 shared canonical opponent 的 MP 放進 recipient own slot。保存 MP 或 maxMP 為零時保持真值；opaque GUI 對零最大值的最終顯示仍未驗收。

logical117／119／120 選定 0，屬明示 CUSTOM 序列化，不因限定路徑沒有直接讀取就稱為 global padding。logical118 選定 0，明示關閉已資格的 operational display mask bits 08／04／02／01；不是 unused byte，也不創造 learned skill 或 action permission。其 UI／資源後代與完整畫面效果沒有執行或驗收。

目前 native audit 指向普通 reset `51FC40` 的 inline arena：side2 × slot14 × type6 共 168 個實際地址，透過 pointer table 寫入；這不是要求十四份虛構 S1C，也不是為每槽另外分配 actor。成功的 normal initialization 因而提供 side0 全十四個 type0 pointers，S88 的 bulk writer 才能對十四槽執行 unchecked HP／MP store。reset 的空槽保留 invalid identity／handles，不因 zero vitals 變成十四名實際玩家。已資格 refresh child 對空槽的 signed renderer handle FFFF 返回，不呼叫後續 opaque GUI helper。

這些靜態流向有前提：實際 normal initializer、resource cleanup 與必要 allocation／opaque helpers 必須成功；服務端收據不是 native constructor 成功回報。不得用人工指標、額外 identity 或 zero 值掩飾失敗初始化。這次 complete121 producer 解決 caller 模板依賴，沒有宣稱目前 native client 已建構或呈現。

S88 full top 對 counter0 沒有已資格的 raw-zero reject；它複製初始 counter 並影響後續 cache/rearm。raw1180 亦非拒絕條件。第一次 counter cache 為 sentinel 時保留原 C70，之後部分分支重設 20；不能據此宣稱官方初次 counter 或所有 turn windows。後續回合 counter／bulk／grant producer 仍是獨立來源工作，不能重用這份初始資料作一般更新。

## Prepared 與房間整合

新 `prepare_waiting_notification_owned_initial_contexts(OwnedPlayers, OwnedVitals, catalog)` 沒有 caller View／context／bulk／grant 參數。它內部取得兩份完整 82／88，傳入 TW272 的初次控制 factory；後者沿用真正私有玩家、生命值、appearance 與四個 side-qualified Fight selections（每 selection 四個 component rows）。Prepared 增加 optional `owned_initial_contexts()`，每份 Observation 保留 complete raw82／raw88 及 exact Player／Vital 收據。這是被實際 entry 與 room readset 消費的來源，不是 unused token。

等待中的入場流仍是九個 records／305 bytes：82、兩個86/4、own1C、ownHP、ownMP、other1C、otherHP、88。S86/5 仍不在這份 waiting stream；其完整17 bytes 由 TW272 私有來源準備，等雙方初始0B通知都被接收後才進既有 grant delivery epoch。普通 relative notification bounds 仍是每 side 的 slot0，不用 S88 0 counter 推導 hit targets 或期待原生 mask 常數。

實際 root 修改的房間端已消費 private context source 與 exact Player／Vital／Combat receipts，核對 contextA 與實際 Pair prebattle generation 的 checked+1、一致的 complete82 與 command_contexts、實際兩份 stream 的 prefix82／tail88，以及 source current／connection／RESERVED closed material。完整 source／rawbytes／policy 已進 conditional readset 與 internally derived profile digest；舊 optional absent path 不新增欄位。完整 normalized diff 與所有新增 guards/readset 函式已靜態閱讀。這不將構造方法本身冒稱已完成 Application hosting。

## 不變的界線與後續接點

既有邀請只在 exact69 Accept 後才啟動兩端 held entry transport；不提早暫停邀請者或收件者而阻擋 Accept。兩端 hold 仍保留 InWorld／原 battle generation，直到 shared room 單一 durable activation 完成後才各自 commit。完整 socket write 可以更新 durable submitted，卻不是 native ACK／render。prefence 到 SQL／網路之間的外部修改及 postcommit partial I/O／recovery 還有明示限制；TCP 未收到的舊 bytes 沒有原生 epoch nonce 可自動消歧。

本輪不改原生客戶端、帳號、存檔、chat／IME／字體／轉換／CN／web；不選傷害公式、技能、target permission、EXP／HP cap；完整64位共用數值域目標繼續保留，這條 legacy DWORD projection 超域直接拒絕而不 clip。本輪新增 bounded complete initial-context source；不增加 opcode、complete gameplay route 或全遊戲百分比。67.6% 舊數字仍僅為 parser 限定覆蓋，不能作台服完成率。

## 證據與封存

本輪 own truebefore 已依 root manifest 保留 127 份完整檔案／18,703,929 bytes，包含 90 份 source。首版 source candidate 保留 new InitialContextSource 4,058 bytes 與 Projection 22,933 bytes，共26,991 bytes；完整 before/after hashes 與 unified diff 存於 agents/source。native current input 仍是 pinned TW149c，原 PE／mapped／old sealed receipts 不覆寫。本輪新增 audit／source／review／account pins 將附於獨立終端封存；獨立審查終端封存由 root 輪次報告記錄。


### 本輪 immutable native 與來源 pins

- 新 `src/game/OwnedTaiwanPkInitialContextSource.h`：4,058 bytes，SHA256 `4f6a5f392d71e1aa1502c00fe71f9d9a1af8af8e93a944434c2cd55b5a16b046`。
- `src/protocol/RecoveredPkEntryProjection.h`：22,933 bytes，SHA256 `68e1391290495beca7e36c74b49bf0782e8bef16a6d3e1e1c6ef3cc8265a5390`。
- root 修改 `src/db/SqliteOwnedPkRoomRepository.cpp`：57,680 bytes，SHA256 `81394eb04c313c5348333a6ccb9779e9e3fe8216ab82cde5ae1a2ebffc3ce1ef`。
- 三份 source 共84,671 bytes。首版兩份 worker source 完整保留；未執行 code／codec 來產生測試結果。
- TW273 native terminal `agents/native/seal.json`：SHA256 `fde96e22a26bdb773cb26b969f8cf3b0d730e4303a9701131beabeb2f64b757c`，72 members／6,695,226 bytes；findings SHA256 `9199ece5dd1165f46bdb94c75a35ea9741441bfa9159086efbe39beaacc90291`。完整72份 member 已讀取原bytes、逐份 hashmatch 並複製到 worker `native-terminal`；這是證據檔案完整性保留，不是 native 執行驗收。
- 該 native scope 保留28份完整原輸入、16個 raw spans；14個 qualified code spans 聯集3,756 bytes／1,003 instruction sites。selected originalPE／mapped bytes 相符，不宣稱整張 image 等價或全遊戲 coverage。
- 既有 TW272 reviewer S88 audit 終端 `agents/review/audit/seal.json` SHA256 `e7d4f410e7a8e050ac6afeb89a68df5bce3f9687f2c0c885130090160b41ff21`。56份 immutable member 已另保留於 worker `prior272-s88-audit`；該獨立 audit 資格完整 `511C30` 對 mask08／04／02／01 的使用，TW273 pointer audit 本身只資格 raw118 copy，兩者來源範圍不混為新 global 追蹤。

原生普通初始化的 exact 空槽 display guard 是 actor `+1D8` 的 signed WORD；`+1A` 是不同欄位，不能替代此 guard。reset `51FF01` 將 `+1D8` 設為 FFFF，`52DA02` 的 signed-negative branch 在 opaque `508F50` 前返回。原生內嵌 arena 的每槽位置與地址只能作靜態結構證據，不作服務端 pointer authority 或 live client 成功證明。
