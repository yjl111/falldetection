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
          <label>用户名</label>
          <input type="text" v-model="username" placeholder="请输入用户名" />
        </div>
        <div class="input-group">
          <label>密码</label>
          <input type="password" v-model="password" placeholder="请输入密码" />
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
import { ref } from 'vue';

// 定义两个事件：登录成功，切换到注册
const emit = defineEmits(['login-success', 'switch-to-register']);
const username = ref('');
const password = ref('');
const errorMsg = ref('');
const loading = ref(false);

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMsg.value = "用户名或密码不能为空";
    return;
  }
  loading.value = true;
  errorMsg.value = '';

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    });
    const data = await res.json();
    if (data.success) {
      localStorage.setItem('token', data.token); 
      emit('login-success'); 
    } else {
      errorMsg.value = data.msg;
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
</style>