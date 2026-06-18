from google import genai
from google.genai import types
from typing import List, Dict, Any
from src.config import Config
from src.utils import logger, retry_on_exception

class ResponseGenerator:
    """Generates persona-adaptive customer support responses based strictly on retrieved RAG context."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to configure Gemini client in Generator: {e}")
                
    def reconfigure(self, api_key: str):
        """Reconfigures the Gemini client with a new API key."""
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                self.api_key = api_key
            except Exception as e:
                logger.error(f"Failed to reconfigure Gemini client in Generator: {e}")
                self.client = None

    @retry_on_exception(max_retries=3, initial_delay=1.0)
    def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        persona: str, 
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generates a customer support response adapted to the given persona,
        grounded strictly in the retrieved context chunks.
        """
        if not self.client:
            return (
                "Welcome to the Support Portal. Please configure your Gemini API Key in the "
                "sidebar to activate the AI Agent response generator."
            )

        # Shortcut: if query is very short or is a greeting, return a friendly welcome directly
        # without making an LLM call — saves quota and avoids errors on trivial inputs
        q_stripped = query.strip().lower().rstrip("?.!")
        words = q_stripped.split()
        greeting_prefixes = ("hi", "hey", "hello", "helo", "howdy", "hu", "yo", "sup")
        is_greeting = (
            (len(words) <= 2 and len(q_stripped) <= 10) or
            any(q_stripped.startswith(p) for p in greeting_prefixes)
        )
        if is_greeting:
            return (
                "👋 Hello! Welcome to the **Persona-Adaptive Support Hub**.\n\n"
                "I'm your AI support agent. I can help you with:\n"
                "- 🔐 Password resets & account lockouts\n"
                "- 🔑 API authentication & integrations\n"
                "- 💳 Billing, invoices & subscription management\n"
                "- 📊 Dashboard errors & troubleshooting\n"
                "- 👥 User roles & team permissions\n\n"
                "Please describe your issue and I'll get you the right answer right away!"
            )

        # Compile retrieved context
        context_str = ""
        if not context_chunks:
            context_str = "NO RETRIEVED CONTEXT AVAILABLE."
        else:
            for idx, chunk in enumerate(context_chunks):
                source = chunk['metadata'].get('source', 'Unknown')
                page = chunk['metadata'].get('page_number', '')
                section = chunk['metadata'].get('section', '')
                location = f"Page {page}" if page else f"Section: {section}" if section else ""
                context_str += f"--- Document Reference [{idx + 1}] ({source} - {location}) ---\n"
                context_str += f"{chunk['text']}\n\n"

        # Format conversation history
        history_str = ""
        if history:
            history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-6:]])

        # Persona-specific instruction blocks
        if persona == "Technical Expert":
            persona_instructions = """
- Style: Highly detailed, technical, logical, and structured.
- Tone: Professional, authoritative, and helpful.
- Content Requirements: Provide a thorough explanation of the underlying system mechanics. Outline root cause if available. Provide complete technical troubleshooting steps. Use code blocks and specific error mappings.
"""
        elif persona == "Frustrated User":
            persona_instructions = """
- Style: High empathy, comforting, reassuring, and action-oriented.
- Tone: Heartfelt, supportive, apologetic, and friendly.
- Content Requirements: Start by acknowledging and validating their frustration. Use calming language. Explain things in very simple terms. Break down the solution into clear, simple, numbered steps. Do NOT use technical jargon.
"""
        elif persona == "Business Executive":
            persona_instructions = """
- Style: Highly concise, clear, summarized, and outcome-oriented.
- Tone: Executive, strategic, business-focused, and polite.
- Content Requirements: Provide a concise summary first. Focus on business impacts, SLAs, and timelines. Use bullet points. Avoid all technical details and developer jargon.
"""
        else:
            persona_instructions = "- Tone: Helpful and professional. Provide clear instructions."

        prompt = f"""
You are an advanced Customer Support AI Agent. Your goal is to resolve customer inquiries using ONLY the facts present in the provided Retrieved Context.

=== STRICT CONSTRAINTS ===
1. You MUST formulate your answer using ONLY the information in "Retrieved Context" below.
2. If the answer cannot be found in the context, state: "I'm sorry, I cannot find sufficient information in our support documents to answer your request."
3. Do NOT hallucinate any facts, URLs, or commands not in the context.
4. Use the conversation history to maintain context continuity.

=== ADAPTIVE PERSONA INSTRUCTIONS ===
Respond as a "{persona}" using these style rules:
{persona_instructions}

=== RETRIEVED CONTEXT ===
{context_str}

=== CONVERSATION HISTORY ===
{history_str}

=== CURRENT CUSTOMER QUERY ===
Customer: {query}

Formulate your response below:
"""

        try:
            response = self.client.models.generate_content(
                model=Config.GEMINI_MODEL_NAME,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error during response generation call: {e}")
            return f"An error occurred while generating the response: {str(e)}"
