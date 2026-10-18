# 台服FC技能選取窗口與D5確認鏈（round458）

本輪將D5上游的WORLD FC開窗資料、選入／移除及確認分支接起來，新增無損
FC資料視圖與D5槽數比對。這是原生格式與客戶端流程，不是技能資格、費用、
保存或完整窗口服務。D5仍預設關閉，完整玩法新增0。

## 現用來源與方法

EXE SHA256：`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
453筆BIN SHA256：`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
完整外部證據位於：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/skill-selection-window-followup/`。

使用既有REA6.5.0公開launcher與Ghidra。v16／v17分析映像SHA256分別為：
`516b4e5b8bbb0875301bce2613c29b1b9973ee35cc612b7b3d518c09e4f38404`、
`d9066a93d264200f34047c9fe4f1b96d54919fa155d1486e832952173f29929c`。
13個原始sections保持，86／89個analyst CALL不當作原始caller，映像未執行。
新helper先AST／語法檢查後單次執行，失敗／局部版本保留，修正另存新檔。
沒有建置、測試、native/VM、遊戲、網路、codec執行、遊戲DB SQL、遷移或部署。
上一輪1376798增加D5預設關閉接點並閉合socket來源，分類為進展；未重跑舊盤點。

## FC由世界狀態發出，不能借FB分支

原始WORLD根468AE0使用queue1，經413420／413650取logical buffer到EBX。
讀第一個BYTE、guard opcode<=FD後查原始254 DWORD表46B5D4；
FC的第252項精確指向468D2E。該分支INC EBX，傳logical+1及selector FC
到4858B0，後者在485C53以物件 `[(world+A7F2F6C)+232EBC]` 呼叫489DE0。

```text
world queue1 → 468AE0 → table[FC]/468D2E
→ 4858B0(FC,logical+1) → 485C53/489DE0
→ 489970／507B20條件式show，48A2C0重畫
```

相鄰的battle接收鏈51985B明確傳FB，不是FC，不能作這條路徑的證據。
4858B0還接受內部selector100等值，不能將其所有selector都當wire opcode。
`window-dispatch-fc-route-v1.json` 保存原始表、pointer與selected CFG。
468AE0的靜態CFG只選FB／FC／FD，並非全dispatcher閉合；REA另有移除unreachable
block警告，偽碼也省略部分callee實參，所選FC參數以原始push／call bytes為準。

489970需檢查selected window index及20h／08h flags；允許時關閉其他UI，
再呼叫507B20。507B20本身也有控制項有效性／狀態檢查。
所以收到FC與「一定成功顯示窗口」是不同結論。

## 原生窗口格式與數值來源

489DE0收到logical+1，前兩個WORD分別是total logical size與secondary byte count：

```text
FC | LE16(total_size) | LE16(secondary_bytes)
   | N * LE16(primary_word) | M * LE16(secondary_word)
