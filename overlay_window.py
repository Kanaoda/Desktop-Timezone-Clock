"""桌面時鐘 overlay：覆蓋於 Windows 工作列原生時鐘位置上方。

策略：
  把 overlay 視窗用 SetParent 嵌入 TrayClockWClass，成為它的子視窗。
  子視窗永遠繪製在父視窗 (TrayClockWClass) 的內容上方，完全不需要
  與工作列搶奪 Z-order，也不需要 LWA_COLORKEY（避免 hit-test 穿透）。
  click 事件由我們的 Tkinter binding 正常處理。
"""
import time
import tkinter as tk
import win32gui
import win32con
import win32api

from timezone_utils import get_current_time_in_tz
from utils import get_system_theme, sample_taskbar_color
from calendar_popup import CalendarPopup


def _find_tray_clock_window():
    shell_tray = win32gui.FindWindow("Shell_TrayWnd", None)
    if not shell_tray:
        return 0
    tray_notify = win32gui.FindWindowEx(shell_tray, 0, "TrayNotifyWnd", None)
    if tray_notify:
        clk = win32gui.FindWindowEx(tray_notify, 0, "TrayClockWClass", None)
        if clk:
            return clk
    clocks = []
    def _cb(hwnd, acc):
        try:
            if win32gui.GetClassName(hwnd) == "TrayClockWClass":
                acc.append(hwnd)
        except Exception:
            pass
        return True
    win32gui.EnumChildWindows(shell_tray, _cb, clocks)
    return clocks[0] if clocks else 0


def _embed_tk_in_native_parent(hwnd, parent_hwnd, w, h):
    """SetParent 後依 Windows 建議補上 WS_CHILD / 清掉 WS_POPUP，讓子視窗能正確收到滑鼠與重繪。"""
    try:
        win32gui.SetParent(hwnd, parent_hwnd)
    except Exception as e:
        print(f"[overlay] SetParent failed: {e}")
        return False
    try:
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        # MS 文件：子視窗需 WS_CHILD，且不可維持 WS_POPUP
        style = (style & ~win32con.WS_POPUP) | win32con.WS_CHILD
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOP, 0, 0, w, h,
            win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED,
        )
    except Exception as e:
        print(f"[overlay] child style/pos failed: {e}")
    return True


def _tray_clock_client_size(clock_wnd):
    """使用父視窗 *客戶區* 寬高，與我們覆蓋的區域一致，避免邊界裁切與點擊偏位。"""
    try:
        l, t, r, b = win32gui.GetClientRect(clock_wnd)
        w = max(r - l, 72)
        h = max(b - t, 28)
        return w, h
    except Exception:
        left, top, right, bottom = win32gui.GetWindowRect(clock_wnd)
        return max(right - left, 72), max(bottom - top, 28)


