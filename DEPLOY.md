# 部署文档：跌倒检测与预警系统（Rocky Linux 8）

> 本文档描述如何在 **Rocky Linux 8** 虚拟机上以 **Nginx + gunicorn + Flask** 的方式部署本项目（方案 B，推荐）。
> 文末附「方案 A：Flask 直接运行（快速验证）」与「CentOS 7 差异说明」。

---

## 0.5 快速开始：一键部署脚本（推荐）

项目提供了自动化脚本 [deploy_rocky8.sh](deploy_rocky8.sh)，把第 2~8 步全部自动化（Python 环境、依赖、MongoDB、Nginx、SELinux、防火墙、systemd 服务）。

```bash
# 1. 上传代码（任选其一）
git clone https://github.com/yjl111/falldetection.git
# 或 scp -r D:\falldetection 用户名@服务器IP:/home/用户名/

cd falldetection
bash deploy_rocky8.sh        # 需要 root，脚本会自动 sudo 提权
```

脚本特性：
- **幂等**：可重复执行，已完成的步骤自动跳过（依赖已装、MongoDB 已装等）
- **自动选 Python**：优先用系统已有的 3.11/3.10/3.9，都没有则自动装 3.9
- **交互提示**：仅在你输入 API Key 时暂停一次，其余全自动
- **自带健康检查**：部署完成后自动验证 `http://127.0.0.1` 是否返回 200

> 若脚本报 `$'\r': command not found`（Windows 编辑导致行尾问题），先执行：
> `sed -i 's/\r$//' deploy_rocky8.sh` 再运行。

脚本执行完成后，物理机浏览器访问 `http://虚拟机IP` 即可。以下章节为手动部署的详细说明。

---

## 0. 部署架构

```
浏览器 ──> Nginx (:80) ──> gunicorn (:5000) ──> Flask app
                         │                       ├── MongoDB (:27017) fall_detection_db
                         │                       ├── YOLO 模型推理 (backend/best.pt)
                         │                       └── DeepSeek API (可选，AI 分析)
                         └── /video_feed 关闭缓冲，保证 MJPEG 视频流不卡顿
```

| 组件 | 版本要求 | 说明 |
|---|---|---|
| 系统 | Rocky Linux 8.x（glibc 2.28，依赖可正常安装） | CentOS 8 的官方替代品，支持至 2029-05 |
| Python | 3.10（系统模块提供） | 项目开发环境为 3.10.7 |
| MongoDB | 6.0.x（最高支持 7.0） | 硬依赖，未启动时系统功能大幅降级 |
| Nginx | 1.20+（AppStream 自带） | 反向代理 + 静态资源 |
| gunicorn | 最新即可 | Python WSGI 服务器 |

**前置条件：**
- 虚拟机内存 ≥ 4GB（torch 推理需要；低于 2GB 会被 OOM 杀掉）
- 网络建议设为 **桥接模式**，否则宿主机无法访问 `http://虚拟机IP`
- 代码通过 `git clone` 或 `scp` 传入虚拟机（见第 1 步）

---

## 1. 上传项目代码

任选其一：

```bash
# 方式一：git clone（推荐，代码已在 GitHub）
git clone https://github.com/yjl111/falldetection.git
cd falldetection

# 方式二：从本机 scp（Windows PowerShell 中执行）
scp -r D:\falldetection 用户名@虚拟机IP:/home/用户名/
```

> 本项目前端 `frontend/dist/` 已构建完毕，后端 Flask 直接托管，**无需在服务器上安装 Node.js**。

---

## 2. 系统基础准备

```bash
sudo dnf update -y
sudo dnf install -y git curl vim wget

# 安装 Python 3.10（Rocky 8 AppStream 提供）
sudo dnf install -y python3.10 python3.10-pip python3.10-devel
python3.10 --version   # 应输出 Python 3.10.x
```

> 若 `dnf` 找不到 `python3.10`（较旧版本的 Rocky 8），改用：
> `sudo dnf module enable python39 -y && sudo dnf install -y python39`

---

## 3. 创建虚拟环境并安装后端依赖

```bash
cd falldetection
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# 安装依赖（ultralytics 会自动带入 torch/torchvision/numpy 等，约 2GB，耐心等待）
pip install -r backend/requirements.txt
pip install gunicorn

# 验证关键包可导入
python -c "import cv2, ultralytics, pymongo, flask, openai; print('OK')"
```

> **内存较小（<4GB）时**：先安装 CPU 版 torch 再装其余依赖，避免安装时 OOM：
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> pip install -r backend/requirements.txt
> ```

---

## 4. 安装并启动 MongoDB 6.0

```bash
sudo tee /etc/yum.repos.d/mongodb-org-6.0.repo <<'EOF'
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/8/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
EOF

sudo dnf install -y mongodb-org
sudo systemctl enable --now mongod
sudo systemctl status mongod      # 确认 active (running)
```

---

## 5. 配置环境变量

```bash
cd falldetection
cp .env.example .env
vim .env    # 填入真实 DEEPSEEK_API_KEY（不填则 AI 分析功能不可用，其余功能正常）
```

---

## 6. 初始化数据库

```bash
source .venv/bin/activate
cd backend
python init_database.py    # 创建集合与索引、写入种子数据
```

---

## 7. 方案 A：先用 Flask 直接跑通验证（必做）

```bash
cd falldetection/backend
../.venv/bin/python app.py
# 浏览器访问 http://虚拟机IP:5000
# 验证：登录 → 实时检测（上传视频）→ 报警管理 → 历史回放
```

验证通过后 `Ctrl+C` 停止，继续下面的正式部署。

---

## 8. 方案 B：Nginx + gunicorn 正式部署

### 8.1 安装 Nginx

```bash
sudo dnf install -y nginx
sudo systemctl enable --now nginx
```

### 8.2 配置 Nginx 反向代理

```bash
sudo tee /etc/nginx/conf.d/falldetect.conf <<'EOF'
server {
    listen 80;
    server_name _;              # 有域名则填域名

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # MJPEG 视频流：必须关闭缓冲，否则画面卡死/延迟
    location /video_feed {
        proxy_pass http://127.0.0.1:5000;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        proxy_set_header Connection '';
    }
}
EOF

