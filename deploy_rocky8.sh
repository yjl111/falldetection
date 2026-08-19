#!/usr/bin/env bash
# ============================================================================
# 跌倒检测与预警系统 — Rocky Linux 8 一键部署脚本
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
# 第 7 步：Nginx + SELinux + 防火墙
# ============================================================================
if ! command -v nginx >/dev/null 2>&1; then
  log "安装 Nginx ..."
  dnf install -y nginx
fi

log "写入 Nginx 配置 $NGINX_CONF ..."
cat > "$NGINX_CONF" <<'EOF'
server {
    listen 80;
    server_name _;

    # 业务接口：反向代理到 gunicorn
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

nginx -t || die "Nginx 配置校验失败"
systemctl enable --now nginx
systemctl reload nginx

if [[ -x /usr/sbin/getenforce ]] && /usr/sbin/getenforce | grep -qi enforcing; then
  log "SELinux 为 enforcing，放行反向代理（httpd_can_network_connect）..."
  setsebool -P httpd_can_network_connect 1
fi

if systemctl is-active --quiet firewalld; then
  log "放行防火墙 HTTP(80) / 5000 ..."
  firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || true
  firewall-cmd --permanent --add-port=5000/tcp >/dev/null 2>&1 || true
  firewall-cmd --reload >/dev/null 2>&1 || true
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
log "============================================================"
