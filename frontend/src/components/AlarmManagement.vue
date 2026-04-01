<template>
  <div class="alarm-layout">
    <!-- 左侧：报警配置 -->
    <div class="config-section">
      <div class="config-card glass-panel">
        <h2>⚙️ 报警配置</h2>
        
        <div class="config-group">
          <h3>报警级别设置</h3>
          <div class="level-item">
            <label class="switch-label">
              <input type="checkbox" v-model="config.enableSound" class="toggle-switch">
              <span class="switch-slider"></span>
              <span class="switch-text">声音报警</span>
            </label>
          </div>
          <div class="level-item">
            <label class="switch-label">
              <input type="checkbox" v-model="config.enableNotification" class="toggle-switch">
              <span class="switch-slider"></span>
              <span class="switch-text">浏览器通知</span>
            </label>
          </div>
          <div class="level-item">
            <label class="switch-label">
              <input type="checkbox" v-model="config.enableEmail" class="toggle-switch">
              <span class="switch-slider"></span>
              <span class="switch-text">邮件通知</span>
            </label>
          </div>
          <div class="level-item">
            <label class="switch-label">
              <input type="checkbox" v-model="config.enableSMS" class="toggle-switch">
              <span class="switch-slider"></span>
              <span class="switch-text">短信通知</span>
            </label>
          </div>
        </div>

        <div class="config-group">
          <h3>通知联系人</h3>
          <div class="contact-list">
            <div v-for="contact in contacts" :key="contact.id" class="contact-item">
              <div class="contact-info">
                <div class="contact-name">{{ contact.name }}</div>
                <div class="contact-detail">{{ contact.phone }} / {{ contact.email }}</div>
              </div>
              <button @click="removeContact(contact.id)" class="btn-remove">删除</button>
            </div>
          </div>
          <button @click="showAddContact = true" class="btn-add">+ 添加联系人</button>
        </div>

        <div class="config-group">
          <h3>通知时段</h3>
          <div class="time-range">
            <input type="time" v-model="config.startTime" class="time-input">
            <span>至</span>
            <input type="time" v-model="config.endTime" class="time-input">
          </div>
          <div class="hint">仅在该时段内发送通知</div>
        </div>

        <button @click="saveConfig" class="btn-save">保存配置</button>
      </div>
    </div>

    <!-- 右侧：报警历史 -->
    <div class="history-section">
      <div class="history-card glass-panel">
        <div class="history-header">
          <h2>📜 报警历史</h2>
          <div class="filter-group">
            <select v-model="filterStatus" class="filter-select">
              <option value="all">全部</option>
              <option value="pending">待处理</option>
              <option value="handled">已处理</option>
            </select>
            <input type="date" v-model="filterDate" class="date-input">
          </div>
        </div>

        <div class="history-list">
          <div v-for="alarm in filteredAlarms" :key="alarm.id" class="alarm-item">
            <div class="alarm-time">
              <div class="time-label">{{ alarm.date }}</div>
              <div class="time-value">{{ alarm.time }}</div>
            </div>
            <div class="alarm-content">
              <div class="alarm-title">{{ alarm.title }}</div>
              <div class="alarm-desc">{{ alarm.description }}</div>
              <div class="alarm-tags">
                <span class="tag location">{{ alarm.location }}</span>
                <span class="tag type">{{ alarm.type }}</span>
              </div>
            </div>
            <div class="alarm-actions">
              <span class="status-badge" :class="alarm.status">{{ alarm.statusText }}</span>
              <button v-if="alarm.status === 'pending' && isAdmin" @click="openWorkorderModal(alarm.id)" class="btn-handle">
                处理
              </button>
              <button @click="viewDetails(alarm.id)" class="btn-detail">详情</button>
            </div>
          </div>
          <div v-if="filteredAlarms.length === 0" class="empty-state">暂无报警记录</div>
        </div>
      </div>
    </div>

    <!-- 添加联系人弹窗 -->
    <div v-if="showAddContact" class="modal-overlay" @click="showAddContact = false">
      <div class="modal-content" @click.stop>
        <h3>添加联系人</h3>
        <div class="form-group">
          <label>姓名</label>
          <input type="text" v-model="newContact.name" placeholder="请输入姓名">
        </div>
        <div class="form-group">
          <label>电话</label>
          <input type="tel" v-model="newContact.phone" placeholder="请输入电话">
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input type="email" v-model="newContact.email" placeholder="请输入邮箱">
        </div>
        <div class="modal-actions">
          <button @click="addContact" class="btn-confirm">确定</button>
          <button @click="showAddContact = false" class="btn-cancel">取消</button>
        </div>
      </div>
    </div>

    <div v-if="selectedAlarm" class="modal-overlay" @click="selectedAlarm = null">
      <div class="modal-content detail-modal" @click.stop>
        <h3>报警详情</h3>
        <div class="detail-grid">
          <div class="detail-row">
            <span class="detail-label">报警编号</span>
            <span class="detail-value">#{{ selectedAlarm.id }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">报警时间</span>
            <span class="detail-value">{{ selectedAlarm.date }} {{ selectedAlarm.time }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">发生位置</span>
            <span class="detail-value">{{ selectedAlarm.location }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">事件类型</span>
            <span class="detail-value">{{ selectedAlarm.type }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">当前状态</span>
            <span class="detail-value">{{ selectedAlarm.statusText }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">描述信息</span>
            <span class="detail-value">{{ selectedAlarm.description }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">工单结果</span>
            <span class="detail-value">{{ selectedAlarm.workorder?.result || '暂无工单' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">工单备注</span>
            <span class="detail-value">{{ selectedAlarm.workorder?.comment || '-' }}</span>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-confirm" @click="selectedAlarm = null">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showWorkorderModal" class="modal-overlay" @click="closeWorkorderModal">
      <div class="modal-content detail-modal" @click.stop>
        <h3>处理报警工单</h3>
        <div class="form-group">
          <label>处理结果</label>
          <select v-model="workorderForm.result" class="time-input workorder-select">
            <option value="已确认真实跌倒">已确认真实跌倒</option>
            <option value="误报">误报</option>
            <option value="需继续观察">需继续观察</option>
          </select>
        </div>
        <div class="form-group">
          <label>处理备注</label>
          <textarea v-model="workorderForm.comment" class="workorder-textarea" placeholder="请输入处理说明"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeWorkorderModal">取消</button>
          <button class="btn-confirm" @click="submitWorkorder">提交工单</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const config = ref({
  enableSound: false,
  enableNotification: false,
  enableEmail: false,
  enableSMS: false,
  startTime: '00:00',
  endTime: '23:59'
});

const contacts = ref([]);

const alarmHistory = ref([]);

const filterStatus = ref('all');
const filterDate = ref('');
const showAddContact = ref(false);
const newContact = ref({ name: '', phone: '', email: '' });
const selectedAlarm = ref(null);
const showWorkorderModal = ref(false);
const pendingAlarmId = ref(null);
const workorderForm = ref({ result: '已确认真实跌倒', comment: '' });
const isAdmin = localStorage.getItem('role') === 'admin';

const filteredAlarms = computed(() => {
  return alarmHistory.value.filter(alarm => {
    const statusMatch = filterStatus.value === 'all' || alarm.status === filterStatus.value;
    const dateMatch = !filterDate.value || alarm.date === filterDate.value;
    return statusMatch && dateMatch;
  });
});

const saveConfig = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/alarms/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sound: config.value.enableSound,
        notification: config.value.enableNotification,
        email: config.value.enableEmail,
        sms: config.value.enableSMS,
        time_start: config.value.startTime,
        time_end: config.value.endTime,
        contacts: contacts.value
      })
    });
    const result = await response.json();
    alert(result.message || '配置已保存！');
  } catch (error) {
    console.error('保存配置失败:', error);
    alert('保存失败，请检查网络连接');
  }
};

const addContact = async () => {
  if (newContact.value.name && newContact.value.phone) {
    try {
      const contactToAdd = {
        id: Date.now(),
        name: newContact.value.name,
        phone: newContact.value.phone,
        email: newContact.value.email
      };
      
      const response = await fetch('http://localhost:5000/api/alarms/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(contactToAdd)
      });
      
      const result = await response.json();
      
      if (result.success) {
        contacts.value.push(contactToAdd);
        newContact.value = { name: '', phone: '', email: '' };
        showAddContact.value = false;
        alert('联系人添加成功！');
      } else {
        alert(result.message || '添加失败');
      }
    } catch (error) {
      console.error('添加联系人失败:', error);
      alert('保存失败，请检查网络连接');
    }
  }
};

