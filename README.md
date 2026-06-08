# Fay 数字人知识库助手

本仓库基于 Fay 数字人框架进行二次开发，集成了 Vue 管理端、用户认证、数据看板、消息会话、头像上传、MCP 管理、知识库上传与 RAG 检索等能力。项目主要用于搭建可本地运行的数字人问答平台，并支持通过本地 embedding 模型构建私有知识库。

## 功能概览

- 数字人对话：支持文本、语音、图片消息以及数字人播报。
- 用户体系：支持登录、注册、管理员用户管理、个人中心、头像上传和密码修改。
- 管理看板：提供运行状态、用户数据、会话数据和系统指标展示。
- 知识库：管理员可在前端上传文档，触发 ingest 后供 RAG 查询使用。
- MCP 管理：在 Vue 页面中管理 MCP server、工具、资源和连接状态。
- 本地 embedding：支持加载 `model/bge-large-zh-v1.5` 等本地模型，避免依赖远程 embedding API。

## 项目结构

```text
.
├── main.py                 # 主启动入口
├── fay_booter.py           # Fay 服务编排与启动逻辑
├── core/                   # 认证、会话、看板、核心交互服务
├── gui/                    # Flask 后端接口与传统页面
├── fay-frontend/           # Vue 3 + Vite 前端管理端
├── faymcp/                 # MCP 服务、MCP API 与知识库路由
├── mcp_servers/            # 本地 MCP server 示例与实现
├── llm/ asr/ tts/          # LLM、语音识别、语音合成适配
├── utils/                  # 配置、embedding、图片存储等工具
├── config/                 # 配置相关模块
└── readme/                 # README 图片资源
```

运行期数据通常会生成到 `memory/`、`logs/`、`cache_data/`、`library/` 等目录，这些内容不应提交到 Git。

## 环境要求

- Python 3.12
- Node.js 18+，用于运行 `fay-frontend`
- Windows、macOS 或 Ubuntu
- Ubuntu 需要先安装音频编译依赖：

```bash
sudo apt update
sudo apt install build-essential portaudio19-dev
```

## 后端启动

首次运行建议创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

如果使用本地配置，将 `system.conf.bak` 复制为 `system.conf`，并按需配置 LLM、ASR、TTS、认证和 embedding 参数：

```powershell
Copy-Item system.conf.bak system.conf
python main.py start
```

也可以使用配置中心启动：

```powershell
python main.py start -config_center <配置中心项目ID>
```

默认服务端口：

- Flask 管理接口：`http://127.0.0.1:5000`
- MCP 管理服务：`http://127.0.0.1:5010`
- 数字人 WebSocket：`10002`
- 前端数据 WebSocket：`10003`

## 前端启动

```powershell
cd fay-frontend
npm install
npm run dev
```

前端开发服务启动后，按终端输出的 Vite 地址访问。生产构建命令：

```powershell
npm run build
npm run preview
```

前端默认通过相对路径访问 Flask API，并通过 `VITE_MCP_API_BASE_URL` 访问 MCP API。需要单独指定 MCP 地址时，可在前端环境变量中配置：

```env
VITE_MCP_API_BASE_URL=http://127.0.0.1:5010
```

## 登录与用户管理

认证开启后，系统会在没有管理员时创建默认管理员：

```text
用户名：admin
密码：admin123
```

首次进入后请在个人中心或管理员用户管理中修改密码。普通用户可注册账号，管理员可在用户管理页面维护用户、重置密码、启用或停用账号。

## 知识库与 RAG

知识库文件默认存放在 `library/`。管理员可以在前端“知识库”页面上传 Word、文本等文档，然后执行 ingest，将文档切分、向量化并写入向量库。之后 LLM 可通过 RAG 查询相关内容。

MCP 中常见知识库工具含义：

- `ingest`：导入并向量化知识库文件。
- `query`：按问题检索相关知识片段。
- `status`：查看知识库索引、文件和服务状态。

如果对应的 RAG MCP server 未启动或未连接，RAG 工具不会参与回答。

## 本地 Embedding 模型

推荐将本地模型放在：

```text
model/bge-large-zh-v1.5
```

然后在配置中将 embedding 模型指向该路径，或使用环境变量：

```powershell
$env:EMBEDDING_MODEL_PATH="model/bge-large-zh-v1.5"
python main.py start
```

服务启动日志中出现 embedding 维度初始化和预热完成，说明本地 embedding 服务已加载。`bge-large-zh-v1.5` 的常见向量维度为 1024。

## 常用开发命令

```powershell
# 后端启动
python main.py start

# 前端开发
cd fay-frontend
npm run dev

# 前端构建
npm run build

# 前端测试
npm run test
```

## Git 与安全注意事项

不要提交密钥、个人配置、本地模型、运行日志、缓存、知识库原文或构建产物。重点避免提交：

```text
system.conf
.env
memory/
logs/
cache_data/
library/
model/
fay-frontend/node_modules/
fay-frontend/dist/
```

提交前建议检查：

```powershell
git status --short
git diff --cached --name-status
git diff --cached --name-only -G "TOKEN|PASSWORD|PRIVATE"
```

## 致谢

感谢 Fay 原项目及其相关开源生态提供的数字人、语音、MCP 和工具调用基础能力。本仓库在此基础上补充了面向本地知识库和多用户管理的应用层能力。
