import argparse
import json
import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv

API_URL = "https://api.openweathermap.org/assistant/session"


def ask_weather_assistant(prompt: str) -> Dict[str, Any]:
    load_dotenv()

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("缺少 OPENWEATHER_API_KEY，请在 .env 中配置")

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
    }
    payload = {"prompt": prompt}

    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="调用 OpenWeather AI 天气助手 API")
    parser.add_argument(
        "--prompt",
        default=os.getenv("WEATHER_PROMPT", "What's weather like in London?"),
        help="向助手提问的天气相关问题",
    )
    args = parser.parse_args()

    result = ask_weather_assistant(args.prompt)

    print(f"User: {args.prompt}")
    print(f"Assistant: {result.get('answer', '')}")

    session_id = result.get("session_id")
    if session_id:
        print(f"Session ID: {session_id}")

    if "data" in result:
        print("Data:")
        print(json.dumps(result["data"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
