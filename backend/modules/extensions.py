from flask import Blueprint, jsonify, request
import pymongo
from datetime import datetime, timedelta
from bson import ObjectId
from modules.auth import has_role, get_request_user

extensions_bp = Blueprint('extensions', __name__, url_prefix='/api/ext')

# MongoDB 连接
try:
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    db = mongo_client["fall_detection_db"]
except Exception as e:
    db = None

def serialize_doc(doc):
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
        elif isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc


def write_audit(action, details="", target_type="", target_id=None, username="system", status="success"):
    if db is None:
        return
    try:
        db.audit_logs.insert_one({
            "username": username,
            "action": action,
            "details": details,
            "target_type": target_type,
            "target_id": target_id,
            "status": status,
            "created_at": datetime.now()
        })
    except Exception as e:
        print(f"[Extensions][Audit] 写入失败: {e}")


def get_current_user():
    payload = get_request_user(request)
    if not payload:
        return None, "未登录或令牌无效"
    return payload, None


def ensure_admin():
    allowed, payload = has_role(request, 'admin')
    if not allowed:
        return None, (jsonify({"error": "仅管理员可操作"}), 403)
    return payload, None

# ================= 紧急联系人 (emergency_contacts) CRUD =================

@extensions_bp.route('/contacts', methods=['GET'])
def get_contacts():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    contacts = list(db.emergency_contacts.find())
    return jsonify([serialize_doc(c) for c in contacts])

@extensions_bp.route('/contacts', methods=['POST'])
def add_contact():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json
    data['created_at'] = datetime.now()
    if 'is_active' not in data: data['is_active'] = True
    result = db.emergency_contacts.insert_one(data)
    return jsonify({"success": True, "id": str(result.inserted_id)})

@extensions_bp.route('/contacts/<contact_id>', methods=['PUT'])
def update_contact(contact_id):
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json
    db.emergency_contacts.update_one({'_id': ObjectId(contact_id)}, {'$set': data})
    return jsonify({"success": True})

