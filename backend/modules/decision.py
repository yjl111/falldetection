import math

class DecisionModule:
    def __init__(self):
        self.consecutive_frames = 0
        self.FALL_THRESHOLD_FRAMES = 5  # 连续多少帧异常才报警(防抖)

    def analyze(self, results):
        """
        分析检测结果，返回是否跌倒及绘制后的帧
        """
        annotated_frame = results[0].plot()
        is_fall_detected = False
        detections_data = []

        # 遍历检测结果
        for r in results:
            for i, box in enumerate(r.boxes):
                # 1. 提取基础信息
                coords = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = r.names[cls_id]

                # 2. 简单的宽高比跌倒判定逻辑 (AspectRatio)
                # 实际项目中可替换为 Pose Keypoints 角度判断
                x1, y1, x2, y2 = coords
                w = x2 - x1
                h = y2 - y1
                aspect_ratio = w / h

                # 判定规则：如果人只有“person”类且宽大于高 (躺着)
                if cls_name == 'person' and aspect_ratio > 1.2:
                    is_fall_detected = True
                
                detections_data.append({
                    "id": i + 1,
                    "class": cls_name,
                    "conf": f"{conf:.1%}",
                    "bbox": str(coords.tolist())
                })

        # 3. 时序逻辑防抖
        if is_fall_detected:
            self.consecutive_frames += 1
        else:
            self.consecutive_frames = 0

        # 只有连续帧数达标，才确认为跌倒事件
        confirmed_fall = self.consecutive_frames >= self.FALL_THRESHOLD_FRAMES

        return confirmed_fall, annotated_frame, detections_data