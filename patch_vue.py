import io

path = 'd:/falldetection/frontend/src/components/AlarmManagement.vue'
with io.open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add button
old_btn = '''            <div class="alarm-actions">
              <span class="status-badge" :class="alarm.status">{{ alarm.statusText }}</span>
              <button v-if="alarm.status === 'pending'" @click="handleAlarm(alarm.id)" class="btn-handle">
                处理
              </button>
              <button @click="viewDetails(alarm.id)" class="btn-detail">详情</button>
            </div>'''
new_btn = '''            <div class="alarm-actions">
              <span class="status-badge" :class="alarm.status">{{ alarm.statusText }}</span>
              <button v-if="alarm.status === 'pending'" @click="handleAlarm(alarm.id)" class="btn-handle">
                处理
              </button>
              <button @click="openFeedbackModal(alarm)" class="btn-detail" style="background:#ff9800; color:#000; border:none; margin-right:5px;">AI 误报纠错</button>
              <button @click="viewDetails(alarm.id)" class="btn-detail">详情</button>
            </div>'''
content = content.replace(old_btn, new_btn)

# 2. Add Modal
old_modal = '''        </template>
          <div class="modal-actions">
            <button @click="showDetail = false" class="btn-confirm">关闭</button>
          </div>
        </div>
      </div>
    </div>
</template>'''
new_modal = '''        </template>
          <div class="modal-actions">
            <button @click="showDetail = false" class="btn-confirm">关闭</button>
          </div>
        </div>
      </div>

      <!-- AI 误报纠错弹窗 -->
      <div v-if="showFeedbackModal" class="modal-overlay" @click="showFeedbackModal = false">
        <div class="modal-content" @click.stop style="max-width: 450px;">
          <h3 style="color: #ff9800;">🤖 AI 误报纠错</h3>
          <p style="color: #a4b5c4; font-size: 13px; margin-bottom: 20px;">
            请为您认为不准确的报警打上更为准确的标签，以帮助我们的模型进行下一轮迭代。
          </p>
          
          <div class="form-group">
            <label>此事件是否为误报？</label>
            <div style="display: flex; gap: 15px; margin-top: 5px; color:#fff;">
              <label><input type="radio" :value="true" v-model="feedbackForm.is_false_positive" /> 是，这是误报（正常行为）</label>
              <label><input type="radio" :value="false" v-model="feedbackForm.is_false_positive" /> 否，确实跌倒了（漏报或类型错）</label>
            </div>
          </div>
          
          <div class="form-group" style="margin-top: 15px;">
            <label>正确的状态/动作标签：</label>
            <select v-model="feedbackForm.correct_label" style="width: 100%; border-radius: 6px; padding: 10px; background: rgba(0,0,0,0.3); color: #fff; border: 1px solid rgba(255,255,255,0.1);">
              <optgroup label="正常行为 (False Positives)">
                <option value="sitting">坐下 (Sitting)</option>
                <option value="bending">弯腰捡东西 (Bending)</option>
                <option value="sleeping">正常躺卧 (Sleeping)</option>
                <option value="squatting">下蹲 (Squatting)</option>
                <option value="other_normal">其他正常行为 (Other Normal)</option>
              </optgroup>
              <optgroup label="跌倒事件 (True Positives)">
                <option value="fall_heavy">重度跌倒 (Heavy Fall)</option>
                <option value="fall_slip">滑倒 (Slip)</option>
                <option value="fainting">晕厥 (Fainting)</option>
              </optgroup>
            </select>
          </div>
          
          <div class="form-group" style="margin-top: 15px;">
            <label>详细描述 (可选)：</label>
            <textarea v-model="feedbackForm.comment" rows="3" placeholder="例如：用户只是蹲下捡东西，被系统误判..." style="width: 100%; border-radius: 6px; padding: 10px; background: rgba(0,0,0,0.3); color: #fff; border: 1px solid rgba(255,255,255,0.1); box-sizing: border-box;"></textarea>
          </div>

          <div class="modal-actions" style="margin-top: 25px;">
            <button @click="showFeedbackModal = false" class="btn-cancel">取消</button>
            <button @click="submitFeedback" class="btn-confirm" style="background:#ff9800;">提交并反馈至库</button>
          </div>
        </div>
      </div>

    </div>
</template>'''
content = content.replace(old_modal, new_modal)

# 3. Add Script Variables
old_script = '''<script setup>
import { ref, computed, onMounted } from 'vue';

const config = ref({'''
new_script = '''<script setup>
import { ref, computed, onMounted } from 'vue';

const showFeedbackModal = ref(false);
const currentFeedbackAlarmId = ref(null);
const feedbackForm = ref({
  is_false_positive: true,
  correct_label: 'sitting',
  comment: '',
  reviewer: localStorage.getItem('username') || 'admin'
});

const openFeedbackModal = (alarm) => {
  currentFeedbackAlarmId.value = alarm.id || alarm._id;
  feedbackForm.value.is_false_positive = true;
  feedbackForm.value.correct_label = 'sitting';
  feedbackForm.value.comment = '';
  showFeedbackModal.value = true;
};

const submitFeedback = async () => {
  try {
    const payload = { ...feedbackForm.value, alarm_id: currentFeedbackAlarmId.value };
    await fetch('http://127.0.0.1:5000/api/ext/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    showFeedbackModal.value = false;
    alert('感谢您的反馈，该数据将用于下一轮模型训练优化！');
    loadAlarms(); // 刷新列表
  } catch (err) {
    console.error("提交反馈失败:", err);
    alert('提交失败，请检查网络');
  }
};

const config = ref({'''
content = content.replace(old_script, new_script)

with io.open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched successfully!')