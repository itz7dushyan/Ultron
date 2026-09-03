import ast
from pathlib import Path
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from tools.shell_control import shell_tools
from tools.file_ops import file_tools

class QAAgent(BaseAgent):
    """
    QA / Debugger Agent: Verifies code syntax, runs unit tests, analyzes logs,
    and reports issues or suggested fixes.
    """

    def __init__(self):
        super().__init__(
            name="QA_Debugger",
            role_description="Quality assurance engineer, syntax validator, and bug debugger."
        )

    def verify_python_syntax(self, file_path: str) -> Dict[str, Any]:
        """Validates Python syntax using AST parsing."""
        read_res = file_tools.read_file(file_path)
        if not read_res.get("success"):
            return {"passed": False, "error": read_res.get("error")}

        code_str = read_res.get("content", "")
        try:
            ast.parse(code_str)
            self.log("SYNTAX_CHECK", target=file_path, status="passed")
            return {"passed": True, "message": "Syntax validation passed with zero errors."}
        except SyntaxError as e:
            err_details = f"Line {e.lineno}, col {e.offset}: {e.msg}"
            self.log("SYNTAX_CHECK", target=file_path, details=err_details, status="failed")
            return {"passed": False, "error": err_details, "line": e.lineno}

    def run_automated_test(self, test_command: str, cwd: str) -> Dict[str, Any]:
        """Runs a test command in the project directory and analyzes output."""
        res = shell_tools.execute_command(test_command, cwd=cwd)
        passed = res.get("success", False) and res.get("exit_code", -1) == 0

        self.log(
            action="TEST_EXECUTION",
            target=test_command,
            details={"exit_code": res.get("exit_code"), "passed": passed},
            status="passed" if passed else "failed"
        )

        return {
            "passed": passed,
            "stdout": res.get("stdout", ""),
            "stderr": res.get("stderr", ""),
            "exit_code": res.get("exit_code")
        }

    def analyze_bug_and_suggest_fix(self, error_message: str, file_context: str) -> Dict[str, Any]:
        """Uses LLM to analyze stack trace or error and propose a concrete patch."""
        system_prompt = (
            "You are the QA / Debugger Agent of Ultron. Analyze the error and code context.\n"
            "Return JSON with:\n"
            '{"cause": "Description of why it failed", "suggested_patch": "Code or instructions to fix"}'
        )
        user_prompt = f"Error:\n{error_message}\n\nContext:\n{file_context}"
        raw = self.llm.complete(system_prompt, user_prompt, temperature=0.1, json_mode=True)
        return self.parse_json(raw)

qa_agent = QAAgent()
