import io
import os
import unittest
from contextlib import redirect_stdout

from dotenv import load_dotenv

import openai_http_call


class TestOpenAIHTTPCallReal(unittest.TestCase):
    def test_http_real_request(self) -> None:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY", "")
        prompt = os.getenv("OPENAI_PROMPT", "")
        self.assertTrue(api_key, "OPENAI_API_KEY 未在 .env 中配置")
        self.assertNotIn("your_api_key_here", api_key, "请在 .env 中配置真实的 OPENAI_API_KEY")

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            openai_http_call.main()

        output = buffer.getvalue().strip()
        self.assertTrue(output, "HTTP API 响应为空")
        print(f"User: {prompt}")
        print(f"Assistant: {output}")


if __name__ == "__main__":
    unittest.main()
