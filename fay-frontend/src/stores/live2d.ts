import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getLive2dUrl } from '../api/live';

export const useLive2dStore = defineStore('live2d', () => {
  const iframeUrl = ref(getLive2dUrl());
  const lastCommand = ref('');

  function updateUrl(url: string) {
    iframeUrl.value = url.trim() || getLive2dUrl();
  }

  function rememberCommand(command: string) {
    lastCommand.value = command;
  }

  return {
    iframeUrl,
    lastCommand,
    updateUrl,
    rememberCommand,
  };
});
