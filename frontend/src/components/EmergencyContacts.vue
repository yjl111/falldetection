<template>
  <div class="contacts-dashboard dashboard-panel">
    <div class="panel-header">
      <h2><span class="icon">👤</span> 用户中心</h2>
      <p class="subtitle">维护个人资料、查看系统消息，并管理跌倒报警紧急联系人</p>
    </div>

    <div class="tab-bar">
      <button class="tab-btn" :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">个人资料</button>
      <button class="tab-btn" :class="{ active: activeTab === 'messages' }" @click="activeTab = 'messages'">我的消息</button>
      <button class="tab-btn" :class="{ active: activeTab === 'contacts' }" @click="activeTab = 'contacts'">紧急联系人</button>
    </div>

    <div v-if="activeTab === 'profile'" class="profile-panel">
      <div class="form-grid">
        <div class="form-group">
          <label>用户名</label>
          <input type="text" class="input-field" :value="profile.username || localUsername" disabled />
        </div>
        <div class="form-group">
          <label>真实姓名</label>
          <input type="text" v-model="profile.real_name" class="input-field" placeholder="请输入真实姓名" />
        </div>
        <div class="form-group">
          <label>联系电话</label>
          <input type="text" v-model="profile.phone" class="input-field" placeholder="请输入联系电话" />
        </div>
        <div class="form-group">
          <label>年龄</label>
          <input type="number" v-model="profile.age" class="input-field" placeholder="请输入年龄" />
        </div>
        <div class="form-group full-width">
          <label>家庭住址</label>
          <input type="text" v-model="profile.address" class="input-field" placeholder="请输入家庭住址" />
        </div>
        <div class="form-group full-width">
          <label>健康备注</label>
          <textarea v-model="profile.medical_notes" class="input-field textarea-field" placeholder="例如慢病情况、行动不便情况等"></textarea>
        </div>
      </div>
      <div class="actions-bar">
        <button class="btn btn-primary" @click="saveProfile">保存资料</button>
      </div>
    </div>

    <div v-else-if="activeTab === 'messages'" class="message-panel">
      <div class="message-list" v-if="messages.length">
        <div v-for="message in messages" :key="message._id" class="message-card" :class="{ unread: !message.is_read }">
          <div class="message-header">
            <div>
              <div class="message-title">{{ message.title }}</div>
              <div class="message-meta">{{ message.type || 'system' }} · {{ formatTime(message.created_at) }}</div>
            </div>
            <button v-if="!message.is_read" class="btn btn-outline btn-sm" @click="markAsRead(message._id)">标记已读</button>
          </div>
          <div class="message-content">{{ message.content }}</div>
        </div>
      </div>
      <div v-else class="empty-text">暂无消息</div>
    </div>

    <div v-else>
      <div class="actions-bar">
        <button class="btn btn-primary" @click="showAddModal = true">+ 新增联系人</button>
      </div>

      <div class="content-table">
      <table class="data-table">
        <thead>
          <tr>
            <th>姓名</th>
            <th>关系</th>
            <th>联系电话</th>
            <th>电子邮箱</th>
            <th>通知优先级</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="contact in contacts" :key="contact._id">
            <td>{{ contact.contact_name }}</td>
            <td><span class="badge">{{ contact.relationship }}</span></td>
            <td>{{ contact.phone }}</td>
            <td>{{ contact.email || '-' }}</td>
            <td>{{ contact.notify_level === 1 ? '🔴 紧急' : '🟡 普通' }}</td>
            <td>
              <span :class="['status-dot', contact.is_active ? 'active' : 'inactive']"></span>
              {{ contact.is_active ? '启用' : '停用' }}
            </td>
            <td>
              <button class="btn btn-sm btn-outline" @click="toggleStatus(contact)">切换状态</button>
              <button class="btn btn-sm btn-danger" @click="deleteContact(contact._id)">删除</button>
            </td>
          </tr>
          <tr v-if="contacts.length === 0">
            <td colspan="7" class="empty-text">暂无联系人数据</td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <div class="modal-overlay" v-if="showAddModal">
      <div class="modal-content">
        <h3>新增紧急联系人</h3>
        <div class="form-group">
          <label>姓名</label>
          <input type="text" v-model="form.contact_name" class="input-field" placeholder="如：张三" />
        </div>
        <div class="form-group">
          <label>关系</label>
          <select v-model="form.relationship" class="input-field">
            <option value="子女">子女</option>
            <option value="配偶">配偶</option>
            <option value="护工">护工</option>
            <option value="医生">医生</option>
            <option value="管理员">管理员</option>
          </select>
        </div>
        <div class="form-group">
          <label>联系电话</label>
          <input type="text" v-model="form.phone" class="input-field" placeholder="手机号" />
        </div>
        <div class="form-group">
          <label>电子邮箱</label>
          <input type="email" v-model="form.email" class="input-field" placeholder="通知邮箱" />
        </div>
        <div class="form-group">
          <label>通知优先级</label>
          <select v-model="form.notify_level" class="input-field">
            <option :value="1">紧急 (优先通知)</option>
            <option :value="2">普通 (延迟通知)</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveContact">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const activeTab = ref('profile');
const contacts = ref([]);
const showAddModal = ref(false);
const localUsername = localStorage.getItem('username') || 'admin';
const profile = ref({
  username: localUsername,
  real_name: '',
  phone: '',
  address: '',
  age: '',
  medical_notes: ''
});
const messages = ref([]);

const form = ref({
  belong_to_user: localUsername,
  contact_name: '',
  relationship: '子女',
  phone: '',
  email: '',
  notify_level: 1,
  is_active: true
});

const formatTime = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', { hour12: false });
};

