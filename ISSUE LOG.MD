# ISSUE LOG - Desktop Timezone Clock Overlay

此文件記錄了在 Windows 10/11 開發桌面時間覆蓋工具時遇到的技術挑戰、失敗原因及目前的解決方案。

## 1. 設定視窗無反應 (Settings Not Responding)
- **問題描述**：點擊系統匣選單中的 "Settings" 後，視窗未出現或出現後立即卡死。
- **原因分析**：Tkinter 是一個單執行緒的 UI 框架。之前的程式碼試圖在 `pystray` 的回調執行緒（子執行緒）中建立並運行 `SettingsWindow`。這會導致 Tcl/Tk 核心崩潰或無法響應。
- **解決方法**：使用 `root.after()` 或隊列機制，將設定視窗的建立請求轉發給主 UI 執行緒執行。

## 2. 透明度失效與「黑盒」現象 (Transparency/Black Box Issue)
- **問題描述**：時鐘背景顯示為純黑色塊，無法看到下方的任務欄。
- **原因分析**：
    - Windows 11 的 DWM (Desktop Window Manager) 渲染機制對 `WS_EX_LAYERED` 的屬性處理非常嚴格。
    - Tkinter 的 `-transparentcolor` 在處理非純色邊緣（反鋸齒）時會失敗。
- **解決方法**：
    - 強制使用 `win32gui.SetLayeredWindowAttributes` 並指定 `LWA_COLORKEY`。
    - 設置 `-alpha` 為 0.99 觸發 DWM 重新渲染。

## 3. 點擊穿透與原生日曆彈出 (Click-through & Calendar Popup)
- **問題描述**：點擊小工具時無法開啟 Windows 日曆，或原生時鐘會短暫跳出。
- **原因分析**：
    - `WS_EX_TRANSPARENT` 會讓視窗完全失去事件感應，無法進行任何交互。
    - 轉發 `WM_LBUTTONDOWN` 訊息給 `TrayClockWClass` 在 Win11 下經常被攔截。
- **解決方法**：
    - 移除 `WS_EX_TRANSPARENT`，讓小工具攔截點擊。
    - 使用 `pyautogui` 模擬 `Win + N` (Win11 日曆熱鍵) 或模擬點擊底層坐標。

## 4. 時區切換不生效 (Timezone Sync Issue)
- **問題描述**：在設定頁面修改時區並儲存後，桌面時鐘沒有變化。
- **原因分析**：`main.py` 與 `ClockOverlay` 之間的配置對象引用不一致，且 `update_clock` 循環中未正確重新載入配置。
- **解決方法**：在 `update_config` 中執行深度複製，並在 `ClockOverlay` 中顯式重置時區相關變數。

## 5. 按下工作列時跳回本機時間 (Jumping to Local Time)
- **問題描述**：當點擊工作列其他區域時，原生時鐘會浮現覆蓋小工具。
- **原因分析**：Windows 工作列在獲得焦點時會強制執行重繪，其層級可能暫時高於普通置頂視窗。
- **解決方法**：增加一個極高頻率（如 500ms）的 `force_topmost` 校準循環。

---
**Status**: 修復中 (Fixing...)
**Author**: Kanaoda
**Date**: 2026-04-25
