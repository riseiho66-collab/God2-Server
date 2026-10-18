# 台服戰鬥接收來源與技能複本續追（round456）

本輪接續追查真正的技能／戰鬥公式 producer。先前round455已核對收到量的
型別及K相鄰queue的複製範圍；本輪往queue寫入端、完整初始化及整筆技能複本
追查。新增C++效果查表讀取，沒有將它當成權威傷害或治療公式。
目前仍只開發台服，舊goal文字中的其他地區範圍已被現用AGENTS取代。

## 來源與執行界線

現用 `God2/God2.exe` SHA256：
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`。
現用453筆BIN SHA256：
`3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7`。
重型證據外存於：
`C:/Users/risei/.codex/artifact-archives/god2-server/20261019/formula-authority-followup/`。

使用既有REA6.5.0公開launcher與本機Ghidra。v13分析PE SHA256為
`3a7b33f42d7399f264f09225203be446a628328ceda70dc7b08d69eaa75d468e`，
v14為 `9cf6202d6acffc5e9cf26ccae8cbe7e8d25137c798cc6d20aee3e9ddcc04b3ee`。
兩者保留現用EXE的13個原始sections，analyst CALL各71／73個，
只用來辨識入口，不是原始caller，分析映像沒有執行。
新helper均先AST／語法檢查後單次執行，完整原始bytes／CFG／Evidence保留。
沒有建置、測試、VM／native、遊戲、網路、codec、遊戲DB SQL、遷移或部署。

上一輪 `f82d3f5` 是進展：補上兩條數值來源鏈、排除一條K複製候選並保存現用
技能書來源界線，據此本輪改追真正queue producer；沒有重跑舊正式報告或黑箱。

## 戰鬥queue的兩處原始寫入端

後續狀態（round457）：下述當時未閉合的network+758 producer已由原始pointer
與REA追到Winsock recv及傳輸解碼；詳見
[round457記錄](tw-d5-skill-selection-and-network-origin-20261019.md)。以下保留本輪原始邊界。

現用原始.text的 `0051D4E0` 直接E8 caller只有 `005195C2/005195DD`，
都位於真入口 `00519370`，該入口的原始直接caller為 `005158B1`（根函數515770）。
兩處都將 `ECX=owner+A9EA4B0` 作為queue，將未改的ESI作為source，
length則為 `00415840(first_opcode)` 的回傳值。

原始 `00519A04` byte map與 `00519908` pointer table將
1C/38/83/84/85/86/87/88導向 `005195B1` 的第一個writer，89導向
`005195CC` 的第二個writer。原始表逐byte解析；沒有手動推測opcode序號。
所選完整direct CFG為472個指令，沒有未展開的indirect jump。

輸入鏈為：

```text
515770 → 5158B1/519370
→ [battle owner+10] 作為network object
→ 519398/413420 組成logical record
→ 5193BD/413650 回傳 network object+2CC4 → ESI
→ 5195C2或5195DD/51D4E0 → battle owner+A9EA4B0 queue
→ 5140C0/51D3D0 → battle owner+A9E9CB0 → 516AE0/52C520等consumer
```

新REA確認 `00413650` 回傳原物件+2CC4；其呼叫415AF0的記錄用途由有限
靜態鏈支持，未展開所有log callee，不據此宣稱沒有外部副作用。
`00413420` 則從 `00412520` 逐byte填入+2CC4。
415840的-1／-2值有不同分支；-2路徑讀logical WORD+1作為可變長度，
並有原始長度檢查。這是組包與緩衝區管理，不是攻守能力運算。

進一步原始指令將 `00412520 → 00410AF0(dst,1)` 的讀取queue綁為
network object+758（+104子物件再+654）。這個queue的真正上游寫入端尚未閉合，
因此只稱**已組好的接收logical packet**，不宣稱全部原始socket bytes已驗證。
兩個戰鬥writer分支沒有本地合成傷害或治療量；不擴大為所有callee／aliases排除。

完整資料在 `queue-producer-source-manifest-v1.json`；三個新REA入口為
519370／413650／413420。這將先前「收到的WORD」再接回實際接收緩衝區，
仍沒有取得原始服務端的攻防、倍率、命中或五行計算。

## K區初始化與文字解析器的界線

`005109D0` 是完整建構入口，原始正常direct CFG有318個指令。
`005109EE` 將incoming ECX保存在ESI作為owner。尾端 `00510EF7..00510F04`
以ECX=43、EAX=0、EDI=owner+A9EA4F0執行REP STOSD，清除172 bytes：

```text
[owner+A9EA4F0, owner+A9EA59C)
```

該清零後沒有call，正常 `00510F20 RET10` 返回前這個區域仍為零。
本輪新REA核對整個建構入口；清零片段本身是舊證據，不能重算為新非零producer。
direct CFG沒有展開SEH handler，不能將正常返回結論推到異常路徑。

原始caller根函數 `00464910` 完整direct CFG為805個指令。
`00465104/00465109` 配置AB3B8C4 bytes，`0046514C/0046514E` 將allocation
交給5109D0，`00465164` 把結果存到外層owner+A7E05EC。
另一個escape在 `004651D4/004651D9` 將innerOwner+A924D7C存到
outerOwner+1539AD40。這是實際subobject alias線索，不是已證實的K writer。

依此新bias計算，Kcount相對subobject為C5774、rows為C5778、timestamp為C581C。
原始.text的7個精確shifted memory displacement沒有命中；outer+1539AD40
精確位移只見4651D9 store，沒有可資格化的load→callee。
這個新範圍也未找到非零writer，但computed base、small-field aliases及bulk範圍
仍未排除。`k-escaped-subobject-bias-v1.json` 保留計算、原始範圍及限制。

原先count讀取 `0051A8E7` 屬同一個519E30函數。此函數中EBP曾被重用，
到 `0051A8BD` 才從stack恢復owner，不能把整支函數的EBP一律標成owner。
限定CFG有890個指令，確認row stride32及三個既知count reads，仍未找到非零填入。

本輪也以新REA核對 `00519B40`：它是五個stack參數的文字解析器，不取incoming
ECX作this。先把來源字串複製到256-byte stack buffer，以空格分token，比對
H/T/S/N/F，再透過原始 `%d`／sscanf寫入caller提供的arg4／arg5。
數值寫入是外部out-pointer，不能由函數沒有owner literal推成不會寫K；
必須先找到原始caller並資格化輸出別名。現在仍沒有該caller或非零K寫入證據。
不從token名稱推測角色能力、治療規則或暴擊倍率。

## 更正角色指標別名與技能整筆複本

舊 `element-role-forward-targets-v1.json` 的forward候選不能全部升格為真正role
callee：`004E6BF9` 載入role到EAX後，`004E6C0D mov ax,...` 已改變低16位。
因此後面的 `004E6C16 → 00507150` 不是完整role指標轉送。
另舊helper在push role後、改ECX為owner時過早停止，漏掉真正stack參數call。
本輪以exact32 alias及保留stack推導重做，舊證據保留不改寫。

新有限pass仍有357個syntactic owner+86888 loads與50筆first-call候選；
這些不是357個獨立能力consumer或50條完整玩法。
九個有真正role第一參數的callees，所選direct CFG未見+94..B4能力欄位operand；
未展開其subcalls，所以不宣稱整個客戶端沒有能力運算。
5077C0不使用入口ECX，也不因caller恰好殘留role就稱role-this函數。
`role-qualified-forward-v1.json` 保留修正及原始指令。

整筆技能copy則有實際來源鏈：

```text
[copy object+DC] → [owner+86888] → [role+4474]
→ 489DE0 → copy object+D9D4 或 +175B8，每row110 bytes
```

原始來源指標算式為rowBase+kind*6E04+id*110-106，不能直接換成BIN file offset。
限定buffer直接／LEA讀取者為489DE0、48A010、48A190、48A2C0、48A610：
48A010移除／搬移整筆、48A190由secondary選入primary、48A2C0讀identity顯示
名稱及類別、48A610讀WORD identity組出C2S D5。
本輪再以REA核對後兩個新的選擇／發送入口48A190與48A610；
所選copied reader沒有恢復傷害、五行或抗性的數值公式。
只查首row相對範圍、indexed stride與LEA線索，不是所有copied heap alias的閉包。

新REA `0048A190` 的slot guard為0..13，index=slot+secondary page*14，另檢查
已選count小於primary欄位及secondary對應flag==1。通過後清flag、
複製27 DWORD加1 WORD共110 bytes，增加已選count，更新14項分頁再調48A2C0。
這是copy物件內的選擇操作，不能當成正式技能學習／授權。

`0048A610` 則以WORD+D456為N，不以已選count+D458當N；依序讀
primary+D9D4+i*110的WORD identity，含尚未資格化的尾端值。
在stack緩衝區前放uint16(2*N+3)，以D5及該值減1的長度交 `004132E0`，
再調489AD0。函數本身沒有N的明確容量guard，不能從stack大小發明原生技能上限。
目前只證實此producer與它的輸入／送出鏈，不由它取得技能所有權、學習費用、
傷害係數，也沒有新增D5權威服務端handler或宣稱完整transport已驗收。

## 新增C++效果查表讀取

`RecoveredBattleDeferredEffect::Record::mapped_effect_type()` 保留現用
`00571610` 的完整67-byte表，依logical BYTE+14回傳可選mapped值。
獨立逐byte複核一致，table SHA256：
`2b0daaf174caa3652e6aa6701739b42f0ef7626e37641bca4c51a10e584df274`。

此為0052C000的表值，不是完整的狀態轉移：action0D的0052C0C0分支在
0052C1D2／0052C1E4存source actor的indexed+27A／+27D後返回，
不直接寫target+232或HP。原生非法selector會走diagnostic及fallback；
本accessor回nullopt、保留raw，不模擬fallback，也不稱原生會拒絕這個packet。
parse／encode、WORD+11零變體隔離及runtime false旗標均未變。
沒有設定技能費用、持續時間、權威HP或發送，完整玩法新增0。
詳細複核見 `source-static-review-v1.json`。

## 證據與盤點

五函數建構／parser／receive batch：
`ev_e00de0f71b721beb3450ce3969ca480958998a6b6f4719f61ee877577f666b69`。
兩函數技能copy／sender batch：
`ev_208849228ec42b91c89cc14fd6ffac40fed45f230c82297435ddfd67404a7649`。
七函數的完整偽碼與所選組語外存，兩次REA session均已關閉。

命中／閃避／暴擊門檻、傷害／治療生成、DoT實例與週期、攻防減傷順序、
五行相剋矩陣／抗性仍未恢復完整原始公式。中毒當前maxHP十分之一仍是既定
使用者規則，不能把本輪接收／查表程式稱為這條規則已實作。
下一步的真實缺口是network+758上游、escaped subobject與parser out-pointer
的實際寫入來源，以及能力／copied-record的剩餘資格化callee。

唯一正式靜態報告為 `round456-tw-combat-queue-authority`，執行前reservation。
報告沿用149c...歷史封包格式索引，不能當成aaf0...的全量重新盤點。
全遊戲分母與完成率保持null，沒有新增完成玩法或部署，goal保持active。
