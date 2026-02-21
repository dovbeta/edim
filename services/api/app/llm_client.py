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

    async def generate(self, message, context=None, history=None):
        prompt = self._build_prompt(message, context, history)
        response = self.model.generate_content(prompt)
        return response.text

    # -------------------------------------------------

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