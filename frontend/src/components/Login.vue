<template>
  <div class="login-container">
    <div class="background-animation"></div>
    <div class="glass-card">
      <div class="header">
        <span class="icon">🛡️</span>
        <h2>系统 <span class="highlight">登录</span></h2>
      </div>

      <div class="form-body">
        <div class="input-group">
          <label>登录端口</label>
          <div class="portal-switch">
            <button
              type="button"
              class="portal-btn"
              :class="{ active: loginPortal === 'user' }"
              @click="loginPortal = 'user'"
            >
              用户端
            </button>
            <button
              type="button"
              class="portal-btn"
              :class="{ active: loginPortal === 'admin' }"
              @click="loginPortal = 'admin'"
            >
              管理端
            </button>
          </div>
        </div>

        <div class="input-group">
          <label>用户名</label>
          <input type="text" v-model="username" placeholder="请输入用户名" />
        </div>
        <div class="input-group">
          <label>密码</label>
          <input type="password" v-model="password" placeholder="请输入密码" />
        </div>

        <div class="input-group captcha-group">
          <label>验证码</label>
          <div class="captcha-row">
            <input type="text" v-model="captchaInput" placeholder="请输入验证码" maxlength="4" />
            <canvas ref="captchaCanvas" width="110" height="40" @click="refreshCaptcha" title="点击刷新"></canvas>
          </div>
        </div>

        <p class="error-msg" v-if="errorMsg">{{ errorMsg }}</p>

        <button class="cyber-btn primary" @click="handleLogin" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <!-- 修改：点击按钮不再直接注册，而是触发切换事件 -->
        <button class="cyber-btn secondary" @click="$emit('switch-to-register')" :disabled="loading">
          注册新用户
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// 定义两个事件：登录成功，切换到注册
const emit = defineEmits(['login-success', 'switch-to-register']);
const username = ref('');
const password = ref('');
const loginPortal = ref('user');
const captchaInput = ref('');
const captchaCode = ref('');
const captchaCanvas = ref(null);
const errorMsg = ref('');
const loading = ref(false);

const CHARS = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678';

function generateCaptcha() {
  let code = '';
  for (let i = 0; i < 4; i++) {
    code += CHARS[Math.floor(Math.random() * CHARS.length)];
  }
  return code;
}

function drawCaptcha(code) {
  const canvas = captchaCanvas.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  // 背景
  ctx.clearRect(0, 0, w, h);
  const grad = ctx.createLinearGradient(0, 0, w, h);
  grad.addColorStop(0, '#1e2a3a');
  grad.addColorStop(1, '#0f172a');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  // 干扰线
  for (let i = 0; i < 4; i++) {
    ctx.strokeStyle = `hsla(${Math.random() * 360},60%,60%,0.5)`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(Math.random() * w, Math.random() * h);
    ctx.lineTo(Math.random() * w, Math.random() * h);
    ctx.stroke();
  }

  // 干扰点
  for (let i = 0; i < 30; i++) {
    ctx.fillStyle = `hsla(${Math.random() * 360},60%,70%,0.6)`;
    ctx.beginPath();
    ctx.arc(Math.random() * w, Math.random() * h, 1, 0, 2 * Math.PI);
    ctx.fill();
  }

  // 字符
  const colors = ['#00f3ff', '#7000ff', '#ff6b6b', '#ffd93d', '#6bcb77'];
  for (let i = 0; i < code.length; i++) {
    ctx.save();
    ctx.font = `bold ${22 + Math.random() * 6}px monospace`;
    ctx.fillStyle = colors[i % colors.length];
    const x = 12 + i * 24;
    const y = 28 + (Math.random() * 6 - 3);
    ctx.translate(x, y);
    ctx.rotate((Math.random() - 0.5) * 0.5);
    ctx.fillText(code[i], 0, 0);
    ctx.restore();
  }
}

function refreshCaptcha() {
  captchaCode.value = generateCaptcha();
  captchaInput.value = '';
  drawCaptcha(captchaCode.value);
}

onMounted(() => {
  refreshCaptcha();
});

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMsg.value = "用户名或密码不能为空";
    return;
  }
  if (!captchaInput.value) {
    errorMsg.value = "请输入验证码";
    return;
  }
  if (captchaInput.value.toLowerCase() !== captchaCode.value.toLowerCase()) {
    errorMsg.value = "验证码错误，请重新输入";
    refreshCaptcha();
    return;
  }
  loading.value = true;
  errorMsg.value = '';

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
        expected_role: loginPortal.value
      })
    });
    const data = await res.json();
    if (data.success) {
      localStorage.setItem('token', data.token);
      localStorage.setItem('username', data.username || username.value);
      localStorage.setItem('role', data.role || 'user');
      localStorage.setItem('login_portal', loginPortal.value);
      emit('login-success', { username: data.username || username.value, role: data.role || 'user' });
    } else {
      errorMsg.value = data.msg;
      refreshCaptcha();
    }
  } catch (e) {
    errorMsg.value = "登录失败：网络连接错误";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.background-animation {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
  background: radial-gradient(circle at 50% 50%, rgba(112, 0, 255, 0.1) 0%, #0f172a 70%);
}

.glass-card {
  width: 360px;
  padding: 40px;
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  text-align: center;
}

.header { margin-bottom: 30px; }
.header .icon { font-size: 40px; display: block; margin-bottom: 10px; }
.header h2 { font-size: 24px; color: #fff; margin: 0; font-weight: 700; letter-spacing: 1px; }
.highlight { color: #00f3ff; }

.input-group { text-align: left; margin-bottom: 20px; }
.input-group label { display: block; color: #94a3b8; font-size: 12px; margin-bottom: 8px; font-weight: 600; }
.input-group input {
  width: 100%; padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.3); color: #fff; outline: none; transition: 0.3s;
  box-sizing: border-box; 
}
.input-group input:focus { border-color: #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); }

.portal-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.portal-btn {
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(0, 0, 0, 0.25);
  color: #94a3b8;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
  font-weight: 700;
}
.portal-btn.active {
  border-color: #00f3ff;
  color: #fff;
  background: linear-gradient(135deg, rgba(0, 243, 255, 0.22), rgba(112, 0, 255, 0.22));
  box-shadow: 0 0 16px rgba(0, 243, 255, 0.15);
}

.cyber-btn {
  width: 100%; padding: 14px; border-radius: 8px; font-weight: bold; cursor: pointer;
  transition: 0.3s; border: none; margin-bottom: 15px; letter-spacing: 1px;
}
.cyber-btn.primary { background: linear-gradient(135deg, #7000ff, #4c1d95); color: #fff; }
.cyber-btn.primary:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(112, 0, 255, 0.4); }
.cyber-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.cyber-btn.secondary { background: transparent; border: 1px solid rgba(255, 255, 255, 0.2); color: #94a3b8; font-size: 12px; }
.cyber-btn.secondary:hover { border-color: #00f3ff; color: #00f3ff; }

.error-msg { color: #ff0055; font-size: 13px; margin-bottom: 15px; }

.captcha-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.captcha-row input {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
  outline: none;
  transition: 0.3s;
  box-sizing: border-box;
  font-size: 14px;
}
.captcha-row input:focus { border-color: #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); }
.captcha-row canvas {
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.15);
  flex-shrink: 0;
}
.captcha-row canvas:hover { border-color: #00f3ff; }
</style>
