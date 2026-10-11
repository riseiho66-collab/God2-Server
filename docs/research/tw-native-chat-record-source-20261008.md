# 原生聊天處理來源與混合分派（第178輪）

本輪接續全部來源串接，目標模式保持 active。只進行靜態原生恢復與 C++ 來源接入，沒有建置、測試、遊戲／codec／API 執行、資料庫存取或部署。

新增 `SharedTaiwanNativeChatSource`，接收已解析但完整保留四個 header bytes 的 TW `2F` Request。真正的 WorldOwner 必須資格化原生文字種類、CP950／CP936、完整 UTF-8 原文與真正正文範圍、權限、收件者集合及完整 native `5C`；不從玩家名字、共同角色 ID 或語系 bit 猜原生身分、協定或編碼。未知 GM／control／channel 分支沒有普通文字替代。正文沿用既有繁簡轉換，完整 header、名字、控制 prefix／suffix 保留，顯示替換或截斷由真實 owner 對完整結果明確資格化。

台服新來源限定本輪已恢復的 `5C` 普通 channel 0／6 接收域，整段 text 預算252 bytes，再扣原始名字／prefix／suffix。陸服輸出使用既有獨立 CN consumer contract，普通 peer bubble 必須有真正 preceding visibility token、完整 actor DWORD 及原生名字投影。TW bubble 不借用 CN token 當證明，實際 loaded window／renderer／容量與權限仍由真來源提供。完整 TW／CN 收件者 native bytes 在傳送前準備；來源失效或部分提交失敗只令精確 Session／Lease 終止，不重播前段、不聲稱跨收件者原子性。

自己的 `5C` 不能直接傳送而越過混合批次前面的 movement／其他回覆。新來源由必要的 `sender_wire` 供應端提供與完整 prepared native record 對應的實際 Session profile envelope，資格完成後回傳原始加密位元組；不默認選零 seed laboratory encoder。`SharedTaiwanNativeRecordHandlerSource` 將每個 chat request 和最大連續的其餘原生區段按原序交真正處理端，再將 sender envelopes 按原順序交混合 dispatcher。沒有額外回覆必須由實際來源明確決定，不補假 ACK。

`RecordSources::with_native_chat` 使用 Application 同一個真正 Context 的 Presence／Visibility 組裝聊天來源與剩餘處理端，再交既有 MixedRecords plan／WorldRecordSource／Application。OtherBinding 增加必要的 release／invalidate_active：被捕捉的外層重入會傳到真正 Others 與 movement，兩條都嘗試；斷線先移除精確 record bookkeeping 並清理 Others，再沿既有 Application 撤下 movement／scene。一般 Main 仍未選取，實際 WorldOwner、native header／權限／cipher／場景供應及其餘處理者仍待補齊，不能算成全功能已打通。

本輪新原生證據明確更正來源定位：`4968E0` 使用 `$gmsoft01 %s`，是特殊命令 producer，不能當普通 common chat；普通／頻道 UI producer 為另一條 `496990` 路徑。凍結的 serializer 與其歷史原件不改寫。`47DE00` 組合256-byte local buffer 時先加原生3-byte prefix，再複製完整 text 與 NUL，形成252-byte前置安全域；實際 loaded text owner 的行數、各行 capacity、renderer handle 與 generation 仍需完整資格。固定 transport 上限不能替代所有 sink 的容量證明。台服普通 bubble consumer 本身不強制 `name: `，不能把限定來源的身分格式當成全原生規則。

TW 代理保留26段原生範圍、9317 bytes、117個精確指令位置及18份原始 literal／table 資料；分類為12個新增完整 sink 函式、1個新增有界 caller、5個擴展既有範圍、8個保留 context。擴展與保留部分不重新當成新增函式，更不計為新封包。

CN 子代理新增三個完整函式及一個有界 setup 區段，共2809 bytes、六條關係。恢復了八組 signed direction 的真正 fallback 候選順序、path owner 的126-byte buffer 初始化和 `+0C` setter／實際 caller。零方向或全部候選 AL0 時不寫 output pointers，不能補默認座標或把 ret18 說成 bool；constructor 也不是完整 buffer 清零。真正 map `+BC` producer、服務端權限、完整 path count／容量與 native5D 仍開放，CN receiver14／qualified12不變。

| 目前索引／本輪增量 | TW | CN |
|---|---:|---:|
| C2S opcode 索引 | 156（151一般＋5補充） | 156 |
| S2C length-supported opcode／phase entries | 252（230定長＋22變長） | 280（帳號6／世界206／戰鬥68） |
| 新 opcode／phase binding | 0／0 | 0／0 |
| 新完整雙向遊戲路徑 | 0 | 0 |

四個新、四個既有 C++ 檔案實際變更，來源紀錄169增為170。958個 endpoint rows、28個群組與30個戰鬥 action／selector entries 不重計。全遊戲路徑分母、完整已打通總數及百分比仍未知；本輪可接入來源與新的原生證據不充當完成率。

後續持續補真正 native input／權限／收件者／完整輸出／cipher／loaded resource 來源與剩餘玩法；TW／CN entry／world supplier／Main、64位元儲存／線路／物件／飄字／網頁、stack99全部變動路徑及網頁 WSS／TLS／hosting 都保留。仙幣上限99999999999、其他上限另定、等級不改、原生字體、繁簡轉換、帳號存檔／認證／IME／頭像與既有凍結功能保持原要求。

fresh before1277 SHA256 `c13dab36dbf2e0b6db741e34cf0f2845e25e6646d51a4976c8426251c6df3318`，第177輪完整2231個封存成員保留。完整實際來源／native inputs、初版與修補前原件、代理封存、四份原始及四份最終報告分別保存，舊基準不刷新。本輪未執行 native／C++／Lua／codec／API／DB／SQL，也未重試曾被安全工具停止的 formatter／capacity 鏈。
