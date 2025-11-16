# alarm_loader.py
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from config import make_engine_and_session

# 初始化資料庫
engine, Session, Base = make_engine_and_session("db/alarm_zones.db")

class AlarmZone(Base):
    __tablename__ = "alarm_zones"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    geojson = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def load_alarm_zones():
    """載入所有警戒區（Polygon）"""
    session = Session()
    zones = session.query(AlarmZone).all()
    result = []
    for z in zones:
        try:
            f = json.loads(z.geojson)
            coords = f["geometry"]["coordinates"][0]
            result.append({
                "id": z.id,
                "name": f["properties"].get("name", "未命名警戒區"),
                "coords": coords
            })
        except Exception as e:
            print(f"⚠️ 載入警戒區失敗 {z.id}: {e}")
    session.close()
    return result
