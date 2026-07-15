# 第三方组件与数字人资源声明

本文件用于记录项目参赛、演示和发布时涉及的主要第三方组件及素材。实际发布前仍应核对各权利方的最新条款。

## Fay

本项目基于 Fay 数字人框架进行二次开发。Fay 原项目代码及相关资源继续适用其原始许可证和版权声明。

## Live2D Cubism SDK for Web

- 组件：Live2D Cubism SDK for Web 5-r.4
- 权利方：Live2D Inc.
- Framework：Live2D Open Software License
- Cubism Core：Live2D Proprietary Software License
- 发布许可：根据主体规模、发布方式和应用类型另行判断

本项目将 Live2D 用作 AI/chatbot 交互界面，并支持发现、导入和切换模型。该使用方式可能需要按照 Expandable Application 规则接受 Live2D 审核，发布前应取得 Live2D 的明确答复。

## Live2D 原创示例角色

当前参赛精简版本保留以下 Live2D Original Characters：

- Chitose
- Epsilon
- Haru
- Hibiki
- Hiyori Momose
- Izumi
- Kei
- Mao Niziiro
- Mark-kun
- Rice Glassfield
- Wankoromochi

Hiyori 不得修改角色设计；Mark-kun 必须保持卡通角色性质；Wankoromochi 必须保持年糕主题。渲染项目保留 Wankoromochi，但 Fay 当前默认数字人列表未启用该角色。

本项目不包含或启用合作角色 Natori、第三方授权角色 Hatsune Miku，以及未启用的 Kei Basic 和 Miara。模型随附的示例声音和原始下载 ZIP 不属于本项目交付内容。

## 必要版权声明

> This content uses sample data owned and copyrighted by Live2D Inc.
> The sample data are utilized in accordance with terms and conditions set by Live2D Inc.
> This content itself is created at the author's sole discretion.

## 语音合成

数字人的对话声音由项目配置的外部 TTS 服务实时生成，不使用 Live2D 示例模型随附的声音。

当前部署使用 `mzzsfy/tts` Docker 镜像作为 OpenAI 兼容的 TTS 接口适配层。该镜像实际连接微软 Edge/Bing Read Aloud 在线语音接口，不是容器内运行的本地开源语音模型，也不是标准 Azure AI Speech 订阅接口。镜像代码许可、第三方自动调用方式、音色和合成输出的公开或商业使用范围仍需分别向镜像作者和微软确认。

在取得明确授权前，参赛材料不得将其描述为“自研 TTS”“本地 TTS 模型”或“已获微软商业授权”。正式公开或商业版本建议替换为具有明确使用条款的 Azure AI Speech 官方服务，或具有清晰代码、模型权重和音色许可证的本地 TTS。

## 参考条款

- https://www.live2d.com/eula/live2d-sample-model-terms_en.html
- https://www.live2d.jp/en/terms/live2d-free-material-license-agreement/
- https://www.live2d.com/en/sdk/license/
- https://hub.docker.com/r/mzzsfy/tts
