"""
报警管理模块
提供报警配置、联系人管理和报警历史记录功能
"""

from flask import Blueprint, jsonify, request
import pymongo
from datetime import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import time as _time_module

alarms_bp = Blueprint('alarms', __name__, url_prefix='/api/alarms')

# MongoDB 连接
mongo_client = None
db = None


def log_audit(action, username="system", details="", target_type="", target_id=None, status="success"):
    """写入审计日志，失败时静默降级为控制台输出"""
    if db is None:
        print(f"[Audit] skip {action}: DB not connected")
        return
    try:
        db.audit_logs.insert_one({
            "username": username or "system",
            "action": action,
            "details": details,
            "target_type": target_type,
            "target_id": target_id,
            "status": status,
            "created_at": datetime.now()
        })
    except Exception as e:
        print(f"[Audit] 写入失败: {e}")


def log_notification(channel, recipient, success, message="", alarm_id=None):
    """记录通知发送结果"""
    if db is None:
        print(f"[Notification Log] skip {channel}: DB not connected")
        return
    try:
        db.notification_logs.insert_one({
            "alarm_id": alarm_id,
            "channel": channel,
            "recipient": recipient,
            "success": bool(success),
            "message": message,
            "created_at": datetime.now()
        })
    except Exception as e:
        print(f"[Notification Log] 写入失败: {e}")

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
                    "sms_access_key_id": config.get('sms_access_key_id', ''),
                    "sms_access_key_secret": config.get('sms_access_key_secret', ''),
                    "sms_sign_name": config.get('sms_sign_name', ''),
                    "sms_template_code": config.get('sms_template_code', ''),
                    "time_start": config.get('time_start', '00:00'),
                    "time_end": config.get('time_end', '23:59'),
                    "smtp_host": config.get('smtp_host', ''),
                    "smtp_port": config.get('smtp_port', 465),
                    "smtp_user": config.get('smtp_user', ''),
                    "smtp_password": config.get('smtp_password', ''),
                    "contacts": config.get('contacts', []),
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
            print(f"[Alarm Config] 更新配置: {config}")
            log_audit(
                action="UPDATE_ALARM_CONFIG",
                details="更新报警配置",
                target_type="alarm_config",
                target_id="main_config"
            )
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
                    "sms_access_key_id": config.get('sms_access_key_id', ''),
                    "sms_access_key_secret": config.get('sms_access_key_secret', ''),
                    "sms_sign_name": config.get('sms_sign_name', ''),
                    "sms_template_code": config.get('sms_template_code', ''),
                    "time_start": config.get('time_start', '00:00'),
                    "time_end": config.get('time_end', '23:59'),
                    "smtp_host": config.get('smtp_host', ''),
                    "smtp_port": config.get('smtp_port', 465),
                    "smtp_user": config.get('smtp_user', ''),
                    "smtp_password": config.get('smtp_password', ''),
                    "contacts": config.get('contacts', [])
                })
            else:
                # 返回默认配置
                return jsonify({
                    "sound": True,
                    "notification": True,
                    "email": False,
                    "sms": False,
                    "sms_access_key_id": "",
                    "sms_access_key_secret": "",
                    "sms_sign_name": "",
                    "sms_template_code": "",
                    "time_start": "00:00",
                    "time_end": "23:59",
                    "smtp_host": "",
                    "smtp_port": 465,
                    "smtp_user": "",
                    "smtp_password": "",
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
            log_audit(
                action="HANDLE_ALARM",
                details=f"处理报警记录 {alarm_id}",
                target_type="alarm",
                target_id=alarm_id
            )
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
            log_audit(
                action="ADD_CONTACT",
                details=f"新增联系人 {contact.get('name', '')}",
                target_type="contact",
                target_id=contact.get('id')
            )
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
            if result.deleted_count > 0:
                log_audit(
                    action="DELETE_CONTACT",
                    details=f"删除联系人 {contact_id}",
                    target_type="contact",
                    target_id=contact_id
                )
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


def _send_sms_notify(cfg, location, alarm_type, phones=None, alarm_id=None):
    """通过阿里云官方 SDK 发送报警短信"""
    access_key_id = cfg.get('sms_access_key_id', '')
    access_key_secret = cfg.get('sms_access_key_secret', '')
    sign_name = cfg.get('sms_sign_name', '')
    template_code = cfg.get('sms_template_code', '')

    if not access_key_id or not access_key_secret or not sign_name or not template_code:
        print("[SMS] 阿里云 SMS 未配置，跳过短信发送")
        log_notification("sms", "", False, "SMS 未配置", alarm_id=alarm_id)
        return

    if phones is None:
        if db is not None:
            all_contacts = list(db.contacts.find({}, {"_id": 0}))
        else:
            all_contacts = []
        phones = [c['phone'] for c in all_contacts if c.get('phone', '').strip()]

    if not phones:
        print("[SMS] 无有效手机号，跳过发送")
        log_notification("sms", "", False, "无有效手机号", alarm_id=alarm_id)
        return

    try:
        from alibabacloud_dysmsapi20170525 import models as sms_models
        from alibabacloud_dysmsapi20170525.client import Client as SmsClient
        from alibabacloud_tea_openapi import models as open_api_models
    except ImportError:
        print("[SMS] 请先安装 SDK: pip install alibabacloud_dysmsapi20170525")
        log_notification("sms", "", False, "缺少阿里云 SMS SDK", alarm_id=alarm_id)
        return

    timestamp = _time_module.strftime('%Y-%m-%d %H:%M', _time_module.localtime())
    code_value = f"{timestamp} {location}检测到{alarm_type}"
    template_param = json.dumps({"code": code_value}, ensure_ascii=False, separators=(',', ':'))

    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint='dysmsapi.aliyuncs.com'
    )
    client = SmsClient(config)

    for phone in phones:
        try:
            send_req = sms_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=sign_name,
                template_code=template_code,
                template_param=template_param
            )
            resp = client.send_sms(send_req)
            code = resp.body.code if resp.body else 'UNKNOWN'
            message = resp.body.message if resp.body else ''
            if code == 'OK':
                print(f"[SMS] ✅ 短信已发送至: {phone}")
                log_notification("sms", phone, True, "发送成功", alarm_id=alarm_id)
            else:
                print(f"[SMS] ❌ 发送失败 {phone}: Code={code} Message={message}")
                log_notification("sms", phone, False, f"Code={code} Message={message}", alarm_id=alarm_id)
        except Exception as e:
            print(f"[SMS] ❌ 发送异常 {phone}: {e}")
            log_notification("sms", phone, False, str(e), alarm_id=alarm_id)


