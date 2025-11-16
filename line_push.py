import os
import json
import hashlib
from datetime import datetime, timedelta

from linebot import LineBotApi, WebhookHandler
from linebot.models import FlexSendMessage
from config import LINE_ACCESS_TOKEN, LINE_CHANNEL_SECRET, LINE_TARGET_USER_ID
from utils import (
    log_failed_record,
    describe_location_text,
    nearest_reference_point
)

from config import ENABLE_LINE_PUSH

def safe_push(user_id, message):
    if not ENABLE_LINE_PUSH:
        print("[LINE PUSH] 已停用，訊息不會發送")
        return
    if line_bot_api:
        line_bot_api.push_message(user_id, message)


# =========================================
# LINE API 初始化
# =========================================
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN) if LINE_ACCESS_TOKEN else None
handler = WebhookHandler(LINE_CHANNEL_SECRET) if LINE_CHANNEL_SECRET else None

# =========================================
# 推播防重複機制
# =========================================
_last_push_hash_enter = None   # 進入警戒區 hash
_last_push_hash_exit = None    # 離開警戒 hash
_last_push_time = None
PUSH_COOLDOWN = timedelta(minutes=8)

# =========================================
# 狀態儲存檔
# =========================================
STATE_FILE = "state_cache.json"


def load_state():
    """載入上一輪狀態"""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):
    """寫入狀態紀錄"""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[STATE] write failed: {e}")


# =========================================
# 時間轉換
# =========================================
def utc_to_taipei(ts):
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts


# =========================================
# Flex 卡片：警戒區內船隻（單艘）
# =========================================
def build_flex_card(ship):
    lat = float(ship["lat"])
    lon = float(ship["lon"])
    course = ship.get("course")
    speed = ship.get("speed")
    name = ship.get("shipname", "UNKNOWN")
    ts_local = utc_to_taipei(ship.get("timestamp", ""))
    zone = ship.get("zone", "unknown")  # 👈 從 fetcher.py 傳來

    # 根據 zone 判斷顏色與標題
    if zone == "12":
        header_color = "#B71C1C"  # 🔴 紅色
        header_text = "🚨 中國海警船闖入台灣 12 海浬內！"
    elif zone == "12-24":
        header_color = "#EF6C00"  # 🟠 橘色
        header_text = "⚠️ 中國海警船進入 12–24 海浬"
    else:
        header_color = "#1565C0"  # 🔵 預設
        header_text = "🌊 海域外船舶"

    # 以下保留原有格式
    location_text = describe_location_text(lat, lon)
    speed_text = f"{float(speed):.1f} 節" if speed is not None else "— 節"
    map_url = f"https://www.google.com/maps?q={lat},{lon}&z=8"

    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": header_color,
            "contents": [{"type": "text", "text": header_text, "weight": "bold", "color": "#FFFFFF", "wrap": True}]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"🚢 {name}", "weight": "bold", "size": "md"},
                {"type": "text", "text": f"📍 {lat:.6f}, {lon:.6f}", "size": "sm"},
                {"type": "text", "text": f"➡️ 航向 {course}° | {speed_text}", "size": "sm"},
                {"type": "text", "text": f"🕒 資料時間 {ts_local}", "size": "sm"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": f"📌 {location_text}", "size": "sm", "wrap": True}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": header_color,
                    "action": {"type": "uri", "label": "🌍 查看地圖", "uri": map_url}
                }
            ]
        }
    }



# =========================================
# Flex Carousel：進入警戒
# =========================================
def build_flex_carousel(ships):
    bubbles = [build_flex_card(s) for s in ships]
    return FlexSendMessage(
        alt_text="中國海警船動態通知",
        contents={"type": "carousel", "contents": bubbles[:12]}
    )


# =========================================
# FLEX：退出警戒區 B1 版本
# =========================================
def build_departure_flex(exited_ships):
    now = datetime.utcnow() + timedelta(hours=8)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    body_list = []
    for s in exited_ships:
        lat = float(s["lat"])
        lon = float(s["lon"])
        ref_name, dist_nm = nearest_reference_point(lat, lon)
        body_list.append(
            {"type": "text", "text": f"🚢 {s['shipname']}　📏 距{ref_name} {dist_nm:.1f} 海浬", "size": "sm", "wrap": True}
        )

    return FlexSendMessage(
        alt_text="中國海警船離開 24 海浬",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#2E7D32",
                "contents": [{"type": "text", "text": "🟢【情資更新：已離開 24 海浬】", "weight": "bold", "color": "#FFFFFF"}]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "下列船隻已退出警戒範圍：", "wrap": True, "size": "sm"},
                    *body_list,
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "📌 威脅暫時解除，但仍需監控可能折返", "size": "sm", "wrap": True},
                    {"type": "text", "text": f"🕒 {now_str} (UTC+8)", "size": "xs", "color": "#777777"}
                ]
            }
        }
    )


# =========================================
# 船隻離開偵測
# =========================================
def detect_exited_ships(prev_state, current_ships):
    prev_names = set(prev_state.keys())
    current_names = set(s["shipname"] for s in current_ships)
    exited_names = prev_names - current_names
    return [prev_state[name] for name in exited_names]


# =========================================
# 主推播函式
# =========================================
def send_line_alert(ships_inside, ships_outside, *, force=False, send_empty_summary=False):
    global _last_push_hash_enter, _last_push_hash_exit, _last_push_time

    if not line_bot_api or not LINE_TARGET_USER_ID:
        print("[PUSH] skipped: missing LINE credentials")
        return

    # ---- 進入區域船 (加上 zone 標記) ----
    for s in ships_inside:
        s["zone"] = "12"       # 代表 12 海浬內
    for s in ships_outside:
        s["zone"] = "12-24"    # 代表 12-24 海浬間

    entering_ships = ships_inside + ships_outside


    # ---- 狀態讀取 ----
    prev_state = load_state()
    current_state = {s["shipname"]: s for s in entering_ships}

    # ---- 偵測退出船 ----
    exited_ships = detect_exited_ships(prev_state, entering_ships)

    # ---- 推播：進入警戒 ----
    if entering_ships:
        hash_enter = hashlib.sha256(json.dumps(entering_ships, sort_keys=True).encode()).hexdigest()
        now = datetime.utcnow()

        if force or (_last_push_hash_enter != hash_enter or not _last_push_time or now - _last_push_time > PUSH_COOLDOWN):
            flex_msg = build_flex_carousel(entering_ships)
            line_bot_api.push_message(LINE_TARGET_USER_ID, flex_msg)
            _last_push_hash_enter = hash_enter
            _last_push_time = now
            print("[PUSH] sent ENTER alert")

    # ---- 推播：退出警戒 ----
    if exited_ships:
        hash_exit = hashlib.sha256(json.dumps(exited_ships, sort_keys=True).encode()).hexdigest()

        if force or (_last_push_hash_exit != hash_exit):
            flex_msg = build_departure_flex(exited_ships)
            line_bot_api.push_message(LINE_TARGET_USER_ID, flex_msg)
            _last_push_hash_exit = hash_exit
            print("[PUSH] sent EXIT alert")

    # ---- 更新狀態 ----
    save_state(current_state)

    if not entering_ships and not exited_ships:
        print("[PUSH] no activity")
