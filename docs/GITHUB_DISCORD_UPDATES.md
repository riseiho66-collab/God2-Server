# 私有原始碼與更新通知

專案：https://github.com/riseiho66-collab/God2-Server （Private）。
通知頻道：https://discord.com/channels/1550341919379562498/1558770971291164682 。

每次推送分支後，`Discord updates` 工作流以 GitHub Actions 名稱發送綠色卡片，
標題包含專案／分支，點擊可查看提交；清單逐項標示新增、修改、刪除、重新命名。
大量變更時卡片顯示前段，完整清單附為 `changed-files.txt`，避免洗頻或默默漏項。
首次提交列出全部加入的檔案。需要補發時可在 Actions 手動執行；補發會新增訊息。

Webhook 儲存在 repository secret `DISCORD_WEBHOOK_URL`，不放入原始碼、日誌或文件。
通知只發往上述頻道；頻道成員會看見檔案名稱，私有 GitHub 內容仍需授權才能開啟。
工作流只有 contents: read，沒有遊戲建置、測試、服務重啟或部署步驟。

Git 只保存原始碼與文件。本機 artifacts、資料庫／存檔、客戶端二進位、建置輸出、
封包捕獲及封存不納入 Git。研究文件引用的本機證據路徑須依原交接記錄另行取得，
私有原始碼備份不等於完整本機證據備份，也不代表遊戲已部署或完成驗收。
