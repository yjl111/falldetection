<template>
  <div class="replay-layout">
    <!-- 左侧列表 -->
    <aside class="sidebar glass-panel">
      <div class="panel-header">
        <h3><span class="deco">#</span> 历史记录</h3>
        <div class="header-actions">
          <span class="record-count">共 {{ records.length }} 条</span>
          <button class="refresh-btn" @click="fetchHistory" :disabled="loading" title="刷新">↻</button>
        </div>
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="搜索文件名..."
          type="text"
        />
        <button v-if="searchKeyword" class="search-clear" @click="searchKeyword = ''">×</button>
      </div>

      <div class="record-list" v-if="filteredRecords.length > 0">
        <div
          v-for="item in filteredRecords"
          :key="item.id"
          class="record-item"
          :class="{ active: currentVideoId === item.id }"
          @click="playVideo(item)"
        >
          <div class="item-icon">🎬</div>
          <div class="item-info">
            <div class="item-name">{{ item.filename }}</div>
            <div class="item-time">{{ item.timestamp }}</div>
          </div>
          <button
            class="item-delete"
            @click.stop="confirmDelete(item)"
            title="删除"
          >🗑</button>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">📂</div>
        <div>{{ loading ? '正在加载...' : (searchKeyword ? '无匹配记录' : '暂无历史记录') }}</div>
      </div>
    </aside>

    <!-- 右侧播放器 -->
    <main class="player-container">
      <div class="video-card glass-panel">
        <!-- 视频信息头部 -->
        <div class="card-header" v-if="currentVideoId">
          <div class="video-meta">
            <h2>{{ currentVideoName }}</h2>
            <div class="meta-tags">
              <span class="meta-tag time">🕐 {{ currentVideoTime }}</span>
              <span class="meta-tag type">⚡ 跌倒事件</span>
              <span class="meta-tag source">📦 证据留存</span>
            </div>
          </div>
          <button class="download-btn" @click="downloadVideo">⬇ 下载</button>
        </div>
        <div class="card-header" v-else>
          <h2 class="placeholder-title">请从左侧选择一条记录播放</h2>
        </div>

        <div class="player-wrapper">
          <video
            v-if="currentVideoUrl"
            ref="videoPlayer"
            controls
            autoplay
            class="cyber-player"
            :src="currentVideoUrl"
          ></video>

          <div v-else class="placeholder">
            <div class="radar-scan"></div>
            <p>从左侧列表选择视频开始播放</p>
          </div>
        </div>
      </div>
    </main>

    <!-- 删除确认弹窗 -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal-box glass-panel">
        <div class="modal-icon">⚠️</div>
        <h3>确认删除</h3>
        <p>删除后将无法恢复，确认删除该记录？</p>
        <div class="modal-name">{{ deleteTarget.filename }}</div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="deleteTarget = null">取消</button>
          <button class="btn-confirm" @click="doDelete">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const records = ref([]);
const loading = ref(false);
const searchKeyword = ref('');
const currentVideoId = ref(null);
const currentVideoUrl = ref('');
const currentVideoName = ref('');
const currentVideoTime = ref('');
const videoPlayer = ref(null);
const deleteTarget = ref(null);

// 搜索过滤
const filteredRecords = computed(() => {
  if (!searchKeyword.value.trim()) return records.value;
  const kw = searchKeyword.value.trim().toLowerCase();
  return records.value.filter(r => r.filename.toLowerCase().includes(kw));
});

const fetchHistory = async () => {
  loading.value = true;
  try {
    const res = await fetch('http://localhost:5000/api/history');
    if (res.ok) records.value = await res.json();
  } catch (e) {
    console.error('加载历史记录失败', e);
  } finally {
    loading.value = false;
  }
};

const playVideo = (item) => {
  currentVideoId.value = item.id;
  currentVideoName.value = item.filename;
  currentVideoTime.value = item.timestamp;
  currentVideoUrl.value = `http://localhost:5000/api/video/db/${item.id}`;
};