@alarms_bp.route('/sms/test', methods=['POST'])
def test_sms():
    """发送测试短信"""
    body = request.get_json(silent=True) or {}
    access_key_id = body.get('access_key_id') or ''
    access_key_secret = body.get('access_key_secret') or ''
    sign_name = body.get('sign_name') or ''
    template_code = body.get('template_code') or ''

    if not access_key_id and db is not None:
        cfg = db.alarm_config.find_one({"key": "main_config"}) or {}
        access_key_id = cfg.get('sms_access_key_id', '')
        access_key_secret = cfg.get('sms_access_key_secret', '')
        sign_name = cfg.get('sms_sign_name', '')
        template_code = cfg.get('sms_template_code', '')

    if not access_key_id or not access_key_secret or not sign_name or not template_code:
        return jsonify({"success": False, "message": "SMS 未配置，请填写 AccessKey 和模板信息"})

    if db is not None:
        all_contacts = list(db.contacts.find({}, {"_id": 0}))
    else:
        all_contacts = []
    phones = [c['phone'] for c in all_contacts if c.get('phone', '').strip()]
    if not phones:
        return jsonify({"success": False, "message": "无有效手机号，请先添加含手机号的联系人"})

    test_cfg = {
        'sms_access_key_id': access_key_id,
        'sms_access_key_secret': access_key_secret,
        'sms_sign_name': sign_name,
        'sms_template_code': template_code,
    }
    try:
        _send_sms_notify(test_cfg, "测试位置", "测试短信", phones=phones)
        return jsonify({"success": True, "message": f"✅ 测试短信已发送至 {phones}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ 发送失败: {str(e)}"})


