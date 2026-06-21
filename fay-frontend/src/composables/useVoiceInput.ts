import type { ComputedRef, Ref } from 'vue';
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { BRAND_SERVICE_NAME } from '../config/brand';

const TOKEN_KEY = 'fay_token';
const DEFAULT_AUDIO_MIME = 'audio/webm';
const AUDIO_MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];

interface VoiceInputOptions {
  selectedUsername: ComputedRef<string>;
  selectedSessionId: ComputedRef<number | null>;
  newMessage: Ref<string>;
  getLiveState: () => number;
  submitMessage: () => void | Promise<void>;
}

interface TranscribeResponse {
  success?: boolean;
  text?: string;
  error?: string;
}

function getStoredToken() {
  if (typeof localStorage === 'undefined') {
    return '';
  }
  return localStorage.getItem(TOKEN_KEY) || '';
}

function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function selectAudioMimeType() {
  const recorder = globalThis.MediaRecorder as typeof MediaRecorder & {
    isTypeSupported?: (mimeType: string) => boolean;
  };
  if (!recorder?.isTypeSupported) {
    return '';
  }
  return AUDIO_MIME_CANDIDATES.find((mimeType) => recorder.isTypeSupported?.(mimeType)) || '';
}

function createRecorder(stream: MediaStream) {
  const mimeType = selectAudioMimeType();
  return mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
}

function buildAudioFilename(mimeType: string) {
  if (mimeType.includes('mp4')) {
    return 'voice-input.mp4';
  }
  return 'voice-input.webm';
}

async function readError(response: Response) {
  try {
    const data = await response.json() as TranscribeResponse;
    return data.error || '语音识别失败';
  } catch {
    return await response.text();
  }
}

export function useVoiceInput(options: VoiceInputOptions) {
  const isRecording = ref(false);
  const isTranscribing = ref(false);
  let recorder: MediaRecorder | null = null;
  let mediaStream: MediaStream | null = null;
  let chunks: Blob[] = [];
  let stopTask: Promise<void> | null = null;

  function cleanupStream() {
    mediaStream?.getTracks().forEach((track) => track.stop());
    mediaStream = null;
    recorder = null;
    chunks = [];
  }

  async function transcribeAndSend() {
    isRecording.value = false;
    isTranscribing.value = true;
    try {
      const blob = new Blob(chunks, { type: chunks[0]?.type || DEFAULT_AUDIO_MIME });
      if (blob.size === 0) {
        return;
      }
      const text = await transcribeBlob(blob);
      if (text) {
        options.newMessage.value = text;
        await options.submitMessage();
      }
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '语音识别失败');
    } finally {
      isTranscribing.value = false;
      cleanupStream();
    }
  }

  async function transcribeBlob(blob: Blob) {
    const formData = new FormData();
    formData.append('audio', blob, buildAudioFilename(blob.type));
    formData.append('username', options.selectedUsername.value);
    const sessionId = options.selectedSessionId.value;
    if (sessionId !== null) {
      formData.append('session_id', String(sessionId));
    }

    const response = await fetch('/api/asr/transcribe', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    const result = await response.json() as TranscribeResponse;
    if (!result.success) {
      throw new Error(result.error || '语音识别失败');
    }
    return (result.text || '').trim();
  }

  async function startRecording() {
    if (isRecording.value || isTranscribing.value) {
      return;
    }
    if (options.selectedSessionId.value === null) {
      ElMessage.warning('请先选择会话');
      return;
    }
    if (options.getLiveState() !== 1) {
      ElMessage.warning(`请先开启 ${BRAND_SERVICE_NAME}`);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      ElMessage.error('当前浏览器不支持语音输入');
      return;
    }

    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = createRecorder(mediaStream);
    chunks = [];
    stopTask = new Promise((resolve) => {
      if (!recorder) {
        resolve();
        return;
      }
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      recorder.onstop = () => {
        transcribeAndSend().finally(resolve);
      };
    });
    recorder.start();
    isRecording.value = true;
  }

  async function stopRecording() {
    if (!recorder || recorder.state === 'inactive') {
      return stopTask ?? undefined;
    }
    const task = stopTask;
    recorder.stop();
    await task;
  }

  async function toggleRecording() {
    if (isRecording.value) {
      await stopRecording();
      return;
    }
    await startRecording();
  }

  return {
    isRecording,
    isTranscribing,
    startRecording,
    stopRecording,
    toggleRecording,
  };
}
