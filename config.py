# import os
# import json
# from dotenv import load_dotenv, find_dotenv
# from shapely.geometry import Polygon

# # =========================================
# # 載入環境變數
# # =========================================
# load_dotenv(find_dotenv())  # 自動尋找並載入 .env

# # LINE 設定
# LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN", "")
# LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
# LINE_TARGET_USER_ID = os.getenv("LINE_TARGET_USER_ID", "")

# #Gmail 設定
# GMAIL_USER = os.getenv("GMAIL_USER", "")
# GMAIL_PASS = os.getenv("GMAIL_PASS", "")


# # =========================================
# # 資料庫路徑設定（統一使用絕對路徑 + 小寫命名）
# # =========================================
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_DIR = os.path.join(BASE_DIR, "db")
# os.makedirs(DB_DIR, exist_ok=True)  # 確保 db 資料夾存在

# # ✅ 所有 DB 路徑一致採用小寫命名，避免跨系統錯誤
# MAIN_DB_PATH = os.path.join(DB_DIR, "ais_data.db")
# TEST_DB_PATH = os.path.join(DB_DIR, "data_test.db")
# BOAT_DB_PATH = os.path.join(DB_DIR, "boat_test.db")
# BOAT_CHECK12_DB_PATH = os.path.join(DB_DIR, "boat_check12.db")
# BOAT_CHECK24_DB_PATH = os.path.join(DB_DIR, "boat_check24.db")
# CCG_DB_PATH = os.path.join(DB_DIR, "ccg.db")
# CCG_CHECK12_DB_PATH = os.path.join(DB_DIR, "ccg_check12.db")
# CCG_CHECK24_DB_PATH = os.path.join(DB_DIR, "ccg_check24.db")
# CHINA_BOAT_DB_PATH = "chinaboat.db"


# FAILED_LOG_FILE = os.path.join(BASE_DIR, "failed_records.json")

# # =========================================
# # GeoJSON 載入函式
# # =========================================
# def load_geojson_polygon(filename):
#     """
#     載入 GeoJSON 並回傳 shapely Polygon。
#     支援 Polygon / MultiPolygon / LineString / MultiLineString。
#     """
#     path = os.path.join(BASE_DIR, filename)
#     if not os.path.exists(path):
#         print(f"[config] ⚠️ 找不到 {filename}")
#         return None

#     try:
#         with open(path, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         coords = []

#         for feature in data.get("features", []):
#             geom = feature.get("geometry", {})
#             geom_type = geom.get("type")
#             geom_coords = geom.get("coordinates", [])

#             # ✅ Polygon
#             if geom_type == "Polygon":
#                 coords.extend(geom_coords[0])

#             # ✅ MultiPolygon
#             elif geom_type == "MultiPolygon":
#                 for poly in geom_coords:
#                     coords.extend(poly[0])

#             # ✅ LineString / MultiLineString → 封成 Polygon
#             elif geom_type in ["LineString", "MultiLineString"]:
#                 if geom_type == "LineString":
#                     line_coords = geom_coords
#                 else:
#                     line_coords = [pt for line in geom_coords for pt in line]
#                 # 若首尾沒封閉就補上
#                 if line_coords[0] != line_coords[-1]:
#                     line_coords.append(line_coords[0])
#                 coords.extend(line_coords)

#         if not coords:
#             print(f"[config] ⚠️ {filename} 沒有可用座標")
#             return None

#         poly = Polygon(coords)
#         if not poly.is_valid:
#             poly = poly.buffer(0)  # 修復自交錯誤

#         print(f"[config] ✅ 載入 {filename} 成功，共 {len(coords)} 點")
#         return poly

#     except Exception as e:
#         print(f"[config] ⚠️ 載入 {filename} 失敗: {e}")
#         return None


# # =========================================
# # 載入台灣海域範圍 (12nm / 24nm)
# # =========================================
# TAIWAN_12NM_POLYGON = load_geojson_polygon("static/taiwan_12nm.geojson")
# TAIWAN_24NM_POLYGON = load_geojson_polygon("static/taiwan_24nm.geojson")

# # 舊版程式相容性
# TAIWAN_POLYGON = TAIWAN_12NM_POLYGON


