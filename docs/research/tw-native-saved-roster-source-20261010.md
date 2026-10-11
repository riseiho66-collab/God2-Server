# 台服已存神祇資料接實際世界登入發送，第249輪

本輪修改5個既有C++檔，將完整已存神祇資料、選擇修訂與原始回包批次接到既有Application fresh-world實際呼叫者。第248輪找到的世界資料發送來源已具體保留；普通戰鬥入場、actor對應、initial issuer與完整施法仍未完成。既有CUSTOM-0039存檔／選擇政策和原生顯示來源資格保持原標籤，沒有將它升格為same149c戰鬥授權。

## 實際儲存來源與回包

SqliteCompanionRepository新增私有建構的OwnedDeityRosterReadset，綁定實際repository及實例identity，完整保存account／character、依key排序的全部30／31／34原始記錄、各列revision／provenance、optional selection及其revision、同一觀察取得的GOD模板keys。load_deity_roster在自身READ transaction取得資料，拒絕既有交易、TEMP同名遮蔽、錯誤owner、重入、變更觀察及不合格記錄；所有Statement先析構再COMMIT。空清單與沒有selection是有效狀態，懸空selection或壞資料直接失敗，不退回假空清單。

deity_roster_current先保留借用材料副本，核對repository及弱identity，再完整重讀與比較全部列、raw records、順序、count、修訂、provenance、selection的存在／不存在及模板keys。它只證明當次觀察仍相同，不是未來寫入CAS。既有load_deities、selected-skill來源、寫入與schema沒有改。

RecoveredOwnedCompanions::restore_with_source使用該完整來源經既有byte builder產生相同批次，分開的pet資料觀察後再重讀神祇來源。私有Restoration將完整神祇readset和exact batches綁在一起。原restore介面保留，兩者共用原30宣告、非選擇31／34、選擇31最後及pet回包次序；原logical boundary及A00容量分批保持。這個神祇readset沒有資格化pet修訂，也沒有宣稱跨family原子快照。

## 已接實際Application呼叫者

原fresh-world Tick admission後的companions.restore呼叫已換成restore_with_source，不是新增未使用API。game scope的來源map保存實際Session弱參照、account／character、當時phase與battle generation、const Restoration及各void提交呼叫返回次數。原其他世界初始化回包順序保持。

到原companions發送位置，先核對同map entry、實際Session incarnation、未closing、owner、phase、world-ready、battle generation，再以實際repository完整重讀，回來再核對本地條件。逐個既有batch交原send_world_records，呼叫返回才累計，全部返回才標記。這些計數只有void呼叫返回的含義，不代表queue接受、async write、客戶端消費或ACK；尚未作任何battle grant依據。disconnect第一段精確移除同Session材料，避免後續無關observer例外留下來源，也不按可重用ID刪另一Session。

這是既有Application fresh-world呼叫者的具體接線；沒有啟用新的ordinary Main/native gameplay計畫，也沒有建置、啟動或部署。後續仍需實際傳輸write資格、world roster epoch及普通battle admission將saved owner對應到真正actor／viewer／initial issuer。

## same149c新查明的原生資料footprint

靜態保留6段550B、174指令位置與39B相關資料，全域新增覆蓋0。S30的重複重置flag在body十進位17（logical含opcode索引18），不是body18；完整logical S30仍19B。

4AA040先檢查abs(signed subject BYTE)>0及unsigned source count<16，再在old count位置暫寫inactive row key／classification／name。只有key>=100的packet-name分支且flag=1，才掃描active rows找首個signed row WORD等於abs key，命中僅把該row+1F0 learned_count清0後返回。learned flags／pointers、aux count／pointers及inactive tails保留，先前暫寫的inactive row也不回滾；不能視為全清或原子無變更。正常append只增加source count；負subject另設定選擇pointer／index，所保留前綴沒有技能或aux清零。下游opaque helper未在本輪擴大推論。

真正全roster清零的純資料前綴是468120..46814A共42B，在任何GUI call前結束：root+164 count=0、root+15F selector=FF、root+160 pointer=0，REP清root+168..4028共3EC0B，即16列×3EC。它必須綁真正caller／root／reset事件，不能當作普通S30或任意預設初始化。S31純資料175B前綴依sign-extended subject BYTE匹配row WORD並寫其獨立scalar／bit欄位，沒有learned／aux寫入；後續GUI不在此資格內。本輪尚未把這些reset事件臆造接入C++。

## 本輪進度與下一個實際缺口

5改0新C++，混合TW/CN部分來源233→234；新增完整雙向玩法0、opcode0。TW C2S156、世界S2C252（230固定／22變長）、battle索引110不變；它們不是全遊戲功能分母。完整台服方向／階段／狀態／變體路徑分母與完成百分比仍未知。

下一步先把真正world reset／roster事件與已保留的saved資料接成同一來源，再接普通battle admission／actor與initial issuer；實際write、secondary key-search、grant incarnation、MP／resources／rules、once settlement、fullreply／WorldOwner／Main與其餘台服流程仍OPEN。未build／test／compiler／runtime／native／codec／遊戲DBSQL／migration／deploy，未連線官方服務。goal active，持續TW優先，保留common／CN／web、凍結功能與數值要求。

完整before／候選／終版及native／roster／review材料：
C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-saved-roster-source-249
