#!/usr/bin/env bash
# ============================================================================
# 跌倒检测与预警系统 — Rocky Linux 8 一键部署脚本（增强版 v2）
# 部署方式: Nginx(80) + gunicorn(5000) + Flask + MongoDB
#
# 用法:
#   bash deploy_rocky8.sh              # 自动提权（需要 sudo 权限）
#   sudo bash deploy_rocky8.sh
#
# 前提:
#   - Rocky Linux 8.x（RHEL 8 / CentOS 8 Stream 亦可）
#   - 本脚本需放在项目根目录（falldetection/）下运行
#   - 内存建议 >= 4GB
#
# 特性:
#   - 幂等：可重复执行，已完成的步骤自动跳过
#   - Python 自动选择系统可用版本（3.11 / 3.10 / 3.9，均支持本项目）
#   - 自动安装 OpenCV 运行时库（libGL）与 tkinter，避免 ImportError
#   - 自动处理 SELinux：放行反向代理 + 家目录代码执行标签
#   - Nginx 配置包含前端静态托管 + Vue Router 路由兜底 + /api 代理 + 上传大小限制
#   - 自动检查前端 dist 是否完整（缺失时提示构建/上传方法）
#   - 自动安装 ffmpeg 并给 storage.py 打 H.264 转码补丁（留证视频浏览器可播）
#   - 若在 Windows 上编辑过本脚本且报 "$'\r': command not found"，
#     先执行: sed -i 's/\r$//' deploy_rocky8.sh
# ============================================================================

set -euo pipefail

# ---------------- 基础配置 ----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"                        # 项目根目录（本脚本所在目录）
APP_USER="${SUDO_USER:-$(whoami)}"           # 实际执行用户
SERVICE_NAME="fall-detect"                   # systemd 服务名
NGINX_CONF="/etc/nginx/conf.d/falldetect.conf"
MONGO_VERSION="6.0"
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

# ---------------- 颜色输出 ----------------
GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
die()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

# ---------------- 权限检查 ----------------
if [[ $EUID -ne 0 ]]; then
  warn "需要 root 权限，正在通过 sudo 重新执行本脚本..."
  exec sudo -E bash "$0" "$@"
fi

# ---------------- 发行版检查 ----------------
if ! grep -qiE 'rocky|rhel|centos' /etc/os-release 2>/dev/null; then
  die "此脚本仅支持 Rocky Linux / RHEL / CentOS 8 系列"
fi

log "项目目录: $APP_DIR"
log "执行用户: $APP_USER"

# ============================================================================
# 第 1 步：基础工具
# ============================================================================
if ! command -v git >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
  log "安装基础工具 git curl vim ..."
  dnf install -y git curl vim
fi

# ============================================================================
# 第 2 步：Python + 虚拟环境 + 依赖
# ============================================================================
PY=""
for cand in python3.11 python3.10 python3.9; do
  if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [[ -z "$PY" ]]; then
  log "未找到可用 Python，安装 Python 3.9 (Rocky 8 AppStream)..."
  dnf module enable -y python39 || true
  dnf install -y python39 python39-pip python39-devel
  PY=python3.9
fi
log "使用 Python: $PY"

VENV="$APP_DIR/.venv"
if [[ ! -d "$VENV" ]]; then
  log "创建虚拟环境 $VENV ..."
  "$PY" -m venv "$VENV"
fi

log "升级 pip ..."
export PIP_DEFAULT_TIMEOUT=120
"$VENV/bin/pip" install --upgrade pip

if [[ ! -f "$APP_DIR/backend/requirements.txt" ]]; then
  die "未找到 backend/requirements.txt，请确认脚本位于项目根目录"
fi
log "安装后端依赖（含 torch，约 2GB，请耐心等待）..."
"$VENV/bin/pip" install -r "$APP_DIR/backend/requirements.txt" gunicorn

# ============================================================================
# 第 2.5 步：OpenCV / tkinter 运行时系统库（修复 ImportError）
# ============================================================================
log "安装 OpenCV 与 tkinter 系统依赖 ..."
dnf install -y libGL mesa-libGL mesa-libEGL glib2 fontconfig 2>/dev/null || \
  dnf install -y libGL mesa-libGL 2>/dev/null || true

case "$PY" in
  python3.11) TKPKG="python3.11-tkinter" ;;
  python3.10) TKPKG="python3.10-tkinter" ;;
  python3.9)  TKPKG="python39-tkinter" ;;
  *)          TKPKG="" ;;
