第238輪繼續台服背包 C24 實際處理：新增明確 opt-in 的完整3B物品材料模式，直接從既有同庫完整 owned aliases 讀取，不增加外部 Action／issuer callback 占位。新增 TaiwanOwnedBagItemMaterial 比對同一物件兩個精確 profile、完整20／25 bytes、key、slot、revision 與相同來源宣告；缺少真25-byte材料就拒絕，不從1215 cache或舊helper的0,0猜未知WORD。

CUSTOM-0094 明示保留每件真full25內原有incoming count與opaque WORD，只投影已知slot欄位。這是自訂的材料保留政策，並非已恢復原版服務端搬移規則或原生helper相容性。內建 whole-instance plan 同步兩個alias及物件revision、完整共同庫／native witness的CAS；預編碼先清兩格數量、逐件發其完整3B、最後以兩筆41設定真正數量／key。所有20-byte物品資料保留，prefix1..3、其他格與DA15不變。incoming count不當作canonical quantity；原生3B中途clamp與helper副作用仍待全串接後驗收。

既有 CUSTOM-0093 create／with_owned_bag_moves 預設仍只用單alias及兩格tail18相同的41子集。新增 create_with_item_material／with_owned_bag_move_material 才選0094；沒有缺料回落舊模式。新增profile為tw149c-item3b25-material，仍用同一通用持有物品alias表，不拆台陸玩法表，不匯入或執行資料庫。變更slot後材料須稱derived來源；sourceSHA是原始宣告，不是改後raw的雜湊。來源標記只首次附加，不累積操作字串。

同版3B完整receiver保留498 bytes／151個指令位置；另純lookup30 bytes／8位置，合計528 bytes／159位置，新增全域原生覆蓋0。logical3..4未被本函式直接讀取，但完整payload指標EBX跨opaque CALL，因此不能宣稱全域unused／padding或任意補零。沒有找到真正原服務端producer；新模式仍要求真正full25來源與未來完整原生相容性資格。

本輪新增1個、修改4個C++來源檔，增加1段條件式來源能力，整個C24完成數仍0。真正acquisition／full25材料發行者、Main、移動到1215 witness同步、一般完整裝卸與所有台服路線仍待接齊。TW觀測C2S156／世界S2C252（230固定、22可變）不變；完整路線分母與台服整體百分比未知。

本輪未建置、測試、原生或服務端執行、codec、DB／SQL、遷移或部署；未變更陸服、網頁、凍結功能、原生字體與文字轉換。既有0093註冊與第237輪封存完整保留，0094另行註冊；不得把這個有明示缺口的模式計成100%。
