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

    def create_and_write(
        self,
        topic: str,
        app_target: str = "google_docs",
        custom_text: Optional[str] = None,
        target_folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a document on the topic, opens Google Docs or local editor,
        saves to target folder (e.g. 'Voice model testing' on Desktop),
        and automatically inserts the written content.
        """
        content = custom_text or self._generate_paragraph(topic)
        safe_name = "".join(c for c in topic if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_") or "Document"

        # Determine target directory
        dest_dir = DOCS_DIR
        if target_folder:
            desktop = Path.home() / "Desktop" / target_folder
            dest_dir = desktop
            dest_dir.mkdir(parents=True, exist_ok=True)
            # Also keep workspace backup
            (PROJECTS_DIR / target_folder).mkdir(parents=True, exist_ok=True)

        # 1. Save TXT backup
        local_txt = dest_dir / f"{safe_name}.txt"
        local_txt.write_text(content, encoding="utf-8")

        # 2. Save native Word DOCX
        local_docx = dest_dir / f"{safe_name}.docx"
        try:
            import docx
            doc = docx.Document()
            doc.add_heading(topic, level=1)
            doc.add_paragraph(content)
            doc.save(str(local_docx))
        except Exception as e:
            logger.debug(f"DOCX generation note: {e}")

        # 3. Copy content to clipboard
        try:
            import pyperclip
            pyperclip.copy(content)
        except Exception as e:
            logger.debug(f"Clipboard copy note: {e}")

        # 4. Open destination folder in Windows Explorer if custom folder requested
        if target_folder:
            try:
                import subprocess
                subprocess.Popen(["explorer.exe", str(dest_dir)], shell=False)
            except Exception:
                pass

        # 5. Launch target application
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
                details={"folder": str(dest_dir), "txt": str(local_txt), "docx": str(local_docx), "target": "https://docs.new"}
            )
            return {
                "success": True,
                "topic": topic,
                "content_preview": content[:120] + "...",
                "folder": str(dest_dir),
                "files": [str(local_txt), str(local_docx)],
                "url": "https://docs.new",
                "message": f"Created Google Document on '{topic}', saved in '{dest_dir.name}', and opened folder."
            }

        else:
            # Open local file in default editor
            os.startfile(str(local_docx if local_docx.exists() else local_txt))
            state_manager.record_action("DocWriter", "CREATE_LOCAL_DOC", str(dest_dir))
            return {
                "success": True,
                "topic": topic,
                "content_preview": content[:120] + "...",
                "folder": str(dest_dir),
                "files": [str(local_txt), str(local_docx)],
                "message": f"Created document on '{topic}' in '{dest_dir.name}' and opened in editor."
            }

doc_writer = DocumentWriter()
