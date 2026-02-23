<template>
  <div class="settings-layout">
    <div class="settings-sidebar">
      <div class="sidebar-menu glass-panel">
        <div 
          v-for="item in menuItems" 
          :key="item.id"
          class="menu-item"
          :class="{ active: activeMenu === item.id }"
          @click="activeMenu = item.id"
        >
          <span class="menu-icon">{{ item.icon }}</span>
          <span class="menu-label">{{ item.label }}</span>
        </div>
      </div>
    </div>

    <div class="settings-content">
      <!-- 检测参数设置 -->
      <div v-show="activeMenu === 'detection'" class="settings-panel glass-panel">
        <h2>🎯 检测参数设置</h2>
        
        <div class="setting-group">
          <label>置信度阈值</label>
          <div class="slider-control">
            <input type="range" v-model="detection.confidence" min="0" max="1" step="0.01" class="slider">
            <span class="value">{{ detection.confidence }}</span>
          </div>
          <p class="hint">设置目标检测的最低置信度，值越高误检越少但可能漏检</p>
        </div>

        <div class="setting-group">
          <label>IoU 阈值</label>
          <div class="slider-control">
            <input type="range" v-model="detection.iou" min="0" max="1" step="0.01" class="slider">
            <span class="value">{{ detection.iou }}</span>
          </div>
          <p class="hint">用于非极大值抑制，控制重叠框的过滤程度</p>
        </div>

        <div class="setting-group">
          <div class="group-title">检测区域</div>
          <div class="checkbox-group">
            <label class="checkbox-label"><input type="checkbox" v-model="detection.areas.bedroom"> 卧室</label>
            <label class="checkbox-label"><input type="checkbox" v-model="detection.areas.livingroom"> 客厅</label>
            <label class="checkbox-label"><input type="checkbox" v-model="detection.areas.bathroom"> 浴室</label>
            <label class="checkbox-label"><input type="checkbox" v-model="detection.areas.kitchen"> 厨房</label>
          </div>
        </div>

        <button @click="saveDetection" class="btn-save">保存检测设置</button>
      </div>

      <!-- 存储设置 -->
      <div v-show="activeMenu === 'storage'" class="settings-panel glass-panel">
        <h2>💾 存储设置</h2>

        <div class="setting-group">
          <label>视频留证时长</label>
          <div class="time-config">
            <div class="time-item">
              <span>跌倒前</span>
              <input type="number" v-model="storage.beforeSeconds" min="0" max="10" class="time-input">
              <span>秒</span>
            </div>
            <div class="time-item">
              <span>跌倒后</span>
              <input type="number" v-model="storage.afterSeconds" min="0" max="10" class="time-input">
              <span>秒</span>
            </div>
          </div>
        </div>

        <div class="setting-group">
          <label>存储路径</label>
          <div class="path-input">
            <input type="text" v-model="storage.path" readonly>
            <button class="btn-browse">浏览</button>
          </div>
        </div>

        <div class="setting-group">
          <label>自动清理策略</label>
          <select v-model="storage.autoClean" class="select-input">
            <option value="never">从不清理</option>
            <option value="7d">保留7天</option>
            <option value="30d">保留30天</option>
            <option value="90d">保留90天</option>
          </select>
        </div>

        <div class="storage-info">
          <div class="info-item">
            <span class="label">已用空间</span>
            <span class="value">2.3 GB / 10 GB</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: 23%"></div>
          </div>
        </div>

        <button @click="saveStorage" class="btn-save">保存存储设置</button>
      </div>

      <!-- 系统配置 -->
      <div v-show="activeMenu === 'system'" class="settings-panel glass-panel">
        <h2>⚙️ 系统配置</h2>

        <div class="setting-group">
          <label>系统语言</label>
          <select v-model="system.language" class="select-input">
            <option value="zh-CN">简体中文</option>
            <option value="en-US">English</option>
          </select>
        </div>

        <div class="setting-group">
          <label>主题模式</label>
          <div class="theme-selector">
            <div class="theme-option" :class="{ active: system.theme === 'dark' }" @click="system.theme = 'dark'">
              <span class="theme-icon">🌙</span>
              <span>暗色</span>
            </div>
            <div class="theme-option" :class="{ active: system.theme === 'light' }" @click="system.theme = 'light'">
              <span class="theme-icon">☀️</span>
              <span>亮色</span>
            </div>
          </div>
        </div>

        <div class="setting-group">
          <div class="group-title">系统日志</div>
          <div class="log-config">
            <label class="checkbox-label"><input type="checkbox" v-model="system.logs.enable"> 启用日志记录</label>
            <label class="checkbox-label"><input type="checkbox" v-model="system.logs.debug"> 调试模式</label>
          </div>
        </div>

        <div class="setting-group">
          <div class="group-title">数据库备份</div>
          <div class="backup-actions">
            <button class="btn-action">立即备份</button>
            <button class="btn-action">恢复备份</button>
          </div>
        </div>

        <button @click="saveSystem" class="btn-save">保存系统设置</button>
      </div>

      <!-- 高级设置 -->
      <div v-show="activeMenu === 'advanced'" class="settings-panel glass-panel">
        <h2>🔧 高级设置</h2>

        <div class="setting-group">
          <label class="toggle-wrapper">
            <div class="toggle-container">
              <input type="checkbox" v-model="advanced.gpu" class="toggle-input">
              <span class="toggle-slider"></span>
            </div>
            <span class="toggle-text">启用 CUDA 加速（需要 NVIDIA 显卡）</span>
          </label>
        </div>

        <div class="setting-group">
          <label>多线程处理</label>
          <div class="slider-control">
            <input type="range" v-model="advanced.workers" min="1" max="8" step="1" class="slider">
            <span class="value">{{ advanced.workers }} 线程</span>
          </div>
        </div>

        <div class="setting-group">
          <label>API 服务器</label>
          <input type="text" v-model="advanced.apiUrl" class="text-input" placeholder="http://localhost:5000">
        </div>

        <div class="danger-zone">
          <h3>⚠️ 危险操作</h3>
          <button class="btn-danger">重置所有设置</button>
          <button class="btn-danger">清空所有数据</button>
        </div>

        <button @click="saveAdvanced" class="btn-save">保存高级设置</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const activeMenu = ref('detection');

