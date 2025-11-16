import json
from datetime import datetime
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points
import cloudscraper
from sqlalchemy import func

from config import TAIWAN_12NM_POLYGON, TAIWAN_24NM_POLYGON
from utils import safe_float, haversine, log_failed_record
from models import (
    db, ShipAIS,
    TestShipAIS, BoatShipAIS,
    BoatCheck12AIS, BoatCheck24AIS,
    CCGShipAIS, CCGCheck12ShipAIS, CCGCheck24ShipAIS,
    TestSession, BoatSession, BoatCheck12Session, BoatCheck24Session,
    CCGSession, CCGCheck12Session, CCGCheck24Session, ChinaBoatSession, ChinaBoatAIS
)
from line_push2 import send_line_alert
from alarm_loader import load_alarm_zones  # 🔹 新增，用來載入警戒範圍

# =========================================
# MarineTraffic API URL 列表
# =========================================
urls = [
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:426/Y:221/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:427/Y:221/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:105/Y:54/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:106/Y:54/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:107/Y:54/station:0",
]

# 建立爬蟲 client
scraper = cloudscraper.create_scraper()


# =========================================
# 共用函式：有就更新，沒有就新增
# =========================================
def upsert_ship(session, Model, ship_id, values_dict):
    record = session.query(Model).filter_by(ship_id=ship_id).first()
    if record:
        for key, val in values_dict.items():
            setattr(record, key, val)
    else:
        session.add(Model(**values_dict))


