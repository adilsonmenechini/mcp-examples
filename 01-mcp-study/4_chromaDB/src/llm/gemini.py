import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class GeminiClient:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model
        self.config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT"],
        )

    async def generate(self, contents):
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=self.config
        )
        return response.text