# 第200輪：陸服技能書來源接入共用資料庫及原生操作條件

本輪新增4份C++來源、修改2份，完成釘定陸服386筆SKB原始紀錄到同一SQLite連線的明確匯入、來源表及讀取器串接。部分來源段189→190；新增完整雙向遊戲路徑0。整個遊戲的路徑分母及完成百分比仍未知；不把這次來源匯入程式當作技能學習完成。

PHASE1只做靜態來源工作。未建置、執行客戶端／服務端／codec／SQL、存取遊戲資料庫、遷移、測試或部署。所有帳號、存檔、聊天、IME、認證、頭像、原生EXE、字體、文字轉換、等級及既有TW解析表保持。共用64位元數值、仙幣99999999999、合格可堆疊物品99與TW/CN/web全遊戲要求仍有效。

## 本輪實際來源串接

新增 `src/db/NativeSkillBookSourceCatalog.h/.cpp`：共用 `native_skill_book_source_records` 以 `(dataset_id,source_record_index)` 為主鍵、`(dataset_id,item_id)` 唯一，連到既有 `native_data_sources`。按精確來源與物品／索引讀回全部9項來源資訊、來源行號、偏移、原始雜湊及owned原始bytes。實際來源row_count限制索引，沒有固定381或假造396解析欄位；資料型別、雜湊字串、孤兒及重複結果不符則拒絕。讀取器核對字串格式，不聲稱重新計算雜湊或證明全表資格；完整比對由實際匯入者負責。

新增 `src/cn/assets/CnNativeSkillBookSourceImport.h/.cpp`：只接受 `CnNativeSkillBookBindings` 當前釘定來源，不接受JSON／fixture／同號台服資料。先取6501..6900範圍中的386筆實際紀錄，依source index0..385重組；要求共同actual_revision／client SHA、來源行9442..9827、完整CRLF與連續decoded offset739107..806862。此來源工廠已釘定795868B encoded及3042675B decoded完整雜湊，來源行雜湊包含CRLF。來源dataset為 `cn-native-skill-books-582f-v1`；SKB parser VA42CFB0/RVA2cfb0、selector lookup VA4D2BB0/RVAd2bb0沿用已保留的完整定點來源，不是本轮重新執行原生parser。

匯入程式先完整materialize所有原始紀錄再進入自有transaction，要求既有來源schema5、foreign keys與完整相同的新增DDL。禁止借用外層transaction、部分／孤兒／衝突資料覆寫；對已有來源只允許全部386筆、來源metadata、item與index雙讀回精確一致的冪等結果。查詢及寫入明確限定main schema，避免TEMP同名表遮蔽。新DDL只移除尾部空白／分號後精確比較，不悄悄放寬不相容schema。這些是本輪寫好的來源邏輯，未執行SQL或匯入。

`SqliteDatabase.h/.cpp` 新增同一impl connection上的明確schema installation／CN import及lazy borrowed reader API。constructor、default migration、Main及登入不觸發schema或匯入。外部呼叫者必須維持資料庫與game owner lifetime；原生資源的current不會自動證明共同角色、DB epoch、背包權利或已學技能。來源表不改角色、背包、學習權利，也不反推alias成共同skill grant。

保留原TW `native_skill_books`：其索引0..380、381筆來源及必需396B parsed image，無法直接容納CN386筆未完整恢復的原生parsed image。TW既有匯入器剝除CRLF後雜湊，CN原始行包含CRLF；各自保留精確bytes。新增的是可供各dataset共用的來源證據表，沒有因線路差異拆成兩套玩法或資料庫。

## 子代理新增的實際原生關係

ready1F代理保存9段817B code／243 instruction sites與32B data，其中新完整4960A0 leaf40B、新5176B0 prefix136B、展開既有5182D0 caller141B；另6段500B是保留上下文，不重算全新來源。4960A0實讀signed WORD handle及UI window flags20，不是角色／技能current或學習權限。5176B0實寫owner430A8並以451460 UI建立返回AX寫profilehandle1C84C6；451460與後續render/UI interiors均停止不進入。

