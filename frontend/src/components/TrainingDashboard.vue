<template>
  <div class="train-layout">
    <!-- 顶部配置卡片 -->
    <div class="config-card glass-panel">
      <div class="card-header">
        <h2>🚀 神经网络模型训练</h2>
        <div class="status-badge" :class="{ running: isTraining }">
          {{ isTraining ? '训练进行中' : '准备就绪' }}
        </div>
      </div>
      
      <div class="form-grid">
        <div class="input-group full-width">
          <label>数据集路径 (data.yaml)</label>
          <div class="path-input-wrapper">
            <input type="text" v-model="datasetPath" placeholder="请选择配置文件..." readonly :disabled="isTraining">
            <button @click="openFileBrowser" :disabled="isTraining" class="icon-btn">📂</button>
          </div>
        </div>

        <div class="input-group">
          <label>训练轮数 (Epochs)</label>
          <input type="number" v-model="epochs" :disabled="isTraining" min="1" max="500">
        </div>

        <div class="input-group">
          <label>批次大小 (Batch Size)</label>
          <input type="number" v-model="batch" :disabled="isTraining" min="1" max="128">
        </div>

        <div class="input-group">
          <label>图像尺寸 (Image Size)</label>
          <input type="number" v-model="imgsz" :disabled="isTraining" min="320" max="1280" step="32">
        </div>

        <div class="input-group">
          <label>优化器 (Optimizer)</label>
          <select v-model="optimizer" :disabled="isTraining" class="param-select">
            <option value="SGD">SGD</option>
            <option value="Adam">Adam</option>
            <option value="AdamW">AdamW</option>
          </select>
        </div>

        <div class="input-group">
          <label>初始学习率 (Learning Rate)</label>
          <input type="number" v-model="lr0" :disabled="isTraining" min="0.0001" max="0.1" step="0.001">
        </div>

        <div class="action-group">
          <button @click="startTrain" :disabled="isTraining" class="start-btn" :class="{ 'is-loading': isTraining }">
            <span v-if="!isTraining">▶ 开始训练</span>
            <span v-else>正在处理... 第 {{ metrics.epochs.length }} / {{ epochs }} 轮</span>
          </button>
          
          <button @click="stopTrain" :disabled="!isTraining" class="stop-btn">
            ⏹ 停止训练
          </button>
        </div>
      </div>
      
      <div class="msg-box" v-if="message" :class="{ error: isError }">{{ message }}</div>
    </div>

    <!-- 图表展示区 -->
    <div class="charts-grid">
      <!-- 1. Loss 折线图 -->
      <div class="chart-card glass-panel">
        <div class="chart-header">
          <h3>📉 损失函数分析 (Loss)</h3><span class="live-tag" v-if="isTraining">实时</span>
        </div>
        <div class="chart-body"><Line v-if="loaded" :data="lossData" :options="lineChartOpt" /></div>
      </div>

      <!-- 2. mAP 折线图 -->
      <div class="chart-card glass-panel">
        <div class="chart-header">
          <h3>🏆 精度分析 (mAP@50)</h3><span class="live-tag" v-if="isTraining">实时</span>
        </div>
        <div class="chart-body"><Line v-if="loaded" :data="mapData" :options="lineChartOpt" /></div>
      </div>

      <!-- 3. Precision 仪表盘 (饼图) -->
      <div class="chart-card glass-panel">
        <div class="chart-header">
          <h3>🎯 当前精确率 (Precision)</h3><span class="live-tag" v-if="isTraining">实时</span>
        </div>
        <div class="chart-body doughnut-wrapper">
          <!-- 饼图组件 -->
          <Doughnut v-if="loaded" :data="precisionDoughnutData" :options="doughnutOpt" />
          <!-- 中心文字显示具体数值 -->
          <div class="center-text">
            <span class="value">{{ currentPrecision }}%</span>
            <span class="label">Precision</span>
          </div>
        </div>
      </div>

      <!-- 4. Recall 折线图 -->
      <div class="chart-card glass-panel">
        <div class="chart-header">
          <h3>🔍 召回率 (Recall)</h3><span class="live-tag" v-if="isTraining">实时</span>
        </div>
        <div class="chart-body"><Line v-if="loaded" :data="recallData" :options="lineChartOpt" /></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  Title, 
  Tooltip, 
  Legend,
  ArcElement // 引入圆弧元素用于饼图
} from 'chart.js';
import { Line, Doughnut } from 'vue-chartjs'; // 引入 Doughnut 组件

