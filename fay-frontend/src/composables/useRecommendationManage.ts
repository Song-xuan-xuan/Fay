import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import {
  createRecommendationAttraction,
  createRecommendationEdge,
  createRecommendationMaterial,
  createRecommendationStop,
  createRecommendationTemplate,
  deleteRecommendationAttraction,
  deleteRecommendationEdge,
  deleteRecommendationMaterial,
  deleteRecommendationStop,
  deleteRecommendationTemplate,
  exportRecommendationAttractions,
  exportRecommendationData,
  getRecommendationConfig,
  importRecommendationAttractionFile,
  importRecommendationData,
  initializeRecommendationAttractions,
  listRecommendationAttractions,
  listRecommendationEdges,
  listRecommendationLogs,
  listRecommendationMaterials,
  listRecommendationStops,
  listRecommendationTemplates,
  updateRecommendationConfig,
  type RecommendationAttraction,
  type RecommendationEdge,
  type RecommendationMaterial,
  type RecommendationStop,
  type RecommendationTemplate,
} from '../api/recommendation';

export function useRecommendationManage() {
  const state = createManageState();
  const loaders = createLoaders(state);
  const editors = createEditors(state, loaders);
  const creators = createCreators(state, loaders);
  const removers = createRemovers(state, loaders);
  const transfers = createTransfers(state, loaders);
  onMounted(loaders.loadAll);
  return { ...state, ...loaders, ...editors, ...creators, ...removers, ...transfers };
}

function createManageState() {
  const attractions = ref<RecommendationAttraction[]>([]);
  const templates = ref<RecommendationTemplate[]>([]);
  return {
    activeTab: ref('attractions'),
    attractionForm: reactive<RecommendationAttraction>(emptyAttraction()),
    attractionOptions: computed(() => attractions.value.map((item) => ({ label: item.name, value: item.id || 0 }))),
    attractions,
    edgeForm: reactive<RecommendationEdge>(emptyEdge()),
    edges: ref<RecommendationEdge[]>([]),
    fileInput: ref<HTMLInputElement | null>(null),
    importText: ref(''),
    loading: ref(false),
    logs: ref<Array<Record<string, any>>>([]),
    materialForm: reactive<RecommendationMaterial>({ attraction_id: 0, interest_tag: '', title: '', focus: '', script: '' }),
    materials: ref<RecommendationMaterial[]>([]),
    selectedTemplateId: ref<number | null>(null),
    stopForm: reactive<RecommendationStop>({ attraction_id: 0, order_index: 1, stay_minutes: 30 }),
    stops: ref<RecommendationStop[]>([]),
    templateForm: reactive<RecommendationTemplate>(emptyTemplate()),
    templateOptions: computed(() => templates.value.map((item) => ({ label: item.name, value: item.id || 0 }))),
    templates,
    weightForm: reactive({ interest_match: 0.45, satisfaction: 0.2, popularity: 0.15, time_fit: 0.1, intensity_fit: 0.1 }),
  };
}

type ManageState = ReturnType<typeof createManageState>;
type Loaders = ReturnType<typeof createLoaders>;

function createLoaders(state: ManageState) {
  async function loadAll() {
    state.loading.value = true;
    try {
      const [attractionResult, templateResult, materialResult, edgeResult, logResult, configResult] = await Promise.all([
        listRecommendationAttractions(),
        listRecommendationTemplates(),
        listRecommendationMaterials(),
        listRecommendationEdges(),
        listRecommendationLogs(30),
        getRecommendationConfig(),
      ]);
      state.attractions.value = attractionResult.items || [];
      state.templates.value = templateResult.items || [];
      state.materials.value = materialResult.items || [];
      state.edges.value = edgeResult.items || [];
      state.logs.value = logResult.items || [];
      Object.assign(state.weightForm, (configResult.config.weights || {}) as Record<string, number>);
      if (!state.selectedTemplateId.value && state.templates.value[0]?.id) state.selectedTemplateId.value = state.templates.value[0].id;
      await loadStops();
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '加载推荐配置失败');
    } finally {
      state.loading.value = false;
    }
  }

  async function loadStops() {
    if (!state.selectedTemplateId.value) {
      state.stops.value = [];
      return;
    }
    const result = await listRecommendationStops(state.selectedTemplateId.value);
    state.stops.value = result.items || [];
  }

  return { loadAll, loadStops };
}

function createEditors(state: ManageState, loaders: Loaders) {
  function handleEditAttraction(row: RecommendationAttraction) {
    Object.assign(state.attractionForm, { ...row, tags: [...(row.tags || [])] });
  }

  async function handleEditTemplate(row: RecommendationTemplate) {
    Object.assign(state.templateForm, { ...row, interest_tags: [...(row.interest_tags || [])] });
    if (row.id) state.selectedTemplateId.value = row.id;
    await loaders.loadStops();
  }

  function handleEditStop(row: RecommendationStop) {
    Object.assign(state.stopForm, { ...row });
    if (row.template_id) state.selectedTemplateId.value = row.template_id;
  }

  function handleEditEdge(row: RecommendationEdge) {
    Object.assign(state.edgeForm, { ...row });
  }

  function handleEditMaterial(row: RecommendationMaterial) {
    Object.assign(state.materialForm, { ...row });
  }

  return { handleEditAttraction, handleEditTemplate, handleEditStop, handleEditEdge, handleEditMaterial };
}

