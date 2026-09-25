from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore 
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import logging
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart-cache")

# Load environment variables
load_dotenv()

# 1. Initialize Firebase gracefully with robust path detection
db = None
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if not cred_path:
    candidate = os.path.join(os.path.dirname(__file__), "firebase-credentials.json")
    if os.path.exists(candidate):
        cred_path = candidate
    elif os.path.exists("firebase-credentials.json"):
        cred_path = "firebase-credentials.json"

if cred_path and os.path.exists(cred_path):
    try:
        cred = credentials.Certificate(cred_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info(f"Firebase Firestore initialized successfully from {cred_path}")
    except Exception as e:
        logger.warning(f"Failed to initialize Firebase credentials ({e}). Caching will be disabled.")
else:
    logger.warning("No firebase-credentials.json found. Firestore caching will be disabled.")

app = FastAPI(
    title="Smart Caching System API",
    description="Self-Refining AI Assistant with Vector RAG & Firebase Firestore Caching",
    version="1.0.0"
)

# 2. Allow React (Frontend) to communicate with FastAPI (Backend)
cors_origins_env = os.getenv("ALLOWED_ORIGINS")
if cors_origins_env:
    origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

# 3. High-Performance, Low-Memory Vector Store for RAG
class LightweightVectorStore:
    def __init__(self):
        self.chunks = []
        self.vectorizer = None
        self.tfidf_matrix = None

    def add_documents(self, new_chunks: list[str]):
        if not new_chunks:
            return
        self.chunks.extend(new_chunks)
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)

    def similarity_search(self, query: str, k: int = 3) -> list[str]:
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []
        try:
            query_vec = self.vectorizer.transform([query])
            sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            top_indices = np.argsort(sims)[::-1][:k]
            return [self.chunks[i] for i in top_indices if sims[i] > 0]
        except Exception as e:
            logger.warning(f"Vector search calculation error: {e}")
            return []

vector_store = LightweightVectorStore()

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    chunks = []
    start = 0
    clean_text = " ".join(text.split())
    while start < len(clean_text):
        end = start + chunk_size
        chunk = clean_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

# 4. Helper for Groq clients
def get_groq_clients():
    req_key = os.getenv("api_request") or os.getenv("GROQ_API_KEY")
    cmp_key = os.getenv("api_compare") or os.getenv("GROQ_API_KEY_COMPARE") or req_key
    if not req_key:
        raise HTTPException(
            status_code=500,
            detail="Groq API key is not configured. Please set 'api_request' or 'GROQ_API_KEY' in .env"
        )
    client1 = Groq(api_key=req_key)
    client2 = Groq(api_key=cmp_key if cmp_key else req_key)
    return client1, client2


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Smart Caching System API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "firebase_connected": db is not None,
        "rag_ready": len(vector_store.chunks) > 0,
        "indexed_chunks": len(vector_store.chunks)
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Endpoint to upload a PDF, extract text, and add it to our Vector Store."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    tmp_path = None
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Extract text using PyPDF
        reader = PdfReader(tmp_path)
        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

        if not full_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any readable text from the PDF.")

        # Chunk text
        splits = chunk_text(full_text)
        if not splits:
            raise HTTPException(status_code=400, detail="PDF has no readable text chunks.")

        # Add to vector store
        vector_store.add_documents(splits)

        logger.info(f"Embedded {len(splits)} chunks from {file.filename}")
        return {
            "message": f"Successfully processed and embedded {file.filename} ({len(splits)} chunks)"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError as cleanup_err:
                logger.warning(f"Could not remove temporary file {tmp_path}: {cleanup_err}")


@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    query_raw = request.query.strip()
    if not query_raw:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    query = query_raw.lower()
    local_answer = None
    doc_id = None
    cache_ref = None

    # 1. Check Firebase for a cached answer if Firestore is initialized
    if db is not None:
        try:
            cache_ref = db.collection("aura_cache")
            query_results = cache_ref.where("query", "==", query).stream()
            for doc in query_results:
                local_answer = doc.to_dict().get("answer")
                doc_id = doc.id
                break
        except Exception as e:
            logger.warning(f"Firestore cache lookup failed: {e}")

    # 2. Retrieve Context from Documents (RAG)
    context = ""
    try:
        relevant_docs = vector_store.similarity_search(query_raw, k=3)
        if relevant_docs:
            context = "\n\n".join(relevant_docs)
    except Exception as e:
        logger.warning(f"Vector search failed: {e}")

    # Construct an augmented prompt if we have context
    if context:
        augmented_prompt = f"""Use the following context to answer the question. If the context doesn't contain the answer, use your general knowledge.

Context:
{context}

Question:
{query_raw}"""
    else:
        augmented_prompt = query_raw

    # 3. Fetch fresh answer from Groq
    req1, req2 = get_groq_clients()
    primary_model = os.getenv("GROQ_PRIMARY_MODEL", "openai/gpt-oss-120b")
    evaluator_model = os.getenv("GROQ_EVALUATOR_MODEL", "openai/gpt-oss-20b")

    try:
        resp = req1.chat.completions.create(
            model=primary_model,
            messages=[{"role": "user", "content": augmented_prompt}]
        )
        ai_answer = resp.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API primary inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI model error: {str(e)}")

    # 4. The AI Evaluator / Self-Refining Logic
    if local_answer:
        compare_prompt = f"""You are an AI evaluator.
Compare the following two answers.
QUESTION:
{query_raw}
ANSWER 1 (Local Database Cache):
{local_answer}
ANSWER 2 (Fresh AI Response):
{ai_answer}
Tasks:
1. Which answer is more accurate?
2. Which answer is more complete?
3. Which answer is easier to understand?
4. Final winner: {local_answer} or {ai_answer}

Rules:
- Return only the final best answer.
- Response should feel natural, direct, and human-like.
- Do not explain how the answer was selected.
- Do not mention multiple answers existed.
- Keep the response concise but complete.
- If code is involved, provide the most optimized and correct version only.
"""
        try:
            judge = req2.chat.completions.create(
                model=evaluator_model,
                messages=[{"role": "user", "content": compare_prompt}]
            )
            result = judge.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq evaluator failed ({e}); falling back to fresh AI answer")
            result = ai_answer

        if cache_ref is not None and doc_id:
            try:
                cache_ref.document(doc_id).update({"answer": result})
            except Exception as e:
                logger.warning(f"Firestore cache update failed: {e}")

        return {"answer": result, "cached": True, "refined": True}

    else:
        if cache_ref is not None:
            try:
                cache_ref.add({
                    "query": query,
                    "answer": ai_answer
                })
            except Exception as e:
                logger.warning(f"Firestore cache insert failed: {e}")

        return {"answer": ai_answer, "cached": False, "refined": False}