"""PDF ingestion, vector storage, and Gemini-powered RAG for infertility guidance."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import google.generativeai as genai
import numpy as np
from deep_translator import GoogleTranslator
from langdetect import detect as _ld_detect
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from app.config import settings


SYSTEM_PROMPT = """You are UZAZI ASSISTANT, an intelligent AI assistant designed to provide accurate, reliable, and conversational responses about infertility and reproductive health.

Language:
- Respond in the user's language: {language}

Your role:
1. Answer questions about infertility using ONLY the verified knowledge base excerpts provided below.
2. Correct common misinformation clearly and gently — explain why a claim is inaccurate and what evidence shows instead.
3. When discussing traditional or complementary medicine (TCM, Ayurveda, herbal remedies, acupuncture, etc.):
   - Acknowledge cultural value and why people explore these options
   - Distinguish between well-studied supportive care and unproven claims
   - Never recommend stopping prescribed medical treatment
   - Encourage consulting a qualified fertility specialist before trying supplements or herbs
4. Use plain, supportive language. Avoid alarmist tone.
5. If the knowledge base does not contain enough information, say so honestly and suggest speaking with a reproductive endocrinologist or OB/GYN.
6. Never provide a definitive diagnosis or prescribe medication dosages.

CRITICAL FORMATTING RULES:
- Write in natural, conversational paragraphs - NOT as a numbered list
- Do NOT use asterisks (**) for bold or emphasis
- Do NOT use quotation marks around terms or phrases
- Do NOT use markdown formatting of any kind
- Write plain text that flows naturally like a human would speak or write
- Use simple, clear sentences without special formatting

Always end your response with a brief reminder that this is educational information, not a substitute for professional medical care.

Knowledge base excerpts:
{context}

Common misinformation patterns to watch for in the user's question:
- "Infertility is always the woman's fault" → Infertility affects both partners; male factor contributes in ~40–50% of cases.
- "Stress alone causes infertility" → Stress may affect cycles but is rarely the sole cause; medical evaluation is important.
- "IVF guarantees a baby" → Success rates vary by age and diagnosis; no treatment guarantees pregnancy.
- "Natural/herbal cures replace fertility treatment" → Most lack rigorous evidence; they may complement, not replace, medical care.
- "Age doesn't matter until 40" → Ovarian reserve declines gradually from the early 30s onward.