esac
if [[ -n "$TKPKG" ]]; then
  dnf install -y "$TKPKG" 2>/dev/null || true
fi

log "验证关键包可导入 ..."
"$VENV/bin/python" -c "import cv2, ultralytics, pymongo, flask" 2>/dev/null || \
  warn "关键包导入验证未通过（可能仍有缺库），部署后可用 journalctl -u $SERVICE_NAME 查看"

# ============================================================================
# 第 3 步：MongoDB 6.0
# ============================================================================
if ! command -v mongod >/dev/null 2>&1; then
  log "安装 MongoDB ${MONGO_VERSION} ..."
  if [[ ! -f "/etc/yum.repos.d/mongodb-org-${MONGO_VERSION}.repo" ]]; then
    cat > "/etc/yum.repos.d/mongodb-org-${MONGO_VERSION}.repo" <<EOF
[mongodb-org-${MONGO_VERSION}]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/8/mongodb-org/${MONGO_VERSION}/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-${MONGO_VERSION}.asc
EOF
  fi
  dnf install -y mongodb-org
fi
systemctl enable --now mongod

log "等待 MongoDB 就绪 ..."
mongo_ready=0
for i in $(seq 1 30); do
  if mongosh --quiet --eval 'db.runCommand({ping:1}).ok' 2>/dev/null | grep -qx '1'; then
    mongo_ready=1
    break
  fi
  sleep 2
done
if [[ $mongo_ready -ne 1 ]]; then
  die "MongoDB 启动超时，请检查: journalctl -u mongod -n 50"
fi
log "MongoDB 已就绪"

# ============================================================================
# 第 4 步：.env 配置
# ============================================================================
if [[ ! -f "$APP_DIR/.env" ]]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  warn "已创建 .env（可稍后编辑: vim $APP_DIR/.env）"
  read -rp "是否现在输入 DeepSeek API Key？（y/N，AI 分析功能可选）" -n 1 ans
  echo
  if [[ "$ans" =~ [yY] ]]; then
    read -rp "请输入 API Key: " apikey
    if [[ -n "$apikey" ]]; then
      sed -i "s|your_deepseek_api_key_here|$apikey|" "$APP_DIR/.env"
      log "API Key 已写入 .env"
    fi
  fi
else
  log ".env 已存在，跳过配置"
fi

# ============================================================================
# 第 5 步：初始化数据库
# ============================================================================
log "初始化数据库（创建集合与索引）..."
(cd "$APP_DIR/backend" && "$VENV/bin/python" init_database.py)

# ============================================================================
# 第 6 步：目录权限（留证视频 / 上传文件）
# ============================================================================
chmod -R 777 "$APP_DIR/backend/evidence" "$APP_DIR/backend/uploads"
log "evidence / uploads 目录权限已设置"

# ============================================================================
# 第 6.5 步：前端 dist 完整性检查
# ============================================================================
if [[ ! -f "$APP_DIR/frontend/dist/index.html" ]]; then
  warn "================================================================"
  warn " frontend/dist 不存在或缺少 index.html！"
  warn " 前端产物被 .gitignore 忽略，git clone/pull 不会带过来。"
  warn " 请在【本地开发机】构建并上传："
  warn "   cd frontend && npm install && npm run build"
  warn "   然后上传 frontend/dist 到: $APP_DIR/frontend/dist/"
  warn "  （可用 scp 或 Xftp 上传）"
  warn "================================================================"
else
  log "前端 dist 已存在: $(ls "$APP_DIR/frontend/dist/assets/" 2>/dev/null | tr '\n' ' ')"
fi

# ============================================================================
# 第 7 步：Nginx + SELinux + 防火墙
# ============================================================================
if ! command -v nginx >/dev/null 2>&1; then
  log "安装 Nginx ..."
  dnf install -y nginx
fi

# --- 7.1 处理 nginx.conf 默认 server 块（避免欢迎页抢占 80 端口）---
if grep -qE '^\s*listen\s+80\s+default_server' /etc/nginx/nginx.conf 2>/dev/null; then
  warn "检测到 nginx.conf 默认 server 块（会导致显示欢迎页），备份并替换为干净配置..."
  cp -f /etc/nginx/nginx.conf "/etc/nginx/nginx.conf.bak.$(date +%s)"
  cat > /etc/nginx/nginx.conf <<'NGINXEOF'
