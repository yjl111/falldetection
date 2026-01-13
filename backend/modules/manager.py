import os
import threading
import logging
import shutil
import tkinter as tk
from tkinter import filedialog
from ultralytics import YOLO

class SystemManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.config = {
            "source": 0,
            "conf": 0.30,
            "iou": 0.45
        }
        self.training_state = {
            "is_training": False,
            "metrics": {"epochs": [], "box_loss": [], "cls_loss": [], "map50": []}
        }
        self.setup_logging()

    def setup_logging(self):
        class NoPollingFilter(logging.Filter):
            def filter(self, record):
                msg = record.getMessage()
                if 'GET /api' in msg: return False
                if 'GET /video_feed' in msg: return False
                return True
        logging.getLogger('werkzeug').addFilter(NoPollingFilter())

    def update_params(self, conf, iou):
        self.config["conf"] = conf
        self.config["iou"] = iou

    def set_source(self, source):
        self.config["source"] = source

    def open_file_dialog(self):
        """服务端弹出文件选择"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            path = filedialog.askopenfilename(
                title="Select data.yaml",
                filetypes=[("YAML", "*.yaml"), ("All", "*.*")]
            )
            root.destroy()
            return path
        except:
            return ""

    # --- 训练逻辑 (封装在管理模块中) ---
    def start_training(self, data_path, epochs, batch):
        if self.training_state["is_training"]: return False
        
        def _train():
            self.training_state["is_training"] = True
            # 重置指标
            self.training_state["metrics"] = {"epochs": [], "box_loss": [], "cls_loss": [], "map50": []}
            
            try:
                model = YOLO('yolov8n.pt')
                model.add_callback("on_train_epoch_end", self._on_epoch_end)
                
                runs_dir = os.path.join(self.base_dir, 'runs')
                model.train(data=data_path, epochs=epochs, batch=batch, imgsz=640, 
                            project=runs_dir, name='detect', exist_ok=True)
                
                # 更新最佳模型
                best_pt = os.path.join(runs_dir, 'detect', 'weights', 'best.pt')
                target_pt = os.path.join(self.base_dir, 'best.pt')
                if os.path.exists(best_pt):
                    shutil.copy(best_pt, target_pt)
                    print("[Manager] 模型训练完成并已更新")
            except Exception as e:
                print(f"[Manager] 训练出错: {e}")
            finally:
                self.training_state["is_training"] = False

        threading.Thread(target=_train).start()
        return True

    def _on_epoch_end(self, trainer):
        metrics = self.training_state["metrics"]
        metrics["epochs"].append(trainer.epoch + 1)
        if hasattr(trainer, 'loss_items'):
            metrics["box_loss"].append(float(trainer.loss_items[0]))
            metrics["cls_loss"].append(float(trainer.loss_items[1]))
        metrics["map50"].append(float(trainer.metrics.get("metrics/mAP50(B)", 0)))