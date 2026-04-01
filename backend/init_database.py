"""
MongoDB 数据库初始化脚本
创建所有需要的集合（表）和索引
"""

import pymongo
from datetime import datetime, timedelta
import random

# MongoDB 连接配置
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "fall_detection_db"

def init_database():
    """初始化数据库，创建集合和索引"""
    try:
        # 连接 MongoDB
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        
        # 测试连接
        client.server_info()
        print(f"✅ MongoDB 连接成功")
        print(f"📦 数据库名称: {DB_NAME}")
        print("-" * 60)
        
        # 1. 创建 users 集合（用户表）
        if "users" not in db.list_collection_names():
            db.create_collection("users")
            print("✅ 创建集合: users (用户表)")
        else:
            print("ℹ️  集合已存在: users")
        
        # 为 username 创建唯一索引
        db.users.create_index("username", unique=True)
        print("   ├─ 创建索引: username (唯一)")
        
        # 2. 创建 alarms 集合（报警记录表）
        if "alarms" not in db.list_collection_names():
            db.create_collection("alarms")
            print("✅ 创建集合: alarms (报警记录表)")
        else:
            print("ℹ️  集合已存在: alarms")
        
        # 为 alarms 创建索引
        db.alarms.create_index("id", unique=True)
        db.alarms.create_index("timestamp")
        db.alarms.create_index("status")
        print("   ├─ 创建索引: id (唯一), timestamp, status")
        
        # 3. 创建 alarm_config 集合（报警配置表）
        if "alarm_config" not in db.list_collection_names():
            db.create_collection("alarm_config")
            print("✅ 创建集合: alarm_config (报警配置表)")
        else:
            print("ℹ️  集合已存在: alarm_config")
        
        db.alarm_config.create_index("key", unique=True)
        print("   ├─ 创建索引: key (唯一)")
        
        # 4. 创建 contacts 集合（联系人表）
        if "contacts" not in db.list_collection_names():
            db.create_collection("contacts")
            print("✅ 创建集合: contacts (联系人表)")
        else:
            print("ℹ️  集合已存在: contacts")
        
        db.contacts.create_index("id", unique=True)
        print("   ├─ 创建索引: id (唯一)")
        
        # 5. 创建 system_config 集合（系统配置表）
        if "system_config" not in db.list_collection_names():
            db.create_collection("system_config")
            print("✅ 创建集合: system_config (系统配置表)")
        else:
            print("ℹ️  集合已存在: system_config")
        
        db.system_config.create_index("key", unique=True)
        print("   ├─ 创建索引: key (唯一)")
        
        # 6. 创建 config 集合（通用配置表）
        if "config" not in db.list_collection_names():
            db.create_collection("config")
            print("✅ 创建集合: config (通用配置表)")
        else:
            print("ℹ️  集合已存在: config")
        
        db.config.create_index("key", unique=True)
        print("   ├─ 创建索引: key (唯一)")
        
        # 7. 创建 history 集合（视频历史记录表）
        if "history" not in db.list_collection_names():
            db.create_collection("history")
            print("✅ 创建集合: history (视频历史记录表)")
        else:
            print("ℹ️  集合已存在: history")
        
        db.history.create_index("timestamp")
        db.history.create_index("video_file_id")
        print("   ├─ 创建索引: timestamp, video_file_id")

        # ==================== 新增表初始化 ====================
        
        # 8. 创建 devices 集合（设备与视频源管理表）
        if "devices" not in db.list_collection_names():
            db.create_collection("devices")
            print("✅ 创建集合: devices (设备与视频源管理表)")
        else:
            print("ℹ️  集合已存在: devices")
        db.devices.create_index("device_id", unique=True)
        print("   ├─ 创建索引: device_id (唯一)")

        # 9. 创建 emergency_contacts 集合（紧急联系人扩展表）
        if "emergency_contacts" not in db.list_collection_names():
            db.create_collection("emergency_contacts")
            print("✅ 创建集合: emergency_contacts (紧急联系人扩展表)")
        else:
            print("ℹ️  集合已存在: emergency_contacts")
        db.emergency_contacts.create_index("belong_to_user")
        print("   ├─ 创建索引: belong_to_user")

        # 10. 创建 model_training_logs 集合（模型训练与指标记录表）
        if "model_training_logs" not in db.list_collection_names():
            db.create_collection("model_training_logs")
            print("✅ 创建集合: model_training_logs (模型训练与指标记录表)")
        else:
            print("ℹ️  集合已存在: model_training_logs")
        db.model_training_logs.create_index("version_name", unique=True)
        print("   ├─ 创建索引: version_name (唯一)")

        # 11. 创建 alarm_feedback 集合（误报反馈与数据收集表）
        if "alarm_feedback" not in db.list_collection_names():
            db.create_collection("alarm_feedback")
            print("✅ 创建集合: alarm_feedback (误报反馈与数据收集表)")
        else:
            print("ℹ️  集合已存在: alarm_feedback")
        db.alarm_feedback.create_index("alarm_id")
        print("   ├─ 创建索引: alarm_id")

        # 12. 创建 audit_logs 集合（系统审计与操作日志表）
        if "audit_logs" not in db.list_collection_names():
            db.create_collection("audit_logs")
            print("✅ 创建集合: audit_logs (系统审计与操作日志表)")
        else:
            print("ℹ️  集合已存在: audit_logs")
        db.audit_logs.create_index("created_at")
        db.audit_logs.create_index("username")
        db.audit_logs.create_index("action")
        print("   ├─ 创建索引: created_at")

        # 13. 创建 notification_logs 集合（通知发送日志表）
        if "notification_logs" not in db.list_collection_names():
            db.create_collection("notification_logs")
            print("✅ 创建集合: notification_logs (通知发送日志表)")
        else:
            print("ℹ️  集合已存在: notification_logs")
        db.notification_logs.create_index("alarm_id")
        db.notification_logs.create_index("channel")
        db.notification_logs.create_index("created_at")
        print("   ├─ 创建索引: alarm_id, channel, created_at")

        # 14. 创建 user_profiles 集合（用户资料表）
        if "user_profiles" not in db.list_collection_names():
            db.create_collection("user_profiles")
            print("✅ 创建集合: user_profiles (用户资料表)")
        else:
            print("ℹ️  集合已存在: user_profiles")
        db.user_profiles.create_index("username", unique=True)
        print("   ├─ 创建索引: username (唯一)")

        # 15. 创建 alarm_workorders 集合（报警工单表）
        if "alarm_workorders" not in db.list_collection_names():
            db.create_collection("alarm_workorders")
            print("✅ 创建集合: alarm_workorders (报警工单表)")
        else:
            print("ℹ️  集合已存在: alarm_workorders")
        db.alarm_workorders.create_index("alarm_id")
        db.alarm_workorders.create_index("handler")
        db.alarm_workorders.create_index("created_at")
        print("   ├─ 创建索引: alarm_id, handler, created_at")

        # 16. 创建 user_messages 集合（用户消息表）
        if "user_messages" not in db.list_collection_names():
            db.create_collection("user_messages")
            print("✅ 创建集合: user_messages (用户消息表)")
        else:
            print("ℹ️  集合已存在: user_messages")
        db.user_messages.create_index("username")
        db.user_messages.create_index("is_read")
        db.user_messages.create_index("created_at")
        print("   ├─ 创建索引: username, is_read, created_at")

        # 17. 创建 health_reports 集合（健康报告表）
        if "health_reports" not in db.list_collection_names():
            db.create_collection("health_reports")
            print("✅ 创建集合: health_reports (健康报告表)")
        else:
            print("ℹ️  集合已存在: health_reports")
        db.health_reports.create_index("username")
        db.health_reports.create_index("report_type")
        db.health_reports.create_index("created_at")
        print("   ├─ 创建索引: username, report_type, created_at")

        # 18. 创建 device_heartbeats 集合（设备心跳表）
        if "device_heartbeats" not in db.list_collection_names():
            db.create_collection("device_heartbeats")
            print("✅ 创建集合: device_heartbeats (设备心跳表)")
        else:
            print("ℹ️  集合已存在: device_heartbeats")
        db.device_heartbeats.create_index("device_id")
        db.device_heartbeats.create_index("ping_at")
        print("   ├─ 创建索引: device_id, ping_at")

        # 19. 创建 alarm_snapshots 集合（报警截图表）
        if "alarm_snapshots" not in db.list_collection_names():
            db.create_collection("alarm_snapshots")
            print("✅ 创建集合: alarm_snapshots (报警截图表)")
        else:
            print("ℹ️  集合已存在: alarm_snapshots")
        db.alarm_snapshots.create_index("alarm_id")
        db.alarm_snapshots.create_index("created_at")
        print("   ├─ 创建索引: alarm_id, created_at")

        # 20. 创建 notification_rules 集合（通知规则表）
        if "notification_rules" not in db.list_collection_names():
            db.create_collection("notification_rules")
            print("✅ 创建集合: notification_rules (通知规则表)")
        else:
            print("ℹ️  集合已存在: notification_rules")
        db.notification_rules.create_index("username")
        db.notification_rules.create_index("device_id")
        db.notification_rules.create_index("enabled")
        print("   ├─ 创建索引: username, device_id, enabled")
        
        # 21. GridFS 集合（自动创建，用于存储视频文件）
        print("ℹ️  GridFS 集合: fs.files, fs.chunks (视频文件存储)")
        
        print("-" * 60)
        print("🎉 数据库初始化完成！")
        
        return db
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return None


