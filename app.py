import os
import streamlit as st
import json
from pathlib import Path
from src.config import Config
from src.utils import logger
from src.rag_pipeline import RAGPipeline
from src.classifier import CustomerClassifier
from src.generator import ResponseGenerator
from src.escalator import Escalator

# Configure Streamlit page settings
st.set_page_config(
    page_title="Persona-Adaptive Customer Support Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-family: 'Inter', sans-serif;
        color: #8a99ad;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
        margin-right: 5px;
    }
    .badge-technical {
        background-color: #1e3a8a;
        color: #3b82f6;
        border: 1px solid #3b82f6;
    }
    .badge-frustrated {
        background-color: #7f1d1d;
        color: #f87171;
        border: 1px solid #f87171;
    }
    .badge-executive {
        background-color: #701a75;
        color: #e879f9;
        border: 1px solid #e879f9;
    }
    .badge-sentiment-pos {
        background-color: #064e3b;
        color: #34d399;
    }
    .badge-sentiment-neu {
        background-color: #374151;
        color: #d1d5db;
    }
    .badge-sentiment-neg {
        background-color: #7f1d1d;
        color: #f87171;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- CACHED RESOURCES -----------------

@st.cache_resource
def load_rag_pipeline() -> RAGPipeline:
    """Instantiates and caches the RAG database pipeline.
    Auto-indexes documents on startup if ChromaDB is empty (e.g. fresh Streamlit Cloud deploy)."""
    pipeline = RAGPipeline()
    # Auto-generate KB files if data dir is empty or missing
    if not Config.DATA_DIR.exists() or not any(Config.DATA_DIR.iterdir()):
        try:
            from generate_kb import generate_documents
            generate_documents()
        except Exception as e:
            logger.warning(f"Could not auto-generate KB files: {e}")
    # Auto-index into ChromaDB if collection is empty
    if pipeline.collection.count() == 0:
        try:
            pipeline.index_documents()
        except Exception as e:
            logger.warning(f"Could not auto-index documents: {e}")
    return pipeline

# ----------------- SESSION STATE SETUP -----------------

# Initialize API Keys and configuration
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = Config.GEMINI_API_KEY

# Initialize conversation and sentiment logs
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "sentiment_history" not in st.session_state:
    st.session_state.sentiment_history = []
    
if "escalated" not in st.session_state:
    st.session_state.escalated = False

if "handoff_summary" not in st.session_state:
    st.session_state.handoff_summary = None

# Initialize cached instances
rag_pipeline = load_rag_pipeline()

# Reconfigure AI clients based on active API key
classifier = CustomerClassifier(api_key=st.session_state.gemini_api_key)
generator = ResponseGenerator(api_key=st.session_state.gemini_api_key)
escalator = Escalator(api_key=st.session_state.gemini_api_key)

def update_api_keys():
    """Triggers update of keys in pipeline modules."""
    classifier.reconfigure(st.session_state.gemini_api_key)
    generator.reconfigure(st.session_state.gemini_api_key)
    escalator.reconfigure(st.session_state.gemini_api_key)

# ----------------- SIDEBAR INTERFACE -----------------

with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/bot.png", width=70)
    st.markdown("### Agent Configuration")
    
    # 1. API Credentials Setup
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.gemini_api_key,
        type="password",
        help="Input your Gemini API key to activate classification and answers. Overrides .env key.",
    )
    
    if api_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key_input
        update_api_keys()
        st.success("API key updated!")
        
    st.divider()
    
    # 2. RAG & Escalation Parameters
    st.markdown("### System Tuners")
    
    confidence_slider = st.slider(
        "Escalation Similarity Threshold",
        min_value=0.10,
        max_value=0.90,
        value=Config.DEFAULT_ESCALATION_THRESHOLD,
        step=0.05,
        help="If the retrieved context's highest similarity score is below this, the query automatically escalates."
    )
    
    top_k_slider = st.slider(
        "RAG Top-K Chunks",
        min_value=1,
        max_value=8,
        value=Config.DEFAULT_TOP_K,
        step=1,
        help="Number of relevant document chunks to feed to the response generator."
    )
    
    st.divider()
    
    # 3. Knowledge Base Diagnostic Status
    st.markdown("### Knowledge Base Hub")
    
    kb_status = rag_pipeline.get_kb_status()
    st.metric("Total Indexed Chunks", kb_status["total_chunks"])
    st.metric("Active Support Documents", kb_status["document_count"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Re-index Docs", use_container_width=True, help="Re-scans /data/support_docs and re-builds Chroma DB."):
            with st.spinner("Re-indexing..."):
                rag_pipeline.clear_database()
                chunk_count = rag_pipeline.index_documents()
                st.success(f"Indexed {chunk_count} chunks!")
                st.rerun()
                
    with col2:
        if st.button("Generate Default KB", use_container_width=True, help="Creates 15 SaaS support docs and re-indexes them."):
            with st.spinner("Generating documents and indexing..."):
                try:
                    from generate_kb import generate_documents
                    generate_documents()
                    rag_pipeline.clear_database()
                    chunk_count = rag_pipeline.index_documents()
                    st.success(f"Generated docs & indexed {chunk_count} chunks!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    
    with st.expander("List of Available Docs"):
        for doc in sorted(kb_status["documents"]):
            st.caption(f"📄 {doc}")
            
    st.divider()
    
    # 4. Utility Actions
    if st.button("Clear Chat Session", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.sentiment_history = []
        st.session_state.escalated = False
        st.session_state.handoff_summary = None
        st.success("Session reset completed.")
        st.rerun()

# ----------------- MAIN PANEL INTERFACE -----------------

st.markdown('<div class="main-title">Persona-Adaptive Support Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI support agent adapting responses dynamically according to customer behavior and context</div>', unsafe_allow_html=True)

# Warning if API key is not configured
if not st.session_state.gemini_api_key:
    st.warning("⚠️ **Gemini API Key Missing**: Please input a valid Gemini API Key in the left sidebar to unlock full agent reasoning and generation.")

# 1. Present Chat Log
for message in st.session_state.messages:
    role = message["role"]
    with st.chat_message(role):
        # Render assistant message
        if role == "assistant":
            st.markdown(message["content"])
            
            # Show diagnostic metadata panel
            with st.expander("🔍 System Diagnostic Insights & Metadata"):
                c1, c2, c3 = st.columns(3)
                
                # Persona classification
                with c1:
                    st.markdown("**Persona Classification**")
                    p_badge = f'<span class="badge badge-technical">Technical Expert</span>'
                    if message["persona"] == "Frustrated User":
                        p_badge = f'<span class="badge badge-frustrated">Frustrated User</span>'
                    elif message["persona"] == "Business Executive":
                        p_badge = f'<span class="badge badge-executive">Business Executive</span>'
                    
                    st.markdown(f"Detected: {p_badge}", unsafe_allow_html=True)
                    st.markdown(f"Confidence Score: `{message['confidence']:.2f}`")
                    st.caption(f"Reasoning: *{message['reasoning']}*")
                    
                # Sentiment Classification
                with c2:
                    st.markdown("**Sentiment Logs**")
                    s_badge = f'<span class="badge badge-sentiment-neu">Neutral</span>'
                    if message["sentiment"] == "Positive":
                        s_badge = f'<span class="badge badge-sentiment-pos">Positive</span>'
                    elif message["sentiment"] == "Negative":
                        s_badge = f'<span class="badge badge-sentiment-neg">Negative</span>'
                        
                    st.markdown(f"Sentiment: {s_badge}", unsafe_allow_html=True)
                    
                # Escalation Status
                with c3:
                    st.markdown("**Escalation Evaluation**")
                    if message.get("escalated", False):
                        st.error("🚨 Escalated to Human Support")
                        st.caption(f"Trigger: *{message.get('escalation_reason', '')}*")
                    else:
                        st.success("🟢 Automated Mode Active")
                        st.caption("All criteria within automated safety limits.")
                        
                # Retrieved Chunks sub-viewer
                st.markdown("---")
                st.markdown("**Retrieved Document Context Chunks**")
                retrieved_chunks = message.get("retrieved", [])
                if not retrieved_chunks:
                    st.caption("No context retrieved for this query.")
                else:
                    for i, chunk in enumerate(retrieved_chunks):
                        meta = chunk.get("metadata", {})
                        source = meta.get("source", "Unknown")
                        page = meta.get("page_number", "")
                        section = meta.get("section", "")
                        score = chunk.get("similarity", 0.0)
                        
                        loc = f"Page {page}" if page else f"Section: {section}" if section else "General"
                        
                        st.markdown(f"**[{i+1}] {source} ({loc})** — Similarity: `{score:.2f}`")
                        # Progress bar of similarity
                        st.progress(float(score))
                        st.code(chunk["text"], language="text")
                        
            # If Escalated, print the structured JSON Handoff Summary
            if message.get("escalated", False) and message.get("handoff_summary"):
                st.error("🚨 **System Handoff Triggered**")
                st.info("The automated agent has compiled the following handoff package for the next available support agent:")
                st.json(message["handoff_summary"])
        else:
            # Render user message
            st.markdown(message["content"])

# 2. Check general escalation state
if st.session_state.escalated:
    st.error("⚠️ **This session has been escalated to a human support representative.**")
    st.info("Automated response generation is currently locked. The support agent summary package is available below.")
    if st.session_state.handoff_summary:
        with st.expander("📋 Active Human Handoff Summary (JSON)", expanded=True):
            st.json(st.session_state.handoff_summary)
            
# 3. Chat Input Processing
if not st.session_state.escalated:
    if query := st.chat_input("How can I assist you today?"):
        # Append user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Display user message instantly
        with st.chat_message("user"):
            st.markdown(query)
            
        # Run agent logic in progress spinner
        with st.chat_message("assistant"):
            with st.spinner("Analyzing request and searching database..."):
                # A. Classifier
                class_res = classifier.classify(query, st.session_state.messages[:-1])
                persona = class_res["persona"]
                confidence = class_res["confidence"]
                sentiment = class_res["sentiment"]
                reasoning = class_res["reasoning"]
                
                # Update sentiment history log
                st.session_state.sentiment_history.append(sentiment)
                
                # B. Retrieve relevant documents
                retrieved_chunks = rag_pipeline.retrieve(query, top_k=top_k_slider)
                
                # C. Check Escalation Conditions
                escalate_res = escalator.evaluate_escalation(
                    query=query,
                    retrieved_chunks=retrieved_chunks,
                    confidence_threshold=confidence_slider,
                    conversation_history=st.session_state.messages,
                    sentiment_history=st.session_state.sentiment_history
                )
                
                should_escalate = escalate_res["should_escalate"]
                escalation_reason = escalate_res["reason"]
                
                # D. Generate Response or handle Escalation
                handoff_summary = None
                if should_escalate:
                    st.session_state.escalated = True
                    # Generate the structured JSON handoff summary via LLM
                    handoff_summary = escalator.generate_handoff_summary(
                        persona=persona,
                        issue_reason=escalation_reason,
                        conversation_history=st.session_state.messages,
                        retrieved_chunks=retrieved_chunks
                    )
                    st.session_state.handoff_summary = handoff_summary
                    
                    response_text = (
                        "I apologize, but this issue exceeds my automated support parameters. "
                        f"**Reason for transfer**: {escalation_reason}\n\n"
                        "I am escalating your ticket to a human representative right now. They will have access to "
                        "the full diagnostic log of our session and will contact you shortly to resolve the problem."
                    )
                else:
                    response_text = generator.generate_response(
                        query=query,
                        context_chunks=retrieved_chunks,
                        persona=persona,
                        history=st.session_state.messages[:-1]
                    )
                    
                # E. Log and render assistant reply
                st.markdown(response_text)
                
                # Save assistant message configuration in logs
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "persona": persona,
                    "confidence": confidence,
                    "sentiment": sentiment,
                    "reasoning": reasoning,
                    "retrieved": retrieved_chunks,
                    "escalated": should_escalate,
                    "escalation_reason": escalation_reason,
                    "handoff_summary": handoff_summary
                })
                
                # Triggers page refresh to update sidebar metrics & render details
                st.rerun()
