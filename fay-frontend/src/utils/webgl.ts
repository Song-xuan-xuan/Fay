export type WebglSupportReason = 'available' | 'context-unavailable' | 'context-error';

export interface WebglSupport {
  supported: boolean;
  reason: WebglSupportReason;
  message: string;
}

type CanvasLike = {
  getContext: (name: string) => unknown;
};

type CanvasFactory = () => CanvasLike;

const WEBGL_CONTEXT_NAMES = ['webgl2', 'webgl', 'experimental-webgl'];

function createBrowserCanvas(): CanvasLike {
  return document.createElement('canvas');
}

export function detectWebglSupport(createCanvas: CanvasFactory = createBrowserCanvas): WebglSupport {
  let canvas: CanvasLike;

  try {
    canvas = createCanvas();
  } catch {
    return {
      supported: false,
      reason: 'context-error',
      message: '检测 WebGL 时发生异常，请检查浏览器硬件加速或显卡驱动设置。',
    };
  }

  let hasContextError = false;

  for (const name of WEBGL_CONTEXT_NAMES) {
    try {
      if (canvas.getContext(name)) {
        return {
          supported: true,
          reason: 'available',
          message: 'WebGL 可用',
        };
      }
    } catch {
      hasContextError = true;
    }
  }

  if (hasContextError) {
    return {
      supported: false,
      reason: 'context-error',
      message: '检测 WebGL 时发生异常，请检查浏览器硬件加速或显卡驱动设置。',
    };
  }

  return {
    supported: false,
    reason: 'context-unavailable',
    message: '当前浏览器无法创建 WebGL 上下文，Live2D 渲染页面可能无法启动。',
  };
}