class ClockOverlay:
    def __init__(self, clock_config, global_config, on_open_settings=None):
        self.config = clock_config.copy()
        self.global_config = global_config
        self.on_open_settings = on_open_settings
        self.root = tk.Tk()

        self.sys_fg, self.sys_bg = get_system_theme()
        self._calendar_popup = None
        self._single_click_job = None
        self._last_click_time  = 0.0   # 用於雙擊計時（不依賴 WM_LBUTTONDBLCLK）
        self._embedded = False       # 是否已完成 SetParent 嵌入
        self._clock_wnd = 0          # TrayClockWClass hwnd 快取

        bg = self._resolve_bg_color()
        fg = self._resolve_font_color()
        print(f"[overlay] init  bg={bg}  fg={fg}  tz={self.config.get('target_timezone')}")

        self.root.geometry("1x1-10000-10000")  # 初始將視窗定位於極遠的螢幕外，避免在 (0,0) 處短暫映射
        self.root.overrideredirect(True)
        # 移除起始的 -topmost 屬性，避免 DWM 在 (0,0) 留下置頂點擊穿透與攔截陰影。
        # 置頂狀態將僅在 fallback（非嵌入模式）中透過 Win32 HWND_TOPMOST 或 attributes("-topmost") 啟用。
        self.root.config(bg=bg, borderwidth=0, highlightthickness=0)

        self.label = tk.Label(
            self.root,
            text="",
            font=(self.config["font_family"], self.config["font_size"]),
            fg=fg,
            bg=bg,
            anchor="center",
            justify="center",
            padx=2,
            borderwidth=0,
            highlightthickness=0,
        )
        self.label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # 只綁 <Button-1>，內部用時間差區分單/雙擊（整面積由 label 覆蓋，避免重複綁定）
        self.label.bind("<Button-1>", self._on_click_raw)

        # 先讓 Tk 建好視窗 (HWND 必須存在才能呼叫 win32 API)
        self.root.update_idletasks()

        # 設定基本樣式（不啟用 layered，避免 DWM Z-order 問題）
        self._apply_base_styles()

        # 嘗試嵌入工作列
        self._try_embed()

        self.update_clock()
        self.root.update()
        self.sync_theme()
        self.force_topmost()
        print(f"[overlay] ready  embedded={self._embedded}  geometry={self.root.geometry()}")

    # ------------------------------------------------------------------ #
    #  EMBED INTO TASKBAR                                                  #
    # ------------------------------------------------------------------ #

    def _apply_base_styles(self):
        """設定 WS_EX_NOACTIVATE（不搶 focus）。不加 WS_EX_LAYERED 以避免 Z-order 問題。"""
        hwnd = self.root.winfo_id()
        ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex |= win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)

        bg = self._resolve_bg_color()
        self.root.config(bg=bg, borderwidth=0, highlightthickness=0)
        self.label.config(
            bg=bg, fg=self._resolve_font_color(),
            borderwidth=0, highlightthickness=0,
        )

    def _try_embed(self):
        """把 overlay 嵌入 TrayClockWClass，成為它的子視窗。"""
        clock_wnd = _find_tray_clock_window()
        if not clock_wnd:
            print("[overlay] TrayClockWClass not found, using TOPMOST fallback")
            self._topmost_fallback()
            return

        self._clock_wnd = clock_wnd
        hwnd = self.root.winfo_id()
        try:
            w, h = _tray_clock_client_size(clock_wnd)

            if not _embed_tk_in_native_parent(hwnd, clock_wnd, w, h):
                raise RuntimeError("SetParent failed")

            self._embedded = True
            # 只同步「寬高」給 Tk，不要用螢幕 +x+y（SetParent 後子視窗實際在 (0,0)，
            # 若仍寫成螢幕座標，滑鼠點擊座標映射會錯亂導致點不進 label）
            self.root.geometry(f"{w}x{h}")
            self.root.update_idletasks()
            # 仍記錯誤的螢幕座標在 geometry 內是為了讓 Toplevel 邏輯有合理尺寸；
            # CalendarPopup 若需螢幕位置請用 GetWindowRect(overlay)
            _sx, _sy, _ex, _ey = win32gui.GetWindowRect(hwnd)
            print(
                f"[overlay] embedded in TrayClockWClass  client={w}x{h} "
                f"screen=({_sx},{_sy}) tk winfo={self.root.winfo_width()}x{self.root.winfo_height()}"
            )
        except Exception as e:
            print(f"[overlay] embed failed: {e}, using TOPMOST fallback")
            self._topmost_fallback()

    def _topmost_fallback(self):
        """找不到 TrayClockWClass 時的備用方案：覆蓋在畫面右下角。"""
        try:
            self.root.attributes("-topmost", True)  # 啟用置頂屬性
        except Exception:
            pass
        sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self.root.geometry(f"100x40+{sw - 110}+{sh - 50}")
        hwnd = self.root.winfo_id()
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW,
        )

    # ------------------------------------------------------------------ #
    #  TOPMOST + SYNC                                                      #
    # ------------------------------------------------------------------ #

    def force_topmost(self):
        """
        若已嵌入，持續確保子視窗在父 (TrayClockWClass) 最上層。
        若使用 fallback，持續保持 HWND_TOPMOST。
        同時監視 TrayClockWClass 是否重建（例如 Explorer 重啟），
        若消失則重新嵌入。
        """
        try:
            hwnd = self.root.winfo_id()
            if self._embedded:
                # 確保仍在父視窗最上層
                win32gui.SetWindowPos(
                    hwnd, win32con.HWND_TOP, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                )
                # 監視父視窗（Explorer 重啟後 HWND 會改變）
                if self._clock_wnd and not win32gui.IsWindow(self._clock_wnd):
                    print("[overlay] TrayClockWClass gone, re-embedding...")
                    self._embedded = False
                    self._clock_wnd = 0
                    self._try_embed()
            else:
                self._try_embed()
                if not self._embedded:
                    win32gui.SetWindowPos(
                        hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                    )
        except Exception:
            pass
        self.root.after(500, self.force_topmost)

    def sync_theme(self):
        new_fg, new_bg = get_system_theme()
        if new_fg != self.sys_fg or new_bg != self.sys_bg:
            self.sys_fg = new_fg
            self.sys_bg = new_bg
            self._apply_base_styles()
        self.root.after(10000, self.sync_theme)

    # ------------------------------------------------------------------ #
    #  COLOR HELPERS                                                       #
    # ------------------------------------------------------------------ #

    def _resolve_font_color(self):
        v = self.config.get("font_color", "system")
        if v in ("system", "auto", None, ""):
            return self.sys_fg if self.sys_fg in ("white", "black") or (
                isinstance(self.sys_fg, str) and self.sys_fg.startswith("#")
            ) else "white"
        return v

    def _resolve_bg_color(self):
        v = self.config.get("bg_color", "system")
        if v in ("system", "auto", None, ""):
            sampled = sample_taskbar_color()
            if sampled:
                # 這裡更新 sys_bg 和 sys_fg，確保字體顏色能即時跟隨背景採樣更新
                self.sys_bg = sampled
                from utils import get_color_brightness
                brightness = get_color_brightness(sampled)
                self.sys_fg = "black" if brightness > 140 else "white"
                return sampled
            return self.sys_bg if isinstance(self.sys_bg, str) and self.sys_bg.startswith(
                "#") else "#000000"
        return self._norm(v)

    def _norm(self, value):
        if isinstance(value, str) and len(value) == 7 and value.startswith("#"):
            try:
                int(value[1:], 16)
                return value
            except ValueError:
                pass
        return "#000000"

    def _current_language(self):
        try:
            return str(self.global_config.get("language", "zh")).lower()
        except Exception:
            return "zh"

    # ------------------------------------------------------------------ #
    #  CLICK → CALENDAR POPUP                                              #
    # ------------------------------------------------------------------ #

    # ── 單擊 / 雙擊偵測（純 <Button-1>，在嵌入子視窗中最可靠）─────────────────

    _DBLCLICK_MS = 450   # 雙擊間隔門檻（ms），略寬以符合一般操作節奏

    def _on_click_raw(self, event=None):
        """所有點擊都從這裡進入：用時間差區分單擊 / 雙擊。"""
        now = time.time()
        gap = (now - self._last_click_time) * 1000  # ms
        self._last_click_time = now

        if gap < self._DBLCLICK_MS:
            # ── 雙擊：取消延遲的單擊，改為開設定 ──────────────────────────
            self._last_click_time = 0.0   # 重置，防止第三次點擊被視為雙擊
            if self._single_click_job is not None:
                try:
                    self.root.after_cancel(self._single_click_job)
                except Exception:
                    pass
                self._single_click_job = None
            # print("[overlay] double-click → open settings")
            if callable(self.on_open_settings):
                self.root.after(0, self.on_open_settings)
        else:
            # ── 單擊：延遲執行，給雙擊留時間取消 ──────────────────────────
            if self._single_click_job is not None:
                try:
                    self.root.after_cancel(self._single_click_job)
                except Exception:
                    pass
            self._single_click_job = self.root.after(
                self._DBLCLICK_MS, self._do_single_click)
        return "break"

    def _do_single_click(self):
        self._single_click_job = None
        # print("[overlay] single click → toggle calendar")
        self.toggle_calendar()

    def toggle_calendar(self):
        """供 overlay 單擊與托盤單擊共用：切換日曆開/關。"""
        try:
            inst = CalendarPopup._instance

            if inst is not None and getattr(inst, "_closed", True):
                CalendarPopup._instance = None
                self._calendar_popup = None
                inst = None

            if inst is not None:
                try:
                    inst.close()
                except Exception:
                    pass
                CalendarPopup._instance = None
                self._calendar_popup = None
                print("[overlay] popup closed (toggle)")
                return

            tz_name  = self.config.get("target_timezone", "Asia/Hong_Kong")
            language = self.global_config.get("language", "zh")
            self._calendar_popup = CalendarPopup(
                parent=self.root, tz_name=tz_name, language=language)
            print("[overlay] popup created")
        except Exception as e:
            print(f"[overlay] on_click error: {e}")
            CalendarPopup._instance = None

    # ------------------------------------------------------------------ #
    #  CLOCK UPDATE                                                        #
    # ------------------------------------------------------------------ #

    def update_clock(self):
        tz_name = self.config.get("target_timezone", "Asia/Hong_Kong")
        now = get_current_time_in_tz(tz_name)

        time_str = now.strftime(self.config.get("time_format", "%p %I:%M"))
        if self._current_language() == "zh":
            time_str = time_str.replace("AM", "上午").replace("PM", "下午")

        if self.config.get("show_date", True):
            date_str = now.strftime(self.config.get("date_format", "%Y/%m/%d"))
            self.label.config(text=f"{time_str}\n{date_str}")
        else:
            self.label.config(text=time_str)

        self.root.after(1000, self.update_clock)

    # ------------------------------------------------------------------ #
    #  POSITION (公開，供 apply_window_styles 呼叫)                         #
    # ------------------------------------------------------------------ #

    def position_overlay(self):
        """重新定位（用於設定變更後 re-sync）。"""
        if not self._embedded:
            return
        if not self._clock_wnd or not win32gui.IsWindow(self._clock_wnd):
            return
        try:
            w, h = _tray_clock_client_size(self._clock_wnd)
            hwnd = self.root.winfo_id()
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_TOP, 0, 0, w, h,
                win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW,
            )
            self.root.geometry(f"{w}x{h}")
            self.root.update_idletasks()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  CONFIG UPDATE                                                       #
    # ------------------------------------------------------------------ #

    def update_config(self, new_config):
        self.config = new_config.copy()
        self.sys_fg, self.sys_bg = get_system_theme()
        self.label.config(
            font=(self.config["font_family"], self.config["font_size"]),
            fg=self._resolve_font_color(),
            bg=self._resolve_bg_color(),
        )
        self.root.config(bg=self._resolve_bg_color())
        self.position_overlay()

    def apply_window_styles(self):
        """供外部 update_config 呼叫的相容方法。"""
        self.update_config(self.config)

    def run(self):
        self.root.mainloop()

    def close(self):
        try:
            if self._calendar_popup is not None:
                self._calendar_popup.close()
        except Exception:
            pass
        self.root.destroy()
