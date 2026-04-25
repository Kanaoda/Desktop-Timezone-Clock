import json
import os
import copy

DEFAULT_CLOCK_CONFIG = {
    "target_timezone": "Asia/Hong_Kong",
    "font_family": "Microsoft JhengHei UI",
    "font_size": 9,
    "font_color": "system",
    "bg_color": "system",
    "show_date": True,
    "time_format": "%p %I:%M",
    "date_format": "%Y/%m/%d",
    "position": "overlay_taskbar" # overlay_taskbar or custom
}

DEFAULT_CONFIG = {
    "clocks": [DEFAULT_CLOCK_CONFIG],
    "autostart": False,
    "language": "zh",
    "version": "1.0.0"
}

CONFIG_FILE = "config.json"

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
