# 第234輪：台服物品原生欄位與交易回覆來源

本輪將同一149c台服的完整3B物品資料編碼、既有41數量更新，接到實際共用物品／原生裝備聯合交易的回覆元件來源。新增3個C++檔、修改6個C++檔；增加1項局部來源串接，新增完整玩法路線0。台服／全遊戲完成百分比與完整路線分母仍未知。

同版原生呼叫證實 C28 傳來源格、物品鍵與旗標，目的格只參與本地條件；反向卸裝也走旗標1。來源不能由旗標猜裝備目的地或玩法權限。這輪保存6段有界指令切片776 bytes／222處指令，沒有宣稱它們是全歷史未曾涵蓋的新位元組；另保留3B／41兩段780 bytes／236處指令的完整既有同版證據。

`RecoveredTaiwanInventoryItemRecord` 必須明確供應 incoming raw count、0..49格、opaque WORD 與完整20 bytes，25-byte邏輯記錄逐欄保留，無預設opaque0。3B替換完整20 bytes，但數量依metadata分支相加或設1，不能當絕對數量；41的 signed BYTE 才決定絕對數量或清除count/key，其餘18 bytes與未知prefix不因此清空。原生伺服器順序、opaque helper副作用與完整1200-byte afterstate尚未恢復。

`SharedTaiwanOwnedInventoryReplySource` 由同一 Application Context 的實際owned reader與joint transaction組裝，準備時以同一讀取範圍核對完整共用／原生before，並核對私有實際C28 occurrence及選中full20 alias。供應者必須明確傳入已排序操作及限額；每筆3B都是該格真實before／next instance，拒絕重複3B；每筆正值41都須符合真實before／next count/key，所有修改格均須涵蓋並以絕對41收尾，未知prefix不得虛構。這是有界來源投影政策，不是恢復原服回覆順序。

封包在未來實際COMMIT之前配置／編碼。取出時只接受同一joint writer的私有提交憑據，重讀完整已提交雙資料群與當前Session、私有input、ready lease／位置；取出一次後不能重送或重建。提交後仍有實際current讀取，可能配置或拋例外，並非聲稱整個取出流程零配置。故意將Component與完整World Reply區分，不能冒稱能力重算、pending完成或DA外觀發布已接通。

凍結既有背包projection與其他功能。尚待真正的definition/acquisition、裝卸合法性與目的格選擇、Lua規則、完整next issuer、能力變化、物品到DA映射、完整有序回覆與Main供應者。保留CN／網頁／共用資料、64位元數值目標、99堆疊目標、原生字體與繁簡轉換。

本輪只做靜態原生來源追查、C++來源串接和檔案帳本；未建置、未執行遊戲／native／codec、未測試、未連資料庫／執行SQL、未遷移或部署。目標維持active，遵照台服完整串接100%後才停止的最新指示。
