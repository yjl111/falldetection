import pymongo
# import hashlib # 不需要 hash 库了
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import datetime
import os

# 密钥，用于签名，生产环境应放在环境变量中
SECRET_KEY = "your_secret_key_here_change_this"

class AuthModule:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="fall_detection_db"):
        # 兼容性处理：如果传入的是旧版 app.py 中的 SQLite 文件路径，则忽略它并使用默认 MongoDB 库名
        if db_name and (db_name.endswith('.db') or os.sep in db_name):
             print(f"[Auth] 提示: 检测到旧版 SQLite 路径参数，已自动切换为 MongoDB 默认库 'fall_detection_db'")
             db_name = "fall_detection_db"

        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.users_collection = None
        # 初始化序列化器
        self.serializer = URLSafeTimedSerializer(SECRET_KEY)
        self._init_db()

    def _init_db(self):
        try:
            # 连接 MongoDB
            self.client = pymongo.MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000)
            self.db = self.client[self.db_name]
            self.users_collection = self.db["users"]
            
            # 创建唯一索引以确保用户名唯一
            self.users_collection.create_index("username", unique=True)
            
            # 测试连接
            self.client.server_info()
            print("[Auth] ✅ MongoDB 用户数据库连接成功")
        except Exception as e:
            print(f"[Auth] ❌ MongoDB 连接失败: {e}")
            self.client = None
            self.users_collection = None

    # 删除 _hash_password 方法，因为不再需要

    def register(self, username, password):
        # 必须显式通过 is None 判断，并提示数据库状态
        if self.users_collection is None:
            return False, "数据库未连接，请检查 MongoDB 是否启动"
        
        # 增加非空校验，防止报错
        if not username or not password:
             return False, "用户名或密码不能为空"
            
        try:
            # 直接存储明文密码
            user_doc = {
                "username": username,
                "password": password,  # 这里直接存储明文，不再是 password_hash
                "created_at": datetime.datetime.utcnow()
            }
            self.users_collection.insert_one(user_doc)
            return True, "注册成功"
        except pymongo.errors.DuplicateKeyError:
            return False, "用户名已存在"
        except Exception as e:
            return False, f"注册异常: {str(e)}"

    def login(self, username, password):
        # 登录同样增加校验
        if self.users_collection is None:
            return False, "数据库未连接，请检查 MongoDB 是否启动"

        if not username or not password:
             return False, "用户名或密码不能为空"

        try:
            # 从 MongoDB 查询用户
            user = self.users_collection.find_one({"username": username})
            
            # 直接比对明文密码
            # 注意：字段名现在是 "password"
            if user and user.get("password") == password:
                # 生成 Token
                token = self.serializer.dumps({'user': username})
                return True, token
            else:
                return False, "用户名或密码错误"
        except Exception as e:
            return False, f"登录异常: {str(e)}"

    def verify_token(self, token):
        try:
            # 验证 Token，有效期 24 小时 (86400 秒)
            self.serializer.loads(token, max_age=86400)
            return True
        except (SignatureExpired, BadSignature):
            return False
        except Exception:
            return False