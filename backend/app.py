import os
import cv2
import threading
import time
import shutil
import tkinter as tk
import logging
from datetime import datetime
import pymongo
from openai import OpenAI
from tkinter import filedialog
from flask import Flask, Response, jsonify, request, render_template
from flask_cors import CORS
from ultralytics import YOLO
from werkzeug.utils import secure_filename

# 导入模块
try:
    from modules.storage import StorageModule
except ImportError:
    print("⚠️ 警告: 未找到 modules.storage，视频留证功能将不可用。")
    StorageModule = None

# 【新增】导入认证模块
from modules.auth import AuthModule
from modules.auth import has_role

# 【新增】导入功能模块蓝图
from modules.statistics import statistics_bp
from modules.alarms import alarms_bp, save_alarm_record
from modules.settings import settings_bp
from modules.extensions import extensions_bp

# ================= 配置区域 =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIST = os.path.join(BASE_DIR, '..', 'frontend', 'dist')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
MODEL_PATH = os.path.join(BASE_DIR, 'best.pt')
EVIDENCE_DIR = os.path.join(BASE_DIR, 'evidence')
FALL_LABELS = ['fall', 'falling', 'down', 'faint', 'lying', 'accident', 'fallen']

def load_local_env():
    """轻量加载 .env，避免强依赖 python-dotenv"""
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"[Config] 读取 .env 失败: {e}")

load_local_env()

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '').strip()

# 初始化 OpenAI 客户端
deepseek_client = None
if DEEPSEEK_API_KEY:
    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )
else:
    print("[Config] 未检测到 DEEPSEEK_API_KEY，AI 分析功能将不可用。")

for path in [UPLOAD_FOLDER, EVIDENCE_DIR]:
    if not os.path.exists(path): os.makedirs(path)

# ================= 日志优化 =================
class NoPollingFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if 'GET /api/train/metrics' in msg: return False
        if 'GET /api/data' in msg: return False
        if 'GET /api/alarm' in msg: return False
        if 'GET /video_feed' in msg: return False 
        return True

logging.getLogger('werkzeug').addFilter(NoPollingFilter())

# ================= Flask 初始化 =================
app = Flask(__name__, 
            static_folder=os.path.join(FRONTEND_DIST, 'assets'), 
            template_folder=FRONTEND_DIST)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ================= 注册蓝图 =================
