# MongoDB 数据库结构说明

## 数据库名称
`fall_detection_db`

## 当前状态
本文档已按当前项目代码更新，和 [backend/init_database.py](D:/falldetection/backend/init_database.py)、[backend/modules/extensions.py](D:/falldetection/backend/modules/extensions.py)、[backend/modules/auth.py](D:/falldetection/backend/modules/auth.py) 中的真实实现保持一致。

## 集合总览
当前项目会使用以下集合：

- `users`
- `alarms`
- `alarm_config`
- `contacts`
- `system_config`
- `config`
- `history`
- `devices`
- `emergency_contacts`
- `model_training_logs`
- `alarm_feedback`
- `audit_logs`
- `notification_logs`
- `user_profiles`
- `alarm_workorders`
- `user_messages`
- `health_reports`
- `device_heartbeats`
- `alarm_snapshots`
- `notification_rules`
- `fs.files`
- `fs.chunks`

## 集合结构

### 1. `users`（用户表）
存储系统登录账号。当前系统已支持角色区分：

- `admin`：管理端
- `user`：用户端

```javascript
{
  "_id": ObjectId,
  "username": String,
  "password": String,
  "role": String,            // admin / user
  "created_at": DateTime
}
```

**索引：**
- `username` (unique)

**说明：**
- 当前密码仍为明文存储，后续建议改为哈希。
- 第一个注册账号会自动成为 `admin`。

### 2. `alarms`（报警记录表）
存储跌倒检测产生的报警记录。

```javascript
{
  "_id": ObjectId,
  "id": Number,              // 报警ID（唯一）
  "timestamp": DateTime,     // 报警时间
  "location": String,        // 位置
  "type": String,            // 事件类型
  "status": String,          // 待处理 / 已处理 / 已纠错
  "video_filename": String,  // 关联视频文件名
  "created_at": DateTime,

  // 处理后可能补充的字段
  "handled_at": DateTime,
  "handler": String,
  "workorder_id": ObjectId,
  "is_false_positive": Boolean,

  // 预留/可选字段，部分接口会尝试使用
  "username": String,
  "device_id": String
}
```

**索引：**
- `id` (unique)
- `timestamp`
- `status`

### 3. `alarm_config`（报警配置表）
存储主报警配置。

```javascript
{
  "_id": ObjectId,
  "key": "main_config",
  "sound": Boolean,
  "notification": Boolean,
  "email": Boolean,
  "sms": Boolean,
  "time_start": String,      // HH:MM
  "time_end": String,        // HH:MM
  "contacts": Array,
  "updated_at": DateTime
}
```

**索引：**
- `key` (unique)

### 4. `contacts`（报警联系人表）
存储报警模块中的基础联系人。

```javascript
{
  "_id": ObjectId,
  "id": Number,
  "name": String,
  "phone": String,
  "email": String,
  "created_at": DateTime
}
```

**索引：**
- `id` (unique)

### 5. `system_config`（系统设置表）
存储系统参数与界面配置。

```javascript
{
  "_id": ObjectId,
  "key": "main_settings",
  "detection": {
    "confidence": Number,
    "iou": Number,
    "areas": {
      "bedroom": Boolean,
      "livingroom": Boolean,
      "bathroom": Boolean,
      "kitchen": Boolean
    }
  },
  "storage": {
    "beforeSeconds": Number,
    "afterSeconds": Number,
    "autoClean": String
  },
  "system": {
    "language": String,
    "theme": String,
    "logs": {
      "enable": Boolean,
      "debug": Boolean
    }
  },
  "advanced": {
    "gpu": Boolean,
    "workers": Number,
    "apiUrl": String
  },
  "updated_at": DateTime
}
```

**索引：**
- `key` (unique)

### 6. `config`（通用配置表）
存储全局统计或系统级配置。

```javascript
{
  "_id": ObjectId,
  "key": String,
  "value": Mixed,
  "updated_at": DateTime
}
```

**索引：**
- `key` (unique)

**当前示例值：**
```javascript
{ "key": "accuracy", "value": 94.5 }
{ "key": "uptime", "value": 99.8 }
```

### 7. `history`（视频历史记录表）
存储证据视频元数据，视频本体走 GridFS。

```javascript
{
  "_id": ObjectId,
  "filename": String,
  "timestamp": String,
  "filepath": String,
  "video_file_id": ObjectId,
  "created_at": DateTime
}
```

