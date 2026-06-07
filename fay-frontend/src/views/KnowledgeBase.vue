<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Activity, FileText, RefreshCw, RotateCcw, Search, Trash2, Upload } from '@lucide/vue';
import {
  deleteKnowledgeBaseFile,
  getKnowledgeBaseStats,
  ingestKnowledgeBase,
  listKnowledgeBaseFiles,
  queryKnowledgeBase,
  uploadKnowledgeBaseFiles,
  type KnowledgeBaseFile,
} from '../api/knowledgeBase';

const files = ref<KnowledgeBaseFile[]>([]);
const libraryDir = ref('library');
const selectedFiles = ref<File[]>([]);
const fileInputRef = ref<HTMLInputElement | null>(null);
const loadingFiles = ref(false);
const uploading = ref(false);
const indexingMode = ref<'incremental' | 'reset' | null>(null);
const statsLoading = ref(false);
const querying = ref(false);
const queryText = ref('');
const topK = ref(5);
const resultText = ref('--');

const totalSize = computed(() => files.value.reduce((sum, file) => sum + Number(file.size || 0), 0));
const shortLibraryDir = computed(() => libraryDir.value.replace(/\\/g, '/').split('/').slice(-1)[0] || 'library');
const canUpload = computed(() => selectedFiles.value.length > 0 && !uploading.value);

function formatSize(size: number) {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`;
  if (size >= 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${size} B`;
}

function stringifyResult(value: unknown) {
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2);
}

function setResult(title: string, value: unknown) {
  resultText.value = `${title}\n${stringifyResult(value)}`;
}

async function loadFiles() {
  loadingFiles.value = true;
  try {
    const data = await listKnowledgeBaseFiles();
    libraryDir.value = data.library_dir || libraryDir.value;
    files.value = Array.isArray(data.files) ? data.files : [];
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载文件列表失败');
  } finally {
    loadingFiles.value = false;
  }
}

function triggerFilePicker() {
  fileInputRef.value?.click();
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const nextFiles = Array.from(input.files || []);
  const validFiles = nextFiles.filter((file) => /\.(docx|pdf)$/i.test(file.name));
  if (validFiles.length !== nextFiles.length) {
    ElMessage.warning('仅支持 .docx 和 .pdf 文件');
  }
  selectedFiles.value = validFiles;
}

function clearSelectedFiles() {
  selectedFiles.value = [];
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
}

function removeSelectedFile(index: number) {
  selectedFiles.value = selectedFiles.value.filter((_, itemIndex) => itemIndex !== index);
}

async function uploadFiles() {
  if (!canUpload.value) return;
  uploading.value = true;
  try {
    const result = await uploadKnowledgeBaseFiles(selectedFiles.value);
    setResult('上传结果', result);
    clearSelectedFiles();
    await loadFiles();
    if (result.errors?.length) {
      ElMessage.warning(`已上传 ${result.files.length} 个文档，${result.errors.length} 个失败`);
    } else {
      ElMessage.success('文档已上传');
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '上传失败');
  } finally {
    uploading.value = false;
  }
}

async function removeFile(row: KnowledgeBaseFile) {
  try {
    await ElMessageBox.confirm(`确认删除 ${row.name}？`, '删除文档', { type: 'warning' });
  } catch {
    return;
  }
  try {
    const result = await deleteKnowledgeBaseFile(row.name);
    setResult('删除结果', result);
    await loadFiles();
    ElMessage.success('文档已删除');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除失败');
  }
}

async function runIngest(reset: boolean) {
  if (reset) {
    try {
      await ElMessageBox.confirm('重建索引会先清空现有向量库，再重新导入 library。确认继续？', '重建索引', { type: 'warning' });
    } catch {
      return;
    }
  }
  indexingMode.value = reset ? 'reset' : 'incremental';
  resultText.value = reset ? '正在重建索引...' : '正在增量索引...';
  try {
    const result = await ingestKnowledgeBase(reset);
    setResult(reset ? '重建索引结果' : '增量索引结果', result.result ?? result);
    ElMessage.success(reset ? '重建索引已完成' : '增量索引已完成');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '索引失败');
  } finally {
    indexingMode.value = null;
  }
}

async function loadStats() {
  statsLoading.value = true;
  resultText.value = '正在读取状态...';
  try {
    const result = await getKnowledgeBaseStats();
    if (result.library_dir) libraryDir.value = result.library_dir;
    setResult('知识库状态', result.result ?? result);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '读取状态失败');
  } finally {
    statsLoading.value = false;
  }
}

