# 台服D5技能選取格式與戰鬥網路來源（round457）

本輪將上一輪的技能複本sender接到實際C++接收來源，同時把戰鬥logical packet
的上游閉合到Winsock recv。D5只增加獨立、預設關閉的格式能力；沒有實作
技能學習／施放／選取窗口保存或原服回覆，也不計為完整玩法。

## 身分、方法與範圍

現用EXE SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
現用453筆技能BIN SHA256：
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
外部完整證據：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/skill-selection-source-followup/`。

沿用既有REA6.5.0公開launcher及本機Ghidra，新增六函數：
4132E0、489DE0、410AF0、410AB0、410A10、410BC0。
完整Evidence：`ev_5003da1f4565fc755d8546ae7f415965841ee4015231084d02ca2b0f56d55dc5`。
v15分析映像SHA256為
`bf4c9ac9e934333a50197a05b357dd8b6d4d0d617a9ac55cc656859ef85bcef2`，
13個原始sections逐byte保持，79個analyst CALL只協助辨識入口，不是原始caller。
分析映像未執行；REA已關閉。新helper先AST／語法檢查再單次執行。
沒有建置、測試、native/VM、遊戲、網路、codec執行、遊戲DB SQL或部署。
上一輪ef72e40有來源與C++增量，分類為進展；本輪沒有重跑其報告或黑箱。

## D5的原始sender與原樣WORD

上一輪48A610以copy物件WORD+D456為N，從primary+D9D4+i*110取WORD。
本輪REA確認generic sender4132E0先寫一個opcode，再原樣複製caller的payload，
最後把queue count增加payload length+1。因此自洽、未wrap的logical格式為：

```text
D5 | LE16(2*N+3) | N * LE16(raw_identity)
```

LE16長度包含opcode。現用453個原始row的首兩bytes均為id／kind，
raw_identity=id|(kind<<8)，sender沒有再轉碼。這只是source identity，
零值、重複或未識別WORD也不能由解析器替換成某個已知技能。

48A610用的N不是D458已選count。REA489DE0先清除copy物件，
由收到資料兩個WORD算 `trunc((WORD(+0)-WORD(+2)-5)/2)` 後存D456／D458，
再把所選110-byte定義複製到primary／secondary。48A010會減D458並清尾row，
48A190會增加D458；D456保留槽數。不能把D5宣告為「只傳已選技能」。

本輪沒有取得原生N上限。4132E0的A00比較是現有queue加新record超過門檻時
先flush，不是拒絕或裁切大型單筆record。112-byte stack也不是權威技能上限。
大N仍有原始short迴圈與WORD長度wrap邊界，未宣稱這些是合法玩法輸入。
新grammar只接受完整、自洽、未wrap的logical record，不補造其他變體。

`d5-source-conclusion-v1.json` 保存sender、N來源、唯一原始caller及BIN逐row核對。
485C53→489DE0的上游dispatcher／原生S2C選取窗口仍須另行資格化，
不能由相鄰FC比較就宣布完整request/reply配對。
後續round458已以WORLD原始table及logical+1指標證實S2C FC來源，並補確認回呼；
仍未形成完整權威服務，詳見[續追記錄](tw-fc-selection-window-and-confirmation-20261019.md)。

## C++格式與預設關閉的接點

新增 `RecoveredSkillSelectionRequest.h`：

- `record_size`只讀D5／LE16前綴，要求至少3 bytes及偶數identity尾端。
- `decode`要求declared size與完整record一致，擁有所有raw bytes。
- identity按ordinal讀原始WORD，保留zero／duplicate／unknown；沒有catalog、
  所有權或canonical轉換。N由raw size導出，不混用D458。
- moved-from request的getter不會產生size下溢；encode拒絕空／無效record，
  合法record則回傳原始bytes。沒有製造缺省資料或授權功能。

真正入口是Session的recovered-world鏈，不是另一套WorldHandler封包殼：

```text
OtherBinding.native_skill_selection_requests
→ NativeRecordHandlerSource → WorldRecordSource Binding
→ NativeWorldHostPlan wrapper → Application
→ Session RecoveredCharacterHandlers
→ RecoveredWorldRecords::parse_frame → decode
→ 原始完整batch → 實際Others／Current
```

Record variant追加於尾端；decode／parse_frame參數與三個aggregate的旗標均
追加於尾端、預設false，舊positional initializer與舊variant index保持。
Application在move binding前捕獲此旗標。D5不借C35／C56／preborn旗標；
目前沒有生產來源將它設為true。

D5分支先檢查opt-in，再檢record size及remaining，最後解析單筆並推進offset。
整個bounded batch通過才回傳；不是先執行prefix再發現tail損壞。
既有frame大小限制保持，但沒有新增任意N上限。
後續D5仍屬Others，沿用實際whole-batch Current、phase／lease、排序及回覆檢查。
沒有no-op、空成功handler或自動發包。

`d5-grammar-static-review-v1.json` 與 `d5-integration-static-review-v1.json`
是兩份獨立source review，核對完整格式、邊界、旗標轉送、aggregate及visitor。
這不是成功編譯／測試或原版遊戲驗收。

## 戰鬥上游已閉合到recv

上一輪尚缺的network object+758上游，本輪取得原始pointer及import資格化：

```text
413420：Q=network object+758 → 410BC0
→ 543D56 thunk → IAT570820 / ws2_32.dll recv
→ Q+1818集齊transport frame
→ 410AB0 → 410A10 → Q+C10的logical buffer
→ 410AF0 → 412520 → network object+2CC4的logical record
→ 519370 → 51D4E0 → battle queue → 5140C0／52C520等consumer
```

410BC0分別讀兩個header bytes，再以length的低15bits接收剩餘frame；
所選接收分支有BFF長度檢查。集齊後以**同一個Q**呼叫410AB0，
後者將410A10的結果長度放Q+1810、讀取位置清到Q+1814。
410AF0從Q+C10+read_index複製可用bytes，推進read_index。

410A10依現有flag呼叫4106F0解碼，經410750校驗，header bit80選410820的RLE
或直接複製payload。這是傳輸格式處理，不能將logical bytes稱為原始encoded
wire bytes。這些callee只做靜態讀取，本輪沒有執行解碼器或建立socket。
Ghidra把410A10推為void，但410AB0使用其原始EAX；不把猜測prototype當API契約。

本次已能將所查戰鬥結果接回Winsock輸入，不能繼續稱這個socket producer未找到。
所選鏈沒有按技能、HP、攻守能力生成傷害；仍不能由此宣稱全客戶端或
原始服務端所有公式不存在。完整靜態鏈見 `network-source-manifest-v1.json`。

## 權威缺口與唯一盤點

D5仍缺真實issued選取窗口、身份／槽位／階段綁定、可選規則、原子保存、
原服回覆／拒絕、取消與重連生命週期。453筆定義、C25／C26學習或C35 issued
source不能代替這些證據；沒有把D5輸入寫入正式DB或當成技能grant。
傷害／治療生成、DoT週期、命中／暴擊、攻防減傷、五行／抗性公式仍未恢復。
中毒當前maxHP十分之一仍是使用者既定要求，這次來源沒有實作其狀態生命週期。

本輪唯一正式靜態報告為 `round457-tw-d5-and-network-source`，預先reservation後
只執行一次。D5登記為pending/default-off grammar，沒有增加已完成玩法。
source閉包加入新header及接線檔案；全遊戲分母與完成率仍為null，goal保持active。
報告沿用149c...歷史格式索引，本輪current aaf0...函數由獨立REA核對，
不是現用EXE的全量重新盤點或部署。
