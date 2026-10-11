# 台服主技能初始化與清除來源，第247輪

本輪修改3個既有C++檔，將已釘定的原生主銀行初始化資料前綴、主／次enable-clear葉接入具體model及同一registry。新增的是initial material→private Ticket→既有有序S87寫出／C35資格的來源能力；普通battle admission／完整client初始化及真正發送者尚未安裝。沒有把資料前綴當作整個初始化完成，也沒有新增封包、Gameplay CUSTOM或空authority callback。

## 主銀行初始化資料前綴

same149c51BB80..51BC2A從actual第7arg S取得角色列來源，S=Battle14+90，Battle14由511323的descriptor+10寫入。該prefix實際將16個完整0x2D0 primary銀行清0，銀行rowlink+2C4設為S+D8+i*3EC，page_count+2CC設1，再將raw_page_index+2C8設為0%1=0。source S+CF／S+D4的實際BYTE分別成為signed current selector及bank_count；signed selector不由count推算。prefix還有selector+2E14 WORD、+2E28及catalog+3518寫入，完整原始footprint保留，這些額外handle／UI資料不在此技能model。

新增InitializationPrefix材料明列16個linked row的WORD key、獨立row+5C count／+60有序nullable完整定義；包括未落在count內的linked row。這些是另外取得的真same-roster觀察，不冒稱prefix已解參照。S34的row+1F0／+258已學資料仍獨立，不能借來填aux或main。control A/B、actor51/52、last86、catalog與optional完整secondary由實際owner提供，prefix沒有寫入它們；缺失不補0、不由selected deity推actor。

具體from_initialization_prefix建立原native實際清0的main count／100WORD／100aux／state，page_count1與raw_page_index0，再連上actual row觀察。這些零是原REP寫入，沒有宣稱角色未學技能；非空戰鬥技能仍來自獨立S87。新增raw_page_index保存完整DWORD，後續87／38／clear不改它，完整Ticket snapshot equality也包括它。

install_from_initialization_prefix直接沿既有install_from_issued實際game owner／真Session／common ready lease／位置／battle_generation／完整catalog／容量及private installation流程。沒有合成before Ticket或入場事件receipt。普通issuer仍須先資格化真正initial event、全部roster/control/secondary資料及後續local初始化結果；此API本身不能證client已跑完整constructor、已收包或獲得回合權限。

## 兩個不同的完整資料葉

主clear51C4B0..51C4EB（59B、含RET）對全部16銀行的100WORD AND7FFF，全部100auxBYTE清0，stateBYTE+2C0清0；保留count、全部定義pointer／rowlink、page_count／raw_page_index、selector及controls等其他資料。即使inactive尾資料也依精確footprint處理，不僅清active count。

次clear51C4F0..51C516（38B、含RET）只對3銀行各10WORD AND7FFF；保留secondary aux、nullable pointer、count、opaque與selector。它不是主銀行initializer，也不同於51BD70的secondary full-bank reset prefix。先前246 next-frontier的11C4F0初始化建議保留原件，本輪以精確原文訂正其用途，不重寫歷史。

model clear_enable明確區分兩葉；缺實際secondary snapshot時不憑空創建它。registry apply_enable_clear_from_issued持有真Session並沿exact previous private Ticket／pending屏障／完整來源重讀的同一replacement CAS。此處只是actual issuer觀察到的local資料事件，不是wire opcode；不能因收到C35就猜client執行了哪個clear，沒有送虛構reset／ACK，也沒有以清enable代替durable grant消耗。

## 入場身分交會

本輪同時釐清：S88是14個friendly位置的HP／MP，83／84只更新既有actor；它們不提供saved deity身分。實際construction input是45-byte S1C，須保留position、level、identity WORD、variant WORD、ordinal WORD及全部opaque bytes。variant2000取既有world-role cache，6000屬NPCAppearData selector，0000／4000屬EnyName資料路徑；不可通用地令identity WORD等於deity key。

existing CUSTOM0086的own0／opponent14及role identity映射仍只是其PK policy。一般神仙actor需要actual spawned roster event保留真battle incarnation、viewer common lease、完整S1C、canonical owner及完整saved row／revision／provenance，再與86/5控制位置交會。現有source尚無這個真正producer，本輪沒有把PK或codec泛化成神仙權威。

## 進度與下一步

3改0新C++，混合TW/CN部分來源231→232；新增完整雙向玩法0、opcode0。TW C2S156、world S2C252（230固定／22變長）、battle索引110不變，完整台服方向／階段／狀態／變體分母和百分比仍未知。原生保留5段339B、96指令位置，全域新增覆蓋0；既有bytes與本輪原件各自保留。

下一個最短接點是完整actual battle-entry actor→saved deity／roster event及真initial issuer。尚缺的row+5C／+60實際供應、native secondary key-search／全重複變體、grant incarnation、MP cost／refund／rules、once durable settlement、完整reply、concrete WorldOwner、Main與其餘台服玩法繼續追查；不以本模型代替它們。

未build／test／compiler／runtime／native／codec／遊戲DBSQL／migration／deploy，沒有連線官方服務。目標實際active，繼續台服優先，保留common/CN/web、凍結功能及數值要求。

完整before／候選／終版與獨立native／actor／review封存：
C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-skill-initial-source-247

