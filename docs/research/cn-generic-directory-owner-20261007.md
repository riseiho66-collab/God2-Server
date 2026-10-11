# CN一般排行榜94／AF條件式共用owner（2026-10-07）

新增`CnGenericDirectoryWire.h`與`SharedGenericDirectory.h/.cpp`，接上已認證
同連線／同帳號／共用角色lease／目前world offer的mode0→限定94→必要共用
WorldOwner→完整AF→相同CNtransport。正式common backend、排序／身份／權限
及發給規則仍未完成，Application正式世界dispatcher未掛載此owner。
本輪是可追查的來源增量，不是已可玩的排行榜或完整遊戲路徑。

原生exe SHA256為
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
新證據`cn-generic-directory-owner-01`保存本輪來源、前輪catalog35、未改共用
身份／presence／傳輸來源，以及primary CFG。前輪來源与基準不覆寫。

## 正確的producer／consumer分別

前輪0050E3B0原生94請求為9bytes：selector在record1、三個未寫padding在
record2..4，DWORD游標在record5。其一般來源為player+22D0C+selector*3F0。

一般排行榜S2C是AF：0048FCC0 caseAF實際0049020B先push1，0049021D呼叫
00511290，this為main+89B26C，record+1為payload，額外owner參數取main+A69F20。
F9在00490227先push2再跳共同call，但00511290進另一種分支，不能用AF格式
解析F9。完整本地函式00511290..005115A1是785bytes，包含tag1／tag2分支；
本輪只資格化tag1的AF資料契約，未將F9玩法算完成。

S2C94→00524E10只從payload0找既有21byte狀態列、用payload1寫該列+4，
並重建50列指標及刷新；與上述C2S94／AF排行不同。本輪保存其204byte完整
本地CFG及原世界case原文，沒有建立94→94的虛構回覆。

## AF完整邏輯record格式

|欄位|record偏移|格式|
|---|---:|---|
|opcode|0|AF|
|BlockSize總record bytes|1|WORD little endian|
|selector|3|byte，consumer允許0..2D|
|count|4|byte|
|cursor／原始header DWORD|5|DWORD，保留原值|
|rows|9|一般20bytes／selector14為24bytes|

一般總長=9+count*20，14總長=9+count*24。005114FE／00511550各自對應
原生尺寸assert；assert後仍繼續copy，不能把原生assert誤說成安全拒絕器。
來源reader以完整record bytes界限讀取；這是來源邊界，不是原生已具相同檢查。

一般00511575複製BlockSize-1 bytes到player+22D08+selector*3F0，包含8byte
payload header及20byte rows。第一個16bytes是原始字串區，DWORD16為原始
數值bits；不能跨selector自動命名為等級、名聲、積分或金錢。
21種現有一般來源的94游標位置正好為該AF目的header+4。

14在00511516將BlockSize-1複製到player+301C4，另外把count寫301B8，
再00512C50→00513C40呈現。每列前16bytes文字、DWORD16數值、WORD20以
%4d顯示，22..23仍opaque。空文字會從009F097C原生資源指標複製fallback字串；
供應器必須資格化真實字串終止及fallback目的容量，不能把零字串當安全占位。
14的AF header DWORD在301C8，但C2S94仍讀generic27BCC；未證明這兩者alias，
來源不得強制cursor echo／相等，也不能自動將回覆DWORD写到請求cache。

## 已接來源範圍與容量限制

mode0、此mapper有明確條件、producer只發94／不帶D1、且無已知specialized
B0布局的22種selector：
`00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0E 0F 10 13 14 1E 1F 20 29`。
selector00明確保留。這是限定來源覆蓋，不是其他selector或mode1不存在／非法。
22個selector只增加一條局部source owner chain，不計22條完整玩法。

0050EB00在0050EDF3從player+22CF0清除B538 bytes：24byte摘要後正好46個
3F0-byte generic cache slots（8byte header+50*20byte rows）。來源一般AF回覆
限制完整copy落在該已初始化slot，即count<=50。這是已恢復初始化範圍的
來源限制，不是宣稱全原生協定容量50。14沒有同樣的slot初始化證據，
`fits_initialized_generic_slot()`對14回null；真正WorldOwner的mandatory
qualify_delivery須依實際native目的範圍／字串／field供應證據處理14。

SharedGenericDirectory從當前07／world offer取得mode，確認同lease仍ready，
格式預讀整個同類94 run後逐請求交必要owner。每份publication須有真實
nonzero source_revision與完整AF；發送前檢查所有大小、selector與一般slot，
再由owner資格化當前snapshot／權限／原生目的容量等，再現讀current lease。
保留實際回覆順序和游標，不製造空回覆或預設權威資料。
同selector回覆是此條件式來源的範圍要求，並非證明官方所有issuance／push
因果與順序。不同selector推播、AE摘要、B1觸發重新請求、D1／F9、其他
caller及一般清單翻頁仍需要接續；不用S2C長度表分割C2S。

## 本輪記帳

新增3份C++來源，修改1份catalog工具。新增1條未掛載局部owner鏈、
2項phase／方向／opcode來源關聯（WORLD C2S94、S2CAF）；opcode新值0。
兩者已有native索引；新增AF來源關聯不是發現新的封包。
新完整雙向路徑0，全遊戲總數／完成數／百分比仍unknown/null。
本輪只有靜態primary/source恢復與來源記帳，沒有建置、測試、執行、Lua、
asset loader、部署、正式DB讀寫、修改客戶端／原生字體／繁簡轉換。
