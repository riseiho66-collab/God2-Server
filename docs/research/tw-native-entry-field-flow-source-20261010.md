# 第226輪：TW2A逐位來源與同版DA狀態寫入

本輪完成有界靜態資料流研究，C++新增0、修改0，來源串接段維持214，新增完整雙向玩法路線0。兩個子代理分別追原生資料流與36B來源對照；完整研究、來源原件和報告保存在本輪外部封存區。沒有建置、測試、原生／codec／遊戲／資料庫／SQL執行或部署。台服和全遊戲分母及百分比仍未知，目標保持active。

本輪訂正第223輪對B26..27的推論，保留舊報告原件。4682DB的IMUL先覆寫EDX，之後計數運算及未進入的4607D0呼叫使高位來源未資格化；4682F9只把AX搬到DX，468304也只右移DX。46830C傳給461AD0的完整EDX高位不是已證明來自B26..27。不能把未知高位改稱零，也不能推論B26..27全域無用或讓serializer任填。

完整1904B既有initializer內另見46865C的第四次B24 DWORD load；468660先將完整ECX複製到EDI，ECX經AND3F取area，EDI另經ANDFFFF再右移6取scene，兩條分支皆丟掉高WORD。未識別到B26..27直接持久scalar store；但46819C傳遞完整body目的指標，4684D6傳body+12給未知callee，alias可讀範圍未恢復。因此所有callee都不觀察高位的說法仍不成立。本輪保持461AD0、4607D0、461270及其他場景／GUI／render函式為閱讀邊界。

同一149c映像已找到2A與DA共同寫入的實際狀態：

| 2A body欄位 | initializer目的 | 同版DA payload來源 | DA寫入位置 |
|---|---|---|---|
| B32..33 WORD | R+4696 = W+1539AED2 | payload+2 WORD（logical3..4） | 503D4F／503D56 |
| B34 BYTE | R+4695 = W+1539AED1 | payload+4 BYTE（logical5） | 503D3D／503D40 |
| B35 BYTE | R+4698 = W+1539AED4 | payload+5 BYTE（logical6） | 503D46／503D49 |

DA實際dispatch表目標469369，長度表401252對應logical15。consumer先比較當前已綁定local actor，再以真正payload呼叫503D30；這是客戶端狀態選擇，不能代替服務端權威。只閱讀503D30..503D88純資料前綴。468315..468326清除R+90起的0x1141 DWORD，結束於R+4594，不覆蓋以上scalar；未據此宣稱整個後續生命週期不改寫。

36B完整對照表拆成54個mask部分，逐一區分consumer、共同來源、條件式對應及未知producer。已具共同來源的actor14bit、area6／scene10、x／y15bit仍須維持精確account／selection／position lineage，禁止截斷。B0／B4的資源與status、B8..11、B26..27、kind的權威產生規則，以及transform與兩個scalar的實際語義／合法狀態來源仍有缺口。名字、logical22角色資料及logical24資源數值各自接原有來源，不填入2A opaque欄位。

現有appearance view確實有2A→DA對應，但儲存契約釘定6bf／CUSTOM-0047及transform0，不能直接升格為149c正式producer。本輪獨立恢復149c DA寫入，沒有更換舊schema來源或修改凍結功能。下一步先追actual149c完整8個appearance components、transform WORD、兩個scalar的owned after-state issuer，再處理B0／B4資源status和其餘opaque；完整40B保存／CAS只能保留現有資料，不能產生缺失資料。

盤點維持TW C2S觀察156值；世界S2C有效252項（230固定、22變長）、戰鬥分派110項（9特殊、101預設）、83動作23項、86 selector7項。CN C2S156值、S2C階段280項。958個endpoint索引、214個來源串接段都不是完整玩法分母；完整雙向串接百分比目前不能可靠計算。背包stack99、仙幣99999999999、共用64位元數值、CN／web、原生字體及繁簡轉換保持既定範圍。

帳本工具新增完整metadata外部封存與本地精確雜湊索引，以保留原件並維持God2容量方向；所有歷史原件不變。這只改靜態來源記帳位置，不啟用服務、連線或測試。
