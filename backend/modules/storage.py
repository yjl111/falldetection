import os
import cv2
import time
import threading
from collections import deque
from datetime import datetime
import pymongo
import gridfs
from bson.objectid import ObjectId

class StorageModule:
    def __init__(self, save_dir='evidence', buffer_seconds=3, after_seconds=2, fps=30):
        # 视频保存路径 (生成过程仍需暂存磁盘)
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        self.fps = fps
        self.buffer_seconds = buffer_seconds  # 跌倒前的秒数
        self.after_seconds = after_seconds    # 跌倒后的秒数
        self.buffer_size = buffer_seconds * fps
        self.frame_buffer = deque(maxlen=self.buffer_size)  # 跌倒前的帧缓冲
        self.after_buffer = []  # 跌倒后的帧缓冲
        self.is_saving = False
        self.is_recording_after = False  # 是否正在录制跌倒后的帧
        self.after_frame_count = 0  # 已录制的跌倒后帧数
        
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

    def _save_snapshot_record(self, alarm_id, frame):
        """为报警保存关键帧截图和元数据"""
        if self.db is None or frame is None:
            return
        try:
            snapshot_name = f"snapshot_{alarm_id}.jpg"
            snapshot_abs = os.path.join(self.save_dir, snapshot_name)
            snapshot_rel = f"evidence/{snapshot_name}"
            cv2.imwrite(snapshot_abs, frame)
            self.db.alarm_snapshots.insert_one({
                "alarm_id": alarm_id,
                "filename": snapshot_name,
                "filepath": snapshot_rel,
                "snapshot_type": "alarm_frame",
                "created_at": datetime.now()
            })
            print(f"[Storage] 🖼️ 报警截图已保存: {snapshot_name}")
        except Exception as e:
            print(f"[Storage] 保存截图失败: {e}")

    def delete_record(self, record_id_str):
        """删除一条历史记录（同时删除 GridFS 视频文件和 history 文档，或本地文件）"""
        # 本地文件
        if record_id_str.endswith('.mp4'):
            local_path = os.path.join(self.save_dir, record_id_str)
            try:
                if os.path.exists(local_path):
                    os.remove(local_path)
                return True, "本地文件已删除"
            except Exception as e:
                return False, str(e)

        # MongoDB 记录
        if self.db is None:
            return False, "数据库未连接"
        try:
            record = self.db.history.find_one({"_id": ObjectId(record_id_str)})
            if not record:
                return False, "记录不存在"
            # 删除 GridFS 文件
            if "video_file_id" in record:
                try:
                    self.fs.delete(record["video_file_id"])
                except Exception:
                    pass
            # 删除 history 文档
            self.db.history.delete_one({"_id": ObjectId(record_id_str)})
            return True, "记录已删除"
        except Exception as e:
            return False, str(e)

    def get_record_by_id(self, record_id_str):
        """根据 ID 获取单条记录的元数据"""
        if self.db is None:
            return None
        try:
            doc = self.db.history.find_one({"_id": ObjectId(record_id_str)})
            if doc:
                return {
                    "id": str(doc["_id"]),
                    "filename": doc["filename"],
                    "timestamp": doc["timestamp"],
                    "filepath": doc.get("filepath", ""),
                    "source": "db"
                }
        except Exception:
            pass
        return None

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
        """缓冲帧：跌倒前存入循环队列，跌倒后存入临时列表"""
        # 如果正在录制跌倒后的帧
        if self.is_recording_after:
            self.after_buffer.append(frame.copy())
            self.after_frame_count += 1
            # 检查是否已录制足够的跌倒后帧
            if self.after_frame_count >= self.after_seconds * self.fps:
                self._finalize_video()
        else:
            # 正常情况下，存入循环缓冲区（跌倒前）
            self.frame_buffer.append(frame)

    def save_event_clip(self):
        """
        触发跌倒事件：标记开始录制跌倒后的帧
        """
        if self.is_saving or self.is_recording_after:
            return
        
        print(f"[Storage] 🎬 跌倒检测触发，开始录制后续 {self.after_seconds} 秒...")
        self.is_recording_after = True
        self.after_frame_count = 0
        self.after_buffer = []
    
    def _finalize_video(self):
        """
        完成视频录制：合并跌倒前后的帧并保存
        """
        if self.is_saving:
            return
        
        self.is_saving = True
        self.is_recording_after = False
        
        def _write_task():
            try:
                # 1. 准备文件名和路径
                display_time = time.strftime("%Y-%m-%d %H:%M:%S")
                file_time = time.strftime("%Y%m%d_%H%M%S")
                filename = f"fall_{file_time}.mp4"
                abs_path = os.path.join(self.save_dir, filename)
                rel_path = f"evidence/{filename}"

                # 2. 合并跌倒前后的帧
                before_frames = list(self.frame_buffer)  # 跌倒前3秒
                after_frames = self.after_buffer.copy()  # 跌倒后2秒
                all_frames = before_frames + after_frames
                
                if not all_frames:
                    print("[Storage] ⚠️ 无有效帧，跳过保存")
                    self.is_saving = False
                    return
                
                print(f"[Storage] 📊 合并帧数: 跌倒前 {len(before_frames)} 帧 + 跌倒后 {len(after_frames)} 帧 = 总计 {len(all_frames)} 帧")
                
                height, width, _ = all_frames[0].shape

                # 3. 写入视频文件
                try:
                    fourcc = cv2.VideoWriter_fourcc(*'avc1')
                    out = cv2.VideoWriter(abs_path, fourcc, self.fps, (width, height))
                    if not out.isOpened():
                         raise Exception("avc1 writer not opened")
                except Exception as e:
                    print(f"[Storage] avc1 编码不可用 ({e})，尝试回退到 mp4v")
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(abs_path, fourcc, self.fps, (width, height))

                for f in all_frames:
                    out.write(f)
                out.release()
                print(f"[Storage] 🎥 视频文件已生成: {abs_path}")

                # 4. 读取生成的文件为二进制数据
                with open(abs_path, 'rb') as video_file:
                    video_binary = video_file.read()

                # 5. 存入 MongoDB
                self._save_to_db(filename, display_time, rel_path, video_binary)
                
                # 6. 同时保存报警记录
                self._save_alarm_record(display_time, filename)
                
                # 清空跌倒后缓冲区
                self.after_buffer = []

            except Exception as e:
                print(f"[Storage] 保存流程异常: {e}")
            finally:
                self.is_saving = False

        threading.Thread(target=_write_task).start()

    def _save_alarm_record(self, timestamp_str, video_filename):
        """保存报警记录到MongoDB"""
        if self.db is None:
            return
        
        try:
            from datetime import datetime
            # 生成唯一ID（使用当前时间戳）
            alarm_id = int(datetime.now().timestamp())
            
            alarm_record = {
                "id": alarm_id,
                "timestamp": datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S"),
                "location": "监控区域",  # 可以后续根据实际情况更新
                "type": "跌倒",
                "status": "待处理",
                "video_filename": video_filename,
                "created_at": datetime.now()
            }
            
            self.db.alarms.insert_one(alarm_record)
            print(f"[Storage] 📢 报警记录已保存 (ID: {alarm_id})")
            snapshot_frame = None
            if self.after_buffer:
                snapshot_frame = self.after_buffer[0]
            elif self.frame_buffer:
                snapshot_frame = self.frame_buffer[-1]
            self._save_snapshot_record(alarm_id, snapshot_frame)
        except Exception as e:
            print(f"[Storage] 保存报警记录失败: {e}")