const removeContact = async (id) => {
  try {
    const response = await fetch(`http://localhost:5000/api/alarms/contacts?id=${id}`, {
      method: 'DELETE'
    });
    
    const result = await response.json();
    
    if (result.success) {
      contacts.value = contacts.value.filter(c => c.id !== id);
      alert('联系人已删除');
    } else {
      alert(result.message || '删除失败');
    }
  } catch (error) {
    console.error('删除联系人失败:', error);
    alert('删除失败，请检查网络连接');
  }
};

const handleAlarm = async (id) => {
  try {
    const response = await fetch(`http://localhost:5000/api/alarms/handle/${id}`, {
      method: 'POST'
    });
    const result = await response.json();
    if (result.success) {
      const alarm = alarmHistory.value.find(a => a.id === id);
      if (alarm) {
        alarm.status = 'handled';
        alarm.statusText = '已处理';
      }
    }
  } catch (error) {
    console.error('处理报警失败:', error);
  }
};

const openWorkorderModal = (id) => {
  pendingAlarmId.value = id;
  workorderForm.value = { result: '已确认真实跌倒', comment: '' };
  showWorkorderModal.value = true;
};

const closeWorkorderModal = () => {
  showWorkorderModal.value = false;
  pendingAlarmId.value = null;
};

const fetchWorkorders = async () => {
  if (!isAdmin) return [];
  try {
    const res = await fetch('http://127.0.0.1:5000/api/ext/workorders');
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error('获取工单失败:', error);
    return [];
  }
};