async function runQuery() {
  const query = queryText.value.trim();
  if (!query) {
    ElMessage.warning('请输入检索问题');
    return;
  }
  querying.value = true;
  resultText.value = '正在检索...';
  try {
    const result = await queryKnowledgeBase(query, topK.value);
    setResult('检索结果', result.result ?? result);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '检索失败');
  } finally {
    querying.value = false;
  }
}

onMounted(loadFiles);
</script>

<template>
  <section class="panel knowledge-panel">
    <div class="panel-header">
      <div>
        <h2>知识库</h2>
        <p>管理 library 文档，并通过 yueshen rag 完成索引和检索。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="RefreshCw" :loading="loadingFiles" @click="loadFiles">刷新</el-button>
        <el-button :icon="Activity" :loading="statsLoading" @click="loadStats">状态</el-button>
      </div>
    </div>

    <div class="knowledge-layout">
      <div class="knowledge-main">
        <section class="kb-section">
          <div class="kb-section-header">
            <div>
              <h3>上传文档</h3>
              <p>目录：{{ shortLibraryDir }}</p>
            </div>
            <el-tag type="info">{{ selectedFiles.length }} 个待上传</el-tag>
          </div>
          <input ref="fileInputRef" class="file-input" type="file" multiple accept=".docx,.pdf" @change="handleFileChange" />
          <div class="upload-actions">
            <el-button :icon="Upload" type="primary" @click="triggerFilePicker">选择文档</el-button>
            <el-button :disabled="!canUpload" :loading="uploading" @click="uploadFiles">上传</el-button>
            <el-button :disabled="selectedFiles.length === 0" @click="clearSelectedFiles">清空</el-button>
          </div>
          <div v-if="selectedFiles.length" class="selected-file-list">
            <el-tag
              v-for="(file, index) in selectedFiles"
              :key="`${file.name}-${index}`"
              closable
              type="info"
              @close="removeSelectedFile(index)"
            >
              {{ file.name }} · {{ formatSize(file.size) }}
            </el-tag>
          </div>
        </section>

        <section class="kb-section file-table-section">
          <div class="kb-section-header">
            <div>
              <h3>library 文件</h3>
              <p>{{ files.length }} 个文档，{{ formatSize(totalSize) }}</p>
            </div>
          </div>
          <el-table :data="files" v-loading="loadingFiles" empty-text="library 中暂无 .docx/.pdf 文档" height="360">
            <el-table-column label="文件名" min-width="260">
              <template #default="{ row }">
                <div class="file-name-cell">
                  <FileText :size="16" aria-hidden="true" />
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="大小" width="120">
              <template #default="{ row }">{{ formatSize(row.size) }}</template>
            </el-table-column>
            <el-table-column label="更新时间" prop="mtime" width="180" />
            <el-table-column label="操作" width="96" align="right">
              <template #default="{ row }">
                <el-button :icon="Trash2" text type="danger" @click="removeFile(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </div>

      <aside class="knowledge-side">
        <section class="kb-section">
          <div class="kb-section-header compact">
            <div>
              <h3>索引</h3>
              <p>需要 yueshen rag MCP 在线。</p>
            </div>
          </div>
          <div class="side-actions">
            <el-button :icon="RefreshCw" :loading="indexingMode === 'incremental'" @click="runIngest(false)">增量索引</el-button>
            <el-button :icon="RotateCcw" plain type="danger" :loading="indexingMode === 'reset'" @click="runIngest(true)">重建索引</el-button>
          </div>
        </section>

        <section class="kb-section">
          <div class="kb-section-header compact">
            <div>
              <h3>检索测试</h3>
              <p>返回最相关的知识片段。</p>
            </div>
          </div>
          <el-input v-model="queryText" type="textarea" :rows="4" placeholder="输入问题" />
          <div class="query-actions">
            <el-input-number v-model="topK" :min="1" :max="20" size="small" controls-position="right" />
            <el-button :icon="Search" type="primary" :loading="querying" @click="runQuery">检索</el-button>
          </div>
        </section>

        <section class="kb-section result-section">
          <div class="kb-section-header compact">
            <div>
              <h3>输出</h3>
              <p>{{ libraryDir }}</p>
            </div>
          </div>
          <pre class="result-box">{{ resultText }}</pre>
        </section>
      </aside>
    </div>
  </section>
</template>
