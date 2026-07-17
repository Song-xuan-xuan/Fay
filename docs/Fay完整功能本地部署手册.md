# Fay 完整功能本地部署手册

本文说明如何在 Ubuntu 22.04 LTS 上从 GitHub 源码构建并运行 Fay 的完整功能。部署完成后，在本机浏览器访问：

```text
http://127.0.0.1:5000
```

本文仅描述本地部署，不包含域名、HTTPS、反向代理、进程管理器、后续升级、备份或回滚。

## 1. 部署内容

本方案包含以下组件：

- Fay Python 后端与内置管理服务
- Vue 3 管理前端，由部署人员在 Ubuntu 上从源码构建
- 智谱 OpenAI 兼容 LLM
- 智谱 `glm-asr-2512` 语音识别
- Docker 部署的 OpenAI 兼容 TTS
- 硅基流动 `BAAI/bge-m3` Embedding
- Live2D renderer 和 10 个现有数字人模型
- 悦神 RAG MCP
- 灵山课程知识库 MCP
- 和风天气 MCP
- 旅游数据看板 Excel
- 历史、自然、亲子三条初始推荐路线

完整运行时只需要手动维护以下三个启动单元：

```text
Docker TTS
Live2D renderer
Fay 主程序
```

前端构建产物由 Fay 的 5000 端口直接提供。MCP 管理服务由 Fay 主程序自动启动，不需要再单独启动前端服务或 MCP 管理服务。

## 2. 部署文件来源

### 2.1 GitHub 源码

源码仓库：

```text
https://github.com/Song-xuan-xuan/Fay.git
```

GitHub 中包含程序源码、前端源码、配置样例、Docker Compose 文件和 MCP 服务源码。

### 2.2 私有资源包

以下资源不放入 GitHub，通过网盘提供：

```text
文件名：fay-private-resources.zip
网盘地址：<填写网盘地址>
提取密码：<填写提取密码>
```

ZIP 解压后只有一个顶层目录：

```text
fay-private-resources/
├── library/
│   ├── live2d/Samples/Resources/
│   ├── 灵山胜境 景点结构化数据集.docx
│   ├── 灵山胜境：历史、文化、景点特色与个性化游览指南.docx
│   └── 景点景区旅游数据行为分析数据.xlsx
├── live2d-render/
│   └── current/
├── fay_player_knowledge/
│   └── 灵山胜境个性化游览指南课程包.zip
├── data/
│   └── 景点景区旅游数据行为分析数据.xlsx
└── recommendation/
    └── initial-routes.json
```

各目录用途如下：

- `library/`：RAG 原始文档和 Live2D 模型资源。
- `live2d-render/current/`：浏览器使用的 Live2D renderer 静态文件。
- `fay_player_knowledge/`：课程知识库 MCP 读取的原生课程包。
- `data/`：数据看板首次运行时导入的旅游 Excel。
- `recommendation/`：三条初始推荐路线的导入 JSON。

资源包不包含 API Key、`system.conf`、`.env`、用户数据库、MCP 运行配置、日志、缓存、历史推荐或背景资源。

## 3. 安装系统环境

以下命令可以在任意普通用户的终端中执行。系统软件安装命令需要 `sudo`。

### 3.1 基础软件和音频依赖

```bash
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  gnupg \
  git \
  unzip \
  ffmpeg \
  build-essential \
  portaudio19-dev \
  libgl1 \
  libglib2.0-0 \
  software-properties-common
```

`ffmpeg` 用于把 TTS 返回的 MP3 转换为 Fay 播放所需的 WAV。`portaudio19-dev` 用于安装 PyAudio。

### 3.2 安装 Python 3.12

Ubuntu 22.04 默认 Python 版本不是 3.12，因此安装 Python 3.12 及其虚拟环境和开发包：

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

确认版本：

```bash
python3.12 --version
```

### 3.3 安装 Node.js 20

Node.js 仅用于在部署机器上构建前端源码：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

确认版本：

```bash
node --version
npm --version
```

### 3.4 安装 Docker 和 Docker Compose

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt update
sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

确认安装：

```bash
sudo docker version
sudo docker compose version
```

## 4. 获取源码和私有资源

### 4.1 克隆源码

在准备存放项目的位置执行：

