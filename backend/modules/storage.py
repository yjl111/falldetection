import os
import cv2
import time
import threading
from collections import deque
import pymongo
import gridfs
from bson.objectid import ObjectId

class StorageModule:
    def __init__(self, save_dir='evidence', buffer_seconds=3, fps=30):
        # 视频保存路径 (生成过程仍需暂存磁盘)
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        self.fps = fps
        self.buffer_size = buffer_seconds * fps
        self.frame_buffer = deque(maxlen=self.buffer_size)
        self.is_saving = False
        
        # --- MongoDB 配置 ---
        # 请确保您的 MongoDB 服务已启动
        self.mongo_uri = "mongodb://localhost:27017/"
        self.db_name = "fall_detection_db"
        self._init_mongo()

    def _init_mongo(self):
        """初始化 MongoDB 连接和 GridFS"""
        try:
            self.client = pymongo.MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000)
            self.db = self.client[self.db_name]
            # 初始化 GridFS 用于存储大文件
            self.fs = gridfs.GridFS(self.db)
            
            # 测试连接
            self.client.server_info()
            print("[Storage] ✅ MongoDB 已连接 (使用 GridFS 存储视频)")
        except Exception as e:
            print(f"[Storage] ❌ MongoDB 连接失败: {e}")
            self.db = None
            self.fs = None

    def _save_to_db(self, filename, timestamp, filepath, video_binary):
        """将视频存入 GridFS，并将元数据写入集合"""
        if self.db is None:
            print("[Storage] 数据库未连接，跳过保存")
            return

        try:
            # 1. 将视频二进制数据存入 GridFS
            # put 方法会返回文件在 GridFS 中的唯一 ID (ObjectId)
            grid_file_id = self.fs.put(video_binary, filename=filename, content_type='video/mp4')

            # 2. 将元数据存入普通集合，并关联 GridFS 的 ID
            record = {
                "filename": filename,
                "timestamp": timestamp,
                "filepath": filepath, # 保留相对路径字段，兼容前端逻辑
                "video_file_id": grid_file_id # 关联 GridFS 文件的关键 ID
            }
            self.db.history.insert_one(record)
            
            print(f"[Storage] 📝 MongoDB 记录已添加 (GridFS ID: {grid_file_id})")
        except Exception as e:
            print(f"[Storage] MongoDB 写入错误: {e}")

    def get_all_records(self):
        """查询所有历史记录 (支持 MongoDB 和 本地文件)"""
        data = []
        
        # 1. 尝试从 MongoDB 读取
        if self.db is not None:
            try:
                cursor = self.db.history.find().sort('_id', -1)
                for doc in cursor:
                    data.append({
                        "id": str(doc["_id"]),
                        "filename": doc["filename"],
                        "timestamp": doc["timestamp"],
                        "filepath": doc["filepath"],
                        "source": "db"
                    })
            except Exception as e:
                print(f"[Storage] DB 查询失败: {e}")

        # 2. 如果数据为空（DB未连接或无数据），扫描本地 evidence 目录
        if not data:
            try:
                files = [f for f in os.listdir(self.save_dir) if f.endswith('.mp4')]
                # 按修改时间倒序
                files.sort(key=lambda x: os.path.getmtime(os.path.join(self.save_dir, x)), reverse=True)
                
                for f in files:
                    file_path = os.path.join(self.save_dir, f)
                    # 尝试从文件名解析时间 fall_20251214_202138.mp4
                    try:
                        time_part = f.replace('fall_', '').replace('.mp4', '')
                        ts = time.strptime(time_part, "%Y%m%d_%H%M%S")
                        display_time = time.strftime("%Y-%m-%d %H:%M:%S", ts)
                    except:
                        # 解析失败则使用文件修改时间
                        mtime = os.path.getmtime(file_path)
                        display_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
                    
                    data.append({
                        "id": f, # 本地文件 ID 直接使用文件名
                        "filename": f,
                        "timestamp": display_time,
                        "filepath": f"evidence/{f}",
                        "source": "local"
                    })
            except Exception as e:
                print(f"[Storage] 本地扫描失败: {e}")
        
        return data

    def get_video_blob(self, record_id_str):
        """根据记录 ID 获取视频数据 (支持 MongoDB 和 本地文件)"""
        
        # 1. 如果 ID 以 .mp4 结尾，说明是本地文件
        if record_id_str.endswith('.mp4'):
            local_path = os.path.join(self.save_dir, record_id_str)
            if os.path.exists(local_path):
                try:
                    with open(local_path, 'rb') as f:
                        return f.read()
                except Exception as e:
                    print(f"[Storage] 读取本地文件失败: {e}")
                    return None
            return None

        # 2. 否则尝试从 MongoDB 读取
        if self.db is None: return None

        try:
            # 先通过记录 ID 找到 history 文档
            record = self.db.history.find_one({"_id": ObjectId(record_id_str)})
            if not record or "video_file_id" not in record:
                print("[Storage] 未找到关联的视频文件")
                return None
            
            # 通过 video_file_id 从 GridFS 读取文件内容
            grid_out = self.fs.get(record["video_file_id"])
            return grid_out.read()
            
        except Exception as e:
            print(f"[Storage] 获取视频数据失败: {e}")
            return None

    def buffer_frame(self, frame):
        self.frame_buffer.append(frame)

    def save_event_clip(self):
        """
        核心功能：保存视频文件 -> 读取二进制 -> 存入 MongoDB
        """
        if self.is_saving: 
            return 
        
        self.is_saving = True
        
        def _write_task():
            try:
                # 1. 准备文件名和路径
                display_time = time.strftime("%Y-%m-%d %H:%M:%S")
                file_time = time.strftime("%Y%m%d_%H%M%S")
                filename = f"fall_{file_time}.mp4"
                abs_path = os.path.join(self.save_dir, filename)
                rel_path = f"evidence/{filename}"

                # 2. 将视频先写入临时文件 (OpenCV 需要文件路径)
                frames = list(self.frame_buffer)
                if not frames:
                    self.is_saving = False
                    return
                
                height, width, _ = frames[0].shape

                # 尝试使用 H.264 编码 (avc1)，这兼容现代浏览器
                # 如果系统缺少 openh264 dll，可能回退或失败，如果失败请尝试改为 'vp09' (webm)
                try:
                    fourcc = cv2.VideoWriter_fourcc(*'avc1')
                    out = cv2.VideoWriter(abs_path, fourcc, self.fps, (width, height))
                    if not out.isOpened():
                         raise Exception("avc1 writer not opened")
                except Exception as e:
                    # 回退方案
                    print(f"[Storage] avc1 编码不可用 ({e})，尝试回退到 mp4v")
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(abs_path, fourcc, self.fps, (width, height))

                for f in frames:
                    out.write(f)
                out.release()
                print(f"[Storage] 🎥 临时文件已生成: {abs_path}")

                # 3. 读取生成的文件为二进制数据
                with open(abs_path, 'rb') as video_file:
                    video_binary = video_file.read()

                # 4. 存入 MongoDB
                self._save_to_db(filename, display_time, rel_path, video_binary)
                
                # (可选) 如果你想完全依赖数据库，可以在这里删除本地文件
                # os.remove(abs_path) 

            except Exception as e:
                print(f"[Storage] 保存流程异常: {e}")
            finally:
                time.sleep(3) 
                self.is_saving = False

        threading.Thread(target=_write_task).start()