import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure the root directory is in the Python search path
sys.path.append(str(Path(__file__).resolve().parent))

from src.config import Config
from src.utils import logger
from src.rag_pipeline import RAGPipeline
from src.classifier import CustomerClassifier
from src.generator import ResponseGenerator
from src.escalator import Escalator

def run_verification():
    load_dotenv()
    
    print("=" * 60)
    print("      Persona-Adaptive Support Agent Verification Suite      ")
    print("=" * 60)
    
    # 1. Verify generate_kb.py has run or runs
    print("\n[Step 1] Checking Knowledge Base documents...")
    kb_dir = Path("data/support_docs")
    
    if not kb_dir.exists() or len(list(kb_dir.glob("*"))) < 15:
        print("-> Generating Support Documents (running generate_kb.py programmatically)...")
        try:
            from generate_kb import generate_documents
            generate_documents()
        except ImportError:
            print("ERROR: generate_kb.py not found in working directory.")
            return
    else:
        print(f"-> Found {len(list(kb_dir.glob('*')))} files in {kb_dir}. Generation OK.")

    # Check API Key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("\n[WARNING] GEMINI_API_KEY environment variable is missing.")
        print("AI classification, generation, and escalation summaries will run in offline fallback mode.")
    else:
        print("\n-> GEMINI_API_KEY detected. Online mode active.")

    # 2. Verify RAG Pipeline & ChromaDB
    print("\n[Step 2] Initializing RAG Pipeline & indexing ChromaDB...")
    try:
        pipeline = RAGPipeline()
        # Re-index to ensure ChromaDB gets populated
        print("-> Indexing documents in ChromaDB...")
        pipeline.clear_database()
        total_chunks = pipeline.index_documents()
        status = pipeline.get_kb_status()
        
        print(f"-> ChromaDB Populated: {status['total_chunks']} chunks from {status['document_count']} files.")
        if status['total_chunks'] > 0:
            print("-> ChromaDB Population check: PASS ✓")
        else:
            print("-> ChromaDB Population check: FAIL ✗")
            return
    except Exception as e:
        print(f"-> Error initializing RAG pipeline: {e}")
        return

    # Instantiate modules
    classifier = CustomerClassifier(api_key=api_key)
    generator = ResponseGenerator(api_key=api_key)
    escalator = Escalator(api_key=api_key)

    # 3. Test Persona Classification
    print("\n[Step 3] Testing Persona Classification...")
    persona_tests = [
        {
            "query": "Can you explain why the API is returning 401 and provide logs?",
            "expected": "Technical Expert"
        },
        {
            "query": "I've tried everything and nothing works!",
            "expected": "Frustrated User"
        },
        {
            "query": "How will this affect our business operations?",
            "expected": "Business Executive"
        }
    ]
    
    for test in persona_tests:
        res = classifier.classify(test["query"])
        print(f"Query: \"{test['query']}\"")
        print(f"  -> Detected Persona: {res['persona']} (Confidence: {res['confidence']:.2f})")
        print(f"  -> Sentiment: {res['sentiment']}")
        print(f"  -> Match Expected ({test['expected']}): {'PASS ✓' if res['persona'] == test['expected'] else 'FAIL ✗ (or fallback mode)'}")

    # 4. Check RAG is used
    print("\n[Step 4] Checking RAG usage (Source Citing)...")
    rag_query = "What is the password reset process?"
    retrieved = pipeline.retrieve(rag_query, top_k=2)
    
    if retrieved:
        sources = [c["metadata"].get("source", "") for c in retrieved]
        print(f"Query: \"{rag_query}\"")
        print(f"  -> Retrieved sources: {sources}")
        print(f"  -> Top Score: {retrieved[0]['similarity']:.4f}")
        if "password_reset_guide.pdf" in sources:
            print("  -> RAG citing verification: PASS ✓")
        else:
            print("  -> RAG citing verification: WARNING (Expected password_reset_guide.pdf in retrieval)")
    else:
        print("  -> RAG citing verification: FAIL ✗ (No documents retrieved)")

    # 5. Verify Hallucination Prevention
    print("\n[Step 5] Checking Hallucination Prevention...")
    hallucination_query = "How do I configure Kubernetes auto-scaling?"
    retrieved_h = pipeline.retrieve(hallucination_query, top_k=2)
    
    # We pass it to generator. It should refuse as Kubernetes auto-scaling is not in context.
    response = generator.generate_response(hallucination_query, retrieved_h, "Technical Expert")
    print(f"Query: \"{hallucination_query}\"")
    print(f"  -> Retrieved Chunks: {len(retrieved_h)}")
    print(f"  -> Generated Response: \"{response}\"")
    if "cannot find" in response.lower() or "sorry" in response.lower() or not retrieved_h:
        print("  -> Hallucination Prevention check: PASS ✓")
    else:
        print("  -> Hallucination Prevention check: FAIL ✗ (Model generated an ungrounded response)")

    # 6. Test Escalation Criteria
    print("\n[Step 6] Testing Escalation Criteria...")
    escalation_query = "I was charged twice and want a refund immediately."
    retrieved_e = pipeline.retrieve(escalation_query, top_k=2)
    
    # Test billing escalation
    eval_res = escalator.evaluate_escalation(
        query=escalation_query,
        retrieved_chunks=retrieved_e,
        confidence_threshold=0.45,
        conversation_history=[{"role": "user", "content": escalation_query}],
        sentiment_history=["Negative"]
    )
    
    print(f"Query: \"{escalation_query}\"")
    print(f"  -> Escalated: {eval_res['should_escalate']}")
    print(f"  -> Reason: {eval_res['reason']}")
    if eval_res['should_escalate'] and "billing" in eval_res['reason'].lower():
        print("  -> Billing Escalation check: PASS ✓")
    else:
        print("  -> Billing Escalation check: FAIL ✗")

    # 7. Check Human Handoff JSON
    print("\n[Step 7 & 8] Checking Human Handoff JSON Generation and Similarity Scores...")
    if eval_res['should_escalate']:
        handoff_summary = escalator.generate_handoff_summary(
            persona="Frustrated User",
            issue_reason=eval_res['reason'],
            conversation_history=[{"role": "user", "content": escalation_query}],
            retrieved_chunks=retrieved_e
        )
        print("  -> Handoff JSON keys check:")
        expected_keys = {"persona", "issue", "conversation_history", "documents_used", "attempted_steps", "recommendation"}
        keys_present = expected_keys.issubset(handoff_summary.keys())
        print(f"     Keys: {list(handoff_summary.keys())}")
        print(f"     Valid JSON Format: {'PASS ✓' if keys_present else 'FAIL ✗'}")
        print("     Formatted Handoff Output:")
        print(json.dumps(handoff_summary, indent=2))
        
    if retrieved_e:
        print(f"  -> Similarity score display check: PASS ✓ (Score: {retrieved_e[0]['similarity']:.2f})")
    else:
        print("  -> Similarity score display check: FAIL ✗")

    # 10. Run the 5 Demo Queries
    print("\n" + "=" * 60)
    print("      Executing 5 Demo Queries Pathway Simulator      ")
    print("=" * 60)
    
    demo_queries = [
        "Why is API authentication returning 401?",
        "I've tried resetting my password five times and nothing works.",
        "How will this outage impact business operations?",
        "What are the bearer token header requirements?",
        "I was charged twice and demand a refund."
    ]
    
    history = []
    sentiments = []
    
    for idx, q in enumerate(demo_queries, 1):
        print(f"\nDemo Query {idx}: \"{q}\"")
        history.append({"role": "user", "content": q})
        
        # 1. Classify
        c_res = classifier.classify(q, history[:-1])
        persona = c_res["persona"]
        sentiment = c_res["sentiment"]
        sentiments.append(sentiment)
        print(f"  -> Persona: {persona} (Confidence: {c_res['confidence']:.2f})")
        print(f"  -> Sentiment: {sentiment}")
        
        # 2. Retrieve
        retrieved_q = pipeline.retrieve(q, top_k=2)
        print(f"  -> Retrieved Sources: {[c['metadata'].get('source','') for c in retrieved_q]}")
        if retrieved_q:
            print(f"  -> Top Score: {retrieved_q[0]['similarity']:.2f}")
            
        # 3. Escalation Check
        esc_res = escalator.evaluate_escalation(
            query=q,
            retrieved_chunks=retrieved_q,
            confidence_threshold=0.45,
            conversation_history=history,
            sentiment_history=sentiments
        )
        
        print(f"  -> Escalated: {esc_res['should_escalate']}")
        
        # 4. Generate Response
        if esc_res["should_escalate"]:
            print(f"  -> Escalation Reason: {esc_res['reason']}")
            h_summary = escalator.generate_handoff_summary(
                persona=persona,
                issue_reason=esc_res['reason'],
                conversation_history=history,
                retrieved_chunks=retrieved_q
            )
            print("  -> JSON Handoff Summary Recommendation:")
            print(f"     \"{h_summary.get('recommendation', '')}\"")
            history.append({
                "role": "assistant", 
                "content": f"Escalated: {esc_res['reason']}"
            })
        else:
            resp = generator.generate_response(q, retrieved_q, persona, history[:-1])
            print(f"  -> Response Preview: {resp[:120]}...")
            history.append({
                "role": "assistant",
                "content": resp
            })

    print("\n" + "=" * 60)
    print("Verification Completed.")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
