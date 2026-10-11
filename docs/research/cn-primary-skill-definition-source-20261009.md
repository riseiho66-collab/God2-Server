# 第203輪：陸服世界主技能清單與同庫來源

第203輪是使用者這次續工五輪中的第1輪。依「從本輪開始算起，5輪之後結束並停止工作」，第203至207輪完成後暫停，不開始208輪。第202輪停止點已完成並保留歷史；本輪因使用者「繼續工作」恢复active。

新增 `CnWorldPrimarySkillSource.h/.cpp`，修改11份C++來源，新增1段來源串接，累計193段。新增完整雙向遊戲路徑0，完整遊戲分母與百分比未知。本輪不建置、測試、執行native/codec/server/DB/SQL、不遷移部署。

原世界主技能解析器只有 bank pointer+4、group6E04、record110 的指標幾何，再查共用目錄；沒有比對原指標位置的實際bank。新可選來源持有完整 actual selected snapshot、完整112656B bank payload及強原生目錄，在任何外部 observer 前複製原始输入。bank address必須等於實際subject保存的bank，且整段payload與釘定resource去除4B檔头後逐byte相等。按原主清單順序匹配每個實際pointer、完整110B record、source、offset、hash，保留flags、重複與順序；不拿row+5C/+60 auxiliary當primary，不生成pointer，不读取客户端process memory。

共用 `CnSharedSkillCatalog` 現在保留實際store的強生命週期owner及必需StoreCurrent。每次原生來源callback、借用SQLite讀取之前及之後都需先由真正store owner确认同一reader、native provider、store lifetime、population及epoch；resource SHA/Current不代替DB Current。既有453筆驗定義流程及所有lookup經過nonreentrant guard，捕捉到nested reentry也不可復活；已匹配定義的共享列缺失/腐壞會使該來源失效。這是必要來源接線，不是自動取得資料庫所有權或新實際schema/data。

SharedServerPlan對顯式native_skill_definitions新增必需native_skill_store_lifetime/native_skill_store_current，唯一原生host bindcall同步傳入；只有store資格而沒有native definitions被拒絕。未選定該opt-in的舊來源不添加讀取，也沒有任何默認非擁有marker。真正Application store owner必須仍由實際配置提供；Main沒有因此變成完整可用的正式遊戲owner。

WORLD primary來源接入 `CnPrebornSkillReferences` 與 `CnPrebornSkillChoiceSource`，強來源路徑逐整筆比對shared/native definition。窗口Source可選read_primary_skills；選定後缺少subject、supplier返回null或不一致都拒絕，不回退舊幾何路徑。沒有選此額外證據時，原幾何推算保留未知bank身份，不能宣稱已驗明actualbank。own-server共同operation本身不要求native記憶體。

prepare/issued/current/selection各階段持有同一完整Window及強Primary，回呼之前複製Scope/Selection/Window並拒絕nested reentry；true callback即使吞掉重入錯誤也不能復活已terminal窗口。發布轉交Choices前結束本source觀察stage，允許合法來源prepare。apply把原生bank scope與完整entries/flags定義保存為owned Facts，再退休原窗口執行真正一次共用operation；postcommit delivery只交retained provenance，不問過期precommit Current。沒有新增default學習、扣書、common技能identity、資格或原生成功回覆。

子代理新增127B/34個原生指令位置：493FC0完整70B為真正whole-row reset；4927FC呼叫端57B明確傳R=P+1478084，ECX另為P。R+164=0、R+15F=FF、R+160=0，memset(R+168,0,3EC0)清16個完整3EC列，同時清主技能count/flags/pointers及aux。之後獨立inventory reset不是技能grant；WORLD CF success分支後的C1F/C23沒有證明技能學習或回覆因果。旧116B初始化context保留不重算。這與WORLD30只清primary count、可能保留aux stale state的生命週期不同。

正向初始主清單供應、WORLD→battle primary填入、真實common actor/learned/custody、技能書扣除與持久事件/交易及原生回覆仍待接。下一個具體原生data leaf為4D2B50的primary pointer ordinal lookup，僅會員查找不當writer/grant；將接著沿實際非GUI寫入端追源。帳號存檔、client EXE、原生字體、繁簡轉換、等級與凍結功能維持。

現有盤點未變：TW/CN觀察C2S聯集各156；TW世界S2C長度支持252/256，戰鬥110條分派；CN S2C階段条目280（帳號6／世界206／戰鬥68）。958個端點索引與193段來源不是全遊戲完成路徑。TW解析分支審閱42/65＝64.6%，僅限這個範圍。完整遊戲完成百分比仍null。
