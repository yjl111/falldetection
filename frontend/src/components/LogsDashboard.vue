<template>
  <div class="logs-layout">
    <div class="logs-header glass-panel">
      <div>
        <h2>日志中心</h2>
        <p>查看系统审计记录与通知发送记录</p>
      </div>
      <button class="refresh-btn" @click="loadLogs" :disabled="loading">
        {{ loading ? '加载中...' : '刷新数据' }}
      </button>
    </div>

    <div class="summary-grid">
      <div class="summary-card glass-panel">
        <span class="summary-label">审计日志</span>
        <span class="summary-value">{{ auditLogs.length }}</span>
      </div>
      <div class="summary-card glass-panel">
        <span class="summary-label">通知日志</span>
        <span class="summary-value">{{ notificationLogs.length }}</span>
      </div>
      <div class="summary-card glass-panel">
        <span class="summary-label">发送成功</span>
        <span class="summary-value success">{{ successCount }}</span>
      </div>
      <div class="summary-card glass-panel">
        <span class="summary-label">发送失败</span>
        <span class="summary-value fail">{{ failureCount }}</span>
      </div>
    </div>

    <div class="logs-toolbar glass-panel">
      <div class="logs-switch">
        <button class="switch-btn" :class="{ active: currentView === 'audit' }" @click="currentView = 'audit'">
          审计日志
        </button>
        <button class="switch-btn" :class="{ active: currentView === 'notification' }" @click="currentView = 'notification'">
          通知日志
        </button>
      </div>
      <div class="toolbar-note">
        {{ currentView === 'audit' ? '记录登录、配置修改、工单处理等关键操作' : '记录邮件、短信等通知发送结果' }}
      </div>
    </div>

    <div v-if="errorMsg" class="error-banner glass-panel">
      {{ errorMsg }}
    </div>

    <div v-if="currentView === 'audit'" class="logs-panel glass-panel">
      <div class="panel-title">
        <h3>审计日志</h3>
        <span>{{ auditLogs.length }} 条</span>
      </div>

      <div v-if="auditLogs.length" class="log-list">
        <div v-for="log in auditLogs" :key="log._id" class="log-card">
          <div class="log-main">
            <div class="log-top">
              <span class="log-action">{{ log.action || 'UNKNOWN' }}</span>
              <span class="log-status" :class="log.status === 'success' ? 'ok' : 'fail'">
                {{ log.status || 'unknown' }}
              </span>
            </div>
            <div class="log-details">{{ log.details || '暂无详情' }}</div>
          </div>
          <div class="log-meta">
            <span>用户: {{ log.username || 'system' }}</span>
            <span>对象: {{ log.target_type || '-' }} / {{ log.target_id || '-' }}</span>
            <span>时间: {{ formatTime(log.created_at) }}</span>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">暂无审计日志</div>
    </div>

    <div v-else class="logs-panel glass-panel">
      <div class="panel-title">
        <h3>通知日志</h3>
        <span>{{ notificationLogs.length }} 条</span>
      </div>

      <div v-if="notificationLogs.length" class="log-list">
        <div v-for="log in notificationLogs" :key="log._id" class="log-card">
          <div class="log-main">
            <div class="log-top">
              <span class="log-action">{{ (log.channel || 'unknown').toUpperCase() }}</span>
              <span class="log-status" :class="log.success ? 'ok' : 'fail'">
                {{ log.success ? 'success' : 'failed' }}
              </span>
            </div>
            <div class="log-details">{{ log.message || '暂无返回信息' }}</div>
          </div>
          <div class="log-meta">
            <span>报警ID: {{ log.alarm_id || '-' }}</span>
            <span>接收方: {{ log.recipient || '-' }}</span>
            <span>时间: {{ formatTime(log.created_at) }}</span>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">暂无通知日志</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';

const currentView = ref('audit');
const loading = ref(false);
const auditLogs = ref([]);
const notificationLogs = ref([]);
const errorMsg = ref('');

const successCount = computed(() => notificationLogs.value.filter((item) => item.success).length);
const failureCount = computed(() => notificationLogs.value.filter((item) => !item.success).length);

const formatTime = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', { hour12: false });
};