const menuItems = [
  { id: 'detection', icon: '🎯', label: '检测参数' },
  { id: 'storage', icon: '💾', label: '存储设置' },
  { id: 'system', icon: '⚙️', label: '系统配置' },
  { id: 'advanced', icon: '🔧', label: '高级设置' }
];

const detection = ref({
  confidence: 0.30,
  iou: 0.45,
  areas: {
    bedroom: true,
    livingroom: true,
    bathroom: true,
    kitchen: false
  }
});

const storage = ref({
  beforeSeconds: 3,
  afterSeconds: 2,
  path: 'D:\\falldetection\\backend\\evidence',
  autoClean: '30d'
});

const system = ref({
  language: 'zh-CN',
  theme: 'dark',
  logs: {
    enable: true,
    debug: false
  }
});

const advanced = ref({
  gpu: false,
  workers: 4,
  apiUrl: 'http://localhost:5000'
});

const saveDetection = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ detection: detection.value })
    });
    const result = await response.json();
    alert(result.message || '检测设置已保存！');
  } catch (error) {
    console.error('保存失败:', error);
    alert('保存失败，请检查网络连接');
  }
};
const saveStorage = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ storage: storage.value })
    });
    const result = await response.json();
    alert(result.message || '存储设置已保存！');
  } catch (error) {
    console.error('保存失败:', error);
    alert('保存失败，请检查网络连接');
  }
};
const saveSystem = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ system: system.value })
    });
    const result = await response.json();
    alert(result.message || '系统设置已保存！');
  } catch (error) {
    console.error('保存失败:', error);
    alert('保存失败，请检查网络连接');
  }
};
const saveAdvanced = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ advanced: advanced.value })
    });
    const result = await response.json();
    alert(result.message || '高级设置已保存！');
  } catch (error) {
    console.error('保存失败:', error);
    alert('保存失败，请检查网络连接');
  }
};

// 加载系统设置
const loadSettings = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/settings');
    const settings = await response.json();
    
    detection.value = settings.detection;
    storage.value = settings.storage;
    system.value = settings.system;
    advanced.value = settings.advanced;
  } catch (error) {
    console.error('加载设置失败:', error);
  }
};

onMounted(() => {
  loadSettings();
});
</script>

