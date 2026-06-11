<script setup lang="ts">
import { Database, Download, Pencil, Plus, RefreshCw, Settings, Trash2, Upload } from '@lucide/vue';
import { useRecommendationManage } from '../composables/useRecommendationManage';

const {
  activeTab, attractionForm, attractionOptions, attractions, edgeForm, edges, fileInput, handleAttractionFile,
  handleCreateAttraction, handleCreateMaterial, handleCreateStop, handleCreateTemplate,
  handleCreateEdge, handleDeleteAttraction, handleDeleteEdge, handleDeleteMaterial, handleDeleteStop,
  handleDeleteTemplate, handleEditAttraction, handleEditEdge, handleEditMaterial, handleEditStop,
  handleEditTemplate, handleExportAll, handleExportAttractions, handleImportAll, handleInitialize, handleSelectTemplate,
  handleWeights, importText, loadAll, loadStops, loading, logs, materialForm,
  materials, selectedTemplateId, stopForm, stops, templateForm, templateOptions,
  templates, weightForm,
} = useRecommendationManage();
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

    <el-tabs v-model="activeTab" class="dashboard-tabs">
      <el-tab-pane label="景点" name="attractions">
        <div class="split-grid">
          <section class="chart-panel">
            <h3>新增景点</h3>
            <el-form label-position="top">
              <el-form-item label="名称"><el-input v-model="attractionForm.name" /></el-form-item>
              <el-form-item label="分类"><el-input v-model="attractionForm.category" /></el-form-item>
              <el-form-item label="标签"><el-select v-model="attractionForm.tags" multiple allow-create filterable /></el-form-item>
              <div class="recommendation-form-grid">
                <el-form-item label="停留分钟"><el-input-number v-model="attractionForm.visit_minutes" :min="5" /></el-form-item>
                <el-form-item label="难度"><el-input-number v-model="attractionForm.difficulty" :min="1" :max="5" /></el-form-item>
              </div>
              <el-form-item label="简介"><el-input v-model="attractionForm.summary" type="textarea" :rows="3" /></el-form-item>
              <el-checkbox v-model="attractionForm.indoor">室内点位</el-checkbox>
              <el-checkbox v-model="attractionForm.enabled">启用</el-checkbox>
              <div class="form-actions"><el-button type="primary" :icon="Plus" @click="handleCreateAttraction">保存景点</el-button></div>
            </el-form>
          </section>
          <section class="chart-panel">
            <h3>景点列表</h3>
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

      <el-tab-pane label="路线" name="routes">
        <div class="split-grid">
          <section class="chart-panel">
            <h3>路线模板</h3>
            <el-form label-position="top">
              <el-form-item label="名称"><el-input v-model="templateForm.name" /></el-form-item>
              <el-form-item label="兴趣标签"><el-select v-model="templateForm.interest_tags" multiple allow-create filterable /></el-form-item>
              <div class="recommendation-form-grid">
                <el-form-item label="时长"><el-input-number v-model="templateForm.duration_minutes" :min="30" :step="15" /></el-form-item>
                <el-form-item label="强度"><el-select v-model="templateForm.intensity"><el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /></el-select></el-form-item>
              </div>
              <el-form-item label="摘要"><el-input v-model="templateForm.summary" type="textarea" :rows="3" /></el-form-item>
              <el-button type="primary" :icon="Plus" @click="handleCreateTemplate">保存模板</el-button>
            </el-form>
            <el-table :data="templates" height="220" @row-click="handleSelectTemplate">
              <el-table-column prop="name" label="模板" />
              <el-table-column label="兴趣"><template #default="{ row }">{{ (row.interest_tags || []).join(', ') }}</template></el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button text :icon="Pencil" @click.stop="handleEditTemplate(row)" />
                  <el-button text type="danger" :icon="Trash2" @click.stop="handleDeleteTemplate(row)" />
                </template>
              </el-table-column>
            </el-table>
          </section>
          <section class="chart-panel">
            <h3>停靠点</h3>
            <el-select v-model="selectedTemplateId" class="manage-select" @change="loadStops">
              <el-option v-for="item in templateOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <div class="recommendation-form-grid">
              <el-select v-model="stopForm.attraction_id"><el-option v-for="item in attractionOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select>
              <el-input-number v-model="stopForm.order_index" :min="1" />
              <el-input-number v-model="stopForm.stay_minutes" :min="5" />
              <el-button type="primary" :icon="Plus" @click="handleCreateStop">添加停靠点</el-button>
            </div>
            <el-table :data="stops" height="420">
              <el-table-column prop="order_index" label="序" width="70" />
              <el-table-column label="景点"><template #default="{ row }">{{ attractions.find((item) => item.id === row.attraction_id)?.name || row.attraction_id }}</template></el-table-column>
              <el-table-column prop="stay_minutes" label="停留" width="90" />
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button text :icon="Pencil" @click="handleEditStop(row)" />
                  <el-button text type="danger" :icon="Trash2" @click="handleDeleteStop(row)" />
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
        <section class="chart-panel route-edge-panel">
          <h3>步行边</h3>
          <div class="recommendation-form-grid">
            <el-select v-model="edgeForm.from_attraction_id" placeholder="起点">
              <el-option v-for="item in attractionOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="edgeForm.to_attraction_id" placeholder="终点">
              <el-option v-for="item in attractionOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-input-number v-model="edgeForm.walk_minutes" :min="0" />
            <el-input-number v-model="edgeForm.distance_meters" :min="0" />
            <el-input-number v-model="edgeForm.difficulty" :min="1" :max="5" />
            <el-checkbox v-model="edgeForm.bidirectional">双向</el-checkbox>
            <el-checkbox v-model="edgeForm.enabled">启用</el-checkbox>
            <el-button type="primary" :icon="Plus" @click="handleCreateEdge">保存步行边</el-button>
          </div>
          <el-table :data="edges" height="260">
            <el-table-column label="起点"><template #default="{ row }">{{ attractions.find((item) => item.id === row.from_attraction_id)?.name || row.from_attraction_id }}</template></el-table-column>
            <el-table-column label="终点"><template #default="{ row }">{{ attractions.find((item) => item.id === row.to_attraction_id)?.name || row.to_attraction_id }}</template></el-table-column>
            <el-table-column prop="walk_minutes" label="步行" width="90" />
            <el-table-column prop="distance_meters" label="距离" width="90" />
            <el-table-column prop="bidirectional" label="双向" width="80" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button text :icon="Pencil" @click="handleEditEdge(row)" />
                <el-button text type="danger" :icon="Trash2" @click="handleDeleteEdge(row)" />
              </template>
            </el-table-column>
          </el-table>
        </section>
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
            <h3>权重配置</h3>
            <div class="weight-grid">
              <label v-for="(_, key) in weightForm" :key="key"><span>{{ key }}</span><el-input-number v-model="weightForm[key]" :min="0" :max="1" :step="0.05" /></label>
            </div>
            <el-button type="primary" :icon="Settings" @click="handleWeights">保存权重</el-button>
          </section>
          <section class="chart-panel">
            <h3>导入导出</h3>
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
  </section>
</template>