def _send_email_notify(cfg, location, alarm_type, alarm_id=None):
    """通过 SMTP 向所有有邮箱的联系人发送报警邮件"""
    smtp_host = cfg.get('smtp_host', '')
    smtp_port = int(cfg.get('smtp_port', 465))
    smtp_user = cfg.get('smtp_user', '')
    smtp_password = cfg.get('smtp_password', '')

    if not smtp_host or not smtp_user or not smtp_password:
        print("[Email] SMTP 未配置，跳过邮件发送")
        log_notification("email", "", False, "SMTP 未配置", alarm_id=alarm_id)
        return

    # 直接从 contacts 集合读，避免与 alarm_config 不同步
    if db is not None:
        all_contacts = list(db.contacts.find({}, {"_id": 0}))
    else:
        all_contacts = cfg.get('contacts', [])
    recipients = [c['email'] for c in all_contacts if c.get('email', '').strip()]

    if not recipients:
        print("[Email] 无有效收件人邮箱，跳过发送（请先添加含有邮箱的联系人）")
        log_notification("email", "", False, "无有效邮箱联系人", alarm_id=alarm_id)
        return

    print(f"[Email] 准备发送至: {recipients}, SMTP: {smtp_host}:{smtp_port}, 用户: {smtp_user}")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    subject = f"⚠️ 跌倒报警通知 - {timestamp}"
    body = (
        f"<h2 style='color:red'>⚠️ 跌倒事件报警</h2>"
        f"<p><b>时间：</b>{timestamp}</p>"
        f"<p><b>位置：</b>{location}</p>"
        f"<p><b>类型：</b>{alarm_type}</p>"
        f"<p>请及时处理。</p>"
    )

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = ', '.join(recipients)
        msg.attach(MIMEText(body, 'html', 'utf-8'))

        ctx = ssl.create_default_context()
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=ctx, timeout=10) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipients, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls(context=ctx)
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipients, msg.as_string())

        print(f"[Email] ✅ 报警邮件已发送至: {recipients}")
        for recipient in recipients:
            log_notification("email", recipient, True, "发送成功", alarm_id=alarm_id)
    except Exception as e:
        print(f"[Email] ❌ 邮件发送失败: {e}")
        for recipient in recipients:
            log_notification("email", recipient, False, str(e), alarm_id=alarm_id)


@alarms_bp.route('/email/test', methods=['POST'])
def test_email():
    """发送测试邮件（参数优先使用请求体，其次读 DB）"""
    body = request.get_json(silent=True) or {}
    
    # 优先使用前端直接传入的参数
    smtp_host = body.get('smtp_host') or ''
    smtp_port = int(body.get('smtp_port') or 465)
    smtp_user = body.get('smtp_user') or ''
    smtp_password = body.get('smtp_password') or ''

    # 若前端未传，则读 DB
    if not smtp_host and db is not None:
        cfg = db.alarm_config.find_one({"key": "main_config"}) or {}
        smtp_host = cfg.get('smtp_host', '')
        smtp_port = int(cfg.get('smtp_port', 465))
        smtp_user = cfg.get('smtp_user', '')
        smtp_password = cfg.get('smtp_password', '')

    if not smtp_host or not smtp_user or not smtp_password:
        return jsonify({"success": False, "message": "SMTP 未配置，请先选择服务商并填写邮箱/授权码"})

    if db is not None:
        all_contacts = list(db.contacts.find({}, {"_id": 0}))
    else:
        all_contacts = []
    recipients = [c['email'] for c in all_contacts if c.get('email', '').strip()]
    if not recipients:
        return jsonify({"success": False, "message": "无有效收件人，请先添加含邮箱的联系人"})

    test_cfg = {
        'smtp_host': smtp_host,
        'smtp_port': smtp_port,
        'smtp_user': smtp_user,
        'smtp_password': smtp_password
    }
    try:
        _send_email_notify(test_cfg, "测试位置", "测试邮件")
        return jsonify({"success": True, "message": f"✅ 测试邮件已发送至 {recipients}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ 发送失败: {str(e)}"})


def save_alarm_record(location="未知", alarm_type="跌倒"):
    """由检测模块调用，将跌倒事件写入报警集合，并按配置发送邮件"""
    if db is None:
        return
    try:
        import time as _time
        alarm_id = int(_time.time() * 1000) % 2147483647
        db.alarms.insert_one({
            "id": alarm_id,
            "timestamp": datetime.now(),
            "location": location,
            "type": alarm_type,
            "status": "待处理"
        })
        print(f"[Alarms] 报警记录已写入: {alarm_type} @ {location}")
        log_audit(
            action="CREATE_ALARM",
            details=f"新增报警 {alarm_type} @ {location}",
            target_type="alarm",
            target_id=alarm_id
        )

        # 读取配置，按需触发邮件/短信
        cfg = db.alarm_config.find_one({"key": "main_config"}) or {}
        import threading
        if cfg.get('email', False):
            threading.Thread(target=_send_email_notify, args=(cfg, location, alarm_type, alarm_id), daemon=True).start()
        if cfg.get('sms', False):
            threading.Thread(target=_send_sms_notify, args=(cfg, location, alarm_type, None, alarm_id), daemon=True).start()
    except Exception as e:
        print(f"[Alarms] 写入报警记录失败: {e}")
