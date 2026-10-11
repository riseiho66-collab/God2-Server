# CN D1(25/26)與固定2105-byte F9來源（2026-10-07）

本輪新增`CnSpecialDirectoryWire.h`及`SharedSpecialDirectory.h/.cpp`，
接目前已入世界的同帳號／角色／連線／lease／07 mode0→原生3byte D1
25/26→必要共用WorldOwner→完整固定F9及25名稱對照→同CNtransport。
這是條件式來源；實際資料、發給／權限規則、原生NPC資源投影、Application
一般世界dispatcher與正式登入／世界供應仍未完成，沒有自動新增玩法資料表。

client SHA256仍為
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`。
原生完整局部consumer/renderer/loader及精確來源封存在
`cn-special-directory-owner-01`，不覆寫catalog36或歷史基準。

## 固定尺寸與真正方向

C2SD1完整3bytes：opcodeD1，selector25或26，頁碼原始byte。
0050E3B0的初次refresh會發selector,01後return，不發94；00515680在
UI36/37、group2、非快取頁條件下發selector及目前頁碼+方向的byte。
頁碼byte不是共用ID或存取許可；本輪不把clientcache條件當server規則。

00567B50的長度分派表00567CA4，opcodeF9索引249的實際分支返回2105。
因此F9完整record固定2105bytes，即使count為0或selector26使用56byte列。
S2CD1本身長度21，屬另一原生consumer，不是3byte C2SD1的同名回覆。
0048FCC0 F9 case00490227先push2、再進0049020D共同call00511290，
和AF先push1不同。前輪已閉合00511290完整785bytes，本輪資格化tag2。

F9 record偏移：opcode0、selector1、page2、count3、opaque4、rows5。
25列stride84，26列stride56；剩餘全部raw tail保留，不能縮短、清零或
自造tail。count只按完整record界限讀取：25最多有25個完整列，26最多37個。
這是此record可讀bytes界限，不是已證明官方可發25／37列的玩法規則。
例如26/count25仍有700bytes尾段，來源完全保留。

##25：名稱lookup及停止條件

00511290讀payload8（row4）的DWORD，遇0立即停止copy並把cached count改成
page*25-25+已copy列數；不是單憑WORD NPC key0停止，也不是跳過空列繼續。
所copy的84bytes由row0開始。row4低WORD作資源選擇索引，與signed
resource+124E0比較，若超出native會得到null後直接讀字串，沒有安全fallback。
來源要求每個真正copy列具唯一、真正build-qualified名稱、索引界限及16byte
內NUL；WorldOwner另負責證明實際來源／build／資料revision，不讓形狀冒充證據。

名稱來源為00428C80的NPCAppearData分支→0042EAC0：ID直接索引94-byte資源列，
列base為resource+124E2+ID*5E，名稱在其offset0。loader將名稱超過15byte時
第15byte強制NUL，最大ID寫signed WORD124E0。這是顯示／外觀資源key，
不是已證實的世界NPC instance或共用角色ID，也不含怪物攻防／技能權威資料。
實際當前CN資源列與TW共用catalog的對應仍須取得；没有拿TW名稱／數據替代。
先前保留message.csv是ProgramMsg資源，其內無此NPCAppearData section；
本輪沒有因此宣稱全部CN客戶端資源都沒有NPC名，也没有執行新的資源loader。

copy目的為間接owner+4F90+(page*25+n)*84；名稱為4D14+(page*25+n)*16。
00514060真正renderer卻從57C4+(page-1)*25*84與4EA4+(page-1)*25*16讀取。
兩者的25格偏移恰相合，page1不應改成page0。
0050EB00實際清除57C4的2FE8bytes與4EA4的920bytes，都是146列／名稱。
來源發布要求(page-1)*25+已copy列數<=146，非聲稱全原生allocation容量146；
其他頁／容量變體仍待證明。原生count<=92hex检查是列數，不能當絕對index界限。

00514060 UI36/group2 的欄位原始取值：column1顯示資源名稱及row28文字，
column2顯示row8文字與row0低byte，column3顯示row44文字。
raw文字區分別20／16／36bytes；row80..83等剩餘欄位不命名為怪物能力。
原生格式%-20s／%-16s／%-36s是最小寬度、不是讀取上限，來源另要求
這些已copy欄位在各自區域內NUL，不能把完整無NUL陣列當安全名字。
ProgramMsg883／884／885標題為星宿神玩家／位置及等級／留言；精確ID来自
008A0048，由0050EB00供應009F07E8..7F4，再00515F80 UI36送到表頭。

##26：56-byte列與獨立顯示

copy目的為間接owner+8A7C+(page*25+n)*56，renderer005142D0由
8FF4+(page-1)*25*56讀取；0050EB00清除8FF4的1FF0bytes，即146列。
沒有25的DWORD0終止規則或NPC資源名稱lookup，不能共享25的停止判斷。
row0低byte與row1／17／33字串供前三個文字區，row52 DWORD用signed%d
顯示最後欄；48..51等未指明原始bytes保留。來源要求各15byte文字區NUL，
必要WorldOwner仍資格化實際含義、發給、權限、存儲與規則。
ProgramMsg898／899／904標題為等級星宿神／被懸賞者角色1及角色2／懸賞賞金，
ID表008A0050→0050EB00 009F07F8..804→00515F80 UI37。
這只資格化顯示，不得由signed DWORD52自創共用賞金發放／扣款規則。

## 尚未完成與計數

WorldOwner resolve及qualify_delivery為必要真實供應，沒有預設資料／姓名／
成功回覆。發布前現查同lease／mode、完整F9格式、已初始化區域、字串及25
名稱證據，再由owner資格化實際revision／權限／build等，再現查lease才send。
保留實際頁碼與count，source同selector要求不是已證明官方回覆因果／echo。
27/28後續D1→B0／94、其他F9變體、共用star／bounty authority、真實CN
NPC資源／TW mapping及一般ready-world混合分派仍未完成。

新增3份C++來源、1個catalog工具修改；新增未掛載局部owner鏈1、WORLD
C2SD1／S2CF9兩項來源關聯、opcode新值0、完整雙向路徑新增0。
全遊戲總數／完成數／百分比仍unknown/null；沒有將2個顯示selector
算成2條完整玩法或怪物數值恢復。沒有建置、測試、執行、Lua、loader、
部署、正式DB讀寫或改客戶端。原生字體、繁簡轉換、存檔、IME及聊天保持。
