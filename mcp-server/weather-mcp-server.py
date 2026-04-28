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
        raise ValueError("缺少 OPENWEATHER_API_KEY，请在 .env 中配置")

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json={"prompt": prompt},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@mcp.tool()
def get_weather_advice(prompt: str) -> Dict[str, Any]:
    """通过自然语言提问调用 OpenWeather AI 天气助手。"""
    try:
        result = call_weather_api(prompt)
        return {
            "ok": True,
            "answer": result.get("answer", ""),
            "session_id": result.get("session_id"),
            "data": result.get("data", {}),
        }
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        detail = ""
        if exc.response is not None:
            try:
                detail = exc.response.text
            except Exception:
                detail = ""
        return {
            "ok": False,
            "error": f"HTTP 错误 {status}：{detail}".strip(),
        }
    except requests.exceptions.ProxyError as exc:
        return {"ok": False, "error": f"代理错误：{exc}"}
    except requests.exceptions.Timeout as exc:
        return {"ok": False, "error": f"请求超时：{exc}"}
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "error": f"请求失败：{exc}"}


@mcp.prompt(
    name="weather_trip_brief",
    description="天气感知型出行/户外规划模板，引导模型调用 get_weather_advice。",
)
def weather_trip_brief(city: str, day: str = "today", activity: str = "outdoor travel") -> str:
    """生成可复用的 prompt 模板，并指示模型先调用天气工具再总结。"""
    return (
        "You are a weather-aware travel assistant.\n"
        f"The user plans {activity} in {city} on {day}.\n"
        "First call tool `get_weather_advice` with a clear weather question.\n"
        "Then provide:\n"
        "1) Short weather summary\n"
        "2) Risk alerts (rain/wind/visibility/temperature)\n"
        "3) Clothing and timing suggestions\n"
        "4) Whether to proceed with the activity\n"
        f"Tool input suggestion: What's weather like in {city} on {day}?"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
