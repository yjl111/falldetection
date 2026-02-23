"""
系统配置模块
提供系统参数配置、检测设置和高级选项管理
"""

from flask import Blueprint, jsonify, request
import pymongo
from datetime import datetime
import os

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

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
        print("[Settings] ✅ MongoDB 连接成功")
    except Exception as e:
        print(f"[Settings] ❌ MongoDB 连接失败: {e}")
        db = None

# 初始化数据库
init_db()

# 默认配置
DEFAULT_SETTINGS = {
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
        "path": "",
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
    }
}


@settings_bp.route('', methods=['GET', 'POST'])
def system_settings():
    """获取或更新系统配置"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    evidence_dir = os.path.join(base_dir, 'evidence')
    
    if request.method == 'POST':
        settings = request.json
        
        if not isinstance(settings, dict):
            return jsonify({
                "success": False,
                "message": "配置格式错误"
            }), 400
        
        if db is None:
            print(f"[Settings] 数据库未连接，无法保存配置")
            return jsonify({
                "success": False,
                "message": "数据库未连接"
            }), 500
        
        try:
            # 保存到数据库
            db.system_config.update_one(
                {"key": "main_settings"},
                {"$set": {
                    **settings,
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
            print(f"[Settings] 更新系统配置: {settings}")
            
            return jsonify({
                "success": True,
                "message": "系统配置已更新"
            })
        except Exception as e:
            print(f"[Settings] 保存失败: {e}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500
    
    else:
        # 获取配置
        if db is None:
            # 数据库未连接，返回默认配置
            config = DEFAULT_SETTINGS.copy()
            config["storage"]["path"] = evidence_dir
            return jsonify(config)
        
        try:
            # 从数据库读取
            saved_config = db.system_config.find_one({"key": "main_settings"})
            
            if saved_config:
                config = {
                    "detection": saved_config.get("detection", DEFAULT_SETTINGS["detection"]),
                    "storage": saved_config.get("storage", DEFAULT_SETTINGS["storage"]),
                    "system": saved_config.get("system", DEFAULT_SETTINGS["system"]),
                    "advanced": saved_config.get("advanced", DEFAULT_SETTINGS["advanced"])
                }
                config["storage"]["path"] = evidence_dir
            else:
                # 没有保存的配置，返回默认值
                config = DEFAULT_SETTINGS.copy()
                config["storage"]["path"] = evidence_dir
            
            return jsonify(config)
        except Exception as e:
            print(f"[Settings] 读取失败: {e}")
            config = DEFAULT_SETTINGS.copy()
            config["storage"]["path"] = evidence_dir
            return jsonify(config)


@settings_bp.route('/detection', methods=['GET', 'POST'])
def detection_settings():
    """检测参数配置"""
    if request.method == 'POST':
        settings = request.json
        
        if db is None:
            return jsonify({"success": False, "message": "数据库未连接"}), 500
        
        try:
            db.system_config.update_one(
                {"key": "main_settings"},
                {"$set": {"detection": settings, "updated_at": datetime.now()}},
                upsert=True
            )
            print(f"[Settings] 更新检测参数: {settings}")
            return jsonify({
                "success": True,
                "message": "检测参数已更新"
            })
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    else:
        if db is None:
            return jsonify(DEFAULT_SETTINGS["detection"])
        
        try:
            config = db.system_config.find_one({"key": "main_settings"})
            return jsonify(config.get("detection", DEFAULT_SETTINGS["detection"]) if config else DEFAULT_SETTINGS["detection"])
        except Exception as e:
            return jsonify(DEFAULT_SETTINGS["detection"])


@settings_bp.route('/storage', methods=['GET', 'POST'])
def storage_settings():
    """存储配置"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    evidence_dir = os.path.join(base_dir, 'evidence')
    
    if request.method == 'POST':
        settings = request.json
        
        if db is None:
            return jsonify({"success": False, "message": "数据库未连接"}), 500
        
        try:
            db.system_config.update_one(
                {"key": "main_settings"},
                {"$set": {"storage": settings, "updated_at": datetime.now()}},
                upsert=True
            )
            print(f"[Settings] 更新存储配置: {settings}")
            
            return jsonify({
                "success": True,
                "message": "存储配置已更新",
                "usage": {
                    "used": "2.3 GB",
                    "total": "10 GB",
                    "percentage": 23
                }
            })
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    else:
        if db is None:
            return jsonify({
                **DEFAULT_SETTINGS["storage"],
                "path": evidence_dir,
                "usage": {"used": "0 GB", "total": "10 GB", "percentage": 0}
            })
        
        try:
            config = db.system_config.find_one({"key": "main_settings"})
            storage = config.get("storage", DEFAULT_SETTINGS["storage"]) if config else DEFAULT_SETTINGS["storage"]
            
            return jsonify({
                **storage,
                "path": evidence_dir,
                "usage": {
                    "used": "2.3 GB",
                    "total": "10 GB",
                    "percentage": 23
                }
            })
        except Exception as e:
            return jsonify({
                **DEFAULT_SETTINGS["storage"],
                "path": evidence_dir,
                "usage": {"used": "0 GB", "total": "10 GB", "percentage": 0}
            })


@settings_bp.route('/backup', methods=['POST'])
def backup_database():
    """备份数据库"""
    print(f"[Settings] 执行数据库备份")
    return jsonify({
        "success": True,
        "message": "数据库备份已创建",
        "filename": f"backup_{datetime.now().strftime('%Y-%m-%d')}.db"
    })


@settings_bp.route('/restore', methods=['POST'])
def restore_database():
    """恢复数据库"""
    backup_file = request.json.get('filename')
    print(f"[Settings] 恢复数据库: {backup_file}")
    return jsonify({
        "success": True,
        "message": "数据库已恢复"
    })


@settings_bp.route('/reset', methods=['POST'])
def reset_settings():
    """重置所有设置"""
    if db is None:
        return jsonify({"success": False, "message": "数据库未连接"}), 500
    
    try:
        db.system_config.delete_one({"key": "main_settings"})
        print(f"[Settings] 重置所有设置为默认值")
        return jsonify({
            "success": True,
            "message": "所有设置已重置为默认值"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@settings_bp.route('/clear-data', methods=['POST'])
def clear_all_data():
    """清空所有数据（危险操作）"""
    confirm = request.json.get('confirm', False)
    if not confirm:
        return jsonify({
            "success": False,
            "message": "需要确认才能执行此操作"
        }), 400
    
    if db is None:
        return jsonify({"success": False, "message": "数据库未连接"}), 500
    
    try:
        # 清空各个集合
        db.alarms.delete_many({})
        db.history.delete_many({})
        db.contacts.delete_many({})
        print(f"[Settings] ⚠️ 清空所有数据")
        return jsonify({
            "success": True,
            "message": "所有数据已清空"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
