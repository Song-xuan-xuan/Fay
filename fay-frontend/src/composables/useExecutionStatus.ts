import { onBeforeUnmount, ref, watch, type Ref } from 'vue';
import { getExecutionStatus } from '../api/message';
import type { ExecutionStatus } from '../types';

const EXECUTION_REFRESH_MS = 3000;

export function useExecutionStatus(username: Ref<string>) {
  const execution = ref<ExecutionStatus>({ status: 'idle' });
  let timer: number | null = null;

  async function refreshExecution() {
    execution.value = await getExecutionStatus(username.value);
  }

  function startExecutionPolling() {
    refreshExecution().catch(() => undefined);
    timer = window.setInterval(() => refreshExecution().catch(() => undefined), EXECUTION_REFRESH_MS);
  }

  onBeforeUnmount(() => {
    if (timer !== null) {
      window.clearInterval(timer);
    }
  });

  watch(username, () => {
    refreshExecution().catch(() => undefined);
  });

  return {
    execution,
    startExecutionPolling,
  };
}
