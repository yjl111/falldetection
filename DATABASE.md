# MongoDB 数据库结构说明

## 数据库名称
`fall_detection_db`

## 集合（表）结构

### 1. users（用户表）
存储系统用户账户信息

```javascript
{
  "_id": ObjectId,           // MongoDB 自动生成
  "username": String,        // 用户名（唯一）
  "password": String,        // 密码（明文存储，建议后续改为加密）
  "created_at": DateTime     // 注册时间
}
```

**索引：**
- `username` (unique) - 确保用户名唯一


### 2. alarms（报警记录表）
存储跌倒检测报警记录

```javascript
{
  "_id": ObjectId,
  "id": Number,              // 报警ID（唯一）
  "timestamp": DateTime,     // 报警时间
  "location": String,        // 发生位置（卧室/客厅/浴室/厨房）
  "type": String,            // 跌倒类型（跌倒/摔倒/滑倒等）
  "status": String,          // 状态（待处理/已处理）
  "video_filename": String,  // 关联的视频文件名
  "handled_at": DateTime,    // 处理时间（可选）
  "created_at": DateTime     // 创建时间
}
```

**索引：**
- `id` (unique) - 报警唯一ID
- `timestamp` - 便于按时间查询
- `status` - 便于按状态筛选


### 3. alarm_config（报警配置表）
存储报警系统配置

```javascript
{
  "_id": ObjectId,
  "key": "main_config",      // 配置键（唯一）
  "sound": Boolean,          // 是否启用声音
  "notification": Boolean,   // 是否启用通知
  "email": Boolean,          // 是否启用邮件
  "sms": Boolean,           // 是否启用短信
  "time_start": String,      // 通知时段开始（HH:MM）
  "time_end": String,        // 通知时段结束（HH:MM）
  "contacts": Array,         // 联系人列表
  "updated_at": DateTime     // 更新时间
}
```

**索引：**
- `key` (unique) - 配置键唯一


### 4. contacts（联系人表）
存储报警联系人信息

```javascript
{
  "_id": ObjectId,
  "id": Number,              // 联系人ID（唯一）
  "name": String,            // 姓名
  "phone": String,           // 电话
  "email": String,           // 邮箱
  "created_at": DateTime     // 创建时间
}
```

**索引：**
- `id` (unique) - 联系人唯一ID


### 5. system_config（系统配置表）
存储系统参数配置

```javascript
{
  "_id": ObjectId,
  "key": "main_settings",    // 配置键（唯一）
  "detection": {             // 检测参数
    "confidence": Number,     // 置信度阈值
    "iou": Number,           // IoU阈值
    "areas": {               // 检测区域
      "bedroom": Boolean,
      "livingroom": Boolean,
      "bathroom": Boolean,
      "kitchen": Boolean
    }
  },
  "storage": {               // 存储设置
    "beforeSeconds": Number,  // 跌倒前秒数
    "afterSeconds": Number,   // 跌倒后秒数
    "autoClean": String      // 自动清理策略
  },
  "system": {                // 系统配置
    "language": String,       // 语言
    "theme": String,         // 主题
    "logs": {
      "enable": Boolean,
      "debug": Boolean
    }
  },
  "advanced": {              // 高级设置
    "gpu": Boolean,          // GPU加速
    "workers": Number,       // 线程数
    "apiUrl": String         // API地址
  },
  "updated_at": DateTime     // 更新时间
}
```

**索引：**
- `key` (unique) - 配置键唯一


### 6. config（通用配置表）
存储系统级别的通用配置

```javascript
{
  "_id": ObjectId,
  "key": String,             // 配置键（唯一）
  "value": Mixed,            // 配置值（可以是任意类型）
  "updated_at": DateTime     // 更新时间
}
```

**示例数据：**
```javascript
{ "key": "accuracy", "value": 94.5 }      // 系统准确率
{ "key": "uptime", "value": 99.8 }        // 系统运行时间
```

**索引：**
- `key` (unique) - 配置键唯一


### 7. history（视频历史记录表）
存储视频证据的元数据

```javascript
{
  "_id": ObjectId,
  "filename": String,        // 文件名
  "timestamp": String,       // 时间戳（显示用）
  "filepath": String,        // 文件路径（相对路径）
  "video_file_id": ObjectId, // GridFS文件ID（关联fs.files）
  "created_at": DateTime     // 创建时间
}
```

**索引：**
- `timestamp` - 便于按时间查询
- `video_file_id` - 关联GridFS文件


### 8. GridFS 集合（视频文件存储）
MongoDB GridFS 用于存储大文件（视频）

#### fs.files（文件元数据）
```javascript
{
  "_id": ObjectId,           // 文件唯一ID
  "filename": String,        // 文件名
  "length": Number,          // 文件大小（字节）
  "chunkSize": Number,       // 分块大小
  "uploadDate": DateTime,    // 上传时间
  "contentType": String      // MIME类型（video/mp4）
}
```

#### fs.chunks（文件分块）
```javascript
{
  "_id": ObjectId,
  "files_id": ObjectId,      // 关联的文件ID
  "n": Number,               // 块序号
  "data": Binary             // 二进制数据
}
```


## 使用方法

### 1. 初始化数据库
运行初始化脚本创建所有集合和索引：

```bash
python backend/init_database.py
```

### 2. 启动MongoDB
确保MongoDB服务已启动：

```bash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
```

### 3. 查看数据库
使用MongoDB Compass或命令行工具：

```bash
mongo
use fall_detection_db
show collections
db.alarms.find().pretty()
```


## 数据流程

1. **用户注册/登录** → `users` 表
2. **跌倒检测触发** → 
   - 视频保存到 `GridFS` (fs.files + fs.chunks)
   - 元数据保存到 `history` 表
   - 报警记录保存到 `alarms` 表
3. **报警配置** → `alarm_config` 表
4. **联系人管理** → `contacts` 表
5. **系统设置** → `system_config` 表
6. **统计数据** → 从 `alarms` 表聚合计算
