from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from config import (
    MAIN_DB_PATH,
    TEST_DB_PATH,
    BOAT_DB_PATH,
    BOAT_CHECK12_DB_PATH,
    BOAT_CHECK24_DB_PATH,
    CCG_DB_PATH,
    CCG_CHECK12_DB_PATH,
    CCG_CHECK24_DB_PATH,
    CHINA_BOAT_DB_PATH
)
from database import db, make_engine_and_session  # ✅ 用 database.py 的 db

# =========================================
# 共用欄位 Mixin
# =========================================
class ShipBaseMixin:
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(200))
    ship_id = Column(String(50))
    shipname = Column(String(200))
    lat = Column(Float)
    lon = Column(Float)
    speed = Column(Float)
    course = Column(Float)
    heading = Column(Float)
    rot = Column(Float)
    destination = Column(String(200))
    dwt = Column(String(50))
    flag = Column(String(50))
    shiptype = Column(String(50))
    gt_shiptype = Column(String(50))
    length = Column(String(50))
    width = Column(String(50))

    def to_dict(self):
        """將 ORM 物件轉為 JSON 可用 dict"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# =========================================
# 主資料庫（Flask 綁定的 SQLAlchemy）
# =========================================
class ShipAIS(db.Model, ShipBaseMixin):   # ✅ 用 database.py 的 db
    __tablename__ = "ship_ais"


# =========================================
# 其他 SQLite 資料庫（非 Flask 綁定）
# =========================================
# 各 DB 的 engine + session + Base
test_engine, TestSession, TestBase = make_engine_and_session(TEST_DB_PATH)
boat_engine, BoatSession, BoatBase = make_engine_and_session(BOAT_DB_PATH)
boat_check12_engine, BoatCheck12Session, BoatCheck12Base = make_engine_and_session(BOAT_CHECK12_DB_PATH)
boat_check24_engine, BoatCheck24Session, BoatCheck24Base = make_engine_and_session(BOAT_CHECK24_DB_PATH)
ccg_engine, CCGSession, CCGBase = make_engine_and_session(CCG_DB_PATH)
ccg_check12_engine, CCGCheck12Session, CCGCheck12Base = make_engine_and_session(CCG_CHECK12_DB_PATH)
ccg_check24_engine, CCGCheck24Session, CCGCheck24Base = make_engine_and_session(CCG_CHECK24_DB_PATH)
china_boat_engine, ChinaBoatSession, ChinaBoatBase = make_engine_and_session(CHINA_BOAT_DB_PATH)



# =========================================
# 各 DB 對應的表格類別
# =========================================

# 最新資料（data_test.db）
class TestShipAIS(TestBase, ShipBaseMixin):
    __tablename__ = "ship_ais"

# 所有海警船歷史資料（boat_test.db）
class BoatShipAIS(BoatBase, ShipBaseMixin):
    __tablename__ = "ship_ais"

# 進入 12 海里內的海警船歷史資料（boat_check12.db）
class BoatCheck12AIS(BoatCheck12Base, ShipBaseMixin):
    __tablename__ = "ship_ais"

# 位於 12–24 海里範圍內的海警船歷史資料（boat_check24.db）
class BoatCheck24AIS(BoatCheck24Base, ShipBaseMixin):
    __tablename__ = "ship_ais"

# 每艘海警船的最新狀態（CCG.db）
class CCGShipAIS(CCGBase, ShipBaseMixin):
    __tablename__ = "ship_ais"

# 目前在 12 海里內的海警船最新狀態（ccg_check12.db）
class CCGCheck12ShipAIS(CCGCheck12Base, ShipBaseMixin):
    __tablename__ = "ship_ais"

# 目前在 12–24 海里範圍內的海警船最新狀態（ccg_check24.db）
class CCGCheck24ShipAIS(CCGCheck24Base, ShipBaseMixin):
    __tablename__ = "ship_ais"

# 所有中國籍船舶歷史資料（chinaboat.db, flag == "CN"）
class ChinaBoatAIS(ChinaBoatBase, ShipBaseMixin):
    __tablename__ = "ship_ais"



# =========================================
# 初始化資料表
# =========================================
def init_models(app):
    """初始化所有資料庫的表格"""
    print("🚀 初始化所有資料庫表格...")

    with app.app_context():
        db.create_all()   # ✅ Flask 綁定主 DB (ais_data.db)

    TestBase.metadata.create_all(test_engine)
    BoatBase.metadata.create_all(boat_engine)
    BoatCheck12Base.metadata.create_all(boat_check12_engine)
    BoatCheck24Base.metadata.create_all(boat_check24_engine)
    CCGBase.metadata.create_all(ccg_engine)
    CCGCheck12Base.metadata.create_all(ccg_check12_engine)
    CCGCheck24Base.metadata.create_all(ccg_check24_engine)
    ChinaBoatBase.metadata.create_all(china_boat_engine)


    print("✅ 所有資料表初始化完成！")