# For more information on configuration, see:
#   * Official English Documentation: http://nginx.org/en/docs/
#   * Official Russian Documentation: http://nginx.org/ru/docs/

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

# Load dynamic modules. See /usr/share/doc/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    include /etc/nginx/conf.d/*.conf;
}
NGINXEOF
fi

# --- 7.2 写入 Nginx 站点配置（静态托管 + Vue 路由兜底 + /api 代理 + 上传限制）---
log "写入 Nginx 配置 $NGINX_CONF ..."
cat > "$NGINX_CONF" <<EOF
server {
    listen 80;
    server_name _;

    # 上传大小限制（视频文件可能较大，默认 1MB 会 413）
    client_max_body_size 200m;

    # 前端静态资源 + Vue Router 路由兜底（解决 /register 等 404）
    location / {
        root ${APP_DIR}/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # 后端接口：反向代理到 gunicorn
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
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

nginx -t || die "Nginx 配置校验失败"
systemctl enable --now nginx
systemctl reload nginx

# --- 7.3 SELinux：放行反向代理 + 家目录代码执行标签 ---
if [[ -x /usr/sbin/getenforce ]] && /usr/sbin/getenforce | grep -qi enforcing; then
  log "SELinux 为 enforcing："
  log "  - 放行反向代理（httpd_can_network_connect）..."
  setsebool -P httpd_can_network_connect 1

  # 项目若位于家目录（/root 或 /home），systemd 执行会被 SELinux 拦截（203/EXEC）
  # 给项目目录打 usr_t 标签，避免必须移动到 /opt
  if [[ "$APP_DIR" == /root/* || "$APP_DIR" == /home/* ]]; then
    warn "项目位于家目录下（SELinux 默认拦截 systemd 执行），正在打标签..."
    chcon -R -t usr_t "$APP_DIR" 2>/dev/null || \
      warn "chcon 打标签失败，如服务报 203/EXEC 请手动执行: sudo chcon -R -t usr_t $APP_DIR"
  fi
fi

# --- 7.4 防火墙放行 ---
if systemctl is-active --quiet firewalld; then
  log "放行防火墙 HTTP(80) / 5000 ..."
  firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || true
  firewall-cmd --permanent --add-port=5000/tcp >/dev/null 2>&1 || true
  firewall-cmd --reload >/dev/null 2>&1 || true
fi

# ============================================================================
# 第 7.5 步：ffmpeg 安装 + storage.py H.264 转码补丁（留证视频浏览器可播）
# ============================================================================
log "检测 ffmpeg（留证视频 H.264 转码需要）..."
if ! command -v ffmpeg >/dev/null 2>&1; then
  log "安装 ffmpeg（尝试 dnf rpmfusion）..."
  dnf install -y epel-release >/dev/null 2>&1 || true
  dnf install -y --nogpgcheck https://mirrors.aliyun.com/rpmfusion/free/el/rpmfusion-free-release-8.noarch.rpm >/dev/null 2>&1 || true
  dnf install -y --nobest ffmpeg >/dev/null 2>&1 || true
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  warn "dnf 安装 ffmpeg 失败，下载静态二进制（无需依赖）..."
  TMP_FF=$(mktemp -d)
  if curl -L --connect-timeout 30 --max-time 300 -o "$TMP_FF/ffmpeg.tar.xz" "$FFMPEG_URL" 2>/dev/null; then
    tar -xf "$TMP_FF/ffmpeg.tar.xz" -C "$TMP_FF"
    cp "$TMP_FF"/ffmpeg-*-static/ffmpeg /usr/local/bin/ffmpeg 2>/dev/null && chmod +x /usr/local/bin/ffmpeg
    rm -rf "$TMP_FF"
  else
    warn "静态 ffmpeg 下载失败（网络受限？）。留证视频将保持 mp4v 编码，浏览器可能无法播放。"
    warn "可稍后手动安装: https://johnvansickle.com/ffmpeg/"
  fi
fi

if command -v ffmpeg >/dev/null 2>&1; then
  log "ffmpeg 可用: $(ffmpeg -version 2>/dev/null | head -1)"
  if ! ffmpeg -encoders 2>/dev/null | grep -q libx264; then
    warn "当前 ffmpeg 缺少 libx264（H.264 编码器），浏览器播放可能仍受限"
  fi
else
  warn "ffmpeg 未安装，跳过 storage.py 转码补丁"
fi

# --- storage.py 转码补丁（幂等：已打过则跳过）---
STORAGE_PY="$APP_DIR/backend/modules/storage.py"
if command -v ffmpeg >/dev/null 2>&1 && [[ -f "$STORAGE_PY" ]]; then
  if grep -q '用 ffmpeg 转码为 H.264' "$STORAGE_PY"; then
    log "storage.py 已包含 H.264 转码逻辑，跳过补丁"
  else
    log "为 storage.py 添加 H.264 转码补丁（mp4v 编码浏览器不可播）..."
    cp -f "$STORAGE_PY" "$STORAGE_PY.bak.$(date +%s)"
    "$VENV/bin/python" - "$STORAGE_PY" <<'PYEOF'
import sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = """                for f in all_frames:
                    out.write(f)
                out.release()
                print(f"[Storage] 🎥 视频文件已生成: {abs_path}")"""

new = """                for f in all_frames:
                    out.write(f)
                out.release()

                # 用 ffmpeg 转码为 H.264（浏览器可播放）
                import subprocess
                tmp_mp4v = abs_path
                h264_path = abs_path.replace('.mp4', '_h264.mp4')
                try:
                    r = subprocess.run(
                        ['/usr/local/bin/ffmpeg', '-y', '-i', tmp_mp4v, '-c:v', 'libx264',
                         '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p', h264_path],
                        capture_output=True, timeout=120)
                    if r.returncode == 0 and os.path.exists(h264_path) and os.path.getsize(h264_path) > 0:
                        os.replace(h264_path, abs_path)
                        print(f"[Storage] 🎥 H.264 转码完成: {abs_path}")
                    else:
                        print(f"[Storage] ⚠️ ffmpeg 转码失败({r.returncode})，保留 mp4v: {r.stderr.decode()[-300:]}")
                except Exception as e:
                    print(f"[Storage] ⚠️ ffmpeg 异常，保留 mp4v: {e}")
                print(f"[Storage] 🎥 视频文件已生成: {abs_path}")"""

if old in c:
    c = c.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print("✅ storage.py H.264 转码补丁已应用")
else:
    # 兼容已改为 mp4v 直写的版本
    old2 = """                for f in all_frames:
                    out.write(f)
                out.release()
                print(f"[Storage] 🎥 视频文件已生成: {abs_path}")"""
    if old2 in c:
        c = c.replace(old2, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print("✅ storage.py H.264 转码补丁已应用（mp4v 版本）")
    else:
        print("⚠️ 未匹配到 storage.py 已知代码段，请手动检查")
PYEOF
  fi
fi

# ============================================================================
# 第 8 步：systemd 服务（gunicorn 常驻 + 开机自启）
# ============================================================================
log "写入 systemd 服务 /etc/systemd/system/${SERVICE_NAME}.service ..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Fall Detection Backend
After=network.target mongod.service

[Service]
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV/bin"
ExecStart=$VENV/bin/gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 --chdir $APP_DIR/backend app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

# ============================================================================
# 第 9 步：健康检查
# ============================================================================
log "等待服务启动（最多 30 秒）..."
http_code="000"
for i in $(seq 1 15); do
  http_code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ 2>/dev/null || true)
  if [[ "$http_code" == "200" || "$http_code" == "302" ]]; then
    break
  fi
  sleep 2
done

if [[ "$http_code" == "200" || "$http_code" == "302" ]]; then
  log "服务健康检查通过 (HTTP $http_code)"
else
  warn "服务未返回预期状态码（当前: $http_code），请查看日志: journalctl -u $SERVICE_NAME -n 50"
  warn "常见排查：缺库 ImportError → dnf install libGL python3.9-tkinter；SELinux 203/EXEC → chcon -R -t usr_t $APP_DIR"
fi

# ============================================================================
# 完成
# ============================================================================
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo
log "============================================================"
log " 部署完成！"
log " 物理机浏览器访问:  http://${IP:-<服务器IP>}"
log ""
log " 常用命令:"
log "   查看后端日志:  journalctl -u ${SERVICE_NAME} -f"
log "   重启后端:      systemctl restart ${SERVICE_NAME}"
log "   重载 Nginx:    systemctl reload nginx"
log "   数据库 shell:  mongosh fall_detection_db"
if [[ ! -f "$APP_DIR/frontend/dist/index.html" ]]; then
  log ""
  log " ⚠️  注意: 前端 dist 尚未上传！"
  log "     本地: cd frontend && npm install && npm run build"
  log "     然后上传 dist 到 $APP_DIR/frontend/dist/"
fi
log "============================================================"
