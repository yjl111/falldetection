<template>
  <div class="stats-layout">
    <!-- 顶部统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card glass-panel">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-label">今日跌倒事件</div>
          <div class="stat-value">{{ stats.todayFalls }}</div>
          <div class="stat-trend" :class="{ up: stats.todayTrend > 0, down: stats.todayTrend < 0 }">
            {{ stats.todayTrend > 0 ? '↑' : '↓' }} {{ Math.abs(stats.todayTrend) }}%
          </div>
        </div>
      </div>

      <div class="stat-card glass-panel">
        <div class="stat-icon">📅</div>
        <div class="stat-content">
          <div class="stat-label">本周跌倒事件</div>
          <div class="stat-value">{{ stats.weekFalls }}</div>
          <div class="stat-subtitle">平均 {{ (stats.weekFalls / 7).toFixed(1) }} 次/天</div>
        </div>
      </div>

      <div class="stat-card glass-panel">
        <div class="stat-icon">🎯</div>
        <div class="stat-content">
          <div class="stat-label">检测准确率</div>
          <div class="stat-value">{{ stats.accuracy }}%</div>
          <div class="stat-subtitle">误报率 {{ stats.falseAlarm }}%</div>
        </div>
      </div>

      <div class="stat-card glass-panel">
        <div class="stat-icon">⏱️</div>
        <div class="stat-content">
          <div class="stat-label">系统运行时长</div>
          <div class="stat-value">{{ stats.uptime }}</div>
          <div class="stat-subtitle">在线率 99.8%</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 时段分布图 -->
      <div class="chart-panel glass-panel">
        <div class="panel-header">
          <h3>📈 跌倒事件时段分布</h3>
          <div class="time-selector">
            <button @click="timeRange = '7d'" :class="{ active: timeRange === '7d' }">7天</button>
            <button @click="timeRange = '30d'" :class="{ active: timeRange === '30d' }">30天</button>
            <button @click="timeRange = '90d'" :class="{ active: timeRange === '90d' }">90天</button>
          </div>
        </div>
        <div class="chart-body">
          <Bar v-if="loaded" :data="hourlyData" :options="barChartOptions" />
        </div>
      </div>

      <!-- 每日趋势折线图 -->
      <div class="chart-panel glass-panel">
        <div class="panel-header">
          <h3>📉 每日跌倒事件趋势</h3>
          <div class="time-selector">
            <button @click="trendDays = 7; loadTrend()" :class="{ active: trendDays === 7 }">7天</button>
            <button @click="trendDays = 30; loadTrend()" :class="{ active: trendDays === 30 }">30天</button>
          </div>
        </div>
        <div class="chart-body">
          <Line v-if="trendLoaded" :data="trendData" :options="lineChartOptions" />
          <div v-else class="loading-placeholder">加载中...</div>
        </div>
      </div>

      <!-- 报警处理率饼图 -->
      <div class="chart-panel glass-panel small">
        <div class="panel-header">
          <h3>✅ 报警处理率</h3>
        </div>
        <div class="chart-body doughnut-wrap">
          <Doughnut v-if="loaded" :data="alarmRateData" :options="doughnutOptions" />
          <div class="doughnut-center">
            <div class="doughnut-pct">{{ alarmHandledPct }}%</div>
            <div class="doughnut-label">已处理</div>
          </div>
        </div>
      </div>

      <!-- 最近事件列表 -->
      <div class="chart-panel glass-panel small">
        <div class="panel-header">
          <h3>🔔 最近跌倒事件</h3>
        </div>
        <div class="recent-events">
          <div v-for="event in recentEvents" :key="event.id" class="event-item">
            <div class="event-time">{{ event.time }}</div>
            <div class="event-desc">{{ event.location }} - {{ event.type }}</div>
            <div class="event-actions">
              <div class="event-status" :class="event.status">{{ event.statusText }}</div>
              <button
                v-if="event.status === 'pending'"
                class="btn-handle"
                @click="handleEvent(event.id)"
              >处理</button>
            </div>
          </div>
          <div v-if="recentEvents.length === 0" class="empty-state">暂无事件</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Line, Doughnut } from 'vue-chartjs';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend);

