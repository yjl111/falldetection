<template>
  <div class="replay-layout">
    <!-- 左侧列表 -->
    <aside class="sidebar glass-panel">
      <div class="panel-header">
        <h3><span class="deco">#</span>  历史记录</h3>
        <button class="refresh-btn" @click="fetchHistory" :disabled="loading">
          <span class="icon">↻</span>
        </button>
      </div>
      
      <div class="record-list" v-if="records.length > 0">
        <div 
          v-for="item in records" 
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
          <div class="item-status"></div>
        </div>
      </div>
      
      <div v-else class="empty-state">
        {{ loading ? 'Loading records...' : 'No history found' }}
      </div>
    </aside>

    <!-- 右侧播放器 -->
    <main class="player-container">
      <div class="video-card glass-panel">
        <div class="card-header">
          <h2>{{ currentVideoName || 'Select a video to play' }}</h2>
          <button v-if="currentVideoId" class="download-btn" @click="downloadVideo">
            ⬇ Download
          </button>
        </div>
        
        <div class="player-wrapper">
          <video 
            v-if="currentVideoUrl" 
            ref="videoPlayer" 
            controls 
            autoplay 
            class="cyber-player"
            :src="currentVideoUrl"
          >
            Your browser does not support the video tag.
          </video>
          
          <div v-else class="placeholder">
            <div class="radar-scan"></div>
            <p>等待选择</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const records = ref([]);
const loading = ref(false);
const currentVideoId = ref(null);
const currentVideoUrl = ref('');
const currentVideoName = ref('');
const videoPlayer = ref(null);

const fetchHistory = async () => {
  loading.value = true;
  try {
    const res = await fetch('/api/history');
    if (res.ok) {
      records.value = await res.json();
    }
  } catch (e) {
    console.error("Failed to load history", e);
  } finally {
    loading.value = false;
  }
};

const playVideo = (item) => {
  currentVideoId.value = item.id;
  currentVideoName.value = item.filename;
  // 使用 MongoDB 的 GridFS 接口
  // 如果 item.video_file_id 存在，说明是 MongoDB 存储，否则可能是旧的本地文件
  // 这里统一使用后端提供的通用接口 /api/video/db/<id>
  // 注意：这里的 id 是数据库记录的 _id
  currentVideoUrl.value = `/api/video/db/${item.id}`;
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

onMounted(() => {
  fetchHistory();
});
</script>

<style scoped>
.replay-layout { display: flex; height: 100%; gap: 20px; padding: 20px; box-sizing: border-box; }
.glass-panel { background: var(--bg-panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow); }

/* Sidebar */
.sidebar { width: 320px; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.panel-header h3 { margin: 0; font-size: 14px; color: var(--text-dim); text-transform: uppercase; }
.deco { color: var(--primary); }
.refresh-btn { background: transparent; border: none; color: var(--primary); cursor: pointer; font-size: 18px; transition: 0.3s; }
.refresh-btn:hover { transform: rotate(180deg); color: #fff; }

.record-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 5px; }
.record-item { 
  display: flex; align-items: center; gap: 12px; padding: 12px; 
  background: rgba(255,255,255,0.03); border-radius: 8px; cursor: pointer; transition: 0.2s; border: 1px solid transparent;
}
.record-item:hover { background: rgba(255,255,255,0.08); }
.record-item.active { background: rgba(0, 243, 255, 0.1); border-color: var(--primary); }

.item-icon { font-size: 20px; }
.item-info { flex: 1; overflow: hidden; }
.item-name { font-size: 14px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
.item-time { font-size: 11px; color: var(--text-dim); }

.empty-state { text-align: center; color: var(--text-dim); margin-top: 50px; font-style: italic; }

/* Player */
.player-container { flex: 1; display: flex; flex-direction: column; }
.video-card { flex: 1; display: flex; flex-direction: column; padding: 24px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.card-header h2 { margin: 0; font-size: 18px; color: var(--primary); }
.download-btn { 
  background: var(--secondary); color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; transition: 0.2s;
}
.download-btn:hover { background: #5a189a; }

.player-wrapper { flex: 1; background: #000; border-radius: 12px; overflow: hidden; position: relative; border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; }
.cyber-player { width: 100%; height: 100%; object-fit: contain; }

.placeholder { text-align: center; color: var(--text-dim); }
.radar-scan { 
  width: 100px; height: 100px; border: 2px solid var(--border); border-radius: 50%; margin: 0 auto 20px; 
  position: relative; animation: radar 3s infinite linear; 
}
.radar-scan::after {
  content: ''; position: absolute; top: 0; left: 50%; width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.1));
  transform-origin: 0 50%;
}
@keyframes radar { to { transform: rotate(360deg); } }
</style>