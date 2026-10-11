# 第228輪：台服裝備外觀權威與原子提交接點

本輪完成有界靜態原生／實際來源研究；C++新增0、修改0，來源串接段維持214，新增完整雙向玩法路線0。未建置、測試、執行原生／codec／遊戲／資料庫／SQL或部署。前輪的實際入場外觀基準存取保持不變；台服及全遊戲完整分母、百分比仍未知，目標active。

現有裝備→外觀→回包路徑有真正可參考的交易結構，但來源資格不能沿用：`SqliteWeaponSlotRepository::move`擁有同一BEGIN IMMEDIATE，先比對兩個完整slot及revision，更新並讀回，再呼叫PrepareExtra。舊Application在此callback內用`SqlitePlayerAppearanceRepository::save`借用SAVEPOINT保存外觀，預先編碼pair＋DA；兩slot再次讀回後才COMMIT。提交後才commit visibility與發送。這是現有實際caller，沒有執行它。

該路徑仍是6bf／CUSTOM-0046、CUSTOM-0047與兩個synthetic WPN實例；`fixture_after`不提供一般item→component映射，外觀repository限定transform0。armor路徑是另一c5d8 pin／CUSTOM-0066，只有instance及完整slot CAS，沒有外觀權威。不同EXE pin與來源不能因交易結構相似而升格成149c正式資料。一般`InventoryRepository`仍是reserved interface，`Inventory`仍placeholder；既有bag proof只限定背包格並排除部分instance類別，不是equipment after-proof。

本輪獨立核對同149c的4個既有原生範圍，共1436B／420指令位置，另保留3個宣告資料表共215B；全部是既有範圍的再資格化，不增加全域原生覆蓋。459420..459960 parser的CALL均維持邊界，不追UI／formatter／render。family1／2／25／26走同一已識別分支，numeric source26／27／28／29分別保存到metadata+11C BYTE／11D BYTE／11E WORD／120 BYTE；459933取+114 WORD，經459FC0有界RomMaps ordinal查找寫+116 WORD，+118設FFFF。459A60的低WORD key界限／pointer lookup沒有生成完整appearance component。

來源tag與metadata用途保持分開：本輪完整parser範圍的直接token callsite沒有找到WPN／TWP分支讀source1／2／30／31，未建立WPN tag到DA component的資料流；未知CALL及全client alias仍未全資格化，不能把這個有界結果當全域不存在的證明。歷史6bf differential結果保持歷史。icon／RomMaps ordinal、tooltip欄位、等級顯示與reach各有消費端，不能據名字、數字巧合或ItemType code直接推導HeroDoll外觀。原始tag表含重複WPN／EQU到default的表項，也不能任挑alias當family。NativeWeaponCatalog保存1259筆完整definition來源與396B metadata及指紋，並不持有玩家完整20B instance、裝備權限或item→外觀規則。本輪沒有查DB或聲稱catalog已載入。

完整入場witness的writer不能直接塞進舊PrepareExtra：`replace_from_issuer`要求autocommit並擁有自己的BEGIN；Issuer明確禁止SQL寫入。它資格化full root、position、完整record與revision，沒有inventory expected／revision。`SharedTaiwanWorldEntrySource`及entryOffer針對尚未入場的selection／presence，會拒已reserved角色，不是InWorld裝備提交入口。放寬該writer或套另一Current callback會丟失其現有契約。

共用`SharedActorVisibility`亦尚無149c裝備→DA更新API；舊`RecoveredVisibility::prepare_appearance`是production_disabled的CUSTOM-0027路徑，不能代替actual Binding的已出現狀態與incarnation。後續正式實作須使用真正共同inventory／equipment expected及來源revision、完整12B prior／after appearance、同庫交易owner；在Prepared／BeforeWrite／BeforeCommit核對來源及staged next，外層COMMIT後才由game owner發布。每個recipient仍須符合真正已出現Binding、generation／incarnation、Current與queue生命週期，不藉DA產生不存在的actor。

下一個實作切點因此是共同owned instance／equipment mutation owner與真正149c完整after-state來源，然後接完整witness、DA與actual visibility。不能直接重用測試武器、從icon／reach拼外觀、以舊2A基準當current，或再增加可插拔Current wrapper。缺失producer值保持OPEN；交易與資料表預設共用，僅證明不可共用的原生raw儲存才用_tw／_cn後綴。

盤點維持TW C2S觀察156值；世界S2C有效252項（230固定、22變長）；戰鬥分派110項（9特殊、101預設）、83動作23、86子型別7。CN C2S156值、S2C階段280項。214個來源段與958個endpoint不是完整玩法分母；本輪新增opcode／完整路線均0。CN／web、64位數值、stack99、仙幣99999999999、原生字體、繁簡轉換、帳號存檔及凍結功能保留。完整before、研究原件與報告外部封存，本地只有精確索引。
