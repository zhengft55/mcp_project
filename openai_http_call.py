import json
import os
import time
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

WEATHER_API_URL = "https://api.openweathermap.org/assistant/session"


def post_chat_completion(
    endpoint: str, headers: Dict[str, str], payload: Dict[str, Any]
) -> Dict[str, Any]:
    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ChunkedEncodingError as exc:
            last_error = exc
            if attempt == 2:
                raise
            time.sleep(1 + attempt)

    raise RuntimeError(f"HTTP 请求重试后仍失败：{last_error}")


def get_weather_advice(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "error": "缺少 OPENWEATHER_API_KEY，请在 .env 中配置",
        }

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
    }

    try:
        response = requests.post(
            WEATHER_API_URL,
            headers=headers,
            json={"prompt": prompt},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return {
            "ok": True,
            "answer": result.get("answer", ""),
            "session_id": result.get("session_id"),
            "data": result.get("data", {}),
        }
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "error": f"天气 API 请求失败：{exc}"}


def main() -> None:
    load_dotenv()

    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "openai/gpt-5.2")
    prompt = os.getenv("OPENAI_PROMPT", "What's weather like in London?")
    referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
    title = os.getenv("OPENROUTER_APP_TITLE", "")

    if not api_key:
        raise ValueError("缺少 OPENAI_API_KEY，请在 .env 中配置")

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-OpenRouter-Title"] = title

    tools: List[Dict[str, Any]] = [
        {
            "type": "function",
            "function": {
                "name": "get_weather_advice",
                "description": "针对具体的天气问题获取建议与结构化天气数据。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "包含地点的天气提问，例如：伦敦今天天气怎么样？",
                        }
                    },
                    "required": ["prompt"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": "Use weather tool when user asks weather/travel/outdoor planning questions.",
        },
        {"role": "user", "content": prompt},
    ]

    for _ in range(3):
        payload = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }

        data = post_chat_completion(endpoint, headers, payload)
        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            print(message.get("content", ""))
            return

        messages.append(
            {
                "role": "assistant",
                "content": message.get("content", ""),
                "tool_calls": tool_calls,
            }
        )

        for tool_call in tool_calls:
            name = tool_call.get("function", {}).get("name")
            raw_args = tool_call.get("function", {}).get("arguments", "{}")
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}

            if name == "get_weather_advice":
                result = get_weather_advice(args.get("prompt", ""))
            else:
                result = {"ok": False, "error": f"未知工具：{name}"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError("模型在工具调用后未给出最终回复")


if __name__ == "__main__":
    main()