sudo nginx -t && sudo systemctl reload nginx
```

### 8.3 放行 SELinux（不做会 502）

```bash
# 允许 Nginx 反向代理到本地 5000 端口（Rocky 8 默认 SELinux enforcing）
sudo setsebool -P httpd_can_network_connect 1
```

### 8.4 放行防火墙

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

### 8.5 创建 systemd 服务（gunicorn 常驻 + 开机自启）

```bash
sudo tee /etc/systemd/system/fall-detect.service <<'EOF'
[Unit]
Description=Fall Detection Backend
After=network.target mongod.service

[Service]
WorkingDirectory=/home/你的用户名/falldetection
Environment="PATH=/home/你的用户名/falldetection/.venv/bin"
ExecStart=/home/你的用户名/falldetection/.venv/bin/gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 --chdir /home/你的用户名/falldetection/backend 'app:app'
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now fall-detect
sudo systemctl status fall-detect    # 确认 active (running)
```

> **为什么 gunicorn 必须是 `-w 1 --threads 8`？**
> `/video_feed` 是 MJPEG 长连接视频流，会一直占住一个 worker。若用多进程（`-w 4` 无线程），打开视频流后其余请求会被占满；单进程多线程是最简单可靠的组合。

### 8.6 权限修正

```bash
# evidence/uploads 目录需要写权限（留证视频与上传文件）
chmod -R 777 ~/falldetection/backend/evidence ~/falldetection/backend/uploads
```

---

## 9. 验收清单

| 检查项 | 方法 | 预期 |
|---|---|---|
| 页面访问 | 浏览器打开 `http://虚拟机IP` | 登录页正常显示 |
| 注册/登录 | 注册首个账号 | 自动成为 admin，进入管理端 |
| 实时检测 | 检测页「上传视频」选择 `backend/uploads/` 下的测试视频 | 画面出现检测框，可切换暂停 |
| 报警触发 | 播放含跌倒动作的视频 | 红色告警框 + 「FALL DETECTED」提示 |
| 历史回放 | 报警管理/历史回放页 | 能看到留证视频并可播放 |
| 视频流流畅 | 打开检测页观察 | 画面无卡死（验证 nginx 缓冲已关） |

---

## 10. 常见问题排查

| 现象 | 原因 | 解决 |
|---|---|---|
| Nginx 返回 502 | SELinux 拦截反向代理 | `sudo setsebool -P httpd_can_network_connect 1` |
| 页面打不开 | firewalld 未放行 | `sudo firewall-cmd --permanent --add-service=http && sudo firewall-cmd --reload` |
| 日志大量 "MongoDB 连接失败" | mongod 未启动 | `sudo systemctl start mongod` |
| 切摄像头黑屏 | 虚拟机无摄像头 | 用「上传视频」功能演示；或给 VM 挂 USB 摄像头 |
| 训练页选数据集报错/卡住 | tkinter 弹窗需要图形界面 | 服务器场景跳过训练功能；或改用有桌面的环境 |
| 视频留证保存失败 | evidence 目录无写权限 | `chmod -R 777 backend/evidence backend/uploads` |
| pip 报 `glibc >= 2.28` | 用了 CentOS 7（glibc 2.17） | 本方案基于 Rocky 8 不会出现；如仍出现则按第 3 步降级 torch 版本 |
| 内存不足被杀 (OOM) | 虚拟机内存过小 | 调到 ≥4GB；或改用 CPU 版 torch |

**日志查看：**
```bash
sudo journalctl -u fall-detect -f     # gunicorn/Flask 运行日志
sudo journalctl -u mongod -f          # MongoDB 日志
```

---

## 11. 后续扩展

### 11.1 HTTPS（可选）

```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

### 11.2 静态资源交给 Nginx（可选，降低 Flask 压力）

将 `frontend/dist` 复制到 `/usr/share/nginx/falldetect`，Nginx 增加：

```nginx
location /assets/ {
    root /usr/share/nginx/falldetect;
    expires 7d;
}
```

### 11.3 升级到 Rocky 9（如需长期维护）

Rocky 9 步骤与本文档几乎一致，差异仅：`dnf` 自带 python3.11、MongoDB 可用 7.0、`server_name _;` 写法相同。核心的 Nginx/gunicorn/systemd 配置完全复用。

---

## 12. CentOS 7 用户参考（仅当必须用 CentOS 7）

CentOS 7 已于 2024-06-30 EOL，官方源已下线，且 glibc 2.17 无法安装新版 torch/opencv，**强烈不建议**。如必须使用，差异点：

1. 先切换 vault 归档源：`sed -i 's|mirror.centos.org|vault.centos.org|g' /etc/yum.repos.d/CentOS-*.repo`
2. 用 Miniconda 安装 Python 3.10（系统 Python 2.7 不可动）
3. 固定旧版本依赖：`torch==2.2.2 torchvision==0.17.2 numpy==1.26.4 opencv-python==4.9.0.80`（cpu 源安装）
4. MongoDB 最高只能装 4.4（repo 地址换 `/redhat/7/`）
5. 包管理器为 yum，其余 Nginx/gunicorn/systemd 配置相同