def insert_sample_data(db):
    """插入示例数据（可选）"""
    if db is None:
        return
    
    print("\n" + "=" * 60)
    print("📝 是否插入示例数据？(y/n): ", end="")
    choice = input().strip().lower()
    
    if choice != 'y':
        print("跳过示例数据插入")
        return
    
    print("-" * 60)
    
    try:
        # 插入系统配置示例
        if db.config.count_documents({}) == 0:
            db.config.insert_many([
                {"key": "accuracy", "value": 94.5, "updated_at": datetime.now()},
                {"key": "uptime", "value": 99.8, "updated_at": datetime.now()}
            ])
            print("✅ 插入配置数据: accuracy, uptime")
        
        # 插入报警配置示例
        if db.alarm_config.count_documents({"key": "main_config"}) == 0:
            db.alarm_config.insert_one({
                "key": "main_config",
                "sound": True,
                "notification": True,
                "email": False,
                "sms": False,
                "time_start": "00:00",
                "time_end": "23:59",
                "contacts": [],
                "updated_at": datetime.now()
            })
            print("✅ 插入默认报警配置")
        
        # 插入联系人示例
        if db.contacts.count_documents({}) == 0:
            db.contacts.insert_many([
                {
                    "id": 1,
                    "name": "张医生",
                    "phone": "138****8888",
                    "email": "zhang@example.com",
                    "created_at": datetime.now()
                },
                {
                    "id": 2,
                    "name": "李护士",
                    "phone": "139****9999",
                    "email": "li@example.com",
                    "created_at": datetime.now()
                }
            ])
            print("✅ 插入示例联系人: 2条")
        
        # 插入模拟报警记录（最近7天）
        if db.alarms.count_documents({}) == 0:
            alarm_types = ["跌倒", "摔倒", "滑倒", "侧向跌倒", "向前跌倒"]
            locations = ["卧室", "客厅", "浴室", "厨房"]
            statuses = ["已处理", "待处理"]
            
            alarms = []
            alarm_id = 1
            
            # 生成过去7天的随机报警记录
            for day in range(7):
                date = datetime.now() - timedelta(days=day)
                num_alarms = random.randint(1, 4)  # 每天1-4条报警
                
                for _ in range(num_alarms):
                    # 随机时间
                    hour = random.randint(0, 23)
                    minute = random.randint(0, 59)
                    timestamp = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    alarms.append({
                        "id": alarm_id,
                        "timestamp": timestamp,
                        "location": random.choice(locations),
                        "type": random.choice(alarm_types),
                        "status": random.choice(statuses),
                        "video_filename": f"fall_{timestamp.strftime('%Y%m%d_%H%M%S')}.mp4",
                        "created_at": timestamp
                    })
                    alarm_id += 1
            
            db.alarms.insert_many(alarms)
            print(f"✅ 插入模拟报警记录: {len(alarms)}条")
        
        # 插入系统设置示例
        if db.system_config.count_documents({"key": "main_settings"}) == 0:
            db.system_config.insert_one({
                "key": "main_settings",
                "detection": {
                    "confidence": 0.30,
                    "iou": 0.45,
                    "areas": {
                        "bedroom": True,
                        "livingroom": True,
                        "bathroom": True,
                        "kitchen": False
                    }
                },
                "storage": {
                    "beforeSeconds": 3,
                    "afterSeconds": 2,
                    "autoClean": "30d"
                },
                "system": {
                    "language": "zh-CN",
                    "theme": "dark",
                    "logs": {
                        "enable": True,
                        "debug": False
                    }
                },
                "advanced": {
                    "gpu": False,
                    "workers": 4,
                    "apiUrl": "http://localhost:5000"
                },
                "updated_at": datetime.now()
            })
            print("✅ 插入默认系统设置")

        # 插入设备管理示例
        if db.devices.count_documents({}) == 0:
            db.devices.insert_many([
                {
                    "device_id": "CAM-001",
                    "name": "客厅主摄像头",
                    "location": "客厅",
                    "source_type": "webcam",
                    "source_url": "0",
                    "status": "online",
                    "framerate": 30,
                    "resolution": "1920x1080",
                    "created_at": datetime.now()
                },
                {
                    "device_id": "CAM-002",
                    "name": "卧室辅助摄像头",
                    "location": "卧室",
                    "source_type": "rtsp",
                    "source_url": "rtsp://192.168.1.22:554/live",
                    "status": "offline",
                    "framerate": 25,
                    "resolution": "1280x720",
                    "created_at": datetime.now()
                }
            ])
            print("✅ 插入示例设备: 2条")

        # 插入紧急联系人示例
        if db.emergency_contacts.count_documents({}) == 0:
            db.emergency_contacts.insert_many([
                {
                    "belong_to_user": "admin",
                    "contact_name": "王女士",
                    "phone": "13700001111",
                    "email": "family1@example.com",
                    "relationship": "子女",
                    "notify_level": 1,
                    "is_active": True,
                    "created_at": datetime.now()
                },
                {
                    "belong_to_user": "admin",
                    "contact_name": "赵护工",
                    "phone": "13600002222",
                    "email": "caregiver@example.com",
                    "relationship": "护工",
                    "notify_level": 2,
                    "is_active": True,
                    "created_at": datetime.now()
                }
            ])
            print("✅ 插入示例紧急联系人: 2条")

        # 插入审计日志示例
        if db.audit_logs.count_documents({}) == 0:
            db.audit_logs.insert_many([
                {
                    "username": "admin",
                    "action": "LOGIN",
                    "details": "管理员登录系统",
                    "target_type": "user",
                    "target_id": "admin",
                    "status": "success",
                    "created_at": datetime.now() - timedelta(minutes=25)
                },
                {
                    "username": "admin",
                    "action": "UPDATE_ALARM_CONFIG",
                    "details": "更新报警配置并启用邮件通知",
                    "target_type": "alarm_config",
                    "target_id": "main_config",
                    "status": "success",
                    "created_at": datetime.now() - timedelta(minutes=15)
                },
                {
                    "username": "admin",
                    "action": "HANDLE_ALARM",
                    "details": "处理报警记录 10001",
                    "target_type": "alarm",
                    "target_id": 10001,
                    "status": "success",
                    "created_at": datetime.now() - timedelta(minutes=5)
                }
            ])
            print("✅ 插入示例审计日志: 3条")

        # 插入通知日志示例
        if db.notification_logs.count_documents({}) == 0:
            db.notification_logs.insert_many([
                {
                    "alarm_id": 10001,
                    "channel": "email",
                    "recipient": "family1@example.com",
                    "success": True,
                    "message": "发送成功",
                    "created_at": datetime.now() - timedelta(minutes=12)
                },
                {
                    "alarm_id": 10001,
                    "channel": "sms",
                    "recipient": "13700001111",
                    "success": True,
                    "message": "发送成功",
                    "created_at": datetime.now() - timedelta(minutes=12)
                },
                {
                    "alarm_id": 10002,
                    "channel": "email",
                    "recipient": "caregiver@example.com",
                    "success": False,
                    "message": "SMTP 认证失败",
                    "created_at": datetime.now() - timedelta(minutes=3)
                }
            ])
            print("✅ 插入示例通知日志: 3条")

        if db.user_profiles.count_documents({}) == 0:
            db.user_profiles.insert_many([
                {
                    "username": "admin",
                    "real_name": "系统管理员",
                    "phone": "13500000000",
                    "address": "上海市浦东新区",
                    "age": 38,
                    "medical_notes": "管理员演示账号",
                    "updated_at": datetime.now()
                },
                {
                    "username": "demo_user",
                    "real_name": "张三",
                    "phone": "13612345678",
                    "address": "上海市徐汇区",
                    "age": 72,
                    "medical_notes": "轻度高血压，需关注夜间跌倒风险",
                    "updated_at": datetime.now()
                }
            ])
            print("✅ 插入示例用户资料: 2条")

        if db.alarm_workorders.count_documents({}) == 0:
            db.alarm_workorders.insert_many([
                {
                    "alarm_id": 10001,
                    "handler": "admin",
                    "result": "已确认真实跌倒",
                    "comment": "已电话联系家属并安排护工上门查看",
                    "status": "closed",
                    "created_at": datetime.now() - timedelta(minutes=20),
                    "handled_at": datetime.now() - timedelta(minutes=18)
                },
                {
                    "alarm_id": 10002,
                    "handler": "admin",
                    "result": "误报",
                    "comment": "用户只是弯腰拾物，非真实跌倒",
                    "status": "closed",
                    "created_at": datetime.now() - timedelta(minutes=8),
                    "handled_at": datetime.now() - timedelta(minutes=6)
                }
            ])
            print("✅ 插入示例报警工单: 2条")

        if db.user_messages.count_documents({}) == 0:
            db.user_messages.insert_many([
                {
                    "username": "demo_user",
                    "title": "报警处理反馈",
                    "content": "您 10:15 的跌倒报警已由管理员处理，请注意休息并保持联系畅通。",
                    "type": "alarm",
                    "is_read": False,
                    "created_at": datetime.now() - timedelta(minutes=12)
                },
                {
                    "username": "demo_user",
                    "title": "系统提醒",
                    "content": "建议完善个人资料与紧急联系人信息，以便发生报警时快速通知。",
                    "type": "system",
                    "is_read": True,
                    "created_at": datetime.now() - timedelta(days=1)
                }
            ])
            print("✅ 插入示例用户消息: 2条")

        if db.health_reports.count_documents({}) == 0:
            db.health_reports.insert_many([
                {
                    "username": "demo_user",
                    "report_type": "weekly",
                    "start_date": datetime.now() - timedelta(days=7),
                    "end_date": datetime.now(),
                    "fall_count": 3,
                    "false_positive_count": 1,
                    "high_risk_period": "20:00-24:00",
                    "summary": "本周夜间跌倒风险偏高，建议加强晚间陪护与巡查。",
                    "created_at": datetime.now()
                },
                {
                    "username": "demo_user",
                    "report_type": "daily",
                    "start_date": datetime.now() - timedelta(days=1),
                    "end_date": datetime.now(),
                    "fall_count": 1,
                    "false_positive_count": 0,
                    "high_risk_period": "08:00-12:00",
                    "summary": "今日整体状态平稳，仅有一次真实报警。",
                    "created_at": datetime.now()
                }
            ])
            print("✅ 插入示例健康报告: 2条")

        if db.device_heartbeats.count_documents({}) == 0:
            db.device_heartbeats.insert_many([
                {
                    "device_id": "CAM-001",
                    "status": "online",
                    "ping_at": datetime.now() - timedelta(minutes=1),
                    "latency": 32,
                    "remark": "运行正常"
                },
                {
                    "device_id": "CAM-002",
                    "status": "offline",
                    "ping_at": datetime.now() - timedelta(minutes=6),
                    "latency": None,
                    "remark": "设备离线待检查"
                }
            ])
            print("✅ 插入示例设备心跳: 2条")

        if db.alarm_snapshots.count_documents({}) == 0:
            db.alarm_snapshots.insert_many([
                {
                    "alarm_id": 10001,
                    "filename": "snapshot_10001.jpg",
                    "filepath": "evidence/snapshot_10001.jpg",
                    "snapshot_type": "alarm_frame",
                    "created_at": datetime.now() - timedelta(minutes=11)
                },
                {
                    "alarm_id": 10002,
                    "filename": "snapshot_10002.jpg",
                    "filepath": "evidence/snapshot_10002.jpg",
                    "snapshot_type": "alarm_frame",
                    "created_at": datetime.now() - timedelta(minutes=4)
                }
            ])
            print("✅ 插入示例报警截图: 2条")

        if db.notification_rules.count_documents({}) == 0:
            db.notification_rules.insert_many([
                {
                    "username": "demo_user",
                    "device_id": "CAM-001",
                    "alarm_type": "跌倒",
                    "time_start": "00:00",
                    "time_end": "23:59",
                    "channels": ["sms", "email"],
                    "target_contacts": ["王女士", "赵护工"],
                    "enabled": True,
                    "updated_at": datetime.now()
                },
                {
                    "username": "demo_user",
                    "device_id": "CAM-002",
                    "alarm_type": "跌倒",
                    "time_start": "20:00",
                    "time_end": "08:00",
                    "channels": ["sms"],
                    "target_contacts": ["赵护工"],
                    "enabled": True,
                    "updated_at": datetime.now()
                }
            ])
            print("✅ 插入示例通知规则: 2条")
        
        print("-" * 60)
        print("🎉 示例数据插入完成！")
        
    except Exception as e:
        print(f"❌ 插入示例数据失败: {e}")


