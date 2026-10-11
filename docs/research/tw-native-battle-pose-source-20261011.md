# 台服戰鬥符號 C66→S77 來源，第262輪

本輪修改6個既有C++檔、新增1個protocol header，完整來源800,883B。CUSTOM-0103把實際Application內既有診斷戰鬥綁定的單筆C66 posture0，接到擁有者原生actor WORD的S77符號回包。功能預設關閉，屬部分、條件式診斷呈現來源；一般共用PvP房間及完整台服玩法仍未完成。

## 原生欄位與世界姿態的區別

獨立native代理靜態讀取當前釘定映像，區分原PE、當前mapped範圍及另存補充，不將不同輸入冒稱完整同一基準。戰鬥Ctrl1..0在local50B840成功後，經514E95→497E00送logical4 C66：symbol BYTE、(posture<<3)|directionLow3、opaque尾BYTE；該尾未寫，不要求0。symbol來自玩家設定BYTE，再經47FC60對220..225可能隨機替換，不是固定1..10技能或按鍵編號。原生共享DWORD時鐘的unsigned elapsed必須嚴格>500ms。

戰鬥S77為logical7。519300只讀logical1..2 native actor WORD及logical3 symbol BYTE；世界77的posture/direction/effect解讀不能套用。52DC50依side0→1、slot0..13找第一個actor+DB0完整WORD相等者，並檢查actor+1A與model+1D8的signed資格；完整顯示及opaque子呼叫仍OPEN。

S1C515D10..23保留raw3/4完整WORD至metadata低16位；variant2000在516149..15C把14DWORD metadata複製到actual actor+DB0。nonowner0400補充確認515FED未改metadata低WORD，經516016/025傳至5216C0；若constructor抵達521A3F..4A的14DWORD copy，其DB0仍為同一rawWORD。資源不足、constructor/model資格及實際顯示尚未證明；這是條件式資料流，不是所有actor已成功建立。

S86/5 raw3 mask0x01寫primary selector=raw4&0x0F，mask0x02另管secondary。mask0x01為0時跳過primary寫入，不能自行稱作撤銷。初值FF與其他寫入／opaque子路徑各自保留；本輪只保留真正bootstrap的歷史primary來源，不宣稱當前client selector或回合權限。

## 實際掛載與權威

Config新增battle.owned_pose.enabled，false預設；啟用需要既有authenticated dual-connection與diagnostic player/participants bootstrap。沒有改動現用設定。Application唯一producer仍是Timer36後組裝真vitals/S1C/S86、設Session為InBattle並呼叫diagnostic_combat->bind的既有診斷入口；本輪直接保留即將返回的完整bootstrap bytes。沒有創造BattleRoom、改monster資料、把fixture當普通PvP或製造ID／ACK。

新RecoveredBattlePose.h以封閉固定格式走完真batch，保存全部原bytes、完整28位置S1C及17-byte86/5；只認1C45B、2225B、8315B、8617B、873B、88121B，unknown／truncated／重複position／缺actor或多個86/5拒絕，不掃描payload湊來源。bind核對整個Battle roster、owner variant2000／nonzero native WORD、primary mask與位置；其他actor僅允許已資格的2000／0400條件式identity mapping，任一其他rawWORD與owner相同則拒絕，避免已知first-match碰撞。這不是實際建構後唯一性觀察。

full64-bit controller與原生WORD分開：原有bind及C66路徑核對真controller，不由position或common character縮窄生成native ID。新cosmetic狀態保留exact weak Session incarnation、完整account/character、bind battle_generation；只在真InBattle、active Battle、同owner controller且generation不變時接受單筆posture0。symbol只作完整BYTE顯示資料，不改HP／MP、RNG、技能、回合、checkpoint或任何持久狀態；directionLow3和opaque尾不作權威。

RecoveredWorldService先把單筆battle C66交給既有battle callback；未啟用policy仍拒絕。Application既有C66分支在battle結果後立即返回，先於world movement／location／visibility／pending-pose處理。原世界modes1..3與CN/web／凍結聊天IME認證字體客戶端不變。混合C66與攻擊仍在呼叫combat前整批拒絕。

回包先形成native logical7並完成既有framing／reply validation，才發布cosmetic symbol及server時鐘；logical4..6未讀bytes是明示CUSTOM零投影。server steady_clock獨立quota允許第一筆，後續<=500ms接受但無回包且不改clock；這不是原生共享DWORD時鐘的觀測或原server政策。

## 限制與記錄

初次grant是實際prepared bootstrap資料，CUSTOM cosmetic權限來自當前server active binding，並不宣稱current native grant／model eligibility。Session普通callback返回framedbytes並由原queue送出；未使用只允許world phase的send_world_records_observed，也不借NormalWorldInitialization或recovered_world_ready當battle permission。沒有private battle Written receipt、client ACK、atomic delivery、rollback、render acceptance或ordinary shared PvP資格。

first-candidate完整7檔800,427B保留。root/native補充指出其他variant identity可能轉換；refinement2增加只允許2000／0400的保守guard，完整7檔800,883B。原before6檔790,045B；新header absent-before。各epoch完整檔、hash及全diff分開保存，不刷新舊封存。

本輪新增opcode0、完成一般完整玩法0；TW全遊戲方向／階段／狀態／變體分母與百分比仍未知。僅靜態來源及獨立閱讀，未test／build／compiler／runtime／native／codec執行、遊戲DBSQL、migration或deploy。下一步仍需真正ordinary battle admission／全roster supplier／current native初始化及grant生命周期，再接共用戰鬥；本條件式診斷呈現不能替代那些工作。

封存：C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-native-battle-pose-source-262

獨立原生主封存保留23個code span（加總3,272B／union2,916B／1,041 instruction sites）與4個data table；0400補充另保留2 spans／1,005B／296 sites。這些是本輪限定靜態取讀量，含既有及重疊證據，新增全域原生覆蓋仍為0。原PE SHA256 `5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`、mapped image `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` 分別保留；選取範圍逐bytes相同不代表整個檔案同一雜湊。

S77實際background queue2由519370取出，519A04[77]選到519642，再經519646呼叫519300；本輪不增加原有110項primary battle索引，也不增加既有世界77 opcode或限定回覆登錄數。原生Ctrl預覽與實際發送各自呼叫47FBB0；220..225的隨機替換可能使預覽及發送符號不同，不能用預覽值作固定回包依據。
