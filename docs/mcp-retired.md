# MCP 下线归档说明

本文记录景区数字人项目当前 MCP 服务取舍，避免后续维护时误判这些服务是遗漏配置。

## 当前保留

- `RAG`：保留为通用文档 RAG 能力，可用于景区资料、历史文档、宣传册等非结构化内容检索。当前 `autostart=true`，`YUESHEN_PERSIST_DIR=cache_data/chromadb_yueshen_clean`，部署时避免写本机绝对路径。
- `课程知识库`：保留为核心景区知识库入口，适合承载景点目录、路线、讲解重点和章节化内容。

## 已从注册配置下线

以下 MCP 已从 `faymcp/data/mcp_servers.json` 移除，不会出现在 MCP 管理页，也不会进入 LLM 可调用工具集合。
对应的历史工具启停状态也已从 `faymcp/data/mcp_tool_states.json` 清理，避免旧状态影响后续工具聚合。

- `tools`
  - 原配置：`python test/mcp_stdio_example.py`
  - 下线原因：示例/调试工具，不属于景区数字人业务能力。
  - 处理方式：保留测试脚本，后续仍可作为 MCP 链路调试参考。

- `Fay日程管理`
  - 原配置目录：`mcp_servers/schedule_manager`
  - 下线原因：当前景区数字人主线聚焦知识问答、路线推荐和讲解，不包含游客日程提醒。
  - 处理方式：保留源码目录，未来如果需要预约讲解、集合提醒或活动提醒，可重新注册。

- `window capture`
  - 原配置：`python mcp_servers/window_capture/server.py`
  - 下线原因：桌面窗口截图能力不属于游客端核心场景，并存在隐私风险。
  - 处理方式：保留源码目录，后续仅在明确需要本地桌面感知能力时再启用。

- `logseq`
  - 原配置目录：`mcp_servers/logseq`
  - 原环境变量：`LOGSEQ_GRAPH_DIR`
  - 下线原因：属于个人 Logseq 图谱读写能力，依赖本机图谱目录，不适合作为游客端默认知识能力。
  - 处理方式：保留源码目录；未来如果要把管理员个人笔记接入数字人，再重新注册并配置服务器上的图谱路径。

## 恢复方式

如需恢复某个已下线 MCP，可用管理员账号直接访问隐藏入口 `/mcp` 并重新新增对应 stdio 配置，或通过 5010 API 恢复；服务运行中不建议只手工改 `faymcp/data/mcp_servers.json`，避免被 5010 服务内存态回写。

恢复前建议确认：

- 该 MCP 是否确实属于当前景区数字人使用场景。
- 是否需要登录态、用户确认或隐私提示。
- 是否会增加 LLM 工具误调用风险。
