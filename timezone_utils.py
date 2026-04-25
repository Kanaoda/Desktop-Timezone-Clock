from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # 備退方案 (如果 Python 版本較低，但這裡應該是 3.12)
    from backports.zoneinfo import ZoneInfo
import zoneinfo

_TZ_PART_ZH = {
    "Africa": "非洲",
    "America": "美洲",
    "Antarctica": "南極洲",
    "Arctic": "北極",
    "Asia": "亞洲",
    "Atlantic": "大西洋",
    "Australia": "澳洲",
    "Europe": "歐洲",
    "Indian": "印度洋",
    "Pacific": "太平洋",
    "UTC": "世界協調時間",
    "GMT": "格林威治",
    "Hong": "香港",
    "Kong": "香港",
    "Taipei": "台北",
    "Tokyo": "東京",
    "Seoul": "首爾",
    "Shanghai": "上海",
    "Singapore": "新加坡",
    "Macau": "澳門",
    "Bangkok": "曼谷",
    "Manila": "馬尼拉",
    "London": "倫敦",
    "Paris": "巴黎",
    "Berlin": "柏林",
    "Rome": "羅馬",
    "Madrid": "馬德里",
    "Lisbon": "里斯本",
    "Moscow": "莫斯科",
    "Dubai": "杜拜",
    "Istanbul": "伊斯坦堡",
    "Kolkata": "加爾各答",
    "New": "新",
    "York": "約克",
    "Los": "洛杉磯",
    "Angeles": "安吉利斯",
    "Chicago": "芝加哥",
    "Denver": "丹佛",
    "Phoenix": "鳳凰城",
    "Toronto": "多倫多",
    "Vancouver": "溫哥華",
    "Sao": "聖保羅",
    "Paulo": "保羅",
    "Mexico": "墨西哥",
    "City": "市",
}


def _translate_timezone_name_zh(tz_name: str) -> str:
    parts = tz_name.split("/")
    zh_parts = []
    for part in parts:
        tokens = part.split("_")
        zh_tokens = [_TZ_PART_ZH.get(token, token) for token in tokens]
        zh_parts.append("_".join(zh_tokens))
    return "/".join(zh_parts)


def get_current_time_in_tz(tz_name):
    try:
        now = datetime.now(timezone.utc)
        target_tz = ZoneInfo(tz_name)
        return now.astimezone(target_tz)
    except Exception as e:
        print(f"Timezone error: {e}")
        return datetime.now()

def get_all_timezones_with_offset(lang_code="zh"):
    # 獲取所有時區並計算目前的偏移量
    now = datetime.now(timezone.utc)
    tz_list = []
    for tz_name in zoneinfo.available_timezones():
        try:
            tz = ZoneInfo(tz_name)
            offset = now.astimezone(tz).utcoffset()
            offset_hours = offset.total_seconds() / 3600
            offset_str = f"GMT{'+' if offset_hours >= 0 else ''}{int(offset_hours)}:{'30' if offset_hours % 1 != 0 else '00'}"
            if lang_code == "zh":
                zh_name = _translate_timezone_name_zh(tz_name)
                display_name = f"{zh_name} ({tz_name})" if zh_name != tz_name else tz_name
            else:
                display_name = tz_name

            tz_list.append({
                "name": tz_name,
                "offset": offset_hours,
                "display": f"({offset_str}) {display_name}"
            })
        except Exception:
            continue
    
    # 根據偏移量排序
    tz_list.sort(key=lambda x: x["offset"])
    return tz_list
