import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent
PROJECTS_DIR = PROJECT_ROOT / "UltronProjects"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure runtime directories exist
PROJECTS_DIR.mkdir(exist_ok=True, parents=True)
DATA_DIR.mkdir(exist_ok=True, parents=True)
LOGS_DIR.mkdir(exist_ok=True, parents=True)

# Load environment variables
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # If .env does not exist, look in current working directory
    load_dotenv()

class UltronConfig:
    """Central configuration for Ultron AI Assistant."""
    
    # LLM Provider selection
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower()
    
    # API Keys
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_FALLBACK_API_KEY: Optional[str] = os.getenv("GEMINI_FALLBACK_API_KEY")
    
    # Models
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
    
    # Voice configuration
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-IN-PrabhatNeural")
    TTS_RATE: str = os.getenv("TTS_RATE", "+5%")
    TTS_VOLUME: str = os.getenv("TTS_VOLUME", "+0%")
    VOICE_INPUT_ENABLED: bool = os.getenv("VOICE_INPUT_ENABLED", "true").lower() in ("true", "1", "yes")
    VOICE_OUTPUT_ENABLED: bool = os.getenv("VOICE_OUTPUT_ENABLED", "true").lower() in ("true", "1", "yes")
    WAKE_WORD: str = os.getenv("WAKE_WORD", "hey ultron").lower()
    
    # Safety
    REQUIRE_CONFIRMATION_FOR_DANGEROUS: bool = os.getenv(
        "REQUIRE_CONFIRMATION_FOR_DANGEROUS", "true"
    ).lower() in ("true", "1", "yes")
    MAX_COMMAND_TIMEOUT_SECONDS: int = int(os.getenv("MAX_COMMAND_TIMEOUT_SECONDS", "60"))
    
    # VPN
    VPN_TYPE: str = os.getenv("VPN_TYPE", "windows_rasdial")
    VPN_CONNECTION_NAME: str = os.getenv("VPN_CONNECTION_NAME", "MyVPN")
    VPN_CLI_PATH: Optional[str] = os.getenv("VPN_CLI_PATH")
    
    # External APIs
    GMAIL_CLIENT_SECRET_FILE: Optional[str] = os.getenv("GMAIL_CLIENT_SECRET_FILE")
    META_ACCESS_TOKEN: Optional[str] = os.getenv("META_ACCESS_TOKEN")
    META_AD_ACCOUNT_ID: Optional[str] = os.getenv("META_AD_ACCOUNT_ID")
    META_PAGE_ID: Optional[str] = os.getenv("META_PAGE_ID")
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Paths
    DATABASE_PATH: Path = DATA_DIR / "ultron_state.db"
    AUDIT_LOG_FILE: Path = LOGS_DIR / "ultron_audit.log"

config = UltronConfig()