<style scoped>
.settings-layout { padding: 30px; display: grid; grid-template-columns: 250px 1fr; gap: 30px; height: 100%; overflow: hidden; }
.glass-panel { background: var(--bg-panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow); padding: 24px; }

.settings-sidebar { overflow-y: auto; }
.sidebar-menu { padding: 12px; }
.menu-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; transition: 0.3s; }
.menu-item:hover { background: rgba(255,255,255,0.05); }
.menu-item.active { background: var(--primary); color: #000; }
.menu-icon { font-size: 20px; }
.menu-label { font-size: 14px; font-weight: 500; }

.settings-content { overflow-y: auto; }
.settings-panel h2 { margin: 0 0 30px 0; font-size: 22px; color: #fff; }

.setting-group { margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.setting-group:last-of-type { border-bottom: none; }
.setting-group > label { display: block; font-size: 14px; color: #fff; font-weight: bold; margin-bottom: 12px; }
.group-title { display: block; font-size: 14px; color: #fff; font-weight: bold; margin-bottom: 12px; }
.hint { font-size: 12px; color: var(--text-dim); margin-top: 8px; font-style: italic; }

.slider-control { display: flex; align-items: center; gap: 15px; }
.slider { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; outline: none; -webkit-appearance: none; }
.slider::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; background: var(--primary); border-radius: 50%; cursor: pointer; }
.value { font-size: 14px; color: var(--primary); font-weight: bold; min-width: 50px; }

.checkbox-group { display: flex; flex-direction: column; gap: 10px; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #fff; cursor: pointer; font-weight: normal; }

.time-config { display: flex; gap: 20px; }
.time-item { display: flex; align-items: center; gap: 8px; color: #fff; }
.time-input { width: 60px; background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 4px; text-align: center; }

.path-input { display: flex; gap: 10px; }
.path-input input { flex: 1; background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 4px; }
.btn-browse { background: rgba(0,243,255,0.2); border: 1px solid var(--primary); color: var(--primary); padding: 10px 20px; border-radius: 4px; cursor: pointer; }

.select-input { width: 100%; background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 4px; }

.storage-info { background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; margin-top: 20px; }
.info-item { display: flex; justify-content: space-between; margin-bottom: 10px; color: #fff; font-size: 13px; }
.progress-bar { height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--primary), var(--secondary)); }

.theme-selector { display: flex; gap: 15px; }
.theme-option { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px; background: rgba(0,0,0,0.2); border: 2px solid transparent; border-radius: 8px; cursor: pointer; transition: 0.3s; }
.theme-option.active { border-color: var(--primary); background: rgba(0,243,255,0.1); }
.theme-icon { font-size: 32px; }

.log-config { display: flex; flex-direction: column; gap: 10px; }

.backup-actions { display: flex; gap: 10px; }
.btn-action { background: rgba(0,243,255,0.2); border: 1px solid var(--primary); color: var(--primary); padding: 10px 20px; border-radius: 4px; cursor: pointer; }

.toggle-wrapper { display: flex; align-items: center; gap: 12px; cursor: pointer; font-weight: normal; }
.toggle-container { display: flex; align-items: center; }
.toggle-input { display: none; }
.toggle-slider { width: 40px; height: 20px; background: #333; border-radius: 20px; position: relative; transition: 0.3s; }
.toggle-slider::before { content: ''; position: absolute; width: 16px; height: 16px; background: #666; border-radius: 50%; top: 2px; left: 2px; transition: 0.3s; }
.toggle-input:checked + .toggle-slider { background: var(--primary); }
.toggle-input:checked + .toggle-slider::before { transform: translateX(20px); background: #fff; }
.toggle-text { color: #fff; font-size: 14px; }

.text-input { width: 100%; background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 4px; }

.danger-zone { background: rgba(255,0,85,0.1); border: 1px solid rgba(255,0,85,0.3); padding: 20px; border-radius: 8px; margin-top: 30px; }
.danger-zone h3 { color: #ff0055; margin: 0 0 15px 0; font-size: 14px; }
.btn-danger { background: transparent; border: 1px solid #ff0055; color: #ff0055; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px; }

.btn-save { width: 100%; background: linear-gradient(135deg, var(--primary), #0099cc); color: #000; border: none; padding: 14px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 30px; font-size: 15px; }
</style>