const loaded = ref(false);
const trendLoaded = ref(false);
const timeRange = ref('7d');
const trendDays = ref(7);

const stats = ref({
  todayFalls: 0,
  todayTrend: 0,
  weekFalls: 0,
  accuracy: 0,
  falseAlarm: 0,
  uptime: '0小时'
});

const recentEvents = ref([]);

const hourlyDataRaw = ref({ labels: [], data: [] });
const trendDataRaw = ref({ labels: [], data: [] });
const alarmCounts = ref({ handled: 0, pending: 0 });

// 时段分布数据
const hourlyData = computed(() => ({
  labels: hourlyDataRaw.value.labels,
  datasets: [{
    label: '跌倒次数',
    data: hourlyDataRaw.value.data,
    backgroundColor: 'rgba(0, 243, 255, 0.6)',
    borderColor: 'rgba(0, 243, 255, 1)',
    borderWidth: 1
  }]
}));


// 每日趋势数据
const trendData = computed(() => ({
  labels: trendDataRaw.value.labels,
  datasets: [{
    label: '跌倒事件',
    data: trendDataRaw.value.data,
    borderColor: '#ff6b6b',
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    tension: 0.4,
    fill: true,
    pointBackgroundColor: '#ff6b6b',
    pointRadius: 4
  }]
}));

// 报警处理率数据
const alarmRateData = computed(() => ({
  labels: ['已处理', '待处理'],
  datasets: [{
    data: [alarmCounts.value.handled, alarmCounts.value.pending],
    backgroundColor: ['rgba(0, 255, 157, 0.7)', 'rgba(255, 107, 107, 0.7)'],
    borderColor: ['#00ff9d', '#ff6b6b'],
    borderWidth: 2
  }]
}));

const alarmHandledPct = computed(() => {
  const total = alarmCounts.value.handled + alarmCounts.value.pending;
  if (total === 0) return 0;
  return Math.round((alarmCounts.value.handled / total) * 100);
});

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#ccc' } } },
  scales: {
    x: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } },
    y: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } }
  }
};

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#ccc' } } },
  scales: {
    x: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } },
    y: { beginAtZero: true, ticks: { color: '#888', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } }
  }
};

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: { legend: { position: 'bottom', labels: { color: '#ccc', padding: 16, font: { size: 13 } } } }
};


// 加载统计数据
const loadStatistics = async () => {
  // 统计摘要
  try {
    const summaryRes = await fetch('http://localhost:5000/api/statistics/summary');
    const summary = await summaryRes.json();
    stats.value = {
      todayFalls: summary.today_falls,
      todayTrend: parseFloat(summary.today_trend),
      weekFalls: summary.week_falls,
      accuracy: summary.accuracy,
      falseAlarm: summary.false_alarm_rate,
      uptime: `${summary.uptime}小时`
    };
  } catch (e) { console.error('摘要加载失败:', e); }

  // 每小时分布
  try {
    const hourlyRes = await fetch('http://localhost:5000/api/statistics/hourly');
    hourlyDataRaw.value = await hourlyRes.json();
  } catch (e) {
    console.error('时段数据加载失败:', e);
    hourlyDataRaw.value = { labels: ['0-4时','4-8时','8-12时','12-16时','16-20时','20-24时'], data: [0,0,0,0,0,0] };
  }
  loaded.value = true;

  // 报警列表
  try {
    const alarmsRes = await fetch('http://localhost:5000/api/alarms?status=all');
    const alarms = await alarmsRes.json();
    if (Array.isArray(alarms)) {
      recentEvents.value = alarms.slice(0, 10).map(a => ({
        id: a.id,
        time: a.time,
        location: a.location || '未知位置',
        type: a.type || '跌倒',
        status: a.status === '已处理' ? 'handled' : 'pending',
        statusText: a.status || '待处理'
      }));
      alarmCounts.value.handled = alarms.filter(a => a.status === '已处理').length;
      alarmCounts.value.pending  = alarms.filter(a => a.status !== '已处理').length;
    }
  } catch (e) { console.error('报警数据加载失败:', e); }

  // 每日趋势（独立加载）
  await loadTrend();
};

