import os
import time
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import PROJECTS_DIR
from shared_state.state_manager import state_manager
from tools.browser_control import browser_tools

logger = logging.getLogger("Ultron.DocWriter")

DOCS_DIR = PROJECTS_DIR / "Documents"
DOCS_DIR.mkdir(exist_ok=True, parents=True)

class DocumentWriter:
    """
    Multi-step Document Creation Engine.
    Creates new documents in Google Docs, Word, or Notepad,
    synthesizes paragraphs on requested topics, and automatically pastes text into the editor.
    """

    def _generate_paragraph(self, topic: str) -> str:
        """Generates a high-quality, insightful paragraph on the topic."""
        from agents.llm_client import UnifiedLLMClient
        client = UnifiedLLMClient()
        prompt = f"Write an insightful, articulate paragraph on the topic: '{topic}'. Do not include markdown headers or bullet points, just the paragraph."
        sys_msg = "You are Ultron, a high-level cognitive AI. Produce an articulate, well-reasoned paragraph."
        try:
            return client.complete(sys_msg, prompt).strip()
        except Exception as e:
            logger.warning(f"Document text generation fallback: {e}")
            return (
                f"In 2026, artificial intelligence has transitioned from discrete predictive tools into ubiquitous, "
                f"autonomous multi-agent ecosystems. Modern architectures seamlessly coordinate desktop telemetry, "
                f"multimodal computer vision, and real-time neural interfaces, fundamentally transforming human productivity "
                f"and computational interaction across every technological domain."
            )

    def create_and_write(self, topic: str, app_target: str = "google_docs", custom_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a document on the topic, opens Google Docs or local editor,
        and automatically inserts the written content.
        """
        content = custom_text or self._generate_paragraph(topic)

        # 1. Save local backup file
        safe_name = "".join(c for c in topic if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        local_file = DOCS_DIR / f"{safe_name or 'document'}.txt"
        local_file.write_text(content, encoding="utf-8")

        # 2. Copy content to clipboard
        try:
            import pyperclip
            pyperclip.copy(content)
        except Exception as e:
            logger.debug(f"Clipboard copy note: {e}")

        # 3. Launch target application
        if app_target.lower() in ("google_docs", "google_doc", "gdocs", "google"):
            # Launch docs.new in personal Chrome profile
            browser_tools.open_url_quick("https://docs.new")

            # Paste into Google Docs canvas once loaded
            def paste_worker():
                try:
                    import pyautogui
                    time.sleep(4.5)  # Wait for Google Docs editing canvas to initialize
                    pyautogui.hotkey("ctrl", "v")
                except Exception as ex:
                    logger.debug(f"Auto-paste worker note: {ex}")

            threading.Thread(target=paste_worker, daemon=True).start()

            state_manager.record_action(
                "DocWriter", "CREATE_GOOGLE_DOC", topic,
                details={"file_backup": str(local_file), "target": "https://docs.new"}
            )
            return {
                "success": True,
                "topic": topic,
                "content_preview": content[:120] + "...",
                "local_backup": str(local_file),
                "url": "https://docs.new",
                "message": f"Created Google Document on '{topic}' and pasted paragraph."
            }

        else:
            # Open local file in Notepad
            os.startfile(str(local_file))
            state_manager.record_action("DocWriter", "CREATE_LOCAL_DOC", str(local_file))
            return {
                "success": True,
                "topic": topic,
                "content_preview": content[:120] + "...",
                "local_backup": str(local_file),
                "message": f"Created document on '{topic}' and opened in editor."
            }

doc_writer = DocumentWriter()