const submitWorkorder = async () => {
  if (!pendingAlarmId.value) return;
  try {
    const response = await fetch('http://127.0.0.1:5000/api/ext/workorders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        alarm_id: pendingAlarmId.value,
        result: workorderForm.value.result,
        comment: workorderForm.value.comment,
        status: 'closed'
      })
    });
    const result = await response.json();
    if (result.success) {
      await handleAlarm(pendingAlarmId.value);
      closeWorkorderModal();
      loadAlarms();
    } else {
      alert(result.error || '提交工单失败');
    }
  } catch (error) {
    console.error('提交工单失败:', error);
  }
};

const viewDetails = (id) => {
  selectedAlarm.value = alarmHistory.value.find(alarm => alarm.id === id) || null;
};

// 加载报警数据
const loadAlarms = async () => {
  try {
    // 获取报警配置
    const configRes = await fetch('http://localhost:5000/api/alarms/config');
    const configData = await configRes.json();
    config.value = {
      enableSound: configData.sound ?? false,
      enableNotification: configData.notification ?? false,
      enableEmail: configData.email ?? false,
      enableSMS: configData.sms ?? false,
      startTime: configData.time_start || '00:00',
      endTime: configData.time_end || '23:59'
    };
    
    // 从独立的contacts接口获取联系人列表
    const contactsRes = await fetch('http://localhost:5000/api/alarms/contacts');
    const contactsData = await contactsRes.json();
    contacts.value = Array.isArray(contactsData) ? contactsData : [];

    // 获取报警历史
    const [historyRes, workorders] = await Promise.all([
      fetch('http://localhost:5000/api/alarms'),
      fetchWorkorders()
    ]);
    const history = await historyRes.json();
    const workorderMap = {};
    workorders.forEach((workorder) => {
      workorderMap[workorder.alarm_id] = workorder;
    });
    alarmHistory.value = (Array.isArray(history) ? history : []).map(alarm => ({
      id: alarm.id,
      date: (alarm.time || '').split(' ')[0] || '',
      time: (alarm.time || '').split(' ')[1] || '',
      title: '跌倒警报',
      description: `检测到${alarm.location}发生跌倒事件`,
      location: alarm.location,
      type: alarm.type,
      status: alarm.status === '已处理' ? 'handled' : 'pending',
      statusText: alarm.status,
      workorder: workorderMap[alarm.id] || null
    }));
  } catch (error) {
    console.error('加载报警数据失败:', error);
  }
};

onMounted(() => {
  loadAlarms();
});
</script>

<style scoped>
.alarm-layout { padding: 30px; display: grid; grid-template-columns: 400px 1fr; gap: 30px; height: 100%; overflow: hidden; }
.glass-panel { background: var(--bg-panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow); padding: 24px; }

