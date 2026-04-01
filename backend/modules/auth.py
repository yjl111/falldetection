import pymongo
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import datetime
import os

# 密钥，用于签名，生产环境应放在环境变量中
SECRET_KEY = "your_secret_key_here_change_this"
TOKEN_MAX_AGE = 86400
_serializer = URLSafeTimedSerializer(SECRET_KEY)


def issue_token(username, role):
    return _serializer.dumps({'user': username, 'role': role})


def decode_token(token, max_age=TOKEN_MAX_AGE):
    try:
        return _serializer.loads(token, max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
    except Exception:
        return None


def get_request_user(request):
    auth_header = request.headers.get('Authorization', '').strip()
    token = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
    elif request.headers.get('X-Auth-Token'):
        token = request.headers.get('X-Auth-Token', '').strip()
    elif request.is_json:
        body = request.get_json(silent=True) or {}
        token = body.get('token', '').strip()

    if not token:
        return None
    return decode_token(token)


def has_role(request, *roles):
    payload = get_request_user(request)
    if not payload:
        return False, None
    return payload.get('role') in roles, payload


def _log_auth_audit(db, action, username, status="success", details=""):
    if db is None:
        return
    try:
        db.audit_logs.insert_one({
            "username": username or "anonymous",
            "action": action,
            "status": status,
            "details": details,
            "target_type": "user",
            "target_id": username,
            "created_at": datetime.datetime.utcnow()
        })
    except Exception as e:
        print(f"[Auth][Audit] 写入失败: {e}")

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
        self.serializer = _serializer
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
            role = "admin" if self.users_collection.count_documents({}) == 0 else "user"
            # 直接存储明文密码
            user_doc = {
                "username": username,
                "password": password,  # 这里直接存储明文，不再是 password_hash
                "role": role,
                "created_at": datetime.datetime.utcnow()
            }
            self.users_collection.insert_one(user_doc)
            _log_auth_audit(self.db, "REGISTER", username, "success", f"用户注册成功，角色={role}")
            return True, f"注册成功，当前角色：{role}"
        except pymongo.errors.DuplicateKeyError:
            _log_auth_audit(self.db, "REGISTER", username, "failed", "用户名已存在")
            return False, "用户名已存在"
        except Exception as e:
            _log_auth_audit(self.db, "REGISTER", username, "failed", str(e))
            return False, f"注册异常: {str(e)}"

    def login(self, username, password, expected_role=None):
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
                role = user.get("role", "user")
                if expected_role and role != expected_role:
                    _log_auth_audit(self.db, "LOGIN", username, "failed", f"登录端口不匹配，账号角色={role}，请求端口={expected_role}")
                    return False, f"该账号无权进入{'管理端' if expected_role == 'admin' else '用户端'}"
                token = issue_token(username, role)
                _log_auth_audit(self.db, "LOGIN", username, "success", "登录成功")
                return True, {"token": token, "username": username, "role": role}
            else:
                _log_auth_audit(self.db, "LOGIN", username, "failed", "用户名或密码错误")
                return False, "用户名或密码错误"
        except Exception as e:
            _log_auth_audit(self.db, "LOGIN", username, "failed", str(e))
            return False, f"登录异常: {str(e)}"

    def verify_token(self, token):
        return decode_token(token) is not None

    def verify_token_data(self, token):
        return decode_token(token)
