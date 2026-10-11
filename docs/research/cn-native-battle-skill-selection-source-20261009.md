# 第193輪：陸服實際選中技能列表接入戰鬥命令資料

本輪新增3個C++檔、修改3個C++檔，共6檔58,465B，將真正供應的主／次技能列表、選中索引、紀錄指標及完整110B技能定義，經 `CnBattleSkillSelectionSource` 接入既有 `SharedNativeBattleCommandData`／Groups／CommandSource。來源段184→185；新增opcode、phase binding與完整雙向遊戲路徑均為0。全遊戲分母與百分比仍未知；958端點行不是完成路徑數。

## 原生寫入與完整來源

CN582f完整554750..55497E寫入helper，依raw WORD bit14選主／次清單，kind取高位低6bit、ID取低BYTE，將同一bank的精確技能指標與raw WORD保留。命中已有key只更新bit15，不因此取得學習權。主清單的group+2D4來自真正初始化參數的subject row；54A6A5..54A6E4把實際H+9D223C銀行交給553BC0，保存component+3518。這些證明原始地址關係，沒有證明WORLD subject與當前戰鬥actor是同一身分。

561BB0另讀資源檔的4B header，載入記憶體的是112,656B payload，並非整份112,660B資源檔。原file offset8對應bank offset4。新只讀快照完整保留component、bank、index與flags，逐項比對實際紀錄地址、file offset、原始110B、source與hash；不把檔案header或全bank padding擅自當成技能資料。完整bank的當前來源仍由真正Current供應者限定。

清單代理保存17段2,110B：5新增完整helper922B、3新增限定區317B、9保留舊區871B；不是17個完成封包。主清單100／次清單10是本只讀view接受的已限定layout範圍，不是學習上限，也不是554750已做容量防護的證明。553F30只重設次清單count；553FA0只清主清單bit15與狀態，不能將留下的指標解釋為當前授權。

subject代理另保存新的553C7B..553DF9限定區382B，與前述區段不重疊；保留6段1,075B舊WORLD34／35與mode0關係。新區只確認16group／100WORD清bit15與狀態，以及實際552870／553220／5540B0／5545C0呼叫前沿；**缺少的subject row→已學技能列表填入本體仍未恢復**。UI／render只保留callsite。WORLD34新增flag0、WORLD35置flag3與同bank pointer均不等於服務端學習權。

## 實際程式串接

`CnBattleSkillSelection.h`要求同一真實battle owner／list／bank／selector／flags epoch及固定native catalog source。先完整複製輸入，再做Current／catalog／Current夾持；精確signed選中index決定紀錄，保留原bit14／15，沒有相同ID搜尋或自動換成別的選擇。最後細修使用已擁有scope計算expected bank address，避免callback後重讀借來的Input.address；初版、source-ready版及修改diff皆保留。

`CnBattleSkillSelectionSource.h/.cpp`保留strong catalog與私有來源身分，factory不讀借用DB。真正DataAuthority先限定catalog／reader／store lifetime，再resolve：每筆原指標、file offset、source、hash與完整110B比對共用catalog，保持原順序與選中index。Current保留原快照而不偷偷重讀或rebase；它是資料來源限定，沒有實作學習、MP或施放權。

`SharedNativeBattleCommandData.h/.cpp`增加可選、明確供應的SkillSelectionBinding。選用時，實際Read→resolve→selected→完整definition交原有權威與整組結算路徑；失敗不fallback到相同key。未選用時仍要求真正共同學習／actor／cost權威，沒有因definition存在而通過。該只讀native投影是恢復來源，**不是要求正式服務端存取玩家客戶端記憶體**。Gameplay compose核對完整供應者與同一catalog，沒有預設啟用或Main部署。

既有TW持久deity declaration/status/skills與CAS revision已讀，但屬TW／CUSTOM0039／0058／0059來源，不能當CN原生學習權。既有CUSTOM Battle／Lua與Inventory placeholder也未冒充CN native。沒有改存檔、表名、EXE、字體、轉換或凍結功能。

## 網頁來源交接

新commands v4.1與Runtime v8原件依指定SHA完整保存，契約最新前段與相關API／sourceConnections／formation／gaps已現讀；未冒稱整份歷史契約全文已讀。既有C35 Request實際consumer保留logical17／payload16、offset5完整DWORD，Data交原始Request給必要權威，沒有通用mask解析。kind2且effect !=0xFF5時，此欄位是來源5..13與目的5..13／零延伸255兩WORD；普通mask分支分開，255不新增actor。完整群組／owner／grant／成本／一次結算／native回覆供應者仍OPEN，客戶端私有token與送出後14友方回位不是服務端權限。

本輪回覆授權webpeer的source ACK單獨保存，不當雙方完整玩法已接通或已驗收。secondary0x17／0x97仍獨立待接，不泛用清bit80。

## 帳本與保留

三代理完整交付已獨立封存。清單：current7／context5／actual originals31；subject：current12／context9／actual originals38（其中native17）；selection source：current35／context4／actual originals39（native0）。selection工具原finding總數77漏計4份read-context，另有原件與更正附錄：實際完整來源副本81；保持原seal不改。

本輪before1382原件與完整prior192共2472封存成員、六CPP全文／diff、初版／細修／final context及四原始／四最終報告另存。只做檔案／來源盤點、PE／靜態反組譯與hash；没有build、tests、native/game/C++/Lua/codec/API/runtime/DB/SQL/部署，不重試155 formatter／capacity／render／glyph或52F330／52F170。

仍須接通真正552870／553220列表資料、共同學習／battle actor／context issuer／S86 grant歷史／target與formation／MP及道具／原生規則／一次結算／完整回覆／Main與其餘TW-CN-web全遊戲路徑。64位共用數值與同步台陸網頁wire／object／飄字、仙幣99999999999、qualified stack99、原level、共用表／尾綴例外與先全部串接再集中測試修復發布的完整目標保持active。
