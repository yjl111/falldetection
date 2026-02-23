"""
报警管理模块
提供报警配置、联系人管理和报警历史记录功能
"""

from flask import Blueprint, jsonify, request
import pymongo
from datetime import datetime

alarms_bp = Blueprint('alarms', __name__, url_prefix='/api/alarms')

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
        print("[Alarms] ✅ MongoDB 连接成功")
    except Exception as e:
        print(f"[Alarms] ❌ MongoDB 连接失败: {e}")
        db = None

# 初始化数据库
init_db()


@alarms_bp.route('', methods=['GET'])
def get_alarms():
    """获取报警历史记录"""
    status = request.args.get('status', 'all')
    date = request.args.get('date', '')
    
    if db is None:
        return jsonify([])
    
    try:
        # 构建查询条件
        query = {}
        if status != 'all':
            query['status'] = '已处理' if status == 'handled' else '待处理'
        if date:
            # 按日期筛选
            start = datetime.strptime(date, '%Y-%m-%d')
            end = start.replace(hour=23, minute=59, second=59)
            query['timestamp'] = {"$gte": start, "$lte": end}
        
        # 查询报警记录，按时间倒序
        alarms = db.alarms.find(query).sort('timestamp', -1).limit(50)
        
        result = []
        for alarm in alarms:
            timestamp = alarm.get('timestamp', datetime.now())
            result.append({
                "id": alarm.get('id', str(alarm['_id'])),
                "time": timestamp.strftime('%Y-%m-%d %H:%M'),
                "location": alarm.get('location', '未知'),
                "type": alarm.get('type', '跌倒'),
                "status": alarm.get('status', '待处理')
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"[Alarms] 查询失败: {e}")
        return jsonify({"error": str(e)}), 500


@alarms_bp.route('/config', methods=['GET', 'POST'])
def alarm_config():
    """获取或更新报警配置"""
    if db is None:
        if request.method == 'POST':
            return jsonify({"success": False, "message": "数据库未连接"}), 500
        return jsonify({
            "sound": True,
            "notification": True,
            "email": False,
            "sms": False,
            "time_start": "00:00",
            "time_end": "23:59",
            "contacts": []
        })
    
    try:
        if request.method == 'POST':
            config = request.json
            # 更新或插入配置
            db.alarm_config.update_one(
                {"key": "main_config"},
                {"$set": {
                    "sound": config.get('sound', True),
                    "notification": config.get('notification', True),
                    "email": config.get('email', False),
                    "sms": config.get('sms', False),
                    "time_start": config.get('time_start', '00:00'),
                    "time_end": config.get('time_end', '23:59'),
                    "contacts": config.get('contacts', []),
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
            print(f"[Alarm Config] 更新配置: {config}")
            return jsonify({
                "success": True,
                "message": "报警配置已更新"
            })
        else:
            # 获取配置
            config = db.alarm_config.find_one({"key": "main_config"})
            if config:
                return jsonify({
                    "sound": config.get('sound', True),
                    "notification": config.get('notification', True),
                    "email": config.get('email', False),
                    "sms": config.get('sms', False),
                    "time_start": config.get('time_start', '00:00'),
                    "time_end": config.get('time_end', '23:59'),
                    "contacts": config.get('contacts', [])
                })
            else:
                # 返回默认配置
                return jsonify({
                    "sound": True,
                    "notification": True,
                    "email": False,
                    "sms": False,
                    "time_start": "00:00",
                    "time_end": "23:59",
                    "contacts": []
                })
    except Exception as e:
        print(f"[Alarms] 配置操作失败: {e}")
        return jsonify({"error": str(e)}), 500


@alarms_bp.route('/handle/<int:alarm_id>', methods=['POST'])
def handle_alarm(alarm_id):
    """处理报警"""
    if db is None:
        return jsonify({"success": False, "message": "数据库未连接"}), 500
    
    try:
        # 更新报警状态
        result = db.alarms.update_one(
            {"id": alarm_id},
            {"$set": {"status": "已处理", "handled_at": datetime.now()}}
        )
        
        if result.modified_count > 0:
            print(f"[Alarm] 处理报警 ID: {alarm_id}")
            return jsonify({
                "success": True,
                "message": f"报警 {alarm_id} 已标记为已处理"
            })
        else:
            return jsonify({
                "success": False,
                "message": "未找到该报警记录"
            }), 404
    except Exception as e:
        print(f"[Alarms] 处理报警失败: {e}")
        return jsonify({"error": str(e)}), 500


@alarms_bp.route('/contacts', methods=['GET', 'POST', 'DELETE'])
def manage_contacts():
    """管理联系人"""
    if db is None:
        if request.method == 'GET':
            return jsonify([])
        return jsonify({"success": False, "message": "数据库未连接"}), 500
    
    try:
        if request.method == 'POST':
            # 添加联系人
            contact = request.json
            contact['created_at'] = datetime.now()
            result = db.contacts.insert_one(contact)
            print(f"[Contacts] 添加联系人: {contact}")
            return jsonify({
                "success": True,
                "message": "联系人已添加",
                "id": str(result.inserted_id)
            })
        
        elif request.method == 'DELETE':
            # 删除联系人
            contact_id = request.args.get('id', type=int)
            result = db.contacts.delete_one({"id": contact_id})
            print(f"[Contacts] 删除联系人 ID: {contact_id}")
            return jsonify({
                "success": True if result.deleted_count > 0 else False,
                "message": "联系人已删除" if result.deleted_count > 0 else "未找到该联系人"
            })
        
        else:
            # 获取联系人列表
            contacts = list(db.contacts.find({}, {"_id": 0}))
            return jsonify(contacts)
    except Exception as e:
        print(f"[Contacts] 操作失败: {e}")
        return jsonify({"error": str(e)}), 500
