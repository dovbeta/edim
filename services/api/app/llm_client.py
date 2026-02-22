import os
import json
import google.generativeai as genai


class GeminiClient:
    SYSTEM_PROMPT = (
        "Ти — AI-помічник ОСББ E-Dim. "
        "Відповідай українською, коротко і по суті."
    )

    MAX_HISTORY_CHARS = 2000

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    # =================================================
    # CHAT MODE (Responder)
    # =================================================

    async def generate(self, message, context=None, history=None):
        """
        Conversational generation (existing behavior)
        """
        prompt = self._build_prompt(message, context, history)
        response = self.model.generate_content(prompt)
        return self._extract_text(response)

    # =================================================
    # PLANNER MODE (SQL / structured)
    # =================================================

    async def generate_text(self, prompt: str) -> str:
        """
        Raw prompt → text
        Used by Planner
        """
        response = self.model.generate_content(prompt)
        return self._extract_text(response)

    async def generate_json(self, prompt: str, retries: int = 2) -> dict:
        """
        Raw prompt → JSON
        Used by Planner
        """
        json_prompt = f"Return ONLY valid JSON.\n\n{prompt}"

        last_text = ""

        for _ in range(retries + 1):
            last_text = await self.generate_text(json_prompt)

            try:
                start = last_text.find("{")
                end = last_text.rfind("}") + 1
                return json.loads(last_text[start:end])
            except Exception:
                continue

        raise ValueError(f"Invalid JSON from LLM: {last_text}")

    # =================================================
    # INTERNAL
    # =================================================

    def _build_prompt(self, message, context, history):

        parts = []

        # SYSTEM
        parts.append(f"[СИСТЕМА]\n{self.SYSTEM_PROMPT}")

        # DOMAIN CONTEXT
        if context:
            parts.append(
                "[ДАНІ КОРИСТУВАЧА]\n"
                + json.dumps(context, ensure_ascii=False, indent=2)
            )

        # HISTORY
        if history and len(history) > 0:
            hist_lines = []
            for m in history:
                role = "Користувач" if m["role"] == "user" else "Помічник"
                hist_lines.append(f"{role}: {m['content']}")

            hist_text = "\n".join(hist_lines)

            if len(hist_text) > self.MAX_HISTORY_CHARS:
                hist_text = hist_text[-self.MAX_HISTORY_CHARS:]

            parts.append("[ІСТОРІЯ ДІАЛОГУ]\n" + hist_text)

        # USER
        parts.append(f"[ЗАПИТ КОРИСТУВАЧА]\n{message}")

        return "\n\n".join(parts)

    def _extract_text(self, response):
        """
        Safe extraction from Gemini response
        """
        if hasattr(response, "text") and response.text:
            return response.text

        try:
            return response.candidates[0].content.parts[0].text
        except Exception:
            return str(response)