const loadTrend = async () => {
  trendLoaded.value = false;
  try {
    const res = await fetch(`http://localhost:5000/api/statistics/trend?days=${trendDays.value}`);
    const data = await res.json();
    if (data && Array.isArray(data.labels) && Array.isArray(data.data)) {
      trendDataRaw.value = data;
    } else {
      throw new Error('数据格式错误');
    }
  } catch (e) {
    console.error('加载趋势数据失败:', e);
    // fallback: 用 0 填充
    const days = trendDays.value;
    const labels = Array.from({ length: days }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (days - 1 - i));
      return `${d.getMonth()+1}/${d.getDate()}`;
    });
    trendDataRaw.value = { labels, data: Array(days).fill(0) };
  } finally {
    trendLoaded.value = true;
  }
};

onMounted(() => {
  loadStatistics();
});

const handleEvent = async (id) => {
  if (!id) return;
  try {
    const res = await fetch(`http://localhost:5000/api/alarms/handle/${id}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      // 本地更新状态，无需重新请求
      const evt = recentEvents.value.find(e => e.id === id);
      if (evt) { evt.status = 'handled'; evt.statusText = '已处理'; }
      alarmCounts.value.handled += 1;
      alarmCounts.value.pending = Math.max(0, alarmCounts.value.pending - 1);
    }
  } catch (e) {
    console.error('处理报警失败:', e);
  }
};
</script>

<style scoped>
.stats-layout { padding: 30px; display: flex; flex-direction: column; gap: 30px; height: 100%; overflow-y: auto; }
.glass-panel { background: var(--bg-panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow); padding: 24px; }

.stats-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.stat-card { display: flex; gap: 20px; align-items: center; }
.stat-icon { font-size: 48px; }
.stat-content { flex: 1; }
.stat-label { font-size: 12px; color: var(--text-dim); margin-bottom: 8px; text-transform: uppercase; }
.stat-value { font-size: 32px; font-weight: bold; color: #fff; margin-bottom: 4px; }
.stat-subtitle { font-size: 12px; color: var(--text-dim); }
.stat-trend { font-size: 14px; font-weight: bold; }
.stat-trend.up { color: #ff6b6b; }
.stat-trend.down { color: var(--success); }

.charts-section { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.chart-panel { display: flex; flex-direction: column; min-height: 300px; }
.chart-panel.small { min-height: 250px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid var(--border); }
.panel-header h3 { margin: 0; font-size: 16px; color: #fff; }
.time-selector { display: flex; gap: 5px; }
.time-selector button { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text-dim); padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: 0.3s; }
.time-selector button.active { background: var(--primary); color: #000; border-color: var(--primary); }
.chart-body { flex: 1; position: relative; }
.doughnut-wrap { position: relative; display: flex; align-items: center; justify-content: center; }
.doughnut-center { position: absolute; text-align: center; pointer-events: none; }
.doughnut-pct { font-size: 28px; font-weight: bold; color: #00ff9d; }
.doughnut-label { font-size: 12px; color: var(--text-dim); margin-top: 2px; }

.recent-events { display: flex; flex-direction: column; gap: 12px; max-height: 220px; overflow-y: auto; }
.event-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; border-left: 3px solid var(--primary); }
.event-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.event-time { font-size: 12px; color: var(--text-dim); min-width: 50px; }
.event-desc { flex: 1; font-size: 13px; color: #fff; }
.event-status { font-size: 11px; padding: 3px 8px; border-radius: 4px; }
.event-status.handled { background: rgba(0, 255, 157, 0.2); color: var(--success); }
.event-status.pending { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
.empty-state { text-align: center; padding: 40px; color: var(--text-dim); font-style: italic; }
.btn-handle { background: rgba(0, 243, 255, 0.15); border: 1px solid var(--primary); color: var(--primary); padding: 3px 10px; border-radius: 4px; cursor: pointer; font-size: 11px; transition: 0.2s; white-space: nowrap; }
.btn-handle:hover { background: var(--primary); color: #000; }
.loading-placeholder { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-dim); font-style: italic; font-size: 14px; }

@media (max-width: 1200px) {
  .stats-cards { grid-template-columns: repeat(2, 1fr); }
  .charts-section { grid-template-columns: 1fr; }
}
</style>
