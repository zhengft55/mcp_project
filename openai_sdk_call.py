import os

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv()

    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "openai/gpt-5.2")
    prompt = os.getenv("OPENAI_PROMPT", "What is the meaning of life?")
    referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
    title = os.getenv("OPENROUTER_APP_TITLE", "")

    if not api_key:
        raise ValueError("缺少 OPENAI_API_KEY，请在 .env 中配置")

    client = OpenAI(api_key=api_key, base_url=base_url)

    extra_headers = {}
    if referer:
        extra_headers["HTTP-Referer"] = referer
    if title:
        extra_headers["X-OpenRouter-Title"] = title

    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        extra_headers=extra_headers or None,
    )

    print(completion.choices[0].message.content or "")


if __name__ == "__main__":
    main()