const downloadVideo = () => {
  if (!currentVideoUrl.value) return;
  const a = document.createElement('a');
  a.href = currentVideoUrl.value;
  a.download = currentVideoName.value;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

const confirmDelete = (item) => {
  deleteTarget.value = item;
};

const doDelete = async () => {
  if (!deleteTarget.value) return;
  const id = deleteTarget.value.id;
  try {
    const res = await fetch(`http://localhost:5000/api/history/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      records.value = records.value.filter(r => r.id !== id);
      // 如果删除的是当前播放视频，清空播放器
      if (currentVideoId.value === id) {
        currentVideoId.value = null;
        currentVideoUrl.value = '';
        currentVideoName.value = '';
        currentVideoTime.value = '';
      }
    }
  } catch (e) {
    console.error('删除失败', e);
  } finally {
    deleteTarget.value = null;
  }
};

onMounted(() => {
  fetchHistory();
});
</script>

<style scoped>
.replay-layout { display: flex; height: 100%; gap: 20px; padding: 20px; box-sizing: border-box; }
.glass-panel { background: var(--bg-panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow); }

/* ===== 侧边栏 ===== */
.sidebar { width: 320px; padding: 20px; display: flex; flex-direction: column; gap: 12px; flex-shrink: 0; }

.panel-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.panel-header h3 { margin: 0; font-size: 14px; color: var(--text-dim); text-transform: uppercase; }
.deco { color: var(--primary); }
.header-actions { display: flex; align-items: center; gap: 10px; }
.record-count { font-size: 12px; color: var(--text-dim); background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 10px; }
.refresh-btn { background: transparent; border: none; color: var(--primary); cursor: pointer; font-size: 18px; transition: 0.3s; line-height: 1; }
.refresh-btn:hover { transform: rotate(180deg); color: #fff; }

/* 搜索框 */
.search-box { display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.25); border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; }
.search-icon { font-size: 14px; flex-shrink: 0; }
.search-input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 13px; }
.search-input::placeholder { color: var(--text-dim); }
.search-clear { background: transparent; border: none; color: var(--text-dim); cursor: pointer; font-size: 16px; line-height: 1; padding: 0; }
.search-clear:hover { color: #fff; }

/* 记录列表 */
.record-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px; }
.record-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  background: rgba(255,255,255,0.03); border-radius: 8px; cursor: pointer;
  transition: 0.2s; border: 1px solid transparent;
}
.record-item:hover { background: rgba(255,255,255,0.07); }
.record-item.active { background: rgba(0, 243, 255, 0.08); border-color: var(--primary); }

.item-icon { font-size: 18px; flex-shrink: 0; }
.item-info { flex: 1; overflow: hidden; }
.item-name { font-size: 13px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 3px; }
.item-time { font-size: 11px; color: var(--text-dim); }
.item-delete { background: transparent; border: none; color: var(--text-dim); cursor: pointer; font-size: 14px; padding: 4px; border-radius: 4px; opacity: 0; transition: 0.2s; }
.record-item:hover .item-delete { opacity: 1; }
.item-delete:hover { color: #ff6b6b; background: rgba(255,107,107,0.1); }

.empty-state { text-align: center; color: var(--text-dim); margin-top: 40px; font-style: italic; font-size: 13px; }
.empty-icon { font-size: 36px; margin-bottom: 10px; }

/* ===== 播放器 ===== */
.player-container { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.video-card { flex: 1; display: flex; flex-direction: column; padding: 24px; }

.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 16px; }
.video-meta { flex: 1; min-width: 0; }
.video-meta h2 { margin: 0 0 8px 0; font-size: 16px; color: var(--primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.placeholder-title { margin: 0; font-size: 15px; color: var(--text-dim); font-weight: normal; }
.meta-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.meta-tag { font-size: 11px; padding: 3px 8px; border-radius: 10px; background: rgba(255,255,255,0.06); color: var(--text-dim); border: 1px solid var(--border); }
.meta-tag.time { border-color: rgba(0,243,255,0.3); color: var(--primary); }
.meta-tag.type { border-color: rgba(255,107,107,0.3); color: #ff6b6b; }

.download-btn { background: var(--secondary); color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; transition: 0.2s; white-space: nowrap; flex-shrink: 0; }
.download-btn:hover { background: #5a189a; }

.player-wrapper { flex: 1; background: #000; border-radius: 12px; overflow: hidden; position: relative; border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; min-height: 200px; }
.cyber-player { width: 100%; height: 100%; object-fit: contain; display: block; }

.placeholder { text-align: center; color: var(--text-dim); }
.placeholder p { font-size: 13px; margin-top: 16px; }
.radar-scan {
  width: 80px; height: 80px; border: 2px solid var(--border); border-radius: 50%; margin: 0 auto;
  position: relative; animation: radar 3s infinite linear;
}
.radar-scan::after {
  content: ''; position: absolute; top: 0; left: 50%; width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0,243,255,0.15));
  transform-origin: 0 50%;
}
@keyframes radar { to { transform: rotate(360deg); } }

/* ===== 确认弹窗 ===== */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-box { padding: 32px; width: 360px; text-align: center; }
.modal-icon { font-size: 40px; margin-bottom: 12px; }
.modal-box h3 { margin: 0 0 8px 0; font-size: 18px; color: #fff; }
.modal-box p { margin: 0 0 12px 0; font-size: 13px; color: var(--text-dim); }
.modal-name { font-size: 12px; color: var(--primary); background: rgba(0,243,255,0.08); border: 1px solid rgba(0,243,255,0.2); border-radius: 6px; padding: 6px 12px; margin-bottom: 24px; word-break: break-all; }
.modal-actions { display: flex; gap: 12px; justify-content: center; }
.btn-cancel { flex: 1; background: rgba(255,255,255,0.08); border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 14px; transition: 0.2s; }
.btn-cancel:hover { background: rgba(255,255,255,0.15); }
.btn-confirm { flex: 1; background: rgba(255,107,107,0.2); border: 1px solid #ff6b6b; color: #ff6b6b; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 14px; transition: 0.2s; }
.btn-confirm:hover { background: #ff6b6b; color: #fff; }
</style>

 