```bash
git clone https://github.com/Song-xuan-xuan/Fay.git
cd Fay
```

从本节开始，除非特别说明，所有命令均在项目根目录执行。

### 4.2 合并私有资源

将 `fay-private-resources.zip` 放到项目根目录，然后执行：

```bash
unzip fay-private-resources.zip
cp -a fay-private-resources/. .
```

复制后，项目根目录中应直接出现以下路径：

```text
library/live2d/Samples/Resources/
live2d-render/current/index.html
fay_player_knowledge/灵山胜境个性化游览指南课程包.zip
data/景点景区旅游数据行为分析数据.xlsx
recommendation/initial-routes.json
```

不要把资源复制到源码目录之外。Fay、renderer 和 MCP 配置均使用相对于项目根目录的路径。

## 5. 安装 Python 依赖

在项目根目录创建独立虚拟环境，不修改系统 Python 环境：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -r mcp_servers/yueshen_rag/requirements.txt
python -m pip install -r mcp_servers/weather/requirements.txt
```

以后在新的终端中运行 Fay 相关 Python 命令前，先执行：

```bash
source .venv/bin/activate
```

## 6. 从源码构建前端

前端必须在部署机器上从 GitHub 源码构建，不需要从其他机器上传 `dist`：

```bash
cd fay-frontend
npm ci
npm run build
cd ..
```

构建结果位于：

```text
fay-frontend/dist/
```

Fay 启动后会直接读取该目录，并通过 `http://127.0.0.1:5000` 提供前端页面。正式运行时不要再执行 `npm run dev` 或 `npm run preview`。

## 7. 配置 Fay

### 7.1 创建本地配置

仓库已经提供 `system.conf.bak` 样例，不需要额外上传配置模板：

```bash
cp system.conf.bak system.conf
nano system.conf
```

`system.conf` 不应提交到 GitHub。部署时填写实际 API Key 和已开通的模型 ID。

### 7.2 配置 ASR、LLM、TTS 和 Embedding

在 `system.conf` 的 `[key]` 中完整填写以下配置：

```ini
[key]
# 智谱语音识别
ASR_mode=zhipu
asr_api_url=https://open.bigmodel.cn/api/paas/v4/audio/transcriptions
asr_api_key=<填写智谱 ASR API Key>
asr_api_model=glm-asr-2512
asr_api_timeout=30

# 本地 OpenAI 兼容 TTS
tts_module=openai
openai_tts_speed=1.0

# 智谱小模型：日常对话和工具编排
gpt_api_key=<填写智谱 LLM API Key>
gpt_base_url=https://open.bigmodel.cn/api/paas/v4
gpt_model_engine=GLM-4.6V-FlashX

# 智谱大模型：复杂推理和核实场景
big_model_engine=<填写智谱大模型 ID>
big_model_base_url=https://open.bigmodel.cn/api/paas/v4
big_model_api_key=<填写智谱大模型 API Key>

# 硅基流动 Embedding
embedding_api_model=BAAI/bge-m3
embedding_base_url=https://api.siliconflow.cn/v1
embedding_api_key=<填写硅基流动 API Key>

proxy_config=
start_mode=web
fay_url=http://127.0.0.1:5000
```

模型 ID 必须与对应服务商控制台中实际开通的模型一致。不要把尖括号占位符原样保留在配置文件中。

### 7.3 设置初始管理员密码

仓库中的 `config.json` 已包含认证和 10 个数字人配置。首次启动前编辑：

```bash
nano config.json
```

找到：

```json
"auth": {
  "default_admin_password": "CHANGE_ME_BEFORE_FIRST_START",
  "default_admin_username": "admin",
  "enabled": true,
  "jwt_expiration_hours": 168
}
```

将 `CHANGE_ME_BEFORE_FIRST_START` 改为本次部署使用的管理员初始密码。该密码只在数据库中尚无管理员时用于创建默认管理员。

不要修改 `digital_humans` 中现有模型的 `render_url`。本地 renderer 固定使用 `http://127.0.0.1:5174`。

## 8. 启动 OpenAI 兼容 TTS

仓库已提供 TTS 的 Docker Compose 文件：

```text
deploy/tts/docker-compose.yml
```

拉取镜像并启动：

