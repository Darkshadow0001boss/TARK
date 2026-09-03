import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai

from app.ai.provider import AIProvider


load_dotenv()


class GeminiProvider(AIProvider):
    """
    Gemini implementation of TARK's AIProvider interface.
    """

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from .env")

        self.client = genai.Client(api_key=api_key)

    def generate_json(
        self,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Send a prompt to Gemini and return a JSON dictionary.
        """

        response = self.client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response")

        try:
            return json.loads(response.text)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Gemini returned invalid JSON: {response.text}"
            ) from error