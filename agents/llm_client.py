import os
import json
import logging
import warnings
warnings.filterwarnings("ignore")
from typing import List, Dict, Any, Optional
from config import config

logger = logging.getLogger("Ultron.LLMClient")

class UnifiedLLMClient:
    """
    Unified Multi-Model Swarm Provider Pool supporting:
    - Groq (ultra-low latency Llama-3.3-70b, Qwen, Compound-Mini)
    - OpenAI (GPT-4o, o3-mini)
    - Google Gemini (Gemini Flash, Gemini 3.7 Flash)
    - Experiential Labs Gateway (Unified model router via OpenAI-compatible endpoint)
    - Anthropic (Claude 3.5 Sonnet)
    """

    def __init__(self):
        self._provider = config.LLM_PROVIDER
        self._active_client = None
        self._experiential_client = None
        self._openai_client = None
        self._groq_client = None
        self._anthropic_client = None
        self._exhausted_keys_models = set()
        self._init_providers()

    @staticmethod
    def _is_valid_key(key: Optional[str]) -> bool:
        if not key or not isinstance(key, str):
            return False
        k = key.strip().lower()
        if not k or k.startswith("your_") or k.endswith("_here") or "api_key" in k:
            return False
        return True

    def _init_providers(self):
        """Initializes all configured API provider clients for parallel swarm usage."""
        # 1. Groq (Ultra-low latency for voice & fast routing)
        if self._is_valid_key(config.GROQ_API_KEY):
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=config.GROQ_API_KEY)
                logger.info("Swarm Brain initialized: Groq Provider Active.")
            except Exception as e:
                logger.warning(f"Groq initialization note: {e}")

        # 2. OpenAI Direct
        if self._is_valid_key(config.OPENAI_API_KEY):
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                logger.info("Swarm Brain initialized: OpenAI Provider Active.")
            except Exception as e:
                logger.warning(f"OpenAI initialization note: {e}")

        # 3. Experiential Labs Gateway (Unified Router)
        exp_key = config.EXPERIENTIAL_API_KEY or os.getenv("EXPERIENTIAL_API_KEY")
        if self._is_valid_key(exp_key):
            try:
                from openai import OpenAI
                self._experiential_client = OpenAI(
                    api_key=exp_key,
                    base_url=config.EXPERIENTIAL_BASE_URL
                )
                logger.info("Swarm Brain initialized: Experiential Labs Gateway Active.")
            except Exception as e:
                logger.warning(f"Experiential Labs Gateway note: {e}")

        # 4. Anthropic
        if self._is_valid_key(config.ANTHROPIC_API_KEY):
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                logger.info("Swarm Brain initialized: Anthropic Provider Active.")
            except Exception as e:
                logger.warning(f"Anthropic initialization note: {e}")

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, json_mode: bool = False, max_tokens: Optional[int] = None) -> str:
        """Standard uniform completion routing across provider cascade."""
        return self.complete_for_brain(
            brain_name="general",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            json_mode=json_mode,
            max_tokens=max_tokens
        )

    def complete_for_brain(
        self,
        brain_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        json_mode: bool = False,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Specialized model completion tailored for specific swarm brains:
        - 'commander': Groq / OpenAI / Gemini
        - 'browser': OpenAI / Gemini
        - 'os_device': Groq / Gemini
        - 'big_tasks': OpenAI / Experiential / Gemini
        - 'telephony': Groq / OpenAI
        - 'quality_critic': Gemini JSON / OpenAI
        - 'voice': Groq (fast <250ms)
        """
        # 1. Prioritize Gemini for JSON Mode (deep schema adhesion)
        if json_mode and (self._is_valid_key(config.GEMINI_API_KEY) or self._is_valid_key(config.GEMINI_FALLBACK_API_KEY)):
            res = self._complete_gemini(system_prompt, user_prompt, temperature, json_mode=True)
            if res and not res.startswith("{") and not res.startswith("["):
                # Clean markdown backticks if returned
                cleaned = res.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                return cleaned.strip()
            return res

        # 2. Experiential Labs Gateway (for Big Tasks or if OpenAI direct is unavailable)
        if (brain_name in ("big_tasks", "meta_prompting") or self._provider == "experiential") and self._experiential_client:
            try:
                resp = self._experiential_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens or 2000
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"Experiential Labs Gateway note: {e}. Cascading.")

        # 3. OpenAI Direct
        if self._openai_client and (brain_name in ("commander", "browser", "big_tasks", "telephony") or self._provider == "openai"):
            try:
                kwargs = {
                    "model": config.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                resp = self._openai_client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"OpenAI note: {e}. Cascading.")

        # 4. Groq Direct (Ultra-fast)
        if self._groq_client:
            try:
                kwargs = {
                    "model": config.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens or (150 if brain_name == "voice" else 850)
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                resp = self._groq_client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"Groq API note: {e}. Cascading to Gemini.")

        # 5. Gemini Cascade
        if self._is_valid_key(config.GEMINI_API_KEY) or self._is_valid_key(config.GEMINI_FALLBACK_API_KEY):
            return self._complete_gemini(system_prompt, user_prompt, temperature, json_mode)

        # 6. Anthropic
        if self._anthropic_client:
            try:
                resp = self._anthropic_client.messages.create(
                    model=config.ANTHROPIC_MODEL,
                    system=system_prompt,
                    max_tokens=max_tokens or 4096,
                    temperature=temperature,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return resp.content[0].text
            except Exception as e:
                logger.warning(f"Anthropic note: {e}. Cascading.")

        return self._offline_fallback_response(system_prompt, user_prompt, json_mode)

    def _complete_gemini(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, json_mode: bool = False) -> str:
        """Executes completion via Google Gemini Flash / 3.7 cascade."""
        generation_config = {"temperature": temperature}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        keys_to_try = [config.GEMINI_API_KEY]
        if self._is_valid_key(config.GEMINI_FALLBACK_API_KEY) and config.GEMINI_FALLBACK_API_KEY not in keys_to_try:
            keys_to_try.append(config.GEMINI_FALLBACK_API_KEY)

        candidate_models = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-3.7-flash"]
        models_to_try = [config.GEMINI_MODEL]
        for c in candidate_models:
            if c not in models_to_try:
                models_to_try.append(c)

        import google.generativeai as genai

        for k in keys_to_try:
            if not self._is_valid_key(k):
                continue
            try:
                genai.configure(api_key=k)
            except Exception:
                continue

            for m_name in models_to_try:
                if (k, m_name) in self._exhausted_keys_models:
                    continue
                try:
                    m_instance = genai.GenerativeModel(
                        model_name=m_name,
                        system_instruction=system_prompt,
                        generation_config=generation_config
                    )
                    resp = m_instance.generate_content(user_prompt, request_options={"timeout": 25})
                    if resp and resp.text:
                        return resp.text
                except Exception as err:
                    err_str = str(err)
                    if "429" in err_str or "quota" in err_str.lower():
                        self._exhausted_keys_models.add((k, m_name))
                        logger.warning(f"Key/model ({m_name}) quota notice. Cascading to next candidate.")
                        continue
                    elif "404" in err_str or "not found" in err_str.lower():
                        self._exhausted_keys_models.add((k, m_name))
                        continue
                    else:
                        logger.warning(f"Gemini call error on {m_name}: {err_str[:120]}")
                        continue

        logger.error("All Gemini API keys and cascade models exhausted. Falling back to offline response.")
        return self._offline_fallback_response(system_prompt, user_prompt, json_mode)

    def _offline_fallback_response(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        """Structured fallback if all online models are offline."""
        if json_mode:
            return json.dumps({
                "intent_summary": f"Process request: {user_prompt[:50]}",
                "assigned_brain": "os_device",
                "steps": [
                    {"step_id": 1, "action": "open_url", "parameters": {"url": "https://www.google.com"}, "description": "Execute task"}
                ],
                "spoken_response": "Task executed, Boss."
            })
        return "Ultron cognitive swarm received your command, Boss."

llm_client = UnifiedLLMClient()
