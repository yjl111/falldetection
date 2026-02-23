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

      <!-- 趋势分析图 -->
      <div class="chart-panel glass-panel">
        <div class="panel-header">
          <h3>📉 跌倒事件趋势分析</h3>
        </div>
        <div class="chart-body">
          <Line v-if="loaded" :data="trendData" :options="lineChartOptions" />
        </div>
      </div>

      <!-- 分类统计 -->
      <div class="chart-panel glass-panel small">
        <div class="panel-header">
          <h3>🏷️ 跌倒类型分布</h3>
        </div>
        <div class="chart-body">
          <Doughnut v-if="loaded" :data="categoryData" :options="doughnutOptions" />
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
            <div class="event-status" :class="event.status">{{ event.statusText }}</div>
          </div>
          <div v-if="recentEvents.length === 0" class="empty-state">暂无事件</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar, Line, Doughnut } from 'vue-chartjs';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement);

const loaded = ref(false);
const timeRange = ref('7d');

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

// 趋势数据
const trendData = computed(() => ({
  labels: trendDataRaw.value.labels,
  datasets: [{
    label: '跌倒事件',
    data: trendDataRaw.value.data,
    borderColor: '#ff6b6b',
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    tension: 0.4,
    fill: true
  }]
}));

// 分类数据
const categoryData = computed(() => ({
  labels: ['向前跌倒', '向后跌倒', '侧向跌倒', '滑倒'],
  datasets: [{
    data: [12, 8, 15, 6],
    backgroundColor: ['#ff6b6b', '#4ecdc4', '#ffe66d', '#a29bfe'],
    borderWidth: 0
  }]
}));

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#ccc' } } },
  scales: {
    x: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } },
    y: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } }
  }
};

const lineChartOptions = { ...barChartOptions };
const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'right', labels: { color: '#ccc', padding: 15 } } }
};

// 加载统计数据
const loadStatistics = async () => {
  try {
    // 获取统计摘要
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

    // 获取每小时数据
    const hourlyRes = await fetch('http://localhost:5000/api/statistics/hourly');
    const hourly = await hourlyRes.json();
    hourlyDataRaw.value = hourly;

    // 获取趋势数据
    const trendRes = await fetch(`http://localhost:5000/api/statistics/trend?days=${timeRange.value === '7d' ? 7 : timeRange.value === '30d' ? 30 : 90}`);
    const trend = await trendRes.json();
    trendDataRaw.value = trend;

    loaded.value = true;
  } catch (error) {
    console.error('加载统计数据失败:', error);
    loaded.value = true;
  }
};

onMounted(() => {
  loadStatistics();
});
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

.recent-events { display: flex; flex-direction: column; gap: 12px; max-height: 220px; overflow-y: auto; }
.event-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; border-left: 3px solid var(--primary); }
.event-time { font-size: 12px; color: var(--text-dim); min-width: 50px; }
.event-desc { flex: 1; font-size: 13px; color: #fff; }
.event-status { font-size: 11px; padding: 3px 8px; border-radius: 4px; }
.event-status.handled { background: rgba(0, 255, 157, 0.2); color: var(--success); }
.event-status.pending { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
.empty-state { text-align: center; padding: 40px; color: var(--text-dim); font-style: italic; }

@media (max-width: 1200px) {
  .stats-cards { grid-template-columns: repeat(2, 1fr); }
  .charts-section { grid-template-columns: 1fr; }
}
</style>
