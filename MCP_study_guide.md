# MCP 讲义（基于 weather-assistant 项目）

---

## 1. 讲义定位

这份讲义不是“概念罗列”，而是按“从认知到落地”的顺序组织：

1. 先建立 MCP 的标准分层认知。
2. 再理解协议调用链和核心模块边界。
3. 最后映射到当前 weather 项目的具体代码、配置、运行与排错。

---

## 2. 学习目标

完成本讲义后，你应当能：

- 准确区分 Host / Client / Server 的职责边界。
- 理解 Resources / Tools / Prompts 的定位和适用场景。
- 独立搭建一个可运行的 MCP Server，并接入 Claude Desktop/Cursor。
- 使用 `mcp-cli` 与 Inspector 完成联调。
- 处理常见问题（端口冲突、路径转义、401、代理异常、stdio 误用等）。
- 理解 HTTP 化与授权的升级方向。

---

## 3. 项目概览（当前仓库）

核心文件：

- `mcp-server/weather-mcp-server.py`：MCP Server（核心入口）
- `weather_assistant_call.py`：独立天气 API 调用脚本（非 MCP）
- `openai_http_call.py` / `openai_sdk_call.py`：模型调用样例
- `.env`：本地变量
- `images/mcp_flow.png`：MCP 调用流程图

你当前 server 暴露能力：

- Tool：`get_weather_advice(prompt)`
- Prompt：`weather_trip_brief(city, day, activity)`

---

## 4. MCP 三层架构（标准模型）

## 4.1 Host（宿主应用）

Host 是用户使用的 AI 应用外壳（如 Claude Desktop、Cursor Agent）。它负责：

- 用户交互入口
- 模型调用编排
- 工具调用审批与展示

## 4.2 Client（协议客户端）

Client 是 Host 内部“会说 MCP 协议”的组件。它负责：

- 与 Server 建连
- 初始化与协议协商
- 能力发现（list tools/resources/prompts）
- 请求转发与结果回收

## 4.3 Server（能力提供端）

Server 负责把真实外部系统能力标准化暴露给 Client。它负责：

- 声明能力（tools/resources/prompts）
- 执行后端动作（API/DB/文件系统）
- 返回结构化结果

一句话记忆：

- Host 管交互
- Client 管协议
- Server 管能力

---

## 5. MCP 能力模型与关键词

## 5.1 Resources

- 定位：给模型“看”的只读上下文
- 常见内容：文档、schema、配置、报表、说明数据
- 关键特征：读多写少，无副作用

## 5.2 Tools

- 定位：给模型“做”的可执行动作
- 常见动作：查询、创建、更新、触发外部 API
- 关键特征：有参数、可能有副作用、需要权限边界

## 5.3 Prompts

- 定位：可复用任务模板
- 作用：规范任务输入，提升模型工具调用稳定性
- 关键特征：模板本身不执行外部动作，常用于引导调用 Tool

## 5.4 扩展能力（生产常见）

- Transport：STDIO / SSE / Streamable HTTP
- Authorization：谁能调、代表谁调、能调什么
- Protocol Negotiation：协议版本对齐
- Capability Discovery：能力菜单发现
- Notifications / Sampling：高级交互机制

---

## 6. MCP 标准调用流程（时序）

MCP 调用流程画板

流程摘要：

1. Client 初始化连接 Server，并获取可用工具列表。
2. 用户提问后，Host 将“问题 + 可用工具信息”交给模型。
3. 模型决定是否调用工具；若调用，返回工具调用指令。
4. Client 调用 MCP Server 对应 Tool。
5. Server 调用第三方 API/本地逻辑并返回结构化结果。
6. Host 将工具结果回填模型，生成最终自然语言答复。

---

## 7. 当前项目的映射关系

对应路径：`mcp-server/weather-mcp-server.py`

- Host：Claude Desktop / Cursor
- Client：各自内置 MCP Client
- Server：`weather-assistant`
- Tool：`get_weather_advice(prompt)`
- Prompt：`weather_trip_brief(city, day, activity)`
- 第三方 API：OpenWeather Assistant API

Tool 执行链：

`Client -> get_weather_advice -> call_weather_api -> OpenWeather -> structured result -> Client`

---

## 8. mcp-cli 安装与使用（Windows + uv）

## 8.1 安装

```powershell
cd E:\mcp_project
uv venv .venv
uv pip install --python .venv\Scripts\python.exe "mcp[cli]"
```

## 8.2 验证

```powershell
E:\mcp_project\.venv\Scripts\mcp.exe --help
E:\mcp_project\.venv\Scripts\mcp.exe version
```

## 8.3 常用命令

调试运行（Inspector）：