.config-section { overflow-y: auto; }
.config-card h2 { margin: 0 0 24px 0; font-size: 20px; color: #fff; }
.config-group { margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
.config-group:last-child { border-bottom: none; }
.config-group h3 { font-size: 14px; color: var(--text-dim); margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }

.level-item { margin-bottom: 12px; }
.switch-label { display: flex; align-items: center; gap: 12px; cursor: pointer; }
.toggle-switch { display: none; }
.switch-slider { width: 40px; height: 20px; background: #333; border-radius: 20px; position: relative; transition: 0.3s; }
.switch-slider::before { content: ''; position: absolute; width: 16px; height: 16px; background: #666; border-radius: 50%; top: 2px; left: 2px; transition: 0.3s; }
.toggle-switch:checked + .switch-slider { background: var(--primary); }
.toggle-switch:checked + .switch-slider::before { transform: translateX(20px); background: #fff; }
.switch-text { color: #fff; font-size: 14px; }

.contact-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px; }
.contact-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; }
.contact-info { flex: 1; }
.contact-name { font-size: 14px; color: #fff; font-weight: bold; margin-bottom: 4px; }
.contact-detail { font-size: 12px; color: var(--text-dim); }
.btn-remove { background: rgba(255,0,85,0.2); border: 1px solid #ff0055; color: #ff0055; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }
.btn-add { width: 100%; background: rgba(0,243,255,0.1); border: 1px dashed var(--primary); color: var(--primary); padding: 10px; border-radius: 8px; cursor: pointer; }

.time-range { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.time-input { background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 8px 12px; border-radius: 4px; }
.hint { font-size: 12px; color: var(--text-dim); font-style: italic; }

.btn-save { width: 100%; background: linear-gradient(135deg, var(--primary), #0099cc); color: #000; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 20px; }

.history-section { display: flex; flex-direction: column; overflow: hidden; }
.history-card { display: flex; flex-direction: column; height: 100%; }
.history-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid var(--border); }
.history-header h2 { margin: 0; font-size: 20px; color: #fff; }
.filter-group { display: flex; gap: 10px; }
.filter-select, .date-input { background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 6px 10px; border-radius: 4px; font-size: 12px; }

.history-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.alarm-item { display: flex; gap: 20px; padding: 16px; background: rgba(0,0,0,0.2); border-radius: 8px; border-left: 4px solid #ff6b6b; }
.alarm-time { min-width: 100px; }
.time-label { font-size: 11px; color: var(--text-dim); margin-bottom: 4px; }
.time-value { font-size: 16px; color: #fff; font-weight: bold; }
.alarm-content { flex: 1; }
.alarm-title { font-size: 14px; color: #fff; font-weight: bold; margin-bottom: 6px; }
.alarm-desc { font-size: 13px; color: var(--text-dim); margin-bottom: 8px; }
.alarm-tags { display: flex; gap: 6px; }
.tag { font-size: 11px; padding: 3px 8px; border-radius: 4px; }
.tag.location { background: rgba(0,243,255,0.2); color: var(--primary); }
.tag.type { background: rgba(255,230,109,0.2); color: #ffe66d; }
.alarm-actions { display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
.status-badge { font-size: 11px; padding: 4px 10px; border-radius: 4px; }
.status-badge.pending { background: rgba(255,107,107,0.2); color: #ff6b6b; }
.status-badge.handled { background: rgba(0,255,157,0.2); color: var(--success); }
.btn-handle, .btn-detail { background: rgba(0,243,255,0.2); border: 1px solid var(--primary); color: var(--primary); padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-dim); font-style: italic; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 16px; padding: 30px; min-width: 400px; }
.modal-content h3 { margin: 0 0 20px 0; color: #fff; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; font-size: 12px; color: var(--text-dim); margin-bottom: 6px; }
.form-group input { width: 100%; background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 4px; box-sizing: border-box; }
.workorder-select { width: 100%; }
.workorder-textarea { width: 100%; min-height: 110px; background: rgba(0,0,0,0.3); border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 4px; box-sizing: border-box; resize: vertical; }
.modal-actions { display: flex; gap: 10px; margin-top: 20px; }
.btn-confirm, .btn-cancel { flex: 1; padding: 10px; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-confirm { background: var(--primary); color: #000; border: none; }
.btn-cancel { background: transparent; border: 1px solid var(--border); color: var(--text-dim); }
.detail-modal { max-width: 520px; }
.detail-grid { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }
.detail-row { display: flex; justify-content: space-between; gap: 16px; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; }
.detail-label { color: var(--text-dim); font-size: 13px; flex-shrink: 0; }
.detail-value { color: #fff; font-size: 14px; text-align: right; word-break: break-word; }
</style>
