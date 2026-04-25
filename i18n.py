LANGUAGES = {
    "zh": {
        # ── 通用 ──────────────────────────────────────────────────────────────
        "app_title":         "桌面多時區時鐘",
        "app_subtitle":      "桌面時區時鐘",
        "settings":          "設定 (Settings)",
        "exit":              "退出 (Exit)",
        "save_apply":        "保存並套用",
        "cancel":            "取消",
        "check_update":      "檢查更新",

        # ── 設定視窗章節 ──────────────────────────────────────────────────────
        "clock_settings":    "時鐘設定",
        "preview":           "預覽",
        "timezone_section":  "時區",
        "appearance":        "外觀",
        "system_section":    "系統",
        "support_section":   "支持作者",
        "sponsor_github":    "GitHub Sponsor",
        "sponsor_coffee":    "Buy Me a Coffee",

        # ── 行標籤 ────────────────────────────────────────────────────────────
        "language_label":    "語言",
        "font_size_label":   "字體大小",
        "show_date_label":   "顯示日期",
        "font_color_row":    "文字顏色",
        "bg_color_row":      "背景顏色",
        "autostart_label":   "開機自動啟動",

        # ── 顏色模式 ──────────────────────────────────────────────────────────
        "color_auto":        "自動",
        "color_custom":      "自訂",
        "color_system":      "跟隨系統",

        # ── 時區選擇器 ────────────────────────────────────────────────────────
        "search_tz":         "搜尋時區…",

        # ── 時間標籤 ──────────────────────────────────────────────────────────
        "local_time":        "本地時間:",

        # ── 顏色對話框標題 ────────────────────────────────────────────────────
        "choose_font_color": "選擇文字顏色",
        "choose_bg_color":   "選擇背景顏色",

        # ── 舊版相容 ──────────────────────────────────────────────────────────
        "target_tz":         "選擇目標時區:",
        "font_size":         "字體大小:",
        "show_date":         "顯示日期",
        "autostart":         "隨開機自動啟動",
        "add_clock":         "新增時鐘",
        "delete_clock":      "刪除時鐘",
        "language":          "語言:",
        "time_preview":      "時間預覽",
        "font_color_label":  "字色:",
        "bg_color_label":    "背景:",
    },
    "en": {
        # ── General ───────────────────────────────────────────────────────────
        "app_title":         "Desktop Timezone Clock",
        "app_subtitle":      "Desktop Timezone Clock",
        "settings":          "Settings",
        "exit":              "Exit",
        "save_apply":        "Save & Apply",
        "cancel":            "Cancel",
        "check_update":      "Check for Updates",

        # ── Settings window sections ──────────────────────────────────────────
        "clock_settings":    "Clock Settings",
        "preview":           "Preview",
        "timezone_section":  "Timezone",
        "appearance":        "Appearance",
        "system_section":    "System",
        "support_section":   "Support",
        "sponsor_github":    "GitHub Sponsor",
        "sponsor_coffee":    "Buy Me a Coffee",

        # ── Row labels ────────────────────────────────────────────────────────
        "language_label":    "Language",
        "font_size_label":   "Font Size",
        "show_date_label":   "Show Date",
        "font_color_row":    "Font Color",
        "bg_color_row":      "Background Color",
        "autostart_label":   "Launch on Startup",

        # ── Color mode ────────────────────────────────────────────────────────
        "color_auto":        "Auto",
        "color_custom":      "Custom",
        "color_system":      "System",

        # ── Timezone picker ───────────────────────────────────────────────────
        "search_tz":         "Search timezone…",

        # ── Time labels ───────────────────────────────────────────────────────
        "local_time":        "Local:",

        # ── Color dialog titles ───────────────────────────────────────────────
        "choose_font_color": "Font Color",
        "choose_bg_color":   "Background Color",

        # ── Legacy compatibility ──────────────────────────────────────────────
        "target_tz":         "Target Timezone:",
        "font_size":         "Font Size:",
        "show_date":         "Show Date",
        "autostart":         "Auto-start on Boot",
        "add_clock":         "Add Clock",
        "delete_clock":      "Delete Clock",
        "language":          "Language:",
        "time_preview":      "Time Preview",
        "font_color_label":  "Font:",
        "bg_color_label":    "Bg:",
    }
}


class I18n:
    def __init__(self, lang_code="zh"):
        self.lang_code    = lang_code if lang_code in LANGUAGES else "en"
        self.translations = LANGUAGES[self.lang_code]

    def get(self, key: str) -> str:
        return self.translations.get(key, key)
