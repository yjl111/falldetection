import time

class ResponseModule:
    def __init__(self):
        self.alarm_active = False
        self.alarm_message = ""
        self.last_print_time = 0
        self.print_interval = 1.0  # 控制终端打印频率(秒)，防止刷屏

    def trigger_alarm(self, message="Detected Fall Event!"):
        """
        触发报警逻辑
        """
        # 1. 优先在终端显示报警 (控制频率)
        current_time = time.time()
        if current_time - self.last_print_time > self.print_interval:
            timestamp = time.strftime("%H:%M:%S")
            # \033[91m 是红色的 ANSI 代码，\033[0m 是重置颜色
            print(f"\n\033[91m{'='*10} [ALARM {timestamp}] ⚠ {message} ⚠ {'='*10}\033[0m")
            self.last_print_time = current_time

        # 2. 更新内部状态 (供前端 API 查询弹窗)
        self.alarm_active = True
        self.alarm_message = message
        
        # 3. (扩展点) 这里可以添加发送邮件、短信或播放本地音频的代码
        # self.play_sound()

    def reset_alarm(self):
        """
        重置报警状态
        """
        if self.alarm_active:
            # 只有从报警状态变回正常时才打印，避免一直打印“正常”
            print(f"\033[92m[INFO] 警报解除 - System Normal\033[0m")
            
        self.alarm_active = False
        self.alarm_message = ""

    def get_status(self):
        """
        供 API 获取当前报警状态
        """
        return {
            "is_alarm": self.alarm_active,
            "message": self.alarm_message
        }