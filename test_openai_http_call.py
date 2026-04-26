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
        self.assertTrue(api_key, "OPENAI_API_KEY is missing in .env")
        self.assertNotIn("your_api_key_here", api_key, "Please set a real OPENAI_API_KEY")

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            openai_http_call.main()

        output = buffer.getvalue().strip()
        self.assertTrue(output, "HTTP API response is empty")
        print(f"User: {prompt}")
        print(f"Assistant: {output}")


if __name__ == "__main__":
    unittest.main()
