# Desktop Timezone Clock Overlay | 桌面多時區時鐘覆蓋工具

[English](#english) | [繁體中文](#繁體中文)

---

## 繁體中文

這是一個專為 Windows 10/11 設計的輕量化桌面工具，旨在解決系統時區與顯示時間不一致的需求。

### 🚀 解決的核心問題
本工具特別適合以下族群：
1. **頻繁外遊的用家**：需要電腦底層運行特定時區（如工作需要的美國時間），但想在桌面上快速查看當地或家鄉時間。
2. **長期使用 VPN 的用家**：解決因使用 VPN 導致電腦系統時間與實際身處時區不符，或不方便修改系統底層時間的問題。

### ✨ 功能特點
- **精準位置覆蓋**：自動偵測並完美覆蓋 Windows 工作列原有的時鐘位置。
- **顏色自動跟隨工作列**：直接採樣工作列實際像素顏色作為覆蓋層底色，與工作列視覺 100% 一致；亦可自訂背景／文字色。
- **內建月曆 popup**：點擊時鐘即彈出自家設計的月曆視窗（顯示完整日期、所選時區當前時間，並可瀏覽前後月份），不依賴 Windows 原生日曆觸發機制，穩定可靠。
- **全球時區支援**：內建完整時區資料庫，可自由切換全球任何城市時間。
- **中英雙語介面**：設定視窗支援繁體中文與英文，可在設定中即時切換。
- **現代化設定 UI**：採用 CustomTkinter 打造的深色科技風格介面，支援深色標題列。
- **輕量與開源**：基於 Python 開發，佔用資源極低，且完全透明公開。

### 🛠️ 安裝與使用
1. **環境需求**：安裝 [Python 3.9+](https://www.python.org/)。
2. **安裝套件**：
   ```bash
   pip install pywin32 pystray Pillow tzdata requests customtkinter
   ```
3. **啟動程式**：執行 `python main.py`。
4. **設定時區**：在右下角系統匣圖示點擊右鍵，選擇 **「設定 (Settings)」** 即可自訂時區。
5. **切換語言**：在設定視窗的「語言」列選擇 **中文** 或 **EN**，介面即時切換。

### 📦 打包與發佈（Windows 安裝檔）
若你要發佈到 GitHub Releases，建議用以下流程：

1. 安裝 Inno Setup 6（需有 `ISCC.exe`）。
2. 先建立 exe + 安裝檔：
   ```bash
   python build_installer.py
   ```
3. 產物位置：
   - `dist/DesktopTimezoneClock.exe`
   - `dist/DesktopTimezoneClock-Setup.exe`

安裝器特性（`installer.iss`）：
- 預設安裝到使用者目錄（不需系統管理員權限）。
- 安裝時預設勾選「開機自動啟動」。
- 寫入 `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`。
- 可在安裝完成後立即啟動程式。

### 🌐 語言支援
| 語言 | 狀態 |
|------|------|
| 繁體中文 | ✅ 完整支援 |
| English | ✅ 完整支援 |

### ☕ 支持作者
如果你覺得這個工具對你有幫助，歡迎支持我的持續開發：
- **GitHub Sponsors**: [https://github.com/sponsors/Kanaoda](https://github.com/sponsors/Kanaoda)
- **Buy Me a Coffee**: [https://buymeacoffee.com/kanaoda](https://buymeacoffee.com/kanaoda)

**作者**: Kanaoda  
**版權**: © 2026 Kanaoda. Licensed under the MIT License.

---

## English

A lightweight desktop utility for Windows 10/11 designed to bridge the gap between system-level timezone settings and your desired display time.

### 🚀 Who is this for?
This tool is specifically built for:
1. **Frequent Travelers**: Keep your system on a specific timezone (e.g., US time for work) while displaying local or home time on your taskbar.
2. **Long-term VPN Users**: Solve the issue where system time doesn't match your actual location due to VPN usage, without messing with low-level system settings.

### ✨ Key Features
- **Precise Taskbar Overlay**: Automatically detects and covers the original Windows taskbar clock.
- **Auto Color Matching**: Samples the actual pixel color of the taskbar to keep the overlay 100% visually consistent, including DWM tinting. Custom font/background colors are also supported.
- **Built-in Calendar Popup**: Clicking the clock opens a self-rendered calendar popup (full date, target-timezone time, and month navigation). No reliance on Windows' native calendar flyout — works consistently on Windows 10 and 11.
- **Global Timezone Support**: Full timezone database support for any city worldwide.
- **Bilingual Interface**: Settings window supports both Traditional Chinese and English, switchable at runtime.
- **Modern Settings UI**: Dark tech-style interface built with CustomTkinter, with dark title bar support.
- **Lightweight & Open Source**: Built with Python, minimal resource usage, and fully transparent code.

### 🛠️ Installation & Usage
1. **Prerequisites**: Install [Python 3.9+](https://www.python.org/).
2. **Install Dependencies**:
   ```bash
   pip install pywin32 pystray Pillow tzdata requests customtkinter
   ```
3. **Run Application**: Execute `python main.py`.
4. **Configure**: Right-click the system tray icon and select **"Settings"** to choose your target timezone.
5. **Switch Language**: In the Settings window, select **中文** or **EN** in the Language row to switch the interface instantly.

### 📦 Packaging for GitHub Release (Windows Installer)
For publishing to GitHub Releases, use this flow:

1. Install Inno Setup 6 (must provide `ISCC.exe`).
2. Build EXE + installer:
   ```bash
   python build_installer.py
   ```
3. Output files:
   - `dist/DesktopTimezoneClock.exe`
   - `dist/DesktopTimezoneClock-Setup.exe`

Installer behavior (`installer.iss`):
- Per-user install (no admin required).
- "Launch on Startup" is enabled by default at install time.
- Writes to `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`.
- Optionally launches the app immediately after installation.

### 🌐 Language Support
| Language | Status |
|----------|--------|
| Traditional Chinese (繁體中文) | ✅ Full support |
| English | ✅ Full support |

### ☕ Support the Developer
If you find this tool useful, feel free to support my work:
- **GitHub Sponsors**: [https://github.com/sponsors/Kanaoda](https://github.com/sponsors/Kanaoda)
- **Buy Me a Coffee**: [https://buymeacoffee.com/kanaoda](https://buymeacoffee.com/kanaoda)

**Author**: Kanaoda  
**Copyright**: © 2026 Kanaoda. Licensed under the MIT License.
