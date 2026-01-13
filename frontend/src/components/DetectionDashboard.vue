<template>
  <div class="gui-layout" @click="unlockAudio">
    <!-- 报警声音源 -->
    <audio ref="alarmAudio" src="https://www.soundjay.com/buttons/beep-01a.mp3" loop></audio>

    <!-- 报警遮罩层 -->
    <div class="alarm-overlay" v-if="isAlarm">
      <div class="alarm-banner">⚠️ 危险警报：检测到跌倒 ⚠️</div>
    </div>

    <aside class="sidebar glass-panel">
      <!-- 1. Tasks -->
      <div class="panel-section">
        <h3><span class="deco">#</span> 任务选择</h3>
        <div class="radio-card">
          <label class="radio-item active"><span class="status-indicator glow"></span> 目标检测+姿态估计</label>
          
        </div>
      </div>

      <!-- 2. Models -->
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
      
      <!-- 3. Input Source -->
      <div class="panel-section">
        <div class="section-header">
          <h3><span class="deco">#</span> 输入源</h3>
        </div>
        <div class="action-grid">
          <!-- 文件按钮 -->
          <button 
            class="cyber-btn" 
            :class="{ active: activeSource === 'file', 'is-loading': activeSource === 'switching' }"
            @click="$refs.fileInput.click()"
            :disabled="activeSource === 'switching'"
          >
            <span class="icon">📁</span>
            <span class="label">上传文件</span>
          </button>

          <!-- 摄像头按钮 (开关) -->
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

      <!-- 4. Params -->
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
        <div class="table-scroll">
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
              <!-- 只有开启流时才渲染数据行 -->
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

const isStreaming = ref(false); 
const isAlarm = ref(false); 
const isPaused = ref(false);
const activeSource = ref(null); // 'webcam' | 'file' | 'switching' | null
const alarmAudio = ref(null);
const audioUnlocked = ref(false);
const conf = ref(0.30);
const iou = ref(0.45);
const tableData = ref([]);
const streamUrl = ref('/video_feed');
const streamKey = ref(Date.now());
let timer = null;

// 监听流状态：关闭时重置数据
watch(isStreaming, (newVal) => { 
  if (!newVal) {
    tableData.value = [];
    isAlarm.value = false;
    isPaused.value = false;
    if (activeSource.value !== 'switching') {
        // 只有非切换状态下才清除源标记
        // activeSource.value = null; 
    }
  }
});

watch(isAlarm, (newVal) => {
  if (newVal) alarmAudio.value?.play().catch(() => {});
  else { if (alarmAudio.value) { alarmAudio.value.pause(); alarmAudio.value.currentTime = 0; } }
});

const unlockAudio = () => {
  if (!audioUnlocked.value && alarmAudio.value) {
    alarmAudio.value.play().then(() => { alarmAudio.value.pause(); audioUnlocked.value = true; }).catch(() => {});
  }
};

const formatClass = (cls) => cls ? cls.replace(/_/g, ' ').toUpperCase() : 'UNKNOWN';
const getStatusClass = (cls) => {
  const c = cls.toLowerCase();
  if (c.includes('not') || c.includes('normal')) return 'tag-success';
  if (c.includes('fall')) return 'tag-danger';
  return 'tag-neutral';
};
const getConfColor = (c) => {
  const v = parseFloat(c);
  if (v > 80) return 'linear-gradient(90deg, #00f260, #0575e6)';
  if (v > 50) return 'linear-gradient(90deg, #f12711, #f5af19)';
  return 'linear-gradient(90deg, #8E2DE2, #4A00E0)';
};
const formatBBox = (b) => {
  try {
    const a = JSON.parse(b);
    return `X:${a[0]} Y:${a[1]} | ${a[2]-a[0]}×${a[3]-a[1]}px`;
  } catch (e) { return b; }
};

const togglePause = async () => {
  try {
    const res = await fetch('/api/video/toggle_pause', { method: 'POST' });
    const data = await res.json();
    isPaused.value = data.is_paused;
  } catch (e) { console.error(e); }
};

// 核心修复：更彻底的停止与释放
const stopAndRelease = async () => {
  // 1. 前端停止显示
  isStreaming.value = false;
  isAlarm.value = false;
  tableData.value = [];
  isPaused.value = false;
  
  // 2. 告诉后端强制停止当前循环
  try {
    await fetch('/api/video/stop', { method: 'POST' });
  } catch(e) { console.error(e); }

  // 3. 等待后端清理
  await new Promise(r => setTimeout(r, 500));
};

const handleUpload = async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  activeSource.value = 'switching';
  
  // 先停止一切
  await stopAndRelease();

  const formData = new FormData();
  formData.append('file', file);
  
  try {
    // 上传文件并开启新流
    await fetch('/api/upload', { method: 'POST', body: formData });
    await new Promise(r => setTimeout(r, 300)); // 额外缓冲
    
    activeSource.value = 'file';
    streamKey.value = Date.now();
    isStreaming.value = true;
    
  } catch (error) {
    console.error('上传失败:', error);
    activeSource.value = null;
  } finally {
    e.target.value = ''; 
  }
};

