import json
from datetime import datetime
from shapely.geometry import Point
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

# 這裡就是你的 line_push.py 檔案
from line_push2 import send_line_alert

# =========================================
# MarineTraffic API URL 列表
# =========================================
urls = [
    # (你的 URL 列表... 保持不變)
    # 北部/東北
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:854/Y:440/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:855/Y:440/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:854/Y:441/station:0",
    # 中部/海峽中段
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:426/Y:221/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:427/Y:221/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:428/Y:221/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:429/Y:221/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:426/Y:222/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:427/Y:222/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:428/Y:222/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:429/Y:222/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:426/Y:223/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:427/Y:223/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:428/Y:223/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:429/Y:223/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:426/Y:224/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:427/Y:224/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:428/Y:224/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:429/Y:224/station:0",
    # 西南部
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:852/Y:443/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:851/Y:442/station:0",
    # 金門/馬祖與靠陸地區
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:108/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:108/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:110/station:0",
    # 更大範圍外海
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:105/Y:54/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:106/Y:54/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:107/Y:54/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:105/Y:55/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:106/Y:55/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:107/Y:55/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:105/Y:56/station:0",
    # "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:106/Y:56/station:0",
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
# 主函式：抓取 + 儲存 + 分類
# =========================================


def fetch_data(force_push=False):
    timestamp = datetime.utcnow()
    print(f"[{timestamp}] 🚢 Fetching AIS data...")

    # *** 新增 ***
    # 建立兩個列表，用來收集要推播的船隻
    ships_inside_list = []
    ships_outside_list = []
    # ************

    # === 每次重抓前，清空 data_test.db ===
    try:
        TestSession.query(TestShipAIS).delete()
        TestSession.commit()
        print("🧹 Cleared data_test.db")
    except Exception as e:
        TestSession.rollback()
        log_failed_record({}, f"Clear data_test failed: {e}")

    scraper = cloudscraper.create_scraper()

    for url in urls:
        try:
            response = scraper.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            log_failed_record({"url": url}, f"Fetch error: {e}")
            continue

        key = url.replace("https://www.marinetraffic.com/getData/",
                          "").replace("/", "_").replace(":", "_")
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
                "timestamp": timestamp,  # 這裡的 timestamp 是 datetime 物件
                "source": key,
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

            # === 所有船隻歷史資料 ===
            db.session.add(ShipAIS(**record_kwargs))
            # === 最新資料（覆蓋寫入）===
            upsert_ship(TestSession, TestShipAIS, ship_id, record_kwargs)

            # === 若為中國籍船舶 (flag == "CN") ===
            if record_kwargs.get("flag") == "CN":
                ChinaBoatSession.add(ChinaBoatAIS(**record_kwargs))

            # === 若為海警船 ===
            if shipname.startswith("CHINACOASTGUARD"):
                BoatSession.add(BoatShipAIS(**record_kwargs))
                upsert_ship(CCGSession, CCGShipAIS, ship_id, record_kwargs)

                p = Point(lon, lat)
                in_12nm = p.within(TAIWAN_12NM_POLYGON)
                in_24nm = p.within(TAIWAN_24NM_POLYGON)

                # *** 修改：將 timestamp 轉為字串 ***
                # line_push 函式需要的是字串
                time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                # ✅ 12nm 內
                if in_12nm:
                    BoatCheck12Session.add(BoatCheck12AIS(**record_kwargs))
                    upsert_ship(CCGCheck12Session, CCGCheck12ShipAIS,
                                ship_id, record_kwargs)
                    print(f"🚨 {shipname} 進入 12nm")

                    # *** 新增 ***
                    # 加入到 12 海浬推播列表
                    ships_inside_list.append({
                        'shipname': shipname,
                        'lat': lat,
                        'lon': lon,
                        'course': record_kwargs['course'],
                        'speed': record_kwargs['speed'],
                        'timestamp': time_str
                    })

                # ✅ 12–24nm 間（在 24nm 內但不在 12nm 內）
                elif in_24nm and not in_12nm:
                    BoatCheck24Session.add(BoatCheck24AIS(**record_kwargs))
                    upsert_ship(CCGCheck24Session, CCGCheck24ShipAIS,
                                ship_id, record_kwargs)
                    print(f"⚠️ {shipname} 在 12–24nm 之間")

                    # *** 新增 ***
                    # 計算到 12nm 邊界的距離 (line_push 函式需要這個)
                    p_12nm, _ = nearest_points(TAIWAN_12NM_POLYGON, p)
                    distance_km = haversine(p.y, p.x, p_12nm.y, p_12nm.x)

                    # 加入到 12-24 海浬推播列表
                    ships_outside_list.append({
                        'shipname': shipname,
                        'lat': lat,
                        'lon': lon,
                        'course': record_kwargs['course'],
                        'speed': record_kwargs['speed'],
                        'timestamp': time_str,
                        'distance_km': distance_km  # 推播函式需要的額外欄位
                    })

    # === *** 新增：觸發 LINE 推播 *** ===
    # 在所有 URL 都爬完後，整理一次並發送
    print(
        f"📊 抓取完成. 12nm 內: {len(ships_inside_list)} 艘, 12-24nm: {len(ships_outside_list)} 艘")

    # 判斷是否要推播：
    # 1. 有找到任何船 (inside 或 outside)
    # 2. 或是 app.py 啟動時傳來的 force_push=True (這時就算沒船也會報平安)
    if ships_inside_list or ships_outside_list or force_push:
        print("🚀 正在觸發 LINE 推播...")
        try:
            send_line_alert(
                ships_inside_list,
                ships_outside_list,
                force=force_push,
                # 如果是 force_push (通常是剛啟動)，即使列表為空也發送"報平安"訊息
                send_empty_summary=force_push
            )
        except Exception as e:
            print(f"❌ LINE 推播失敗: {e}")
            log_failed_record({"ships_inside": len(
                ships_inside_list)}, f"LINE push failed in fetcher: {e}")
    else:
        print("ℹ️ 無海警船可通報，且非 force_push，本次跳過推播。")
    # === *** 推播區塊結束 *** ===

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
        TestSession.rollback()
        BoatSession.rollback()
        BoatCheck12Session.rollback()
        BoatCheck24Session.rollback()
        CCGSession.rollback()
        CCGCheck12Session.rollback()
        CCGCheck24Session.rollback()
        ChinaBoatSession.rollback()
        log_failed_record({"url": "N/A - DB Commit"}, f"DB commit error: {e}")
