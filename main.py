import sys
import os
import warnings
warnings.filterwarnings("ignore")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich import box

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import config
from shared_state.state_manager import state_manager
from agents.manager import manager_agent
from voice.audio_engine import audio_engine
from voice.wake_word import wake_detector
from tools.safety_sentinel import safety_sentinel

console = Console(force_terminal=True, legacy_windows=False)

BANNER = """[bold red]
██╗   ██╗██╗  ████████╗██████╗  ██████╗ ███╗   ██╗
██║   ██║██║  ╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║
██║   ██║██║     ██║   ██████╔╝██║   ██║██╔██╗ ██║
██║   ██║██║     ██║   ██╔══██╗██║   ██║██║╚██╗██║
╚██████╔╝███████╗██║   ██║  ██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
[/bold red][bold white]Autonomous Multi-Agent Desktop Assistant[/bold white] [dim]| Windows 11 Engine[/dim]
"""

def print_welcome():
    console.print(BANNER)
    info_table = Table(show_header=False, box=box.ROUNDED, border_style="dim")
    if config.LLM_PROVIDER == 'gemini':
        model_name = config.GEMINI_MODEL
    elif config.LLM_PROVIDER == 'groq':
        model_name = config.GROQ_MODEL
    elif config.LLM_PROVIDER == 'anthropic':
        model_name = config.ANTHROPIC_MODEL
    else:
        model_name = config.OPENAI_MODEL
    info_table.add_row("🧠 Brain (LLM Provider)", f"[cyan]{config.LLM_PROVIDER.upper()}[/cyan] ({model_name})")
    info_table.add_row("🎙️ Voice Persona", "[bold red]Marvel Ultron (Deep Robotic Baritone)[/bold red]")
    info_table.add_row("📞 Live Call Mode", "[bold green]Continuous (Stays on call until dismissed)[/bold green]")
    info_table.add_row("👂 Voice Wake Triggers", "[bold cyan]'Ultron', 'Hey Ultron', 'Wake up'[/bold cyan]")
    info_table.add_row("🛡️ Safety Sentinel", "[bold yellow]Active (Dangerous actions require confirmation)[/bold yellow]")
    info_table.add_row("🌐 Multi-Agent Team", "[magenta]Manager, Thinker, Executor, Coder, QA/Debugger[/magenta]")
    info_table.add_row("📁 Projects Directory", f"[blue]{config.PROJECT_ROOT / 'UltronProjects'}[/blue]")
    console.print(Panel(info_table, title="[bold red]System Status[/bold red]", border_style="red"))
    console.print("[dim]Say [bold cyan]'Hey Ultron'[/bold cyan] to connect a live call. Say [bold red]'That\\'s enough'[/bold red] to end it.[/dim]\n")

def show_audit_logs():
    events = state_manager.get_history(limit=15)
    if not events:
        console.print("[yellow]No audit events logged yet.[/yellow]")
        return

    table = Table(title="Recent Ultron Audit Log", box=box.SIMPLE_HEAVY)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Timestamp", style="cyan", width=19)
    table.add_column("Agent", style="magenta", width=12)
    table.add_column("Action", style="bold yellow", width=18)
    table.add_column("Target / Details", style="white")
    table.add_column("Status", style="green")

    for ev in reversed(events):
        status_style = "green" if ev["status"] == "success" else ("yellow" if ev["status"] == "cancelled" else "red")
        target_str = str(ev.get("target") or "")[:50]
        table.add_row(
            str(ev["id"]),
            str(ev["timestamp"])[:19].replace("T", " "),
            ev["agent_name"],
            ev["action"],
            target_str,
            f"[{status_style}]{ev['status']}[/{status_style}]"
        )

    console.print(table)

def execute_command(clean_input: str, source: str = "Keyboard"):
    if not clean_input:
        return

    if clean_input.lower() in ("exit", "quit", "shutdown"):
        farewell = "Goodbye. Ultron shutting down."
        console.print(f"[bold red]Ultron:[/bold red] {farewell}")
        audio_engine.speak(farewell)
        os._exit(0)

    if clean_input.lower() in ("logs", "audit", "history"):
        show_audit_logs()
        return

    if clean_input.lower() in ("status", "info"):
        print_welcome()
        return

    if source == "Voice":
        console.print(f"\n[bold cyan]⚡ Voice Input Received:[/bold cyan] [bold white]\"{clean_input}\"[/bold white]")

    # Process command through Multi-Agent System
    with console.status("[bold red]Ultron Multi-Agent Swarm coordinating...[/bold red]"):
        response = manager_agent.handle_user_command(clean_input)

    spoken_text = response.get("spoken_response", "Task completed.")
    
    # Print Ultron's response
    console.print(Panel(
        f"[bold white]{spoken_text}[/bold white]",
        title=f"[bold red]Ultron Response ({source})[/bold red]",
        border_style="red"
    ))

    # Voice reply
    audio_engine.speak(spoken_text)
    console.print("[dim green]✓ Task complete. Ready for next command (speak 'Ultron' or type):[/dim green]")

def main():
    print_welcome()

    # Hook safety sentinel voice response
    def voice_confirm(prompt_text: str) -> bool:
        audio_engine.speak(prompt_text)
        return Prompt.ask(f"[bold yellow]{prompt_text}[/bold yellow] (yes/no)", choices=["yes", "no", "y", "n"], default="no").startswith("y")

    safety_sentinel.set_confirmation_hook(voice_confirm)

    is_hands_free = "--voice" in sys.argv

    # Start continuous background voice listener
    if config.VOICE_INPUT_ENABLED:
        wake_detector.start_background_listener(
            on_command_callback=lambda cmd: execute_command(cmd, source="Voice"),
            status_logger=lambda msg: console.print(f"[dim cyan]{msg}[/dim cyan]")
        )

    if is_hands_free:
        console.print("[bold green]● Pure Hands-Free Voice Mode Active.[/bold green] Say [bold cyan]'Hey Ultron'[/bold cyan] or [bold cyan]'Wake up'[/bold cyan] to talk.")
        console.print("[dim]Press Ctrl+C anytime to stop.[/dim]\n")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Voice mode stopped.[/yellow]")
            return

    # Standard interactive loop (supports both typing AND voice wake-up)
    while True:
        try:
            user_input = Prompt.ask("\n[bold red]You[/bold red]")
            execute_command(user_input.strip(), source="Keyboard")
        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Type 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
