import { computed, type Ref, ref } from 'vue';
import { ElMessage } from 'element-plus';
import {
  createRecommendationStop,
  type RecommendationAttraction,
  type RecommendationStop,
  type RecommendationTemplate,
} from '../api/recommendation';

interface WorkbenchState {
  attractions: Ref<RecommendationAttraction[]>;
  selectedTemplateId: Ref<number | null>;
  stopForm: RecommendationStop;
  stops: Ref<RecommendationStop[]>;
  templates: Ref<RecommendationTemplate[]>;
}

interface WorkbenchLoaders {
  loadStops: () => Promise<void>;
}

export function createRecommendationWorkbench(state: WorkbenchState, loaders: WorkbenchLoaders) {
  const selectedStopId = ref<number | null>(null);
  const selectedTemplate = computed(() => state.templates.value.find((item) => item.id === state.selectedTemplateId.value));
  const orderedStops = computed(() => [...state.stops.value].sort(stopSorter));
  const routeTotalMinutes = computed(() => orderedStops.value.reduce((sum, item) => sum + Number(item.stay_minutes || 0), 0));

  function attractionName(attractionId?: number) {
    return state.attractions.value.find((item) => item.id === attractionId)?.name || '未选择景点';
  }

  function routeStopName(stop: RecommendationStop) {
    return stop.node_name || attractionName(stop.attraction_id);
  }

  function handleSelectWorkbenchStop(stop: RecommendationStop) {
    selectedStopId.value = stop.id || null;
    Object.assign(state.stopForm, { ...stop });
  }

  function handleNewStopDraft() {
    selectedStopId.value = null;
    Object.assign(state.stopForm, {
      attraction_id: 0,
      enabled: true,
      id: undefined,
      order_index: nextOrderIndex(orderedStops.value),
      stay_minutes: 30,
      template_id: state.selectedTemplateId.value || undefined,
    });
  }

  async function handleMoveStop(stop: RecommendationStop, direction: -1 | 1) {
    const templateId = state.selectedTemplateId.value;
    const ordered = orderedStops.value;
    const index = ordered.findIndex((item) => item.id === stop.id);
    const target = ordered[index + direction];
    if (!templateId || index < 0 || !target?.id || !stop.id) return;
    await Promise.all([
      createRecommendationStop(templateId, { ...stop, order_index: target.order_index }),
      createRecommendationStop(templateId, { ...target, order_index: stop.order_index }),
    ]);
    ElMessage.success('路线顺序已更新');
    await loaders.loadStops();
    selectedStopId.value = stop.id;
  }

  return {
    handleMoveStop,
    handleNewStopDraft,
    handleSelectWorkbenchStop,
    orderedStops,
    routeStopName,
    routeTotalMinutes,
    selectedStopId,
    selectedTemplate,
  };
}

function stopSorter(left: RecommendationStop, right: RecommendationStop) {
  return (left.order_index || 0) - (right.order_index || 0) || (left.id || 0) - (right.id || 0);
}

function nextOrderIndex(stops: RecommendationStop[]) {
  return stops.reduce((max, item) => Math.max(max, item.order_index || 0), 0) + 1;
}
