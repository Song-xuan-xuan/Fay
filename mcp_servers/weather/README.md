# 天气 MCP 服务

该 stdio MCP 服务为 Fay 提供 `query_weather` 工具。目前仅支持查询城市的实时天气，不包含逐小时预报或未来天气预报。

## 环境变量

- `HEFENG_API`：天气服务 API Key。请使用自己的 Key，不要将真实 Key 提交到仓库。
- `HEFENG_API_HOST`：天气服务 API Host，仅填写主机名，不包含 `https://`、端口或路径。

## 安装依赖

在仓库根目录使用 Fay 的 Python 环境安装：

```powershell
.venv\Scripts\python.exe -m pip install -r mcp_servers/weather/requirements.txt
```

## 在 Fay 中添加

启动 Fay 后打开 `http://127.0.0.1:5000/mcp`，添加一个 stdio MCP 服务：

- transport：`stdio`
- command：Fay 使用的 Python，例如 `.venv\Scripts\python.exe`；若 `python` 已指向 Fay 环境，也可填写 `python`
- args：`mcp_servers/weather/server.py`
- cwd：Fay 仓库根目录
- env：填写 JSON 对象，例如：

  ```json
  {
    "HEFENG_API": "<your-api-key>",
    "HEFENG_API_HOST": "<your-api-host>"
  }
  ```

- autostart：开启

保存并连接服务后，在工具列表中启用 `query_weather`。调用时传入城市名称，例如 `{"city_name": "北京"}`。