const toggleWebcam = async () => {
  if (isStreaming.value && activeSource.value === 'webcam') {
    // 关闭逻辑
    await stopAndRelease();
    activeSource.value = null;
    return;
  }

  // 开启逻辑
  activeSource.value = 'switching';
  await stopAndRelease();

  try {
    await fetch('/api/set_source_webcam', { method: 'POST' });
    await new Promise(r => setTimeout(r, 500)); // 等待摄像头预热
    
    activeSource.value = 'webcam';
    streamKey.value = Date.now();
    isStreaming.value = true;
  } catch (err) { 
    console.error(err);
    activeSource.value = null; 
  } 
};

// 后端参数更新
const setWebcam = toggleWebcam; 
const updateParams = async () => { try { await fetch('/api/update_params', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ conf: conf.value, iou: iou.value }) }); } catch (err) {} };

onMounted(() => {
  timer = setInterval(async () => {
    // 修复：每次请求前再次检查 isStreaming
    if (isStreaming.value) {
      try {
        const dataRes = await fetch('/api/data');
        if (dataRes.ok) {
          const newData = await dataRes.json();
          
          // 修复：请求回来后，如果用户已经关闭了开关，则丢弃数据
          if (!isStreaming.value) {
            tableData.value = [];
            return;
          }

          tableData.value = newData;
          
          const hasFallInTable = newData.some(row => {
            const cls = row.class.toLowerCase();
            return (cls === 'falling' || (cls.includes('fall') && !cls.includes('not')));
          });
          
          if (hasFallInTable) { 
            isAlarm.value = true; 
          } else {
            const alarmRes = await fetch('/api/alarm');
            if (alarmRes.ok) isAlarm.value = (await alarmRes.json()).is_alarm;
          }
        }
      } catch (e) {}
    }
  }, 200);
});

onBeforeUnmount(() => { isStreaming.value = false; isAlarm.value = false; if (timer) clearInterval(timer); });
onUnmounted(() => { if (timer) clearInterval(timer); });
</script>

