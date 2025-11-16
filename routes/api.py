from flask import Blueprint, jsonify, request, abort
from dateutil import parser
from datetime import datetime

from models import (
    ShipAIS,
    BoatCheck12AIS, BoatCheck24AIS,
    CCGShipAIS, CCGCheck12ShipAIS, CCGCheck24ShipAIS,
    BoatCheck12Session, BoatCheck24Session,
    CCGSession, CCGCheck12Session, CCGCheck24Session,
    ChinaBoatSession, ChinaBoatAIS
)

# 建立 Blueprint
api_blueprint = Blueprint("api", __name__)

# =========================================
# API: 最新 AIS 資料
# =========================================
@api_blueprint.route("/ais/latest", methods=["GET"])
def get_latest_data():
    try:
        results = {}
        latest = ShipAIS.query.order_by(ShipAIS.timestamp.desc()).all()
        for row in latest:
            if row.source not in results:
                results[row.source] = row.to_dict()
        return jsonify({"timestamp": datetime.utcnow().isoformat(), "results": results})
    except Exception as e:
        abort(500, description=str(e))

# =========================================
# API: AIS 歷史資料查詢
# =========================================
@api_blueprint.route("/ais/history", methods=["GET"])
def get_ship_history():
    try:
        query = ShipAIS.query

        # 篩選船名
        if request.args.get("shipname"):
            query = query.filter(ShipAIS.shipname.ilike(f"%{request.args['shipname']}%"))

        # 篩選船 ID
        if request.args.get("ship_id"):
            query = query.filter_by(ship_id=request.args["ship_id"])

        # 篩選時間區間
        if request.args.get("start") and request.args.get("end"):
            start = parser.parse(request.args.get("start"))
            end = parser.parse(request.args.get("end"))
            query = query.filter(ShipAIS.timestamp.between(start, end))

        # 🟡【加在這裡】加入經緯度篩選條件
        min_lat = request.args.get("min_lat")
        max_lat = request.args.get("max_lat")
        min_lon = request.args.get("min_lon")
        max_lon = request.args.get("max_lon")

        # 經緯度範圍檢查 + 篩選
        if min_lat and max_lat and float(min_lat) < float(max_lat):
            query = query.filter(
                ShipAIS.lat >= float(min_lat),
                ShipAIS.lat <= float(max_lat)
            )
        if min_lon and max_lon and float(min_lon) < float(max_lon):
            query = query.filter(
                ShipAIS.lon >= float(min_lon),
                ShipAIS.lon <= float(max_lon)
            )

        # ✅ 查詢結果
        results = [r.to_dict() for r in query.order_by(ShipAIS.timestamp.desc())]

        # ✅ 額外回傳筆數統計（可在前端 console 顯示）
        return jsonify({
            "count": len(results),
            "data": results
        })

    except Exception as e:
        abort(500, description=str(e))


# =========================================
# API: CCG 最新資料（所有海警船最新）
# =========================================
@api_blueprint.route("/ccg_data", methods=["GET"])
def get_ccg_data():
    try:
        results = CCGSession.query(CCGShipAIS).all()
        data = [
            {
                "ship_id": r.ship_id,
                "shipname": r.shipname,
                "lat": r.lat,
                "lon": r.lon,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            }
            for r in results
        ]
        return jsonify({"timestamp": datetime.utcnow().isoformat(), "boats": data})
    except Exception as e:
        abort(500, description=str(e))

# =========================================
# API: boat_check12（12 海里內歷史）
# =========================================
@api_blueprint.route("/boat_check12", methods=["GET"])
def get_boat_check12_data():
    try:
        results = BoatCheck12Session.query(BoatCheck12AIS).all()
        data = [
            {
                "ship_id": r.ship_id,
                "shipname": r.shipname,
                "lat": r.lat,
                "lon": r.lon,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            }
            for r in results
        ]
        return jsonify({"timestamp": datetime.utcnow().isoformat(), "boats": data})
    except Exception as e:
        abort(500, description=str(e))