// 注册所有需要的组件
ChartJS.register(
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  Title, 
  Tooltip, 
  Legend,
  ArcElement
);

const isTraining = ref(false);
const loaded = ref(true);
const datasetPath = ref('');
const epochs = ref(50);
const batch = ref(16);
const imgsz = ref(640);  // 图像尺寸
const optimizer = ref('Adam');  // 优化器
const lr0 = ref(0.01);  // 初始学习率
const message = ref('');
const isError = ref(false);
const metrics = ref({ epochs: [], box_loss: [], cls_loss: [], map50: [], precision: [], recall: [] });
let timer = null;

// --- 配置项 ---

// 折线图配置
const lineChartOpt = {
  responsive: true, 
  maintainAspectRatio: false, 
  animation: false,
  scales: { 
    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#888' } }, 
    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#888' } } 
  },
  plugins: { legend: { labels: { color: '#ccc' } } }
};

// 饼图配置 (仪表盘风格)
const doughnutOpt = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '75%', // 中空比例
  plugins: {
    legend: { display: false }, // 隐藏图例
    tooltip: { enabled: false } // 禁用提示框，因为中心有文字
  }
};

// --- 数据计算 ---

const lossData = computed(() => ({
  labels: metrics.value.epochs,
  datasets: [
    { label: '定位损失', borderColor: '#ff6b6b', backgroundColor: 'rgba(255,107,107,0.1)', data: metrics.value.box_loss, tension: 0.4, fill: true },
    { label: '分类损失', borderColor: '#4ecdc4', backgroundColor: 'transparent', data: metrics.value.cls_loss, tension: 0.4 }
  ]
}));

const mapData = computed(() => ({
  labels: metrics.value.epochs,
  datasets: [{ label: 'mAP@50', borderColor: '#ffe66d', backgroundColor: 'rgba(255,230,109,0.1)', data: metrics.value.map50, fill: true, tension: 0.4 }]
}));

// 计算当前最新的 Precision 值 (0-100)
const currentPrecision = computed(() => {
  const len = metrics.value.precision.length;
  if (len === 0) return 0;
  // 后端返回的是 0-1 的小数，转为百分比
  return (metrics.value.precision[len - 1] * 100).toFixed(1);
});

// Precision 饼图数据
const precisionDoughnutData = computed(() => {
  const val = parseFloat(currentPrecision.value);
  return {
    labels: ['Precision', 'Loss'],
    datasets: [{
      data: [val, 100 - val], // [当前值, 剩余部分]
      backgroundColor: ['#a29bfe', 'rgba(255,255,255,0.05)'], // 高亮色 vs 背景色
      borderWidth: 0,
      borderRadius: 5
    }]
  };
});

const recallData = computed(() => ({
  labels: metrics.value.epochs,
  datasets: [{ label: 'Recall', borderColor: '#00cec9', backgroundColor: 'rgba(0, 206, 201, 0.1)', data: metrics.value.recall, fill: true, tension: 0.4 }]
}));

// --- 功能函数 ---

const openFileBrowser = async () => {
  try {
    const res = await fetch('/api/system/browse');
    const data = await res.json();
    if (data.path) { datasetPath.value = data.path; message.value = ""; isError.value = false; }
  } catch (e) { message.value = "无法打开文件浏览器"; isError.value = true; }
};

const startTrain = async () => {
  message.value = ""; isError.value = false;
  if(!datasetPath.value) { message.value = "请先选择路径！"; isError.value = true; return; }
  try {
    const res = await fetch('/api/train/start', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ 
        dataset_path: datasetPath.value, 
        epochs: epochs.value, 
        batch: batch.value,
        imgsz: imgsz.value,
        optimizer: optimizer.value,
        lr0: lr0.value
      })
    });
    const d = await res.json();
    if(d.status === 'started') {
      isTraining.value = true; metrics.value = { epochs: [], box_loss: [], cls_loss: [], map50: [], precision: [], recall: [] };
    } else { message.value = d.msg; isError.value = true; }
  } catch(e) { message.value = "网络错误"; isError.value = true; }
};

