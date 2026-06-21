<script setup lang="ts">
import { ArrowDown, ArrowUp, Clock, MapPin, Pencil, Plus, Route as RouteIcon, Trash2 } from '@lucide/vue';
import type {
  RecommendationAttraction,
  RecommendationEdge,
  RecommendationStop,
  RecommendationTemplate,
} from '../../api/recommendation';

defineProps<{
  attractionOptions: Array<{ label: string; value: number }>;
  attractions: RecommendationAttraction[];
  edgeForm: RecommendationEdge;
  edges: RecommendationEdge[];
  handleCreateEdge: () => Promise<void>;
  handleCreateStop: () => Promise<void>;
  handleCreateTemplate: () => Promise<void>;
  handleDeleteEdge: (row: RecommendationEdge) => Promise<void>;
  handleDeleteStop: (row: RecommendationStop) => Promise<void>;
  handleDeleteTemplate: (row: RecommendationTemplate) => Promise<void>;
  handleEditEdge: (row: RecommendationEdge) => void;
  handleEditTemplate: (row: RecommendationTemplate) => Promise<void>;
  handleMoveStop: (row: RecommendationStop, direction: -1 | 1) => Promise<void>;
  handleNewStopDraft: () => void;
  handleSelectTemplate: (row: RecommendationTemplate) => Promise<void>;
  handleSelectTemplateId: (templateId: number) => Promise<void>;
  handleSelectWorkbenchStop: (row: RecommendationStop) => void;
  orderedStops: RecommendationStop[];
  routeStopName: (row: RecommendationStop) => string;
  routeTotalMinutes: number;
  selectedStopId: number | null;
  selectedTemplate?: RecommendationTemplate;
  selectedTemplateId: number | null;
  stopForm: RecommendationStop;
  templateForm: RecommendationTemplate;
  templateOptions: Array<{ label: string; value: number }>;
  templates: RecommendationTemplate[];
}>();

function attractionName(items: RecommendationAttraction[], id?: number) {
  return items.find((item) => item.id === id)?.name || id || '-';
}
</script>