# =========================================
# API: boat_check24（12–24 海里範圍歷史）
# =========================================
@api_blueprint.route("/boat_check24", methods=["GET"])
def get_boat_check24_data():
    try:
        results = BoatCheck24Session.query(BoatCheck24AIS).all()
        data = [
            {
                "ship_id": r.ship_id,
                "shipname": r.shipname,
                "lat": r.lat,
                "lon": r.lon,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            }
            for r in results
        ]
        return jsonify({"timestamp": datetime.utcnow().isoformat(), "boats": data})
    except Exception as e:
        abort(500, description=str(e))

# =========================================
# API: ccg_check12（目前在 12nm 內的最新海警船）
# =========================================
@api_blueprint.route("/ccg_check12_data", methods=["GET"])
def get_ccg_check12_data():
    try:
        results = CCGCheck12Session.query(CCGCheck12ShipAIS).all()
        data = [
            {
                "ship_id": r.ship_id,
                "shipname": r.shipname,
                "lat": r.lat,
                "lon": r.lon,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            }
            for r in results
        ]
        return jsonify({"timestamp": datetime.utcnow().isoformat(), "boats": data})
    except Exception as e:
        abort(500, description=str(e))

# =========================================
# API: ccg_check24（目前在 12–24nm 間的最新海警船）
# =========================================
@api_blueprint.route("/ccg_check24_data", methods=["GET"])
def get_ccg_check24_data():
    try:
        results = CCGCheck24Session.query(CCGCheck24ShipAIS).all()
        data = [
            {
                "ship_id": r.ship_id,
                "shipname": r.shipname,
                "lat": r.lat,
                "lon": r.lon,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            }
            for r in results
        ]
        return jsonify({"timestamp": datetime.utcnow().isoformat(), "boats": data})
    except Exception as e:
        abort(500, description=str(e))

# =========================================
# API: chinaboat/all（所有中國籍船隻資料）
# =========================================
@api_blueprint.route("/chinaboat/all", methods=["GET"])
def get_all_chinaboats():
    try:
        query = ChinaBoatSession.query(ChinaBoatAIS)

        # 船名模糊搜尋
        if request.args.get("shipname"):
            query = query.filter(ChinaBoatAIS.shipname.ilike(f"%{request.args['shipname']}%"))

        # 時間區間
        if request.args.get("start") and request.args.get("end"):
            start = parser.parse(request.args.get("start"))
            end = parser.parse(request.args.get("end"))
            query = query.filter(ChinaBoatAIS.timestamp.between(start, end))

        # 經緯度範圍
        min_lat = request.args.get("min_lat")
        max_lat = request.args.get("max_lat")
        min_lon = request.args.get("min_lon")
        max_lon = request.args.get("max_lon")

        if min_lat and max_lat:
            query = query.filter(ChinaBoatAIS.lat.between(float(min_lat), float(max_lat)))
        if min_lon and max_lon:
            query = query.filter(ChinaBoatAIS.lon.between(float(min_lon), float(max_lon)))

        # 執行查詢
        results = query.order_by(ChinaBoatAIS.timestamp.desc()).all()

        # 格式統一成 AIS 格式
        data = [
            {
                "ship_id": r.ship_id,
                "shipname": r.shipname,
                "lat": r.lat,
                "lon": r.lon,
                "speed": r.speed,
                "course": r.course,
                "shiptype": r.shiptype,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else None
            }
            for r in results
        ]

        return jsonify({"count": len(data), "data": data})

    except Exception as e:
        abort(500, description=str(e))


# =========================================
# API: chinaboat/latest（最新中國籍船隻資料）
# =========================================
@api_blueprint.route("/chinaboat/latest", methods=["GET"])
def get_latest_chinaboats():
    try:
        results = (
            ChinaBoatSession.query(ChinaBoatAIS)
            .order_by(ChinaBoatAIS.timestamp.desc())
            .limit(200)
            .all()
        )

        data = [
            {
                "ship_id": r.ship_id,
                "shipname": r.shipname,
                "lat": r.lat,
                "lon": r.lon,
                "speed": r.speed,
                "course": r.course,
                "shiptype": r.shiptype,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else None
            }
            for r in results
        ]

        return jsonify({"count": len(data), "data": data})

    except Exception as e:
        abort(500, description=str(e))


