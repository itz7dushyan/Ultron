import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from send2trash import send2trash
from shared_state.state_manager import state_manager
from tools.safety_sentinel import safety_sentinel

class FileTools:
    """File and directory operations for Ultron with safety integration."""

    @staticmethod
    def resolve_path(path_str: str) -> Path:
        """Resolves user path, expanding ~ and Desktop/Documents if mentioned."""
        path = Path(path_str).expanduser()
        if not path.is_absolute():
            # If relative, resolve relative to current user profile or Ultron project
            path = (Path.home() / path_str).resolve()
        return path

    def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """Creates a directory and intermediate folders."""
        target = self.resolve_path(dir_path)
        try:
            target.mkdir(parents=True, exist_ok=True)
            state_manager.record_action("FileTools", "CREATE_DIRECTORY", str(target), status="success")
            return {"success": True, "path": str(target), "message": f"Directory created: {target}"}
        except Exception as e:
            state_manager.record_action("FileTools", "CREATE_DIRECTORY", str(target), details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Writes or updates text content in a file."""
        target = self.resolve_path(file_path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            state_manager.record_action("FileTools", "WRITE_FILE", str(target), details={"bytes": len(content)}, status="success")
            return {"success": True, "path": str(target), "message": f"File written successfully ({len(content)} bytes)"}
        except Exception as e:
            state_manager.record_action("FileTools", "WRITE_FILE", str(target), details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def read_file(self, file_path: str, max_bytes: int = 100_000) -> Dict[str, Any]:
        """Reads content of a file."""
        target = self.resolve_path(file_path)
        if not target.exists():
            return {"success": False, "error": f"File not found: {target}"}
        try:
            content = target.read_text(encoding="utf-8", errors="replace")[:max_bytes]
            state_manager.record_action("FileTools", "READ_FILE", str(target), status="success")
            return {"success": True, "path": str(target), "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_path(self, target_path: str) -> Dict[str, Any]:
        """Safely moves a file or folder to the Windows Recycle Bin."""
        target = self.resolve_path(target_path)
        if not target.exists():
            return {"success": False, "error": f"Target not found: {target}"}

        # Security check: prompt user before deletion
        if not safety_sentinel.authorize("DELETE_PATH", str(target), "Will move target to Recycle Bin"):
            state_manager.record_action("FileTools", "DELETE_PATH", str(target), details="Blocked by user", status="cancelled")
            return {"success": False, "cancelled": True, "message": "Deletion cancelled by user"}

        try:
            send2trash(str(target))
            state_manager.record_action("FileTools", "DELETE_PATH", str(target), details="Moved to Recycle Bin", status="success")
            return {"success": True, "message": f"Moved to Recycle Bin: {target}"}
        except Exception as e:
            state_manager.record_action("FileTools", "DELETE_PATH", str(target), details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def move_file(self, source_path: str, dest_path: str) -> Dict[str, Any]:
        """Moves or renames a file or folder."""
        src = self.resolve_path(source_path)
        dst = self.resolve_path(dest_path)
        if not src.exists():
            return {"success": False, "error": f"Source not found: {src}"}
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            state_manager.record_action("FileTools", "MOVE_PATH", f"{src} -> {dst}", status="success")
            return {"success": True, "from": str(src), "to": str(dst)}
        except Exception as e:
            state_manager.record_action("FileTools", "MOVE_PATH", f"{src} -> {dst}", details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def search_files(self, directory: str, pattern: str = "*", recursive: bool = True) -> Dict[str, Any]:
        """Searches for files matching a pattern."""
        root = self.resolve_path(directory)
        if not root.exists() or not root.is_dir():
            return {"success": False, "error": f"Directory not found: {root}"}
        try:
            matches = []
            generator = root.rglob(pattern) if recursive else root.glob(pattern)
            for item in generator:
                matches.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0
                })
                if len(matches) >= 50: # Limit output
                    break
            return {"success": True, "total": len(matches), "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_directory(self, directory: str) -> Dict[str, Any]:
        """Lists files and folders inside a directory."""
        root = self.resolve_path(directory)
        if not root.exists() or not root.is_dir():
            return {"success": False, "error": f"Directory not found: {root}"}
        try:
            items = []
            for entry in root.iterdir():
                items.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else None
                })
            return {"success": True, "path": str(root), "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

file_tools = FileTools()