# =========================================
# 主函式：抓取 + 儲存 + 分類 + 警戒檢查
# =========================================
def fetch_data(force_push=False):
    timestamp = datetime.utcnow()
    print(f"[{timestamp}] 🚢 Fetching AIS data...")

    ships_inside_list = []
    ships_outside_list = []
    scraper = cloudscraper.create_scraper()

    # === 清空 test db ===
    try:
        TestSession.query(TestShipAIS).delete()
        TestSession.commit()
        print("🧹 Cleared data_test.db")
    except Exception as e:
        TestSession.rollback()
        log_failed_record({}, f"Clear data_test failed: {e}")

    for url in urls:
        try:
            response = scraper.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            log_failed_record({"url": url}, f"Fetch error: {e}")
            continue

        rows = data.get("data", {}).get("rows", [])
        if not rows:
            continue

        for row in rows:
            lat = safe_float(row.get("LAT"))
            lon = safe_float(row.get("LON"))
            shipname = row.get("SHIPNAME") or ""
            ship_id = row.get("SHIP_ID")

            if not (lat and lon and ship_id):
                continue

            record_kwargs = {
                "timestamp": timestamp,
                "source": url,
                "ship_id": ship_id,
                "shipname": shipname,
                "lat": lat,
                "lon": lon,
                "speed": safe_float(row.get("SPEED")) / 10,
                "course": safe_float(row.get("COURSE")),
                "heading": safe_float(row.get("HEADING")),
                "rot": safe_float(row.get("ROT")),
                "destination": row.get("DESTINATION"),
                "dwt": row.get("DWT"),
                "flag": row.get("FLAG"),
                "shiptype": row.get("SHIPTYPE"),
                "gt_shiptype": row.get("GT_SHIPTYPE"),
                "length": row.get("LENGTH"),
                "width": row.get("WIDTH"),
            }

            # === 更新資料庫 ===
            db.session.add(ShipAIS(**record_kwargs))
            upsert_ship(TestSession, TestShipAIS, ship_id, record_kwargs)

            # === 中國籍船舶 ===
            if record_kwargs.get("flag") == "CN":
                ChinaBoatSession.add(ChinaBoatAIS(**record_kwargs))

            # =========================================
            # 檢查是否進入「自訂警戒區」
            # 僅針對：
            #   1️⃣ 中國籍船 (flag == "CN")
            #   2️⃣ 中國海警船 (名稱以 CHINACOASTGUARD 開頭)
            # =========================================
            try:
                # 判斷是否為目標船種
                is_cn_flag = (record_kwargs.get("flag") == "CN")
                is_ccg_ship = shipname.upper().startswith("CHINACOASTGUARD")

                if is_cn_flag or is_ccg_ship:
                    # 載入所有警戒區
                    from alarm_loader import load_alarm_zones
                    from shapely.geometry import Point, Polygon

                    zones = load_alarm_zones()
                    p = Point(lon, lat)

                    # 檢查是否進入任一警戒區
                    for z in zones:
                        polygon = Polygon(z["coords"])
                        if polygon.contains(p):
                            # 進入警戒區
                            msg = (
                                f"🚨【警戒區入侵】\n"
                                f"船舶：{shipname}\n"
                                f"區域：{z['name']}\n"
                                f"位置：({lat:.4f}, {lon:.4f})\n"
                                f"時間：{timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                            print(msg)
                            # 呼叫 LINE 推播
                            send_line_alert([], [], force=True, custom_message=msg)
            except Exception as e:
                print(f"⚠️ 警戒區判斷錯誤: {e}")


            # === 檢查是否進入自訂警戒區 ===
            try:
                zones = load_alarm_zones()
                p = Point(lon, lat)
                for z in zones:
                    polygon = Polygon(z["coords"])
                    if polygon.contains(p):
                        msg = (
                            f"🚨【警戒區入侵】\n"
                            f"船舶：{shipname}\n"
                            f"區域：{z['name']}\n"
                            f"位置：({lat:.4f}, {lon:.4f})\n"
                            f"時間：{timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        print(f"⚠️ {shipname} 進入警戒區 {z['name']}")
                        send_line_alert([], [], force=True, custom_message=msg)
            except Exception as e:
                print(f"⚠️ 檢查警戒範圍失敗: {e}")

            # === 海警船特例 ===
            if shipname.startswith("CHINACOASTGUARD"):
                BoatSession.add(BoatShipAIS(**record_kwargs))
                upsert_ship(CCGSession, CCGShipAIS, ship_id, record_kwargs)

                p = Point(lon, lat)
                in_12nm = p.within(TAIWAN_12NM_POLYGON)
                in_24nm = p.within(TAIWAN_24NM_POLYGON)
                time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                if in_12nm:
                    BoatCheck12Session.add(BoatCheck12AIS(**record_kwargs))
                    upsert_ship(CCGCheck12Session, CCGCheck12ShipAIS, ship_id, record_kwargs)
                    ships_inside_list.append({
                        'shipname': shipname, 'lat': lat, 'lon': lon,
                        'course': record_kwargs['course'], 'speed': record_kwargs['speed'],
                        'timestamp': time_str
                    })

                elif in_24nm and not in_12nm:
                    BoatCheck24Session.add(BoatCheck24AIS(**record_kwargs))
                    upsert_ship(CCGCheck24Session, CCGCheck24ShipAIS, ship_id, record_kwargs)
                    p_12nm, _ = nearest_points(TAIWAN_12NM_POLYGON, p)
                    distance_km = haversine(p.y, p.x, p_12nm.y, p_12nm.x)
                    ships_outside_list.append({
                        'shipname': shipname, 'lat': lat, 'lon': lon,
                        'course': record_kwargs['course'], 'speed': record_kwargs['speed'],
                        'timestamp': time_str, 'distance_km': distance_km
                    })

    # === LINE 推播 ===
    if ships_inside_list or ships_outside_list or force_push:
        print("🚀 正在觸發 LINE 推播...")
        try:
            send_line_alert(ships_inside_list, ships_outside_list, force=force_push, send_empty_summary=force_push)
        except Exception as e:
            print(f"❌ LINE 推播失敗: {e}")
            log_failed_record({}, f"LINE push failed in fetcher: {e}")
    else:
        print("ℹ️ 無海警船可通報，跳過推播。")

    # === 提交各 DB ===
    try:
        db.session.commit()
        TestSession.commit()
        BoatSession.commit()
        BoatCheck12Session.commit()
        BoatCheck24Session.commit()
        CCGSession.commit()
        CCGCheck12Session.commit()
        CCGCheck24Session.commit()
        ChinaBoatSession.commit()
    except Exception as e:
        db.session.rollback()
        print(f"❌ DB commit error: {e}")