4AF370的mode0及mode!=0都會供actualcomponent+90給5176B0，因此两種mode都可能重綁430A8。歷史「mode1未呼叫4D2D30」仍保留，但不能擴大成「mode1沒有重綁430A8」。5182D0的profilewindow flags10分支可強制 `4B1B40(1F,1)`，繞過非強制flags20 gate。模態確認、物品使用、頁面開啟等入口均可送相同 `1F 00`；wire本身沒有item、subject、UIhandle或來源epoch，不能反推發送者，也不能直接回bootstrap或技能ACK。保留S22/S24 scalar consumer作對照，未取得C1F→S22/S24因果關係。

技能条件代理新增6段308B code／102sites及32B control table；另2段239B是保留上下文。4D3B60／4D3BB0讀實際selected row catalogpointer，以definition BYTE67非0、unsigned WORD42與inline component DWORD64比較。selected global9EFBE1實際是signed BYTE，不按反編譯宣告猜WORD。4D4200控制2C的真實表項跳4D453A；gate為真才依同一U的430AC首DWORD呼叫已保留C56 producer，再呼叫C1F。另一事件只取得U1C9010／11兩個arm欄位，不補造12或opaque tail。definition BYTE6B是不同的prompt／arm分支條件，尚不能稱作learnable／官方授權。4D37E0對signed native WORD subject做<=100與>100的widget type5投影，不能據此命名人／寵／仙靈或共同64位元身份。

所有完整canonical C及當前source原檔分開保留，PE582f完整SHA按原檔核對、只複製定點raw spans；檔案雜湊與source帳務不是遊戲測試。初版writer邊界錯誤、原工具與修正diff完整保留，未覆蓋舊證據。沒有進入formatter155、capacity、render、glyph或52F330／52F170 interiors。

## 本輪盤點

|範圍|已盤點數量|本輪增量／限制|
|---|---:|---|
|TW C2S observed opcode union|156|0；跨phase與變體未全追完|
|CN C2S observed opcode union|156|0；非全部完整玩法|
|TW世界S2C長度表|252/256：230固定＋22變長|4不支援；長度表不是完整路徑分母|
|TW戰鬥分派|110：9特殊＋101 default|83 action23／86 selector7，不代表都已接通|
|CN S2C phase rows|280：account6／world206／battle68|0；方向及phase分開|
|CN receiver contexts|14／12有資格|47DE70／4812B0的phase仍未知|
|目前endpoint rows／source groups|958／28|0；不等於完整遊戲功能數|
|部分來源段|190|＋1：本輪共用SKB來源儲存串接|
|CN未host來源phase bindings／distinct values|93／71|本輪0|
|TW未host來源phase bindings／distinct values|10／10|本輪0|
|部分owner chains|38＝CN35＋TW3|本輪0|
|TW世界parser reviewed branches|42/65＝64.6%|只限這個review分母，非全遊戲完成度|
|新增完整雙向路徑|0|學習權限、扣書、儲存、回覆及Main仍有缺口|
|全遊戲路徑分母／完成百分比|未知／null|不能以opcode或部分來源段換算百分比|

## 下一個具體來源缺口

追查實際inline430A8+64的當前supplier與selected subject已學技能row來源，再把共同角色、技能資格、精確item custody、扣书、持久化mutation與原生回覆一次接起來。ready1F的多caller／component替換仍需實際owner及回覆因果，不能用UI flag、資源來源或同wire欄位代替。全遊戲來源完成後才集中建置、TW/CN/web全面驗證、修復及可遊玩發布。

三名代理完成本輪定點工作並封存停止；Root目標維持active，沒有啟動201代理。唯一報告： `20261009-cn-native-item-control-source-frontier`；唯一endpoint catalog： `endpoint-catalog200`。前199輪全部2444成員完整保留並逐檔核對，未更新歷史基準。

證據入口： `artifacts/integration/packet-connections-20261006/cn-native-item-control-source-frontier-01`。最終root及catalog manifest包含所有nested agent seal，只排除各自頂層manifest；容量沿用全Desktop/God2 regular-file/no-junction計數，另保留清理chat不同口徑，不混用分母。
