import google.generativeai as genai
from typing import List, Dict, Any
from src.config import Config
from src.utils import logger, retry_on_exception

class ResponseGenerator:
    """Generates persona-adaptive customer support responses based strictly on retrieved RAG context."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.initialized = False
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.initialized = True
            except Exception as e:
                logger.error(f"Failed to configure Gemini API client in Generator: {e}")
                
    def reconfigure(self, api_key: str):
        """Reconfigures the Gemini client with a new API key."""
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.api_key = api_key
                self.initialized = True
            except Exception as e:
                logger.error(f"Failed to reconfigure Gemini API client in Generator: {e}")
                self.initialized = False

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
        if not self.initialized:
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

        # Define persona-specific instruction blocks
        persona_instructions = ""
        if persona == "Technical Expert":
            persona_instructions = """
- Style: Highly detailed, technical, logical, and structured.
- Tone: Professional, authoritative, and helpful.
- Content Requirements: Provide a thorough explanation of the underlying system mechanics or rules. If available, outline the root cause. Provide complete technical troubleshooting steps. Use code blocks, terminal command syntax, or specific error mappings. Keep explanations deep and robust.
"""
        elif persona == "Frustrated User":
            persona_instructions = """
- Style: High empathy, comforting, reassuring, and action-oriented.
- Tone: Heartfelt, supportive, apologetic, and friendly.
- Content Requirements: Start by acknowledging and validating their frustration immediately (e.g., "I completely understand how frustrating this error is...", "I'm so sorry this is blocking your operations..."). Use comforting, calming language. Explain things in very simple terms. Break down the solution into clear, simple, step-by-step action items. Do NOT use heavy developer jargon.
"""
        elif persona == "Business Executive":
            persona_instructions = """
- Style: Highly concise, clear, summarized, and outcome-oriented.
- Tone: Executive, strategic, business-focused, and polite.
- Content Requirements: Provide a concise summary first (the bottom line). Focus on business impacts (costs, subscription levels, data retention, SLAs). Estimate resolution timelines (e.g., "within 14 days", "instantly", "5 to 10 business days"). Avoid deep developer details or technical code snippets. Use bullet points for high-level summaries.
"""
        else:
            # Fallback
            persona_instructions = "- Tone: Helpful and professional. Provide clear instructions."

        # Unified Prompt with system instructions and guidelines
        prompt = f"""
You are an advanced Customer Support AI Agent. Your goal is to resolve customer inquiries using ONLY the facts present in the provided Retrieved Context. 

=== STRICT CONSTRAINTS ===
1. You MUST formulate your answer using ONLY the information provided in the "Retrieved Context" section below.
2. If the answer to the user's query cannot be found in the Retrieved Context, or if the context is insufficient, state exactly:
   "I'm sorry, I cannot find sufficient information in our support documents to answer your request."
3. Do NOT make up any facts, credentials, command names, URLs, or support details that are not explicitly in the context. Zero hallucinations.
4. Integrate the conversation history to ensure contextually relevant responses.

=== ADAPTIVE PERSONA INSTUCTIONS ===
You must respond as a "{persona}". Adapt your response format and tone to follow these rules:
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
            model = genai.GenerativeModel(Config.GEMINI_MODEL_NAME)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error during response generation call: {e}")
            return f"An error occurred while generating the response: {str(e)}"