const stopTrain = async () => {
  try {
    const res = await fetch('/api/train/stop', { method: 'POST' });
    const d = await res.json();
    message.value = d.msg;
  } catch(e) { message.value = "停止失败"; }
};

onMounted(() => {
  timer = setInterval(async () => {
    try {
      const res = await fetch('/api/train/metrics');
      const d = await res.json();
      isTraining.value = d.is_training;
      if(d.metrics.epochs.length !== metrics.value.epochs.length) {
        metrics.value = d.metrics;
      }
    } catch(e){}
  }, 2000);
});
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.train-layout { padding: 30px; display: flex; flex-direction: column; gap: 30px; height: 100%; overflow-y: auto; max-width: 1400px; margin: 0 auto; box-sizing: border-box; }
.glass-panel { background: var(--bg-panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow); padding: 24px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
.card-header h2 { margin: 0; font-size: 18px; color: #fff; letter-spacing: 1px; }
.status-badge { font-size: 12px; font-weight: bold; background: #333; padding: 4px 10px; border-radius: 20px; color: #888; transition: 0.3s; }
.status-badge.running { background: rgba(0, 255, 157, 0.2); color: var(--success); box-shadow: 0 0 10px rgba(0, 255, 157, 0.2); }
.form-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; align-items: end; }
.input-group { display: flex; flex-direction: column; gap: 8px; }
.input-group.full-width { grid-column: 1 / -1; }
.input-group label { font-size: 12px; color: var(--text-dim); font-weight: 500; }
.path-input-wrapper { display: flex; gap: 10px; }
input { background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 12px; border-radius: 8px; outline: none; transition: 0.3s; width: 100%; box-sizing: border-box; }
input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(0, 243, 255, 0.1); }
input:disabled { opacity: 0.5; cursor: not-allowed; }
.param-select { background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 12px; border-radius: 8px; outline: none; transition: 0.3s; width: 100%; box-sizing: border-box; cursor: pointer; }
.param-select:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(0, 243, 255, 0.1); }
.param-select:disabled { opacity: 0.5; cursor: not-allowed; }
.param-select option { background: #1a1a2e; color: #fff; padding: 8px; }
.icon-btn { background: #333; border: 1px solid var(--border); color: #fff; width: 42px; cursor: pointer; border-radius: 8px; transition: 0.2s; }
.icon-btn:hover:not(:disabled) { background: #444; border-color: #fff; }
.action-group { display: flex; gap: 10px; }
.start-btn { background: linear-gradient(135deg, var(--secondary), #4c1d95); color: #fff; border: none; padding: 12px 30px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; height: 42px; min-width: 160px; }
.start-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(112, 0, 255, 0.4); }
.start-btn.is-loading { background: #333; color: #aaa; cursor: wait; animation: pulse 2s infinite; }
.stop-btn { background: rgba(255, 0, 85, 0.2); border: 1px solid #ff0055; color: #ff0055; padding: 12px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; height: 42px; }
.stop-btn:hover:not(:disabled) { background: #ff0055; color: white; box-shadow: 0 0 15px #ff0055; }
.stop-btn:disabled { opacity: 0.3; cursor: not-allowed; border-color: #555; color: #555; background: transparent; }
.msg-box { margin-top: 15px; padding: 10px; background: rgba(0, 255, 157, 0.1); border-left: 3px solid var(--success); font-size: 13px; color: var(--success); }
.msg-box.error { background: rgba(255, 107, 107, 0.1); border-color: #ff6b6b; color: #ff6b6b; }
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; flex: 1; }
.chart-card { display: flex; flex-direction: column; min-height: 300px; }
.chart-header { display: flex; justify-content: space-between; margin-bottom: 15px; }
.chart-header h3 { margin: 0; font-size: 14px; color: var(--text-dim); }
.live-tag { font-size: 10px; background: #ff0000; color: white; padding: 2px 6px; border-radius: 4px; animation: blink 1s infinite; }
.chart-body { flex: 1; position: relative; }

/* 饼图专用样式 */
.doughnut-wrapper { position: relative; display: flex; justify-content: center; align-items: center; }
.center-text { position: absolute; display: flex; flex-direction: column; align-items: center; pointer-events: none; }
.center-text .value { font-size: 32px; font-weight: bold; color: #a29bfe; text-shadow: 0 0 20px rgba(162, 155, 254, 0.4); }
.center-text .label { font-size: 12px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>