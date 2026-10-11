# 第198輪：原生技能書取得路徑與進度

本輪完成三個子代理與主代理的靜態來源研究，保存實際原始檔、完整檔案雜湊、限定 PE 位元組範圍及修正前後紀錄。未修改 C++ 遊戲來源，未執行建置、遊戲、測試、Lua、封包程式或資料庫。依使用者最新指示，本輪結束後暫停目標工作；子代理已完成並停止。

## 完成度與計數

**整個遊戲完整雙向串接完成度：目前無法可靠計算，百分比為未知。** 全遊戲按階段、狀態、變體及延後分派的完整路徑分母仍未釐清，已串接的部分來源也不能當成完整路徑。64.6% 僅代表台服世界 C2S 解析 opcode 中已有審閱來源分支的比例（42/65），不代表全遊戲完成度，也不代表這42個 opcode 的所有玩法變體均完整接通。

| 項目 | 本輪結束數據 | 範圍 |
|---|---:|---|
| TW C2S 已觀察 opcode 聯集 | 156 | 151一般候選加補充分支；階段及變體未全數完成 |
| CN C2S 已觀察 opcode 聯集 | 156 | 依原生產生者盤點，不能按相同值與TW直接合併 |
| TW 世界 S2C 長度表支援值 | 252/256 | 230定長、22變長；長度表不等於串通 |
| TW 戰鬥 dispatch 索引值 | 110 | 9特殊、101預設；不是110個完整玩法 |
| CN S2C 階段紀錄 | 280 | 帳號6、世界206、戰鬥68；跨階段有重用值 |
| TW 世界 C2S 有已審閱來源分支 | 42/65，64.6% | 限定解析器分母；不能換算全遊戲 |
| TW 已審閱 S2C 回覆 opcode 下界 | 43 | 限定來源審閱，並非全部已完成回覆 |
| 端點紀錄 | 958 | 28來源群組；端點不是完整路徑 |
| 部分來源串接段落 | 188 | 本輪增加0；不是完整遊戲路徑數 |
| 未正式掛載的部分 owner 鏈 | 38 | CN35、TW3，仍是部分鏈 |
| 本輪新增完整双向遊戲路徑 | 0 | 學習授權、扣書、存檔及全回覆尚未完成 |
| 本輪新增部署／原生驗收 | 0 | 依指示，全部串接後才全面測試與驗證 |

## 實際新增研究

固定陸服原生 EXE 雜湊 `582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`；完整檔案留在專案外原址，只保留限定原生範圍，不複製整支47,541,760 B EXE。完整原始檔雜湊不表示整支程式的語義已恢復。

386本 SKB 資料的實際 parsed+11A 均為0xF1，mask0x04及0x08為clear，mask0x01為set。從背包使用的分支有367本直送C25，19本先經modal3B：6568–6575、6665–6669、6763–6765、6884–6886。保存的item/slot位於 `[owner+1C85A8]+310FC/+310FE`；真正確認事件與送包仍待追查。相同技能書從快捷欄經4B0760→4B0DE0會走C26，不能只按opcode名稱認定技能學習。

C25產生者4B0720送body4/logical5：低WORD item與BYTE slot；最後body BYTE沿用第一個DWORD參數的highBYTE，第三參數即使傳1也未被使用。精確背包caller因item先zeroextend而產生尾端0，只適用該caller；4B0DE0另一別名來源可能保留parsed item pointer的highBYTE。不能把尾端當數量或全域補零。C26送body6/logical7，targetWORD讀自owner430AC指向的原生物件，itemWORD與bag slot BYTE已定位，最後BYTE未寫入；原生target命名空間不能直接變成共用角色ID。

主代理另保存4B1CA0、4B0790和48C200限定範圍，共324 B、104個線性指令位置。C56是suppliedWORD、owner1C9010/11/12三個BYTE與未寫入尾端BYTE。48C200的-13/-12動作呼叫定位到真正operand及owner，但仍未取得學習語義或共同身份。4B0790另有item0x15C6→AD body12分支。線性反組譯不能當完整控制流程；既有51887D的21 B skeleton也不能當5188E3完整產生者。

提示鏈另保存499FB0／4AB680／4AC4F0共420 B，及57 B舊分派上下文。提示flags低7位被替換，高位沿用原有stack；4AB680不同mode走不同popup。限定同handle的4AC4F0只找到local close，不能推論全部確認流程沒有送包。0x243／0x263提示和既有81／83 choice transport都未證明學習或創角語義。停止於formatter、popup/render边界，未重進禁止範圍。

共用儲存代理保存27份來源、509個定點，追到既有TW C26→Application資格→MED02來源→Lua CUSTOM規則→物品／資源CAS→完整S41/S24→Session queue。這是已存在來源的新追蹤，其MED02/item3101資料域排除SKB，不是本輪新增接通。Application提供的技能書catalog是唯讀來源查詢的Lua值snapshot；Lua table本身可修改，不是不可偽造的權限。現有CUSTOM資源提交與revival書籍例子都不能升格為CN原生學習或扣書授權。

所有前197輪封存與本輪子代理封存保留。原生尾端欄位的初次描述及主代理語義標籤修正均另存初版、差異及理由；最終解讀使用producer的 `refinement/producer-field-relations.json` 與 `findings-source-ready-02.json`。不覆寫原證據、不中途改完成度基準。

## 暫停時剩餘工作

下次經使用者恢復後，先追modal3B保存item/slot的真正確認事件及typed sender，保持formatter/render邊界；再建立實際owned subject、learned grant、book debit/cost/current issuer、單一共用持久交易及完整原生回覆。全TW/CN/web的階段、狀態、變體、64位數值與stack99仍屬原目標。全部串接後才集中建置、全面測試、修復及發布。