# ENABLE_LINE_PUSH = False   # 改成 True 就會重新啟用



import os
import json
from dotenv import load_dotenv, find_dotenv
from shapely.geometry import Polygon
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# =========================================
# 載入環境變數
# =========================================
load_dotenv(find_dotenv())  # 自動尋找並載入 .env

# LINE 設定
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_TARGET_USER_ID = os.getenv("LINE_TARGET_USER_ID", "")

# Gmail 設定
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")

# =========================================
# 資料庫路徑設定（統一使用絕對路徑 + 小寫命名）
# =========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
os.makedirs(DB_DIR, exist_ok=True)  # 確保 db 資料夾存在

# ✅ 所有 DB 路徑一致採用小寫命名，避免跨系統錯誤
MAIN_DB_PATH = os.path.join(DB_DIR, "ais_data.db")
TEST_DB_PATH = os.path.join(DB_DIR, "data_test.db")
BOAT_DB_PATH = os.path.join(DB_DIR, "boat_test.db")
BOAT_CHECK12_DB_PATH = os.path.join(DB_DIR, "boat_check12.db")
BOAT_CHECK24_DB_PATH = os.path.join(DB_DIR, "boat_check24.db")
CCG_DB_PATH = os.path.join(DB_DIR, "ccg.db")
CCG_CHECK12_DB_PATH = os.path.join(DB_DIR, "ccg_check12.db")
CCG_CHECK24_DB_PATH = os.path.join(DB_DIR, "ccg_check24.db")
CHINA_BOAT_DB_PATH = os.path.join(DB_DIR, "chinaboat.db")

FAILED_LOG_FILE = os.path.join(BASE_DIR, "failed_records.json")

# =========================================
# GeoJSON 載入函式
# =========================================
def load_geojson_polygon(filename):
    """
    載入 GeoJSON 並回傳 shapely Polygon。
    支援 Polygon / MultiPolygon / LineString / MultiLineString。
    """
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        print(f"[config] ⚠️ 找不到 {filename}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        coords = []

        for feature in data.get("features", []):
            geom = feature.get("geometry", {})
            geom_type = geom.get("type")
            geom_coords = geom.get("coordinates", [])

            # ✅ Polygon
            if geom_type == "Polygon":
                coords.extend(geom_coords[0])

            # ✅ MultiPolygon
            elif geom_type == "MultiPolygon":
                for poly in geom_coords:
                    coords.extend(poly[0])

            # ✅ LineString / MultiLineString → 封成 Polygon
            elif geom_type in ["LineString", "MultiLineString"]:
                if geom_type == "LineString":
                    line_coords = geom_coords
                else:
                    line_coords = [pt for line in geom_coords for pt in line]
                # 若首尾沒封閉就補上
                if line_coords[0] != line_coords[-1]:
                    line_coords.append(line_coords[0])
                coords.extend(line_coords)

        if not coords:
            print(f"[config] ⚠️ {filename} 沒有可用座標")
            return None

        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)  # 修復自交錯誤

        print(f"[config] ✅ 載入 {filename} 成功，共 {len(coords)} 點")
        return poly

    except Exception as e:
        print(f"[config] ⚠️ 載入 {filename} 失敗: {e}")
        return None


# =========================================
# 載入台灣海域範圍 (12nm / 24nm)
# =========================================
TAIWAN_12NM_POLYGON = load_geojson_polygon("static/taiwan_12nm.geojson")
TAIWAN_24NM_POLYGON = load_geojson_polygon("static/taiwan_24nm.geojson")

# 舊版程式相容性
TAIWAN_POLYGON = TAIWAN_12NM_POLYGON

# =========================================
# 啟用設定
# =========================================
ENABLE_LINE_PUSH = False   # 改成 True 就會重新啟用 LINE 推播

# =========================================
# ✅ 通用工具函式：建立 engine + session + Base
# =========================================
def make_engine_and_session(db_path: str):
    """
    建立一個獨立的 SQLAlchemy engine、session、Base，
    用來管理多個 SQLite 資料庫（非 Flask 綁定的）。
    """
    abs_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    engine = create_engine(
        f"sqlite:///{abs_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    Base = declarative_base()

    return engine, Session, Base