@extensions_bp.route('/contacts/<contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    if db is None: return jsonify({"error": "DB not connected"}), 500
    db.emergency_contacts.delete_one({'_id': ObjectId(contact_id)})
    return jsonify({"success": True})

# ================= 设备管理 (devices) CRUD =================

@extensions_bp.route('/devices', methods=['GET'])
def get_devices():
    allowed, _ = has_role(request, 'admin')
    if not allowed: return jsonify({"error": "仅管理员可查看设备"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    devices = list(db.devices.find().sort('created_at', -1))
    return jsonify([serialize_doc(d) for d in devices])


@extensions_bp.route('/devices', methods=['POST'])
def add_device():
    allowed, _ = has_role(request, 'admin')
    if not allowed: return jsonify({"error": "仅管理员可新增设备"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json or {}
    data['created_at'] = datetime.now()
    if not data.get('device_id'):
        data['device_id'] = f"CAM-{int(datetime.now().timestamp())}"
    if 'status' not in data:
        data['status'] = 'offline'
    result = db.devices.insert_one(data)
    write_audit(
        action="ADD_DEVICE",
        details=f"新增设备 {data.get('device_id')}",
        target_type="device",
        target_id=data.get('device_id')
    )
    return jsonify({"success": True, "id": str(result.inserted_id)})


@extensions_bp.route('/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    allowed, _ = has_role(request, 'admin')
    if not allowed: return jsonify({"error": "仅管理员可更新设备"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json or {}
    result = db.devices.update_one({'_id': ObjectId(device_id)}, {'$set': data})
    if result.matched_count > 0:
        write_audit(
            action="UPDATE_DEVICE",
            details=f"更新设备 {device_id}",
            target_type="device",
            target_id=device_id
        )
    return jsonify({"success": result.matched_count > 0})


@extensions_bp.route('/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    allowed, _ = has_role(request, 'admin')
    if not allowed: return jsonify({"error": "仅管理员可删除设备"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    result = db.devices.delete_one({'_id': ObjectId(device_id)})
    if result.deleted_count > 0:
        write_audit(
            action="DELETE_DEVICE",
            details=f"删除设备 {device_id}",
            target_type="device",
            target_id=device_id
        )
    return jsonify({"success": result.deleted_count > 0})

# ================= AI误报纠错 (alarm_feedback) CRUD =================

@extensions_bp.route('/feedback', methods=['GET'])
def get_feedbacks():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    feedbacks = list(db.alarm_feedback.find())
    return jsonify([serialize_doc(f) for f in feedbacks])

@extensions_bp.route('/feedback', methods=['POST'])
def add_feedback():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json
    data['reviewed_at'] = datetime.now()
    result = db.alarm_feedback.insert_one(data)
    
    # 同步更新原报警记录状态为 "被纠错"（可选辅助逻辑）
    if 'alarm_id' in data and data['alarm_id']:
        try:
            db.alarms.update_one(
                {'_id': ObjectId(data['alarm_id'])},
                {'$set': {'status': '已纠错', 'is_false_positive': data.get('is_false_positive', False)}}
            )
        except:
             # 如果 alarm_id 不是合法的 ObjectId，尝试用原始 id 更新
             db.alarms.update_one(
                {'id': data['alarm_id']},
                {'$set': {'status': '已纠错', 'is_false_positive': data.get('is_false_positive', False)}}
            )

    return jsonify({"success": True, "id": str(result.inserted_id)})

# ================= 训练日志 / 审计日志 / 通知日志只读接口 =================

@extensions_bp.route('/training-logs', methods=['GET'])
def get_training_logs():
    allowed, _ = has_role(request, 'admin')
    if not allowed: return jsonify({"error": "仅管理员可查看训练日志"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    logs = list(db.model_training_logs.find().sort('start_time', -1).limit(50))
    return jsonify([serialize_doc(log) for log in logs])


@extensions_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    allowed, _ = has_role(request, 'admin')
    if not allowed: return jsonify({"error": "仅管理员可查看审计日志"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    logs = list(db.audit_logs.find().sort('created_at', -1).limit(100))
    return jsonify([serialize_doc(log) for log in logs])


@extensions_bp.route('/notification-logs', methods=['GET'])
def get_notification_logs():
    allowed, _ = has_role(request, 'admin')
    if not allowed: return jsonify({"error": "仅管理员可查看通知日志"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    logs = list(db.notification_logs.find().sort('created_at', -1).limit(100))
    return jsonify([serialize_doc(log) for log in logs])


# ================= 用户资料 (user_profiles) =================

@extensions_bp.route('/profile', methods=['GET'])
def get_profile():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = payload.get('user')
    profile = db.user_profiles.find_one({"username": username}) or {"username": username}
    return jsonify(serialize_doc(profile))


@extensions_bp.route('/profile', methods=['POST'])
def save_profile():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = payload.get('user')
    data = request.json or {}
    update_doc = {
        "username": username,
        "real_name": data.get("real_name", ""),
        "phone": data.get("phone", ""),
        "address": data.get("address", ""),
        "age": data.get("age", ""),
        "medical_notes": data.get("medical_notes", ""),
        "updated_at": datetime.now()
    }
    db.user_profiles.update_one({"username": username}, {"$set": update_doc}, upsert=True)
    write_audit("UPDATE_PROFILE", f"更新用户资料 {username}", "user_profile", username, username=username)
    return jsonify({"success": True, "message": "资料已保存"})


# ================= 用户消息 (user_messages) =================

@extensions_bp.route('/messages', methods=['GET'])
def get_messages():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = payload.get('user')
    messages = list(db.user_messages.find({"username": username}).sort('created_at', -1).limit(100))
    return jsonify([serialize_doc(message) for message in messages])


@extensions_bp.route('/messages', methods=['POST'])
def add_message():
    allowed, payload = has_role(request, 'admin')
    if not allowed:
        return jsonify({"error": "仅管理员可发送消息"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json or {}
    doc = {
        "username": data.get("username", ""),
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "type": data.get("type", "system"),
        "is_read": False,
        "created_at": datetime.now()
    }
    result = db.user_messages.insert_one(doc)
    write_audit("CREATE_USER_MESSAGE", f"发送消息给 {doc['username']}", "user_message", str(result.inserted_id), username=payload.get('user'))
    return jsonify({"success": True, "id": str(result.inserted_id)})


@extensions_bp.route('/messages/<message_id>/read', methods=['POST'])
def mark_message_read(message_id):
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = payload.get('user')
    result = db.user_messages.update_one(
        {"_id": ObjectId(message_id), "username": username},
        {"$set": {"is_read": True, "read_at": datetime.now()}}
    )
    return jsonify({"success": result.modified_count > 0})


# ================= 报警工单 (alarm_workorders) =================

@extensions_bp.route('/workorders', methods=['GET'])
def get_workorders():
    allowed, _ = has_role(request, 'admin')
    if not allowed:
        return jsonify({"error": "仅管理员可查看报警工单"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    alarm_id = request.args.get('alarm_id')
    query = {}
    if alarm_id:
        try:
            query["alarm_id"] = int(alarm_id)
        except ValueError:
            query["alarm_id"] = alarm_id
    workorders = list(db.alarm_workorders.find(query).sort('created_at', -1).limit(100))
    return jsonify([serialize_doc(workorder) for workorder in workorders])


@extensions_bp.route('/workorders', methods=['POST'])
def create_workorder():
    allowed, payload = has_role(request, 'admin')
    if not allowed:
        return jsonify({"error": "仅管理员可创建报警工单"}), 403
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json or {}
    alarm_id = data.get("alarm_id")
    doc = {
        "alarm_id": alarm_id,
        "handler": payload.get('user'),
        "result": data.get("result", ""),
        "comment": data.get("comment", ""),
        "status": data.get("status", "closed"),
        "created_at": datetime.now(),
        "handled_at": datetime.now()
    }
    result = db.alarm_workorders.insert_one(doc)
    db.alarms.update_one(
        {"id": alarm_id},
        {"$set": {
            "status": "已处理",
            "handled_at": datetime.now(),
            "handler": payload.get('user'),
            "workorder_id": result.inserted_id
        }}
    )
    alarm = db.alarms.find_one({"id": alarm_id}) or {}
    target_username = alarm.get("username", "demo_user")
    db.user_messages.insert_one({
        "username": target_username,
        "title": "报警处理反馈",
        "content": f"报警 #{alarm_id} 已处理。结果：{doc['result']}。备注：{doc['comment'] or '无'}",
        "type": "alarm",
        "is_read": False,
        "created_at": datetime.now()
    })
    write_audit("CREATE_WORKORDER", f"处理报警工单 {alarm_id}", "alarm_workorder", str(result.inserted_id), username=payload.get('user'))
    return jsonify({"success": True, "id": str(result.inserted_id)})


# ================= 健康报告 (health_reports) =================

@extensions_bp.route('/health-reports', methods=['GET'])
def get_health_reports():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = request.args.get('username', '').strip()
    if payload.get('role') != 'admin':
        username = payload.get('user')
    elif not username:
        username = payload.get('user')
    reports = list(db.health_reports.find({"username": username}).sort('created_at', -1).limit(50))
    return jsonify([serialize_doc(report) for report in reports])


@extensions_bp.route('/health-reports/generate', methods=['POST'])
def generate_health_report():
    payload, failure = ensure_admin()
    if failure:
        return failure
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json or {}
    username = data.get('username', 'demo_user')
    report_type = data.get('report_type', 'weekly')
    days = int(data.get('days', 7))
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    alarms = list(db.alarms.find({
        "timestamp": {"$gte": start_date, "$lte": end_date},
        "username": username
    }))
    if not alarms:
        alarms = list(db.alarms.find({
            "timestamp": {"$gte": start_date, "$lte": end_date}
        }))
    fall_count = len(alarms)
    false_positive_count = db.alarm_feedback.count_documents({
        "reviewer": username,
        "is_false_positive": True
    })
    period_buckets = {"00:00-08:00": 0, "08:00-12:00": 0, "12:00-18:00": 0, "18:00-24:00": 0}
    for alarm in alarms:
        hour = alarm.get("timestamp", datetime.now()).hour
        if hour < 8:
            period_buckets["00:00-08:00"] += 1
        elif hour < 12:
            period_buckets["08:00-12:00"] += 1
        elif hour < 18:
            period_buckets["12:00-18:00"] += 1
        else:
            period_buckets["18:00-24:00"] += 1
    high_risk_period = max(period_buckets, key=period_buckets.get) if period_buckets else "-"
    summary = f"近{days}天共记录{fall_count}次报警，误报{false_positive_count}次，高风险时段为{high_risk_period}。"
    doc = {
        "username": username,
        "report_type": report_type,
        "start_date": start_date,
        "end_date": end_date,
        "fall_count": fall_count,
        "false_positive_count": false_positive_count,
        "high_risk_period": high_risk_period,
        "summary": summary,
        "created_at": datetime.now()
    }
    result = db.health_reports.insert_one(doc)
    write_audit("GENERATE_HEALTH_REPORT", f"生成健康报告 {username}", "health_report", str(result.inserted_id), username=payload.get('user'))
    return jsonify({"success": True, "id": str(result.inserted_id), "summary": summary})


# ================= 设备心跳 (device_heartbeats) =================

@extensions_bp.route('/device-heartbeats', methods=['GET'])
def get_device_heartbeats():
    payload, failure = ensure_admin()
    if failure:
        return failure
    if db is None: return jsonify({"error": "DB not connected"}), 500
    device_id = request.args.get('device_id', '').strip()
    query = {"device_id": device_id} if device_id else {}
    heartbeats = list(db.device_heartbeats.find(query).sort('ping_at', -1).limit(100))
    return jsonify([serialize_doc(item) for item in heartbeats])


@extensions_bp.route('/device-heartbeats', methods=['POST'])
def create_device_heartbeat():
    payload, failure = ensure_admin()
    if failure:
        return failure
    if db is None: return jsonify({"error": "DB not connected"}), 500
    data = request.json or {}
    doc = {
        "device_id": data.get("device_id", ""),
        "status": data.get("status", "online"),
        "ping_at": datetime.now(),
        "latency": data.get("latency"),
        "remark": data.get("remark", "")
    }
    result = db.device_heartbeats.insert_one(doc)
    write_audit("CREATE_DEVICE_HEARTBEAT", f"记录设备心跳 {doc['device_id']}", "device_heartbeat", str(result.inserted_id), username=payload.get('user'))
    return jsonify({"success": True, "id": str(result.inserted_id)})


# ================= 报警截图 (alarm_snapshots) =================

@extensions_bp.route('/alarm-snapshots', methods=['GET'])
def get_alarm_snapshots():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    alarm_id = request.args.get('alarm_id', '').strip()
    query = {}
    if alarm_id:
        try:
            query["alarm_id"] = int(alarm_id)
        except ValueError:
            query["alarm_id"] = alarm_id
    snapshots = list(db.alarm_snapshots.find(query).sort('created_at', -1).limit(100))
    return jsonify([serialize_doc(snapshot) for snapshot in snapshots])


# ================= 通知规则 (notification_rules) =================

@extensions_bp.route('/notification-rules', methods=['GET'])
def get_notification_rules():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = payload.get('user')
    rules = list(db.notification_rules.find({"username": username}).sort('updated_at', -1))
    return jsonify([serialize_doc(rule) for rule in rules])


@extensions_bp.route('/notification-rules', methods=['POST'])
def create_notification_rule():
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = payload.get('user')
    data = request.json or {}
    doc = {
        "username": username,
        "device_id": data.get("device_id", ""),
        "alarm_type": data.get("alarm_type", "跌倒"),
        "time_start": data.get("time_start", "00:00"),
        "time_end": data.get("time_end", "23:59"),
        "channels": data.get("channels", []),
        "target_contacts": data.get("target_contacts", []),
        "enabled": data.get("enabled", True),
        "updated_at": datetime.now()
    }
    result = db.notification_rules.insert_one(doc)
    write_audit("CREATE_NOTIFICATION_RULE", f"新增通知规则 {username}", "notification_rule", str(result.inserted_id), username=username)
    return jsonify({"success": True, "id": str(result.inserted_id)})


@extensions_bp.route('/notification-rules/<rule_id>', methods=['PUT'])
def update_notification_rule(rule_id):
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = payload.get('user')
    data = request.json or {}
    data['updated_at'] = datetime.now()
    result = db.notification_rules.update_one(
        {"_id": ObjectId(rule_id), "username": username},
        {"$set": data}
    )
    return jsonify({"success": result.matched_count > 0})


@extensions_bp.route('/notification-rules/<rule_id>', methods=['DELETE'])
def delete_notification_rule(rule_id):
    if db is None: return jsonify({"error": "DB not connected"}), 500
    payload, error = get_current_user()
    if error:
        return jsonify({"error": error}), 401
    username = payload.get('user')
    result = db.notification_rules.delete_one({"_id": ObjectId(rule_id), "username": username})
    return jsonify({"success": result.deleted_count > 0})
