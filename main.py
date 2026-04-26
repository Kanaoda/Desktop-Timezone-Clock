import copy
import queue
import threading
import time
import pystray
from pystray import _win32 as pystray_win32
from pystray._util import win32 as tray_win32
import win32con
from PIL import Image, ImageDraw
import sys
import ctypes

try:
    # Set DPI awareness (Per Monitor V2 is preferred if available)
    # 2 = PROCESS_PER_MONITOR_DPI_AWARE
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from config_manager import load_config, save_config
from overlay_window import ClockOverlay
from settings_window import SettingsWindow

from i18n import I18n
from utils import is_already_running, is_autostart_enabled


class DesktopTrayIcon(pystray_win32.Icon):
    """自訂 Windows 托盤事件：單擊 / 雙擊分流。"""
    _DBLCLICK_SEC = 0.35
    _WM_LBUTTONDBLCLK = getattr(win32con, "WM_LBUTTONDBLCLK", 0x0203)

    def __init__(self, *args, on_single_left_click=None, on_double_left_click=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_single_left_click = on_single_left_click
        self._on_double_left_click = on_double_left_click
        self._single_click_timer = None
        self._last_left_up_ts = 0.0

    def _cancel_single_timer(self):
        if self._single_click_timer is not None:
            self._single_click_timer.cancel()
            self._single_click_timer = None

    def _fire_single_click(self):
        self._single_click_timer = None
        if callable(self._on_single_left_click):
            self._on_single_left_click(self)
        else:
            self()

    def _fire_double_click(self):
        self._cancel_single_timer()
        if callable(self._on_double_left_click):
            self._on_double_left_click(self)

    def _on_notify(self, wparam, lparam):
        # Windows 可能送 WM_LBUTTONDBLCLK，也可能只送兩次 WM_LBUTTONUP，兩者都處理
        if lparam == self._WM_LBUTTONDBLCLK:
            self._fire_double_click()
            return
        if lparam == tray_win32.WM_LBUTTONUP:
            now = time.time()
            if now - self._last_left_up_ts <= self._DBLCLICK_SEC:
                self._last_left_up_ts = 0.0
                self._fire_double_click()
                return
            self._last_left_up_ts = now
            self._cancel_single_timer()
            self._single_click_timer = threading.Timer(self._DBLCLICK_SEC, self._fire_single_click)
            self._single_click_timer.daemon = True
            self._single_click_timer.start()
            return
        return super()._on_notify(wparam, lparam)


class DesktopClockApp:
    def __init__(self):
        if is_already_running():
            sys.exit(0)

        self.config = load_config()
        
        # 同步開機啟動狀態與註冊表 (解決安裝時勾選自動啟動但設定頁未同步的問題)
        try:
            from utils import is_autostart_enabled
            registry_enabled = is_autostart_enabled()
            if self.config.get("autostart") != registry_enabled:
                self.config["autostart"] = registry_enabled
                save_config(self.config)
        except Exception:
            pass
        self.overlays = []
        self.tray_icon = None
        self._settings_win = None
        self._ui_actions = queue.Queue()
        self.i18n = I18n(self.config.get("language", "zh"))

    def _post_ui_action(self, fn):
        self._ui_actions.put(fn)

    def _drain_ui_actions(self):
        if not self.overlays:
            return
        root = self.overlays[0].root
        try:
            while True:
                fn = self._ui_actions.get_nowait()
                try:
                    fn()
                except Exception as e:
                    pass
        except queue.Empty:
            pass
        root.after(50, self._drain_ui_actions)

    def create_tray_image(self):
        width, height = 64, 64
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        dc = ImageDraw.Draw(image)
        dc.ellipse([8, 8, 56, 56], outline=(0, 0, 0), width=4)
        dc.line([32, 32, 32, 16], fill=(0, 0, 0), width=4)
        dc.line([32, 32, 48, 32], fill=(0, 0, 0), width=4)
        return image

    # ------------------------------------------------------------------ #
    #  SETTINGS WINDOW                                                     #
    # ------------------------------------------------------------------ #

    def on_settings(self, icon, item):
        if self.overlays:
            self.overlays[0].root.after(0, self._open_settings_window)

    def _open_settings_window(self):
        # Prevent duplicate windows
        if self._settings_win is not None:
            try:
                if self._settings_win.root.winfo_exists():
                    self._settings_win.root.lift()
                    self._settings_win.root.focus_force()
                    return
            except Exception:
                pass
            self._settings_win = None

        parent = self.overlays[0].root if self.overlays else None

        def on_settings_closed():
            self._restore_config()
            self._settings_win = None

        self._settings_win = SettingsWindow(
            self.config,
            on_save_callback=self._on_settings_saved,
            on_preview_callback=self._preview_config,
            on_close_callback=on_settings_closed,
            parent=parent,
        )
        self._settings_win.run()

    def _on_settings_saved(self, new_config):
        self._settings_win = None
        self.update_config(new_config)

    def update_config(self, new_config):
        self.config = copy.deepcopy(new_config)
        self.i18n = I18n(self.config.get("language", "zh"))
        save_config(self.config)
        self._apply_config_to_overlays(self.config)

    def _preview_config(self, temp_config):
        self._apply_config_to_overlays(temp_config)

    def _restore_config(self):
        self._apply_config_to_overlays(self.config)

    def _apply_config_to_overlays(self, cfg):
        for i, overlay in enumerate(self.overlays):
            if i < len(cfg["clocks"]):
                clock_cfg = cfg["clocks"][i]
                overlay.root.after(
                    0, lambda o=overlay, c=clock_cfg, g=cfg: (
                        setattr(o, "global_config", g),
                        o.update_config(c)
                    ))

    # ------------------------------------------------------------------ #
    #  TRAY                                                                #
    # ------------------------------------------------------------------ #

    def on_exit(self, icon, item=None):
        icon.stop()
        for overlay in self.overlays:
            overlay.root.after(0, overlay.close)
        import os
        os._exit(0)

    def _on_tray_single_click(self, icon):
        if self.overlays:
            self._post_ui_action(lambda: self.overlays[0].toggle_calendar())

    def _on_tray_double_click(self, icon):
        if self.overlays:
            self._post_ui_action(self._open_settings_window)

    def run_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem(self.i18n.get("settings"),      self.on_settings),
            pystray.MenuItem(self.i18n.get("exit"),          self.on_exit),
        )
        self.tray_icon = DesktopTrayIcon(
            "DesktopClock",
            self.create_tray_image(),
            self.i18n.get("app_title"),
            menu,
            on_single_left_click=self._on_tray_single_click,
            on_double_left_click=self._on_tray_double_click,
        )
        self.tray_icon.run()

    # ------------------------------------------------------------------ #
    #  ENTRY POINT                                                         #
    # ------------------------------------------------------------------ #

    def run(self):
        tray_thread = threading.Thread(target=self.run_tray, daemon=True)
        tray_thread.start()

        for clock_cfg in self.config["clocks"]:
            overlay = ClockOverlay(
                clock_cfg,
                self.config,
                on_open_settings=lambda: self._open_settings_window(),
            )
            self.overlays.append(overlay)

        if self.overlays:
            self.overlays[0].root.after(50, self._drain_ui_actions)
            self.overlays[0].run()


if __name__ == "__main__":
    app = DesktopClockApp()
    app.run()
