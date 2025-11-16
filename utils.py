import json
from math import radians, sin, cos, sqrt, atan2, degrees
from datetime import datetime
from config import FAILED_LOG_FILE

# =========================================
# 安全轉換 float
# =========================================
def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================
# haversine 距離公式（回傳 km）
# =========================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # 地球半徑 (km)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c  # km


# =========================================
# km -> 海浬 (nautical miles)
# 1 km = 0.539957 nm
# =========================================
def km_to_nm(km):
    return km * 0.539957


# =========================================
# 最近台灣基準點（島/港口）
# =========================================
REFERENCE_POINTS = [
    {"name": "台灣本島", "lat": 23.6978, "lon": 120.9605},
    {"name": "金門", "lat": 24.436, "lon": 118.318},
    {"name": "東碇島", "lat": 24.431, "lon": 118.392},
    {"name": "馬祖南竿", "lat": 26.157, "lon": 119.948},
    {"name": "澎湖", "lat": 23.567, "lon": 119.566},
    {"name": "基隆港", "lat": 25.152, "lon": 121.763},
    {"name": "台中港", "lat": 24.276, "lon": 120.517},
    {"name": "高雄港", "lat": 22.621, "lon": 120.284},
]


# =========================================
# 找出距離最近的參考點 (回傳名稱, 海浬距離)
# =========================================
def nearest_reference_point(lat, lon):
    distances = []
    for p in REFERENCE_POINTS:
        km = haversine(lat, lon, p["lat"], p["lon"])
        distances.append((p["name"], km_to_nm(km)))
    return min(distances, key=lambda x: x[1])  # (name, distance_nm)


# =========================================
# 計算方位角 (bearing / 0~360°)
# =========================================
def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = sin(dlon) * cos(lat2)
    y = cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(dlon)
    bearing = atan2(x, y)
    return (degrees(bearing) + 360) % 360


# =========================================
# 自動生成海域/距離描述
# =========================================
def describe_location_text(lat, lon):
    name, dist_nm = nearest_reference_point(lat, lon)
    if dist_nm <= 12:
        return f"正貼近{name}外海，僅 {dist_nm:.1f} 海浬！"
    elif dist_nm <= 24:
        return f"位於{name}外圍海域，約 {dist_nm:.1f} 海浬"
    else:
        return f"在{name}外海約 {dist_nm:.1f} 海浬"


# =========================================
# 錯誤紀錄
# =========================================
def log_failed_record(record_data, error_message):
    try:
        with open(FAILED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "error": error_message,
                "data": record_data
            }, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to write to failed log: {e}")
