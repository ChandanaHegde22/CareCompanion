"""
rag/rag_chain.py – Medical Q&A RAG pipeline.
"""

import logging
import config
from database.connection import execute_write, fetch_all, fetch_one
from prompts.rag_prompt import build_rag_prompt
from rag.document_processor import process_document
from rag.retriever import (build_and_save_index, add_chunks_to_index,
                            search, has_index, get_index_size, delete_user_index)
from utils.helpers import save_uploaded_file, now_str

logger = logging.getLogger(__name__)

# ── Gemini availability ────────────────────────────────────────────────────────
_gemini_available = False
_genai_client = None

try:
    from google import genai
    if config.GEMINI_API_KEY:
        _genai_client = genai.Client(api_key=config.GEMINI_API_KEY)
    _gemini_available = True
except ImportError:
    try:
        import google.generativeai as _lg
        if config.GEMINI_API_KEY:
            _lg.configure(api_key=config.GEMINI_API_KEY)
        _gemini_available = True
        _genai_client = "legacy"
    except ImportError:
        pass


def _generate_answer(prompt: str) -> str:
    if not _gemini_available or not config.GEMINI_API_KEY:
        return "AI unavailable. Please add GEMINI_API_KEY to your .env file."
    try:
        if _genai_client and _genai_client != "legacy":
            from google.genai import types as t
            resp = _genai_client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=t.GenerateContentConfig(temperature=0.1, max_output_tokens=1024),
            )
            return resp.text.strip()
        else:
            import google.generativeai as lg
            model = lg.GenerativeModel(
                config.GEMINI_MODEL,
                generation_config=lg.GenerationConfig(temperature=0.1, max_output_tokens=1024),
            )
            return model.generate_content(prompt).text.strip()
    except Exception as exc:
        logger.error("Gemini RAG error: %s", exc)
        return "I encountered an error generating the answer. Please try again."


def upload_and_index_document(user_id: int, uploaded_file,
                               document_type: str = "general") -> dict:
    import os
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    allowed = {".pdf",".docx",".doc",".txt",".text"}
    if ext not in allowed:
        return {"success":False,"message":f"Unsupported type '{ext}'","chunks":0}
    file_size_mb = len(uploaded_file.getbuffer()) / (1024*1024)
    if file_size_mb > config.MAX_UPLOAD_MB:
        return {"success":False,"message":f"File too large ({file_size_mb:.1f} MB)","chunks":0}
    try:
        file_path = save_uploaded_file(user_id, uploaded_file)
    except Exception as exc:
        return {"success":False,"message":f"Save failed: {exc}","chunks":0}
    chunks = process_document(file_path, uploaded_file.name)
    if not chunks:
        return {"success":False,"message":"Could not extract text.","chunks":0}
    indexed = add_chunks_to_index(user_id, chunks)
    if not indexed:
        return {"success":False,"message":"Indexing failed.","chunks":0}
    execute_write(
        """INSERT INTO documents (user_id, filename, file_type, file_path,
                                  document_type, chunks_count, is_indexed, uploaded_at)
           VALUES (?,?,?,?,?,?,1,?)""",
        (user_id, uploaded_file.name, ext.lstrip("."), file_path,
         document_type, len(chunks), now_str()),
    )
    return {"success":True,"message":f"✅ '{uploaded_file.name}' processed ({len(chunks)} chunks).","chunks":len(chunks)}


def answer_medical_query(user_id: int, query: str, top_k: int = 5) -> dict:
    if not query.strip():
        return {"success":False,"answer":"Please enter a question.","sources":[],"chunks_used":0}
    if not has_index(user_id):
        return {"success":False,
                "answer":"No medical documents found. Please upload your reports first.",
                "sources":[],"chunks_used":0}
    results = search(user_id, query, top_k=top_k)
    if not results:
        return {"success":True,
                "answer":"I couldn't find relevant information in your uploaded documents.",
                "sources":[],"chunks_used":0}
    context_parts = []
    sources = []
    for i, r in enumerate(results, 1):
        src = r.get("source","Unknown")
        context_parts.append(f"[Excerpt {i} – {src}]\n{r['text']}")
        if src not in sources:
            sources.append(src)
    context = "\n\n".join(context_parts)
    prompt  = build_rag_prompt(context, query)
    answer  = _generate_answer(prompt)
    return {"success":True,"answer":answer,"sources":sources,"chunks_used":len(results)}


def get_user_documents(user_id: int) -> list[dict]:
    return fetch_all("SELECT * FROM documents WHERE user_id=? ORDER BY uploaded_at DESC", (user_id,))


def delete_document(user_id: int, document_id: int) -> dict:
    doc = fetch_one("SELECT file_path FROM documents WHERE id=? AND user_id=?", (document_id, user_id))
    if not doc:
        return {"success":False,"message":"Document not found."}
    execute_write("DELETE FROM documents WHERE id=?", (document_id,))
    try:
        import os; os.remove(doc["file_path"])
    except Exception:
        pass
    _rebuild_index_for_user(user_id)
    return {"success":True,"message":"Document deleted and index rebuilt."}


def _rebuild_index_for_user(user_id: int) -> None:
    docs = get_user_documents(user_id)
    if not docs:
        delete_user_index(user_id); return
    all_chunks = []
    for doc in docs:
        all_chunks.extend(process_document(doc["file_path"], doc["filename"]))
    if all_chunks:
        build_and_save_index(user_id, all_chunks)
    else:
        delete_user_index(user_id)
