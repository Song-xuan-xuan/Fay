<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { ref } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { Clipboard, Database, Download, HelpCircle, Pencil, Plus, RefreshCw, Route as RouteIcon, Settings, Trash2, Upload } from '@lucide/vue';
import RouteWorkbench from '../components/recommendation/RouteWorkbench.vue';
import { exampleImportJson } from '../config/recommendationImportExample';
import { useRecommendationManage } from '../composables/useRecommendationManage';

const route = useRoute();
const {
  activeTab, attractionForm, attractionOptions, attractions, edgeForm, edges, fileInput, handleAttractionFile,
  handleCreateAttraction, handleCreateMaterial, handleCreateStop, handleCreateTemplate,
  handleCreateEdge, handleDeleteAttraction, handleDeleteEdge, handleDeleteMaterial, handleDeleteStop,
  handleDeleteTemplate, handleEditAttraction, handleEditEdge, handleEditMaterial,
  handleEditTemplate, handleExportAll, handleExportAttractions, handleImportAll, handleInitialize,
  handleMoveStop, handleNewStopDraft, handleSelectTemplate, handleSelectTemplateId, handleSelectWorkbenchStop,
  handleWeights, importText, loadAll, loading, logs, materialForm,
  materials, selectedTemplateId, stopForm, stops, templateForm, templateOptions,
  orderedStops, routeStopName, routeTotalMinutes, selectedStopId, selectedTemplate, templates, weightForm,
} = useRecommendationManage();

const importTutorialVisible = ref(false);

function isRecommendationPageActive(path: string) {
  if (path === '/app/recommendation') {
    return route.path === path;
  }
  return route.path === path || route.path.startsWith(`${path}/`);
}

async function handleCopyExampleJson() {
  try {
    await navigator.clipboard.writeText(exampleImportJson);
    ElMessage.success('示例 JSON 已复制');
  } catch (error) {
    ElMessage.error('复制失败，请手动选择示例 JSON');
  }
}
</script>

