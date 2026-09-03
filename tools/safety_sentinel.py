import re
import sys
from enum import Enum
from typing import Callable, Optional
from rich.console import Console
from rich.panel import Panel
from config import config

console = Console()

class ActionRisk(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class SafetySentinel:
    """
    Guardian interceptor that evaluates tool calls before execution.
    Halts execution and prompts for confirmation if risk is HIGH.
    """
    
    DANGEROUS_SHELL_PATTERNS = [
        r"format\s+",
        r"rmdir\s+/s",
        r"del\s+/[fqs]",
        r"remove-item\s+.*-recurse",
        r"drop\s+database",
        r"stop-computer",
        r"shutdown",
        r"bcdedit",
        r"reg\s+delete",
    ]

    def __init__(self):
        self._confirmation_hook: Optional[Callable[[str], bool]] = None

    def set_confirmation_hook(self, hook: Callable[[str], bool]):
        """Allows voice engine or custom UI to provide confirmation."""
        self._confirmation_hook = hook

    def evaluate_risk(self, action_name: str, target: str = "", details: str = "") -> ActionRisk:
        """Classifies the risk level of an intended operation."""
        action_lower = action_name.lower()
        target_lower = str(target).lower()
        details_lower = str(details).lower()
        
        # High Risk Conditions
        if "delete" in action_lower or "remove" in action_lower or "drop" in action_lower:
            return ActionRisk.HIGH
            
        if "ad_campaign" in action_lower or "spend" in action_lower or "purchase" in action_lower:
            return ActionRisk.HIGH
            
        if "post" in action_lower and ("social" in action_lower or "instagram" in action_lower or "facebook" in action_lower):
            return ActionRisk.HIGH
            
        if "shell" in action_lower or "terminal" in action_lower:
            for pattern in self.DANGEROUS_SHELL_PATTERNS:
                if re.search(pattern, details_lower):
                    return ActionRisk.HIGH
            return ActionRisk.MEDIUM
            
        if "vpn" in action_lower or "email" in action_lower:
            return ActionRisk.MEDIUM
            
        return ActionRisk.LOW

    def authorize(self, action_name: str, target: str = "", details: str = "") -> bool:
        """
        Validates whether an action should proceed. Prompts user if HIGH risk.
        """
        risk = self.evaluate_risk(action_name, target, details)
        
        if risk != ActionRisk.HIGH or not config.REQUIRE_CONFIRMATION_FOR_DANGEROUS:
            return True

        warning_message = (
            f"[bold red]WARNING: HIGH-RISK ACTION DETECTED[/bold red]\n\n"
            f"Action: [yellow]{action_name}[/yellow]\n"
            f"Target: [cyan]{target}[/cyan]\n"
            f"Details: {details}\n\n"
            f"[bold white]Ultron requires your permission before proceeding.[/bold white]"
        )
        
        console.print(Panel(warning_message, title="[red]Security Sentinel[/red]", border_style="red"))

        # If an external hook (like voice prompt) is registered, invoke it
        if self._confirmation_hook:
            prompt_text = f"Ultron requires confirmation to execute {action_name} on {target}. Do you confirm? Say Yes or No."
            return self._confirmation_hook(prompt_text)

        # Default: Terminal interactive prompt
        try:
            choice = input("\nDo you authorize Ultron to proceed? [y/N]: ").strip().lower()
            return choice in ("y", "yes")
        except EOFError:
            return False

safety_sentinel = SafetySentinel()