```powershell
E:\mcp_project\.venv\Scripts\mcp.exe dev E:\mcp_project\mcp-server\weather-mcp-server.py
```

标准运行（供客户端托管）：

```powershell
E:\mcp_project\.venv\Scripts\mcp.exe run E:\mcp_project\mcp-server\weather-mcp-server.py
```

用 `uv run` 包装（可选）：

```powershell
cd E:\mcp_project
uv run --active mcp dev mcp-server\weather-mcp-server.py
uv run --active mcp run mcp-server\weather-mcp-server.py
```

---

## 9. 客户端接入配置

## 9.1 Claude Desktop（uv 方案）

文件：`C:\Users\50717\AppData\Roaming\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "weather-assistant": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "E:\\mcp_project",
        "--python",
        "E:\\mcp_project\\.venv\\Scripts\\python.exe",
        "mcp",
        "run",
        "E:\\mcp_project\\mcp-server\\weather-mcp-server.py"
      ],
      "env": {
        "OPENWEATHER_API_KEY": "<YOUR_OPENWEATHER_KEY>"
      }
    }
  }
}
```

## 9.2 Cursor（示例）

文件：`C:\Users\50717\.cursor\mcp.json`

```json
{
  "mcpServers": {
    "weather-assistant": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "E:\\mcp_project",
        "--python",
        "E:\\mcp_project\\.venv\\Scripts\\python.exe",
        "mcp",
        "run",
        "E:\\mcp_project\\mcp-server\\weather-mcp-server.py"
      ],
      "env": {
        "OPENWEATHER_API_KEY": "<YOUR_OPENWEATHER_KEY>"
      }
    }
  }
}
```

接入要点：

- 路径在 JSON 中必须使用双反斜杠 `\\`。
- `OPENWEATHER_API_KEY` 建议在客户端 `env` 注入，不要写死代码。

---

## 10. 当前 Server 关键代码（节选）

文件：`mcp-server/weather-mcp-server.py`

```python
@mcp.tool()
def get_weather_advice(prompt: str) -> Dict[str, Any]:
    result = call_weather_api(prompt)
    return {
        "ok": True,
        "answer": result.get("answer", ""),
        "session_id": result.get("session_id"),
        "data": result.get("data", {}),
    }


@mcp.prompt(
    name="weather_trip_brief",
    description="Template for weather-aware travel/outdoor planning that uses get_weather_advice.",
)
def weather_trip_brief(city: str, day: str = "today", activity: str = "outdoor travel") -> str:
    return (
        f"The user plans {activity} in {city} on {day}. "
        "First call tool get_weather_advice, then provide summary, risks, and suggestions."
    )
```

设计说明：

- Tool 负责“执行真实动作”。
- Prompt 负责“提供任务模板并引导模型先调 Tool”。

---

## 11. 高频问题排查

1. `Invalid JSON: EOF while parsing`

- 场景：手工在终端跑 `mcp run`。
- 原因：`run` 需要 MCP Client 协议消息，不是手工输入模式。

1. `File not found: ...mcp-serverweather-mcp-server.py`

- 原因：路径缺少分隔符。

1. `No interpreter found ... E:mcp_project...`

- 原因：路径转义错误，反斜杠被吞。

1. `PORT IS IN USE`（6274 / 6277）

- 原因：Inspector 端口被占用。
- 处理：释放端口后重启 `mcp dev`。

1. `401 Unauthorized`

- 原因：Key 无效或未生效。
- 处理：检查 `env` 注入与 key 是否可用。

1. `ProxyError`

- 原因：系统代理不可达。
- 处理：修正代理配置或临时禁用代理后重试。

---

## 12. HTTP 化与授权升级路径

建议按阶段推进：

1. 阶段 A：本地可用

- `stdio` + 本地 env

1. 阶段 B：内网服务化

- 切到 HTTP/Streamable HTTP
- 前置网关做基础鉴权（JWT/API Key）

1. 阶段 C：规范化授权

- 接入 OAuth 2.1 / Token 校验
- 做 scope 控制、审计日志、最小权限

原则：先稳定，再安全，再规模化。

---

## 13. 命令速查

```powershell
# 安装 mcp-cli
uv pip install --python .venv\Scripts\python.exe "mcp[cli]"

# 查看帮助
E:\mcp_project\.venv\Scripts\mcp.exe --help

# Inspector 调试
uv run --active mcp dev mcp-server\weather-mcp-server.py

# 标准运行
uv run --active mcp run mcp-server\weather-mcp-server.py
```

---

## 14. 一句话记忆

MCP 是 AI 应用连接外部能力的标准协议：

- Host 承载交互
- Client 负责协议
- Server 提供能力
- Resource 给模型看
- Tool 给模型做
- Prompt 给模型模板
