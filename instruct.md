# Fay 数字人项目 — LLM 快速理解指南（instruct.md）

> **文档目的**：本文件面向 LLM / AI 编程助手，提供对本项目的系统性理解，使其能在最短时间内建立全局认知并安全地进行开发。
> **生成方式**：基于 2026-06-10 对全仓库的多代理深度代码审读（18 个并行分析代理、645 次代码读取），所有结论均有 `文件:行号` 级证据。
> **维护要求**：本文件需随代码演进持续维护，修改架构/端口/接口/数据模型时必须同步更新对应章节，详见末尾「文档维护指南」。
> **相关文档**：`CLAUDE.md`（开发规范与命令速查）、`README.md`（用户向使用说明）、`docs/`（专项设计文档）。注意 CLAUDE.md 个别描述已过时（如 MCP SSE 端口），以本文件为准。

---

## 目录

1. [项目概览](#1-项目概览)
2. [技术栈](#2-技术栈)
3. [目录结构](#3-目录结构)
4. [端口与服务总表](#4-端口与服务总表)
5. [配置体系](#5-配置体系)
6. [后端子系统详解](#6-后端子系统详解)
   - 6.1 入口与启动流程
   - 6.2 核心交互链路（最重要）
   - 6.3 认证与用户体系
   - 6.4 数据层与业务服务
   - 6.5 LLM 与 Agent
   - 6.6 MCP 集成
   - 6.7 语音子系统（ASR/TTS）
   - 6.8 HTTP 接口层（API 总清单）
7. [前端 fay-frontend](#7-前端-fay-frontend)
8. [WebSocket 协议规范](#8-websocket-协议规范)
9. [数据存储总表](#9-数据存储总表)
10. [测试与工程化](#10-测试与工程化)
11. [辅助与边缘模块](#11-辅助与边缘模块)
12. [全局编码约定](#12-全局编码约定)
13. [已知坑点汇总](#13-已知坑点汇总)
14. [常见开发任务指引](#14-常见开发任务指引)
15. [文档维护指南](#15-文档维护指南)

---

## 1. 项目概览

**Fay** 是一个基于原版 Fay 开源数字人框架二次开发的「数字人知识库助手」平台，采用 **Flask（Python 3.12）后端 + Vue 3（Vite）前端** 的前后端分离架构。

一句话架构：**多渠道输入（文字/麦克风/远程设备音频）→ ASR → LLM 流式生成（LangGraph Agent + MCP 工具 + RAG）→ 流式切句 → TTS → 数字人驱动（WebSocket 推送音频/文本/情感/动作/唇形）**，外加一套完整的 Web 管理台（登录认证、用户管理、数据看板、消息会话、知识库、MCP 管理、数字人库管理、Live2D 展示）。

核心特性：

- **全链路流式**：LLM 逐句生成 → 逐句 TTS → 逐句推送播放，支持随时打断。
- **多用户并发**：以 `username` 和 `(username, conversation_id)` 为键隔离所有会话状态。
- **二开应用层**（相对原版 Fay 新增）：JWT 认证 + 双角色权限、审计日志、数据看板（运营/用户/旅游）、数字人库管理（Live2D 模型发现与导入）、Vue3 管理前端、本地 embedding 知识库 RAG。
- **MCP 工具生态**：可连接外部 MCP 服务器（stdio/SSE），也将 Fay 内部能力（记忆等）暴露为 MCP 工具。
- **双 UI 并存**：`fay-frontend/`（Vue3 新管理台，主力）与 `gui/templates/`（legacy jQuery 页面，回退路径）。

---

## 2. 技术栈

### 后端

| 类别 | 选型 | 说明 |
|---|---|---|
| 语言/运行时 | Python 3.12 | 虚拟环境 `.venv` |
| Web 框架 | Flask ~3.0 | 主管理 API（5000）；MCP 管理服务用 gevent pywsgi（5010） |
| WebSocket | websockets ~10.4 | 自研 `MyServer` 封装（10002/10003/9001） |
| LLM 编排 | LangChain + LangGraph | Agent 工作流（会话/思考/工具/反思节点） |
| MCP | `mcp` SDK | stdio + SSE 双协议；内置 SSE 服务器用 uvicorn |
| 认证 | PyJWT (HS256) + bcrypt + flask-httpauth | JWT 体系为主；HTTPBasicAuth 为 legacy 残留 |
| 数据库 | SQLite ×5 | `memory/fay.db`、`memory/user_profiles.db`、`memory/tourism.db`、`memory/visitor_reports.db`、`memory/tourism_recommendation.db` |
| 向量库 | ChromaDB | RAG 知识库（yueshen_rag MCP 服务器内） |
| 音频 | PyAudio / pydub / pygame | 录音、格式转换、本地播放 |
| 桌面窗口 | PyQt5（可选，requirements 中被注释） | 仅 `start_mode=common` |

### 前端（fay-frontend/）

| 类别 | 选型 |
|---|---|
| 框架 | Vue 3.4（Composition API + `<script setup>`） |
| 构建 | Vite 5 + vue-tsc（TypeScript 5.3.3） |
| 状态管理 | Pinia 2 |
| 路由 | vue-router 4 |
| UI 组件库 | Element Plus 2.5 + @element-plus/icons-vue + @lucide/vue |
| HTTP | axios |
| 测试 | Vitest 1.6（`npm run test`） |

### 常用命令

```bash
# 后端
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
cp system.conf.bak system.conf                    # 配好密钥后
python main.py start                              # 本地配置启动
python main.py start -config_center <项目ID>      # 配置中心启动
python main.py --migrate                          # 执行数据库迁移（migrations/001_add_auth.py）

# 前端
cd fay-frontend
npm install
npm run dev        # Vite 开发服务器（默认 5173，代理到 Flask 5000）
npm run build      # vue-tsc 类型检查 + 构建到 dist/
npm run test       # Vitest 单测

# 运行时控制台命令（后端进程 stdin）
help / start / stop / restart / in <消息> / exit
```

---

## 3. 目录结构

```text
D:\Fay\Fay\
├── main.py                 # 唯一入口：参数预处理、信号注册、基础服务按序启动、控制台命令循环
├── fay_booter.py           # 业务启动协调器：FeiFei 核心、录音、设备音频、自动播报、MCP SSE
├── config.json             # 运行时行为配置（人设/数字人库/交互/音源/记忆隔离）——会被程序回写
├── system.conf             # 密钥类配置（不入 git）；模板为 system.conf.bak
├── verifier.json           # legacy HTTPBasicAuth 账号文件（当前为空 {}）
├── qa.csv                  # QnA 问答库（采纳回复会写入）
│
├── core/                   # 核心层
│   ├── fay_core.py             # 交互中枢 FeiFei（最大文件，行间双空行格式）
│   ├── interact.py             # Interact 交互对象
│   ├── stream_manager.py       # 每用户句子流缓冲与消费线程、打断标志
│   ├── recorder.py             # 录音基类（VAD/ASR 调度/唤醒词）
│   ├── wsa_server.py           # WebSocket 服务器（10002 数字人 / 10003 UI）
│   ├── socket_bridge_service.py# WS 9001 ↔ TCP 10001 桥
│   ├── action_signal.py        # 动作信号规则匹配（config/action_rules.csv）
│   ├── auth_service.py         # JWT 签发/校验、require_auth/require_role
│   ├── auth_bootstrap.py       # 默认管理员引导（admin/admin123）
│   ├── audit_service.py        # 审计日志（T_AuditLog）
│   ├── member_db.py            # 用户表 T_Member 数据访问
│   ├── authorize_tb.py         # ⚠️ 名字误导：第三方云 token 缓存表，与用户认证无关
│   ├── content_db.py           # 对话/会话/采纳表（memory/fay.db）
│   ├── memory_service.py       # 仿生记忆流读写适配层
│   ├── qa_service.py           # QnA CSV 匹配
│   ├── dashboard_service.py    # 看板门面（+ dashboard_operational / dashboard_sessions / dashboard_tourism）
│   ├── visitor_report_service.py / visitor_report_rules.py / visitor_report_storage.py # 游客感受度报告
│   ├── tourism_recommendation_service.py / tourism_recommendation_algorithm.py / tourism_recommendation_schema.py # 个性化游览推荐服务/算法/建表自愈
│   ├── tourism_recommendation_catalog.py / tourism_recommendation_import.py / tourism_recommendation_repository.py / tourism_recommendation_utils.py # 推荐维护、导入导出、仓储工具
│   ├── digital_human_service.py# 数字人库管理（持久化在 config.json）
│   └── live2d_resource_service.py # Live2D 模型扫描与导入
│
├── llm/                    # LLM 层
│   ├── nlp_cognitive_stream.py # LLM 认知流式核心（LangGraph Agent、question() 入口）
│   ├── execution_manager.py    # 后台任务执行状态跟踪
│   └── rag_citations.py        # RAG 引用标注
│
├── gui/                    # Flask HTTP 层 + legacy 页面
│   ├── flask_server.py         # Flask 主服务（5000），40+ 业务接口
│   ├── auth_routes.py          # 认证/用户管理路由
│   ├── avatar_routes.py        # 头像上传路由
│   ├── dashboard_routes.py     # 看板路由
│   ├── digital_human_routes.py # 数字人管理路由
│   ├── tourism_recommendation_routes.py / tourism_recommendation_user_routes.py / tourism_recommendation_admin_routes.py / tourism_recommendation_route_utils.py # 个性化推荐用户/管理员路由
│   ├── templates/ static/      # legacy jQuery 管理页面（dist 缺失时的回退）
│   └── window.py               # PyQt5 桌面窗口（仅 start_mode=common）
│
├── faymcp/                 # MCP 集成
│   ├── mcp_service.py          # MCP 管理 HTTP 服务（独立端口 5010）
│   ├── mcp_server.py           # 内置 MCP SSE 服务器（默认 8765，暴露记忆等工具）
│   ├── mcp_client.py           # MCP 客户端（stdio/SSE）
│   ├── tool_registry.py / resource_registry.py / prestart_registry.py
│   ├── runtime_bridge.py       # 工具调用 → Fay 核心路由
│   ├── kb_routes.py            # 知识库 HTTP 路由
│   └── data/                   # mcp_servers.json / 工具状态持久化
│
├── mcp_servers/            # 自带外部 MCP 服务器实现
│   ├── schedule_manager/       # 日程管理（含独立 Web 管理 5011）
│   ├── window_capture/         # 窗口截图
│   └── yueshen_rag/            # 知识库 RAG（ChromaDB）
│
├── asr/                    # 语音识别（funasr.py / ali_nls.py / funasr 目录）
├── tts/                    # 语音合成（azure/ali/volcano/gptsovits/openai/edge）
├── ai_module/              # 百度情感分析等
├── genagents/              # 仿生记忆 GenerativeAgent（论文 Generative Agents）
├── simulation_engine/      # GenAgent 依赖的提示词模板与 GPT 调用封装
├── utils/                  # config_util、util、流式工具、embedding 后端、图片存储
├── scheduler/              # thread_manager（MyThread/stopAll）
├── skills/                 # 独立客户端示例脚本（remote_audio_key0.py，不被主程序 import）
├── migrations/             # 数据库迁移（001_add_auth.py，--migrate 触发）
├── config/                 # action_rules.csv（动作信号规则）
├── data/                   # 旅游看板 Excel 数据源
├── test/                   # 后端测试脚本（脚本式 + unittest 混合）+ ovr_lipsync 等资源
├── docs/                   # 专项设计文档（动作改造/MCP知识库/Live2D 制作要求等）
├── scripts/                # 辅助脚本（update_logo_version.py）
│
├── fay-frontend/           # Vue3 前端（详见第 7 章）
│   └── src/
│       ├── api/                # axios 封装与各域 API
│       ├── views/              # 10 个 AppLayout 子页面 + Login
│       ├── components/         # 按业务域分组的组件
│       ├── composables/        # 可复用逻辑
│       ├── stores/             # Pinia（app/auth/live2d）
│       ├── router/             # 路由 + 守卫
│       ├── utils/              # websocket/messageStream/live2d 等核心工具
│       └── styles/             # 全局样式
│
└── 运行期目录（不提交 git）：memory/ logs/ cache_data/ samples/ library/ model/
```

---

## 4. 端口与服务总表

| 端口 | 协议 | 服务 | 定义位置 | 鉴权 |
|---|---|---|---|---|
| **5000** | HTTP | Flask 主管理 API + Vue SPA 托管 + legacy 页面 | `gui/flask_server.py:2379`（werkzeug，0.0.0.0） | JWT（软门禁，见 6.3） |
| **5010** | HTTP | MCP 管理服务（服务器 CRUD/工具/资源/知识库路由） | `faymcp/mcp_service.py:1728`（gevent，默认 127.0.0.1，`FAY_MCP_HOST` 可改） | auth.enabled 时需 admin Bearer |
| **5011** | HTTP | 日程 MCP 的独立 Web 管理（子进程） | `mcp_servers/schedule_manager/web_server.py:385` | 无 |
| **5173** | HTTP | Vite 前端开发服务器（代理 → 5000） | `fay-frontend/vite.config.ts` | — |
| **5174** | HTTP | Live2D 渲染服务（外部独立项目，`render_url` 指向） | `core/digital_human_service.py:11` | — |
| **8765** | HTTP/SSE | 内置 MCP SSE 服务器（⚠️ CLAUDE.md 写 9002 已过时） | `faymcp/mcp_server.py:75-77`，env `FAY_MCP_SSE_HOST/PORT/PATH`，路径 `/sse` | 无 |
| **9001** | WS | 远程音频 WebSocket 桥（→ TCP 10001） | `core/socket_bridge_service.py:146` | 无 |
| **10001** | TCP | 硬件设备音频原生 socket（流内嵌 `<username>`/`<output>` 标签协议） | `fay_booter.py:223` | 无 |
| **10002** | WS | 数字人接口（question/log/text/audio 驱动消息） | `core/wsa_server.py:314` | auth.enabled 时首条消息须带 JWT |
| **10003** | WS | UI 面板接口（panelMsg/panelReply 等） | `core/wsa_server.py:297` | 同上 |
| 外部 | HTTP | 配置中心 `GET /api/projects/{pid}/config` | `utils/config_util.py:233`（默认 http://1.12.69.110:5500） | X-API-Key |

> 控制台 `exit` 命令只按端口清杀 10001/10002/10003/5000/9001（`main.py:277`），5010 与 8765 依赖 `stopAll()`/`os._exit` 兜底。

---

## 5. 配置体系

### 5.1 双文件 + 配置中心

| 文件 | 格式 | 内容 | 读写方 |
|---|---|---|---|
| `system.conf`（模板 `system.conf.bak`） | INI，`[key]` 段 | 密钥类：ASR_mode（funasr/ali/sensevoice）、tts_module、gpt_api_key/base_url/model_engine（小模型）、big_model_engine（大模型）、embedding 配置、代理、start_mode（common/web）、fay_url | `utils/config_util.py` 加载后展开为**模块级全局变量** |
| `config.json` | JSON | 行为类：attribute（人设）、digital_humans（数字人库，**程序会回写**）、interact（QnA 路径/playSound）、source（录音/唤醒词/自动播报）、memory（isolate_by_user/use_bionic_memory）、auth（认证开关，当前缺省=禁用） | `config_util.config` 字典；`save_config_sections()` 分段回写，`save_config()` 全量回写 |

### 5.2 加载机制与优先级（`config_util.py:292-635`）

1. 环境变量 `FAY_CONFIG_CENTER_ID` 存在（来自 `-config_center` 参数）→ 工作路径切到 `cache_data/`，从配置中心 API 拉取，成功后把 system.conf 序列化进环境变量 `FAY_SYSTEM_CONF_JSON`（供 MCP stdio 子进程继承），并缓存到 `cache_data/`；失败回退缓存/内存。
2. 否则读根目录 `system.conf` + `config.json`；二者任一缺失再回退配置中心。
3. **记忆化**：配置中心模式下同一 ID 已加载过则直接返回缓存，改远端配置需 `force_reload=True` 或重启。
4. 隐式回退：`embedding_base_url` 为空复用 `gpt_base_url`，`embedding_api_key` 为空复用 `gpt_api_key`（`config_util.py:556-560`）；`fay_url` 留空自动探测本机 IP 拼 `http://ip:5000`（多网卡可能选错）。

### 5.3 关键环境变量

| 变量 | 作用 |
|---|---|
| `FAY_CONFIG_CENTER_ID` | 配置中心项目 ID |
| `FAY_SYSTEM_CONF_JSON` | system.conf 的 JSON 序列化（跨进程传递，**含密钥**） |
| `FAY_MCP_HOST` | MCP 管理服务绑定地址（默认 127.0.0.1） |
| `FAY_MCP_SSE_HOST/PORT/PATH` | 内置 MCP SSE 服务器（默认 0.0.0.0:8765/sse） |
| `FAY_LIVE2D_SAMPLES_ROOT` | Live2D Cubism SDK Samples 目录；未设置时使用仓库内 `library/live2d/Samples` |
| `EMBEDDING_MODEL_PATH` | 本地 embedding 模型路径（如 `model/bge-large-zh-v1.5`，维度 1024） |
| `YUESHEN_*` | yueshen_rag MCP 服务器配置（语料目录/持久化目录/embedding 覆盖开关等） |

> ⚠️ `config_util.load_config()` 必须先于依赖配置的模块导入执行（`main.py:184`）。

---

## 6. 后端子系统详解

### 6.1 入口与启动流程

**关键文件**：`main.py`（入口）、`fay_booter.py`（业务编排）、`scheduler/thread_manager.py`（线程管理）、`utils/config_util.py`、`utils/util.py`（日志）。

**main.py 导入阶段特殊分支**（在重量级 import 之前）：
- `-config_center <id>` → 预置 `FAY_CONFIG_CENTER_ID` 环境变量（`main.py:86`）
- `--mcp-stdio-runner <script>` → 以 runpy 代跑 MCP 子服务器脚本后退出（`main.py:87`，MCP stdio 服务器以 `python main.py --mcp-stdio-runner xxx/server.py` 形式启动，从而继承 Fay 的运行时环境与 `FAY_SYSTEM_CONF_JSON` 配置）
- `--migrate` → 执行 `migrations.001_add_auth.run()` 后退出（`main.py:63-71`）

**`__main__` 启动序列**（`main.py:286-365`）：
```
归档 samples/logs 历史文件 → content_db.init_db() → auth_bootstrap.ensure_default_admin()
→ WS 10002（数字人）→ WS 10003（UI）→ ali_nls token 线程（仅 ASR_mode=ali）
→ Flask 5000 → faymcp.mcp_service（5010，try/except 容错）→ console_listener 线程
→ argv 带 start（或打包后双击）→ MyThread 异步执行 fay_booter.start()
→ start_mode=common 进 PyQt5 事件循环，否则主线程 while True sleep
```

**`fay_booter.start()` 业务序列**（`fay_booter.py:368-451`）：
```
load_config → embedding 预热（探维度）→ FeiFei().start() → init_memory_scheduler（记忆定时任务）
→ RecorderListener 麦克风监听 → TCP 10001 设备音频 accept 循环 + 心跳线程
→ socket_bridge_service WS 9001 → 自动播报轮询线程 → uvicorn 启动 MCP SSE（默认 8765）
```
`stop()` 顺序与之对称：先停外围 IO、再保存状态（`save_agent_memory`）、最后停核心（`feiFei.stop()`）。

**线程模型**：所有后台线程必须用 `scheduler.thread_manager.MyThread`（构造时自动登记），退出时 `stopAll()` 用 `ctypes.PyThreadState_SetAsyncExc` 注入 SystemExit。⚠️ 阻塞在 `input()`/`socket.accept()`/`recv()` 等 C 层调用的线程无法被注入，最终靠 `os._exit(0)` 强杀（`main.py:160`）。

**信号处理**：SIGINT/SIGTERM/SIGBREAK → 在 daemon 线程中执行清理（`fay_booter.stop()` + `stopAll()`），超时 5 秒 `os._exit(1)`。

**日志约定**：`util.log(level, text)` / `util.printInfo(level, sender, text)`；level≥3 时同步推送 10002/10003 WebSocket 并异步写 `logs/log-时间戳.log`。启动时会把历史 `logs/*.log` 与 `samples/sample-*` 归档到各自的 `archive/<启动批次>/`，默认保留最近 10 个归档批次。

### 6.2 核心交互链路（最重要）

这是理解 Fay 的钥匙。**所有输入渠道最终都构造 `Interact` 对象并调用 `FeiFei.on_interact`**（`core/fay_core.py:844`）。

**Interact 对象**（`core/interact.py`）：`Interact(interleaver, interact_type, data)`，interleaver 标识来源（`console`/`mic`/`socket`/`auto_play`/`text`/`stream`），interact_type `1`=语音文字交互（异步处理，**返回线程对象而非文本**），`2`=透传（同步）。

**完整链路**：

```
【输入】麦克风/远程设备 → Recorder.__record (recorder.py:235) VAD 检测
        → ASR（ali 边录边推 / funasr 录完推文件）→ 唤醒词判断 → on_speaking
        → Interact → feiFei.on_interact
        控制台 in 命令 / HTTP /api/send / WS → 同样构造 Interact

【调度】on_interact (fay_core.py:844)
        → 会话活跃则 clear_Stream_with_audio 打断旧会话
        → 生成 conv_<uuid4> 并 set_current_conversation → set_stop_generation(False)
        → MyThread 异步 __process_interact (fay_core.py:540)

【处理】__process_interact → 推 10002 Key=question → content_db.add_content 存用户消息
        → 推 10003 panelReply(type=member) → QA 命中走 __process_stream_output
        → 未命中调 llm/nlp_cognitive_stream.question() 流式生成

【切句】LLM chunk 累积 ≥20 字符按标点切句 (nlp_cognitive_stream.py:2689)
        → StreamStateManager.prepare_sentence 附 _<isfirst>/_<isend> 隐藏标记
        → StreamManager.write_sentence 附 __<cid=conv_xxx>__ 会话标签
        → 写入每用户独立的 SentenceCache 环形缓冲（主流+NLP流双份）

【消费】每用户一个 listen 线程 (stream_manager.py:306) 读句
        → execute() 剥离标记、校验 cid 与停止标志 → Interact("stream",1) → fay_core.say

【输出】say (fay_core.py:1114)
        → isfirst 建 content_db 记录获 content_id，后续句子累积 update_content
        → __send_panel_message 推 10003 panelMsg+panelReply(type=fay)
        → __send_digital_human_message 推 10002 Key=text
        → 过滤 <think>/<prestart>/emoji/markdown 图片 → TTS（sha1 缓存，上限 1000 条）
        → MyThread 执行 __process_output_audio

【音频下发】__process_output_audio (fay_core.py:2173)
        → 计算 Sentiment（百度情感 API 或关键词兜底）
        → Action（config/action_rules.csv 规则匹配，见 11.3）
        → Lips（Windows OVR LipSync 唇形）
        → __send_human_audio_ordered 按 CONV_MSG_NO 重排后推 10002 Key=audio
        → playSound 开启时入 sound_query 由 pygame 本地串行播放
        → 远程设备 socket 以 \x00..\x08 开始/\x08..\x00 结束标志分帧下发
```

**打断机制**（贯穿全链路的双重校验 `stop_generation_flags[username]` + conversation_id）：
新输入到达 → `clear_Stream_with_audio`（`stream_manager.py:270`）置停止标志、清音频队列、清空双流并写 `_<isend>` 哨兵。下游在 LLM 每 chunk、write_sentence 写入、TTS 前后、音频处理入口、pygame 播放循环每 10ms 共五处检查 `should_stop_generation(username, conversation_id)`，旧会话句子因 cid 不匹配被静默丢弃。停止标志在下一条带 `_<isfirst>` 的句子写入时复位。

**唤醒打断**：播音中识别到唤醒词 → 停止当前播放并回复"在呢，你说？"（`recorder.py:118-135`）。唤醒词 60 秒无交互自动失效。

**重要细节/坑**：
- `sound_query` 与 `speaking` 标志是 FeiFei 实例级全局的：多用户本地播放互相排队；一个用户播音会让无唤醒模式下所有麦克风暂停拾音（`recorder.py:268`）。
- `say()` 在 is_end 时硬编码 `time.sleep(1)`（`fay_core.py:1737`，作者标注 TODO）。
- 音频序号与文本序号是两套独立计数；数字人客户端必须按 `IsEnd` 判断结束而非包数。
- `<think>` 超 5 秒会插播"请稍等..."；`</think>` 前内容不发声。
- `fay_core.py` 每逻辑行间有两个空行（格式异常），grep 时注意行号稀疏。
- fay_core 与 fay_booter 通过文件末尾 `importlib.import_module('fay_booter')` 打破循环依赖（`fay_core.py:3193`）。
- `StreamManager.new_instance(max_sentences)` 参数只在首次创建生效；每用户 listen 线程创建后永不回收。

### 6.3 认证与用户体系

**三层结构**：`core/auth_service.py`（JWT 签发/校验 + `require_auth`/`require_role` 装饰器）→ `core/member_db.py`（T_Member 表，bcrypt）→ `core/audit_service.py`（T_AuditLog 审计）。HTTP 层 `gui/auth_routes.py`（11 接口）+ `gui/avatar_routes.py`（头像）。

**⚠️ 软门禁设计（最重要认知）**：`config.json` 的 `auth.enabled` 默认 false（当前仓库 config.json **没有 auth 段**），此时所有 `require_auth`/`require_role` 接口对无 token/无效 token **一律放行**（`auth_service.py:96-104,117-119`）；只有显式配置 `auth.enabled=true` 才强制 401/403。WS 10002/10003 的 token 鉴权同理。**测试鉴权逻辑前必须先开启 auth.enabled**。

**JWT 细节**：HS256；密钥优先 `config.json auth.jwt_secret`（占位值 `your-secret-key-change-me-in-production` 视为未配置），否则自动生成持久化到 `memory/.jwt_secret`；过期 `auth.jwt_expiration_hours` 默认 168 小时。**无吊销机制**：logout 仅写审计；`require_role` 直接信任 payload 不回查库，用户被删/禁用/降级后旧 token 在过期前依然有效（仅 `/api/auth/me` 回查 is_active）。

**默认管理员引导**（`core/auth_bootstrap.py`，`main.py:296-298` 调用）：auth.enabled 为真且无活跃 admin 时创建 `admin/admin123`（可由 `auth.default_admin_username/password` 覆盖），`force_change=True` 通过 `password_changed_at=NULL` 表达，登录响应返回 `must_change_password` 由前端引导强制改密（后端不真正拦截）。⚠️ 副作用：若同名用户存在但无活跃 admin，重启会强制重置其密码并提升为 admin。

**用户表要点**：列名 `id` 对外重命名为 `uid`；保留用户 `'User'`（匿名对话默认归属，密码空无法登录，每次 init_db `INSERT OR IGNORE`）；`list_users` 返回脱敏字典（**扩展时用它**，勿用含 hash 的 `get_all_users`）。

**审计约定**：action 用小写下划线英文（login_success/user_create/avatar_update...），resource 用 `uid=<n>`，IP 取 X-Forwarded-For 首段；存 `memory/user_profiles.db` T_AuditLog。

**头像**：POST `/api/auth/avatar`（multipart，png/jpg/jpeg/webp/gif ≤2MB 按 Content-Length 粗判）→ `cache_data/avatars/{uid}-{uuid4hex}.{ext}` → `T_Member.avatar_path`；旧头像不删除会堆积。

**前端配合**：JWT 存 localStorage 键 `fay_token`（`stores/auth.ts`），axios 拦截器统一注入 `Authorization: Bearer`。

**其他坑**：注册接口完全开放无频率限制；管理员创建用户不走 `_validate_username`；`PUT /api/users/<uid>` 可把最后一个 admin 降级锁死系统；`core/authorize_tb.py` 名字误导——它是阿里云 NLS/百度 token 的缓存表（存 fay.db T_Authorize），与用户认证无关；`flask_server.py` 残留 HTTPBasicAuth（verifier.json）仅保护 `/` 首页。

**API 清单（认证域）**：

| 方法 | 路径 | 功能 | 鉴权 |
|---|---|---|---|
| POST | /api/auth/login | 登录，返回 JWT/角色/must_change_password/expires_in | 公开 |
| POST | /api/auth/register | 开放注册（role=user，密码≥8 位，禁用 User/admin） | 公开 |
| POST | /api/auth/logout | 登出（仅审计，不吊销） | JWT |
| GET | /api/auth/me | 当前用户（回查库，校验 is_active） | JWT |
| POST | /api/auth/change-password | 自助改密，返回新 token | JWT |
| GET/POST | /api/users | 列出/创建用户 | admin |
| PUT/DELETE | /api/users/\<uid\> | 更新（role/email/is_active）/删除用户 | admin |
| POST | /api/users/\<uid\>/reset-password | 重置密码（强制改密） | admin |
| GET | /api/audit-logs | 审计日志分页（username/action 过滤，limit≤500） | admin |
| POST | /api/auth/avatar | 上传头像 | JWT |
| GET | /avatars/\<filename\> | 头像静态访问 | 公开 |

### 6.4 数据层与业务服务

**五个 SQLite 库**（详见第 9 章总表）：`memory/fay.db`（对话）、`memory/user_profiles.db`（用户/审计）、`memory/tourism.db`（旅游看板）、`memory/visitor_reports.db`（游客报告）、`memory/tourism_recommendation.db`（个性化推荐）。

**core/content_db.py**（fay.db 单例访问层）：
- 对话写入：用户消息 `fay_core.py:602` / 回复 `fay_core.py:1254` 调 `add_content()`；流式回复先 `add_content('fay','speak','')` 占位再反复 `update_content` 覆盖。
- 无 session_id 的用户消息自动按 30 分钟超时 upsert `T_ServiceSession` 并用 `classify_question_topic` 打 topic 标签。
- 采纳：`/api/adopt-msg` → `adopted_message` 写 T_Adopted → `qa_service.record_qapair` 追加 QnA CSV；取消采纳按去 `<think>` 后内容批量匹配删除。
- ⚠️ `get_list` 的 uid/order 参数直接拼 SQL（`content_db.py:314`），调用方必须保证合法。

**core/memory_service.py**（仿生记忆流唯一权威读写入口）：
- tag 必须带命名空间前缀 `<namespace>:<value>`（9 个命名空间），kind 取 KIND_ENUM 八枚举；非法 kind 降级为 observation 不抛错。
- 三段式写入：锁外算 importance/embedding → 持 `ncs.agent_lock` 写节点 → 锁外刷盘 `memory/<user>/memory_stream/nodes.json` + `embeddings.json`。
- 被 `faymcp/mcp_server.py` 以 `memory_*` MCP 工具暴露（asyncio.to_thread 进程内直调）。

**core/qa_service.py**：difflib 相似度阈值 0.6（含子串 +0.3）；多候选命中按「分数 → 问题长度 → CSV 原顺序」稳定选择最佳项；CSV 第三列命令动作默认**不执行**，仅在 `config.json interact.enableQnACommandActions=true` 时才通过 `MyThread` 异步执行。

**看板（dashboard_service + operational + tourism）**：
- 运营指标：优先读取 `T_ServiceSession`（过滤 `deleted_at` 与 `message_count=0`），只对历史无 `session_id` 消息按 30 分钟超时做 legacy 兜底推导，避免与 `content_db` 写入的会话记录不一致。
- 用户指标：T_Member 全表统计，非 admin 邮箱脱敏。
- 旅游指标：`data/imports/tourism_behavior.xlsx`（优先）→ 按 mtime 判重 → **全量重建** `tourism.db` 的 tourism_visit（先 DELETE 再 INSERT）；每次 `get_overview/get_tourism` 请求都触发 mtime 检查导入。
- Excel 列顺序必须与 REQUIRED_HEADERS 一致（按位置取值，跳过第 6 列）。
- 游客感受度报告：`visitor_report_service` 从 `T_Msg` 抽取非管理员游客消息，按回复文本、投诉/未解决关键词、topic 和旅游上下文生成报告，落库到 `memory/visitor_reports.db`；LLM 摘要失败时回退规则报告。

**个性化游览推荐（tourism_recommendation_service + algorithm + schema）**：
- 独立入口，不接入聊天流、MCP 或 `nlp_cognitive_stream`；即使全局 `auth.enabled=false`，推荐路由也额外检查 `current_user()`，要求登录。
- 独立库 `memory/tourism_recommendation.db`，避免被 `tourism.db` 的 Excel 全量重建覆盖；`tourism_visit` 只用于初始化景点草稿和热度/满意度辅助。
- 后台维护景点、路线模板、停靠点、步行边、讲解素材、权重配置，支持全量 JSON 导入导出、景点 CSV/XLSX 导入导出、从旅游访问数据生成未启用草稿。
- 推荐算法为模板优先 + 动态兜底：按兴趣匹配、满意度、热度、时间适配、强度适配加权打分；不可用点位会尝试替换为同兴趣可用点位；无 LLM 时仍生成讲解重点和可播报话术。
- 推荐日志落 `recommendation_log`，保存 `request_json/result_json/score_breakdown_json`；用户偏好落 `recommendation_user_preference`，反馈落 `recommendation_feedback`。

**数字人库（digital_human_service + live2d_resource_service）**：
- **不入数据库**：数据模型持久化在 `config.json` 的 `digital_humans:{active_id, items[]}`，每项含 id/name/type(live2d|iframe|image)/cover_url/render_url/voice/tags/persona(10 字段)/enabled/时间戳。
- **写回策略**：数字人库、激活人设、配置提交和麦克风开关优先走 `save_config_sections()`，只替换指定顶层配置段；文件写入使用临时文件 + `os.replace` 原子替换。
- 激活时把 name/voice/persona 回写到 `attribute` 配置节点，并经 WS 10003 推送切换命令。
- id 约定：手工创建 `dh_<uuid12>`、Live2D 导入 `live2d_<slug>`、默认 `fay_default`。
- Live2D 导入：扫描 `FAY_LIVE2D_SAMPLES_ROOT`；未设置时扫描仓库内 `library/live2d/Samples`，目录下需存在 `Resources/<Model>/<Model>.model3.json`；render_url 指向 Live2D 渲染服务（默认 `http://127.0.0.1:5174?model=<名>`）。
- 封面存 `cache_data/digital_humans/covers/`（≤5MB，魔数校验）。
- ⚠️ `persist_config` 保存后仍触发全局 `load_config(force_reload=True)`；不同顶层段的并发写入可保留，编辑同一顶层段仍是最后写入者生效。新增写入口优先用 `save_config_sections()`，仅在确需整体替换时使用 `save_config()`。

**migrations/001_add_auth.py**（唯一迁移脚本，`python main.py --migrate` 触发）：为旧库补认证列、建审计表、给空密码用户灌默认密码（admin→admin123，其余→fay2026）；执行前备份 db，失败回滚还原。⚠️ 无版本登记表，幂等靠"列是否存在/值是否为空"条件；新迁移脚本需同步修改 `main.py:63-71` 的硬编码模块名。

**API 清单（看板/数字人/会话域）**：

| 方法 | 路径 | 功能 | 鉴权 |
|---|---|---|---|
| GET | /api/dashboard/overview | 8 个 KPI 总览（?range=7d\|30d\|week\|month） | JWT |
| GET | /api/dashboard/service-trends | 按日服务趋势 | JWT |
| GET | /api/dashboard/hot-topics | 热点话题 Top8 | JWT |
| GET | /api/dashboard/tourism | 旅游多维分析（多过滤参数） | JWT |
| GET | /api/dashboard/users | 用户指标（非 admin 邮箱脱敏） | JWT |
| POST | /api/dashboard/tourism/reimport | 强制重导旅游 Excel | admin |
| POST | /api/dashboard/explain | KPI 文字解读 | JWT |
| POST | /api/dashboard/visitor-report/generate | 生成游客感受度报告（range/start_ms/end_ms） | admin |
| GET | /api/dashboard/visitor-report/latest/list/\<id\> | 最新/列表/详情 | admin |
| GET | /api/dashboard/visitor-report/\<id\>/evidence | 报告依据消息 | admin |
| GET | /api/dashboard/visitor-report/\<id\>/export?format=md\|html | 导出报告 | admin |
| POST | /api/dashboard/visitor-report/action/\<id\>/status | 更新建议状态 | admin |
| GET | /api/digital-humans | 数字人列表（?keyword= ?type=） | admin |
| GET | /api/digital-humans/active | 当前激活数字人 | JWT |
| POST | /api/digital-humans | 创建数字人 | admin |
| PUT/DELETE | /api/digital-humans/\<id\> | 更新/删除（激活中禁删） | admin |
| POST | /api/digital-humans/\<id\>/activate | 激活（同步 attribute + WS 推送） | admin |
| POST | /api/digital-humans/\<id\>/cover | 上传封面 | admin |
| POST | /api/digital-humans/import-live2d-resources | 批量导入 Live2D 模型 | admin |
| GET | /digital-humans/covers/\<filename\> | 封面静态文件 | 公开 |
| GET | /digital-humans/live2d-resources/\<model\>/\<path\> | Live2D 资源静态文件（防穿越） | 公开 |
| GET/PUT/DELETE | /api/recommendation/preferences | 读取/保存/删除当前登录用户推荐偏好 | JWT（强制登录） |
| POST | /api/recommendation/recommend | 生成个性化路线（主路线 + 备选 + 时间线 + 讲解稿） | JWT（强制登录） |
| GET | /api/recommendation/history, /api/recommendation/history/\<id\> | 当前用户推荐历史/详情 | JWT（强制登录） |
| POST | /api/recommendation/feedback | 记录采纳/拒绝/评分反馈 | JWT（强制登录） |
| GET/POST | /api/recommendation/admin/attractions | 景点列表/创建 | admin（强制登录） |
| PUT/DELETE | /api/recommendation/admin/attractions/\<id\> | 更新/软删除景点 | admin（强制登录） |
| GET/POST | /api/recommendation/admin/templates | 路线模板列表/创建 | admin（强制登录） |
| PUT/DELETE | /api/recommendation/admin/templates/\<id\> | 更新/软删除模板 | admin（强制登录） |
| GET/POST | /api/recommendation/admin/templates/\<id\>/stops | 模板停靠点列表/创建 | admin（强制登录） |
| DELETE | /api/recommendation/admin/stops/\<id\> | 软删除停靠点 | admin（强制登录） |
| GET/POST | /api/recommendation/admin/edges | 路线步行边列表/创建 | admin（强制登录） |
| DELETE | /api/recommendation/admin/edges/\<id\> | 软删除路线步行边 | admin（强制登录） |
| GET/POST | /api/recommendation/admin/materials | 讲解素材列表/创建 | admin（强制登录） |
| DELETE | /api/recommendation/admin/materials/\<id\> | 软删除讲解素材 | admin（强制登录） |
| GET/PUT | /api/recommendation/admin/config | 推荐权重配置读取/更新 | admin（强制登录） |
| GET/POST | /api/recommendation/admin/export, /api/recommendation/admin/import | 全量 JSON 导出/导入 | admin（强制登录） |
| GET/POST | /api/recommendation/admin/attractions/export, /api/recommendation/admin/attractions/import | 景点 CSV/XLSX 导出/导入 | admin（强制登录） |
| POST | /api/recommendation/admin/initialize-attractions | 从 `tourism_visit` 初始化景点草稿 | admin（强制登录） |
| GET | /api/recommendation/admin/logs | 推荐日志列表 | admin（强制登录） |
| GET/POST | /api/chat-sessions | 列出/创建会话 | JWT |
| PUT/DELETE | /api/chat-sessions/\<id\> | 重命名/删除会话（id=0 为 legacy 默认会话） | JWT |
| POST | /api/adopt-msg, /api/unadopt-msg | 采纳/取消采纳回复进 QnA | JWT |

### 6.5 LLM 与 Agent

这是 Fay 的"大脑"。**统一入口为 `llm/nlp_cognitive_stream.py` 的 `question(content, username, observation, images)`**（3616 行大文件，由 `fay_core.py:671` 调用），同步返回最终文本，过程中经 stream_manager 按句流式推送。

> ⚠️ **CLAUDE.md 已过时**：其描述的 `chat_stream()`/`think_stream()` 接口在当前代码中**已不存在**；thinking LLM 也无独立配置，仅通过 `_remove_think_from_text` 兼容 DeepSeek-R1 类 `<think>` 输出。

**大小模型协作架构**（核心设计）：

```
question() 三种分流（取后台结果 / 后台运行中意图分类 / 正常流程）
│
├─ 小模型规划器 _call_planner_llm (L977，gpt_model_engine，流式)
│   输出 JSON：{"action":"finish","message":...} → 直接分句流式回复
│             {"action":"tool","keyword":...}   → 推过渡语"我来帮你查一下，稍等…"
│                                                 → ExecutionManager.submit 后台执行
├─ 大模型执行循环 _big_model_execute (execution_manager.py:415)
│   big_model_engine（非流式，未配置降级小模型），"决策→调 MCP 工具→再决策"
│   最多 30 步，同名同参防重复；线程名 big-model-exec-<username>
│   完成回调 _auto_reply_after_execution：小模型在原 conversation_id 续写最终回复
│   （含 <think> 执行日志 + RAG 引用段落）
│
├─ 兜底核实：闲聊 finish 超 80 字且有工具可用 → 推"等等，我再帮你核实一下…"
│   → 以 unverified_response 提交后台核实模式（用户会看到两段式回复）
│
└─ 后台运行中收到新消息 → 小模型意图分类
    （update_task / query_progress / cancel_task / new_task / normal_chat）
```

> ⚠️ **LangGraph 图是遗留代码**：`_build_workflow_app`（plan_next ⇄ call_tool 双节点图，L1338）的唯一使用方 `run_workflow` 已无调用点，实际工具执行走 ExecutionManager；但 langgraph 不可用时仍会禁用全部工具（L2642），依赖仍是硬性的。

**仿生记忆**（genagents/ + simulation_engine/，基于 Generative Agents 论文）：

- `GenerativeAgent` = 人设 scratch（从 config.json attribute 实时加载）+ `MemoryStream`。
- 检索：`retrieve()` 按 recency（0.99 衰减）/relevance（余弦）/importance（LLM 评分）三因子加权（hp=[0.8,0.5,0.5]）取 30 条，按 observation/conversation/reflection 分组注入系统提示。
- 写入铁律：**锁外算（LLM 重要度评分 + embedding）→ 持 `agent_lock` 写 → 锁外刷盘**。曾因持锁发起网络调用导致机器 5 小时无响应（`nlp_cognitive_stream.py:2014` 注释）。`gpt_structure.py` 的 openai client 必须显式 timeout=60s/max_retries=1。
- 定时任务（`init_memory_scheduler`，L1794）：每天 23:00 按星期主题反思、0:00 持久化（另有 60s 节流的 save）、11:30 用户画像分析（结果写 `member_db.user_portrait`，下次对话注入提示）。
- 持久化：`memory/<user>/memory_stream/{nodes.json, embeddings.json, meta.json}`；清除记忆有双重标记（内存标志 + `memory/.memory_cleared` 文件），**清除后必须重启**。
- tags 命名空间：`kind:/source:/domain:/session:/date:/schedule:`。

**Embedding**（`utils/api_embedding_service.py` 线程安全单例）：

- `embedding_api_base_url` 为 `"local"`（或模型路径存在）→ `LocalEmbeddingBackend`（sentence-transformers 优先，transformers CLS 兜底，`EMBEDDING_DEVICE`/cuda 自动选择）；否则 → `OpenAIEmbeddingBackend`（URL 自动规范化为 `/embeddings`，指数退避）。
- ⚠️ 失败回退 **SHA256 种子确定性模拟向量**——不报错但检索质量静默劣化。
- 切换模型后维度不一致由 `precheck_embedding_dimensions` 启动时自动重算修复。
- Flask 5000 暴露 OpenAI 兼容 `/v1/embeddings` 透传端点（yueshen_rag 默认消费）。

**RAG 引用**（`llm/rag_citations.py`）：MCP 工具结果 metadata 含 `source`/`page` → 行内"引用来源：xxx 第N页"标记 → 回复末尾汇总"依据：1. ..."清单。**工具只要返回 metadata.source/page 即自动获得引用**，无需改 LLM 模块。

**多模态图片**：前端 POST `/api/upload-image`（≤20MB）→ `ImageStorage` 存 `cache_data/images/<user>/<date>/`（默认保留 7 天）→ 返回 `/api/get-image/...` URL → `_build_dialogue_messages` 调 `multimodal_image.image_ref_to_llm_url` 转 **base64 data URL** 内联进 OpenAI 多模态消息（大图显著膨胀 token）。

**本地知识库**：`llm/data/` 目录的 docx/doc/pptx/txt，启动时加载并按 mtime 热更新；`.doc` 依赖 Windows Word COM 组件。

**其他要点/坑**：
- 模块级小模型 `llm` 实例在导入时创建，改 system.conf 模型配置后**需重启**。
- 每用户同时只能一个后台任务（submit 返回 False），新任务被反问确认而非排队。
- 重要度评分解析失败返回 50、fail_safe 25（上游遗留的尺度不统一）。
- ≤8 字问候词跳过记忆检索（`_is_current_only_turn` 白名单，L96-128）。
- LLM 决策 JSON 解析兼容三种格式（纯 JSON/混合文本/XML tool_call），统一先 `_remove_think_from_text` + `_strip_json_code_fence`。
- genagents/simulation_engine 沿用上游论文代码风格（2 空格缩进、英文 docstring），Fay 自有代码 4 空格 + 中文注释。
- `genagents/genagents_flask.py`：独立"人格克隆决策访谈"Flask 服务（默认 5001，经 `/api/start-genagents` 启动），问卷写入记忆后需重启 Fay。
- `utils/openai_api/api_server.py`：ChatGLM3-6B 离线 OpenAI 兼容服务**参考实现**（FastAPI，/v1/models、/v1/chat/completions、/v1/embeddings），不被主流程 import。

### 6.6 MCP 集成

faymcp 是 MCP（Model Context Protocol）集成层，**四个层面**：

1. **`faymcp/mcp_service.py`** — MCP 管理 Flask 服务（gevent，**独立端口 5010**，⚠️ CLAUDE.md 称"5000 的子路由"已过时）：服务器 CRUD、连接/断开、工具/资源启停、预启动配置、工具调用；`before_request` 做 Bearer+admin 鉴权（auth_enabled 时）；autostart 服务器启动 2 秒后自动连接；**定时断线重连已被注释停用**（`mcp_service.py:1768`）。
2. **`faymcp/mcp_client.py`** — McpClient 兼容 SSE 与 stdio 双协议；每实例一条专属 asyncio 事件循环线程，同步 API 经 `run_coroutine_threadsafe` 包装（超时：init/list 30s，call 90s）；每 60 秒后台刷新工具列表；stdio 子进程 stderr 落盘 `logs/mcp_stdio_*.log`；PyInstaller 打包时改用 `sys.executable --mcp-stdio-runner` 启动；disconnect 用 wmic/taskkill 或 pkill 按命令行子串强杀子进程（有误杀同名进程风险）。
3. **`faymcp/mcp_server.py`** — 内置 MCP SSE 服务器（Starlette+uvicorn，默认 **0.0.0.0:8765**，路由 `GET /sse` + `POST /messages`，无鉴权）：暴露 `broadcast_message`（POST 回 Fay 5000 的 `/transparent-pass` 实现数字人播报）、7 个 `memory_*` 记忆工具（asyncio.to_thread 进程内直调 `core.memory_service`），并把所有已连接外部服务器的启用工具以 `server_id:tool_name` 命名空间聚合转发。
4. **`faymcp/runtime_bridge.py`** — LLM 管道的**进程内直调通道**（`nlp_cognitive_stream.py:58` import 为 `mcp_runtime`）：工具列表、预启动工具、资源文本注入（启用资源拼接上限 8000 字符进 system prompt）、call_tool 转发，避免回环 HTTP。

**三个内存注册表**（模块级单例 + RLock，**要求同进程**）：`tool_registry`（工具快照与"启用且可用"聚合缓存，同名工具按 last_checked 新者胜出）、`resource_registry`（资源文本缓存）、`prestart_registry`（预启动配置，params 模板支持 `{{question}}` 占位符）。

**持久化**（faymcp/data/，JSON，server_id 内存为 int / JSON 键为 str）：`mcp_servers.json`（服务器配置，status/latency 不持久化、启动一律重置 offline，**想自动恢复连接必须 autostart=true**）、`mcp_tool_states.json`（工具启停，缺省启用）、`mcp_resource_states.json`、`mcp_prestart_tools.json`。

**`faymcp/kb_routes.py`** — 知识库 Blueprint（`/api/kb/*`，挂在 5010）：管理 `library/` 目录 .docx/.pdf（白名单+路径穿越防护），ingest/query/stats 调用在线的 yueshen_rag MCP 服务器工具（`skip_enabled_check=True`）；写接口要求同源或本机。

**自带 stdio MCP 服务器**（mcp_servers/，统一样板：`_runtime_dir/_project_root` 双函数支持 PyInstaller，**日志写 stderr 保持 stdout 干净**）：

| 目录 | 工具 | 说明 |
|---|---|---|
| schedule_manager | add/get/update/delete_schedule、send_message_to_fay | SQLite schedules.db；到点经 5000 `/api/schedule/notify` 通知 Fay；连接时拉起 5011 独立日程网页子进程 |
| yueshen_rag | ingest_yueshen/query_yueshen/yueshen_stats | 语料 library/，Chroma 存 cache_data/chromadb_yueshen；embedding 默认走 Fay 5000 `/v1` 透传 |
| window_capture | list_windows/capture_window | Windows 窗口截图（最简参考实现） |
| logseq | search_text/read_page/create_page 等 9 个 | 需环境变量 LOGSEQ_GRAPH_DIR |
| fay_player_knowledge | kb_search/kb_get_catalog 等 8 个 + resources | **手写 JSON-RPC stdio 协议**不依赖 mcp 库；内置图片 HTTP 服务 |

**关键数据流**：
- 连接：`connect_to_real_mcp` → McpClient.connect → list_tools → `_sanitize_tools` → tool_registry（注水持久化 enabled）→ 资源全文缓存进 resource_registry。
- LLM 调用：`runtime_bridge.call_tool` → `mcp_service.call_mcp_tool`（检查启用态）→ McpClient.call_tool（90s 超时）。
- 预启动：LLM 调用前 `_run_prestart_tools` → 在线且可用的预启动工具 → `{{question}}` 替换 → 结果按 include_history/allow_function_call 并入上下文。⚠️ **预启动一律 skip_enabled_check=True，禁用工具也会执行**。
- 知识库：上传 .docx/.pdf → `/api/kb/ingest` → yueshen ingest（切块+embedding 走 5000 `/v1` → 写 Chroma）→ `/api/kb/query` 语义检索。

**已确认的真实 bug / 坑**：
- ⚠️ `mcp_service.add_mcp_server` 的 auto_connect 分支引用未定义变量 `server_id`（`mcp_service.py:544/563/571/581`，应为 new_id），连接成功且有工具时必然 NameError 被吞、服务器误标 offline。
- ⚠️ `llm/execution_manager.py:245` `from faymcp import mcp_runtime` —— 该模块名不存在（实际是 runtime_bridge），ImportError 被吞，执行器 knowledge_sources_hint 恒为空。
- `POST /api/mcp/servers/<id>/restart` 是假实现（仅改 status 字段）。
- **工具启停即时生效**（toggle 同时写 JSON 与 registry），⚠️ CLAUDE.md 所述"需重启 MCP 客户端"已过时。
- stdio 默认 cwd 是**项目根**而非服务器目录，args 相对路径相对项目根解析。
- faymcp 无 `__init__.py`（隐式命名空间包），打包时注意收集。
- mcp_tool_states.json 有历史脏键（元组字符串），现已被 `_sanitize_tools` 过滤。

**API 清单（5010 端口，auth_enabled 时一律需 Bearer+admin）**：

| 方法 | 路径 | 功能 |
|---|---|---|
| GET | /api/mcp/servers | 服务器列表（含运行时 status/latency） |
| POST | /api/mcp/servers | 新增（stdio: name+command；sse: name+ip；可选 auto_connect） |
| PUT/DELETE | /api/mcp/servers/\<id\> | 更新（auto_reconnect 重连）/删除 |
| POST | /api/mcp/servers/\<id\>/connect, /disconnect | 连接（发现工具/缓存资源）/断开 |
| POST | /api/mcp/servers/\<id\>/restart | ⚠️ 假实现 |
| POST | /api/mcp/servers/\<id\>/call | 调用工具 {method, params, is_prestart} |
| GET | /api/mcp/servers/\<id\>/tools, /resources | 工具/资源列表 |
| GET | /api/mcp/servers/online/tools | 聚合在线工具（去重） |
| POST | /api/mcp/tools/\<tool_name\> | 按名直调（首个拥有且启用者执行） |
| POST | /api/mcp/servers/\<id\>/tools/\<name\>/toggle | 工具启停（即时生效） |
| POST | /api/mcp/servers/\<id\>/resources/toggle | 资源启停 {uri, enabled} |
| POST | /api/mcp/servers/\<id\>/tools/\<name\>/prestart | 预启动配置 {enabled, params, include_history} |
| GET | /api/mcp/prestart/runnable | 可运行预启动工具 |
| POST | /api/mcp/prestart/call, /servers/\<id\>/prestart/\<name\>/call | 批量/单个预启动调用 |
| GET | /api/kb/files | 知识库文件列表 |
| POST | /api/kb/files/upload | 上传（+同源/本机校验） |
| DELETE | /api/kb/files/\<filename\> | 删除（+同源校验） |
| POST | /api/kb/ingest, /api/kb/query | 入库 / 语义检索 |
| GET | /api/kb/stats | 向量库统计 |
| GET | /Page3 | 旧版 MCP 管理页（Jinja2） |

### 6.7 语音子系统（ASR/TTS）

**ASR**（asr/，唯一消费者是 `core/recorder.py` 的 `asrclient()` 工厂，按 `system.conf ASR_mode` 选择，**每次说话激活都新建实例**）：

| 模式 | 实现 | 方式 | 备注 |
|---|---|---|---|
| ali | `asr/ali_nls.py` ALiNls | WebSocket 流式边录边传（wss 深圳网关） | token 每 12 小时刷新（缓存 T_Authorize 表）；每次 SentenceEnd 即 close（一连接一句，TODO 标注）；结果等待超时仅 1 秒 |
| funasr / sensevoice | `asr/funasr.py` FunASR | **非流式**：整段录音写临时 wav 后发 `{'url': 路径}` 给 `ws://{local_asr_ip}:{local_asr_port}` | sensevoice 无独立客户端完全复用 FunASR 类；超时 10 秒；`started` 恒为 True |

`asr/funasr/` 子目录是**需独立部署的 FunASR 服务端参考实现**（modelscope paraformer-zh + fsmn-vad + ct-punc-c，ws 端口 10197，支持热词），不被主程序 import。

**ASR 统一鸭子类型契约**：`__init__(username)` + `start()/send(buf)/end()` + `started/done/finalResults` 状态属性（recorder 轮询）。输入统一 16kHz/16bit/单声道 PCM（多声道在 recorder 平均混合）。识别中间/最终结果实时推送 10003 panelMsg 与 10002 数字人日志。

**TTS**（tts/，唯一调度方是 `fay_core.py:103-134` **模块导入期**按 `tts_module` 静态 import，`FeiFei` 持单例 `self.sp`，合成入口 `self.sp.to_sample(text, style)`，**运行时改配置必须重启**）：

| tts_module | 实现 | 输出采样率 | 坑 |
|---|---|---|---|
| （默认 fallback） | `ms_tts_sdk.py`：配 ms_tts_key 走 Azure，否则 edge-tts | 16k / 44.1k | 唯一真正使用 style 语义的实现 |
| ali | `ali_tss.py` | 16k | token 走 T_Authorize 缓存；SSL 校验被禁用 |
| volcano | `volcano_tts.py` | 24k | 手工套 wav 头；音色优先 volcano_tts_voice_type |
| gptsovits | `gptsovits.py` | 16k | 地址硬编码 127.0.0.1:9880 |
| gptsovits_v3 | `gptsovits_v3.py` | 32k | 地址 + **ref_audio_path 本机绝对路径全硬编码，换机必坏** |
| openai_tts | `openai_tts.py` | 44.1k | 地址硬编码 127.0.0.1:8080 |

**TTS 统一鸭子类型契约**（无公共基类）：每文件一个 `class Speech`，实现 `connect()/close()/to_sample(text, style) -> wav路径或None`；输出统一 `./samples/sample-<毫秒时间戳>.wav`；失败返回 None 并打 `[x] 语音转换失败！` 日志。音色取 `config.json attribute.voice`（volcano 例外）。

**要点/坑**：
- `style` 参数只对 azure 分支有实际语义，且 `__get_mood_voice` 固定返回 `styleList['calm']`（`fay_core.py:952`）——**情绪音色实际未按情绪切换**。
- TTS sha1 缓存 key 含 `tts_module|voice|style|text`，缓存的是 samples/ 文件路径，文件被清理自动失效。
- gptsovits/v3/volcano 直接给 response.content 套固定采样率 wav 头，服务端返回完整 wav 或采样率不符会双头/变速。
- `/audio/<filename>` 路由（数字人按 HttpValue 拉取音频）**无鉴权**，samples/ 可被枚举下载。
- `ai_module/` 仅剩 `baidu_emotion.py` 在用（fay_core 给音频消息算 Sentiment，未配密钥降级关键词分析）；`nlp_cemotion.py` 是**死代码**（import 但无调用）。
- 阿里 ASR/TTS、百度情感三方各自复制了一份近乎相同的 token 缓存代码（T_Authorize 表）。
- 麦克风采样率实际固定 16000（`RecorderListener` 注释"按设备更新"的代码被注释掉）。

**新增 TTS/ASR 实现的步骤**见各自 extension：TTS = 新建 `tts/xxx.py` 的 Speech 类 → config_util 加配置 → `fay_core.py:103` if/elif 链加分支 →（可选）flask_server `api_get_data` 加音色列表 → 改 system.conf 重启；ASR = 新建客户端类满足契约 → `recorder.py:59-64` 工厂加分支（文件式需同步改 send_url 调用与超时分支）→（可选）main.py 加预启动。

### 6.8 HTTP 接口层（API 总清单）

HTTP 层由**两个相互独立的 Flask 应用**组成：

1. **主管理服务器** `gui/flask_server.py`（0.0.0.0:5000，werkzeug make_server）：模块级 `__app`，以「注册函数 + app.config 防重入标志」方式（**非 Blueprint**）组装 auth/avatar/dashboard/digital_human/tourism_recommendation 五组路由，另承载 legacy 配置、消息、OpenAI 兼容等路由。
2. **MCP 管理服务器** `faymcp/mcp_service.py`（默认 127.0.0.1:5010，gevent pywsgi）：`before_request` 对 `/api/mcp/`、`/api/kb/` 前缀强制 Bearer+admin（auth_enabled 时）；知识库经**真正的 Blueprint**（`kb_routes.py`，全项目唯一）挂载。

**三套鉴权机制并存**：JWT Bearer（require_auth/require_role，auth.enabled=false 时整体放行）、首页专用 HTTPBasicAuth（verifier.json，仅 `/`）、MCP app 的 before_request 钩子。

`gui/window.py`：PyQt5 桌面窗口（仅 start_mode=common），QWebEngineView 内嵌加载 `http://127.0.0.1:5000`；关闭按钮默认最小化托盘，真正退出走托盘 Exit → `os._exit(0)`；`TDevWindow` 是遗留调试类未被使用。

**约定**：响应体风格不统一（存在 `{'result':'successful'}` / `{'success':True}` / `{'status':'success'}` / 裸 json.dumps 四种），新增接口跟随所在文件主流风格；用户私有数据访问统一经 `_forbid_unless_self_or_admin` / `_forbid_unless_session_owner` 收口；OpenAI 兼容接口均有 `/v1/...` 与 `/api/send/v1/...` 双别名；页面路由经 `__get_vue_app()` 返回 Vue SPA（dist 缺失回退 legacy 模板）；两个 app 均禁用 werkzeug 日志。

**疑似 bug（接口层）**：
- ⚠️ `flask_server.py:1311` `/api/delete-user` 引用未导入的 `nlp_cognitive_stream` → NameError 被吞，**agent 缓存清理从不生效**。
- `/v1/chat/completions` 的 model 参数决定路径：`fay`/`fay-streaming` 走内部 Agent 管道、`llm` 反代 system.conf 配置模型、其他值透传上游——易误以为都走 Fay；若内部管道不产出 `_<isend>`，流式/非流式响应会**永久挂起**（无限轮询 stream_manager）。
- KB 写接口的同源校验基于 Origin/Referer，反向代理部署 Origin 与 Host 不一致会 403。
- `verifier.json` 只在模块导入时加载一次，运行期修改不生效。

#### 5000 端口 完整 API 清单

**页面与静态资源（无鉴权，除 `/` 为 HTTPBasic）**：`GET/POST /`、`GET /setting`、`/live2d`、`/dashboard`、`/visitor-report`、`/recommendation`、`/recommendation/manage`、`/knowledge`、`/mcp`（Vue SPA）、`/assets/<path>`（dist 资源）、`/Page3`（legacy MCP 页）、`/audio/<filename>`（TTS 音频，⚠️ 无鉴权可枚举）、`/robot/<filename>`（表情 GIF）、`/avatars/<filename>`（头像）、`/digital-humans/covers/<filename>`、`/digital-humans/live2d-resources/<model>/<path>`。

**配置与服务控制**：

| 方法 | 路径 | 功能 | 鉴权 |
|---|---|---|---|
| POST | /api/submit | 合并保存 config.json 并热加载 | admin |
| POST | /api/get-data | 完整配置 + TTS 音色列表（并经 WS 10003 推 voiceList/liveState） | admin |
| POST | /api/start-live, /api/stop-live | 启动/停止 Fay 核心（fay_booter） | admin |
| POST | /api/get-run-status | 服务运行状态 | 无 |
| GET | /api/get-system-status | 数字人 WS/远程音频连接状态 | 无 |
| GET | /api/get-audio-config | 麦克风/扬声器开关 | 无 |
| POST | /api/toggle-microphone | 开关麦克风并持久化 | admin |

**消息与会话**：

| 方法 | 路径 | 功能 | 鉴权 |
|---|---|---|---|
| POST | /api/send | 发送文字消息（Interact→on_interact） | JWT（本人或 admin） |
| POST | /api/get-msg | 分页历史消息（含图片/采纳状态） | JWT（本人或 admin） |
| POST | /api/get-msg-by-id | 按 ID 取单条消息 | JWT（所属用户或 admin） |
| GET/POST | /api/chat-sessions | 列出/创建会话 | JWT |
| PUT/DELETE | /api/chat-sessions/\<id\> | 重命名/删除会话 | JWT（会话所有者或 admin） |
| POST | /api/adopt-msg, /api/unadopt-msg | 采纳/取消采纳进 QnA | admin |
| GET | /api/execution-status | 后台工具执行状态（3 秒轮询） | JWT（本人或 admin） |
| POST | /api/execution-cancel, /api/execution-modify | 取消/注入修改后台任务 | JWT（本人或 admin） |

**OpenAI 兼容接口**（双别名 `/v1/...` 与 `/api/send/v1/...`）：

| 方法 | 路径 | 功能 | 鉴权 |
|---|---|---|---|
| GET | /v1/models | 模型列表（fay/fay-streaming/llm + 上游） | 无 |
| POST | /v1/chat/completions | model=fay* 走内部 Agent 管道（SSE 流式/多模态/no_reply）；llm 反代上游 | JWT |
| POST | /v1/embeddings | embedding 透传（api_embedding_service，yueshen_rag 默认消费） | 无 |

**成员与画像**：

| 方法 | 路径 | 功能 | 鉴权 |
|---|---|---|---|
| POST | /api/get-member-list | 成员列表（非 admin 仅见自己） | JWT |
| POST | /api/add-user, /api/delete-user | 添加/删除聊天成员（⚠️ delete 的 agent 清理有 bug） | admin |
| POST | /api/get-user-extra-info, /api/update-user-extra-info | 用户补充信息（附加到提示词） | JWT（本人或 admin） |
| POST | /api/get-user-portrait, /api/update-user-portrait | 用户画像（每天 11:30 自动分析） | JWT（本人或 admin） |

**交互控制（⚠️ 全部无鉴权）**：`POST /to-greet`（打招呼）、`/to-wake`（设唤醒标记）、`/to-stop-talking`（打断）、`/transparent-pass`（透传播报，内置 MCP broadcast_message 的下游，支持 queue 队列模式）。

**记忆与 Agent**：`POST /api/clear-memory`（清记忆，需重启，admin）、`POST /api/start-genagents`（5001 端口拉起人格克隆访谈服务，admin）。

**图片（⚠️ 全部无鉴权）**：`POST /api/upload-image`（≤20MB）、`GET /api/get-image/<user>/<date>/<file>`（防穿越）、`GET /api/list-user-images`、`POST /api/cleanup-images`、`GET /api/image-storage-stats`；另有 `GET /api/local-image`（**按绝对路径读服务器任意图片**，仅扩展名白名单）、`POST /api/open-image`（**在服务器上用默认程序打开图片**）——这两个属高危接口。

**认证/用户/审计/头像**：见 6.3 的 API 表。**看板/数字人**：见 6.4 的 API 表。

#### 5010 端口 完整 API 清单

见 6.6 的 API 表（/api/mcp/* 与 /api/kb/*，外加 `/`→`/Page3` legacy 页面）。

---

## 7. 前端 fay-frontend

### 7.1 架构与网络通道

Vue 3.4 + TS 5.3.3（strict）+ Vite 5 + Pinia 2 + vue-router 4 + Element Plus 2.5（main.ts 全量引入）+ axios + Vitest。**无路径别名**（全相对导入）；构建 `npm run build` 前置 `vue-tsc --noEmit` 类型检查。

**三条网络通道**：

| 通道 | 目标 | 封装 | 说明 |
|---|---|---|---|
| 主 axios 实例 | Flask 5000 | `api/request.ts` | dev 经 Vite 代理（/api /v1 /audio /robot /static /avatars 六前缀）；15s 超时；拦截器注入 Bearer、解包 response.data、**401 时 `window.location.href` 硬跳 /login**（有意设计，彻底重置内存态） |
| MCP/知识库独立 axios | **直连 5010**（`http://hostname:5010`，VITE_MCP_API_BASE_URL 可覆盖） | `api/mcp.ts`、`api/knowledgeBase.ts` | **绕过 Vite 代理**，依赖后端 CORS；⚠️ **无 401 登出逻辑**，token 过期只报错 |
| UI WebSocket | 10003 | `utils/websocket.ts` ReconnectingSocket | 默认 `ws(s)://hostname:10003`（编译期常量 `__FAY_WS_URL__` ← VITE_WS_URL）；onopen 发注册帧 `{Username, token}`；固定 5 秒重连（**无指数退避**；token 过期被 1008 拒绝会无提示死循环重试） |

**环境变量**（仓库无 .env，全走默认值）：`VITE_API_BASE_URL`（dev 代理目标）≠ `VITE_API_BASE_PATH`（运行时 axios baseURL，**易混**）、`VITE_PORT`、`VITE_WS_URL`、`VITE_MCP_API_BASE_URL`、`VITE_LIVE2D_URL`。

**旧协议兼容**：`/api/send`、`/api/get-msg`、`/api/submit` 等 legacy Flask 接口**必须用 `postLegacyData`**（JSON 序列化进 form 字段 `data`，x-www-form-urlencoded）；新接口（auth/users/dashboard/digital-humans/chat-sessions）用标准 JSON。

### 7.2 路由、守卫与 Store

**路由**（`router/index.ts`，全懒加载）：`/login`（公开）+ AppLayout 嵌套 10 子页：`/`（Message）、`/setting`、`/live2d`、`/dashboard`、`/visitor-report`、`/recommendation`、`/recommendation/manage`、`/knowledge`、`/mcp`、`/users`。

**守卫**（`router/guards.ts`）：`meta.requiresAuth !== false` 即默认**所有路由需认证**（新公开页必须显式 `requiresAuth: false`）；token 存在但 user 为空时先 `refreshUser()`（GET /api/auth/me）；`requiresRole: 'admin'` 非管理员重定向消息页。

**Pinia store（全部 setup 风格）**：

| store | 职责 | 要点 |
|---|---|---|
| `auth.ts` | token/user 持久化（localStorage `fay_token`/`fay_user`）、login/logout/refreshUser/isAdmin | ⚠️ persist() 硬编码 'fay_token' 字符串而非常量 |
| `app.ts` | 成员列表/选中用户、**liveState 四态状态机**（0 未开启/1 运行中/2 正在开启/3 正在关闭）、声音列表、系统状态、音频开关（乐观更新失败回滚）、会话、`receiveWebsocketPayload` WS 分发中心 | configEditable 仅 liveState===0；startLive 失败停留中间态 2 无回滚；非 admin 的 panelReply 按用户名过滤、用户列表强制收敛为自己 |
| `live2d.ts` | 数字人列表/激活 ID/iframeUrl（默认 http://127.0.0.1:5174）、WS 推送 upsertHuman 合并 | loadBootstrapData 会跨 store 把 config.digital_humans 灌入此 store |

### 7.3 页面与组件

**views/（10 个 AppLayout 子页面 + Login）**：

| 页面 | 功能 | 关键依赖 |
|---|---|---|
| Message.vue | 三栏聊天（SessionPanel 会话 / MessageList 消息流 / DigitalHumanPanel 数字人）、分享图、think/prestart 折叠、WS 增量合并（watch panelReplySeq → mergePanelReply） | useChatSessions、useMessageSubmit |
| Setting.vue | 人设/声音交互/自动播报三段表单，hydrate/toConfig 双向映射 FayConfig；**仅 liveState===0 可编辑**；⚠️ 保存会把 `memory.use_bionic_memory` 硬编码 false、items 置空 | api/setting.ts |
| Live2D.vue | 数字人库卡片网格 CRUD、封面上传、激活、导入本地 Live2D、iframe 预览 | live2d store、DigitalHumanEditor 抽屉 |
| Dashboard.vue | 看板（KPI/趋势/热门问答/游客感受度/景区/画像/明细），手写 CSS 条形图+SVG 折线，LLM 解读，admin 可重导 Excel/生成游客报告 | api/dashboard.ts |
| VisitorReport.vue | 独立游客感受度报告页，复用 VisitorReportPanel，侧边栏 `/visitor-report` 入口 | components/dashboard/VisitorReportPanel.vue |
| Recommendation.vue | 登录用户个性化游览推荐入口，采集兴趣/时间/强度/同行/预算/避开项，展示主路线+备选、时间线、讲解重点、可播报话术、复制/打印/导出/反馈 | api/recommendation.ts |
| RecommendationManage.vue | admin 推荐数据维护，景点/模板/停靠点/步行边/讲解素材/权重/日志/初始化/JSON+CSV+XLSX 导入导出，支持表格行回填编辑与软删除 | api/recommendation.ts |
| KnowledgeBase.vue | library 文件管理、ingest、检索测试 | **走 5010** api/knowledgeBase.ts |
| Mcp.vue | MCP 服务器 CRUD/连接/工具与资源启停（McpServerList/Detail/Dialog 三子组件，行级 loading 用 actionKey 字符串） | **走 5010** api/mcp.ts |
| UserManagement.vue | 用户表格（角色切换/启停/重置密码/删除）、新建弹窗、审计日志 | api/users.ts（admin） |
| Login.vue | 登录/注册双模式，登录后按 ?redirect= 跳转 | authStore |

**components/** 按业务域分子目录（auth/messages/mcp/digital-humans），全部 props+emits 展示型；双向绑定用 `v-model:visible`/`defineModel`；父调子用 `defineExpose`。

⚠️ **成套遗留死代码**（无任何视图引用，Message 改造为会话模式后废弃未删）：`UserPanel.vue`、`TaskPanel.vue`、`UserInfoDialog.vue`、`useExecutionStatus.ts`、`useUserInfoEditor.ts`、`useAuth.ts`。

**composables/**：`useChatSessions`（会话加载/自动创建/重命名删除）、`useMessageSubmit`（纯文本走 legacy /api/send；带图片先逐张 /api/upload-image 再手动 fetch /v1/chat/completions 多模态，500ms 后刷新历史靠 WS 补齐最终一致）、`useAudioControlActions`（音频开关包装）、`useRecommendationManage`（推荐维护页景点/模板/停靠点/步行边/素材/权重/导入导出逻辑）。

**样式**：`styles/main.css` 按 base→layout→components→页面级→markdown→responsive→element-override 顺序 @import 14 个全局分层 CSS；推荐页样式在 `styles/recommendation.css`；设计令牌在 `base.css`（Apple 配色 `--color-*` 变量、SF Pro/PingFang 字体栈）；类名 kebab-case 带页面前缀（mcp-、kb-、dashboard-、recommendation-...）；scoped 仅用于组件独有微样式。

### 7.4 实时通信与核心工具（utils/）

- **WS 协议无统一 Type 字段**：按顶层字段存在性分发（liveState/panelMsg/panelReply/voiceList/digitalHuman/is_connect/remote_audio_connect），`receiveWebsocketPayload` 用 `!== undefined` 逐字段判断。
- **流式渲染**：`messageStream.ts mergePanelReply` 按 (id,type,session_id,username) 匹配做 content 字符串拼接。⚠️ 依赖增量帧按序到达，无去重/排序；后端 `is_end` 字段**前端未消费**；断线期间丢失的增量不重放，需手动拉历史。
- **内容解析**：`messageContent.ts` 提取 `<think>`/`<prestart>` 标签折叠展示；Markdown 先 escapeHtml 再 marked（防注入，但合法 HTML 也无法渲染）；LLM 回复中的 Windows 绝对图片路径转 `/api/local-image?path=` 缩略图，点击调 `/api/open-image` **在服务器本机打开**。
- **重型库不走 npm**：marked 与 html2canvas 从 Flask `/static/js/*.min.js` 懒加载挂 window——**后端不在线时 Markdown 降级纯文本、分享图失败**；marked 加载完成靠 renderVersion 自增强制重渲染。
- **Live2D 渲染不在本仓库**：`Live2D.vue`/`live2d.css` 名不副实，实际是数字人库管理页；真正渲染由外部 Cubism SDK for Web 应用（5174 端口，仓库外目录 `D:\Fay\mate-human\...`）通过 sandbox iframe 完成（`sandbox="allow-scripts allow-same-origin"` 组合实际不设防）。数字人 WS 推送**仅 activate 触发**，创建/更新/删除不推送。
- 其他：`audioControls.ts`（构造后端配置补丁，非浏览器音频）、`webgl.ts`（WebGL 探测）、`shareSelection/shareImage`（分享图选择与 html2canvas 导出）、`navigation.ts`（菜单高亮）。
- ⚠️ `UserRecord` 是元组类型 `[uid, username, avatar?]`，取 username 用下标 `[1]`；后端用户消息 type 为 `'member'`，前端把所有非 `'fay'` 类型按用户气泡渲染（隐式约定）；`getMessageHistory` 对返回做了 `.flat()`（后端可能返回嵌套数组）。

### 7.5 前端测试与新增页面步骤

**测试**：Vitest，测试文件与源文件同目录同名 `.test.ts`（utils/stores/api 均有）；vite.config 无 test 块 → **默认 node 环境**，window/localStorage/WebSocket/`__FAY_WS_URL__` 都要手动 stub；store 测试用 `vi.mock` api 模块 + `setActivePinia(createPinia())`。

**新增页面标准步骤**：types 定义 → `src/api/` 新建域文件（5010 端口仿 mcp.ts 自建实例）→（可选）setup store + 同目录测试 → `src/views/` 页面组件（错误用 `ElMessage.error(error instanceof Error ? error.message : '兜底文案')`，危险操作 ElMessageBox.confirm）→ router 注册懒加载路由（meta.requiresAuth，admin 加 requiresRole）→ `AppLayout.vue navItems` 加菜单项（lucide 图标）→ 页面级 CSS 进 styles/ 并插入 main.css @import 链 →（可选）WS 推送在 types WebsocketPayload + app.ts receiveWebsocketPayload 加分支 → `npm run test` + `npm run build` 验证。

---

## 8. WebSocket 协议规范

### 8.1 ws://host:10002（数字人接口，HumanServer）

下行消息统一结构：`{"Topic":"human","Data":{...},"Username":"xx","robot":"http://.../robot/Speaking.jpg"}`，按 `Data.Key` 区分：

| Key | 含义 | 关键字段 |
|---|---|---|
| question | 用户问题原文 | Value |
| log | 状态文本（"思考中..."/"唤醒成功！"） | Value |
| text | 流式回复文本 | Value, IsFirst, IsEnd, Images[] |
| audio | 音频驱动 | Value（本地路径）, HttpValue（http://fay_url/audio/xx.wav）, Text, Time（秒）, Type, IsFirst, IsEnd, CONV_ID, CONV_MSG_NO, **Sentiment**（-2~2）, **Action**（{code,behavior,affect,intensity,priority,matchedKeywords,sentimentHint}）, **Lips**（唇形 visemes）, Images[] |

上行：`{"Username":"用户名","Output":true|false}` 绑定身份并声明是否需要服务端推送音频（Output 影响是否做 TTS）。

### 8.2 ws://host:10003（UI 面板接口，WebServer）

| 下行类型 | 结构 |
|---|---|
| panelMsg | `{"panelMsg":"思考中...","Username":"xx","robot":"...jpg"}`（日志区状态） |
| panelReply | `{"panelReply":{"type":"member\|fay","content":"文本","username","uid","id":content_id,"timetext","images":[],"is_end":bool,"is_adopted":bool,"session_id"},"Username":"xx"}`（聊天消息，流式分片） |
| is_connect | `{"is_connect":true}`（数字人在线状态） |
| remote_audio_connect | `{"remote_audio_connect":bool,"Username":"xx"}` |
| liveState / voiceList / digitalHuman | 服务运行状态 / 声音列表 / 数字人切换 |

上行：`{"Username":"xx"}` 绑定/切换面板用户。

**通用规则**：消息含 `Username` 字段则定向推送、缺省群发（`wsa_server.py:111-123`）。鉴权：默认无；`auth.enabled=true` 时连接后 10 秒内首条消息须为 `{"token":"<JWT>"}`，否则以 1008 关闭。⚠️ 未启用认证时首条 `{"Username"}` 即可冒用任意用户身份。

### 8.3 ws://host:9001 / tcp://host:10001（远程音频通道）

WS 9001 由 `socket_bridge_service` 透明桥接到 TCP 10001，协议语义相同（原始字节流）：
- 握手：先发 `<username>xx</username>` 与 `<output>True<output>`（⚠️ 非闭合写法 `<output>True<output>` 是刻意的，与 `fay_booter.py:161` 正则匹配；写成 `</output>` 反而失败；Output=True 才会收到回送音频）。
- 上行：16kHz/16bit/单声道原始 PCM。
- 下行：`\x00..\x08`（9 字节递增）= 音频开始；`\x08..\x00`（递减）= 结束；`\xf0..\xf8` = 心跳（每 10 秒）。
- 参考客户端：`skills/remote_audio_key0.py`（Windows 按住 0 键拾音）、`test/test_remote_audio_websocket_9001.py`。

---

## 9. 数据存储总表

| 存储 | 位置 | 内容 | 主要读写方 |
|---|---|---|---|
| **fay.db** | memory/ | T_Msg（对话，毫秒时间戳）、T_ServiceSession（会话）、T_Adopted（采纳，秒）、T_Authorize（云 token 缓存） | content_db、dashboard_operational、nlp_cognitive_stream、authorize_tb |
| **user_profiles.db** | memory/ | T_Member（用户，含 bcrypt hash/role/avatar_path/extra_info/user_portrait）、T_AuditLog（审计，秒） | member_db、audit_service、auth、dashboard |
| **tourism.db** | memory/ | tourism_visit（旅游行为，全量重建）、tourism_import_log | dashboard_tourism |
| **visitor_reports.db** | memory/ | visitor_experience_report、visitor_interaction_analysis、visitor_report_action | visitor_report_service |
| **tourism_recommendation.db** | memory/ | recommendation_attraction、recommendation_route_template、recommendation_route_stop、recommendation_route_edge、recommendation_explanation_material、recommendation_config、recommendation_user_preference、recommendation_log、recommendation_feedback、recommendation_import_log | tourism_recommendation_service |
| **记忆流** | memory/\<username\>/memory_stream/ | nodes.json + embeddings.json（仿生记忆） | memory_service、genagents、nlp_cognitive_stream |
| **JWT 密钥** | memory/.jwt_secret | 自动生成的签名密钥（删除则全部 token 失效） | auth_service |
| **config.json** | 根目录 | 含数字人库（程序回写！） | digital_human_service、config_util |
| **qa.csv** | 根目录（路径由 interact.QnA 配置） | QnA 问答对（采纳写入；第三列为可选命令动作，默认禁用） | qa_service |
| **mcp_servers.json / 工具状态** | faymcp/data/ | MCP 服务器注册与工具启停持久化 | mcp_service |
| **schedules.db** | mcp_servers/schedule_manager/ | 日程表（server.py 与 web_server.py 两进程共享） | schedule_manager |
| **ChromaDB** | YUESHEN_PERSIST_DIR | RAG 向量库 | yueshen_rag |
| **头像/封面/图片** | cache_data/avatars/、cache_data/digital_humans/covers/ 等 | 上传文件（旧文件不清理） | avatar_routes、digital_human_routes |
| **知识库原文** | library/ | 上传的 Word/文本文档 | kb_routes、yueshen_rag |

约定：表名前缀 `T_` 大驼峰（新表 tourism_visit 改用小写下划线）；数据访问类一律「模块级单例 `new_instance()` + `@synchronized`（RLock）+ 每方法独立 sqlite3 短连接」；schema 演进用启动时自愈（CREATE IF NOT EXISTS + PRAGMA 比对 + ALTER ADD COLUMN）。⚠️ 时间戳不统一：fay.db 毫秒、user_profiles.db/T_Adopted 秒。

---

## 10. 测试与工程化

### 10.1 后端测试（test/，双轨制）

**不使用 pytest**（全仓库无 pytest 配置与 import）。AGENTS.md 明确约定**脚本式测试**：每个文件可 `python test/test_<feature>.py` 直接运行。三类：

1. **冒烟脚本**：需真机麦克风/扬声器和已启动服务（如 `test_remote_audio_websocket_9001.py`，9001 协议参考客户端），不能在 CI/无头环境跑。
2. **unittest 单元/路由测试**（16 个文件带 `unittest.main()`）：依托 **`test/user_management_test_helpers.py` 的 `TempProjectMixin`** —— 临时项目目录（自动生成 system.conf/config.json）、stub pyaudio/fay_booter 等硬件模块、重置 17 个单例模块；路由测试经 `getattr(flask_server, '__app')` 取私有 Flask 实例的 test_client（**直接写 `flask_server.__app` 会触发名称改写**）。
3. **node:test 脚手架测试**（`.mjs`）：对前端源码做存在性与正则断言，须在项目根运行 `node --test test/xxx.mjs`。

**统一惯例**：文件头注入 `PROJECT_ROOT` 到 sys.path（三行样板）；需 Flask/auth 环境就继承 `TempProjectMixin + unittest.TestCase`（Mixin 在前）。

⚠️ **gitignore 白名单陷阱**：`test/` 在 .gitignore 中是白名单模式，当前白名单包含 `test_digital_human_service.py`、`test_digital_human_routes.py`、`test_dashboard_service.py`、`test_qa_service.py`、`test_visitor_report_service.py`、`test_visitor_report_routes.py`、`test_tourism_recommendation_service.py`、`test_tourism_recommendation_routes.py`、`user_management_test_helpers.py`；本地其余 40+ 测试默认不入库——**新测试要入库必须在 .gitignore 白名单区追加 `!test/test_xxx.py`**。`migrations/`、`AGENTS.md`、`CLAUDE.md` 也被 gitignore（本地 AI 协作文件，其他协作者看不到）。

⚠️ test/ 下混有非测试资产：`ovr_lipsync/`（含 ffmpeg，唇形依赖）、`FunAudioLLM/`（SenseVoice 服务）、`easegen_auto_play_server.py` 等辅助服务脚本。

### 10.2 前端测试

Vitest（`npm test`，单文件 `npm test -- src/utils/xxx.test.ts`），细节见 7.5。`npm run build` 含 vue-tsc，**任何 TS 类型错误阻断构建**。

### 10.3 docs/ 与 scripts/

- `docs/Prompt设计文档.md`：双阶段 LLM 架构（规划器+最终输出）、prestart/think 标签语义。⚠️ 规划器 JSON 契约**已落后于代码**（文档写 `{"action":"tool","tool":...}`，实际是闲聊判断器输出 `{"action":"tool","keyword":...}`，且未记载大小模型协作架构）——以代码为准并回填文档。
- `docs/memory_module.md`：记忆模块架构（与代码一致；`_log_prompt` 已是空操作，调试 Prompt 需临时恢复）。
- `docs/MCP外部调用接口.md`：5010 端口对外契约（**比 CLAUDE.md 准确**）。
- `docs/Fay侧标准动作改造说明.md`：动作信号协议设计（对应 11.3）。
- `docs/superpowers/plans/`：已完成的实施计划（YYYY-MM-DD-feature.md，checkbox 全勾选，对应提交 d11e443 认证看板与数字人库——是**实施记录**，勿重复实施）。新实施计划按此格式（Goal/Architecture/Chunk/Task + Final Verification Snapshot）。
- `scripts/update_logo_version.py`：唯一辅助脚本（Pillow 重绘 Logo 版本号，支持 --dry-run）。

---

## 11. 辅助与边缘模块

### 11.1 simulation_engine（仿生记忆底座，源自斯坦福 Generative Agents 论文）

四个 py 文件 + 10 个提示词模板，**真正影响线上行为的只有 importance_score 与 reflection 两组模板**：

- `gpt_structure.py`：模板引擎（`generate_prompt` 按序替换 `!<INPUT n>!`，以 `<commentblockmarker>###</commentblockmarker>` 切除头部注释）+ LLM 网关（`chat_safe_generate`，temperature=0.7）+ `get_text_embedding`（全项目统一向量化入口，被 memory_service/nlp_cognitive_stream/fay_booter/yueshen_rag 四处直接导入）。**OpenAI client 显式 60s 超时 + max_retries=1**——曾因上游不发字节锁死 agent_lock 致机器 5 小时无响应，新增 LLM 调用点必须沿用。
- `settings.py`：**导入即执行 `cfg.load_config()`**，桥接 system.conf 的小模型配置；`LLM_PROMPT_DIR` 模板根目录。
- `llm_json_parser.py`：`extract_first_json_dict`（花括号配对提取）。⚠️ `global_methods.py` 有同名**带 bug 版本**（花引号替换的中文字符已在编码转换中丢失），靠 genagents 模块中 llm_json_parser **导入顺序靠后**而覆盖——**切勿调换 memory_stream.py:12-14 的导入顺序**。
- `global_methods.py`（387 行）：实际只有 `check_if_file_exists`/`create_folder_if_not_there` 被消费，CSV/统计函数全是论文遗留死代码（且打开文件未指定 encoding，复用前需修复）。
- 模板组织：`prompt_template/generative_agent/<域>/<能力>/{singular|batch}_v1.txt`，三段式（Variables 注释 → 分隔符 → 正文+JSON 输出说明）。⚠️ 目录名 `utternace` 是**拼写错误**且 interaction.py:196 硬编码同样拼写，勿单独改目录名。**模板每次调用实时读取，改模板无需重启**。
- ⚠️ `chat_safe_generate` 的重试机制实际失效（判断 `!= 'GENERATION ERROR'` 但实际返回带详情后缀），兜底靠各 clean_up 的 None 检查。
- ⚠️ utterance/categorical/numerical 问卷模板链路在主流程**无调用方**（Fay 实际对话走 nlp_cognitive_stream），改 utterance_v1.txt 不影响日常对话。
- 新增 Agent LLM 行为：新建模板 → 在 memory_stream.py/interaction.py 写 `run_gpt_generate_xxx` 三件套（create_prompt_input / _func_clean_up / _get_fail_safe）→ `chat_safe_generate` 调用 → GenerativeAgent 薄封装。JSON 解析放 llm_json_parser.py，勿放 global_methods。

### 11.2 旧版 Web 管理界面（legacy GUI，并非死代码）

Jinja2 + Vue2（CDN）+ Element UI 三页面，**两个活跃场景**：

1. **回退路径**：`flask_server.__get_vue_app()` 在 `fay-frontend/dist` 缺失时回退渲染 `gui/templates/index.html`（消息页）/`setting.html`（人设页）。当前仓库 dist 存在，默认不触发；`/live2d` 等新路由 dist 缺失时统一回退到旧消息页（无对应 legacy 页）。
2. **始终活跃**：`faymcp/templates/Page3.html` 是 5010 端口的 MCP 管理页（服务端渲染 mcp_servers 卡片 + data-* 属性即状态），**无 Vue 回退逻辑**。

价值：`gui/static/js/index.js`（FayInterface 类）与 `setting.js` 完整记录了后端 API 与 10003 WS 的**行为契约**（panelReply 按 id 拼接 + 150ms 防抖 + 500ms 静默后 `/api/get-msg-by-id` 兜底拉全文；liveState 状态机；config JSON 结构），是核对新前端接口一致性的权威参照。

坑：Jinja2 与 Vue2 共存时 Vue 定界符为 `[[ ]]`；index.js 与 setting.js 各复制一份 FayInterface 不共享；⚠️ `flask_server.py:1720` 的 `/Page3` 路由是**残留死路由**（模板目录无此文件必然报错，真 Page3 在 5010）；启用认证后 legacy 页裸 fetch 5010 不带 Bearer 会 401（MCP 灯恒离线）；页面间 5000↔5010 跳转端口硬编码；`setting.js` 用 eval 解析响应、保存配置 fire-and-forget。

### 11.3 动作信号规则（config/action_rules.csv）

「通用动作语义」机制的唯一规则源：21 行 CSV（表头 + 20 条规则），列为 `code,behavior,affect,intensity,priority,sentimentHint,keywords`（keywords 用 `|` 分隔规避逗号）。`core/action_signal.py` 用 `lru_cache` 一次性加载（**改文件须重启**），`resolve_action_signal()` 对 TTS 文本做小写子串匹配，按（命中数 → 最长关键词 → priority）三元组打分。唯一消费方 `fay_core.py:2307-2310`，结果作为 10002 audio 消息的 `Data.Action` 下发，由外部渲染端自行映射动作/表情；**fay-frontend 不消费此字段**。设计文档：`docs/Fay侧标准动作改造说明.md`。

坑：单行解析失败静默跳过无日志；子串匹配易误触发（英文 "no" 命中 know/now）；priority 只是第三优先级；无任何管理接口只能手工编辑；`sentimentHint`（规则静态标注）与 `Data.Sentiment`（百度 API/关键词动态计算）完全独立。

### 11.4 skills/ 与远程音频示例

`skills/remote_audio_key0.py` 是 10001 协议的唯一官方直连参考实现（Windows 专属按键拾音客户端），**不被主程序 import**，文档价值大于运行价值。协议细节见 8.3。坑：默认握手发 `<output>False<output>` 收不到回送音频；接收文件存为 `.mp3` 实际是 WAV。

### 11.5 MCP 子服务器辅助组件

- **schedule_manager/web_server.py**：日程 MCP 的独立 Flask Web 管理（127.0.0.1:5011），由 server.py 在 MCP 连接建立时以子进程拉起，与 server.py 共享 `schedules.db`；跨进程通知靠写 `.reschedule_<id>` 触发文件（写失败静默吞掉）。坑：无鉴权 CORS 全开；`/api/schedule/complete/<id>` 名为完成实际软删除为 deleted；两进程共写 SQLite 无 WAL 可能锁库。
- **yueshen_rag/embedding_config.py**：embedding 覆盖开关——仅 `YUESHEN_ALLOW_EMBED_OVERRIDE=1` 时才在 MCP 工具 schema 暴露并接受 `embedding_base_url/api_key/model` 覆盖参数，否则**静默忽略**（排查"覆盖不生效"先查此环境变量）。yueshen 默认 embedding 走 Fay 本机透传端点 `http://127.0.0.1:5000/v1`（key `sk-fay`，model `embedding`）。

---

## 12. 全局编码约定

- **线程**：一律 `scheduler.thread_manager.MyThread`，长循环以 `__running` 标志退出，不依赖 stopAll 注入兜底。
- **单例**：模块级私有变量 + `new_instance()` 工厂 + 锁；获取已有实例用 `get_instance()`。
- **服务启动**：服务模块暴露模块级 `start()`，内部自起 MyThread。
- **路由注册**：`register_xxx_routes(app)` 函数 + `app.config['FAY_XXX_ROUTES_REGISTERED']` 防重。
- **鉴权装饰器顺序**：`@app.route` → `@auth_service.require_auth` → `@auth_service.require_role('admin')`。
- **API 响应**：错误 `{'error': 中文消息}` + 4xx；成功 `{'success': True, ...}`。
- **延迟导入**：重模块（fay_core/llm/faymcp）在函数内 import，避免循环依赖。
- **隐藏标记协议**：句子流内 `_<isfirst>`/`_<isend>`/`_<isqa>` + `__<cid=xxx>__`，消费端负责剥离。
- **私有方法**：双下划线前缀；抽象方法 `@abstractmethod`。
- **提交信息**：简洁中文，前缀 `feat:`/`fix:`/`refactor:`/`docs:`（可带 emoji，如 `✨ feat: 新增数字人库管理`）。
- **编码**：所有文件 UTF-8 无 BOM。

---

## 13. 已知坑点汇总

> 各子系统的局部坑见对应章节，此处为跨系统、最易踩的全局级坑。

| 状态 | 坑点 | 当前处理 / 后续修复建议 |
|---|---|---|
| 保留兼容 | **软门禁**：auth.enabled 缺省关闭，所有"受保护"接口实际不设防（6.3） | 生产必须显式配置 `auth.enabled=true`；若要改成默认强鉴权，需要同步 legacy 页面、WS 首包鉴权、测试夹具和部署文档，避免破坏无认证本地启动。 |
| 已修正代码注释 | **文档过时**：CLAUDE.md 称 MCP SSE 端口 9002，实际默认 **8765** | `fay_booter.py` 注释已按默认开启修正；仍以 `FAY_MCP_SSE_HOST/PORT/PATH` 控制绑定地址、端口与路径。CLAUDE.md 被 gitignore，本文件继续作为当前事实来源。 |
| 已修复 | **Live2D Samples 路径**：原默认值是开发者本机绝对路径 | 默认扫描 `library/live2d/Samples`；换机或使用外部 Cubism SDK 时仍可设 `FAY_LIVE2D_SAMPLES_ROOT`。 |
| 已修复 | **config.json 会被程序回写**（数字人库/人设），手工编辑可能与运行中进程互相覆盖 | 已新增 `save_config_sections()` 做顶层配置段级替换，数字人库/人设、`/api/submit`、麦克风开关不再用陈旧内存对象全量覆盖其他顶层段；写文件经临时文件 + `os.replace` 原子替换。仍避免同时编辑同一顶层段。 |
| 操作约束 | **配置中心记忆化**：远端改配置后需 force_reload 或重启；密钥经 `FAY_SYSTEM_CONF_JSON` 传给子进程 | 当前按设计保留；排障时优先重启或调用 `load_config(force_reload=True)`，后续可加管理员 reload API。 |
| 已修复 | **每次启动清空 logs/ 与 samples/**，排障注意日志不保留 | 已改为启动时归档 `logs/*.log` 与 `samples/sample-*` 到 `archive/<启动批次>/`，并默认只保留最近 10 个归档批次，避免无限增长。 |
| 已修正文档 | **MCP 工具启停状态需重启 MCP 客户端连接才生效** | 当前代码已即时生效：toggle 路由写 `mcp_tool_states.json` 后调用 `tool_registry.update_tool_enabled()` 重建聚合缓存，LLM 侧从 `tool_registry.get_enabled_tools()` 读取最新启用工具。 |
| 已修复 | **看板会话统计与 content_db 会话记录曾是两套逻辑** | 已改为读取 `T_ServiceSession`；legacy 无 `session_id` 消息才按 30 分钟规则兜底推导。 |
| 已修复 | **QA 多候选随机选答 + CSV 第三列可执行任意命令** | 已改为稳定选择最高分候选；CSV 第三列命令动作默认禁用，仅 `interact.enableQnACommandActions=true` 时启用。 |
| 操作约束 | **`memory.isolate_by_user` 切换后需重新初始化记忆目录** | 当前仍需人工迁移/重建；后续可提供迁移脚本，把 shared/User 目录按用户名拆分或合并。 |
| 操作约束 | **音频设备冲突/端口占用**是启动失败的最常见原因（用 `kill_process_by_port()`） | 当前仍依赖启动前排查；新增常驻服务时必须补端口表和退出清理清单。 |
| 操作约束 | **PyQt5 未列入 requirements**，start_mode=common 需手动安装 | 当前仍为可选依赖；若桌面模式成为默认入口，再把 PyQt5 拆到 extras 或单独 requirements。 |

---

## 14. 常见开发任务指引

### 14.1 新增一个受保护的 HTTP API
1. 在对应路由文件（或新建 `gui/xxx_routes.py` 提供 `register_xxx_routes(app)`，参照 `auth_routes.py:66-69` 防重模式）定义路由。
2. 按固定顺序叠加 `@auth_service.require_auth`（管理员再加 `@require_role('admin')`），用 `auth_service.current_user()` 取 `{username, role, uid}`。
3. 新路由文件需在 `gui/flask_server.py` 顶部 import 并在 74-77 行附近注册。
4. 敏感写操作调 `audit_service.log(...)` 记审计。
5. 前端在 `fay-frontend/src/api/` 对应文件加调用函数。
6. ⚠️ 本地调试若 auth.enabled=false 鉴权不拦截；测试鉴权须先开启。

### 14.2 新增输入渠道（新硬件/新协议）
1. 音频流：继承 `core/recorder.py` 的 `Recorder`，实现 `get_stream()`（返回带 `read(1024)` 的流，可复用 `StreamCache`）、`on_speaking(text)`、`is_remote()`。
2. `on_speaking` 中构造 `Interact(渠道名, 1, {'user': username, 'msg': text})` 调 `fay_booter.feiFei.on_interact`——打断/会话/TTS/推送全部由下游自动完成。
3. 纯文本输入直接构造 Interact 调 on_interact（参考 flask_server）。
4. 在 `fay_booter.start()` 中用 MyThread 启动监听，在 `stop()` 中对称清理。
5. 任何长耗时处理必须在循环中查 `should_stop_generation(username, conversation_id)` 支持打断。

### 14.3 新增数字人下行字段
在 `fay_core.py __process_output_audio` 的 `content['Data']` 追加字段（参考 Sentiment L2297 / Action L2307 / Lips L2330），保留 prestart 拦截与停止检查；客户端按 `Topic=human + Data.Key` 解析。

### 14.4 新增常驻服务 / 业务期服务
- 常驻基础服务（与会话无关）：服务模块提供 `start()`，在 `main.py __main__` 按依赖顺序插入（参考 mcp_service 的 try/except 容错写法）。
- 业务期服务（依赖 feiFei/LLM）：在 `fay_booter.start()` 创建、`stop()` 对称关闭（先外围 IO → 保存状态 → 停核心）。
- 新端口要加进 `main.py:277` exit 清单并更新本文件第 4 章。

### 14.5 新增配置项
- 密钥类：加 `system.conf.bak` 模板 `[key]` 段 + `config_util.py` 声明模块级全局变量并在 `load_config()` 读取。
- 行为类：加 `config.json`，经 `config_util.config['...']` 访问；写回优先用 `save_config_sections()` 指定顶层段。注意配置中心模式下两份文件都来自 `cache_data/`。

### 14.6 新增 MCP 工具 / 服务器
- 外部服务器：在 `mcp_servers/` 建目录实现 MCP 协议（参考 schedule_manager），注册进 `faymcp/data/mcp_servers.json`，经管理界面/API 启用。
- 暴露 Fay 能力：`faymcp/mcp_server.py` 加工具定义 + `runtime_bridge.py` 实现逻辑，自动经 SSE 服务器暴露。

### 14.7 新增数据库迁移
`migrations/NNN_描述.py` 提供 `run()`（备份 → 事务 → 失败回滚还原），并修改 `main.py:63-71` 加载新模块（当前硬编码模块名，无版本表，幂等自己保证）。

### 14.8 新增动作规则
直接编辑 `config/action_rules.csv` 追加行（关键词尽量用长词组避免子串误触发），重启进程生效；同步更新 `docs/Fay侧标准动作改造说明.md`；新 behavior/affect 锚点需通知渲染端补映射。

### 14.9 新增看板指标
运营指标在 `dashboard_operational.py` 写计算函数；旅游指标在 `dashboard_service.py` 加 `_query_xxx` 并挂进 `get_tourism`；路由在 `gui/dashboard_routes.py` 注册。

### 14.10 新增记忆操作
只在 `core/memory_service.py` 加函数，遵循"锁外算 → 锁内写 → 锁外刷盘"三段式；暴露为 MCP 工具到 `faymcp/mcp_server.py` 加 `asyncio.to_thread` 代理。

---

## 15. 文档维护指南

本文件的设计原则：**每章自洽、按子系统分章、坑点就近记录、全局信息（端口/存储/约定）集中成表**。维护时请遵循：

1. **何时必须更新**：
   - 新增/变更端口或常驻服务 → 第 4 章表格
   - 新增/变更 HTTP API → 6.8（或对应域的小节 API 表）
   - 新增/变更 WS 消息类型 → 第 8 章
   - 新增数据库表/存储文件 → 第 9 章
   - 架构级调整（新子系统/链路变化）→ 第 6/7 章对应小节 + 第 3 章目录树
   - 发现新坑 → 对应小节就近记录；跨系统的进第 13 章
2. **写法约定**：结论尽量带 `文件:行号` 证据；用 ⚠️ 标记坑点；表格优先于长段落；保持简体中文。
3. **扩展新章节**：在目录与正文同步添加；若某小节超过 ~200 行，考虑拆分为 `docs/` 专项文档并在此留索引。
4. **校验**：行号会随代码漂移，重大重构后请抽查关键引用是否仍然有效；过时描述（如 CLAUDE.md 的 9002 端口）应显式标注而非静默删除，帮助读者识别旧资料。