<template>
  <div class="route-workbench">
    <section class="chart-panel route-library-panel">
      <div class="route-head">
        <div>
          <h3>路线工作台</h3>
          <p>{{ templates.length }} 条路线</p>
        </div>
        <el-button :icon="Plus" @click="handleNewStopDraft">新节点</el-button>
      </div>

      <el-table
        :data="templates"
        height="260"
        highlight-current-row
        class="route-template-table"
        @row-click="handleSelectTemplate"
      >
        <el-table-column prop="name" label="路线" min-width="150" />
        <el-table-column label="兴趣" min-width="140">
          <template #default="{ row }">{{ (row.interest_tags || []).join(', ') || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            <el-button text :icon="Pencil" @click.stop="handleEditTemplate(row)" />
            <el-button text type="danger" :icon="Trash2" @click.stop="handleDeleteTemplate(row)" />
          </template>
        </el-table-column>
      </el-table>

      <div class="workbench-editor-block">
        <h4>路线资料</h4>
        <el-form label-position="top">
          <el-form-item label="路线名称"><el-input v-model="templateForm.name" /></el-form-item>
          <el-form-item label="适合兴趣">
            <el-select v-model="templateForm.interest_tags" multiple allow-create filterable />
          </el-form-item>
          <div class="recommendation-form-grid">
            <el-form-item label="预计时长">
              <el-input-number v-model="templateForm.duration_minutes" :min="30" :step="15" />
            </el-form-item>
            <el-form-item label="路线强度">
              <el-select v-model="templateForm.intensity">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="摘要"><el-input v-model="templateForm.summary" type="textarea" :rows="2" /></el-form-item>
          <el-button type="primary" :icon="RouteIcon" @click="handleCreateTemplate">保存路线</el-button>
        </el-form>
      </div>
    </section>

    <section class="chart-panel route-timeline-panel">
      <div class="route-head">
        <div>
          <h3>路线时间轴</h3>
          <p>{{ selectedTemplate?.name || '未选择路线' }}</p>
        </div>
        <el-select
          :model-value="selectedTemplateId"
          class="route-picker"
          placeholder="选择路线"
          @change="handleSelectTemplateId"
        >
          <el-option v-for="item in templateOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>

      <div class="route-summary-strip">
        <span><Clock :size="16" />{{ routeTotalMinutes }} 分钟</span>
        <span><MapPin :size="16" />{{ orderedStops.length }} 个节点</span>
      </div>

      <div class="workbench-timeline">
        <button
          v-for="(stop, index) in orderedStops"
          :key="stop.id || `${stop.order_index}-${stop.attraction_id}`"
          class="workbench-stop"
          :class="{ active: selectedStopId === stop.id }"
          type="button"
          @click="handleSelectWorkbenchStop(stop)"
        >
          <span class="timeline-index">{{ index + 1 }}</span>
          <span class="timeline-body">
            <strong>{{ routeStopName(stop) }}</strong>
            <em>{{ stop.stay_minutes || 0 }} 分钟 · 顺序 {{ stop.order_index }}</em>
          </span>
          <span class="timeline-actions">
            <el-button size="small" :icon="ArrowUp" :disabled="index === 0" @click.stop="handleMoveStop(stop, -1)">上移</el-button>
            <el-button
              size="small"
              :icon="ArrowDown"
              :disabled="index === orderedStops.length - 1"
              @click.stop="handleMoveStop(stop, 1)"
            >
              下移
            </el-button>
          </span>
        </button>
        <el-empty v-if="!orderedStops.length" description="暂无路线节点" />
      </div>
    </section>

    <section class="chart-panel route-node-panel">
      <div class="route-head">
        <div>
          <h3>节点详情</h3>
          <p>{{ stopForm.id ? '编辑节点' : '新增节点' }}</p>
        </div>
        <el-button :icon="Plus" @click="handleNewStopDraft">清空</el-button>
      </div>

      <el-form label-position="top">
        <el-form-item label="景点">
          <el-select v-model="stopForm.attraction_id" filterable>
            <el-option label="非景点节点" :value="0" />
            <el-option v-for="item in attractionOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="节点名称"><el-input v-model="stopForm.node_name" /></el-form-item>
        <div class="recommendation-form-grid">
          <el-form-item label="节点类型">
            <el-select v-model="stopForm.node_type">
              <el-option label="景点" value="attraction" />
              <el-option label="入口" value="start" />
              <el-option label="出口" value="end" />
              <el-option label="草稿" value="draft" />
              <el-option label="途经点" value="path" />
            </el-select>
          </el-form-item>
          <el-form-item label="顺序"><el-input-number v-model="stopForm.order_index" :min="1" /></el-form-item>
          <el-form-item label="停留时间"><el-input-number v-model="stopForm.stay_minutes" :min="0" /></el-form-item>
          <el-form-item label="状态"><el-checkbox v-model="stopForm.enabled">启用</el-checkbox></el-form-item>
        </div>
        <el-form-item label="备注"><el-input v-model="stopForm.note" type="textarea" :rows="3" /></el-form-item>
        <div class="form-actions">
          <el-button type="primary" :icon="Plus" @click="handleCreateStop">保存节点</el-button>
          <el-button v-if="stopForm.id" type="danger" :icon="Trash2" @click="handleDeleteStop(stopForm)">删除节点</el-button>
        </div>
      </el-form>
    </section>

    <section class="chart-panel route-advanced-panel">
      <el-collapse>
        <el-collapse-item title="高级配置：步行时间" name="edges">
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
            <el-button type="primary" :icon="Plus" @click="handleCreateEdge">保存步行时间</el-button>
          </div>
          <el-table :data="edges" height="260">
            <el-table-column label="起点">
              <template #default="{ row }">{{ attractionName(attractions, row.from_attraction_id) }}</template>
            </el-table-column>
            <el-table-column label="终点">
              <template #default="{ row }">{{ attractionName(attractions, row.to_attraction_id) }}</template>
            </el-table-column>
            <el-table-column prop="walk_minutes" label="步行" width="90" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button text :icon="Pencil" @click="handleEditEdge(row)" />
                <el-button text type="danger" :icon="Trash2" @click="handleDeleteEdge(row)" />
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </section>
  </div>
</template>
