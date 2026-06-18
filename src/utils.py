import os
import time
import logging
from typing import Callable, Any, Dict, List
from pathlib import Path
import pypdf

def setup_logger(name: str = "support_agent") -> logging.Logger:
    """Sets up a standardized logger that writes to both console and a log file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(log_dir / "agent.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

def retry_on_exception(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator to retry a function if it raises an exception, with exponential backoff."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
            logger.error(f"All {max_retries} attempts failed for {func.__name__}.")
            raise last_exception
        return wrapper
    return decorator

class DocumentReader:
    """Utility class to extract text and metadata from support documents based on their extension."""
    
    @staticmethod
    def read_txt(file_path: Path) -> List[Dict[str, Any]]:
        """Reads a TXT file and returns a document chunk structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [{
                "text": content,
                "metadata": {
                    "source": file_path.name,
                    "type": "txt",
                    "section": "General"
                }
            }]
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            raise e

    @staticmethod
    def read_pdf(file_path: Path) -> List[Dict[str, Any]]:
        """Reads a PDF file page by page using PyPDF and returns document structures per page."""
        chunks = []
        try:
            reader = pypdf.PdfReader(file_path)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    chunks.append({
                        "text": text,
                        "metadata": {
                            "source": file_path.name,
                            "type": "pdf",
                            "page_number": page_idx + 1
                        }
                    })
            return chunks
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {e}")
            raise e

    @staticmethod
    def read_md(file_path: Path) -> List[Dict[str, Any]]:
        """Reads a Markdown file, attempts to parse H1/H2 headers as sections."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            chunks = []
            current_section = "Introduction"
            current_text = []
            
            for line in lines:
                # Check for headings
                if line.startswith("#"):
                    # Save preceding section if it exists
                    if current_text:
                        chunks.append({
                            "text": "".join(current_text).strip(),
                            "metadata": {
                                "source": file_path.name,
                                "type": "md",
                                "section": current_section
                            }
                        })
                        current_text = []
                    current_section = line.replace("#", "").strip()
                else:
                    current_text.append(line)
            
            # Save the final section
            if current_text:
                chunks.append({
                    "text": "".join(current_text).strip(),
                    "metadata": {
                        "source": file_path.name,
                        "type": "md",
                        "section": current_section
                    }
                })
                
            return chunks
        except Exception as e:
            logger.error(f"Error reading Markdown file {file_path}: {e}")
            raise e

    @classmethod
    def load_document(cls, file_path: Path) -> List[Dict[str, Any]]:
        """Loads a document based on its file extension."""
        ext = file_path.suffix.lower()
        if ext == ".txt":
            return cls.read_txt(file_path)
        elif ext == ".pdf":
            return cls.read_pdf(file_path)
        elif ext in [".md", ".markdown"]:
            return cls.read_md(file_path)
        else:
            logger.warning(f"Unsupported file format: {ext} for file {file_path.name}")
            return []
