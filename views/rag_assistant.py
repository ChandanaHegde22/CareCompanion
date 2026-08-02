"""
pages/rag_assistant.py – Medical Document Q&A (RAG)
Upload PDF/DOCX/TXT reports and ask AI questions answered from the documents.
"""

import streamlit as st
from datetime import datetime

from rag.rag_chain import (
    upload_and_index_document, answer_medical_query,
    get_user_documents, delete_document,
)
from rag.retriever import has_index, get_index_size
from authentication.auth import get_current_user_id
import config

DOC_TYPES = ["General", "Medical Report", "Blood Test", "Prescription",
             "Discharge Summary", "X-Ray Report", "Scan Report", "Other"]


def render():
    user_id = get_current_user_id()

    st.markdown('<div class="page-title">📋 Medical Document Q&A</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Upload your health reports and ask AI questions about them</div>',
                unsafe_allow_html=True)

    # ── Status banner ─────────────────────────────────────────────────────────
    docs       = get_user_documents(user_id)
    index_size = get_index_size(user_id)
    has_docs   = bool(docs)

    if has_docs:
        st.markdown(f"""
        <div class="cc-info-box">
            📚 <strong>{len(docs)} document(s)</strong> indexed · <strong>{index_size} text chunks</strong> ready for search.
            Ask me anything about your medical reports below!
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="cc-info-box" style="border-left-color:#FDCB6E">
            📂 No documents uploaded yet. Upload your medical reports using the panel below
            and I'll answer questions from them — accurately, with zero hallucination.
        </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Ask AI", "📤 Upload Documents", "📁 My Documents"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Q&A Interface
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        # Initialise RAG history
        if "rag_history" not in st.session_state:
            st.session_state["rag_history"] = []

        # Example questions
        st.markdown("**💡 Example questions:**")
        examples = [
            "What medicines am I prescribed?",
            "What is my blood sugar level?",
            "What does my doctor say about my diet?",
            "When is my next follow-up?",
            "What are my cholesterol levels?",
            "What allergies are mentioned?",
        ]
        ex_cols = st.columns(3)
        for i, eq in enumerate(examples):
            with ex_cols[i % 3]:
                if st.button(f"🔹 {eq}", key=f"rag_ex_{i}", use_container_width=True):
                    st.session_state["rag_pending_q"] = eq

        st.markdown("---")

        # Chat history display
        if st.session_state["rag_history"]:
            st.markdown("**Conversation History:**")
            for turn in st.session_state["rag_history"]:
                st.markdown(f"""
                <div class="chat-bubble-user">🙋 {turn['question']}</div>""", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="chat-bubble-ai">
                    🤖 {turn['answer']}
                    {f"<br><small style='color:#636E72;margin-top:6px;display:block'>📄 Sources: {', '.join(turn['sources'])}</small>" if turn.get('sources') else ''}
                </div>""", unsafe_allow_html=True)
            st.markdown("---")

        # Question input
        question = st.text_area(
            "Ask a question about your medical documents…",
            height=90,
            placeholder="e.g. What medicines am I taking? / What is my HbA1c level?",
            key="rag_question_input",
        )

        # Handle pre-filled question from examples
        if "rag_pending_q" in st.session_state:
            question = st.session_state.pop("rag_pending_q")

        col_ask, col_clr = st.columns([3, 1])
        with col_ask:
            ask_btn = st.button("🔍 Search My Documents", type="primary",
                                use_container_width=True, key="ask_rag_btn")
        with col_clr:
            if st.button("🗑️ Clear History", use_container_width=True, key="clear_rag_btn"):
                st.session_state["rag_history"] = []
                st.rerun()

        if ask_btn and question.strip():
            if not has_docs:
                st.warning("⚠️ Please upload at least one document first.")
            else:
                with st.spinner("🔎 Searching through your documents…"):
                    result = answer_medical_query(user_id, question.strip())

                if result["success"]:
                    # Add to history
                    st.session_state["rag_history"].append({
                        "question":    question.strip(),
                        "answer":      result["answer"],
                        "sources":     result["sources"],
                        "chunks_used": result["chunks_used"],
                    })
                    st.rerun()
                else:
                    st.error(f"⚠️ {result['answer']}")
        elif ask_btn:
            st.warning("Please type a question first.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – Upload Documents
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### 📤 Upload Medical Documents")
        st.markdown("""
        <div class="cc-info-box">
            Supported formats: <strong>PDF, DOCX, TXT</strong> · Max size: 20 MB per file<br>
            Your documents are processed locally and never shared.
        </div>""", unsafe_allow_html=True)

        with st.form("upload_doc_form", clear_on_submit=True):
            uploaded_files = st.file_uploader(
                "Choose your medical files",
                accept_multiple_files=True,
                type=["pdf", "docx", "txt"],
                key="doc_uploader",
            )
            doc_type = st.selectbox("Document Type", DOC_TYPES)
            submit_upload = st.form_submit_button("📤 Upload & Process", type="primary",
                                                  use_container_width=True)

            if submit_upload:
                if not uploaded_files:
                    st.warning("Please select at least one file.")
                else:
                    progress_bar = st.progress(0)
                    for i, uf in enumerate(uploaded_files):
                        progress_bar.progress((i) / len(uploaded_files),
                                              text=f"Processing {uf.name}…")
                        with st.spinner(f"⚙️ Indexing {uf.name}…"):
                            res = upload_and_index_document(user_id, uf, doc_type)
                        if res["success"]:
                            st.success(res["message"])
                        else:
                            st.error(f"❌ {uf.name}: {res['message']}")

                    progress_bar.progress(1.0, text="✅ All files processed!")
                    st.balloons()
                    st.rerun()

        # Upload tips
        with st.expander("💡 Tips for best results"):
            st.markdown("""
            - **Blood test reports** → ask about HbA1c, cholesterol, vitamin levels
            - **Prescriptions** → ask about medicines, dosages, instructions
            - **Discharge summaries** → ask about diagnosis, follow-up dates
            - **Scan reports** → ask about findings or doctor's observations
            - Upload **clear PDF** files (not scanned images) for best accuracy
            - For scanned PDFs, OCR will be applied automatically
            """)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – Document Manager
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 📁 Your Uploaded Documents")
        if not docs:
            st.info("No documents yet. Upload your medical files from the 'Upload Documents' tab.")
        else:
            for doc in docs:
                with st.expander(f"📄 {doc['filename']}", expanded=False):
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Type:** {doc['document_type']}")
                    c2.markdown(f"**Chunks:** {doc['chunks_count']}")
                    c3.markdown(f"**Uploaded:** {str(doc['uploaded_at'])[:10]}")
                    c4.markdown(f"**Format:** {doc['file_type'].upper()}") if (c4 := st.columns(1)[0]) else None

                    if st.button(f"🗑️ Delete", key=f"del_doc_{doc['id']}", type="secondary"):
                        with st.spinner("Deleting and rebuilding index…"):
                            res = delete_document(user_id, doc["id"])
                        if res["success"]:
                            st.success(res["message"])
                            st.rerun()
                        else:
                            st.error(res["message"])
