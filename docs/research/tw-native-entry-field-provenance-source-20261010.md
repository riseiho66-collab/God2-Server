# 第223輪：TW2A原生資料來源與場景bank分離

本輪是有界靜態來源研究：C++新增0、修改0、來源串接段維持212、新增完整雙向玩法路線0。未建置、執行測試、客戶端、原生程式、codec、遊戲、API、資料庫、SQL、遷移或部署。台服與全遊戲分母、完成百分比仍未知；目標保持active，台服實際來源100%之前繼續。

本輪新的可操作結論是入場body B[24..27]的高WORD，不能由共同地圖資料或角色HP臆造。對149c原生映像的兩個純資料查表leaf做精確靜態閱讀：45AA70..45AAE6取area低BYTE、scene低WORD，在17個area、9941位元組stride、142位元組scene record中找第一個匹配；45A000..45A04D取area低BYTE、scene低WORD，在17個(count,pointer)根及12位元組scene descriptor中找第一個匹配。兩leaf不使用高WORD，但後續scene呼叫仍可能接收它，因此只證明這兩個查表入口的窄化，不能宣稱整個B26..27無用或清零。195位元組是既有原生範圍的本輪保留，不當作新的全域原生覆蓋。未進入scene/UI/render/font/formatter callee。

兩個入口實際指向不同的資料表：

| 原生入口 | 真正來源 | 既有來源結果 | 正式來源缺口 |
|---|---|---|---|
| 45AA70 | gamedata 的 NPCList，row loader 45A91D..45AA3F | 451來源列、251場景群、1509資源碼；依列序追加(category,ordinal)資源對 | 沒有正式的NPCList場景群catalog。現有NPCAppearData是另一張表。 |
| 45A000／45A0A0 | gamedata 的 EnyName，loader45A1A0 | 7815原始列；重複area替換後7791可見列、96場景群；scene descriptor12B、顯示record26B | NativeEnemyDisplayCatalog已有完整來源與逐列lookup，仍缺場景有序descriptor／26B bank供應API。 |

`tools/strike_lab/import_native_enemy_display.py` 的SOURCE_ROW明確釘定149c映像與原始／decoded gamedata雜湊；`NativeEnemyDisplayCatalog::counts()`資格化全7815列指紋及可見性。這是可重用的原始描述資料來源契約，不能把每列lookup當成完整bank，也不證明現有正式資料庫已載入。本輪沒有讀取資料庫。

`NativeNpcDisplayCatalog`與其importer則釘定6bf映像、NPCAppearData4043列、prefix28／570F0。它不是149c的NPCList251群，不因同一gamedata檔名就能代替。EnyName的名字、資源byte、component及flags也不是怪物HP、雙攻雙防、技能、遭遇率、掉落或座標；那些權威數據仍另追。

另實讀目前安裝路徑 `C:/Users/risei/Desktop/God2/God2/Data2/Patch/Comm/gamedata.csvZ` 為3,131,095位元組，SHA256 `ef297a84e828537c4a18c5cf0be3d1c15bc26d5d2f25850ce9f2f030bdb58fa2`，與歷史同149c來源raw `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`不符。未解碼或匯入它，未刷新舊基準；此差異阻止直接把目前路徑當作舊來源重建，沒有否定可獨立資格化的既有完整catalog。舊decoded pin為 `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`，本輪沒有宣稱其完整輸入已恢復。

角色數值亦保持分離：logical22為25B角色／四維／maxima資料，logical24為17B的HP、MP、maxHP、maxMP四DWORD；共同load_role與load_resources是獨立狀態來源。沒有證據能把它們寫入2A opaque B8..11。原生07的raw36、選取時複製40與create40也不相同，外觀consumer相似不足以授權完整serializer。historical_body、CUSTOM-0047及只覆寫少數profile/geometry的candidate不能變成真full2A供應器。

下一個實作切點已收斂為：同來源／section／occurrence identity的不可變NPCList有序群來源，以及EnyName的完整場景descriptor投影；保留重複area替換、空群、順序、原始列與build pin。再接實際preload/完整2A issuer與場景回覆，不拿NativeMapCatalog、顯示catalog或資源計數代替權限與玩法。

目前盤點維持TW C2S觀察156值；世界S2C有效252項（230固定、22變長）、戰鬥分派110項、83動作23項、86 selector7項。CN維持C2S156值、S2C階段280項。這些層級不能相加成全遊戲分母。純帳本工具本輪讓新的完整round report可存於專用外部封存區，local latest仍可讀，歷史報告與原件不改動。
