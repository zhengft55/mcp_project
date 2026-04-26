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

    raise RuntimeError(f"HTTP request failed after retries: {last_error}")


def get_weather_advice(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "error": "OPENWEATHER_API_KEY is missing. Please set it in .env",
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
        return {"ok": False, "error": f"Weather API request failed: {exc}"}


def main() -> None:
    load_dotenv()

    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "openai/gpt-5.2")
    prompt = os.getenv("OPENAI_PROMPT", "What's weather like in London?")
    referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
    title = os.getenv("OPENROUTER_APP_TITLE", "")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Please set it in .env")

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
                "description": "Get weather advice and weather data for a specific query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Weather question with location, for example: What's weather like in London?",
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
                result = {"ok": False, "error": f"Unknown tool: {name}"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError("Model did not produce a final response after tool calls")


if __name__ == "__main__":
    main()
