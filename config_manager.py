import json
import os
import copy
import sys

DEFAULT_CLOCK_CONFIG = {
    "target_timezone": "Asia/Hong_Kong",
    "font_family": "Microsoft JhengHei UI",
    "font_size": 9,
    "font_color": "system",
    "bg_color": "system",
    "show_date": True,
    "time_format": "%#I:%M %p",
    "date_format": "%#d/%#m/%Y",
    "position": "overlay_taskbar" # overlay_taskbar or custom
}

DEFAULT_CONFIG = {
    "clocks": [DEFAULT_CLOCK_CONFIG],
    "autostart": False,
    "language": "zh",
    "version": "1.0.1"
}

def get_app_base_path():
    """取得應用程式根目錄，相容於腳本執行與 PyInstaller 打包後的 EXE"""
    if getattr(sys, 'frozen', False):
        # 如果是打包後的 EXE
        return os.path.dirname(sys.executable)
    else:
        # 如果是腳本執行
        return os.path.dirname(os.path.abspath(__file__))

def get_config_file_path():
    """取得設定檔的絕對路徑。優先使用 %APPDATA%（解決安裝在 Program Files 時的無寫入權限問題），並自動從舊路徑遷移。"""
    app_dir_config = os.path.join(get_app_base_path(), "config.json")
    appdata = os.environ.get("APPDATA")
    if appdata:
        config_dir = os.path.join(appdata, "DesktopTimezoneClock")
        try:
            os.makedirs(config_dir, exist_ok=True)
            appdata_config = os.path.join(config_dir, "config.json")
            # 自動遷移：如果 APPDATA 內沒有設定檔，但應用程式根目錄下有舊設定檔，則將其複製過去
            if not os.path.exists(appdata_config) and os.path.exists(app_dir_config):
                try:
                    import shutil
                    shutil.copy2(app_dir_config, appdata_config)
                    print(f"[config] Migrated config from {app_dir_config} to {appdata_config}")
                except Exception as e:
                    print(f"[config] Migration failed: {e}")
            return appdata_config
        except Exception:
            pass
    return app_dir_config

# 鎖定設定檔絕對路徑，防範開機自啟動時 CWD 偏移
CONFIG_FILE = get_config_file_path()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        initial = copy.deepcopy(DEFAULT_CONFIG)
        save_config(initial)
        return initial
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 確保所有預設鍵都存在
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = copy.deepcopy(value)

            # 確保 clocks 內每個時鐘都補齊預設鍵
            normalized_clocks = []
            for clock_cfg in config.get("clocks", []):
                merged = copy.deepcopy(DEFAULT_CLOCK_CONFIG)
                if isinstance(clock_cfg, dict):
                    merged.update(clock_cfg)

                # 兼容舊版本：舊預設 white/black 視為「跟隨系統」
                if (
                    isinstance(clock_cfg, dict)
                    and "font_color" in clock_cfg
                    and "bg_color" in clock_cfg
                    and clock_cfg.get("font_color") == "white"
                    and str(clock_cfg.get("bg_color")).lower() in ("black", "#000000")
                ):
                    merged["font_color"] = "system"
                    merged["bg_color"] = "system"

                normalized_clocks.append(merged)
            if not normalized_clocks:
                normalized_clocks = [copy.deepcopy(DEFAULT_CLOCK_CONFIG)]
            config["clocks"] = normalized_clocks
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return copy.deepcopy(DEFAULT_CONFIG)

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
