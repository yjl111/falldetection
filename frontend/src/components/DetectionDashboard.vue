<template>
  <div class="gui-layout" @click="unlockAudio">
    <audio ref="alarmAudio" src="https://www.soundjay.com/buttons/beep-01a.mp3" loop></audio>

    <div class="alarm-overlay" v-if="isAlarm">
      <div class="alarm-banner">⚠️ 危险警报：检测到跌倒 ⚠️</div>
    </div>

    <transition name="fade">
      <div v-if="showReportModal" class="modal-overlay" @click.self="showReportModal = false">
        <div class="modal-content glass-panel">
          <div class="modal-header">
            <h3>🤖 AI 智能安全简报</h3>
            <button class="close-icon" @click="showReportModal = false">×</button>
          </div>
          <div class="report-body custom-scrollbar">
            <pre>{{ aiReport }}</pre>
          </div>
          <div class="modal-footer">
            <button class="neon-btn secondary" @click="showReportModal = false">关闭</button>
            <button class="neon-btn" @click="generateReport" :disabled="reportLoading">
              {{ reportLoading ? '分析中...' : '🔄 重新生成' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <aside class="sidebar glass-panel">
      <div class="panel-section">
        <h3><span class="deco">#</span> 任务选择</h3>
        <div class="radio-card">
          <label class="radio-item active"><span class="status-indicator glow"></span> 目标检测+姿态估计</label>
        </div>
      </div>

      <div class="panel-section">
        <h3><span class="deco">#</span> 模型选择</h3>
        <div class="select-wrapper">
          <select class="cyber-select">
            <option>🚀 best.pt (自定义模型)</option>
            <option>📦 yolov8n.pt (官方基础模型)</option>
          </select>
          <div class="select-arrow">▼</div>
        </div>
      </div>
      
      <div class="panel-section">
        <div class="section-header">
          <h3><span class="deco">#</span> 输入源</h3>
        </div>
        <div class="action-grid">
          <button 
            class="cyber-btn" 
            :class="{ active: activeSource === 'file', 'is-loading': activeSource === 'switching' }"
            @click="$refs.fileInput.click()"
            :disabled="activeSource === 'switching'"
          >
            <span class="icon">📁</span>
            <span class="label">上传文件</span>
          </button>

          <button 
            class="cyber-btn" 
            :class="{ active: activeSource === 'webcam', 'is-loading': activeSource === 'switching' }"
            @click="toggleWebcam()"
            :disabled="activeSource === 'switching'"
          >
            <span class="icon">📷</span>
            <span class="label">{{ activeSource === 'webcam' ? '关闭摄像头' : '实时监控' }}</span>
          </button>
          
          <input type="file" ref="fileInput" @change="handleUpload" hidden accept="video/*,image/*" />
        </div>
      </div>

      <div class="panel-section">
        <h3><span class="deco">#</span> 参数设置</h3>
        <div class="param-item">
          <div class="param-header"><span>置信度阈值</span><span class="param-val">{{ conf }}</span></div>
          <input type="range" v-model="conf" min="0" max="1" step="0.01" @input="updateParams" class="cyber-range">
        </div>
        <div class="param-item">
          <div class="param-header"><span>IoU 阈值</span><span class="param-val">{{ iou }}</span></div>
          <input type="range" v-model="iou" min="0" max="1" step="0.01" @input="updateParams" class="cyber-range secondary">
        </div>
      </div>

      <div class="panel-section">
        <h3><span class="deco">#</span> 智能分析</h3>
        <button 
          class="cyber-btn ai-btn" 
          @click="generateReport"
          :disabled="reportLoading"
        >
          <span class="icon" v-if="!reportLoading">📊</span>
          <span class="icon spin" v-else>⏳</span>
          <span class="label">{{ reportLoading ? 'AI 正在分析...' : '生成安全简报' }}</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <div class="video-wrapper">
        <div class="video-frame" :class="{ 'live': isStreaming, 'alarm-state': isAlarm }">
          <div class="corner t-l"></div><div class="corner t-r"></div><div class="corner b-l"></div><div class="corner b-r"></div>
          
          <img v-if="isStreaming" :src="`${streamUrl}?t=${streamKey}`" :key="streamKey" class="video-feed" alt="Video Feed" />
          
          <div v-if="isStreaming" class="control-overlay">
            <button class="pause-btn" @click.stop="togglePause" :title="isPaused ? '继续播放' : '暂停'">
              {{ isPaused ? '▶' : '❚❚' }}
            </button>
          </div>

          <div v-else class="video-placeholder">
            <div class="placeholder-content">
              <div class="radar-scan"></div>
              <div class="status-text">{{ activeSource === 'switching' ? '系统初始化中...' : '系统待机' }}</div>
              <div class="placeholder-actions" v-if="activeSource !== 'switching'">
                <button class="neon-btn" @click="toggleWebcam()">开启摄像头</button>
                <button class="neon-btn secondary" @click="$refs.fileInput.click()">上传文件</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="data-panel glass-panel">
        <div class="panel-header">
          <h4>📊 实时检测分析</h4>
          <span class="count-badge" :class="{alert: isAlarm}">
            {{ isAlarm ? '⚠️ 警报触发' : tableData.length + ' 个目标' }}
          </span>
        </div>
        <div class="table-scroll custom-scrollbar">
          <table class="cyber-table">
            <thead>
              <tr>
                <th width="10%">ID</th>
                <th width="25%">状态</th>
                <th width="30%">置信度</th>
                <th width="35%">空间数据</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="isStreaming">
                <tr v-for="row in tableData" :key="row.id">
                  <td class="id-col">#{{ row.id }}</td>
                  <td>
                    <span class="status-tag" :class="getStatusClass(row.class)">
                      <span class="dot"></span> {{ formatClass(row.class) }}
                    </span>
                  </td>
                  <td>
                    <div class="conf-wrapper">
                      <div class="progress-bg">
                        <div class="progress-fill" 
                             :style="{ width: row.conf, background: getConfColor(row.conf) }">
                        </div>
                      </div>
                      <span class="conf-text">{{ row.conf }}</span>
                    </div>
                  </td>
                  <td class="mono-text">
                    {{ formatBBox(row.bbox) }}
                  </td>
                </tr>
              </template>
              
              <tr v-if="!isStreaming || tableData.length === 0">
                <td colspan="4" class="empty-state">
                  {{ isPaused ? '系统已暂停' : (activeSource === 'switching' ? '正在切换输入源...' : (!isStreaming ? '系统离线' : '正在扫描...')) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, onBeforeUnmount, watch } from 'vue';

// --- 状态定义 ---
const isStreaming = ref(false); 
const isAlarm = ref(false); 
const isPaused = ref(false);
const activeSource = ref(null); // 'webcam' | 'file' | 'switching' | null
const alarmAudio = ref(null);
const audioUnlocked = ref(false);
const conf = ref(0.30);
const iou = ref(0.45);
const tableData = ref([]);
const streamUrl = ref('http://localhost:5000/video_feed'); // 建议使用完整URL避免相对路径问题
const streamKey = ref(Date.now());
let timer = null;

// --- AI 报告相关状态 ---
const reportLoading = ref(false);
const aiReport = ref('');
const showReportModal = ref(false);

// --- 监听与生命周期 ---
watch(isStreaming, (newVal) => { 
  if (!newVal) {
    tableData.value = [];
    isAlarm.value = false;
    isPaused.value = false;
  }
});

watch(isAlarm, (newVal) => {
  if (newVal && audioUnlocked.value && alarmAudio.value) {
    alarmAudio.value.play().catch(e => console.log("Audio play failed", e));
  } else if (!newVal && alarmAudio.value) {
    alarmAudio.value.pause();
    alarmAudio.value.currentTime = 0;
  }
});

onMounted(() => {
  timer = setInterval(fetchData, 500); // 降低频率到 500ms 减少负载
});

onUnmounted(() => {
  clearInterval(timer);
  stopStream();
});

// --- 核心逻辑方法 ---

const fetchData = async () => {
  if (!isStreaming.value || isPaused.value) return;
  
  try {
    const res = await fetch('http://localhost:5000/data');
    const data = await res.json();
    
    // 更新数据表
    if (data.data) {
      tableData.value = data.data;
      
      // 检测是否包含 "fall"
      const hasFall = data.data.some(item => item.class.toLowerCase().includes('fall'));
      isAlarm.value = hasFall;
    }
  } catch (e) {
    console.error("Data fetch error", e);
  }
};

const updateParams = async () => {
  try {
    await fetch('http://localhost:5000/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conf: parseFloat(conf.value), iou: parseFloat(iou.value) })
    });
  } catch (e) {
    console.error("Settings update failed", e);
  }
};

// AI 报告生成逻辑
const generateReport = async () => {
  reportLoading.value = true;
  aiReport.value = ''; // 清空旧内容
  
  try {
    const response = await fetch('http://localhost:5000/api/report/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();

    if (data.success) {
      aiReport.value = data.report;
      showReportModal.value = true;
    } else {
      alert("生成失败: " + (data.error || "未知错误"));
    }
  } catch (error) {
    console.error("AI Report Error:", error);
    alert("无法连接到后端服务器，请确认后端已启动。");
  } finally {
    reportLoading.value = false;
  }
};

// --- 控制逻辑 ---

const toggleWebcam = async () => {
  if (activeSource.value === 'switching') return;
  
  const targetState = activeSource.value === 'webcam' ? null : 'webcam';
  await switchSource(targetState, 'webcam');
};

const handleUpload = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  // 上传文件逻辑
  const formData = new FormData();
  formData.append('file', file);
  
  await switchSource('file', 'upload', formData);
  e.target.value = ''; // 重置 input
};

const switchSource = async (targetState, type, payload = null) => {
  activeSource.value = 'switching';
  isStreaming.value = false;
  
  try {
    // 1. 停止当前流
    await fetch('http://localhost:5000/stop_stream', { method: 'POST' });
    
    // 2. 如果是开启新源
    if (targetState) {
      let url = type === 'webcam' ? 'http://localhost:5000/start_webcam' : 'http://localhost:5000/upload_video';
      let options = { method: 'POST' };
      
      if (payload) {
        options.body = payload; // FormData for upload
      }
      
      const res = await fetch(url, options);
      const data = await res.json();
      
      if (data.success) {
        activeSource.value = targetState;
        isStreaming.value = true;
        streamKey.value = Date.now(); // 强制刷新 img src
      } else {
        alert("启动失败: " + data.error);
        activeSource.value = null;
      }
    } else {
      activeSource.value = null;
    }
  } catch (e) {
    console.error("Switch source failed", e);
    activeSource.value = null;
  }
};

const stopStream = async () => {
  isStreaming.value = false;
  activeSource.value = null;
  await fetch('http://localhost:5000/stop_stream', { method: 'POST' });
};

const togglePause = () => {
  isPaused.value = !isPaused.value;
};

const unlockAudio = () => {
  if (!audioUnlocked.value && alarmAudio.value) {
    alarmAudio.value.play().then(() => {
      alarmAudio.value.pause();
      audioUnlocked.value = true;
    }).catch(() => {});
  }
};

// --- 辅助格式化方法 ---
const formatBBox = (bbox) => {
  if (!bbox) return '-';
  return `[${bbox.map(n => Math.round(n)).join(', ')}]`;
};

const formatClass = (cls) => {
  if (!cls) return 'Unknown';
  return cls.charAt(0).toUpperCase() + cls.slice(1);
};

const getStatusClass = (cls) => {
  const c = cls.toLowerCase();
  if (c.includes('fall')) return 'status-danger';
  if (c.includes('person')) return 'status-success';
  return 'status-warning';
};

const getConfColor = (conf) => {
  if (conf > 0.8) return '#00ff9d'; // Green
  if (conf > 0.5) return '#ffaa00'; // Orange
  return '#ff4444'; // Red
};
</script>

<style scoped>
/* 全局布局 */
.gui-layout {
  display: flex;
  height: 100vh;
  background: #050505;
  color: #e0e0e0;
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  overflow: hidden;
  --primary: #00f3ff;
  --primary-dim: rgba(0, 243, 255, 0.1);
  --secondary: #7d44ff;
  --danger: #ff2a2a;
  --glass-bg: rgba(20, 20, 30, 0.7);
  --border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 玻璃面板通用样式 */
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border: var(--border);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

/* 侧边栏 */
.sidebar {
  width: 300px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 25px;
  border-right: 1px solid rgba(0, 243, 255, 0.2);
  z-index: 10;
}

.panel-section h3 {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 12px;
  color: #889;
  display: flex;
  align-items: center;
}

.deco {
  color: var(--primary);
  margin-right: 8px;
  font-weight: bold;
}

/* 按钮与输入控件 */
.action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.cyber-btn {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid #333;
  color: #aaa;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.cyber-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: white;
  box-shadow: 0 0 10px var(--primary-dim);
}

.cyber-btn.active {
  background: var(--primary-dim);
  border-color: var(--primary);
  color: var(--primary);
}

.cyber-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* AI 按钮特殊样式 */
.ai-btn {
  width: 100%;
  flex-direction: row;
  justify-content: center;
  font-weight: bold;
  border: 1px solid var(--secondary);
  color: #bfaaff;
}

.ai-btn:hover:not(:disabled) {
  background: rgba(125, 68, 255, 0.1);
  box-shadow: 0 0 15px rgba(125, 68, 255, 0.3);
  border-color: #9e75ff;
  color: white;
}

.spin {
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin { 100% { transform: rotate(360deg); } }

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
  position: relative;
}

/* 视频区域 */
.video-wrapper {
  flex: 2;
  background: #000;
  border-radius: 16px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(0,0,0,0.5);
  border: 1px solid #222;
}

.video-frame {
  width: 100%;
  height: 100%;
  position: relative;
}

.video-feed {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* 视频四角装饰 */
.corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid var(--primary);
  opacity: 0.5;
  transition: all 0.3s;
}
.t-l { top: 10px; left: 10px; border-right: none; border-bottom: none; }
.t-r { top: 10px; right: 10px; border-left: none; border-bottom: none; }
.b-l { bottom: 10px; left: 10px; border-right: none; border-top: none; }
.b-r { bottom: 10px; right: 10px; border-left: none; border-top: none; }

.live .corner {
  border-color: var(--danger);
  width: 30px;
  height: 30px;
  opacity: 1;
}

/* 视频占位符 */
.video-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: radial-gradient(circle, #1a1a2e 0%, #000 100%);
}

.placeholder-content {
  text-align: center;
}

.radar-scan {
  width: 60px;
  height: 60px;
  border: 2px solid #333;
  border-radius: 50%;
  margin: 0 auto 20px;
  position: relative;
}

.radar-scan::after {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: conic-gradient(from 0deg, transparent 0%, rgba(0, 243, 255, 0.2) 100%);
  border-radius: 50%;
  animation: radar 2s linear infinite;
}

@keyframes radar { 100% { transform: rotate(360deg); } }

/* 数据面板 */
.data-panel {
  flex: 1;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 15px 20px;
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.count-badge {
  background: #222;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  color: #888;
}

.count-badge.alert {
  background: var(--danger);
  color: white;
  animation: pulse 1s infinite;
}

@keyframes pulse { 50% { opacity: 0.7; } }

.table-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.cyber-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.cyber-table th {
  text-align: left;
  padding: 10px;
  color: #666;
  font-weight: normal;
  font-size: 12px;
}

.cyber-table td {
  padding: 12px 10px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.status-danger { background: rgba(255, 68, 68, 0.1); color: #ff4444; }
.status-success { background: rgba(0, 255, 157, 0.1); color: #00ff9d; }
.status-warning { background: rgba(255, 170, 0, 0.1); color: #ffaa00; }

.dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.progress-bg {
  height: 4px;
  background: #333;
  border-radius: 2px;
  width: 80%;
  margin-right: 10px;
  display: inline-block;
}

.progress-fill { height: 100%; border-radius: 2px; transition: width 0.3s; }

.mono-text { font-family: 'Courier New', monospace; color: #888; font-size: 12px; }

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 { margin: 0; color: var(--primary); }

.close-icon {
  background: none; border: none; color: #666; font-size: 24px; cursor: pointer;
}
.close-icon:hover { color: white; }

.report-body {
  padding: 25px;
  overflow-y: auto;
  color: #ddd;
  line-height: 1.6;
  font-size: 14px;
  background: rgba(0,0,0,0.2);
}

.report-body pre {
  white-space: pre-wrap;
  font-family: inherit;
  margin: 0;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.neon-btn {
  padding: 8px 20px;
  background: var(--primary);
  color: black;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  transition: 0.3s;
}

.neon-btn:hover {
  box-shadow: 0 0 15px var(--primary);
}

.neon-btn.secondary {
  background: transparent;
  border: 1px solid #444;
  color: #ccc;
}
.neon-btn.secondary:hover {
  border-color: white;
  color: white;
  box-shadow: none;
}

/* 滚动条 */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #111; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #555; }

/* 警报横幅 */
.alarm-overlay {
  position: absolute;
  top: 20px; left: 50%;
  transform: translateX(-50%);
  z-index: 99;
  animation: flash 0.5s infinite;
}

.alarm-banner {
  background: var(--danger);
  color: white;
  padding: 10px 40px;
  font-weight: bold;
  font-size: 20px;
  border-radius: 8px;
  box-shadow: 0 0 20px var(--danger);
  text-transform: uppercase;
}

@keyframes flash {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>