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
        
        # 8. GridFS 集合（自动创建，用于存储视频文件）
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
        "history": "视频历史记录表"
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