N = (total_size - secondary_bytes - 5) / 2
M = secondary_bytes / 2
```

原始函數對收到欄位有signed／truncated16運算，本view只支援完整、自洽、
未wrap的格式。沒有從stack、GUI分頁或buffer大小發明原生N／M上限。
copy來源仍為 `[copy+DC]→[owner+86888]→[role+4474]` 的110-byte定義bank，
其記憶體位址算式不能直接當BIN file offset。

D456保留主要槽數N，D458是已選count。當輸入id byte為0，489DE0跳過
definition copy、保留已清空的110-byte row，卻不減D458。
因此raw WORD的high kind byte非0且low id為0時，raw值與cache的0/0 identity
不同。無損資料視圖保留raw，不能冒充已解析的cache或可發送的合法定義。

## 選入、移除與重複項目的實際規則

48A270以secondary copied rows的kind／id兩個bytes查找，回傳**第一個**相同ordinal。
489DE0初始化及48A010移除都使用這個first-match結果調整secondary flag。
重複項目不會全部一起標禁，也沒有全域identity去重。

48A190只在slot signed0..13、D458<D456、對應secondary ordinal flag==1時
複製整筆110 bytes、清該flag並增加D458。這些局部guard不等於完整ordinal<count
或技能所有權驗證。48A010則恢復第一匹配flag、左移後續row、清尾並減D458；
所選函數沒有固定／永久技能flag的檢查。

若在server資料視圖先排序、去重、刪零或以set取代序列，會改變這些原始行為。
本輪保留ordered raw words，不實作猜測的allowed-set／grant規則。

## 確認框回呼才發D5

489B50的原始8項表已展開：1確認、2取消、3/4 primary翻頁、5/6 secondary翻頁、
7移除、8選入。主窗口確認先要求D456==D458，成立才開type2C確認框；
不成立走原始提示65Dh。此處並不直接呼叫D5 sender。

正確entry483BD0只是建構確認框，實際事件回呼從緊接的483C80開始。
484710保存type到owner+23D5D8，回呼由原始64項表484520分派。
type2C的第44項在4845D0，值為484259。

```text
489B50 equality → 484710(type2C) → 483C80 callback
→ table[2C]/484259 → 48425F/48A610 → D5
→ 4847C0關確認框
```

所選D5分支要求第二參數低byte滿足 `(event&02h)==0`、`(event&01h)!=0`，
第一參數low WORD==0，並且保存type==2C。
`event&02h`非零或按鈕WORD==1的type2C分支只關確認框。
這是限定分支，不宣稱所有64個事件用途都閉合或所有間接callee皆不發包。
`window-choice-confirm-qualified-v2.json` 與conclusion保留table／guards／原始bytes。

## C++資料視圖與權威界線

新增 `RecoveredSkillSelectionWindow.h`：檢查FC、total size、兩個word序列的奇偶、
secondary bytes不超過body，再以owning vector保留完整raw資料。
primary／secondary getter按原始ordinal讀WORD，保留零值、重複與未知值。
encode對合法record回傳原樣，拒絕無效／moved-from record；getter不會在moved-from
狀態越界。parse只是自洽格式子集，不宣稱原生client也會拒絕相同輸入。

`matches_request_slot_count`先確認FC與D5各自完整自洽，再比較D5槽數與FC的N。
它不比較D458、不授權identity、不綁Session／窗口generation、不消費窗口、不保存或發送。
FC與D5格式沒有明列窗口ID；同N不能證明同一次issued window或防止重播。
兩份獨立靜態複核為 `window-source-static-review-v1.json` 及
`window-ui-consistency-review-v1.json`，不是成功編譯或遊戲驗收。

現用source未找到FC issuer或D5槽序保存。C25／C26的S34學習與activation事件、
C35 issued-list，以及舊preborn歷史文件不能提升為此窗口的權限。
尤其activation link的ordinal不是D5槽序。沒有新建DB表或借用退役地區的窗口owner。
真正trigger、完整資格／費用、private issued generation、原子保存、回覆／拒絕、
取消／替換／重連仍缺。原服戰鬥公式也沒有因這條UI流程而恢復。

## 證據與唯一盤點

第一批七函數REA：`ev_7737ca66511c26f95468c9e6b1407da7f3345efce97f5f8632d0af47cc144b6f`。
確認框三函數REA：`ev_6446f42922b0a8a8e381a3cf54212543089485ab3b0f525dca7aa751710c9dab`。
十函數的完整偽碼與所選組語均外存，兩次REA session已關閉。
FC登記為independent S2C format，D5仍pending/default-off，不宣稱正式request/reply玩法。
唯一正式盤點 `round458-tw-fc-selection-window` 已reservation後執行一次，但在
寫出報告前失敗：新增FC分類與不可變v27 frontier不符。失敗terminal／當時工具
原始碼外存，本輪沒有重跑，latest成功報告仍為round457。
另製v28 frontier，只增加FC independent分類，原始native rows逐筆保持，
既有206個nondefault中independent從22到23、未分類從104到103。
這是分類快照更新，不是成功的round458正式盤點或新增玩法。
既有report工具的輸入路徑改指v28，供下一輪使用；本輪只AST檢查修正後工具。
報告沿用149c...歷史格式索引，本輪current函數另由aaf0...REA核對，非全量重新盤點。
全遊戲分母與完成率仍為null，完整玩法與部署新增0，goal保持active。