```bash
sudo docker compose -f deploy/tts/docker-compose.yml pull
sudo docker compose -f deploy/tts/docker-compose.yml up -d
```

该容器只监听本机：

```text
http://127.0.0.1:8080/v1/audio/speech
```

Fay 的 `tts/openai_tts.py` 会自动调用此地址，无需在 `system.conf` 中再填写 TTS URL。

查看容器状态和日志：

```bash
sudo docker compose -f deploy/tts/docker-compose.yml ps
sudo docker compose -f deploy/tts/docker-compose.yml logs --tail=100
```

需要单独检查语音合成时，可执行：

```bash
curl -sS -X POST http://127.0.0.1:8080/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "model":"tts-1",
    "voice":"zh-CN-XiaoxiaoNeural",
    "input":"Fay 语音服务已启动",
    "response_format":"mp3",
    "speed":1.0
  }' \
  --output samples/tts-test.mp3
```

## 9. 启动 Live2D Renderer

打开一个独立终端，进入项目根目录后执行：

```bash
.venv/bin/python -m http.server 5174 \
  --bind 127.0.0.1 \
  --directory live2d-render/current
```

保持该终端运行。10 个现有数字人共用这个 renderer 端口，不需要为每个数字人启动单独服务。

仓库的 `config.json` 已配置以下模型：

```text
Haru
Hiyori
Mao
Mark
Rice
chitose
Epsilon
hibiki
izumi_illust
kei_vowels_pro
```

默认数字人为 `Haru`，对应配置 ID 为 `live2d_haru`。本手册不需要执行“导入本地形象”或新增数字人的操作。

## 10. 启动 Fay

再打开一个独立终端，进入项目根目录后执行：

```bash
source .venv/bin/activate
python main.py start
```

Fay 主程序会自动启动：

- 5000：管理前端和 Flask API
- 5010：MCP 管理服务，仅绑定本机
- 8765：Fay 内置 MCP SSE 服务
- 9001：远程音频 WebSocket
- 10001：远程音频设备输出接口
- 10002：数字人 WebSocket
- 10003：前端数据 WebSocket

不要单独执行 `npm run dev`，也不要单独运行 `faymcp/mcp_service.py`。

浏览器打开：

```text
http://127.0.0.1:5000
```

使用以下账号登录：

```text
用户名：admin
密码：config.json 中设置的初始管理员密码
```

## 11. 配置三个 MCP 服务

登录管理员账号后，打开：

```text
http://127.0.0.1:5000/app/settings
```

三个服务均使用 `stdio`，并统一填写：

```text
传输方式：stdio
启动命令：.venv/bin/python
工作目录：.
启动 MCP 服务时自动连接：开启
保存后立即连接：开启
Prestart：不配置
```

MCP 配置由管理页面写入运行目录，不需要从其他机器上传 `faymcp/data/`。

### 11.1 悦神 RAG MCP

新建服务并填写：

```text
名称：悦神 RAG
参数：mcp_servers/yueshen_rag/server.py
```

环境变量 JSON：

```json
{
  "YUESHEN_CORPUS_DIR": "library",
  "YUESHEN_PERSIST_DIR": "cache_data/chromadb_yueshen",
  "YUESHEN_AUTO_INGEST": "1",
  "YUESHEN_AUTO_RESET_ON_START": "0"
}
```

保存并连接后，在工具列表中启用：

```text
ingest_yueshen
query_yueshen
yueshen_stats
```

RAG 服务会扫描 `library/` 中的 DOCX 和 PDF，并把新生成的向量数据写入 `cache_data/chromadb_yueshen/`。首次连接时自动开始构建索引。

### 11.2 灵山课程知识库 MCP

新建服务并填写：

```text
名称：灵山课程知识库
参数：mcp_servers/fay_player_knowledge/fay_player_knowledge_base_mcp_server.py --source fay_player_knowledge/灵山胜境个性化游览指南课程包.zip
环境变量 JSON：{}
```

保存并连接后，按需要启用以下工具：

```text
kb_list_sources
kb_get_catalog
kb_search
kb_get_section
kb_read_document
kb_reload
```

课程知识库会自动加载资源包中的 ZIP。课程章节包含图片时，该 MCP 进程会在本机 `127.0.0.1:18780` 提供临时图片文件。

