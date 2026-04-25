"""自製日曆 popup。

定位策略：
  withdraw() → 建立 UI → update() → after(10ms, _show_positioned)
  _show_positioned：先 deiconify 到螢幕外（-9999），
  再用 win32gui.SetWindowPos 移到正確螢幕絕對座標。

關閉方式：
  1. 點擊日曆視窗以外任何地方（FocusOut 偵測，200ms 延遲防誤觸）
  2. 再次點擊工作列時鐘 (toggle)
  3. 按 Esc
"""
import calendar
import tkinter as tk
from datetime import datetime
import win32api
import win32con
import win32gui

from timezone_utils import get_current_time_in_tz


class CalendarPopup:
    BG       = "#202020"
    BG_HOVER = "#2D2D2D"
    FG       = "#FFFFFF"
    FG_DIM   = "#888888"
    ACCENT   = "#0078D4"
    BORDER   = "#404040"

    WEEKDAYS_ZH = ["一", "二", "三", "四", "五", "六", "日"]
    WEEKDAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    MONTHS_EN = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    _instance = None

    # ------------------------------------------------------------------ #
    #  INIT                                                                #
    # ------------------------------------------------------------------ #

    def __init__(self, parent, tz_name, language="zh"):
        # 清除任何殘留實例
        if CalendarPopup._instance is not None:
            try:
                CalendarPopup._instance._do_destroy()
            except Exception:
                pass
            CalendarPopup._instance = None

        self.parent   = parent
        self.tz_name  = tz_name
        self.language = language
        self._update_timer  = None
        self._focus_timer   = None
        self._closed = False
        self._drag_start_x = 0
        self._drag_start_y = 0

        now = get_current_time_in_tz(tz_name)
        self.display_year  = now.year
        self.display_month = now.month

        # ── 日曆視窗（無遮罩，改用 FocusOut 偵測點擊外部）──────────────
        self.root = tk.Toplevel(parent)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.withdraw()                      # 先隱藏，定位後再顯示
        self.root.config(bg=self.BORDER, padx=1, pady=1)

        self.inner = tk.Frame(self.root, bg=self.BG, padx=14, pady=12)
        self.inner.pack(fill="both", expand=True)

        self._build_ui()
        self._render_grid()
        self._update_clock()

        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<FocusOut>", self._on_focus_out)
        self.root.attributes("-alpha", 0)  # 先透明，定位後才顯示，避免閃爍

        # ── 讓 Tkinter 完成佈局計算（視窗仍隱藏中）─────────────────────
        self.root.update()
        self._w = self.root.winfo_width()
        self._h = self.root.winfo_height()
        if self._w <= 1:
            self._w = 300
        if self._h <= 1:
            self._h = 400

        CalendarPopup._instance = self
        self.root.after(10, self._show_positioned)

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        # 標題區域（可拖動）
        tz_lbl = tk.Label(
            self.inner, text=self.tz_name,
            font=("Segoe UI", 9), bg=self.BG, fg=self.FG_DIM,
            cursor="fleur",
        )
        tz_lbl.pack(anchor="w")

        self.time_label = tk.Label(
            self.inner, font=("Segoe UI Light", 22),
            bg=self.BG, fg=self.FG, cursor="fleur",
        )
        self.time_label.pack(anchor="w", pady=(0, 2))

        self.date_label = tk.Label(
            self.inner, font=("Segoe UI", 10),
            bg=self.BG, fg=self.FG_DIM, cursor="fleur",
        )
        self.date_label.pack(anchor="w", pady=(0, 12))

        # 讓標題區域可拖動
        for w in (tz_lbl, self.time_label, self.date_label):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_motion)

        tk.Frame(self.inner, bg=self.BORDER, height=1).pack(fill="x", pady=(0, 10))

        nav = tk.Frame(self.inner, bg=self.BG)
        nav.pack(fill="x")

        for text, cmd, side in [("‹", self._prev_month, "left"),
                                  ("›", self._next_month, "right")]:
            btn = tk.Label(nav, text=text, font=("Segoe UI", 14),
                           bg=self.BG, fg=self.FG, cursor="hand2", padx=8)
            btn.pack(side=side)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.BG_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.BG))

        self.month_label = tk.Label(
            nav, font=("Segoe UI", 11, "bold"), bg=self.BG, fg=self.FG)
        self.month_label.pack(side="left", expand=True)

        self.grid_frame = tk.Frame(self.inner, bg=self.BG)
        self.grid_frame.pack(pady=(10, 0))

    def _render_grid(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        weekdays = self.WEEKDAYS_EN if self.language == "en" else self.WEEKDAYS_ZH
        for i, d in enumerate(weekdays):
            tk.Label(self.grid_frame, text=d, bg=self.BG, fg=self.FG_DIM,
                     width=4, font=("Segoe UI", 9, "bold"),
                     ).grid(row=0, column=i, padx=1, pady=(0, 4))

        cal = calendar.monthcalendar(self.display_year, self.display_month)
        now = get_current_time_in_tz(self.tz_name)
        today = (now.year, now.month, now.day)

        for r, week in enumerate(cal, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    cell = tk.Label(self.grid_frame, text="", bg=self.BG,
                                    width=4, font=("Segoe UI", 10))
                else:
                    is_today = (self.display_year, self.display_month, day) == today
                    cell = tk.Label(
                        self.grid_frame, text=str(day),
                        bg=self.ACCENT if is_today else self.BG,
                        fg=self.FG,
                        width=4, padx=2, pady=4,
                        font=("Segoe UI", 10, "bold" if is_today else "normal"),
                    )
                cell.grid(row=r, column=c, padx=1, pady=1)

        if self.language == "en":
            self.month_label.config(
                text=f"{self.MONTHS_EN[self.display_month - 1]} {self.display_year}")
        else:
            self.month_label.config(
                text=f"{self.display_year} 年 {self.display_month} 月")

    # ------------------------------------------------------------------ #
    #  CLOCK                                                               #
    # ------------------------------------------------------------------ #

    def _update_clock(self):
        if self._closed:
            return
        try:
            now = get_current_time_in_tz(self.tz_name)
            if self.language == "en":
                self.time_label.config(text=now.strftime("%I:%M:%S %p"))
                self.date_label.config(text=now.strftime("%Y/%m/%d  %A"))
            else:
                self.time_label.config(text=now.strftime("%H:%M:%S"))
                wd = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
                self.date_label.config(
                    text=f"{now.year}/{now.month:02d}/{now.day:02d}  星期{wd}")
        except Exception:
            pass
        self._update_timer = self.root.after(1000, self._update_clock)

    # ------------------------------------------------------------------ #
    #  NAVIGATION                                                          #
    # ------------------------------------------------------------------ #

    def _prev_month(self):
        if self.display_month == 1:
            self.display_month, self.display_year = 12, self.display_year - 1
        else:
            self.display_month -= 1
        self._render_grid()

    def _next_month(self):
        if self.display_month == 12:
            self.display_month, self.display_year = 1, self.display_year + 1
        else:
            self.display_month += 1
        self._render_grid()

    # ------------------------------------------------------------------ #
    #  POSITION                                                            #
    # ------------------------------------------------------------------ #

    def _calc_position(self):
        try:
            tray = win32gui.FindWindow("Shell_TrayWnd", None)
            if tray:
                tx, ty, tx2, ty2 = win32gui.GetWindowRect(tray)
                taskbar_top  = ty
                screen_right = tx2
            else:
                raise RuntimeError("no tray")
        except Exception:
            screen_right = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            taskbar_top  = win32api.GetSystemMetrics(win32con.SM_CYSCREEN) - 40

        x = max(screen_right - self._w - 8, 0)
        y = max(taskbar_top  - self._h - 8, 0)
        return x, y

    def _show_positioned(self):
        """顯示 popup：先透明定位，再恢復不透明，消除左上角閃爍。"""
        if self._closed:
            return
        try:
            x, y = self._calc_position()

            # 透明狀態下 deiconify，使用者看不到它在 (0,0) 的瞬間
            self.root.deiconify()
            self.root.update()

            # 移到正確位置
            self.root.geometry(f"+{x}+{y}")
            self.root.update_idletasks()

            # 恢復不透明（現在才讓使用者看到）
            self.root.attributes("-alpha", 1)

            print(f"[popup] shown at ({x},{y})  size={self._w}x{self._h}")
            self.root.after(50, self._grab_focus)
        except Exception as e:
            print(f"[popup] _show_positioned error: {e}")
            try:
                self.root.attributes("-alpha", 1)
                self.root.deiconify()
            except Exception:
                pass

    def _grab_focus(self):
        if self._closed:
            return
        try:
            self.root.focus_force()
            self.root.lift()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  DRAG                                                                #
    # ------------------------------------------------------------------ #

    def _drag_start(self, event):
        """記錄拖動起點（滑鼠相對於視窗左上角的偏移）。"""
        self._drag_start_x = event.x_root - self.root.winfo_x()
        self._drag_start_y = event.y_root - self.root.winfo_y()

    def _drag_motion(self, event):
        """拖動中，即時更新視窗位置。"""
        if self._closed:
            return
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------ #
    #  FOCUS OUT → 點擊外部關閉                                           #
    # ------------------------------------------------------------------ #

    def _on_focus_out(self, event):
        if self._closed:
            return
        # 200ms 延遲：防止點擊視窗內子元件（nav 按鈕等）時誤觸
        if self._focus_timer:
            try:
                self.root.after_cancel(self._focus_timer)
            except Exception:
                pass
        self._focus_timer = self.root.after(200, self._check_focus)

    def _check_focus(self):
        if self._closed:
            return
        try:
            focused = self.root.focus_get()
            # 若焦點仍在 popup 視窗或其子元件內，不關閉
            if focused is not None:
                w = str(focused)
                r = str(self.root)
                if w == r or w.startswith(r + "."):
                    return
        except Exception:
            pass
        self.close()

    # ------------------------------------------------------------------ #
    #  CLOSE                                                               #
    # ------------------------------------------------------------------ #

    def close(self):
        if self._closed:
            return
        self._closed = True
        if CalendarPopup._instance is self:
            CalendarPopup._instance = None
        self._do_destroy()

    def _do_destroy(self):
        for timer in [self._update_timer, self._focus_timer]:
            if timer is not None:
                try:
                    self.root.after_cancel(timer)
                except Exception:
                    pass
        try:
            self.root.destroy()
        except Exception:
            pass