<style scoped>
/* 样式保持不变 */
.gui-layout { display: flex; height: 100%; gap: 20px; padding: 20px; box-sizing: border-box; position: relative; }
.glass-panel { background: var(--bg-panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow); }
.sidebar { width: 300px; padding: 24px; display: flex; flex-direction: column; gap: 24px; overflow-y: auto; }
.panel-section h3 { font-size: 12px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px; }
.deco { color: var(--primary); margin-right: 8px; font-weight: bold; }
.radio-card { background: rgba(0,0,0,0.2); border-radius: 12px; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
.radio-item { font-size: 14px; color: var(--text-dim); padding: 8px 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px; }
.radio-item.active { background: rgba(0, 243, 255, 0.1); color: #fff; border: 1px solid rgba(0, 243, 255, 0.2); }
.status-indicator { width: 8px; height: 8px; background: #555; border-radius: 50%; }
.status-indicator.glow { background: var(--success); box-shadow: 0 0 10px var(--success); }
.cyber-select { width: 100%; background: rgba(0,0,0,0.3); color: #fff; padding: 12px; border: 1px solid var(--border); border-radius: 8px; outline: none; appearance: none; }
.select-wrapper { position: relative; } .select-arrow { position: absolute; right: 12px; top: 14px; font-size: 10px; color: var(--primary); pointer-events: none; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.cyber-btn { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text-main); padding: 12px; border-radius: 8px; cursor: pointer; transition: 0.3s; display: flex; flex-direction: column; align-items: center; gap: 5px; }
.cyber-btn:hover { background: rgba(255,255,255,0.1); border-color: var(--primary); }
.cyber-btn.active { background: rgba(0, 243, 255, 0.2); border-color: var(--primary); box-shadow: 0 0 15px rgba(0, 243, 255, 0.3); color: #fff; }
.cyber-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.cyber-switch { position: relative; display: inline-block; width: 50px; height: 26px; }
.cyber-switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #333; transition: .4s; border-radius: 34px; border: 1px solid #555; }
.slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: #888; transition: .4s; border-radius: 50%; }
input:checked + .slider { background-color: rgba(0, 255, 157, 0.2); border-color: var(--success); }
input:checked + .slider:before { transform: translateX(24px); background-color: var(--success); box-shadow: 0 0 10px var(--success); }
.param-item { margin-bottom: 15px; }
.param-header { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; color: var(--text-dim); }
.param-val { color: var(--primary); font-family: monospace; }
.cyber-range { -webkit-appearance: none; width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; outline: none; }
.cyber-range::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; background: var(--primary); border-radius: 50%; cursor: pointer; box-shadow: 0 0 10px var(--primary); }
.main-content { flex: 1; display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.video-wrapper { flex: 2; background: #000; border-radius: 16px; position: relative; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
.video-frame { width: 100%; height: 100%; position: relative; }
.video-frame.live { border: 1px solid var(--primary); box-shadow: 0 0 20px rgba(0, 243, 255, 0.1); }
.video-frame.alarm-state { border-color: var(--danger); box-shadow: 0 0 40px var(--danger); }
.corner { position: absolute; width: 20px; height: 20px; border: 2px solid var(--primary); z-index: 2; }
.t-l { top: 10px; left: 10px; border-right: none; border-bottom: none; } .t-r { top: 10px; right: 10px; border-left: none; border-bottom: none; }
.b-l { bottom: 10px; left: 10px; border-right: none; border-top: none; } .b-r { bottom: 10px; right: 10px; border-left: none; border-top: none; }
.video-feed { width: 100%; height: 100%; object-fit: contain; }
.video-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: radial-gradient(circle, #1a2332 0%, #000 90%); }
.placeholder-content { text-align: center; position: relative; }
.radar-scan { width: 200px; height: 200px; border: 2px solid rgba(0, 243, 255, 0.2); border-radius: 50%; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); animation: radar 2s infinite linear; }
.radar-scan::before { content: ''; position: absolute; top: 0; left: 50%; width: 50%; height: 100%; background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.1)); transform-origin: 0 50%; animation: scan 2s infinite linear; }
.status-text { font-size: 24px; letter-spacing: 4px; color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.5); margin-bottom: 30px; position: relative; z-index: 10; }
.neon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 12px 30px; font-size: 14px; letter-spacing: 2px; cursor: pointer; transition: 0.3s; position: relative; z-index: 10; box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); }
.neon-btn:hover { background: var(--primary); color: #000; box-shadow: 0 0 30px var(--primary); }
.neon-btn.secondary { border-color: var(--secondary); color: var(--secondary); box-shadow: 0 0 15px rgba(112, 0, 255, 0.2); margin-left: 15px;}
.neon-btn.secondary:hover { background: var(--secondary); color: #fff; box-shadow: 0 0 30px var(--secondary); }
@keyframes scan { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.alarm-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; z-index: 999; box-shadow: inset 0 0 100px rgba(255, 0, 50, 0.6); animation: flash 0.8s infinite; display: flex; justify-content: center; align-items: flex-start; }
.alarm-banner { background: var(--danger); color: white; padding: 10px 40px; font-weight: bold; font-size: 20px; margin-top: 20px; border-radius: 4px; box-shadow: 0 0 30px var(--danger); }
@keyframes flash { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

/* 暂停按钮 */
.control-overlay { position: absolute; bottom: 20px; right: 20px; z-index: 10; }
.pause-btn { 
  width: 50px; height: 50px; border-radius: 50%; border: 2px solid var(--primary); 
  background: rgba(0,0,0,0.5); color: var(--primary); font-size: 20px; cursor: pointer; 
  display: flex; align-items: center; justify-content: center; backdrop-filter: blur(5px); transition: 0.3s; 
}
.pause-btn:hover { background: var(--primary); color: #000; box-shadow: 0 0 20px var(--primary); }

/* 表格相关 */
.data-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; padding: 0; }
.panel-header { padding: 15px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.count-badge { background: rgba(0, 255, 157, 0.1); color: var(--success); padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
.count-badge.alert { background: rgba(255, 0, 85, 0.2); color: var(--danger); animation: pulse 1s infinite; }
.table-scroll { flex: 1; overflow-y: auto; padding: 0; }
.cyber-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.cyber-table th { text-align: left; padding: 12px 20px; color: var(--text-dim); font-weight: 500; background: rgba(0,0,0,0.4); position: sticky; top: 0; backdrop-filter: blur(5px); z-index: 10; }
.cyber-table td { padding: 12px 20px; border-bottom: 1px solid rgba(255,255,255,0.03); color: #fff; vertical-align: middle; }
.cyber-table tr:hover td { background: rgba(255,255,255,0.05); }
.status-tag { display: inline-flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid transparent; }
.status-tag .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.tag-danger { background: rgba(255, 0, 85, 0.15); color: #ff0055; border-color: rgba(255, 0, 85, 0.3); }
.tag-success { background: rgba(0, 255, 157, 0.15); color: #00ff9d; border-color: rgba(0, 255, 157, 0.3); }
.tag-neutral { background: rgba(255, 255, 255, 0.1); color: #ccc; }
.conf-wrapper { display: flex; align-items: center; gap: 10px; }
.progress-bg { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; min-width: 60px; }
.progress-fill { height: 100%; border-radius: 3px; transition: width 0.3s ease; box-shadow: 0 0 5px currentColor; }
.conf-text { font-family: monospace; font-size: 12px; color: var(--text-dim); min-width: 40px; text-align: right; }
.mono-text { font-family: 'Courier New', monospace; color: var(--text-dim); font-size: 11px; letter-spacing: 0.5px; opacity: 0.8; }
.empty-state { text-align: center; padding: 30px; color: var(--text-dim); font-style: italic; }
</style>