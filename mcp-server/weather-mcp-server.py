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
    """Ask OpenWeather AI Weather Assistant with a natural language prompt."""
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
            "error": f"HTTP error {status}: {detail}".strip(),
        }
    except requests.exceptions.ProxyError as exc:
        return {"ok": False, "error": f"Proxy error: {exc}"}
    except requests.exceptions.Timeout as exc:
        return {"ok": False, "error": f"Request timeout: {exc}"}
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "error": f"Request failed: {exc}"}


@mcp.prompt(
    name="weather_trip_brief",
    description="Template for weather-aware travel/outdoor planning that uses get_weather_advice.",
)
def weather_trip_brief(city: str, day: str = "today", activity: str = "outdoor travel") -> str:
    """Generate a reusable prompt template and tell the model to call weather tool first."""
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