const loadLogs = async () => {
  loading.value = true;
  errorMsg.value = '';
  try {
    const [auditRes, notificationRes] = await Promise.all([
      fetch('http://127.0.0.1:5000/api/ext/audit-logs'),
      fetch('http://127.0.0.1:5000/api/ext/notification-logs')
    ]);

    if (!auditRes.ok || !notificationRes.ok) {
      const auditError = await auditRes.json().catch(() => ({}));
      const notificationError = await notificationRes.json().catch(() => ({}));
      errorMsg.value = auditError.error || notificationError.error || '日志加载失败，请检查权限或后端状态';
      auditLogs.value = [];
      notificationLogs.value = [];
      return;
    }

    const auditData = await auditRes.json();
    const notificationData = await notificationRes.json();

    auditLogs.value = Array.isArray(auditData) ? auditData : [];
    notificationLogs.value = Array.isArray(notificationData) ? notificationData : [];
  } catch (error) {
    console.error('加载日志失败:', error);
    errorMsg.value = '日志加载失败，请检查网络连接或后端服务';
    auditLogs.value = [];
    notificationLogs.value = [];
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadLogs();
});
</script>

<style scoped>
.logs-layout { padding: 30px; display: flex; flex-direction: column; gap: 20px; height: 100%; overflow-y: auto; box-sizing: border-box; }
.glass-panel { background: var(--bg-panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow); padding: 24px; }
.logs-header { display: flex; justify-content: space-between; align-items: center; gap: 20px; }
.logs-header h2 { margin: 0 0 6px 0; color: #fff; font-size: 24px; }
.logs-header p { margin: 0; color: var(--text-dim); font-size: 13px; }
.refresh-btn { background: linear-gradient(135deg, var(--primary), #0099cc); color: #000; border: none; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-weight: bold; }
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.summary-card { display: flex; flex-direction: column; gap: 8px; min-height: 96px; justify-content: center; }
.summary-label { color: var(--text-dim); font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
.summary-value { color: #fff; font-size: 30px; font-weight: 800; }
.summary-value.success { color: var(--success); }
.summary-value.fail { color: #ff6b6b; }
.logs-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding-top: 14px; padding-bottom: 14px; }
.logs-switch { display: flex; gap: 10px; flex-wrap: wrap; }
.switch-btn { background: rgba(255,255,255,0.05); color: var(--text-dim); border: 1px solid var(--border); padding: 10px 18px; border-radius: 999px; cursor: pointer; font-weight: 600; transition: 0.2s; }
.switch-btn.active { background: linear-gradient(135deg, var(--secondary), #4c1d95); color: #fff; }
.toolbar-note { color: var(--text-dim); font-size: 12px; text-align: right; }
.error-banner { color: #ffb4b4; background: rgba(255, 107, 107, 0.14); border-color: rgba(255, 107, 107, 0.26); padding-top: 14px; padding-bottom: 14px; }
.logs-panel { display: flex; flex-direction: column; min-height: 0; flex: 1; }
.panel-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.panel-title h3 { margin: 0; color: #fff; }
.panel-title span { color: var(--text-dim); font-size: 12px; }
.log-list { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; padding-right: 4px; }
.log-card { background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.log-main { display: flex; flex-direction: column; gap: 8px; }
.log-top { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.log-action { color: var(--primary); font-weight: 700; letter-spacing: 0.5px; }
.log-status { font-size: 12px; padding: 4px 10px; border-radius: 999px; text-transform: uppercase; }
.log-status.ok { background: rgba(0,255,157,0.15); color: var(--success); }
.log-status.fail { background: rgba(255,107,107,0.15); color: #ff6b6b; }
.log-details { color: #fff; font-size: 14px; line-height: 1.5; }
.log-meta { display: flex; flex-wrap: wrap; gap: 16px; color: var(--text-dim); font-size: 12px; }
.empty-state { min-height: 240px; display: flex; align-items: center; justify-content: center; color: var(--text-dim); font-style: italic; }

@media (max-width: 1100px) {
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 900px) {
  .logs-header { flex-direction: column; align-items: flex-start; }
  .logs-toolbar { flex-direction: column; align-items: flex-start; }
  .toolbar-note { text-align: left; }
  .log-top { flex-direction: column; align-items: flex-start; }
  .log-meta { flex-direction: column; gap: 8px; }
}

@media (max-width: 640px) {
  .summary-grid { grid-template-columns: 1fr; }
}
</style>
