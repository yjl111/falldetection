"""
统计分析模块
提供跌倒检测系统的数据统计和分析功能
"""

from flask import Blueprint, jsonify, request
import pymongo
from datetime import datetime, timedelta
from collections import defaultdict

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

# MongoDB 连接
mongo_client = None
db = None

def init_db():
    """初始化数据库连接"""
    global mongo_client, db
    try:
        mongo_client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        db = mongo_client["fall_detection_db"]
        mongo_client.server_info()
        print("[Statistics] ✅ MongoDB 连接成功")
    except Exception as e:
        print(f"[Statistics] ❌ MongoDB 连接失败: {e}")
        db = None

# 初始化数据库
init_db()


@statistics_bp.route('/summary', methods=['GET'])
def get_summary():
    """获取统计摘要数据"""
    if db is None:
        return jsonify({
            "today_falls": 0,
            "today_trend": "+0%",
            "week_falls": 0,
            "week_average": 0,
            "accuracy": 0,
            "false_alarm_rate": 0,
            "uptime": 99.9
        })
    
    try:
        # 计算今天的跌倒次数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_falls = db.alarms.count_documents({"timestamp": {"$gte": today_start}})
        
        # 计算昨天的跌倒次数，用于趋势对比
        yesterday_start = today_start - timedelta(days=1)
        yesterday_falls = db.alarms.count_documents({
            "timestamp": {"$gte": yesterday_start, "$lt": today_start}
        })
        
        # 计算趋势
        if yesterday_falls > 0:
            trend = ((today_falls - yesterday_falls) / yesterday_falls) * 100
            today_trend = f"{'+' if trend > 0 else ''}{int(trend)}%"
        else:
            today_trend = "+0%" if today_falls == 0 else "+100%"
        
        # 计算本周跌倒次数
        week_start = today_start - timedelta(days=today_start.weekday())
        week_falls = db.alarms.count_documents({"timestamp": {"$gte": week_start}})
        week_average = round(week_falls / 7, 1)
        
        # 从配置中获取准确率（或根据误报计算）
        config = db.config.find_one({"key": "accuracy"}) or {}
        accuracy = config.get("value", 94.5)
        false_alarm_rate = round(100 - accuracy, 1)
        
        # 系统运行时间（可从启动时间计算）
        uptime_config = db.config.find_one({"key": "uptime"}) or {}
        uptime = uptime_config.get("value", 99.8)
        
        return jsonify({
            "today_falls": today_falls,
            "today_trend": today_trend,
            "week_falls": week_falls,
            "week_average": week_average,
            "accuracy": accuracy,
            "false_alarm_rate": false_alarm_rate,
            "uptime": uptime
        })
    except Exception as e:
        print(f"[Statistics] 查询失败: {e}")
        return jsonify({"error": str(e)}), 500


@statistics_bp.route('/hourly', methods=['GET'])
def get_hourly():
    """获取每小时跌倒分布数据"""
    if db is None:
        return jsonify({
            "labels": ["0-4时", "4-8时", "8-12时", "12-16时", "16-20时", "20-24时"],
            "data": [0, 0, 0, 0, 0, 0]
        })
    
    try:
        # 获取今天的所有报警
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        alarms = db.alarms.find({"timestamp": {"$gte": today_start}})
        
        # 按时段统计
        hourly_counts = [0] * 6  # 6个时段
        for alarm in alarms:
            hour = alarm["timestamp"].hour
            period = hour // 4  # 0-4时=0, 4-8时=1, ...
            if period < 6:
                hourly_counts[period] += 1
        
        return jsonify({
            "labels": ["0-4时", "4-8时", "8-12时", "12-16时", "16-20时", "20-24时"],
            "data": hourly_counts
        })
    except Exception as e:
        print(f"[Statistics] 查询失败: {e}")
        return jsonify({"error": str(e)}), 500


@statistics_bp.route('/trend', methods=['GET'])
def get_trend():
    """获取趋势数据"""
    days = request.args.get('days', 7, type=int)
    
    if db is None:
        # 返回模拟数据
        if days == 7:
            return jsonify({
                "labels": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
                "data": [0, 0, 0, 0, 0, 0, 0]
            })
        else:
            return jsonify({"labels": [], "data": []})
    
    try:
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        start_date = end_date - timedelta(days=days)
        
        # 查询时间范围内的报警
        alarms = db.alarms.find({
            "timestamp": {"$gte": start_date, "$lte": end_date}
        })
        
        # 按日期统计
        daily_counts = defaultdict(int)
        for alarm in alarms:
            date_key = alarm["timestamp"].date()
            daily_counts[date_key] += 1
        
        # 生成标签和数据
        if days == 7:
            labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            data = []
            current = start_date.date()
            for _ in range(7):
                data.append(daily_counts.get(current, 0))
                current += timedelta(days=1)
        elif days == 30:
            labels = [f"{i+1}日" for i in range(30)]
            data = []
            current = start_date.date()
            for _ in range(30):
                data.append(daily_counts.get(current, 0))
                current += timedelta(days=1)
        else:  # 90天，按周统计
            labels = [f"第{i+1}周" for i in range(13)]
            data = [0] * 13
            current = start_date.date()
            for week in range(13):
                week_count = 0
                for _ in range(7):
                    week_count += daily_counts.get(current, 0)
                    current += timedelta(days=1)
                    if current > end_date.date():
                        break
                data[week] = week_count
        
        return jsonify({
            "labels": labels,
            "data": data
        })
    except Exception as e:
        print(f"[Statistics] 查询失败: {e}")
        return jsonify({"error": str(e)}), 500
