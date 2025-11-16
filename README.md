# 船舶 AIS 資料收集與查詢系統

這是一個基於 Flask 的船舶 AIS 資料收集與查詢系統，使用 SQLite 作為資料庫，並定期從 MarineTraffic 網站抓取船舶 AIS 資料。

## 功能特色

- **定期資料收集**：每 10 分鐘自動從 MarineTraffic 網站抓取最新船舶 AIS 資料
- **資料儲存**：將抓取的資料儲存到 SQLite 資料庫中，包含船舶位置、航速、航向等詳細資訊
- **API 查詢**：
  - 取得最新每區塊的船舶資料
  - 查詢歷史資料，可根據船名、船舶 ID 和時間範圍進行篩選
- **錯誤處理**：自動記錄資料抓取過程中失敗的記錄到 failed_records.json

## 系統需求

- Python 3.8+
- 所需套件請參考 `requirements.txt`

## 安裝步驟

1. 克隆專案：
   ```bash
   git clone https://github.com/your-repo/ais_api.git
   ```
2. 進入專案目錄：
   ```bash
   cd ais_api
   ```
3. 安裝套件：
   ```bash
   pip install -r requirements.txt
   ```
4. 啟動服務：
   ```bash
   python server.py
   ```

## API 使用說明

### 取得最新資料
`GET /api/ais/latest`

**範例回應：**
```json
{
  "timestamp": "2025-03-30T12:33:20.123456",
  "results": {
    "z_2_X_0_Y_0_station_0": {
      "timestamp": "2025-03-30T12:30:00.000000",
      "source": "z_2_X_0_Y_0_station_0",
      "ship_id": "123456789",
      "shipname": "EXAMPLE SHIP",
      "lat": 25.033333,
      "lon": 121.533333,
      "speed": 12.3,
      "course": 270.0,
      "heading": 268.0,
      "rot": 0.5,
      "destination": "Keelung",
      "dwt": "13500",
      "flag": "Taiwan",
      "shiptype": "Cargo",
      "gt_shiptype": "General Cargo",
      "length": "150",
      "width": "23"
    }
  }
}
```

### 查詢歷史資料
`GET /api/ais/history`

**查詢參數：**
- shipname: 船名 (模糊查詢)
- ship_id: 船舶 ID (精確查詢)
- start: 開始時間 (ISO 8601 格式)
- end: 結束時間 (ISO 8601 格式)

**範例請求：**
```
/api/ais/history?shipname=example&start=2025-03-30T00:00:00&end=2025-03-30T23:59:59
```

## 版本資訊

- v1.0.0 (2025-03-30): 初始版本
# Boat
