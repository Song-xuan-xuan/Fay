import type { ComputedRef, Ref } from 'vue';
import { ElMessage } from 'element-plus';
import { sendMessage as sendMessageApi } from '../api/message';

const MESSAGE_REFRESH_DELAY_MS = 500;
const ERROR_PREVIEW_LENGTH = 100;

type MultimodalContentItem =
  | { type: 'text'; text: string }
  | { type: 'image_url'; image_url: { url: string } };

interface UploadResponse {
  result?: string;
  url?: string;
  message?: string;
}

interface MessageSubmitOptions {
  selectedUsername: ComputedRef<string>;
  newMessage: Ref<string>;
  pendingImages: Ref<File[]>;
  getLiveState: () => number;
  clearComposerImages: () => void;
  reloadMessages: () => void;
}

interface SubmitPrecheckOptions {
  files: File[];
  username: string;
  msg: string;
  liveState: number;
}

function buildMultimodalContent(msg: string, imageUrls: string[]): MultimodalContentItem[] {
  const content: MultimodalContentItem[] = msg ? [{ type: 'text', text: msg }] : [];
  for (const url of imageUrls) {
    content.push({ type: 'image_url', image_url: { url } });
  }
  return content;
}

async function uploadImage(file: File, username: string): Promise<string> {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('username', username);

  const response = await fetch('/api/upload-image', { method: 'POST', body: formData });
  const result = await response.json() as UploadResponse;
  if (result.result === 'successful' && result.url) {
    return result.url;
  }
  throw new Error(result.message || '上传失败');
}

async function uploadPendingImages(files: File[], username: string): Promise<string[] | null> {
  if (files.length === 0) {
    return [];
  }
  try {
    const imageUrls = await Promise.all(files.map((file) => uploadImage(file, username)));
    ElMessage.success(`成功上传 ${imageUrls.length} 张图片`);
    return imageUrls;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '图片上传失败');
    return null;
  }
}

async function sendMultimodalMessage(username: string, msg: string, imageUrls: string[]): Promise<void> {
  const response = await fetch('/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'fay',
      messages: [{ role: 'user', content: buildMultimodalContent(msg, imageUrls) }],
      user: username,
      stream: false,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Send message failed:', errorText);
    throw new Error(`HTTP ${response.status}: ${errorText.substring(0, ERROR_PREVIEW_LENGTH)}`);
  }
}

export function useMessageSubmit(options: MessageSubmitOptions) {
  async function submitMessage() {
    const msg = options.newMessage.value.trim();
    const username = options.selectedUsername.value;
    const imageUrls = await validateAndUpload({
      files: options.pendingImages.value,
      username,
      msg,
      liveState: options.getLiveState(),
    });
    if (!imageUrls) {
      return;
    }

    options.newMessage.value = '';
    options.clearComposerImages();

    try {
      if (imageUrls.length > 0) {
        await sendMultimodalMessage(username, msg, imageUrls);
        setTimeout(options.reloadMessages, MESSAGE_REFRESH_DELAY_MS);
        return;
      }
      await sendMessageApi(username, msg);
    } catch (error) {
      console.error('Send message error:', error);
      ElMessage.error(error instanceof Error ? error.message : '发送消息失败');
    }
  }

  return { submitMessage };
}

async function validateAndUpload(options: SubmitPrecheckOptions) {
  if (!options.msg && options.files.length === 0) {
    return null;
  }
  if (options.liveState !== 1) {
    ElMessage.warning('请先开启 Fay 服务');
    return null;
  }
  return uploadPendingImages(options.files, options.username);
}