<template>
  <section class="recommendation-page" v-loading="loading">
    <div class="dashboard-title-row">
      <div>
        <h2>推荐数据维护</h2>
        <p>维护景点、路线、讲解素材、推荐权重与导入导出。</p>
      </div>
      <div class="dashboard-actions">
        <el-button :icon="RefreshCw" :loading="loading" @click="loadAll">刷新</el-button>
        <el-button :icon="Database" @click="handleInitialize">从看板初始化</el-button>
      </div>
    </div>

    <nav class="recommendation-page-tabs" aria-label="推荐功能导航">
      <RouterLink
        to="/app/recommendation"
        class="recommendation-page-tab"
        :class="{ 'is-active': isRecommendationPageActive('/app/recommendation') }"
      >
        <RouteIcon :size="16" aria-hidden="true" />
        <span>路线推荐</span>
      </RouterLink>
      <RouterLink
        to="/app/recommendation/manage"
        class="recommendation-page-tab"
        :class="{ 'is-active': isRecommendationPageActive('/app/recommendation/manage') }"
      >
        <Settings :size="16" aria-hidden="true" />
        <span>维护推荐</span>
      </RouterLink>
    </nav>

    <el-tabs v-model="activeTab" class="dashboard-tabs">
      <el-tab-pane label="景点资料库" name="attractions">
        <div class="split-grid">
          <section class="chart-panel">
            <h3>景点资料库</h3>
            <el-form label-position="top">
              <el-form-item label="名称"><el-input v-model="attractionForm.name" /></el-form-item>
              <el-form-item label="分类"><el-input v-model="attractionForm.category" /></el-form-item>
              <el-form-item label="标签"><el-select v-model="attractionForm.tags" multiple allow-create filterable /></el-form-item>
              <div class="recommendation-form-grid">
                <el-form-item label="停留分钟"><el-input-number v-model="attractionForm.visit_minutes" :min="5" /></el-form-item>
                <el-form-item label="状态"><el-checkbox v-model="attractionForm.enabled">启用推荐</el-checkbox></el-form-item>
              </div>
              <el-form-item label="简介"><el-input v-model="attractionForm.summary" type="textarea" :rows="3" /></el-form-item>
              <el-collapse class="maintenance-advanced">
                <el-collapse-item title="高级信息" name="attraction-advanced">
                  <div class="recommendation-form-grid">
                    <el-form-item label="游览难度"><el-input-number v-model="attractionForm.difficulty" :min="1" :max="5" /></el-form-item>
                    <el-form-item label="点位环境"><el-checkbox v-model="attractionForm.indoor">室内点位</el-checkbox></el-form-item>
                  </div>
                </el-collapse-item>
              </el-collapse>
              <div class="form-actions"><el-button type="primary" :icon="Plus" @click="handleCreateAttraction">保存景点</el-button></div>
            </el-form>
          </section>
          <section class="chart-panel">
            <h3>资料列表</h3>
            <el-table :data="attractions" height="420">
              <el-table-column prop="name" label="名称" min-width="150" />
              <el-table-column prop="category" label="分类" width="120" />
              <el-table-column label="标签" min-width="160"><template #default="{ row }">{{ (row.tags || []).join(', ') }}</template></el-table-column>
              <el-table-column prop="enabled" label="启用" width="80" />
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button text :icon="Pencil" @click="handleEditAttraction(row)" />
                  <el-button text type="danger" :icon="Trash2" @click="handleDeleteAttraction(row)" />
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="路线工作台" name="routes">
        <RouteWorkbench
          :attraction-options="attractionOptions"
          :attractions="attractions"
          :edge-form="edgeForm"
          :edges="edges"
          :handle-create-edge="handleCreateEdge"
          :handle-create-stop="handleCreateStop"
          :handle-create-template="handleCreateTemplate"
          :handle-delete-edge="handleDeleteEdge"
          :handle-delete-stop="handleDeleteStop"
          :handle-delete-template="handleDeleteTemplate"
          :handle-edit-edge="handleEditEdge"
          :handle-edit-template="handleEditTemplate"
          :handle-move-stop="handleMoveStop"
          :handle-new-stop-draft="handleNewStopDraft"
          :handle-select-template="handleSelectTemplate"
          :handle-select-template-id="handleSelectTemplateId"
          :handle-select-workbench-stop="handleSelectWorkbenchStop"
          :ordered-stops="orderedStops"
          :route-stop-name="routeStopName"
          :route-total-minutes="routeTotalMinutes"
          :selected-stop-id="selectedStopId"
          :selected-template="selectedTemplate"
          :selected-template-id="selectedTemplateId"
          :stop-form="stopForm"
          :template-form="templateForm"
          :template-options="templateOptions"
          :templates="templates"
        />
      </el-tab-pane>

      <el-tab-pane label="讲解素材" name="materials">
        <section class="chart-panel">
          <div class="recommendation-form-grid">
            <el-select v-model="materialForm.attraction_id"><el-option v-for="item in attractionOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select>
            <el-input v-model="materialForm.interest_tag" placeholder="兴趣标签" />
            <el-input v-model="materialForm.title" placeholder="标题" />
            <el-button type="primary" :icon="Plus" @click="handleCreateMaterial">保存素材</el-button>
          </div>
          <el-input v-model="materialForm.script" type="textarea" :rows="4" placeholder="讲解话术" />
          <el-table :data="materials" height="420">
            <el-table-column prop="title" label="标题" width="160" />
            <el-table-column prop="interest_tag" label="标签" width="120" />
            <el-table-column prop="script" label="话术" min-width="260" show-overflow-tooltip />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button text :icon="Pencil" @click="handleEditMaterial(row)" />
                <el-button text type="danger" :icon="Trash2" @click="handleDeleteMaterial(row)" />
              </template>
            </el-table-column>
          </el-table>
        </section>
      </el-tab-pane>

      <el-tab-pane label="配置与导入" name="config">
        <div class="split-grid">
          <section class="chart-panel">
            <h3>推荐策略</h3>
            <p class="strategy-hint">调整推荐排序的侧重点。数值越高，对最终路线排序的影响越明显。</p>
            <div class="weight-grid">
              <label>
                <span>更重视兴趣匹配</span>
                <el-input-number v-model="weightForm.interest_match" :min="0" :max="1" :step="0.05" />
              </label>
              <label>
                <span>更重视游客满意度</span>
                <el-input-number v-model="weightForm.satisfaction" :min="0" :max="1" :step="0.05" />
              </label>
              <label>
                <span>更重视热门程度</span>
                <el-input-number v-model="weightForm.popularity" :min="0" :max="1" :step="0.05" />
              </label>
              <label>
                <span>更重视时间合适</span>
                <el-input-number v-model="weightForm.time_fit" :min="0" :max="1" :step="0.05" />
              </label>
              <label>
                <span>更重视强度合适</span>
                <el-input-number v-model="weightForm.intensity_fit" :min="0" :max="1" :step="0.05" />
              </label>
            </div>
            <el-button type="primary" :icon="Settings" @click="handleWeights">保存推荐策略</el-button>
          </section>
          <section class="chart-panel">
            <div class="route-head">
              <h3>导入导出</h3>
              <el-button :icon="HelpCircle" @click="importTutorialVisible = true">导入教程</el-button>
            </div>
            <div class="import-actions">
              <el-button :icon="Download" @click="handleExportAll">导出全部 JSON</el-button>
              <el-button :icon="Download" @click="handleExportAttractions('csv')">导出景点 CSV</el-button>
              <el-button :icon="Download" @click="handleExportAttractions('xlsx')">导出景点 XLSX</el-button>
              <el-button :icon="Upload" @click="fileInput?.click()">导入景点文件</el-button>
              <input ref="fileInput" class="hidden-file-input" type="file" accept=".csv,.xlsx" @change="handleAttractionFile" />
            </div>
            <el-input v-model="importText" type="textarea" :rows="8" placeholder="粘贴完整 JSON 数据" />
            <el-button type="primary" :icon="Upload" @click="handleImportAll">导入 JSON</el-button>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="日志" name="logs">
        <section class="chart-panel">
          <el-table :data="logs" height="520">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column label="请求"><template #default="{ row }">{{ row.request?.interests?.join(', ') || '-' }}</template></el-table-column>
            <el-table-column label="主路线"><template #default="{ row }">{{ row.result?.main_route?.name || '-' }}</template></el-table-column>
            <el-table-column label="得分"><template #default="{ row }">{{ Math.round((row.score_breakdown?.total || 0) * 100) }}</template></el-table-column>
          </el-table>
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="importTutorialVisible"
      title="导入教程"
      append-to-body
      class="import-tutorial-dialog"
      width="min(920px, calc(100vw - 32px))"
    >
      <div class="import-tutorial">
        <section class="import-tutorial-hero">
          <div>
            <span>完整包导入</span>
            <p>一个 JSON 可以同时导入景点、路线、停靠点、讲解素材、步行边和推荐权重。</p>
          </div>
          <el-button type="primary" :icon="Clipboard" @click="handleCopyExampleJson">复制示例 JSON</el-button>
        </section>

        <div class="import-tutorial-grid">
          <section class="import-tutorial-card">
            <h4>导入处理逻辑</h4>
            <ol>
              <li>先把完整 JSON 粘贴到文本框，再点击“导入 JSON”。</li>
              <li>系统先写入景点和路线模板，并记录它们的 <code>external_id</code>、<code>id</code>、<code>name</code> 对应关系。</li>
              <li>再导入停靠点、讲解素材和步行边，用这些对应关系把包内引用转换成数据库 ID。</li>
              <li><code>review_status</code> 为 <code>跳过</code> 的行不会导入；<code>enabled</code> 为 <code>false</code> 的行会保留为禁用草稿。</li>
              <li><code>config</code> 会写入推荐配置，例如左侧的权重值。</li>
            </ol>
          </section>

          <section class="import-tutorial-card">
            <h4>关联 ID 规则</h4>
            <p><code>external_id</code> 是导入包内部用来串联数据的稳定编号，不是文件路径，也不会被当作素材路径处理。</p>
            <p>停靠点、素材和步行边优先使用 <code>template_external_id</code>、<code>attraction_external_id</code>、<code>from_attraction_external_id</code>、<code>to_attraction_external_id</code> 来找刚导入的景点或路线。</p>
          </section>
        </div>

        <section class="import-tutorial-card">
          <h4>完整包字段说明</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="attractions">景点基础资料，包括名称、分类、标签、建议停留时间、热度和满意度。</el-descriptions-item>
            <el-descriptions-item label="templates">路线模板，包括路线名称、兴趣标签、预计时长、强度和是否启用。</el-descriptions-item>
            <el-descriptions-item label="stops">路线停靠点，用 <code>template_external_id</code> 和 <code>attraction_external_id</code> 说明某条路线经过哪些景点。</el-descriptions-item>
            <el-descriptions-item label="materials">讲解素材，用 <code>attraction_external_id</code> 关联景点，并按兴趣标签提供讲解话术。</el-descriptions-item>
            <el-descriptions-item label="edges">景点之间的步行边，用 <code>from_attraction_external_id</code> 和 <code>to_attraction_external_id</code> 描述步行时间、距离和难度。</el-descriptions-item>
            <el-descriptions-item label="config">推荐配置，目前主要是 <code>weights</code> 权重。</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="import-tutorial-card">
          <h4>权重说明</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="interest_match">用户兴趣与路线/景点标签的匹配程度。越高，系统越偏向“兴趣对口”的路线。</el-descriptions-item>
            <el-descriptions-item label="satisfaction">路线中景点满意度的平均表现。越高，系统越偏向评价更好的景点。</el-descriptions-item>
            <el-descriptions-item label="popularity">路线中景点热度的平均表现。越高，系统越偏向更热门的景点。</el-descriptions-item>
            <el-descriptions-item label="time_fit">路线总时长和用户时间预算的接近程度。越高，系统越重视“时间刚好”。</el-descriptions-item>
            <el-descriptions-item label="intensity_fit">路线强度和用户体力偏好的接近程度。越高，系统越重视“走起来合适”。</el-descriptions-item>
          </el-descriptions>
          <p>最终得分是各项分值乘以对应权重后相加；某项权重越大，它对排序的影响越明显。</p>
        </section>

        <section class="import-tutorial-card import-example-panel">
          <div class="import-example-head">
            <div>
              <h4>示例 JSON</h4>
              <p>复制后可直接粘贴到“导入 JSON”的文本框中。</p>
            </div>
            <el-button :icon="Clipboard" @click="handleCopyExampleJson">复制示例 JSON</el-button>
          </div>
          <pre class="import-example-code">{{ exampleImportJson }}</pre>
        </section>
      </div>
    </el-dialog>
  </section>
</template>
