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
    Unified client supporting Groq, OpenAI, Anthropic, and Google Gemini APIs.
    Provides uniform interface for multi-agent reasoning and tool coordination.
    """

    def __init__(self):
        self._provider = config.LLM_PROVIDER
        self._active_client = None
        self._init_provider()

    @staticmethod
    def _is_valid_key(key: Optional[str]) -> bool:
        if not key or not isinstance(key, str):
            return False
        k = key.strip().lower()
        if not k or k.startswith("your_") or k.endswith("_here") or "api_key" in k:
            return False
        return True

    def _init_provider(self):
        """Initializes the preferred provider or searches for an available key."""
        # 1. Check Groq
        if (self._provider == "groq" or not self._active_client) and self._is_valid_key(config.GROQ_API_KEY):
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=config.GROQ_API_KEY)
                self._active_provider = "groq"
                self._active_client = self._groq_client
                logger.info("Ultron Brain initialized via Groq.")
                return
            except Exception as e:
                logger.warning(f"Failed to load Groq: {e}")

        # 2. Check OpenAI
        if (self._provider == "openai" or not self._active_client) and self._is_valid_key(config.OPENAI_API_KEY):
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                self._active_provider = "openai"
                self._active_client = self._openai_client
                logger.info("Ultron Brain initialized via OpenAI.")
                return
            except Exception as e:
                logger.warning(f"Failed to load OpenAI: {e}")

        # 3. Check Anthropic
        if (self._provider == "anthropic" or not self._active_client) and self._is_valid_key(config.ANTHROPIC_API_KEY):
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                self._active_provider = "anthropic"
                self._active_client = self._anthropic_client
                logger.info("Ultron Brain initialized via Anthropic.")
                return
            except Exception as e:
                logger.warning(f"Failed to load Anthropic: {e}")

        # 4. Check Google Gemini
        if (self._provider == "gemini" or not self._active_client) and self._is_valid_key(config.GEMINI_API_KEY):
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.GEMINI_API_KEY)
                self._active_provider = "gemini"
                self._active_client = genai
                logger.info("Ultron Brain initialized via Google Gemini.")
                return
            except Exception as e:
                logger.warning(f"Failed to load Gemini: {e}")

        self._active_provider = "unconfigured"
        logger.warning("No active LLM API key detected. Please configure GROQ_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY in .env.")

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, json_mode: bool = False) -> str:
        """
        Submits prompt to online LLM and returns text completion.
        """
        # Re-check in case .env was modified at runtime
        if self._active_provider == "unconfigured":
            self._init_provider()

        if self._active_provider == "groq":
            try:
                kwargs = {
                    "model": config.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                resp = self._active_client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"Groq API call error: {e}. Falling back to offline response.")
                return self._offline_fallback_response(system_prompt, user_prompt, json_mode)

        elif self._active_provider == "openai":
            try:
                kwargs = {
                    "model": config.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                resp = self._active_client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"OpenAI API call error: {e}. Falling back to offline response.")
                return self._offline_fallback_response(system_prompt, user_prompt, json_mode)

        elif self._active_provider == "anthropic":
            try:
                resp = self._active_client.messages.create(
                    model=config.ANTHROPIC_MODEL,
                    system=system_prompt,
                    max_tokens=4096,
                    temperature=temperature,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return resp.content[0].text
            except Exception as e:
                logger.error(f"Anthropic API call error: {e}. Falling back to offline response.")
                return self._offline_fallback_response(system_prompt, user_prompt, json_mode)

        elif self._active_provider == "gemini":
            generation_config = {"temperature": temperature}
            if json_mode:
                generation_config["response_mime_type"] = "application/json"

            keys_to_try = [config.GEMINI_API_KEY]
            if self._is_valid_key(config.GEMINI_FALLBACK_API_KEY) and config.GEMINI_FALLBACK_API_KEY not in keys_to_try:
                keys_to_try.append(config.GEMINI_FALLBACK_API_KEY)

            models_to_try = [config.GEMINI_MODEL]
            for candidate in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]:
                if candidate not in models_to_try:
                    models_to_try.append(candidate)

            import google.generativeai as genai

            for k in keys_to_try:
                genai.configure(api_key=k)
                for m_name in models_to_try:
                    try:
                        m_instance = genai.GenerativeModel(
                            model_name=m_name,
                            system_instruction=system_prompt,
                            generation_config=generation_config
                        )
                        resp = m_instance.generate_content(user_prompt)
                        return resp.text
                    except Exception as err:
                        err_str = str(err)
                        if "429" in err_str or "quota" in err_str.lower():
                            logger.warning(f"Model {m_name} quota exceeded. Cascading to next available model...")
                            continue
                        elif "404" in err_str or "not found" in err_str.lower():
                            continue
                        else:
                            logger.warning(f"Gemini call error on {m_name}: {err_str[:120]}")
                            continue

            logger.error("All Gemini API keys and cascade models exhausted. Falling back to offline response.")
            return self._offline_fallback_response(system_prompt, user_prompt, json_mode)

        # Offline Mock Fallback for local testing when no keys are configured yet
        return self._offline_fallback_response(system_prompt, user_prompt, json_mode)

    def _offline_fallback_response(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        """Provides graceful structured mock responses if API keys are not yet entered."""
        lower_sys = system_prompt.lower()
        lower_prompt = user_prompt.lower()

        # Handle Coder agent requests
        if "coder" in lower_sys or "files" in lower_sys or "generate full" in lower_sys:
            if json_mode:
                return json.dumps({
                    "files": {
                        "main.py": '# Ultron Generated Python Script\ndef main():\n    print("Hello from Ultron!")\n\nif __name__ == "__main__":\n    main()\n'
                    },
                    "summary": "Generated starter Python application."
                })

        # Handle Thinker agent requests
        if "thinker" in lower_sys or "system architect" in lower_sys:
            if "chrome" in lower_prompt or "browser" in lower_prompt:
                action_plan = {
                    "intent_summary": "Open Google Chrome browser",
                    "requires_confirmation": False,
                    "confirmation_reason": None,
                    "steps": [
                        {"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": "chrome"}, "description": "Open Google Chrome"}
                    ],
                    "spoken_response": "Opening Google Chrome now."
                }
            elif "vpn" in lower_prompt:
                action_plan = {
                    "intent_summary": "Connect to VPN",
                    "requires_confirmation": False,
                    "confirmation_reason": None,
                    "steps": [
                        {"step_id": 1, "assigned_agent": "Executor", "action": "connect_vpn", "parameters": {"country": "Germany"}, "description": "Connect VPN"}
                    ],
                    "spoken_response": "Connecting your VPN now."
                }
            else:
                action_plan = {
                    "intent_summary": f"Process request: {user_prompt[:50]}",
                    "requires_confirmation": False,
                    "confirmation_reason": None,
                    "steps": [
                        {"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": "notepad"}, "description": "Execute task"}
                    ],
                    "spoken_response": "Task completed successfully."
                }
            if json_mode:
                return json.dumps(action_plan)

        if "chrome" in lower_prompt or "browser" in lower_prompt:
            action_plan = {
                "action": "open_app",
                "target": "chrome",
                "explanation": "Opening Google Chrome as requested."
            }
        elif "vpn" in lower_prompt:
            action_plan = {
                "action": "connect_vpn",
                "target": "germany",
                "explanation": "Connecting to VPN server in Germany."
            }
        elif "folder" in lower_prompt or "file" in lower_prompt:
            action_plan = {
                "action": "create_folder",
                "target": "UltronProjects/NewProject",
                "explanation": "Creating project workspace directory."
            }
        else:
            action_plan = {
                "action": "chat",
                "target": "user",
                "explanation": f"Ultron received command: '{user_prompt}'. (Note: Add your GROQ_API_KEY in .env for full autonomous online reasoning)."
            }

        if json_mode:
            return json.dumps(action_plan)
        return action_plan["explanation"]

llm_client = UnifiedLLMClient()
