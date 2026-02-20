import os
import google.generativeai as genai


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text