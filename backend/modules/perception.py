import os
from ultralytics import YOLO

class PerceptionModule:
    def __init__(self, model_path='yolov8n.pt'):
        self.model_path = model_path
        self.model = None

    def load_model(self):
        """懒加载模型"""
        if self.model is None:
            if os.path.exists(self.model_path):
                print(f"[Perception] 加载自定义模型: {self.model_path}")
                self.model = YOLO(self.model_path)
            else:
                print("[Perception] 加载官方预训练模型: yolov8n.pt")
                self.model = YOLO('yolov8n.pt')
        return self.model

    def update_model(self, new_path):
        """更新模型路径并重置"""
        self.model_path = new_path
        self.model = None # 强制下次推理时重载

    def detect(self, frame, conf=0.3, iou=0.45):
        """执行推理"""
        model = self.load_model()
        # verbose=False 防止控制台刷屏
        results = model(frame, conf=conf, iou=iou, verbose=False)
        return results