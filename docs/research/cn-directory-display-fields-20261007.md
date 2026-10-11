# CN mode1清單的原生欄位名稱及重用（2026-10-07）

本輪在前輪實際94/A4→必要權威來源→AE/B0的條件式來源上，補入
`CnDirectoryWire::Row::mode1_display`及`Summary::mode1_personal_display`。
真正業務資料與正式分派仍未完成，沒有新增完整路徑、opcode或來源owner chain。
前輪未命名欄位的紀錄保留；本輪新增證據獨立保存在
`artifacts/integration/packet-connections-20261006/cn-directory-display-fields-01`。

## 資源與程式的完整定位

釘定CN exe SHA256:
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
已保存的原生`message.csvZ` SHA256:
`9c027fdd114073fe9fc88776f7713c0e60575fbe1a2f15059e9bda01a9ec181e`；
原有解碼CP936 `message.csv` SHA256:
`994088ac79051df74b3569fc102ab39849594409964a674796bd67fd9d4bc054`。
本輪只讀原有解碼文件及原始資源雜湊，沒有啟動資源loader／新解碼器。

00428C80在004294CB匹配原生`ProgramMsg`，0042951D建立resource+ B2F60的
文字指標陣列，每列ID-1，B2F64維持列數。必須讀ProgramMsg段，不能因其他段
有相同ID就混用SystemMsg。此資源ProgramMsg宣告1116項，ProgramMsg9是空文字；
SystemMsg1240等資料不補進ProgramMsg，前輪該段缺1240的紀錄不改動。

0050EB00從player+65364同一文字resource取得B2F60/B2F64。主程式data
008A0100起的四個WORD依次是444、865、446、153，分別經0050F9BD..0050FA57
設定009F0868、009F086C、009F0870、009F0874。
00515F80的mode1/UIstate2F分支在005163F9、00516411、00516429、00516441
把上述文字送入欄1、2、3、4。005137B0才填每列資料。
mode bit0仍只是已追明的原生呈現模式，沒有恢復其發給帳號的業務規則或權限。

|ProgramMsg ID|實際原文|mode1列顯示資料|
|---|---|---|
|444|排名 玩家|rowbyte32索引、row0..15文字|
|865|隶属洞府            总场次|row16..31文字、WORD34+WORD36|
|446|胜-负-和|WORD34、WORD36、WORD38|
|153|积分|WORD34再次顯示|

顯示依據支持將WORD34／36／38命名為勝／負／和，亦支持第二文字是所屬洞府
的顯示字串。洞府與共用公會／同盟／城鎮的具体身份關係仍未證明；文字不是共用ID。
此命名限005137B0實際使用的mode1 selectors19／23／24，不能擴張到mode0。

## 積分不是新的獨立欄位

mode1 selector19的AE subtype08被00511620複製至player+30E84。
005131A0在0051323C、00513242、00513248取30E90、30E8C、30E88三個DWORD，
以ProgramMsg446的「胜-负-和」順序格式化。由cdecl反向push可得
AE payload4、8、12對應勝、負、和，格式是有號DWORD。

接著0051325F再次push30E88，00513265使用原生字面字串`積分 : %d`。
因此不是payload16成為獨立score。來源讀取回傳`points_label_value=wins`，
只是精確表達此呈現；payload0..3及16..23仍保持opaque。不能將此重用當成
官方計分公式、points=wins的權威規則，或自創PvP結算。
005137B0清單列同樣把WORD34用作勝場及積分標籤值，總場次則只加勝與負，
沒有納入和局。來源保留該兩個顯示行為，沒有為客戶端改欄位／字體／UI。

mode1 selectors23／24的AE總結仍未找到對應數值消費意義，不套用selector19。
原生mode0分支的007F4DF0字串是簡體「积分 : %d」，其不同來源及業務範圍
仍未一起接入。

## 初始化與容量前沿

0050EB00確實將selector19、23、24及其相鄰清單各自初始化count0、page0、
pages1、cursor0；這是客戶端初始化指令，不是授權server供應假空清單。
B0非空清單由最後row的索引更新cached high index；三者的頁數設為4、每頁25。
這些display/page常數不直接證明陣列能安全寫100列。

已定位selector19 base30E74與另一個selector1B base3166C相隔2040bytes，
按40byte索引，row51會覆蓋後者header。其餘共用opaque布局仍待確認，
本輪不把相鄰header間距當成正式容量50、不把pages4當成容量100，亦不填任意範圍。
保留前輪必要的權威qualify_delivery對實際索引容量、字串終止與欄位來源的責任。

另主檔0089FF64及0089FF70相關標題索引多為9（空ProgramMsg）；原始static data
不能自行補成「個人總排行／30天排行」等業務名稱，也不能用同區的748／749
就推斷selector23／24身份。資料寫入／UI文字切換尚未封閉，保留未明。

## 已保存的具體增量與後續

修改一個C++格式來源及catalog工具；保存loader→ProgramMsg表→標題→列／AE
字段的primary native關聯。005131A0和00515F80的函式metadata span都未包住完整
switch case，依明確CFG與跳表另存原始code/tables，不把header size當完整函式。

原生欄位用途更明確，但backend尚需實際battle結果、洞府身份、排行類別、
排序／積分／30天規則、權限和原生capacity。不能從以上顯示直接新建假排行資料。
下一步沿實際UI分類來源與其寫入繼續追查，再接共用權威與正式世界分派。

本輪新增完整路徑0、opcode0、phase association0、owner chain0。
全遊戲總數／完整總數／百分比仍unknown/null。
未建置／測試／執行／驗收／讀正式DB／部署；帳號存檔、聊天、IME、認證、
頭像、原生字體、客戶端及繁簡轉換保持。
