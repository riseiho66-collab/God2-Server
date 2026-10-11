# 第185輪：同一 Application 世界主機的實際連線來源串接

本輪修改7個既有 C++來源，沒有新增 C++檔。來源成果由176增至177。上一輪的真實連線登記器，現在由實際 SharedWorldHost 建立，並經台服入場／聊天及陸服登入／選角 preparation 的既有呼叫點傳下去。新增 opcode、階段綁定及完整双向玩法路徑均為0；全遊戲分母與百分比仍未知。

SharedWorldHost 在真正的 game owner 建構時，以自己的 presence 建立唯一 SharedNativeWorldTransports。transports() 在同一 owner 返回該物件，owns_repository 同時核對真正 repository／presence／visibility／transport 身分。這個 host 只登記原生連線，沒有建立另一套伺服器或 gameplay database；Token 仍弱引用連線，Snapshot 只在一次實際操作保留強引用。

Application 原有同步及非同步 SharedTaiwanWorldLifecycle factory 的兩個呼叫點，現在明確傳入 common_world->transports()。原有帳號與選角、完整 world_entry、ready、exclusive dispatcher、vault cleanup/publication 條件保持不變。SharedTaiwanNativeWorldHostPlan::RecordSources::with_native_chat 的真正 ChatSource::create 呼叫也使用同一個 Context.common_world->transports()，因此連線登記與聊天收件者查找不再依賴各供應者自行另建來源。

陸服 compose_native_login 從實際 Context.common_world 保留該來源。具體 common_preparation 的 create 呼叫把同一指標送進 SharedWorldPreparation；替代 naming_preparation 與 world preparation 除了核對原 repository／map／presence／visibility，另需核對完全相同的 transport source。SharedWorldPreparation 接收真正 Reservation.gameplay 的 Sources 後，先保留供應者原 cleanup；若選用 host source，缺少的 world_transports 填入同一指標，已存在的不同來源則拒絕，之後接原有正常／transfer 流程及 SharedWorldGameplay::compose。沒有補出缺失的 native bytes、入場成功或權限。

Preparation 階段失敗仍在原世代 Lease 上清理；此時尚未完成後續 initial1C held output／outward，所以登記 Token 尚未產生，不依 session ID 刪除登記。進場後的普通斷線、Ready／Gameplay 失敗則沿上一輪保存的 exact Token capsule 清理。Main 尚未提供完整 native plan；本輪是實際來源呼叫串接，不是已啟用或客戶端驗收。

子代理補充台服觀戰目標的限定原生來源：world S2C D0 經 RVA69DF4／69DFC 到完整78CC0；logical 長度7，body0 是一基 slot，body+2／+4 兩個 WORD 各零擴展為 DWORD，寫入 UI 的89A2C／89AF4兩個目標陣列。body1 在此 callee 未使用，不能補猜欄位。D0 另外令 flags=(old&FE)|02。WORD FFFF 變成0000FFFF，不能補成FFFFFFFF無效值；後者才是已追過 C2S6E caller 的比較值。

S2C CD 經69DE2到78D10，logical 長度65；它更新 flags、兩個22B原始文字及88A98／88A9C metadata DWORD，不是 D0 的目標陣列。不能依 callee 最大讀到 body59 就把原封包縮短。已知 reset77850..778E0 清理50個60B record，並把兩個50-DWORD目標陣列設為FFFFFFFF；只作擴展既有局部證據，未冒算新函式或目前已載入狀態。

D0／CD 寫入者沒有檢查 slot 範圍，因此1..50是未來服務端依實際50槽儲存採用的明確輸出限制，不是原生客戶端會拒絕其他值的證據。CD 可在目標陣列未重寫時改 flags；低位等於2不能證明舊目標仍有效。真正 target namespace、發行者、recipient UI／entry epoch、當前 battle instance／觀戰資格與 common64映射仍需權威來源，不能憑數值、角色名稱或6F遮罩推定。

本輪8個原生 spans／716B：2個新完整函式337B、1個新限定呼叫區36B、1個既有 reset 擴展144B、4個保留區199B；129 instruction sites、4個保留 table entries。原 D0／CD opcode 及長度已在舊盤點，未新增封包數。

| 盤點 | TW | CN |
|---|---:|---:|
| C2S opcode |156（151 generic＋5 supplemental）|156（完整 phase 尚待釐清）|
| S2C 盤點口徑 |252 length 支援：230 fixed＋22 variable；world 非 default206|280 phase/opcode entries：account6＋world206＋battle68|
| 本輪新增 opcode／phase binding |0／0|0／0|
| 本輪新增完整雙向玩法路徑 |0|0|

TW battle83 actions23／battle86 selectors7，共30個追查前沿項目，不是全部變體。958 endpoint rows／28 source groups 不是全遊戲路徑分母。真正 audience／membership／rate／mute、完整 header/body、wire page／native text state／cipher、entry／appearance、全部玩法與 Main 選用仍有缺口。

本輪 fresh before1320、前輪2336封存成員及原始／中間／最終來源分別保存。Application 最終只作兩個精確 bytes 替換，原始文字表示及一度使用的 LF 中間檔均保留。沒有建置、測試、native/C++/Lua/API/codec 執行、DB／SQL存取或部署，也未重試155 formatter/capacity/render/glyph chain 或深入52F330／52F170。帳號、存檔、IME、認證、頭像、客戶端、原生字體與繁簡轉換保留；TW／CN／web共用64位數值、仙幣99999999999、合格堆疊99與等級不改要求持續有效。目標保持 active，全部來源串接後才集中驗證、修復及發布。