function createCreators(state: ManageState, loaders: Loaders) {
  async function handleCreateAttraction() {
    await createRecommendationAttraction({ ...state.attractionForm, tags: [...(state.attractionForm.tags || [])] });
    Object.assign(state.attractionForm, emptyAttraction());
    ElMessage.success('景点已保存');
    await loaders.loadAll();
  }

  async function handleCreateTemplate() {
    await createRecommendationTemplate({ ...state.templateForm, interest_tags: [...(state.templateForm.interest_tags || [])] });
    Object.assign(state.templateForm, emptyTemplate());
    ElMessage.success('路线模板已保存');
    await loaders.loadAll();
  }

  async function handleSelectTemplate(row: RecommendationTemplate) {
    if (!row.id) return;
    state.selectedTemplateId.value = row.id;
    await loaders.loadStops();
  }

  async function handleCreateStop() {
    if (!state.selectedTemplateId.value) return;
    await createRecommendationStop(state.selectedTemplateId.value, { ...state.stopForm });
    Object.assign(state.stopForm, { attraction_id: 0, order_index: 1, stay_minutes: 30, id: undefined });
    ElMessage.success('停靠点已保存');
    await loaders.loadStops();
  }

  async function handleCreateEdge() {
    await createRecommendationEdge({ ...state.edgeForm });
    Object.assign(state.edgeForm, emptyEdge());
    ElMessage.success('步行边已保存');
    await loaders.loadAll();
  }

  async function handleCreateMaterial() {
    await createRecommendationMaterial({ ...state.materialForm });
    Object.assign(state.materialForm, { attraction_id: 0, interest_tag: '', title: '', focus: '', script: '' });
    ElMessage.success('讲解素材已保存');
    await loaders.loadAll();
  }

  return { handleCreateAttraction, handleCreateTemplate, handleSelectTemplate, handleCreateStop, handleCreateEdge, handleCreateMaterial };
}

function createRemovers(state: ManageState, loaders: Loaders) {
  async function handleDeleteAttraction(row: RecommendationAttraction) {
    if (!row.id) return;
    await deleteRecommendationAttraction(row.id);
    await loaders.loadAll();
  }

  async function handleDeleteStop(row: RecommendationStop) {
    if (!row.id) return;
    await deleteRecommendationStop(row.id);
    await loaders.loadStops();
  }

  async function handleDeleteTemplate(row: RecommendationTemplate) {
    if (!row.id) return;
    await deleteRecommendationTemplate(row.id);
    await loaders.loadAll();
  }

  async function handleDeleteEdge(row: RecommendationEdge) {
    if (!row.id) return;
    await deleteRecommendationEdge(row.id);
    await loaders.loadAll();
  }

  async function handleDeleteMaterial(row: RecommendationMaterial) {
    if (!row.id) return;
    await deleteRecommendationMaterial(row.id);
    await loaders.loadAll();
  }

  return { handleDeleteAttraction, handleDeleteStop, handleDeleteTemplate, handleDeleteEdge, handleDeleteMaterial };
}

function createTransfers(state: ManageState, loaders: Loaders) {
  async function handleWeights() {
    await updateRecommendationConfig({ weights: { ...state.weightForm } });
    ElMessage.success('推荐权重已更新');
  }

  async function handleInitialize() {
    const result = await initializeRecommendationAttractions(100);
    ElMessage.success(`已生成 ${result.created || 0} 个景点草稿`);
    await loaders.loadAll();
  }

  async function handleExportAll() {
    const data = await exportRecommendationData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
    downloadBlob(blob, 'tourism-recommendation.json');
  }

  async function handleImportAll() {
    const result = await importRecommendationData(JSON.parse(state.importText.value || '{}'));
    ElMessage.success(`导入完成：${JSON.stringify(result.created || {})}`);
    await loaders.loadAll();
  }

  async function handleAttractionFile(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    const result = await importRecommendationAttractionFile(file);
    ElMessage.success(`已导入 ${result.created || 0} 条景点`);
    await loaders.loadAll();
    if (state.fileInput.value) state.fileInput.value.value = '';
  }

  async function handleExportAttractions(format: 'csv' | 'xlsx') {
    downloadBlob(await exportRecommendationAttractions(format), `recommendation_attractions.${format}`);
  }

  return { handleWeights, handleInitialize, handleExportAll, handleImportAll, handleAttractionFile, handleExportAttractions };
}

function downloadBlob(blob: Blob, filename: string) {
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function emptyAttraction(): RecommendationAttraction {
  return { name: '', category: '', summary: '', tags: [], visit_minutes: 30, difficulty: 1, indoor: false, enabled: true };
}

function emptyTemplate(): RecommendationTemplate {
  return { name: '', summary: '', interest_tags: [], duration_minutes: 120, intensity: 'medium', enabled: true };
}

function emptyEdge(): RecommendationEdge {
  return { from_attraction_id: 0, to_attraction_id: 0, walk_minutes: 5, distance_meters: 0, difficulty: 1, bidirectional: true, enabled: true };
}
