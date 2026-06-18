import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Manages the configuration parameters for the Persona-Adaptive Customer Support Agent."""
    
    # Workspace Directories
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data" / "support_docs"))
    CHROMA_DB_DIR = Path(os.getenv("CHROMA_DB_DIR", BASE_DIR / "data" / "chromadb"))
    
    # API Configurations
    GEMINI_API_KEY = ""
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
        
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Model Configuration — gemini-1.5-flash has 1500 req/day free vs only 20/day for 2.5-flash
    # Force to 1.5-flash; only allow override if explicitly set to a DIFFERENT value
    _model_env = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
    GEMINI_MODEL_NAME = _model_env if _model_env != "gemini-2.5-flash" else "gemini-1.5-flash"
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    
    # Retrieval Configuration
    DEFAULT_TOP_K = 4
    
    # Escalation Settings
    DEFAULT_ESCALATION_THRESHOLD = float(os.getenv("ESCALATION_THRESHOLD", "0.30"))
    MAX_NEGATIVE_TURNS = 2  # Escalate if the user is dissatisfied for 2 consecutive turns
    
    @classmethod
    def validate(cls) -> bool:
        """Validates critical configurations. Returns True if valid, raises ValueError otherwise."""
        # Ensure data directory exists or can be created
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
        
        # We don't raise ValueError immediately on missing API key here, 
        # as the user might input the key in the Streamlit UI sidebar.
        return True
