import json
import google.generativeai as genai
from typing import List, Dict, Any
from src.config import Config
from src.utils import logger, retry_on_exception

class Escalator:
    """Checks escalation criteria and compiles a structured JSON handoff summary for human support agents."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.initialized = False
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.initialized = True
            except Exception as e:
                logger.error(f"Failed to configure Gemini API client in Escalator: {e}")

    def reconfigure(self, api_key: str):
        """Reconfigures the Gemini client with a new API key."""
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.api_key = api_key
                self.initialized = True
            except Exception as e:
                logger.error(f"Failed to reconfigure Gemini API client in Escalator: {e}")
                self.initialized = False

    def evaluate_escalation(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        confidence_threshold: float,
        conversation_history: List[Dict[str, Any]],
        sentiment_history: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluates whether a support ticket should be escalated.
        Returns a dict:
        {
            "should_escalate": bool,
            "reason": str,
            "handoff_summary": dict or None
        }
        """
        # 1. No documents found
        if not retrieved_chunks:
            return {
                "should_escalate": True,
                "reason": "No relevant documents found in the support knowledge base.",
                "handoff_summary": self._generate_fallback_summary("No support documents found", conversation_history, retrieved_chunks)
            }
            
        # 2. Confidence below threshold
        max_similarity = max([c["similarity"] for c in retrieved_chunks]) if retrieved_chunks else 0.0
        if max_similarity < confidence_threshold:
            return {
                "should_escalate": True,
                "reason": f"Retrieval confidence score ({max_similarity:.2f}) is below the threshold ({confidence_threshold:.2f}).",
                "handoff_summary": self._generate_fallback_summary("Retrieval confidence below threshold", conversation_history, retrieved_chunks)
            }
            
        # 3. Billing/Refund issues detected
        billing_keywords = {"billing", "refund", "invoice", "charge", "payment", "pricing", "credit card", "failed transaction", "upgrade plan", "downgrade plan", "cancel subscription"}
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in billing_keywords):
            return {
                "should_escalate": True,
                "reason": "Billing or refund inquiries detected (requires manual administration approval).",
                "handoff_summary": self._generate_fallback_summary("Billing / Refund Issue", conversation_history, retrieved_chunks)
            }
            
        # 4. Legal / Compliance issues detected
        legal_keywords = {"legal", "lawyer", "sue", "compliance", "gdpr", "soc2", "privacy policy", "data protection", "breach", "court"}
        if any(keyword in query_lower for keyword in legal_keywords):
            return {
                "should_escalate": True,
                "reason": "Legal, privacy, or compliance concern detected.",
                "handoff_summary": self._generate_fallback_summary("Legal / Compliance Concern", conversation_history, retrieved_chunks)
            }
            
        # 5. Account sensitive issues detected (MFA reset, lockouts that cannot self-service)
        security_keywords = {"lockout", "locked out", "hacked", "compromise", "breach", "mfa reset", "2fa reset", "reset multi-factor", "reset secondary verification", "owner account reset"}
        if any(keyword in query_lower for keyword in security_keywords):
            return {
                "should_escalate": True,
                "reason": "Account lockout or critical security MFA verification issue.",
                "handoff_summary": self._generate_fallback_summary("Account-Sensitive Security Issue", conversation_history, retrieved_chunks)
            }
            
        # 6. User remains dissatisfied after multiple turns (2 consecutive Negative sentiments)
        # Check last 2 sentiments
        if len(sentiment_history) >= 2:
            last_two_sentiments = sentiment_history[-Config.MAX_NEGATIVE_TURNS:]
            if all(s == "Negative" for s in last_two_sentiments):
                return {
                    "should_escalate": True,
                    "reason": f"Customer has expressed negative sentiment for {Config.MAX_NEGATIVE_TURNS} consecutive turns.",
                    "handoff_summary": self._generate_fallback_summary("Persistent customer dissatisfaction", conversation_history, retrieved_chunks)
                }
                
        # 7. Check if user explicitly requests manual assistance
        explicit_help_keywords = {"human", "representative", "agent", "escalate", "person", "support team", "speak to someone"}
        if any(kw in query_lower for kw in explicit_help_keywords):
            return {
                "should_escalate": True,
                "reason": "Customer explicitly requested transfer to a human support agent.",
                "handoff_summary": self._generate_fallback_summary("Customer requested human agent", conversation_history, retrieved_chunks)
            }

        return {
            "should_escalate": False,
            "reason": "Request is within normal automated handler criteria.",
            "handoff_summary": None
        }

    @retry_on_exception(max_retries=2, initial_delay=1.0)
    def generate_handoff_summary(
        self,
        persona: str,
        issue_reason: str,
        conversation_history: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Uses Gemini to construct a structured, professional JSON summary of the 
        conversation context and specific action items for the human representative.
        """
        if not self.initialized:
            logger.warning("Gemini API key not configured in Escalator. Compiling local fallback summary.")
            return self._generate_fallback_summary(issue_reason, conversation_history, retrieved_chunks, persona)
            
        history_str = ""
        for msg in conversation_history:
            role = msg.get("role", "User").capitalize()
            content = msg.get("content", "")
            history_str += f"- {role}: {content}\n"
            
        docs_used = list(set([chunk["metadata"].get("source", "Unknown") for chunk in retrieved_chunks])) if retrieved_chunks else []
        
        prompt = f"""
You are an escalation manager. We are transferring a support chat session to a human representative.
Please read the details below and generate a structured JSON object summarizing the conversation.

Transfer Reason: {issue_reason}
Customer Persona: {persona}

Chat History:
{history_str}

Retrieved Reference Documents: {', '.join(docs_used) if docs_used else 'None'}

You MUST return a JSON object structured exactly like the template below:
{{
  "persona": "{persona}",
  "issue": "<A concise, one-sentence summary of the user's primary request or grievance>",
  "conversation_history": [<A list of strings capturing the sequence of user inquiries and answers>],
  "documents_used": [<List of document filenames that were retrieved, e.g., "api_authentication.md">],
  "attempted_steps": [<List of troubleshooting steps or solutions already discussed during the conversation>],
  "recommendation": "<Actionable instruction for the human agent. State what they should do next to quickly resolve this based on the context.>"
}}
"""
        try:
            model = genai.GenerativeModel(Config.GEMINI_MODEL_NAME)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            summary = json.loads(response.text.strip())
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate handoff summary via Gemini: {e}")
            return self._generate_fallback_summary(issue_reason, conversation_history, retrieved_chunks, persona)

    def _generate_fallback_summary(
        self,
        reason: str,
        conversation_history: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
        persona: str = "Unknown"
    ) -> Dict[str, Any]:
        """Local fallback summary creator if Gemini is unavailable or errors out."""
        history_summary = []
        for msg in conversation_history:
            role = msg.get("role", "User").capitalize()
            text = msg.get("content", "")
            history_summary.append(f"{role}: {text[:50]}...")
            
        docs_used = list(set([c["metadata"].get("source", "Unknown") for c in retrieved_chunks])) if retrieved_chunks else []
        
        # Deduce attempted steps
        attempted = []
        for msg in conversation_history:
            if msg.get("role") == "assistant":
                # Very simple heuristic
                attempted.append("Sent automated guide response")
                break
        if not attempted:
            attempted = ["Assessed user request"]

        return {
            "persona": persona,
            "issue": f"Escalated due to: {reason}",
            "conversation_history": history_summary,
            "documents_used": docs_used,
            "attempted_steps": attempted,
            "recommendation": "Review conversation history, verify customer identity, and assist with account resolution."
        }
