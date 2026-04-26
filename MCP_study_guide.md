# MCP 系统学习讲义（基于 weather-assistant 项目）

## 1. 学习目标

本讲义目标：

- 建立 MCP 的完整分层认知（Host / Client / Server）。
- 理解 MCP 核心能力（Resources / Tools / Prompts）与扩展机制。
- 掌握从 0 到 1 搭建 MCP Server 的标准流程。
- 将标准流程映射到你当前 `weather-mcp-server.py` 项目。
- 形成可复用的排错与工程化落地方法。

---

## 2. MCP 整体结构（三层架构）

可以把 MCP 先理解为三层：

1. Host（宿主应用）
2. Client（协议客户端）
3. Server（能力提供端）

### 2.1 Host（宿主应用）

定义：用户真正交互的 AI 产品外壳。

职责：

- 承载对话界面或智能体运行环境。
- 决定接入哪些 MCP Server。
- 控制何时允许模型调用外部能力。
- 承担授权确认、结果展示、交互编排。

例子：Claude Desktop、IDE 助手、企业智能体平台。

一句话：Host = 用户入口 + 运行容器。

### 2.2 Client（协议客户端）

定义：Host 内“会说 MCP 协议”的那一层。

职责：

- 与 Server 建连。
- 发送初始化与协议协商。
- 做能力发现（有哪些 tools/resources/prompts）。
- 发起调用并回收结果。

一句话：Client = 协议通信代理。

### 2.3 Server（能力提供端）

定义：对外暴露能力的一端，把真实系统封装为 MCP 能力。

职责：

- 声明能力清单（tools/resources/prompts）。
- 接收调用请求。
- 访问后端资源（DB/API/文件系统）。
- 返回结构化结果。

一句话：Server = 外部能力适配层。

---

## 3. MCP 核心能力模块

## 3.1 Resources（资源）

关键词：读上下文。

含义：提供可读数据（文件、文档、查询结果、配置等），用于让模型“看”。

特点：

- 偏只读。
- 适合结构化或半结构化内容。
- 常用于补上下文。

判断法：无副作用、主要给模型阅读 => Resource。

## 3.2 Tools（工具）

关键词：执行动作。

含义：可调用函数能力，模型可按参数执行，返回结构化结果。

特点：

- 偏执行。
- 带参数。
- 可能有副作用。
- 常涉及权限、审批、审计。

判断法：带动作、带参数、可能改状态 => Tool。

## 3.3 Prompts（提示模板）

关键词：任务模板。

含义：预定义提示模板，标准化某类任务入口。

特点：

- 复用性高。
- 降低用户输入复杂度。
- 常与 tools 组合使用。

关系：Prompt 不是执行器；它常引导模型后续调用 Tool。

---

## 4. 扩展模块（生产落地必备）

## 4.1 Transport（传输层）

关键词：怎么连。

常见：

- STDIO（本地进程通信）
- HTTP / Streamable HTTP（远程服务）

选择建议：

- 本地开发、桌面工具：优先 STDIO。
- 企业共享、多用户、审计：优先 HTTP。

## 4.2 Authorization（授权）

关键词：谁能调、代表谁调、能调什么。

作用：身份认证、权限边界、Token 传递、审计。

## 4.3 Protocol Negotiation（协议协商）

关键词：版本对齐。

作用：建连后确认协议版本兼容；不兼容应终止。

## 4.4 Capability Discovery（能力发现）

关键词：先看菜单再点单。

作用：客户端先发现你暴露的 tools/resources/prompts 及参数 schema。

## 4.5 Notifications（通知）

关键词：异步事件。

作用：服务端主动通知状态变化、进度、资源更新。

## 4.6 Sampling（采样/反向借模）

关键词：Server 反向请求模型能力。

用途：复杂工作流里，让 Server 借助 Host 的模型做总结/分类/抽取。

## 4.7 Development Tools（开发工具）

关键词：调试与验收。

代表：MCP Inspector（相当于 MCP 的协议调试器）。

---

## 5. 标准搭建流程（从 0 到 1）

1. 定义边界

先明确你暴露的是 Tool、Resource 还是 Prompt。

2. 定义契约

为每个能力定义参数 schema、返回结构、错误结构。

3. 选 Transport

本地先 STDIO，验证后再考虑 HTTP 化。

4. 实现 Server

把业务逻辑与协议入口分离：

- 协议层：注册工具与路由。
- 业务层：真实 API/DB 调用。

5. 设计配置与密钥管理

统一环境变量来源，避免 `.env` 和客户端 `env` 冲突。

6. 本地调试

用 Inspector 验证：能力可发现、参数校验、结果结构。

7. 客户端接入

在 Claude Desktop/Cursor 配置 server 命令和 `env`。

8. 生产化加固

补齐：鉴权、审计、超时、重试、幂等、监控、错误码规范。

---

## 6. 完整调用链（一次真实请求）

场景：用户问“帮我查上海天气并给出出行建议”。

1. 用户在 Host 发起问题。
2. Host 内 Client 发现可用工具 `get_weather_advice(prompt)`。
3. Client 与 Server 完成初始化、协商、能力发现。
4. 模型决定是否调用 Tool。
5. Tool 请求到达 Server。
6. Server 调 OpenWeather API。
7. Server 返回结构化数据。
8. 模型基于返回数据组织自然语言答复。
9. Host 展示最终结果。

---

