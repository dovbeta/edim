import os
import json
from typing import Any, Dict, List, Optional
import google.generativeai as genai
from .base import LLMClient
from policy.edim_policy import Policy


class GeminiClient(LLMClient):
    MAX_HISTORY_CHARS = 2000

    def __init__(self, system_prompt: str, model_name: str = "gemini-2.5-flash"):
        self.system_prompt = system_prompt
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def generate(
        self,
        message: str,
        context: Optional[Dict] = None,
        history: Optional[List] = None,
        policy: Optional[Policy] = None
    ) -> str:
        prompt = self._build_prompt(message, context, history, policy)
        response = self.model.generate_content(prompt)
        return self._extract_text(response)

    async def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return self._extract_text(response)

    async def generate_json(self, prompt: str, retries: int = 2) -> Dict[str, Any]:
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

    def _build_prompt(
        self,
        message: str,
        context: Optional[Dict],
        history: Optional[List],
        policy: Optional[Policy] = None
    ) -> str:
        parts = []

        # SYSTEM
        system = self.system_prompt
        if policy:
            system += f"\n\nUser role: {policy.role_name}\n\nAccess policy:\n{policy.to_str()}"

        parts.append(f"[СИСТЕМА]\n{system.strip()}")

        # DOMAIN CONTEXT
        if context:
            parts.append(
                "[КОНТЕКСТ]\n"
                + json.dumps(context, ensure_ascii=False, indent=2)
            )

        # HISTORY
        if history and len(history) > 0:
            hist_lines = []
            for m in history:
                role = "Користувач" if m.get("role") == "user" else "Помічник"
                # Handle different history formats if needed, assuming the same as before
                content = m.get("content") or m.get("text")
                hist_lines.append(f"{role}: {content}")

            hist_text = "\n".join(hist_lines)

            if len(hist_text) > self.MAX_HISTORY_CHARS:
                hist_text = hist_text[-self.MAX_HISTORY_CHARS:]

            parts.append("[ІСТОРІЯ ДІАЛОГУ]\n" + hist_text)

        # USER
        parts.append(f"[ЗАПИТ КОРИСТУВАЧА]\n{message}")

        return "\n\n".join(parts)

    def _extract_text(self, response: Any) -> str:
        if hasattr(response, "text") and response.text:
            return response.text

        try:
            return response.candidates[0].content.parts[0].text
        except Exception:
            return str(response)
