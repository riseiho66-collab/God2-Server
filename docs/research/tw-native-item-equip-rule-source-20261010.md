# 第236輪：物品操作接入神仙裝備完整狀態來源

新增2個C++來源檔、修改6個C++來源檔，直接將同庫持有者的完整D1/D2觀察附到實際C28選中物品。這是1段部分來源串接，完整雙向玩法新增0；台服全遊戲分母與百分比未知。沒有建置、測試、native/codec/runtime/DB/SQL執行或部署。

同149c的40127C長度leaf回21；兩個實際dispatcher的D1 caller先跨過opcode，再將20 bytes交49F510寫到UI866A8。D2的49F540寫到866BC，沒有覆蓋866BA。49B5E0的guard讀D1 body18（logical19）低兩個bits，不讀普通角色sex或目的格。狀態2拒7101..7200/7401..7500，狀態1拒7201..7300/7501..7600；7000以下、8000以上及其餘情形由此client predicate返回允許。這只是客戶端發送條件，不能當服務端裝備權利。

`RecoveredTaiwanDeityEquipmentState`保留D1/D2各完整21 bytes；42-byte Pair是明確儲存容器，不是恢復的封包或回覆排序。原生切片新增擷取7段199 bytes/60指令，另保留715 bytes/208指令及3段18-byte資料表；不宣稱全歷史新覆蓋。既有30/31/34神仙列、選取列、角色性別及1200+DA15裝備cache均不能生成缺失D1/D2。

復用既有version-keyed `main.character_native_world_entries`通用raw witness儲存，不另建表、不修改schema、不把它的名稱解釋成世界入場權限。新kind為`tw149c-deity-d1d2-ownerlocal-v1`，必須由真正來源供應全部42 bytes及獨立provenance/revision。原有CAS寫法仍須真issuer；它不自動證明中途裝卸、battle條件或原服公式。本輪沒有生成或匯入任何D1/D2資料。

`observe_native_deity_equipment`直接使用共用custody repository的私有實際連線，自有READ scope核對完整raw、來源、版本、owner/common root/position與未結battle；拒絕借用交易、寫入期間重入、六個相關common/witness表的TEMP大小寫影子或缺main表借ATTACH。缺資料或舊root/position返回缺失，壞形狀報錯，不猜補未知bytes。私有建構`NativeDeityEquipmentObservation`保存完整觀察。

新的顯式definitions+deity模式把資料交給既有實際C28 Action；Current重讀完整觀察與custody，回覆factory須選同模式。各來源觀察使用各自讀取範圍，沒有聲稱custody/definition/D1跨讀取構成同一原子交易。真正Action的next issuer仍須在實際寫入交易核對所有必要來源。舊普通／definition模式維持原樣，沒有自行選Main或將client guard當授權。

尚未完成：當前D1/D2原件的真正產生／持久化issuer、選中神仙列lineage與狀態變更、裝卸合法性／目的格／Lua規則、完整next issuer、能力結算、item→DA、pending與有序完整回覆、Main及其餘台服路線。保留CN/網頁、共用表、64位數值、仙幣99999999999、堆疊99、原生字體／繁簡轉換、帳號存檔與凍結功能。
