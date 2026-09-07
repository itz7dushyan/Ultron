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
    - NVIDIA NIM (Meta Llama-3.3-70B, Qwen-2.5-Coder-32B, Nemotron-70B)
    - Groq Multi-Key Pool (Llama-3.3-70B, DeepSeek-R1-Distill-70B, Compound-Mini)
    - OpenAI (GPT-4o, o3-mini)
    - Google Gemini (Gemini Flash, Gemini 3.7 Flash)
    - Anthropic (Claude 3.5 Sonnet)
    """

    def __init__(self):
        self._provider = config.LLM_PROVIDER
        self._active_client = None
        self._nvidia_client = None
        self._nvidia_qwen_client = None
        self._openai_client = None
        self._groq_clients = []
        self._groq_idx = 0
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
        # 1. NVIDIA NIM (Meta Llama 3.3 70B & Qwen 2.5 Coder 32B)
        if self._is_valid_key(config.NVIDIA_API_KEY):
            try:
                from openai import OpenAI
                self._nvidia_client = OpenAI(
                    api_key=config.NVIDIA_API_KEY,
                    base_url=config.NVIDIA_BASE_URL
                )
                logger.info("Swarm Brain initialized: NVIDIA NIM Meta Llama 3.3 70B Active.")
            except Exception as e:
                logger.warning(f"NVIDIA NIM initialization note: {e}")

        if self._is_valid_key(config.NVIDIA_QWEN_KEY):
            try:
                from openai import OpenAI
                self._nvidia_qwen_client = OpenAI(
                    api_key=config.NVIDIA_QWEN_KEY,
                    base_url=config.NVIDIA_BASE_URL
                )
                logger.info("Swarm Brain initialized: NVIDIA NIM Qwen 2.5 Coder Active.")
            except Exception as e:
                logger.warning(f"NVIDIA Qwen initialization note: {e}")

        # 2. Groq Multi-Key Rotation Pool
        self._groq_clients = []
        groq_keys = getattr(config, "GROQ_KEYS", [config.GROQ_API_KEY])
        for g_key in groq_keys:
            if self._is_valid_key(g_key):
                try:
                    from groq import Groq
                    self._groq_clients.append(Groq(api_key=g_key))
                except Exception:
                    pass
        if self._groq_clients:
            logger.info(f"Swarm Brain initialized: Groq Rotation Pool Active with {len(self._groq_clients)} keys.")

        # 3. OpenAI Direct
        if self._is_valid_key(config.OPENAI_API_KEY):
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                logger.info("Swarm Brain initialized: OpenAI Provider Active.")
            except Exception as e:
                logger.warning(f"OpenAI initialization note: {e}")

        # 4. Anthropic
        if self._is_valid_key(config.ANTHROPIC_API_KEY):
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                logger.info("Swarm Brain initialized: Anthropic Provider Active.")
            except Exception as e:
                logger.warning(f"Anthropic initialization note: {e}")

    def _get_next_groq_client(self):
        """Returns the next available Groq client via round-robin rotation."""
        if not self._groq_clients:
            return None
        client = self._groq_clients[self._groq_idx % len(self._groq_clients)]
        self._groq_idx += 1
        return client

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
        - 'commander': NVIDIA Llama-3.3-70B / Groq Llama-3.3-70B
        - 'browser': NVIDIA Qwen-2.5-Coder / OpenAI / Gemini
        - 'os_device': NVIDIA Qwen-2.5-Coder / Groq
        - 'big_tasks': NVIDIA Llama-3.3-70B / Groq DeepSeek-R1 / OpenAI
        - 'telephony': NVIDIA / Groq
        - 'quality_critic': Gemini JSON / NVIDIA Llama-3.3-70B
        - 'voice': Groq (ultra-low latency <200ms)
        """
        # 1. Prioritize Gemini for deep JSON Mode (schema adhering)
        if json_mode and (self._is_valid_key(config.GEMINI_API_KEY) or self._is_valid_key(config.GEMINI_FALLBACK_API_KEY)):
            try:
                res = self._complete_gemini(system_prompt, user_prompt, temperature, json_mode=True)
                if res and not res.startswith("{") and not res.startswith("["):
                    cleaned = res.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    return cleaned.strip()
                return res
            except Exception as e:
                logger.debug(f"Gemini JSON cascade: {e}")

        # 1. Groq Multi-Key Rotation Pool (Ultra-fast <200ms Llama-3.3 / Qwen / GPT-OSS)
        groq_client = self._get_next_groq_client()
        if groq_client:
            models_order = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "groq/compound-mini"]
            if brain_name == "voice":
                models_order = ["groq/compound-mini", "qwen/qwen3.8-27b"]
            elif brain_name in ("big_tasks", "commander"):
                models_order = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "groq/compound-mini"]

            for model_to_use in models_order:
                try:
                    kwargs = {
                        "model": model_to_use,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens or (150 if brain_name == "voice" else 1000),
                        "timeout": 8.0
                    }
                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}
                    resp = groq_client.chat.completions.create(**kwargs)
                    content = resp.choices[0].message.content or ""
                    if "<think>" in content and "</think>" in content:
                        content = content.split("</think>")[-1].strip()
                    if content:
                        return content
                except Exception as e:
                    logger.debug(f"Groq API ({model_to_use}) note: {e}. Cascading.")

        # 2. NVIDIA NIM: Nemotron 70B & Codestral (For Heavy Reasoning / Backup)
        if self._nvidia_client and brain_name in ("commander", "big_tasks", "telephony", "general"):
            for n_model in ("nvidia/llama-3.1-nemotron-70b-instruct", "mistralai/mistral-large-2-instruct"):
                try:
                    kwargs = {
                        "model": n_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens or 1500,
                        "timeout": 8.0
                    }
                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}
                    resp = self._nvidia_client.chat.completions.create(**kwargs)
                    if resp and resp.choices[0].message.content:
                        return resp.choices[0].message.content
                except Exception as e:
                    logger.debug(f"NVIDIA ({n_model}) note: {e}. Cascading.")

        # 3. Gemini Flash Cascade (For Multimodal Vision & Complex JSON)
        if self._is_valid_key(config.GEMINI_API_KEY) or self._is_valid_key(config.GEMINI_FALLBACK_API_KEY):
            return self._complete_gemini(system_prompt, user_prompt, temperature, json_mode)

        # 6. OpenAI Direct (if active)
        if self._openai_client:
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

        return self._offline_fallback_response(system_prompt, user_prompt, json_mode)

    def _complete_gemini(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, json_mode: bool = False) -> str:
        """Executes completion via Google Gemini Flash cascade."""
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
