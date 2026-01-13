<template>
  <div class="login-container">
    <div class="background-animation"></div>
    <div class="glass-card">
      <div class="header">
        <span class="icon">📝</span>
        <h2>用户 <span class="highlight">注册</span></h2>
      </div>

      <div class="form-body">
        <div class="input-group">
          <label>用户名</label>
          <input type="text" v-model="username" placeholder="请设置用户名" />
        </div>
        <div class="input-group">
          <label>密码</label>
          <input type="password" v-model="password" placeholder="请设置密码" />
        </div>
        <div class="input-group">
          <label>确认密码</label>
          <input type="password" v-model="confirmPassword" placeholder="请再次输入密码" />
        </div>

        <p class="error-msg" v-if="errorMsg" :class="{ success: isSuccess }">{{ errorMsg }}</p>

        <button class="cyber-btn primary" @click="handleRegister" :disabled="loading">
          {{ loading ? '正在创建账户...' : '注册' }}
        </button>
        <button class="cyber-btn secondary" @click="$emit('switch-to-login')" :disabled="loading">
          返回登录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const emit = defineEmits(['switch-to-login']);
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const errorMsg = ref('');
const isSuccess = ref(false);
const loading = ref(false);

const handleRegister = async () => {
  if (!username.value || !password.value || !confirmPassword.value) {
    errorMsg.value = "所有字段都必须填写";
    isSuccess.value = false;
    return;
  }
  if (password.value !== confirmPassword.value) {
    errorMsg.value = "两次输入的密码不一致";
    isSuccess.value = false;
    return;
  }

  loading.value = true;
  errorMsg.value = '';

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    });
    const data = await res.json();
    
    if (data.success) {
      isSuccess.value = true;
      errorMsg.value = "注册成功！正在跳转至登录页...";
      setTimeout(() => {
        emit('switch-to-login');
      }, 1500);
    } else {
      isSuccess.value = false;
      errorMsg.value = data.msg;
    }
  } catch (e) {
    isSuccess.value = false;
    errorMsg.value = "注册失败：网络连接错误";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* 复用 Login.vue 的大部分样式 */
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.background-animation {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
  background: radial-gradient(circle at 50% 50%, rgba(0, 243, 255, 0.1) 0%, #0f172a 70%); /* 稍微改变色调区分注册页 */
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
.highlight { color: #00ff9d; } /* 使用绿色高亮 */

.input-group { text-align: left; margin-bottom: 15px; }
.input-group label { display: block; color: #94a3b8; font-size: 12px; margin-bottom: 6px; font-weight: 600; }
.input-group input {
  width: 100%; padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.3); color: #fff; outline: none; transition: 0.3s;
  box-sizing: border-box;
}
.input-group input:focus { border-color: #00ff9d; box-shadow: 0 0 15px rgba(0, 255, 157, 0.2); }

.cyber-btn {
  width: 100%; padding: 14px; border-radius: 8px; font-weight: bold; cursor: pointer;
  transition: 0.3s; border: none; margin-bottom: 15px; letter-spacing: 1px;
}
.cyber-btn.primary { background: linear-gradient(135deg, #00ff9d, #00b8ff); color: #000; }
.cyber-btn.primary:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0, 255, 157, 0.4); }
.cyber-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.cyber-btn.secondary { background: transparent; border: 1px solid rgba(255, 255, 255, 0.2); color: #94a3b8; font-size: 12px; }
.cyber-btn.secondary:hover { border-color: #fff; color: #fff; }

.error-msg { color: #ff0055; font-size: 13px; margin-bottom: 15px; }
.error-msg.success { color: #00ff9d; }
</style>