**索引：**
- `timestamp`
- `video_file_id`

### 8. `devices`（设备管理表）
管理摄像头和视频源。

```javascript
{
  "_id": ObjectId,
  "device_id": String,
  "name": String,
  "location": String,
  "source_type": String,     // rtsp / webcam / local_file
  "source_url": String,
  "status": String,          // online / offline / error
  "framerate": Number,
  "resolution": String,
  "created_at": DateTime
}
```

**索引：**
- `device_id` (unique)

### 9. `emergency_contacts`（紧急联系人表）
存储用户专属的紧急联系人。

```javascript
{
  "_id": ObjectId,
  "belong_to_user": String,
  "contact_name": String,
  "phone": String,
  "email": String,
  "relationship": String,
  "notify_level": Number,
  "is_active": Boolean,
  "created_at": DateTime
}
```

**索引：**
- `belong_to_user`

### 10. `model_training_logs`（模型训练日志表）
记录训练流程和结果。

```javascript
{
  "_id": ObjectId,
  "version_name": String,
  "base_model": String,
  "dataset_path": String,
  "epochs": Number,
  "batch": Number,
  "imgsz": Number,
  "optimizer": String,
  "lr0": Number,
  "start_time": DateTime,
  "end_time": DateTime,
  "status": String,          // running / completed / stopped / failed
  "metrics": {
    "best_map50": Number,
    "final_loss": Number
  },
  "weight_path": String
}
```

**索引：**
- `version_name` (unique)

### 11. `alarm_feedback`（误报反馈表）
存储人工复核结果。

```javascript
{
  "_id": ObjectId,
  "alarm_id": ObjectId | Number,
  "reviewer": String,
  "is_false_positive": Boolean,
  "correct_label": String,
  "comment": String,
  "reviewed_at": DateTime
}
```

**索引：**
- `alarm_id`

### 12. `audit_logs`（审计日志表）
记录用户关键操作。

```javascript
{
  "_id": ObjectId,
  "username": String,
  "action": String,
  "details": String,
  "target_type": String,
  "target_id": Mixed,
  "status": String,          // success / failed
  "created_at": DateTime
}
```

**索引：**
- `created_at`
- `username`
- `action`

**当前已接入的典型动作：**
- 登录 / 注册
- 更新报警配置
- 处理报警
- 增删联系人
- 增删改设备
- 更新用户资料
- 生成健康报告

### 13. `notification_logs`（通知日志表）
记录短信、邮件等发送结果。

```javascript
{
  "_id": ObjectId,
  "alarm_id": Number,
  "channel": String,         // sms / email
  "recipient": String,
  "success": Boolean,
  "message": String,
  "created_at": DateTime
}
```

**索引：**
- `alarm_id`
- `channel`
- `created_at`

### 14. `user_profiles`（用户资料表）
存储用户端个人信息。

```javascript
{
  "_id": ObjectId,
  "username": String,
  "real_name": String,
  "phone": String,
  "address": String,
  "age": Number | String,
  "medical_notes": String,
  "updated_at": DateTime
}
```

**索引：**
- `username` (unique)

### 15. `alarm_workorders`（报警工单表）
存储管理员对报警的处理结果。

```javascript
{
  "_id": ObjectId,
  "alarm_id": Number,
  "handler": String,
  "result": String,
  "comment": String,
  "status": String,          // closed 等
  "created_at": DateTime,
  "handled_at": DateTime
}
```

**索引：**
- `alarm_id`
- `handler`
- `created_at`

### 16. `user_messages`（用户消息表）
存储系统发给用户的站内消息。

```javascript
{
  "_id": ObjectId,
  "username": String,
  "title": String,
  "content": String,
  "type": String,            // system / alarm
  "is_read": Boolean,
  "created_at": DateTime,
  "read_at": DateTime
}
```

**索引：**
- `username`
- `is_read`
- `created_at`

### 17. `health_reports`（健康报告表）
存储日报、周报等统计报告。

```javascript
{
  "_id": ObjectId,
  "username": String,
  "report_type": String,     // daily / weekly / monthly
  "start_date": DateTime,
  "end_date": DateTime,
  "fall_count": Number,
  "false_positive_count": Number,
  "high_risk_period": String,
  "summary": String,
  "created_at": DateTime
}
```