app.register_blueprint(statistics_bp)
app.register_blueprint(alarms_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(extensions_bp)

# ================= 模块初始化 =================
# 使用条件初始化，避免多次导入时重复初始化
if 'auth_module' not in globals():
    auth_module = AuthModule(db_name=os.path.join(BASE_DIR, 'users.db'))

if 'storage' not in globals():
    storage = None
    if StorageModule:
        storage = StorageModule(save_dir=EVIDENCE_DIR, buffer_seconds=3, after_seconds=2, fps=30)

# ================= 模块 1: 训练管理器 =================
class TrainingManager:
    def __init__(self):
        self.is_training = False
        self.stop_requested = False
        self.thread = None
        self.metrics = {"epochs": [], "box_loss": [], "cls_loss": [], "map50": [], "precision": [], "recall": []}
        self.mongo_client = None
        self.db = None
        self.current_log_id = None
        self._init_db()

    def _init_db(self):
        try:
            self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
            self.db = self.mongo_client["fall_detection_db"]
            self.mongo_client.server_info()
        except Exception as e:
            print(f"[Training] MongoDB 连接失败，训练日志将仅输出到控制台: {e}")
            self.db = None

    def reset(self):
        self.metrics = {"epochs": [], "box_loss": [], "cls_loss": [], "map50": [], "precision": [], "recall": []}
        self.stop_requested = False

    def _create_training_log(self, data_path, epochs, batch, imgsz, optimizer, lr0, base_model):
        if self.db is None:
            self.current_log_id = None
            return
        try:
            version_name = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result = self.db.model_training_logs.insert_one({
                "version_name": version_name,
                "base_model": base_model,
                "dataset_path": data_path,
                "epochs": epochs,
                "batch": batch,
                "imgsz": imgsz,
                "optimizer": optimizer,
                "lr0": lr0,
                "start_time": datetime.now(),
                "status": "running",
                "metrics": {},
                "weight_path": ""
            })
            self.current_log_id = result.inserted_id
        except Exception as e:
            print(f"[Training] 创建训练日志失败: {e}")
            self.current_log_id = None

    def _finalize_training_log(self, status, weight_path=""):
        if self.db is None or self.current_log_id is None:
            return
        try:
            metrics = {
                "best_map50": max(self.metrics["map50"]) if self.metrics["map50"] else 0,
                "best_precision": max(self.metrics["precision"]) if self.metrics["precision"] else 0,
                "best_recall": max(self.metrics["recall"]) if self.metrics["recall"] else 0,
                "final_box_loss": self.metrics["box_loss"][-1] if self.metrics["box_loss"] else 0,
                "final_cls_loss": self.metrics["cls_loss"][-1] if self.metrics["cls_loss"] else 0
            }
            self.db.model_training_logs.update_one(
                {"_id": self.current_log_id},
                {"$set": {
                    "status": status,
                    "end_time": datetime.now(),
                    "metrics": metrics,
                    "weight_path": weight_path
                }}
            )
        except Exception as e:
            print(f"[Training] 更新训练日志失败: {e}")
        finally:
            self.current_log_id = None

    def on_train_epoch_end(self, trainer):
        if self.stop_requested:
            trainer.stop = True
            return
        epoch = trainer.epoch + 1
        if hasattr(trainer, 'loss_items'):
            losses = trainer.loss_items.cpu().numpy()
            box_loss = round(float(losses[0]), 4)
            cls_loss = round(float(losses[1]), 4)
        else: box_loss, cls_loss = 0, 0
        metrics = trainer.metrics
        map50 = round(float(metrics.get("metrics/mAP50(B)", 0)), 4)
        precision = round(float(metrics.get("metrics/precision(B)", 0)), 4)
        recall = round(float(metrics.get("metrics/recall(B)", 0)), 4)
        self.metrics["epochs"].append(epoch)
        self.metrics["box_loss"].append(box_loss)
        self.metrics["cls_loss"].append(cls_loss)
        self.metrics["map50"].append(map50)
        self.metrics["precision"].append(precision)
        self.metrics["recall"].append(recall)
        print(f"[Training] Epoch {epoch}: Loss={box_loss}, mAP50={map50}")

    def _train_task(self, data_path, epochs, batch, imgsz=640, optimizer='Adam', lr0=0.01):
        try:
            self.is_training = True
            self.reset()
            
            # 优化：使用本地预训练权重，避免网络下载
            pretrained_weights = 'yolov8n.pt'
            if os.path.exists(pretrained_weights):
                print(f"[Training] 使用本地预训练权重: {pretrained_weights}")
            else:
                print(f"[Training] 首次运行，正在下载预训练权重...")
            self._create_training_log(data_path, epochs, batch, imgsz, optimizer, lr0, pretrained_weights)
            
            model = YOLO(pretrained_weights) 
            model.add_callback("on_train_epoch_end", self.on_train_epoch_end)
            print(f"开始训练: {data_path}")
            print(f"训练参数: Epochs={epochs}, Batch={batch}, ImgSize={imgsz}, Optimizer={optimizer}, LR={lr0}")
            
            model.train(
                data=data_path, 
                epochs=epochs, 
                batch=batch, 
                imgsz=imgsz,
                optimizer=optimizer,
                lr0=lr0,
                workers=4,  # 数据加载线程数，根据CPU核心数调整
                cache=True,  # 缓存图像到内存，加速训练
                project=os.path.join(BASE_DIR, 'runs'), 
                name='detect', 
                exist_ok=True
            )
            if not self.stop_requested:
                trained_weight = os.path.join(BASE_DIR, 'runs', 'detect', 'weights', 'best.pt')
                if os.path.exists(trained_weight):
                    shutil.copy(trained_weight, MODEL_PATH)
                    print(">>> 模型已更新: best.pt")
                    global detect_model
                    detect_model = None 
                    self._finalize_training_log("completed", trained_weight)
                else:
                    self._finalize_training_log("completed", "")
            elif self.stop_requested:
                self._finalize_training_log("stopped", "")
        except Exception as e:
            print(f"训练错误: {e}")
            self._finalize_training_log("failed", "")
        finally:
            self.is_training = False
            self.stop_requested = False

    def start(self, data_path, epochs, batch, imgsz=640, optimizer='Adam', lr0=0.01):
        if self.is_training: return False
        if not os.path.exists(data_path): return False
        self.thread = threading.Thread(
            target=self._train_task, 
            args=(data_path, epochs, batch, imgsz, optimizer, lr0)
        )
        self.thread.start()
        return True

    def stop(self):
        if self.is_training:
            self.stop_requested = True
            return True
        return False

trainer = TrainingManager()

# ================= 模块 2: 检测与视频流 =================
video_state = { "source": 0, "conf": 0.30, "iou": 0.45, "table_data": [], "is_alarm": False, "last_alarm_print": 0, "last_alarm_save": 0, "is_paused": False, "last_frame_bytes": None, "is_running": True }
lock = threading.Lock()
detect_model = None 

def get_detect_model():
    global detect_model
    if detect_model is None:
        if os.path.exists(MODEL_PATH):
            print(f"\033[92m[System] 加载自定义模型\033[0m")
            detect_model = YOLO(MODEL_PATH)
        else:
            print("\033[93m[System] 加载官方模型\033[0m")
            detect_model = YOLO("yolov8n.pt")
    return detect_model

def generate_frames():
    with lock: video_state["is_running"] = True
    cap = cv2.VideoCapture(video_state["source"]) if not (video_state["source"] == 0 and os.name == 'nt') else cv2.VideoCapture(0, cv2.CAP_DSHOW)
    model = get_detect_model()
    print("[System] 视频流已开启...")
    try:
        while cap.isOpened():
            if not video_state["is_running"]: break
            if video_state["is_paused"]:
                if video_state["last_frame_bytes"]: yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + video_state["last_frame_bytes"] + b'\r\n')
                time.sleep(0.1)
                continue
            success, frame = cap.read()
            if not success:
                if isinstance(video_state["source"], str): cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
                else: break 
            if storage: storage.buffer_frame(frame.copy())
            results = model(frame, conf=video_state["conf"], iou=video_state["iou"], verbose=False)
            annotated_frame = results[0].plot()
            current_data = []
            fall_detected_in_frame = False
            for r in results:
                for i, box in enumerate(r.boxes):
                    coords = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    cls_name = model.names[cls_id]
                    is_fall = False
                    if cls_name.lower() in FALL_LABELS: is_fall = True
                    elif cls_name == 'person':
                        x1, y1, x2, y2 = coords
                        w = x2 - x1; h = y2 - y1
                        if (w / h if h > 0 else 0) > 1.2: is_fall = True
                    display_name = cls_name
                    if is_fall: fall_detected_in_frame = True; display_name = "FALLING"
                    current_data.append({ "id": i + 1, "class": display_name, "conf": f"{conf:.1%}", "bbox": str(coords.tolist()) })
            with lock: video_state["table_data"] = current_data; video_state["is_alarm"] = fall_detected_in_frame
            if fall_detected_in_frame:
                cv2.rectangle(annotated_frame, (0, 0), (annotated_frame.shape[1], annotated_frame.shape[0]), (0, 0, 255), 10)
                cv2.putText(annotated_frame, "!!! FALL DETECTED !!!", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
                if storage: storage.save_event_clip()
                if time.time() - video_state["last_alarm_print"] > 1.0:
                    print(f"\033[91m[ALARM] 跌倒检测触发!\033[0m")
                    video_state["last_alarm_print"] = time.time()
                if time.time() - video_state["last_alarm_save"] > 5.0:
                    src = video_state["source"]
                    loc = "摄像头" if src == 0 else os.path.basename(str(src))
                    save_alarm_record(location=loc, alarm_type="跌倒")
                    video_state["last_alarm_save"] = time.time()
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()
            video_state["last_frame_bytes"] = frame_bytes
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except GeneratorExit: print("[System] 前端断开连接")
    except Exception as e: print(f"[System] 视频流异常: {e}")
    finally:
        if cap.isOpened(): cap.release()
        print("[System] 资源释放")
        with lock: video_state["table_data"] = []; video_state["is_alarm"] = False

# ================= API 路由 =================
@app.route('/')
def index(): return render_template('index.html')

@app.route('/video_feed')
def video_feed(): return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- 认证接口 ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    success, msg = auth_module.register(data.get('username'), data.get('password'))
    return jsonify({"success": success, "msg": msg})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    success, result = auth_module.login(
        data.get('username'),
        data.get('password'),
        data.get('expected_role')
    )
    if success:
        return jsonify({"success": True, **result})
    return jsonify({"success": False, "msg": result}), 401

@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    data = request.json
    token = data.get('token', '')
    payload = auth_module.verify_token_data(token)
    if payload:
        return jsonify({"success": True, "username": payload.get("user"), "role": payload.get("role", "user")})
    return jsonify({"success": False, "msg": "Token 已过期或无效"}), 401

# --- 其他接口 (保持不变) ---
@app.route('/api/video/db/<string:file_id>')
def stream_video_from_db(file_id):
    if not storage: return "Storage module not initialized", 500
    video_blob = storage.get_video_blob(file_id)
    if not video_blob: return "Video not found", 404
    return Response(video_blob, mimetype='video/mp4')

@app.route('/api/history', methods=['GET'])
def get_history():
    if not storage: return jsonify([])
    return jsonify(storage.get_all_records())

@app.route('/api/history/<string:record_id>', methods=['DELETE'])
def delete_history(record_id):
    if not storage: return jsonify({"success": False, "msg": "存储模块未初始化"}), 500
    ok, msg = storage.delete_record(record_id)
    return jsonify({"success": ok, "msg": msg}), (200 if ok else 500)

@app.route('/api/video/stop', methods=['POST'])
def stop_video_stream():
    with lock: video_state["is_running"] = False
    return jsonify({"success": True})

@app.route('/api/system/browse', methods=['GET'])
def browse_dataset_file():
    allowed, _ = has_role(request, 'admin')
    if not allowed:
        return jsonify({"success": False, "msg": "仅管理员可访问"}), 403
    try:
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(title="Select data.yaml", filetypes=[("YAML", "*.yaml"), ("All", "*.*")])
        root.destroy()
        return jsonify({"path": file_path})
    except Exception as e: return jsonify({"path": "", "error": str(e)})

@app.route('/api/train/start', methods=['POST'])
def start_train():
    allowed, _ = has_role(request, 'admin')
    if not allowed:
        return jsonify({"success": False, "msg": "仅管理员可启动训练"}), 403
    data = request.json
    dataset_path = data.get('dataset_path', '').strip('"')
    epochs = int(data.get('epochs', 50))
    batch = int(data.get('batch', 16))
    imgsz = int(data.get('imgsz', 640))
    optimizer = data.get('optimizer', 'Adam')
    lr0 = float(data.get('lr0', 0.01))
    
    if trainer.start(dataset_path, epochs, batch, imgsz, optimizer, lr0):
        return jsonify({"status": "started"})
    return jsonify({"status": "error"}), 400

@app.route('/api/train/stop', methods=['POST'])
def stop_train():
    allowed, _ = has_role(request, 'admin')
    if not allowed:
        return jsonify({"success": False, "msg": "仅管理员可停止训练"}), 403
    if trainer.stop(): return jsonify({"status": "stopping"})
    return jsonify({"status": "error"}), 400

@app.route('/api/train/metrics')
def get_metrics(): return jsonify({"is_training": trainer.is_training, "metrics": trainer.metrics})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    with lock: video_state["source"] = path; video_state["is_paused"] = False; video_state["is_running"] = True
    return jsonify({"success": True})

@app.route('/api/set_source_webcam', methods=['POST'])
def set_webcam():
    with lock: video_state["source"] = 0; video_state["is_paused"] = False; video_state["is_running"] = True
    return jsonify({"success": True})

@app.route('/api/video/toggle_pause', methods=['POST'])
def toggle_pause():
    with lock: video_state["is_paused"] = not video_state["is_paused"]
    return jsonify({"success": True, "is_paused": video_state["is_paused"]})

@app.route('/api/update_params', methods=['POST'])
def update_params():
    data = request.json
    with lock: video_state["conf"] = float(data.get('conf', 0.3)); video_state["iou"] = float(data.get('iou', 0.45))
    return jsonify({"success": True})

@app.route('/api/data')
def get_table_data():
    with lock: return jsonify(video_state["table_data"])

@app.route('/api/alarm')
def get_alarm_status():
    with lock: return jsonify({"is_alarm": video_state["is_alarm"]})

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    """DeepSeek AI 分析跌倒检测数据"""
    try:
        if deepseek_client is None:
            return jsonify({
                "success": False,
                "error": "未配置 DEEPSEEK_API_KEY，请在 .env 或环境变量中设置"
            }), 500
        data = request.json
        detection_data = data.get('detections', [])
        alarm_history = data.get('alarm_history', [])
        
        # 构建分析提示词
        detection_summary = f"检测到 {len(detection_data)} 个目标"
        alarm_summary = f"跌倒报警次数: {len(alarm_history)} 次"
        
        # 格式化检测数据
        detection_details = "\n".join([
            f"- 目标{i+1}: {d.get('class', 'unknown')} (置信度: {d.get('conf', 'N/A')})" 
            for i, d in enumerate(detection_data[:10])  # 最多显示10个
        ]) if detection_data else "无检测数据"
        
        # 格式化报警历史
        alarm_details = "\n".join([
            f"- {a.get('time', 'unknown')}: {len(a.get('data', []))} 个跌倒目标"
            for a in alarm_history[:5]  # 最近5次
        ]) if alarm_history else "无报警记录"
        
        prompt = f"""你是一个专业的跌倒检测系统分析师。请根据以下检测数据进行专业分析：

检测数据摘要：
- {detection_summary}
- {alarm_summary}

详细检测记录：
{detection_details}

报警历史：
{alarm_details}

请提供以下分析：
1. 当前场景风险评估（低/中/高风险）
2. 检测到的主要目标和状态
3. 是否存在跌倒事件及其严重程度
4. 安全建议和改进措施

请用简洁专业的中文回答，不超过200字。"""
        
        # 使用 OpenAI 客户端调用 DeepSeek API
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的跌倒检测分析助手，擅长分析视频监控数据并提供安全建议。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
            stream=False
        )
        
        analysis = response.choices[0].message.content
        
        return jsonify({
            "success": True,
            "analysis": analysis,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
            
    except Exception as e:
        print(f"[AI Analysis] 错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("系统启动成功！访问 http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
