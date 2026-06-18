import json
from google import genai
from google.genai import types
from typing import Dict, Any, List
from src.config import Config
from src.utils import logger, retry_on_exception

class CustomerClassifier:
    """Classifies a user query and conversation history to determine persona, confidence, and sentiment."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to configure Gemini client in Classifier: {e}")
                
    def reconfigure(self, api_key: str):
        """Reconfigures the Gemini client with a new API key."""
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                self.api_key = api_key
            except Exception as e:
                logger.error(f"Failed to reconfigure Gemini client: {e}")
                self.client = None

    @retry_on_exception(max_retries=3, initial_delay=1.0)
    def classify(self, current_query: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Classifies the user query.
        Returns a dict containing:
        {
            "persona": "Technical Expert" | "Frustrated User" | "Business Executive",
            "confidence": float (between 0.0 and 1.0),
            "sentiment": "Positive" | "Neutral" | "Negative",
            "reasoning": str
        }
        """
        if not self.client:
            logger.warning("Gemini client not initialized. Returning default classification.")
            return {
                "persona": "Frustrated User",
                "confidence": 0.5,
                "sentiment": "Neutral",
                "reasoning": "Gemini API key is not configured. Falling back to default."
            }
            
        history_str = ""
        if history:
            history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-5:]])

        prompt = f"""
Analyze the customer's query and conversation history to determine:
1. The customer's Persona:
   - "Technical Expert": User uses technical vocabulary, code blocks, API terms, asks for deep configurations, error codes, root causes, or architectures.
   - "Frustrated User": User expresses irritation, disappointment, uses exclamation marks, caps lock, aggressive words, complains about blocking problems, demands immediate resolutions.
   - "Business Executive": User asks about pricing, billing, contract renewals, refund policies, corporate seats, SLA terms, timelines, and wants high-level concise summaries with no technical jargon.
2. The classification Confidence Score (float between 0.0 and 1.0).
3. The sentiment: "Positive", "Neutral", or "Negative".
4. A brief, one-sentence reasoning for your decision.

Conversation History:
{history_str}

Current Customer Query:
"{current_query}"

You MUST respond strictly in the following JSON format:
{{
  "persona": "Technical Expert" | "Frustrated User" | "Business Executive",
  "confidence": 0.85,
  "sentiment": "Positive" | "Neutral" | "Negative",
  "reasoning": "Explanation of classification based on query vocabulary and tone."
}}
"""
        
        try:
            response = self.client.models.generate_content(
                model=Config.GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text.strip())
            
            valid_personas = {"Technical Expert", "Frustrated User", "Business Executive"}
            valid_sentiments = {"Positive", "Neutral", "Negative"}
            
            if result.get("persona") not in valid_personas:
                result["persona"] = "Frustrated User"
            if result.get("sentiment") not in valid_sentiments:
                result["sentiment"] = "Neutral"
            try:
                result["confidence"] = float(result.get("confidence", 0.5))
            except (ValueError, TypeError):
                result["confidence"] = 0.5
            result["reasoning"] = result.get("reasoning", "Parsed classification.")
            return result
            
        except Exception as e:
            logger.error(f"Error during Gemini classification call: {e}")
            return {
                "persona": "Frustrated User",
                "confidence": 0.4,
                "sentiment": "Neutral",
                "reasoning": f"Fallback due to model execution error: {str(e)}"
            }
