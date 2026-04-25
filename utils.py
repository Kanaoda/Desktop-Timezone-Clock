import winreg
import sys
import os
import win32event
import win32api
import win32con
import win32gui
import win32security
import winerror

APP_NAME = "DesktopTimezoneClock"
_mutex = None

def is_already_running():
    """
    使用非繼承性 Mutex 防止重複啟動。
    若 Mutex 已存在（例如 shell 父進程殘留句柄），以視窗偵測做二次確認。
    """
    global _mutex
    sa = win32security.SECURITY_ATTRIBUTES()
    sa.bInheritHandle = 0  # 非繼承，避免 shell 父進程殘留句柄
    _mutex = win32event.CreateMutex(sa, False, f"Global\\{APP_NAME}_Mutex")
    if win32api.GetLastError() != winerror.ERROR_ALREADY_EXISTS:
        return False

    # Mutex 已存在 → 用視窗二次確認：看 TrayClockWClass 有無子視窗（我們的 overlay）
    try:
        import win32process
        our_pid = os.getpid()
        clock_wnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if clock_wnd:
            children = []
            def _cb(hwnd, acc):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid != our_pid:
                        acc.append(hwnd)
                except Exception:
                    pass
                return True
            win32gui.EnumChildWindows(clock_wnd, _cb, children)
            if children:
                return True   # 確實有另一實例的視窗在工作列
    except Exception:
        pass
    # Mutex 是殘留句柄，允許啟動
    return False

def _get_dwm_accent_hex():
    """
    讀取 Windows DWM 輔色（accent color）並轉為 #RRGGBB。
    ColorizationColor 的格式為 0xAARRGGBB。
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\DWM")
        val, _ = winreg.QueryValueEx(key, "ColorizationColor")
        winreg.CloseKey(key)
        r = (val >> 16) & 0xFF
        g = (val >> 8)  & 0xFF
        b =  val        & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None


def sample_taskbar_color():
    """
    採樣工作列實際像素色（已包含 DWM 模糊/壓深的最終視覺效果），
    避免 overlay 跟工作列顏色不一致。

    為避免採到 overlay 自己的像素，採樣位置選在工作列「左下角內側」
    （遠離右側 TrayClock 區域）。

    回傳 #RRGGBB；失敗時回傳 None。
    """
    try:
        shell_tray = win32gui.FindWindow("Shell_TrayWnd", None)
        if not shell_tray:
            return None

        left, top, right, bottom = win32gui.GetWindowRect(shell_tray)
        # 工作列方向偵測（橫向 / 直向）
        w = right - left
        h = bottom - top

        if w >= h:
            # 橫向工作列：採樣左邊偏中段，避開「開始」按鈕本身的色塊
            sx = left + min(160, w // 4)
            sy = top + h // 2
        else:
            # 直向工作列：採樣上方
            sx = left + w // 2
            sy = top + min(160, h // 4)

        screen_dc = win32gui.GetDC(0)
        try:
            pixel = win32gui.GetPixel(screen_dc, sx, sy)
        finally:
            win32gui.ReleaseDC(0, screen_dc)

        if pixel < 0:
            return None

        r =  pixel        & 0xFF
        g = (pixel >> 8)  & 0xFF
        b = (pixel >> 16) & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None


def get_system_theme():
    """
    取得工作列的前景色與背景色（用於 overlay 顯示）。
    返回: (fg_color, bg_color)，皆為 #RRGGBB 或具名色。

    優先順序：
      1. 直接採樣工作列實際像素色（最準，已含 DWM 後製）。
      2. ColorPrevalence=1 → DWM 輔色。
      3. 深/淺色主題 fallback。
    """
    sampled = sample_taskbar_color()
    if sampled:
        r = int(sampled[1:3], 16)
        g = int(sampled[3:5], 16)
        b = int(sampled[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        fg = "black" if brightness > 140 else "white"
        return fg, sampled

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        system_light, _    = winreg.QueryValueEx(key, "SystemUsesLightTheme")
        color_prevalence, _ = winreg.QueryValueEx(key, "ColorPrevalence")
        winreg.CloseKey(key)

        if color_prevalence == 1:
            accent = _get_dwm_accent_hex()
            if accent:
                r = int(accent[1:3], 16)
                g = int(accent[3:5], 16)
                b = int(accent[5:7], 16)
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                fg = "black" if brightness > 140 else "white"
                return fg, accent

        if system_light == 0:
            return "white", "#000000"
        else:
            return "black", "#FFFFFF"
    except Exception:
        return "white", "#000000"

def _find_tray_clock_window():
    shell_tray = win32gui.FindWindow("Shell_TrayWnd", None)
    if not shell_tray:
        return 0

    tray_notify = win32gui.FindWindowEx(shell_tray, 0, "TrayNotifyWnd", None)
    if tray_notify:
        clock_wnd = win32gui.FindWindowEx(tray_notify, 0, "TrayClockWClass", None)
        if clock_wnd:
            return clock_wnd

    clocks = []
    def find_clock(hwnd, acc):
        try:
            if win32gui.GetClassName(hwnd) == "TrayClockWClass":
                acc.append(hwnd)
        except Exception:
            pass
        return True
    win32gui.EnumChildWindows(shell_tray, find_clock, clocks)
    if clocks:
        return clocks[0]

    win32gui.EnumWindows(find_clock, clocks)
    return clocks[0] if clocks else 0

def _make_lparam(x, y):
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


def trigger_win_calendar():
    """
    用 PostMessage 把點擊訊息直接送進 TrayClockWClass 的訊息佇列，
    完全繞過 overlay 的 Z 序，不移動游標。
    若找不到時鐘視窗，退回 Win + N。
    """
    try:
        clock_wnd = _find_tray_clock_window()
        if clock_wnd:
            left, top, right, bottom = win32gui.GetWindowRect(clock_wnd)
            cx = (right - left) // 2
            cy = (bottom - top) // 2
            lp = _make_lparam(cx, cy)
            win32gui.PostMessage(
                clock_wnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
            win32gui.PostMessage(
                clock_wnd, win32con.WM_LBUTTONUP, 0, lp)
            return

        # fallback: Win + N (Win11 通知中心熱鍵)
        win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
        win32api.keybd_event(ord("N"), 0, 0, 0)
        win32api.keybd_event(ord("N"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
    except Exception as e:
        print(f"Error triggering calendar: {e}")

def set_autostart(enabled):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            # 獲取目前的 python 執行路徑和腳本路徑
            executable = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            # 如果是腳本執行，需要 python.exe + script_path
            # 如果是打包後的 exe，只需要 script_path
            if script_path.endswith(".py"):
                cmd = f'"{executable}" "{script_path}"'
            else:
                cmd = f'"{script_path}"'
            
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error setting autostart: {e}")
        return False

def is_autostart_enabled():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            enabled = True
        except FileNotFoundError:
            enabled = False
        winreg.CloseKey(key)
        return enabled
    except Exception as e:
        print(f"Error checking autostart: {e}")
        return False