**索引：**
- `username`
- `report_type`
- `created_at`

### 18. `device_heartbeats`（设备心跳表）
存储设备在线状态上报。

```javascript
{
  "_id": ObjectId,
  "device_id": String,
  "status": String,          // online / offline
  "ping_at": DateTime,
  "latency": Number | null,
  "remark": String
}
```

**索引：**
- `device_id`
- `ping_at`

### 19. `alarm_snapshots`（报警截图表）
存储报警关键帧截图元数据。

```javascript
{
  "_id": ObjectId,
  "alarm_id": Number,
  "filename": String,
  "filepath": String,
  "snapshot_type": String,   // alarm_frame
  "created_at": DateTime
}
```

**索引：**
- `alarm_id`
- `created_at`

### 20. `notification_rules`（通知规则表）
存储用户自定义通知策略。

```javascript
{
  "_id": ObjectId,
  "username": String,
  "device_id": String,
  "alarm_type": String,
  "time_start": String,      // HH:MM
  "time_end": String,        // HH:MM
  "channels": Array,         // ["sms", "email"]
  "target_contacts": Array,  // 联系人名称列表
  "enabled": Boolean,
  "updated_at": DateTime
}
```

**索引：**
- `username`
- `device_id`
- `enabled`

### 21. GridFS 集合（视频文件存储）
MongoDB GridFS 用于保存大文件视频。

#### `fs.files`
```javascript
{
  "_id": ObjectId,
  "filename": String,
  "length": Number,
  "chunkSize": Number,
  "uploadDate": DateTime,
  "contentType": String
}
```

#### `fs.chunks`
```javascript
{
  "_id": ObjectId,
  "files_id": ObjectId,
  "n": Number,
  "data": Binary
}
```

## 主要接口与集合对应

### 认证与角色
- 注册 / 登录：`users`
- 登录令牌校验：基于 JWT 负载返回 `username`、`role`

### 报警相关
- 报警记录：`alarms`
- 报警配置：`alarm_config`
- 联系人：`contacts`
- 报警工单：`alarm_workorders`
- 通知日志：`notification_logs`
- 报警截图：`alarm_snapshots`
- 误报反馈：`alarm_feedback`

### 用户端
- 用户资料：`user_profiles`
- 用户消息：`user_messages`
- 紧急联系人：`emergency_contacts`
- 通知规则：`notification_rules`
- 健康报告：`health_reports`

### 管理端
- 设备管理：`devices`
- 设备心跳：`device_heartbeats`
- 训练日志：`model_training_logs`
- 审计日志：`audit_logs`
- 系统设置：`system_config`

## 数据流程

1. 用户注册/登录
   - 数据写入 `users`
   - 同时写入 `audit_logs`

2. 跌倒检测触发
   - 视频文件写入 `fs.files` + `fs.chunks`
   - 视频元数据写入 `history`
   - 报警记录写入 `alarms`
   - 关键帧截图元数据写入 `alarm_snapshots`
   - 如触发通知，写入 `notification_logs`

3. 管理员处理报警
   - 工单写入 `alarm_workorders`
   - 原报警更新 `status`、`handled_at`、`handler`、`workorder_id`
   - 给用户写入 `user_messages`
   - 审计写入 `audit_logs`

4. 用户维护个人中心
   - 个人资料写入 `user_profiles`
   - 紧急联系人写入 `emergency_contacts`
   - 通知规则写入 `notification_rules`

5. 设备与训练
   - 设备管理写入 `devices`
   - 心跳写入 `device_heartbeats`
   - 训练过程写入 `model_training_logs`

6. 报表与复核
   - 误报复核写入 `alarm_feedback`
   - 健康报告写入 `health_reports`

## 初始化与查看

### 1. 初始化数据库
```bash
python backend/init_database.py
```

### 2. 启动 MongoDB
```bash
# Windows
net start MongoDB
```

### 3. 查看集合
```bash
mongo
use fall_detection_db
show collections
db.alarms.find().pretty()
```

## 备注
- 当前数据库连接仍默认使用本地 MongoDB：`mongodb://localhost:27017/`
- 当前文档描述的是“代码实际已接入状态”，不是纯设计草案
- 若后续继续扩展多设备关联、报警归属用户、模型部署记录，建议同步更新本文件