def show_database_status(db):
    """显示数据库状态"""
    if db is None:
        return
    
    print("\n" + "=" * 60)
    print("📊 数据库状态")
    print("-" * 60)
    
    collections = {
        "users": "用户表",
        "alarms": "报警记录表",
        "alarm_config": "报警配置表",
        "contacts": "联系人表",
        "system_config": "系统配置表",
        "config": "通用配置表",
        "history": "视频历史记录表",
        "devices": "设备管理表",
        "emergency_contacts": "紧急联系人表",
        "model_training_logs": "训练日志表",
        "alarm_feedback": "误报反馈表",
        "audit_logs": "审计日志表",
        "notification_logs": "通知日志表",
        "user_profiles": "用户资料表",
        "alarm_workorders": "报警工单表",
        "user_messages": "用户消息表",
        "health_reports": "健康报告表",
        "device_heartbeats": "设备心跳表",
        "alarm_snapshots": "报警截图表",
        "notification_rules": "通知规则表"
    }
    
    for coll_name, coll_desc in collections.items():
        count = db[coll_name].count_documents({})
        print(f"{coll_desc:15} ({coll_name:15}): {count:5} 条记录")
    
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Fall Detection System - 数据库初始化工具")
    print("=" * 60 + "\n")
    
    # 初始化数据库
    db = init_database()
    
    # 插入示例数据（可选）
    if db is not None:
        insert_sample_data(db)
        show_database_status(db)
    
    print("\n✅ 初始化完成！现在可以启动后端服务了。\n")
