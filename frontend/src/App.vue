<template>
  <div class="app-root">
    <div class="background-animation"></div>
    
    <!-- 认证视图组 -->
    <template v-if="!isLoggedIn">
      <Transition name="fade" mode="out-in">
        <!-- 根据状态切换登录或注册组件 -->
        <component 
          :is="authView === 'login' ? Login : Register" 
          @login-success="isLoggedIn = true"
          @switch-to-register="authView = 'register'"
          @switch-to-login="authView = 'login'"
        />
      </Transition>
    </template>

    <!-- 已登录状态：显示主界面 -->
    <div v-else class="main-layout">
      <nav class="top-nav">
        <div class="logo">
          <span class="icon">🛡️</span> 
          <span class="text">YOLOv8 <span class="highlight">VisionHub</span></span>
        </div>
        <div class="tabs">
          <button @click="currentTab = 'detect'" :class="{active: currentTab==='detect'}">
            <span class="btn-icon">🔍</span> 实时检测
          </button>
          <button @click="currentTab = 'train'" :class="{active: currentTab==='train'}">
            <span class="btn-icon">🧠</span> 模型训练
          </button>
          <button @click="currentTab = 'replay'" :class="{active: currentTab==='replay'}">
            <span class="btn-icon">🎬</span> 历史回放
          </button>
          <button @click="currentTab = 'statistics'" :class="{active: currentTab==='statistics'}">
            <span class="btn-icon">📊</span> 统计分析
          </button>
          <button @click="currentTab = 'alarm'" :class="{active: currentTab==='alarm'}">
            <span class="btn-icon">🔔</span> 报警管理
          </button>
          <button @click="currentTab = 'settings'" :class="{active: currentTab==='settings'}">
            <span class="btn-icon">⚙️</span> 系统配置
          </button>
        </div>
        <!-- 登出按钮 -->
        <button class="logout-btn" @click="handleLogout">退出 ➜</button>
      </nav>

      <main class="content-wrapper">
        <Transition name="fade" mode="out-in">
          <component :is="activeComponent" />
        </Transition>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Login from './components/Login.vue';
import Register from './components/Register.vue';
import DetectionDashboard from './components/DetectionDashboard.vue';
import TrainingDashboard from './components/TrainingDashboard.vue';
import VideoReplay from './components/VideoReplay.vue';
import StatisticsDashboard from './components/StatisticsDashboard.vue';
import AlarmManagement from './components/AlarmManagement.vue';
import SystemSettings from './components/SystemSettings.vue';
import { computed } from 'vue';

const isLoggedIn = ref(false);
const authView = ref('login'); // 控制当前显示 'login' 还是 'register'
const currentTab = ref('detect');

const activeComponent = computed(() => {
  switch (currentTab.value) {
    case 'detect': return DetectionDashboard;
    case 'train': return TrainingDashboard;
    case 'replay': return VideoReplay;
    case 'statistics': return StatisticsDashboard;
    case 'alarm': return AlarmManagement;
    case 'settings': return SystemSettings;
    default: return DetectionDashboard;
  }
});

onMounted(() => {
  // 检查本地是否有 Token，如果有则自动登录
  if (localStorage.getItem('token')) {
    isLoggedIn.value = true;
  }
});

const handleLogout = () => {
  localStorage.removeItem('token');
  isLoggedIn.value = false;
  authView.value = 'login'; // 登出后重置为登录页
};
</script>

<style>
/* ... (保留你之前的全局样式，无需变动) ... */
/* 新增登出按钮样式 */
.logout-btn {
  background: transparent; border: 1px solid rgba(255,0,85,0.3); color: #ff0055;
  padding: 6px 15px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold;
  transition: 0.3s;
}
.logout-btn:hover { background: rgba(255,0,85,0.1); box-shadow: 0 0 10px rgba(255,0,85,0.2); }

:root {
  --bg-dark: #0f172a;
  --bg-panel: rgba(30, 41, 59, 0.75);
  --primary: #00f3ff;
  --secondary: #7000ff;
  --success: #00ff9d;
  --text-main: #f1f5f9;
  --text-dim: #94a3b8;
  --border: rgba(255, 255, 255, 0.1);
  --glass: blur(12px);
  --shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

body { margin: 0; background-color: var(--bg-dark); color: var(--text-main); font-family: 'Inter', sans-serif; overflow: hidden; }

.background-animation {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1;
  background: radial-gradient(circle at 10% 20%, rgba(112, 0, 255, 0.15) 0%, transparent 40%),
              radial-gradient(circle at 90% 80%, rgba(0, 243, 255, 0.1) 0%, transparent 40%);
  animation: pulseBg 10s infinite alternate;
}
@keyframes pulseBg { 0% { transform: scale(1); } 100% { transform: scale(1.1); } }

.top-nav { display: flex; align-items: center; justify-content: space-between; padding: 0 30px; height: 64px; background: rgba(15, 23, 42, 0.8); backdrop-filter: var(--glass); border-bottom: 1px solid var(--border); }
.logo { font-size: 20px; font-weight: 800; color: #fff; letter-spacing: 1px; display: flex; align-items: center; gap: 10px; }
.logo .highlight { background: linear-gradient(90deg, var(--primary), var(--success)); -webkit-background-clip: text; color: transparent; }

.tabs { display: flex; gap: 15px; background: rgba(255,255,255,0.05); padding: 5px; border-radius: 30px; border: 1px solid var(--border); }
.tabs button { background: transparent; border: none; color: var(--text-dim); padding: 8px 24px; cursor: pointer; font-size: 14px; font-weight: 600; border-radius: 20px; transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; }
.tabs button:hover { color: #fff; }
.tabs button.active { background: linear-gradient(135deg, var(--secondary), #4c1d95); color: #fff; box-shadow: 0 2px 10px rgba(112, 0, 255, 0.4); }

.content-wrapper { height: calc(100vh - 64px); position: relative; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>