### 11.3 和风天气 MCP

新建服务并填写：

```text
名称：和风天气
参数：mcp_servers/weather/server.py
```

环境变量 JSON：

```json
{
  "HEFENG_API": "<填写和风天气 API Key>",
  "HEFENG_API_HOST": "<填写和风天气 API Host>"
}
```

`HEFENG_API_HOST` 只填写主机名，不包含 `https://`、端口或路径。保存并连接后，启用：

```text
query_weather
```

## 12. 初始化数据看板

资源包已经把旅游 Excel 放到：

```text
data/景点景区旅游数据行为分析数据.xlsx
```

管理员首次打开数据看板时，Fay 会读取该文件并自动生成：

```text
memory/tourism.db
```

需要重新读取原始 Excel 时，在数据看板页面点击“重新导入”。不需要上传 `tourism.db`。

## 13. 导入三条推荐路线

管理员打开：

```text
http://127.0.0.1:5000/app/recommendation/manage
```

进入“配置与导入”标签页：

1. 打开 `recommendation/initial-routes.json`。
2. 复制文件的完整 JSON 内容。
3. 粘贴到“粘贴完整 JSON 数据”文本框。
4. 点击“导入 JSON”。

该文件只导入以下初始业务数据：

```text
17 个景点
3 条路线模板：历史、自然、亲子
26 个路线停靠点
23 条讲解素材
```

该文件不包含用户数据、推荐历史、历史日志或已有数据库 ID，可以导入到全新的数据库中。

## 14. 日常启动和停止

每次启动按以下顺序操作。

### 14.1 启动 TTS

```bash
sudo docker compose -f deploy/tts/docker-compose.yml up -d
```

### 14.2 启动 Live2D Renderer

终端一：

```bash
.venv/bin/python -m http.server 5174 \
  --bind 127.0.0.1 \
  --directory live2d-render/current
```

### 14.3 启动 Fay

终端二：

```bash
source .venv/bin/activate
python main.py start
```

停止时，在 renderer 和 Fay 所在终端按 `Ctrl+C`。停止 TTS 容器：

```bash
sudo docker compose -f deploy/tts/docker-compose.yml down
```

## 15. 常见部署问题

### 15.1 5000 页面不是 Vue 管理端

确认前端已构建：

```bash
test -f fay-frontend/dist/index.html && echo "frontend build exists"
```

如果文件不存在，重新执行：

```bash
cd fay-frontend
npm ci
npm run build
cd ..
```

### 15.2 数字人区域空白

确认 renderer 终端仍在运行，并检查：

```bash
curl -I http://127.0.0.1:5174/
```

同时确认存在：

```text
live2d-render/current/index.html
library/live2d/Samples/Resources/
```

不要点击“导入本地形象”重复创建模型。

### 15.3 发送消息后没有声音

检查 TTS 容器：

```bash
sudo docker compose -f deploy/tts/docker-compose.yml ps
sudo docker compose -f deploy/tts/docker-compose.yml logs --tail=100
```

检查 `system.conf`：

```ini
tts_module=openai
```

检查系统中存在 `ffmpeg`：

```bash
ffmpeg -version
```

### 15.4 MCP 页面无法加载或服务离线

MCP 页面必须通过 5000 端口访问：

```text
http://127.0.0.1:5000/app/settings
```

确认 Fay 主终端没有 5010 端口占用或 Python 子进程启动错误。stdio MCP 的命令和工作目录必须分别为：

```text
.venv/bin/python
.
```

### 15.5 RAG 没有知识库内容

确认文档已复制到 `library/`，并检查悦神 RAG 环境变量中的相对路径。首次索引需要等待 Embedding API 完成文档向量化，可在 MCP 工具列表调用 `yueshen_stats` 查看向量数量。

### 15.6 数据看板没有旅游数据

确认文件存在：

```bash
ls -lh data/景点景区旅游数据行为分析数据.xlsx
```

然后以管理员身份打开数据看板，点击“重新导入”。

### 15.7 路线推荐没有初始路线

确认已在“维护推荐 → 配置与导入”中导入 `recommendation/initial-routes.json`。只把 JSON 文件复制到服务器不会自动写入推荐数据库，必须执行一次页面导入操作。