const fetchProfile = async () => {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/ext/profile');
    if (res.ok) {
      const data = await res.json();
      profile.value = {
        username: data.username || localUsername,
        real_name: data.real_name || '',
        phone: data.phone || '',
        address: data.address || '',
        age: data.age || '',
        medical_notes: data.medical_notes || ''
      };
    }
  } catch (err) {
    console.error("获取资料失败:", err);
  }
};

const saveProfile = async () => {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/ext/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile.value)
    });
    const data = await res.json();
    alert(data.message || '资料已保存');
  } catch (err) {
    console.error("保存资料失败:", err);
  }
};

const fetchMessages = async () => {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/ext/messages');
    if (res.ok) {
      const data = await res.json();
      messages.value = Array.isArray(data) ? data : [];
    }
  } catch (err) {
    console.error("获取消息失败:", err);
  }
};

const markAsRead = async (id) => {
  try {
    await fetch(`http://127.0.0.1:5000/api/ext/messages/${id}/read`, { method: 'POST' });
    fetchMessages();
  } catch (err) {
    console.error("标记已读失败:", err);
  }
};

const fetchContacts = async () => {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/ext/contacts');
    if (res.ok) {
      contacts.value = await res.json();
    }
  } catch (err) {
    console.error("获取联系人失败:", err);
  }
};

const saveContact = async () => {
  try {
    await fetch('http://127.0.0.1:5000/api/ext/contacts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    });
    closeModal();
    fetchContacts();
  } catch (err) {
    console.error("保存失败:", err);
  }
};

const toggleStatus = async (contact) => {
  try {
    await fetch(`http://127.0.0.1:5000/api/ext/contacts/${contact._id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !contact.is_active })
    });
    fetchContacts();
  } catch (err) {
    console.error("更新状态失败:", err);
  }
};

const deleteContact = async (id) => {
  if (!confirm('确定要删除这个联系人吗？')) return;
  try {
    await fetch(`http://127.0.0.1:5000/api/ext/contacts/${id}`, {
      method: 'DELETE'
    });
    fetchContacts();
  } catch (err) {
    console.error("删除失败:", err);
  }
};

const closeModal = () => {
  showAddModal.value = false;
  form.value = {
    belong_to_user: localUsername,
    contact_name: '',
    relationship: '子女',
    phone: '',
    email: '',
    notify_level: 1,
    is_active: true
  };
};

onMounted(() => {
  fetchProfile();
  fetchMessages();
  fetchContacts();
});
</script>

<style scoped>
.dashboard-panel {
  background: rgba(30, 39, 56, 0.7);
  border: 1px solid rgba(0, 255, 136, 0.2);
  border-radius: 12px;
  padding: 20px;
  color: #fff;
}
.panel-header h2 { margin: 0 0 5px 0; color: #00ff88; }
.subtitle { font-size: 13px; color: #8ba3b5; margin-bottom: 20px; }
.tab-bar { display: flex; gap: 10px; margin-bottom: 18px; }
.tab-btn { border: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.15); color: #9fb2c5; padding: 8px 14px; border-radius: 999px; cursor: pointer; font-weight: 700; }
.tab-btn.active { color: #fff; background: linear-gradient(90deg, rgba(0,255,136,0.25), rgba(0,179,255,0.25)); border-color: rgba(0,255,136,0.25); }
.actions-bar { margin-bottom: 15px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.full-width { grid-column: 1 / -1; }
.textarea-field { min-height: 100px; resize: vertical; }
.message-list { display: flex; flex-direction: column; gap: 12px; }
.message-card { background: rgba(15, 23, 42, 0.55); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 16px; }
.message-card.unread { border-color: rgba(0,255,136,0.3); box-shadow: 0 0 0 1px rgba(0,255,136,0.1) inset; }
.message-header { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.message-title { color: #fff; font-weight: bold; margin-bottom: 4px; }
.message-meta { color: #8ba3b5; font-size: 12px; }
.message-content { color: #d9e5ee; line-height: 1.6; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  overflow: hidden;
}
.data-table th, .data-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.data-table th { background: rgba(0, 255, 136, 0.1); color: #00ff88; font-weight: bold; }
.badge { background: rgba(0, 150, 255, 0.2); color: #00e5ff; padding: 3px 8px; border-radius: 12px; font-size: 12px; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
.status-dot.active { background: #00ff88; box-shadow: 0 0 5px #00ff88; }
.status-dot.inactive { background: #ff3366; }
.empty-text { text-align: center!important; color: #666; padding: 30px!important; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7);
  display: flex; justify-content: center; align-items: center; z-index: 1000;
}
.modal-content {
  background: #1e2738; padding: 25px; border-radius: 12px; width: 400px;
  border: 1px solid rgba(0,255,136,0.3);
}
.modal-content h3 { margin-top: 0; color: #00ff88; margin-bottom: 20px; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-size: 14px; color: #a4b5c4; }
.input-field {
  width: 100%; padding: 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);
  background: rgba(0,0,0,0.2); color: #fff; box-sizing: border-box;
}
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }

.btn { padding: 8px 15px; border-radius: 6px; cursor: pointer; border: none; font-weight: bold; transition: 0.3s; }
.btn-primary { background: linear-gradient(90deg, #00ff88, #00b3ff); color: #000; }
.btn-primary:hover { opacity: 0.8; }
.btn-secondary { background: #334; color: #fff; }
.btn-outline { background: transparent; border: 1px solid #00ff88; color: #00ff88; }
.btn-danger { background: transparent; border: 1px solid #ff3366; color: #ff3366; }
.btn-sm { padding: 4px 8px; font-size: 12px; margin-right: 5px; }
</style>