## 7. 你当前项目映射

项目文件：

- `mcp-server/weather-mcp-server.py`：MCP Server（当前核心）。
- `weather_assistant_call.py`：非 MCP 的直连调用脚本。
- `.env`：本地变量。
- `claude_desktop_config.json`：Host 侧 server 接入配置。

角色映射：

- Host：Claude Desktop。
- Client：Claude Desktop 内置 MCP 客户端。
- Server：`weather-mcp-server.py`。
- Tool：`get_weather_advice(prompt)`。
- Prompt：`weather_trip_brief(city, day, activity)`。
- Transport：当前是 STDIO。

---

## 8. Claude Desktop 推荐配置（uv 方案）

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

说明：

- 这套参数可同时用于 Claude Desktop 和 MCP Inspector v0.21.2。
- JSON 内路径必须双反斜杠 `\\`。
- `OPENWEATHER_API_KEY` 建议放在 `env` 中，不要写死在代码。

---

## 8.1 Prompt + Tool 联动示例（当前项目）

你现在的 Server 已包含：

- Tool：`get_weather_advice(prompt)`
- Prompt：`weather_trip_brief(city, day=\"today\", activity=\"outdoor travel\")`

含义：

- Prompt 负责给模型一个“标准任务模板”。
- 模板中明确要求先调用 Tool，再基于 Tool 返回组织最终建议。

示例输入（渲染 prompt 参数）：

- `city=Shanghai`
- `day=tomorrow`
- `activity=city walk`

模型会拿到类似模板：

1. 先调用 `get_weather_advice`
2. 输出天气摘要
3. 输出风险提醒
4. 输出穿衣与时段建议
5. 给出是否适合活动的结论

这就是 “Prompt 做任务模板，Tool 做真实查询动作” 的标准配合。

---

## 9. 高频报错与定位手册

1. `Invalid JSON: EOF while parsing`

原因：手工运行 `mcp run`，但没有 MCP 客户端发 JSON-RPC。

2. `File not found: ...mcp-serverweather-mcp-server.py`

原因：路径漏反斜杠。

3. `No interpreter found for executable name E:mcp_project...`

原因：反斜杠被吞，路径转义错误。

4. `ProxyError`

原因：代理不可达或配置冲突。

5. `401 Unauthorized`

原因：API key 无效、未生效或配置来源混乱。

6. `PORT IS IN USE`

原因：Inspector 默认端口（6274/6277）被占用。

---

## 10. 分工边界速记

- Resource：给模型“看”。
- Tool：给模型“做”。
- Prompt：给模型“按模板做任务”。
- Host：产品容器。
- Client：协议通信层。
- Server：能力封装层。

---

## 11. MCP 与普通 API 的区别

相同点：都可传参、鉴权、返回结果。

关键差异：

- MCP 提供能力发现与标准化暴露。
- MCP 对 AI 更友好（schema、协商、通用客户端接入）。
- MCP 是“AI 与外部系统的标准连接层”，不只是 API 包装。

---

## 12. 你的下一步学习顺序（建议）

1. 先把单 Tool（天气）跑稳。
2. 增加一个 Resource（如城市天气说明文档）
3. 增加一个 Prompt（如“生成出行建议模板”）
4. 统一错误码和响应 schema。
5. 再考虑 HTTP 化与授权。

---

## 13. 一句话记忆

MCP = 用统一协议把外部能力标准化暴露给 AI：

- Host 是入口
- Client 负责通信
- Server 负责能力
- Resource 给模型看
- Tool 给模型做
- Prompt 给模型模板

---

## 14. 更新后的 Server 配置与文件清单

已更新 Server 文件：

- `mcp-server/weather-mcp-server.py`

包含能力：

- Tool：`get_weather_advice(prompt)`
- Prompt：`weather_trip_brief(city, day, activity)`

Claude Desktop 配置（可直接用）：

```json
{
  "mcpServers": {
    "weather-assistant": {
      "command": "E:\\\\mcp_project\\\\.venv\\\\Scripts\\\\mcp.exe",
      "args": [
        "run",
        "E:\\\\mcp_project\\\\mcp-server\\\\weather-mcp-server.py"
      ],
      "env": {
        "OPENWEATHER_API_KEY": "<YOUR_KEY>"
      }
    }
  }
}
```

---

## 15. 关键代码速查（可直接复制）

### 15.1 MCP Server 核心代码（Tool + Prompt）

文件：`mcp-server/weather-mcp-server.py`

```python
import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

API_URL = "https://api.openweathermap.org/assistant/session"
mcp = FastMCP("weather-assistant")


def call_weather_api(prompt: str) -> Dict[str, Any]:
    load_dotenv()
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY is missing. Please set it in .env")

    response = requests.post(
        API_URL,
        headers={"Content-Type": "application/json", "X-Api-Key": api_key},
        json={"prompt": prompt},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


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


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### 15.2 uv 启动命令

开发调试（Inspector）：

```powershell
cd E:\mcp_project
uv run --active mcp dev mcp-server\weather-mcp-server.py
```

标准运行（给客户端托管）：

```powershell
cd E:\mcp_project
uv run --active mcp run mcp-server\weather-mcp-server.py
```

如果 `mcp dev` 提示端口占用，先释放 6274/6277 再重启。

### 15.3 Claude Desktop MCP 项目配置

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

### 15.4 Cursor MCP 项目配置（示例）

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