User question: {question}
"""



@dataclass
class RetrievedChunk:
    document: str
    text: str
    score: float


class VectorStore:
    """Lightweight file-backed vector store (no native C++ dependencies)."""

    def __init__(self, persist_dir: Path, model: SentenceTransformer) -> None:
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = persist_dir / "index.json"
        self.embeddings_path = persist_dir / "embeddings.npy"
        self.model = model
        self.documents: list[str] = []
        self.metadatas: list[dict] = []
        self.embeddings: np.ndarray | None = None
        self._load()

    def _load(self) -> None:
        if self.index_path.exists() and self.embeddings_path.exists():
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            self.documents = data["documents"]
            self.metadatas = data["metadatas"]
            self.embeddings = np.load(self.embeddings_path)

    def _save(self) -> None:
        self.index_path.write_text(
            json.dumps({"documents": self.documents, "metadatas": self.metadatas}),
            encoding="utf-8",
        )
        if self.embeddings is not None:
            np.save(self.embeddings_path, self.embeddings)

    def count(self) -> int:
        return len(self.documents)

    def clear(self) -> None:
        self.documents = []
        self.metadatas = []
        self.embeddings = None
        if self.index_path.exists():
            self.index_path.unlink()
        if self.embeddings_path.exists():
            self.embeddings_path.unlink()

    def add(self, documents: list[str], metadatas: list[dict]) -> None:
        if not documents:
            return
        new_embeddings = self.model.encode(documents, normalize_embeddings=True)
        if self.embeddings is None:
            self.embeddings = np.array(new_embeddings)
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self._save()

    def query(self, query_text: str, top_k: int = 5) -> list[RetrievedChunk]:
        if not self.documents or self.embeddings is None:
            return []

        query_vec = self.model.encode([query_text], normalize_embeddings=True)[0]
        scores = self.embeddings @ query_vec
        k = min(top_k, len(self.documents))
        top_indices = np.argsort(scores)[::-1][:k]

        return [
            RetrievedChunk(
                document=self.metadatas[i].get("source", self.metadatas[i].get("file", "Unknown")),
                text=self.documents[i],
                score=float(scores[i]),
            )
            for i in top_indices
        ]


class RAGEngine:
    def __init__(self) -> None:
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        self.encoder = SentenceTransformer(settings.embedding_model)
        self.store = VectorStore(settings.chroma_path, self.encoder)
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
        else:
            self.model = None

    @staticmethod
    def detect_language(query: str) -> str:
        """Return "sw" for Swahili, "en" for English."""
        try:
            lang = _ld_detect(query or "")
            return "sw" if lang.startswith("sw") else "en"
        except Exception:
            return "en"

    @staticmethod
    def translate_to_english(query: str) -> str:
        """Translate Swahili query to English."""
        translator = GoogleTranslator(source="sw", target="en")
        return translator.translate(query)

    def bilingual_retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """If Swahili: embed/retrieve using both original (sw) and translated (en) queries,
        merge results, deduplicate by chunk id, and re-rank by best score.

        If English: standard single-query retrieval.
        """
        language = self.detect_language(query)

        def chunk_id(c: RetrievedChunk) -> str:
            # Use source + a stable slice of text to deduplicate.
            # (We don't have an explicit id stored in VectorStore.)
            t = c.text
            return f"{c.document}::{t[:120]}"

        if language == "sw":
            english_query = self.translate_to_english(query)
            sw_chunks = self.store.query(query, top_k=top_k)
            en_chunks = self.store.query(english_query, top_k=top_k)
            merged = sw_chunks + en_chunks
        else:
            merged = self.store.query(query, top_k=top_k)

        best_by_id: dict[str, RetrievedChunk] = {}
        for c in merged:
            cid = chunk_id(c)
            prev = best_by_id.get(cid)
            if prev is None or c.score > prev.score:
                best_by_id[cid] = c

        ranked = sorted(best_by_id.values(), key=lambda x: x.score, reverse=True)
        return ranked[:top_k]

    def detect_intent(self, query: str) -> str:
        """Detect user intent: greeting, farewell, appreciation, help_request, knowledge_question, or unknown."""
        query_lower = query.lower().strip()
        
        # Greeting patterns
        greeting_patterns = [
            r'\b(hello|hi|hey|good morning|good afternoon|good evening|habari|mambo|shikamoo|hujambo)\b'
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, query_lower):
                return "greeting"
        
        # Farewell patterns
        farewell_patterns = [
            r'\b(bye|goodbye|see you|kwaheri|tutaonana|asante.*kwaheri)\b'
        ]
        for pattern in farewell_patterns:
            if re.search(pattern, query_lower):
                return "farewell"
        
        # Appreciation patterns
        appreciation_patterns = [
            r'\b(thank|thanks|asante|nashukuru)\b'
        ]
        for pattern in appreciation_patterns:
            if re.search(pattern, query_lower):
                return "appreciation"
        
        # Help request patterns
        help_patterns = [
            r'\b(help|assist|support|can you|could you|please|msaada|saidia)\b'
        ]
        for pattern in help_patterns:
            if re.search(pattern, query_lower):
                return "help_request"
        
        return "knowledge_question"

    def generate_intent_response(self, intent: str, language: str = "en") -> str:
        """Generate appropriate responses for non-knowledge intents."""
        if intent == "greeting":
            if language == "sw":
                return "Habari! Karibu kwenye UZAZI ASSISTANT. Naweza kukusaidiaje leo?"
            return "Hello! Welcome to UZAZI ASSISTANT. How may I assist you today?"
        
        elif intent == "farewell":
            if language == "sw":
                return "Asante kwa kutumia UZAZI ASSISTANT. Ukihitaji msaada tena, usisite kurudi. Nakutakia siku njema."
            return "Thank you for chatting with me today. If you need any assistance in the future, feel free to return. Have a wonderful day!"
        
        elif intent == "appreciation":
            if language == "sw":
                return "Karibu sana! Nimefurahi kukusaidia. Ukiwa na swali lingine, niko hapa kukusaidia."
            return "You're welcome! I'm glad I could help. Let me know if there's anything else you'd like assistance with."
        
        elif intent == "help_request":
            if language == "sw":
                return "Niko hapa kukusaidia! Unaweza kuniuliza maswali yoyote kuhusu uzazi, utasa, au afya ya uzazi. Nipo tayari kukupa maelezo yanayotegemea ushauri wa kitaalamu."
            return "I'm here to help! You can ask me any questions about infertility, fertility treatments, or reproductive health. I'm ready to provide you with evidence-based information."
        
        return ""

    def _clean_response(self, text: str) -> str:
        """Remove markdown formatting from AI response."""
        if not text:
            return text
        
        # Remove asterisks used for bold/italic (**text** or *text*)
        text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
        
        # Remove backticks used for code (`text` or ```text```)
        text = re.sub(r'`{1,3}([^`]+)`{1,3}', r'\1', text)
        
        # Remove markdown headers (# text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove markdown links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove quotation marks around phrases
        text = re.sub(r'"([^"]+)"', r'\1', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text

    def generate_response(self, question: str, language: str = "en") -> tuple[str, list[dict]]:
        # Check if this is a conversational intent that doesn't need RAG
        intent = self.detect_intent(question)
        
        if intent in ["greeting", "farewell", "appreciation", "help_request"]:
            reply = self.generate_intent_response(intent, language)
            sources = []
            return reply, sources
        
        # Otherwise, use RAG for knowledge questions
        chunks = self.bilingual_retrieve(question, top_k=settings.top_k)
        context = self._build_context(chunks)
        prompt = SYSTEM_PROMPT.format(context=context, question=question, language=language)

        if not self.model:
            fallback = (
                "The AI service is not configured. Please set GEMINI_API_KEY in your environment.\n\n"
                "Based on retrieved knowledge:\n" + context[:1500]
            )
            sources = [{"document": c.document, "excerpt": c.text[:300]} for c in chunks]
            return fallback, sources

        response = self.model.generate_content(prompt)
        reply = self._clean_response(response.text) if response.text else "I was unable to generate a response. Please try again."
        sources = [{"document": c.document, "excerpt": c.text[:300]} for c in chunks]
        return reply, sources


    def _chunk_text(self, text: str) -> list[str]:
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + settings.chunk_size
            chunk = text[start:end]
            if end < len(text):
                last_period = chunk.rfind(". ")
                if last_period > settings.chunk_size // 2:
                    chunk = chunk[: last_period + 1]
                    end = start + len(chunk)
            chunks.append(chunk.strip())
            start = max(end - settings.chunk_overlap, start + 1)
        return [c for c in chunks if c]

    def _load_pdf(self, path: Path) -> list[tuple[str, str]]:
        reader = PdfReader(str(path))
        pages: list[tuple[str, str]] = []
        for i, page in enumerate(reader.pages):
            content = page.extract_text() or ""
            if content.strip():
                pages.append((f"{path.name} (page {i + 1})", content))
        return pages

    def ingest_knowledge_base(self) -> dict:
        kb_path = settings.knowledge_base_path
        kb_path.mkdir(parents=True, exist_ok=True)

        pdf_files = list(kb_path.glob("**/*.pdf"))
        if not pdf_files:
            return {"documents": 0, "chunks": 0, "message": "No PDF files found in knowledge base directory"}

        self.store.clear()
        documents: list[str] = []
        metadatas: list[dict] = []

        for pdf in pdf_files:
            for doc_name, page_text in self._load_pdf(pdf):
                for chunk in self._chunk_text(page_text):
                    documents.append(chunk)
                    metadatas.append({"source": doc_name, "file": pdf.name})

        batch_size = 32
        for i in range(0, len(documents), batch_size):
            self.store.add(documents[i : i + batch_size], metadatas[i : i + batch_size])

        return {"documents": len(pdf_files), "chunks": len(documents)}

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        return self.store.query(query, top_k or settings.top_k)

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "No verified excerpts available. Provide general educational guidance and recommend professional consultation."
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[{i}] Source: {chunk.document}\n{chunk.text}")
        return "\n\n".join(parts)

    def rag_query(self, user_query: str) -> str:
        language = self.detect_language(user_query)
        reply, _sources = self.generate_response_bilingual(question=user_query, language=language)
        return reply

    def generate_response_bilingual(self, question: str, language: str = "en") -> tuple[str, list[dict]]:
        # Check if this is a conversational intent that doesn't need RAG
        intent = self.detect_intent(question)
        
        if intent in ["greeting", "farewell", "appreciation", "help_request"]:
            reply = self.generate_intent_response(intent, language)
            sources = []
            return reply, sources
        
        # Otherwise, use RAG for knowledge questions
        chunks = self.bilingual_retrieve(question, top_k=settings.top_k)
        context = self._build_context(chunks)
        prompt = SYSTEM_PROMPT.format(context=context, question=question, language=language)

        if not self.model:
            fallback = (
                "The AI service is not configured. Please set GEMINI_API_KEY in your environment.\n\n"
                "Based on retrieved knowledge:\n" + context[:1500]
            )
            sources = [{"document": c.document, "excerpt": c.text[:300]} for c in chunks]
            return fallback, sources

        response = self.model.generate_content(prompt)
        reply = self._clean_response(response.text) if response.text else "I was unable to generate a response. Please try again."
        sources = [{"document": c.document, "excerpt": c.text[:300]} for c in chunks]
        return reply, sources


rag_engine: RAGEngine | None = None


def get_rag_engine() -> RAGEngine:
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine
