<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { ElMessage } from 'element-plus';
import type { McpServer, McpServerPayload, McpTransport } from '../../api/mcp';

interface FormState {
  name: string;
  transport: McpTransport;
  ip: string;
  key: string;
  command: string;
  argsText: string;
  cwd: string;
  envText: string;
  autostart: boolean;
  connectAfterSave: boolean;
  reconnectAfterSave: boolean;
}

const props = defineProps<{
  visible: boolean;
  server: McpServer | null;
  saving: boolean;
}>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
  save: [payload: McpServerPayload];
}>();

const form = reactive<FormState>({
  name: '',
  transport: 'sse',
  ip: '',
  key: '',
  command: '',
  argsText: '',
  cwd: '',
  envText: '{}',
  autostart: false,
  connectAfterSave: false,
  reconnectAfterSave: false,
});

const isEdit = computed(() => Boolean(props.server));
const dialogTitle = computed(() => (isEdit.value ? '编辑 MCP Server' : '添加 MCP Server'));

function resetForm() {
  const server = props.server;
  form.name = server?.name || '';
  form.transport = server?.transport === 'stdio' ? 'stdio' : 'sse';
  form.ip = server?.ip || '';
  form.key = server?.key || '';
  form.command = server?.command || '';
  form.argsText = Array.isArray(server?.args) ? server.args.join(' ') : '';
  form.cwd = server?.cwd || '';
  form.envText = JSON.stringify(server?.env || {}, null, 2);
  form.autostart = Boolean(server?.autostart);
  form.connectAfterSave = !server;
  form.reconnectAfterSave = Boolean(server);
}

function parseArgs() {
  return form.argsText.split(/\s+/).map((item) => item.trim()).filter(Boolean);
}

function parseEnv() {
  const raw = form.envText.trim();
  if (!raw) return {};
  const parsed = JSON.parse(raw);
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
    throw new Error('环境变量必须是 JSON 对象');
  }
  return parsed as Record<string, string>;
}

function buildPayload(): McpServerPayload | null {
  if (!form.name.trim()) {
    ElMessage.warning('请输入 server 名称');
    return null;
  }
  if (form.transport === 'sse' && !form.ip.trim()) {
    ElMessage.warning('请输入 SSE 地址');
    return null;
  }
  if (form.transport === 'stdio' && !form.command.trim()) {
    ElMessage.warning('请输入 stdio 启动命令');
    return null;
  }
  try {
    const payload: McpServerPayload = {
      name: form.name.trim(),
      transport: form.transport,
      autostart: form.autostart,
      auto_connect: !isEdit.value && form.connectAfterSave,
      auto_reconnect: isEdit.value && form.reconnectAfterSave,
    };
    if (form.transport === 'stdio') {
      payload.command = form.command.trim();
      payload.args = parseArgs();
      payload.cwd = form.cwd.trim();
      payload.env = parseEnv();
    } else {
      payload.ip = form.ip.trim();
      payload.key = form.key.trim();
    }
    return payload;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '环境变量 JSON 无效');
    return null;
  }
}

function closeDialog() {
  emit('update:visible', false);
}

function submit() {
  const payload = buildPayload();
  if (payload) emit('save', payload);
}

watch(() => props.visible, (visible) => {
  if (visible) resetForm();
});

watch(() => props.server, () => {
  if (props.visible) resetForm();
});
</script>

<template>
  <el-dialog :model-value="visible" :title="dialogTitle" width="620px" destroy-on-close @update:model-value="emit('update:visible', $event)">
    <el-form label-position="top" class="mcp-dialog-form">
      <el-form-item label="名称">
        <el-input v-model="form.name" placeholder="例如：yueshen rag" />
      </el-form-item>

      <el-form-item label="传输方式">
        <el-radio-group v-model="form.transport">
          <el-radio-button label="sse">SSE</el-radio-button>
          <el-radio-button label="stdio">stdio</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <template v-if="form.transport === 'sse'">
        <el-form-item label="SSE 地址">
          <el-input v-model="form.ip" placeholder="http://127.0.0.1:8000/sse" />
        </el-form-item>
        <el-form-item label="Key">
          <el-input v-model="form.key" placeholder="可选" show-password />
        </el-form-item>
      </template>

      <template v-else>
        <el-form-item label="启动命令">
          <el-input v-model="form.command" placeholder="python" />
        </el-form-item>
        <el-form-item label="参数">
          <el-input v-model="form.argsText" placeholder="mcp_servers/yueshen_rag/server.py" />
        </el-form-item>
        <el-form-item label="工作目录">
          <el-input v-model="form.cwd" placeholder="可选" />
        </el-form-item>
        <el-form-item label="环境变量 JSON">
          <el-input v-model="form.envText" type="textarea" :rows="4" placeholder='{"KEY":"VALUE"}' />
        </el-form-item>
      </template>

      <div class="mcp-dialog-switches">
        <el-checkbox v-model="form.autostart">启动 MCP 服务时自动连接</el-checkbox>
        <el-checkbox v-if="!isEdit" v-model="form.connectAfterSave">保存后立即连接</el-checkbox>
        <el-checkbox v-else v-model="form.reconnectAfterSave">保存后重新连接</el-checkbox>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="closeDialog">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>
